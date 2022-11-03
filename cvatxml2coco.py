'''
@Created By Reginald Van Woensel
@Created Date 13 Apr 2022
@Copyright (c) 2022, AUTIMATIC

Convert person skeletons from CVAT XML to COCO JSON
'''

import xml.etree.ElementTree as ET
import json
import argparse

from datetime import datetime, date
from pathlib import Path

# personkeypoints
KEY_POINTS_PERSON_LABELS = [ "nose", "left_eye", "right_eye", "left_ear", "right_ear", "left_shoulder", "right_shoulder", "left_elbow", "right_elbow", "left_wrist", "right_wrist", "left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle" ]
KEY_POINTS_FACE_LABELS = [ "nose", "left_eye", "right_eye", "left_ear", "right_ear"]

def _write_json(json_path, dic):
    with open(json_path, "w") as f:
        json.dump(dic, f, indent=2)
    print(f"Wrote json to {json_path}")


def convert(cvat_xml, coco_json_file, with_personkeypoints):
    # Parse XML
    print(f"Parse XML {cvat_xml}")
    tree = ET.parse(cvat_xml)
    root = tree.getroot()

    # META info
    meta = root.find("meta")
    if meta is None:
        taskname = "project"
        date_str = f"{date.today():%Y/%m/%d}"
        start_frame = 0
        stop_frame = 0
    else:
        task = meta.find("task")
        taskname_el = task.find("name")
        taskname = taskname_el.text
        dumped_el = meta.find("dumped")
        date_dt = datetime.strptime(dumped_el.text.split()[0], "%Y-%m-%d").date()
        date_str = f"{date_dt:%Y/%m/%d}"
        start_frame_el = task.find("start_frame")
        start_frame = int(start_frame_el.text)
        stop_frame_el = task.find("stop_frame")
        stop_frame = int(stop_frame_el.text)

    if not coco_json_file:
        coco_json_file = f"{taskname}.json"

    # A collection of “info”, “annotations”, “categories”
    coco_dict = {
        "info": {"description": taskname, "data_created": date_str},
        "categories": [],
        "annotations": [],
        "licenses": [] #TODO check with geert@autimatic.be
    }

    cat_name2id = _add_categories(meta, coco_dict)

    annot_id = 1
    person_ids = _retrieve_person_ids(with_personkeypoints, root, stop_frame)

    # Loop through XML according to person ID (ID indicates shapes belonging to a specific unique person)
    print("Loop through XML according to ID")
    for person_id in person_ids:
        start_frame_per_person, stop_frame_per_person = _retrieve_start_and_stop_frame_per_person_id(with_personkeypoints, root, stop_frame, person_id)
        if stop_frame_per_person == 0:
            continue
        print("Person track %s for start frame %s to end frame %s" % (person_id, start_frame_per_person, stop_frame_per_person))
        for frame_index in range(start_frame_per_person, stop_frame_per_person+1):
            key_points = []
            if with_personkeypoints:
                _convert_personkeypoints(root, person_id, frame_index, key_points)

            # Convert bbox person
            for track_elem in root.findall("track"):
                # group ID different => not the person to convert in this loop
                if with_personkeypoints and ('group_id' in track_elem.attrib) and int(track_elem.attrib["group_id"]) != person_id:
                    continue
                # group ID can be zero for the first person
                if with_personkeypoints and not ('group_id' in track_elem.attrib) and 0 != person_id:
                    continue
                # when the xml contains only boxes no group ids are provided
                if not with_personkeypoints and  int(track_elem.attrib["id"]) != person_id:
                    continue
                for box_elem in track_elem.findall("box"):
                    label_elem = track_elem.attrib["label"]
                    label_name = str(label_elem)
                    if label_name != "person":
                        continue
                    #  if frame ID different => not the bbox to convert in this loop
                    if int(box_elem.attrib["frame"]) != frame_index:
                        continue
                    if bool(int(box_elem.attrib["outside"])):
                        continue
                    frame_idx = int(box_elem.attrib["frame"])
                    occluded = int(box_elem.attrib["occluded"])
                    # [x,y,width,height], → Denoting the bbox location of that person. Box coordinates are measured from the top left image corner and are 0-indexed<br />
                    x = float(box_elem.attrib["xtl"])
                    y = float(box_elem.attrib["ytl"])
                    r = float(box_elem.attrib["xbr"])
                    b = float(box_elem.attrib["ybr"])
                    w = r - x
                    h = b - y
                    # The person's actions which are captured
                    actions = []
                    _convert_actions(box_elem, actions)
                    annot_dict = {
                        "id": annot_id,
                        "frame_id": frame_idx,
                        "category_id": 1,
                        "keypoints": key_points,
                        "bbox": [x, y, round(w, 3), round(h, 3)],
                        "track_id": person_id,
                        "occluded": occluded,
                        "activity": actions
                    }
                    annot_id += 1
                    coco_dict["annotations"].append(annot_dict)

    # Convert other bboxes, index starting from the already converted person tracks
    # generate new track_id
    coco_track_id = 1
    while coco_track_id in person_ids:
        coco_track_id +=1
    for track_elem in root.findall("track"):
        for frame_index in range(start_frame, stop_frame):
            _convert_other_bboxes(coco_dict, annot_id, track_elem, coco_track_id, frame_index, cat_name2id)
        annot_id += 1
    _write_json(coco_json_file, coco_dict)

def _add_categories(meta, coco_dict):
    # The “categories” object contains a list of categories (e.g. dog, boat) and each of those belongs to a supercategory (e.g. animal, vehicle).
    # Category ID 1 is for Human.
    cat_dict_person = {"id": 1, "name": "person",
                       "keypoints": KEY_POINTS_PERSON_LABELS,
                       "skeleton": [[15, 13], [13, 11], [16, 14], [14, 12], [11, 12],
                        [5, 11], [6, 12], [5, 6], [5, 7], [6, 8], [7, 9],
                        [8, 10], [1, 2], [0, 1], [0, 2], [1, 3], [2, 4],
                        [3, 5], [4, 6]],
                       "supercategory": "person"}
    coco_dict["categories"].append(cat_dict_person)
    cat_name2id = {}
    cat_name2id["person"] = 1
    # Other categories than person
    cat_id = 2
    if meta is not None:
        labels_el = meta.find("task").find("labels")
        for label_el in labels_el.findall("label"):
            label_name = label_el.find("name").text
            if label_name == "person":
                continue
            if label_name in KEY_POINTS_PERSON_LABELS:
                continue
            cat_name2id[label_name] = cat_id
            cat_dict = {"id": cat_id, "name": label_name, "supercategory": ""}
            cat_id += 1
            coco_dict["categories"].append(cat_dict)
    return cat_name2id

def _retrieve_person_ids(with_personkeypoints, root, stop_frame):
    if with_personkeypoints:
        person_ids = []
        # It could happen that the first person retrieved from the CVAT xml does not have a group_id. In that case add ID = 0
        start_frame_per_person, stop_frame_per_person = _retrieve_start_and_stop_frame_per_person_id(with_personkeypoints, root, stop_frame, 0)
        if(stop_frame_per_person > 0):
            person_ids = [0]
        for track_elem in root.findall("track"):
            # All shapes (points, bboxes) from one person belong to one group. Add the group ID to the person ID list.
            if ('group_id' in track_elem.attrib):
                person_id = int(track_elem.attrib["group_id"])
                if person_id not in person_ids:
                    person_ids.append(person_id)

    # If no groups are set (in case of only person bboxes in XML), use track ID XML
    else:
        person_ids = []
        for track_elem in root.findall("track"):
            if ('id' in track_elem.attrib):
                person_id = int(track_elem.attrib["id"])
                label = str(track_elem.attrib["label"])
                if label == "person":
                    person_ids.append(person_id)
    return person_ids

def _retrieve_start_and_stop_frame_per_person_id(with_personkeypoints, root, stop_frame, person_id):
    start_frame_per_person = stop_frame
    stop_frame_per_person = 0
    for track_elem in root.findall("track"):
        if track_elem.attrib["label"] != "person":
            continue
        if with_personkeypoints and ('group_id' in track_elem.attrib) and int(track_elem.attrib["group_id"]) != person_id:
            continue
        if not with_personkeypoints and int(track_elem.attrib["id"]) != person_id:
             continue
        for box_elem in track_elem.findall("box"):
            frame_index = int(box_elem.attrib["frame"])
            if frame_index < start_frame_per_person:
                start_frame_per_person = frame_index
            if frame_index > stop_frame_per_person:
                stop_frame_per_person = frame_index
    return start_frame_per_person,stop_frame_per_person

def _convert_actions(box_elem, actions):
    #checkbox
    for attr_elem in box_elem.findall("attribute"):
        if attr_elem.text is not None and str(attr_elem.text.lower()) == "true":
            actions.append(attr_elem.attrib["name"])
    #list
    for attr_elem in box_elem.findall("attribute"):
        if attr_elem.text is not None:
            actions.append(str(attr_elem.text.lower()))

def _convert_personkeypoints(root, person_id, frame_index, key_points):
    # Iterate over all person key points
    for person_label_idx in range(len(KEY_POINTS_PERSON_LABELS)):
        is_point_available = False
        for track_elem in root.findall("track"):
            # if group ID different => not the person to convert in this loop
            if ('group_id' in track_elem.attrib) and int(track_elem.attrib["group_id"]) != person_id:
                continue
            # It could happen that the first person retrieved from the CVAT xml does not have a group_id. In that case ID = 0
            if (not ('group_id' in track_elem.attrib)) and 0 != person_id:
                continue
            # if person label different => not the person key point to convert in this loop
            if KEY_POINTS_PERSON_LABELS[person_label_idx] != track_elem.attrib["label"]:
                continue
            for point_elem in track_elem.findall("points"):
                #  if frame ID different => not the point to convert in this loop
                point_frame_id = int(point_elem.attrib["frame"])
                if int(point_frame_id) != frame_index:
                    continue
                # Indicates visibility— 0: outside, 1: labeled but not visible, and 2: labeled and visible
                if bool(int(point_elem.attrib["outside"])):
                    print("outside")
                    visibil = 0
                elif bool(int(point_elem.attrib["occluded"])):
                    visibil = 1
                else:
                    # The face key points are set to 1 (face blurring)
                    if track_elem.attrib["label"] in KEY_POINTS_FACE_LABELS:
                        visibil = 1
                    else:
                        visibil = 2
                # [x1,y1,v1,x2,y2,v2...], → x and y indicate pixel positions in the image
                points = point_elem.attrib["points"]
                pos_arr = points.split(',')
                key_point = []
                for pos in pos_arr:
                    if visibil == 0:
                        key_point.append(float(0))
                    else:
                        key_point.append(float(pos))
                key_point.append(visibil)
                key_points.extend(key_point)
                is_point_available = True
                # if no point from xml
        if not is_point_available:
            key_point = []
            key_point.append(float(0))
            key_point.append(float(0))
            key_point.append(0)
            key_points.extend(key_point)
            is_point_available = True

    assert len(key_points) == 51, "Error length keypoints %s" %len(key_points)

def _convert_other_bboxes(coco_dict, annot_id, track_elem, track_id, frame_index, cat_name2id):
    for box_elem in track_elem.findall("box"):
        label_elem = track_elem.attrib["label"]
        label_name = str(label_elem)
        if label_name == "person":
            continue
        #  if frame ID different => not the bbox to convert in this loop
        if int(box_elem.attrib["frame"]) != frame_index:
            continue
        if bool(int(box_elem.attrib["outside"])):
            continue
        frame_idx = int(box_elem.attrib["frame"])
        occluded = int(box_elem.attrib["occluded"])
        # [x,y,width,height], → Denoting the bbox location of that person. Box coordinates are measured from the top left image corner and are 0-indexed<br />
        x = float(box_elem.attrib["xtl"])
        y = float(box_elem.attrib["ytl"])
        r = float(box_elem.attrib["xbr"])
        b = float(box_elem.attrib["ybr"])
        w = r - x
        h = b - y
        annot_dict = {
            "id": annot_id,
            "frame_id": frame_idx,
            "category_id": cat_name2id[label_name],
            "bbox": [x, y, round(w, 3), round(h, 3)],
            "track_id": track_id,
            "occluded": occluded
        }
        coco_dict["annotations"].append(annot_dict)

def parse_args():
    """Parse arguments of command line"""
    parser = argparse.ArgumentParser(
        description='Convert CVAT XML to COCO JSON format'
    )
    parser.add_argument(
        '--cvat-xml', metavar='FILE', required=True,
        help='Input file with CVAT annotations in XML format'
    )
    parser.add_argument(
        '--coco-json', metavar='FILE', required=True,
        help='File for output annotations in JSON format'
    )
    parser.add_argument("--with-personkeypoints", default=False, action="store_true",
                    help="Use this flag when person key points are included")

    return parser.parse_args()

def main():
    args = parse_args()
    convert(args.cvat_xml, args.coco_json, args.with_personkeypoints)

if __name__ == '__main__':
    main()