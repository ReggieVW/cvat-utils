"""
Convert from COCO JSON to CVAT XML
"""


import json
import sys
import sys
import argparse

from collections import OrderedDict
from xml.sax.saxutils import XMLGenerator


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


def convert(json_file, xml_file, withBodyKeyPoints):
    """
    Transforms COCO json to an XML in CVAT format.
    """
    # bodykeypoint names
    body_key_labels = ["nose", "", "", "", "", "left_shoulder", "right_shoulder", "left_elbow", "right_elbow", "left_wrist", "right_wrist",
                       "left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle"]

    # Write the xml file
    with open(xml_file, 'w') as f:
        dumper = XmlAnnotationWriter(f)
        dumper.open_root()

        # Opening the JSON file
        print(f"Opening the JSON file {json_file}")
        json_f = open(json_file)
        track_ids_to_convert = []
        json_data = json.load(json_f)
        for data in json_data["annotations"]:
            track_id = data["track_id"]
            if track_id not in track_ids_to_convert:
                track_ids_to_convert.append(track_id)

        xml_track_id = 0
        # Loop through json_data according to track_id (ID remains constant for that person/object in all the sequences)
        for track_id_to_convert in track_ids_to_convert:
            max_frame_id = 0
            for data in json_data["annotations"]:
                track_id = data["track_id"]
                frame_id = data["frame_id"]
                # if track ID different => not the person/object to convert in this loop
                if track_id_to_convert != track_id:
                    continue
                # set max frame_id
                if frame_id > max_frame_id:
                    max_frame_id = frame_id

            track = {
                'id': str(xml_track_id),
                'label': 'person',
                'group_id': str(track_id_to_convert)
            }

            dumper.open_track(track)
            # Add 1 to track for next object to convert
            xml_track_id += 1

            # Convert bounding box to XML
            for data in json_data["annotations"]:
                track_id = data["track_id"]
                # if track ID different => not the person/object to convert in this loop
                if track_id_to_convert != track_id:
                    continue
                box = data["bbox"]
                for a, b, c, d in fourwise(box[:4]):
                    shape = OrderedDict()
                    shape.update(OrderedDict([
                        ("xtl", "{:.2f}".format(a)),
                        ("ytl", "{:.2f}".format(b)),
                        ("xbr", "{:.2f}".format(c)),
                        ("ybr", "{:.2f}".format(d))
                    ]))
                    frame_no = data["frame_id"]
                    shape["frame"] = str(frame_no)
                    shape["keyframe"] = str(0)
                    shape["outside"] = str(0)
                    shape["occluded"] = str(0)
                    shape["z_order"] = str(0)
                    # if frame_no % x ==0: -> keyframe every x frames (use interpolation in between)
                    shape["keyframe"] = str(1)
                    if frame_no == max_frame_id:
                        shape["outside"] = str(1)
                    dumper.open_box(shape)
                    dumper.close_box()
            dumper.close_track()

            # Convert body key points to XML
            if(withBodyKeyPoints):
                # Iterate over all body parts
                for bodykey_idx in range(len(body_key_labels)):
                    # Don't convert pointkey from the face
                    if (bodykey_idx > 0 and bodykey_idx < 5):
                        continue
                    # Create a track for each key point in the XML
                    track = {
                        'id': str(xml_track_id),
                        'label': body_key_labels[bodykey_idx],
                        'group_id': str(track_id_to_convert)
                    }
                    dumper.open_track(track)
                    # Add 1 to track for next object to convert
                    xml_track_id += 1
                    for data in json_data["annotations"]:
                        track_id = data["track_id"]
                        if track_id_to_convert != track_id:
                            continue
                        frame_no = data["frame_id"]
                        xml_point_idx = 0
                        for keypoint in data["keypoints"]:
                            # x and y indicate pixel positions in the image. z indicates conficence
                            for x, y, z in threewise(keypoint):
                                # if point idx different => not the bodypart to convert in this loop
                                if xml_point_idx != bodykey_idx:
                                    continue
                                shape = OrderedDict()
                                shape["frame"] = str(frame_no)
                                shape["outside"] = str(0)
                                shape["keyframe"] = str(1)
                                # if last point from sequence or confidence under threshold, put outside = 1
                                if frame_no == max_frame_id or z < 0.4:
                                    shape["outside"] = str(1)
                                else:
                                    shape["outside"] = str(0)
                                shape["occluded"] = str(0)
                                shape["z_order"] = str(0)
                                shape.update(
                                    {"points": '{:.2f},{:.2f}'.format(x, y)})
                                dumper.open_points(shape)
                                dumper.close_points()
                            xml_point_idx += 1
                    dumper.close_track()
                    bodykey_idx += 1
        # Closing file
        print(f"Closing the JSON file {json_f}")
        json_f.close()
        dumper.close_root()
        print(f"Wrote file {xml_file}")

def parse_args():
    """Parse arguments of command line"""
    parser = argparse.ArgumentParser(
        description='Convert COCO JSON format to CVAT XML annotations'
    )
    parser.add_argument(
        '--cvat-xml', metavar='FILE', required=True,
        help='input file with CVAT annotation in xml format'
    )
    parser.add_argument(
        '--coco', metavar='FILE', required=True,
        help='FILE for output annotations in JSON format'
    )
    return parser.parse_args()


def main():
    withBodyKeyPoints = True
    args = parse_args()
    convert(args.coco, args.cvat_xml, withBodyKeyPoints)


if __name__ == '__main__':
    main()
# print(stream.getvalue())
