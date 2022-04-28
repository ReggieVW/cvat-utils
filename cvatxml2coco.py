"""
Convert from CVAT XML to COCO JSON
"""

import xml.etree.ElementTree as ET
import json
import argparse

from datetime import datetime, date
from pathlib import Path
from PIL import Image
from cocojson.utils.common import path, get_imgs_from_dir


def write_json(json_path, dic):
    with open(json_path, "w") as f:
        json.dump(dic, f, indent=2)
    print(f"Wrote json to {json_path}")


def convert(xmlfile, img_root, jsonfile):
    """
    Transforms an XML in CVAT format to COCO.
    """
    # Parse XML
    print(f"Parse XML {xmlfile}")
    tree = ET.parse(xmlfile)
    root = tree.getroot()

    # META info
    meta = root.find("meta")
    task = meta.find("task")
    taskname = task.find("name")
    if taskname is None:
        taskname = ""
    else:
        taskname = taskname.text

    if jsonfile:
        out_json = jsonfile
    else:
        json_file_name = taskname if taskname else Path(xmlfile).stem
        out_json = f"{json_file_name}.json"

    dumped = meta.find("dumped")
    if dumped is None:
        date_str = f"{date.today():%Y/%m/%d}"
    else:
        date_dt = datetime.strptime(dumped.text.split()[0], "%Y-%m-%d").date()
        date_str = f"{date_dt:%Y/%m/%d}"

    start_frame = task.find("start_frame")
    if start_frame is None:
        start_frame = 0
    else:
        start_frame = int(start_frame.text)
    assert start_frame >= 0

    stop_frame = task.find("stop_frame")
    if stop_frame is None:
        stop_frame = 0
    else:
        stop_frame = int(stop_frame.text)

    # A collection of “info”, “images”, “annotations”, “categories”
    coco_dict = {
        "info": {"description": taskname, "data_created": date_str},
        "annotations": [],
        "categories": [],
        "images": [],
    }

    # bodykeypoint names
    key_body_labels = ["nose", "head_bottom", "head_top", "left_ear", "right_ear", "left_shoulder", "right_shoulder",  "left_elbow",
                       "right_elbow",  "left_wrist", "right_wrist", "left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle"]

    # The “categories” object contains a list of categories (e.g. dog, boat) and each of those belongs to a supercategory (e.g. animal, vehicle).
    # Category ID 1 is for Human.
    cat_dict_person = {"id": 1, "name": "person",
                       "keypoints": key_body_labels,
                       "skeleton": [[16, 14], [14, 12], [17, 15], [15, 13], [12, 13], [6, 12], [7, 13], [6, 7], [6, 8], [7, 9], [8, 10], [9, 11], [2, 3], [1, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7]],
                       "supercategory": "person"}
    coco_dict["categories"].append(cat_dict_person)
    cat_name2id = {}
    this_cat_id = 2
    labels = meta.find("task").find("labels")
    for label in labels.findall("label"):
        label_name = label.find("name").text
        if label_name in key_body_labels:
            continue
        cat_name2id[label_name] = this_cat_id
        cat_dict = {"id": this_cat_id, "name": label_name, "supercategory": ""}
        this_cat_id += 1
        coco_dict["categories"].append(cat_dict)

    # Add image info to JSON file
    # The “images” section contains the complete list of images in the dataset.
    # It's a list of images and information about each one.
    img_idx2id = {}
    if img_root is not None:
        img_root = path(img_root, is_dir=True)
        img_paths = get_imgs_from_dir(img_root)
        img_id = 0
        for i, img_path in enumerate(img_paths):
            w, h = Image.open(img_path).size
            img_idx2id[i] = img_id
            img_dict = {
                "id": img_id,
                "file_name": str(img_path.relative_to(img_root)),
                "height": h,
                "width": w,
            }
            img_id += 1
            coco_dict["images"].append(img_dict)

    this_annot_id = 1

    # All shapes (points, bboxes) from one person belong to one group
    xml_person_ids = []
    for track_elem in root.findall("track"):
        if ('group_id' in track_elem.attrib):
            xml_person_id = int(track_elem.attrib["group_id"])
            if xml_person_id not in xml_person_ids:
                xml_person_ids.append(xml_person_id)

    # No groups are set (in case of only person bboxes in XML), use track ID XML
    if len(xml_person_ids) == 0:
        for track_elem in root.findall("track"):
            if ('id' in track_elem.attrib):
                xml_person_id = int(track_elem.attrib["id"])
                label = str(track_elem.attrib["label"])
                if label == "person":
                    xml_person_ids.append(xml_person_id)

    # Loop through XML according to ID (ID indicates shapes belonging to a specific unique person)
    print("Loop through XML according to ID")
    print(xml_person_ids)
    for xml_person_id in xml_person_ids:
        for frame_index in range(start_frame, stop_frame):
            key_points = []
            prev_pos = []
            # Iterate over all body parts
            for body_label_idx in range(len(key_body_labels)):
                is_point_available = False
                for track_elem in root.findall("track"):
                    # if group ID different => not the person to convert in this loop
                    if (not ('group_id' in track_elem.attrib)) or int(track_elem.attrib["group_id"]) != xml_person_id:
                        continue
                    # if body label different => not the body part to convert in this loop
                    if key_body_labels[body_label_idx] != track_elem.attrib["label"]:
                        continue
                    for point_elem in track_elem.findall("points"):
                        #  if frame ID different => not the point to convert in this loop
                        point_frame_id = int(point_elem.attrib["frame"])
                        if int(point_frame_id) != frame_index:
                            continue
                        # Indicates visibility— 0: outside, 1: labeled but not visible, and 2: labeled and visible
                        if bool(int(point_elem.attrib["outside"])):
                            visibil = 0
                        elif bool(int(point_elem.attrib["occluded"])):
                            visibil = 1
                        else:
                            visibil = 2

                        # [x1,y1,v1,x2,y2,v2...], → x and y indicate pixel positions in the image
                        points = point_elem.attrib["points"]
                        pos_arr = points.split(',')
                        key_point = []
                        for pos in pos_arr:
                            key_point.append(float(pos))
                        key_point.append(visibil)
                        key_points.extend(key_point)
                        prev_pos = pos_arr
                        is_point_available = True
                if not is_point_available and len(prev_pos) > 0:
                    key_point = []
                    for pos in prev_pos:
                        key_point.append(float(pos))
                    key_point.append(0)
                    key_points.extend(key_point)

            # Convert bbox person
            for track_elem in root.findall("track"):
                # group ID different => not the person to convert in this loop
                if (('group_id' in track_elem.attrib) and int(track_elem.attrib["group_id"]) != xml_person_id):
                    continue
                if (('group_id' not in track_elem.attrib) and int(track_elem.attrib["id"]) != xml_person_id):
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

                    if img_root is not None:
                        imgid = img_idx2id[frame_idx - start_frame]
                    else:
                        imgid = 0

                    occluded = bool(int(box_elem.attrib["occluded"]))
                    keyframe = bool(int(box_elem.attrib["keyframe"]))
                    # [x,y,width,height], → Denoting the bbox location of that person. Box coordinates are measured from the top left image corner and are 0-indexed<br />
                    x = float(box_elem.attrib["xtl"])
                    y = float(box_elem.attrib["ytl"])
                    r = float(box_elem.attrib["xbr"])
                    b = float(box_elem.attrib["ybr"])
                    w = r - x
                    h = b - y
                    # The person's actions which are captured
                    actions = []
                    for attr_elem in box_elem.findall("attribute"):
                        if str(attr_elem.text.lower()) == "true":
                            actions.append(attr_elem.attrib["name"])
                    annot_dict = {
                        "id": this_annot_id,
                        "image_id": imgid,
                        "frame_id": frame_idx,
                        "category_id": 1,
                        "keypoints": key_points,
                        "bbox": [x, y, r, b],
                        # "bbox": [l, t, w, h],
                        # "area": w * h,
                        # Is not a crowd (meaning it’s a single object)
                        # "iscrowd": 0,
                        "track_id": xml_person_id,
                        "occluded": occluded,
                        "keyframe": keyframe,
                        "activity": actions
                    }
                    this_annot_id += 1
                    print(this_annot_id)
                    coco_dict["annotations"].append(annot_dict)
    write_json(out_json, coco_dict)


def parse_args():
    """Parse arguments of command line"""
    parser = argparse.ArgumentParser(
        description='Convert CVAT XML wwwto COCO JSON format'
    )
    parser.add_argument(
        '--cvat-xml', metavar='FILE', required=True,
        help='input file with CVAT annotation in xml format'
    )
    parser.add_argument(
        '--image-dir', metavar='DIRECTORY', required=False,
        help='directory which contains original images'
    )
    parser.add_argument(
        '--coco', metavar='FILE', required=True,
        help='FILE for output annotations in JSON format'
    )
    return parser.parse_args()


def main():
    args = parse_args()
    convert(args.cvat_xml, args.image_dir, args.coco)


if __name__ == '__main__':
    main()
