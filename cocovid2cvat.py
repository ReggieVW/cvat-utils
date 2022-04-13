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
        key_labels = ["nose", "", "", "", "" , "leftShoulder","rightShoulder", "leftElbow", "rightElbow", "leftWrist", "rightWrist",
        "leftHip", "rightHip", "leftKnee", "rightKnee", "leftAnkle", "rightAnkle",  "REye", "LEye", "REar",
        "leftEar","leftBigToe","leftSmallToe","leftHeel","rightBigToe","rightSmallToe","rightHeel","Background"]
        id = 0
        frame_seq = 0
        frameNo = 0
        point_track_id = 0
        # Opening JSON file
        json_f = open(inputfile)
        # returns JSON object as
        # a dictionary
        trackids = []
        max_track_id = 0
        json_data = json.load(json_f)
        for data in json_data ["annotations"]:
            track_id = data["track_id"]
            if track_id not in trackids:
                trackids.append(track_id)
        for peopleNo in trackids:
            maxFrameId = 0
            minFrameId = 9999
            for data in json_data["annotations"]:
                track_id = data["track_id"]
                frame_id = data["frame_id"]
                if peopleNo != track_id:
                    continue
                if frame_id > maxFrameId:
                    maxFrameId = frame_id
                if frame_id < minFrameId:
                    minFrameId = frame_id
            # box
            track = {
                'id': str(point_track_id),
                'label': 'person',
                'group_id': str(peopleNo)
            }
            dumper.open_track(track)
            point_track_id += 1
            for data in json_data["annotations"]:
                # Iterating through the json
                track_id = data["track_id"]
                if peopleNo != track_id:
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
                    frameNo = data["frame_id"]
                    shape["frame"] = str(frameNo)
                    shape["keyframe"] = str(0)
                    shape["outside"] = str(0)
                    shape["occluded"] = str(0)
                    shape["z_order"] = str(0)
                    if frameNo == 0 or frameNo % 5 ==0:
                        shape["keyframe"] = str(1)
                    if frameNo == maxFrameId:
                        shape["outside"] = str(1)
                        shape["keyframe"] = str(1)
                    dumper.open_box(shape)
                    dumper.close_box()
            dumper.close_track()
            if(withKeyPoints):
                # points
                for pointNo in range(17):
                    keyPoint = True
                    if (pointNo > 0 and pointNo < 5):
                        continue
                    track = {
                        'id': str(point_track_id),
                        'label': key_labels[pointNo],
                        'group_id': str(peopleNo)
                    }
                    dumper.open_track(track)
                    point_track_id += 1
                    index = 0
                    for data in json_data["annotations"]:
                        # Iterating through the json
                        track_id = data["track_id"]
                        if peopleNo != track_id:
                            continue
                        frameNo = data["frame_id"]
                        keyPointNo = 0
                        for keypoint in data["keypoints"]:
                            for x,y,z in threewise(keypoint):
                                if keyPointNo != pointNo:
                                    continue
                                #dumper.open_track(track)
                                shape = OrderedDict()
                                shape["frame"] = str(frameNo)
                                shape["outside"] = str(0)
                                shape["keyframe"] = str(0)
                                if frameNo == 0 or frameNo % 5 ==0:
                                    shape["keyframe"] = str(1)
                                if frameNo == maxFrameId or z < 0.3:
                                    shape["outside"] = str(1)
                                    shape["keyframe"] = str(1)
                                else:
                                    shape["outside"] = str(0)
                                shape["occluded"] = str(0)
                                shape["z_order"] = str(0)
                                shape.update({"points":'{:.2f},{:.2f}'.format(x, y)})
                                dumper.open_points(shape)
                                dumper.close_points()
                                keyPoint = False
                            keyPointNo += 1
                        index += 1
                    dumper.close_track()
                    pointNo += 1
        # Closing file
        json_f.close()
        dumper.close_root()

if __name__ == '__main__':
    main(sys.argv[1:])
#print(stream.getvalue())