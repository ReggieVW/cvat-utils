from xml.sax import saxutils
import sys
from tempfile import TemporaryFile
from io import StringIO
from collections import OrderedDict
import json
import os
from xml.sax.saxutils import XMLGenerator
import sys, getopt

class XmlAnnotationWriter:
    def __init__(self, file):
        self.version = "1.1"
        self.file = file
        self.xmlgen = XMLGenerator(self.file, 'utf-8')
        self._level = 0

    def _indent(self, newline = True):
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
        #self._add_version()

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

    def open_polygon(self, polygon):
        self._indent()
        self.xmlgen.startElement("polygon", polygon)
        self._level += 1

    def open_polyline(self, polyline):
        self._indent()
        self.xmlgen.startElement("polyline", polyline)
        self._level += 1

    def open_points(self, points):
        self._indent()
        self.xmlgen.startElement("points", points)
        self._level += 1

    def open_cuboid(self, cuboid):
        self._indent()
        self.xmlgen.startElement("cuboid", cuboid)
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

    def close_polygon(self):
        self._level -= 1
        self._indent()
        self.xmlgen.endElement("polygon")

    def close_polyline(self):
        self._level -= 1
        self._indent()
        self.xmlgen.endElement("polyline")

    def close_points(self):
        self._level -= 1
        self._indent()
        self.xmlgen.endElement("points")

    def close_cuboid(self):
        self._level -= 1
        self._indent()
        self.xmlgen.endElement("cuboid")

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

def pairwise(iterable):
    a = iter(iterable)
    return zip(a, a)

def threewise(iterable):
    a = iter(iterable)
    return zip(a, a, a)

def fourwise(iterable):
    a = iter(iterable)
    return zip(a, a, a, a)

def fivewise(iterable):
    a = iter(iterable)
    return zip(a, a, a, a, a)

def main(argv):
    withKeyPoints=True
    inputfile = ''
    outputfile = ''
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
        print ('cocovid2cvat.py -i <inputfile> -o <outputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('cocovid2cvat.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg

    with open(outputfile, 'w') as f:
        #stream = StringIO();
        dumper = XmlAnnotationWriter(f)
        dumper.open_root()
        key_labels = ["nose", "", "", "", "" , "left_shoulder","right_shoulder", "left_elbow", "right_elbow", "left_wrist", "right_wrist",
        "left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle"]
        id = 0
        frame_seq = 0
        frame_no = 0
        point_track_id = 0
        # Opening JSON file
        json_f = open(inputfile)
        # returns JSON object as
        # a dictionary
        track_ids = []
        max_track_id = 0
        json_data = json.load(json_f)
        for data in json_data ["annotations"]:
            track_id = data["track_id"]
            if track_id not in track_ids:
                track_ids.append(track_id)
        for people_no in track_ids:
            max_frame_id = 0
            min_frame_id = 9999
            for data in json_data["annotations"]:
                track_id = data["track_id"]
                frame_id = data["frame_id"]
                if people_no != track_id:
                    continue
                if frame_id > max_frame_id:
                    max_frame_id = frame_id
                if frame_id < min_frame_id:
                    min_frame_id = frame_id
            # box
            track = {
                'id': str(point_track_id),
                'label': 'person',
                'group_id': str(people_no)
            }
            dumper.open_track(track)
            point_track_id += 1
            for data in json_data["annotations"]:
                # Iterating through the json
                track_id = data["track_id"]
                if people_no != track_id:
                    continue
                box = data["bbox"]
               # for a,b,c,d, z in fivewise(box):
                for a,b,c,d in fourwise(box[:4]):
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
                    #if frame_no == 0 or frame_no % 5 ==0:
                    shape["keyframe"] = str(1)
                    if frame_no == max_frame_id:
                        shape["outside"] = str(1)
                        #shape["keyframe"] = str(1)
                    dumper.open_box(shape)
                    dumper.close_box()
            dumper.close_track()
            if(withKeyPoints):
                # points
                for point_no in range(17):
                    key_point = True
                    if (point_no > 0 and point_no < 5):
                        continue
                    track = {
                        'id': str(point_track_id),
                        'label': key_labels[point_no],
                        'group_id': str(people_no)
                    }
                    dumper.open_track(track)
                    point_track_id += 1
                    index = 0
                    for data in json_data["annotations"]:
                        # Iterating through the json
                        track_id = data["track_id"]
                        if people_no != track_id:
                            continue
                        frame_no = data["frame_id"]
                        key_point_no = 0
                        for keypoint in data["keypoints"]:
                            for x,y,z in threewise(keypoint):
                                if key_point_no != point_no:
                                    continue
                                #dumper.open_track(track)
                                shape = OrderedDict()
                                shape["frame"] = str(frame_no)
                                shape["outside"] = str(0)
                                shape["keyframe"] = str(1)
                                if frame_no == max_frame_id or z < 0.4 :
                                    shape["outside"] = str(1)
                                else:
                                    shape["outside"] = str(0)
                                shape["occluded"] = str(0)
                                shape["z_order"] = str(0)
                                shape.update({"points":'{:.2f},{:.2f}'.format(x, y)})
                                dumper.open_points(shape)
                                dumper.close_points()
                                key_point = False
                            key_point_no += 1
                        index += 1
                    dumper.close_track()
                    point_no += 1
        # Closing file
        json_f.close()
        dumper.close_root()

if __name__ == '__main__':
    main(sys.argv[1:])
#print(stream.getvalue())