"""
@Created By Reginald Van Woensel
@Created Date 13 Apr 2022
@Copyright (c) 2022, AUTIMATIC

Convert person skeletons from COCO JSON to CVAT XML
"""

from pickle import FALSE
from collections import OrderedDict
from xml.sax.saxutils import XMLGenerator

import numpy as np
import argparse
import json


class XmlAnnotationWriter:
    def __init__(self, file):
        self.version = "1.1"
        self.file = file
        self.xmlgen = XMLGenerator(self.file, 'utf-8')
        self._level = 0

    def _indent(self, newline=True):
        if newline:
            self.xmlgen.ignorableWhitespace("\n")
        self.xmlgen.ignorableWhitespace("  " * self._level)

    def _add_version(self):
        self._indent()
        self.xmlgen.startElement("version", {})
        self.xmlgen.characters(self.version)
        self.xmlgen.endElement("version")

    def open_root(self):
        self.xmlgen.startDocument()
        self.xmlgen.startElement("annotations", {})
        self._level += 1
        # self._add_version()

    def _add_meta(self, meta):
        self._level += 1
        for k, v in meta.items():
            if isinstance(v, OrderedDict):
                self._indent()
                self.xmlgen.startElement(k, {})
                self._add_meta(v)
                self._indent()
                self.xmlgen.endElement(k)
            elif isinstance(v, list):
                self._indent()
                self.xmlgen.startElement(k, {})
                for tup in v:
                    self._add_meta(OrderedDict([tup]))
                self._indent()
                self.xmlgen.endElement(k)
            else:
                self._indent()
                self.xmlgen.startElement(k, {})
                self.xmlgen.characters(v)
                self.xmlgen.endElement(k)
        self._level -= 1

    def add_meta(self, meta):
        self._indent()
        self.xmlgen.startElement("meta", {})
        self._add_meta(meta)
        self._indent()
        self.xmlgen.endElement("meta")

    def open_track(self, track):
        self._indent()
        self.xmlgen.startElement("track", track)
        self._level += 1

    def open_image(self, image):
        self._indent()
        self.xmlgen.startElement("image", image)
        self._level += 1

    def open_box(self, box):
        self._indent()
        self.xmlgen.startElement("box", box)
        self._level += 1

    def open_polyline(self, polyline):
        self._indent()
        self.xmlgen.startElement("polyline", polyline)
        self._level += 1

    def open_points(self, points):
        self._indent()
        self.xmlgen.startElement("points", points)
        self._level += 1

    def open_tag(self, tag):
        self._indent()
        self.xmlgen.startElement("tag", tag)
        self._level += 1

    def add_attribute(self, attribute):
        self._indent()
        self.xmlgen.startElement("attribute", {"name": attribute["name"]})
        self.xmlgen.characters(attribute["value"])
        self.xmlgen.endElement("attribute")

    def close_box(self):
        self._level -= 1
        self._indent()
        self.xmlgen.endElement("box")

    def close_polyline(self):
        self._level -= 1
        self._indent()
        self.xmlgen.endElement("polyline")

    def close_points(self):
        self._level -= 1
        self._indent()
        self.xmlgen.endElement("points")

    def close_tag(self):
        self._level -= 1
        self._indent()
        self.xmlgen.endElement("tag")

    def close_image(self):
        self._level -= 1
        self._indent()
        self.xmlgen.endElement("image")

    def close_track(self):
        self._level -= 1
        self._indent()
        self.xmlgen.endElement("track")

    def close_root(self):
        self._level -= 1
        self._indent()
        self.xmlgen.endElement("annotations")
        self.xmlgen.endDocument()

def threewise(iterable):
    a = iter(iterable)
    return zip(a, a, a)

def fourwise(iterable):
    a = iter(iterable)
    return zip(a, a, a, a)


def convert(coco_json_file, cvat_xml, with_bodykeypoints, with_dummyaction):
    # Opening the JSON file
    print(f"Opening the JSON file {coco_json_file}")
    json_f = open(coco_json_file)
    track_ids_to_convert = []
    json_data = json.load(json_f)
    last_frame_id = 0
    for data in json_data["annotations"]:
        json_track_id = data["track_id"]
        frame_id = data["frame_id"]
        if json_track_id not in track_ids_to_convert:
            track_ids_to_convert.append(json_track_id)
            # set max frame_id
        if frame_id > last_frame_id:
            last_frame_id = frame_id

    for data in json_data["annotations"]:
        cat_name2id = {}
        for data in json_data["categories"]:
            label_name = data["name"]
            this_cat_id = data["id"]
            cat_name2id[this_cat_id] = label_name

    print("Categories, %s!" % cat_name2id)
    print("track_ids_to_convert, %s!" % track_ids_to_convert)

    # Write the xml file
    with open(cvat_xml, 'w') as f:
        dumper = XmlAnnotationWriter(f)
        dumper.open_root()
        
        cvat_track_id = 0
        # Loop through json_data according to track_id (ID remains constant for that person/object in all the sequences)
        for track_id_to_convert in track_ids_to_convert:
            min_frame_id, max_frame_id = _retrieve_min_and_max_frame_for_track_id(json_data, track_id_to_convert)
            print("track_id_to_convert %s, min_frame_id %s, max_frame_id %s !" %(track_id_to_convert,min_frame_id,max_frame_id))

            category = ""
            for data in json_data["annotations"]:
                json_track_id = data["track_id"]
                # if track ID different => not the person/object to convert in this loop
                if track_id_to_convert != json_track_id:
                    continue
                this_cat_id = data["category_id"]
                category = cat_name2id[this_cat_id]
                break

            track = {
                'id': str(cvat_track_id),
                'label': category,
                'group_id': str(track_id_to_convert + 1)
            }
            dumper.open_track(track)
            # Add 1 to track for next object to convert
            cvat_track_id += 1
            # Convert bounding box to XML
            for data in json_data["annotations"]:
                json_track_id = data["track_id"]
                # if track ID different => not the person/object to convert in this loop
                if track_id_to_convert != json_track_id:
                    continue
                box = data["bbox"]
                frame_no = data["frame_id"]
                shape = _createShapeBox(box, frame_no, last_frame_id, max_frame_id)
                dumper.open_box(shape)
                if category == "person":
                    dumper.add_attribute(OrderedDict([("name", "person_track_id"),("value", str(json_track_id))]))
                else:
                    dumper.add_attribute(OrderedDict([("name", "object_track_id"),("value", str(json_track_id))]))
                dumper.close_box()
            dumper.close_track()
            if(with_dummyaction and category == "person"):
                actions = ['Actions']
                for action in actions:
                    _create_dummy_object_func(action, dumper, json_data, cvat_track_id, track_id_to_convert, frame_no, min_frame_id, max_frame_id, last_frame_id )
                    # Add 1 to track for next object to convert
                    cvat_track_id += 1
            # Convert body key points to XML
            if(category == "person" and with_bodykeypoints):
                # bodykeypoint names
                body_key_labels = [ "nose", "left_eye", "right_eye", "left_ear", "right_ear", "left_shoulder", "right_shoulder", "left_elbow", "right_elbow", "left_wrist", "right_wrist", "left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle" ]
                # Iterate over all body parts
                for bodykey_idx in range(len(body_key_labels)):
                    # Create a track for each key point in the XML
                    track = {
                        'id': str(cvat_track_id),
                        'label': body_key_labels[bodykey_idx],
                        'group_id': str(track_id_to_convert + 1)
                    }
                    dumper.open_track(track)
                    # Add 1 to track for next object to convert
                    cvat_track_id += 1
                    for data in json_data["annotations"]:
                        json_track_id = data["track_id"]
                        if track_id_to_convert != json_track_id:
                            continue
                        frame_no = data["frame_id"]
                        xml_point_idx = 0
                        # x and y indicate pixel positions in the image. z indicates conficence
                        arr_2d_keypoints = np.reshape(data["keypoints"], (17, 3))
                        for keypoint in arr_2d_keypoints:
                            for x, y, z in threewise(keypoint):
                                # if point idx different => not the bodypart to convert in this loop
                                if xml_point_idx != bodykey_idx:
                                    continue
                                shape = OrderedDict()
                                shape["frame"] = str(frame_no)
                                shape["keyframe"] = str(1)
                                shape["occluded"] = str(0)   
                                # if last point from sequence 
                                shape["outside"] = str(0)
                                if frame_no == max_frame_id and last_frame_id != max_frame_id:
                                    shape["outside"] = str(1)
                                if z == 0:
                                    shape["outside"] = str(1)
                                if z == 1:
                                    shape["occluded"] = str(1)                               
                                shape["z_order"] = str(0)
                                shape.update(
                                    {"points": '{:.2f},{:.2f}'.format(x, y)})
                                dumper.open_points(shape)
                                dumper.close_points()
                            xml_point_idx += 1
                    dumper.close_track()
                    bodykey_idx += 1
        # Closing file
        print(f"Closing the JSON file {coco_json_file}")
        json_f.close()
        dumper.close_root()
        print(f"Wrote file {cvat_xml}")

def _retrieve_min_and_max_frame_for_track_id(json_data, track_id_to_convert):
    max_frame_id = 0
    min_frame_id = float('inf')
    for data in json_data["annotations"]:
        track_id = data["track_id"]
        frame_id = data["frame_id"]
                # if track ID different => not the person/object to convert in this loop
        if track_id_to_convert != track_id:
            continue
                # set max frame_id
        if frame_id > max_frame_id:
            max_frame_id = frame_id
                # set min frame_id
        if frame_id < min_frame_id:
            min_frame_id = frame_id
    return min_frame_id,max_frame_id

def _createShapeBox(box, frame_no, last_frame_id, max_frame_id):
    shape = OrderedDict()
    shape.update(OrderedDict([
                    ("xtl", "{:.2f}".format(box[0])),
                    ("ytl", "{:.2f}".format(box[1])),
                    ("xbr", "{:.2f}".format(box[0]+box[2])),
                    ("ybr", "{:.2f}".format(box[1]+box[3]))
                ]))
    shape["frame"] = str(frame_no)
    shape["outside"] = str(0)
    shape["occluded"] = str(0)
    shape["z_order"] = str(0)
    shape["keyframe"] = str(1)
    if frame_no == max_frame_id and last_frame_id != max_frame_id:
        shape["outside"] = str(1)
    return shape

def _create_dummy_object_func(action, dumper, json_data, cvat_track_id, track_id_to_convert, frame_no, min_frame_id, max_frame_id, last_frame_id):
    dummy_track = {
        'id': str(cvat_track_id),
        'label': action,
        'group_id': str(track_id_to_convert + 1)
    }
    dumper.open_track(dummy_track)
    # Convert bounding box to XML
    for data in json_data["annotations"]:
        track_id = data["track_id"]
        frame_no = data["frame_id"]
        # if track ID different => not the person/object to convert in this loop
        if track_id_to_convert != track_id:
            continue
        # if track ID different => not the person/object to convert in this loop
        shape = OrderedDict()
        shape.update(OrderedDict([("points", "0.00,0.00")]))
        shape["frame"] = str(frame_no)
        shape["keyframe"] = str(0)
        shape["outside"] = str(0)
        shape["occluded"] = str(0)
        shape["z_order"] = str(0)
        if frame_no == max_frame_id:
            if last_frame_id != max_frame_id:
                shape["outside"] = str(1)
            shape["keyframe"] = str(1)
        if frame_no == min_frame_id:
            shape["keyframe"] = str(1)
        dumper.open_points(shape)
        dumper.add_attribute(OrderedDict([("name", "person_track_id"),("value", str(track_id_to_convert))]))
        dumper.close_points()
    dumper.close_track()

def parse_args():
    """Parse arguments of command line"""
    parser = argparse.ArgumentParser(
        description='Convert COCO JSON format to CVAT XML annotations'
    )
    parser.add_argument(
        '--coco-json', metavar='FILE', required=True,
        help='FILE for output annotations in JSON format'
    )
    parser.add_argument(
        '--cvat-xml', metavar='FILE', required=True,
        help='input file with CVAT annotations in XML format'
    )
    parser.add_argument("--with-bodykeypoints", default=False, action="store_true",
                    help="Flag to use body key points")

    parser.add_argument("--with-dummyaction", default=False, action="store_true",
                    help="Flag to create dummy action")

    return parser.parse_args()


def main():
    args = parse_args()
    convert(args.coco_json, args.cvat_xml, args.with_bodykeypoints, args.with_dummyaction)


if __name__ == '__main__':
    main()