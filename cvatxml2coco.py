"""
Convert from CVAT XML to COCO JSON
"""

import xml.etree.ElementTree as ET
import json
import argparse
import sys

from datetime import datetime, date
from pathlib import Path
from PIL import Image
from cocojson.utils.common import path, get_imgs_from_dir


def write_json(json_path, dic):
    with open(json_path, "w") as f:
        json.dump(dic, f, indent=2)
    print(f"Wrote json to {json_path}")


def convert(xmlfile, img_root, jsonfile, withBodyKeyPoints, withDummyActions):
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
        "categories": [],
        "annotations": [],
        #"images": [],
    }

    # bodykeypoint labels19
    #key_body_labels = ["nose", "head_bottom", "head_top", "left_ear", "right_ear", "left_shoulder", "right_shoulder",  "left_elbow",
     #                  "right_elbow",  "left_wrist", "right_wrist", "left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle"]
    key_body_labels = [ "nose", "left_eye", "right_eye", "left_ear", "right_ear", "left_shoulder", "right_shoulder", "left_elbow", "right_elbow", "left_wrist", "right_wrist", "left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle" ]
    face_body_labels = [ "nose", "left_eye", "right_eye", "left_ear", "right_ear"]
    # The “categories” object contains a list of categories (e.g. dog, boat) and each of those belongs to a supercategory (e.g. animal, vehicle).
    # Category ID 1 is for Human.
    cat_dict_person = {"id": 1, "name": "person",
                       "keypoints": key_body_labels,
                       "skeleton": [[15, 13], [13, 11], [16, 14], [14, 12], [11, 12],
                        [5, 11], [6, 12], [5, 6], [5, 7], [6, 8], [7, 9],
                        [8, 10], [1, 2], [0, 1], [0, 2], [1, 3], [2, 4],
                        [3, 5], [4, 6]],
                       "supercategory": "person"}
                       
    coco_dict["categories"].append(cat_dict_person)

    cat_name2id = {}
    this_cat_id = 2
    labels = meta.find("task").find("labels")
    for label in labels.findall("label"):
        label_name = label.find("name").text
        if label_name == "person":
            continue
        if label_name in key_body_labels:
            continue
        cat_name2id[label_name] = this_cat_id
        cat_dict = {"id": this_cat_id, "name": label_name, "supercategory": ""}
        this_cat_id += 1
        #coco_dict["categories"].append(cat_dict)

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
    xml_person_ids = [0]
    if withBodyKeyPoints or withDummyActions:
        for track_elem in root.findall("track"):
            if ('group_id' in track_elem.attrib):
                xml_person_id = int(track_elem.attrib["group_id"])
                if xml_person_id not in xml_person_ids:
                    xml_person_ids.append(xml_person_id)

    # If no groups are set (in case of only person bboxes in XML), use track ID XML
    if len(xml_person_ids) == 0:
        for track_elem in root.findall("track"):
            if ('id' in track_elem.attrib):
                xml_person_id = int(track_elem.attrib["id"])
                label = str(track_elem.attrib["label"])
                if label == "person":
                    xml_person_ids.append(xml_person_id)

    print("Person tracks to process, %s" % len(xml_person_ids))
    if len(xml_person_ids) > 500:   
        sys.exit("Too much person tracks to process, %s!" % len(xml_person_ids)) 
         
    # Loop through XML according to ID (ID indicates shapes belonging to a specific unique person)
    print("Loop through XML according to ID")
    for xml_person_id in xml_person_ids:
        xml_person_start_frame = stop_frame
        xml_person_stop_frame = 0
        for track_elem in root.findall("track"):
            if track_elem.attrib["label"] != "person":
                continue
            if ('group_id' in track_elem.attrib) and int(track_elem.attrib["group_id"]) != xml_person_id:
                continue
            if ('group_id' not in track_elem.attrib) and int(track_elem.attrib["id"]) != xml_person_id:
                 continue
            for box_elem in track_elem.findall("box"):
                frame_index = int(box_elem.attrib["frame"])
                if frame_index < xml_person_start_frame:
                    xml_person_start_frame = frame_index
                if frame_index > xml_person_stop_frame:
                    xml_person_stop_frame = frame_index
        print("Person track %s for start frame %s to end frame %s" % (xml_person_id, xml_person_start_frame, xml_person_stop_frame))
        for frame_index in range(xml_person_start_frame, xml_person_stop_frame+1):
            key_points = []
            if withBodyKeyPoints:
                prev_pos = []
                # Iterate over all body parts
                for body_label_idx in range(len(key_body_labels)):
                    is_point_available = False
                    for track_elem in root.findall("track"):
                        # if group ID different => not the person to convert in this loop
                        if ('group_id' in track_elem.attrib) and int(track_elem.attrib["group_id"]) != xml_person_id:
                            continue
                        if (not ('group_id' in track_elem.attrib)) and 0 != xml_person_id:
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
                                if track_elem.attrib["label"] in face_body_labels:
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
                            prev_pos = pos_arr
                            is_point_available = True
                    # if no point from xml make dummy key points from prev points and set visibility on 0
                    if not is_point_available and len(prev_pos) > 0:
                        key_point = []
                        for pos in prev_pos:
                            key_point.append(float(pos))
                        key_point.append(0)
                        key_points.extend(key_point)

            # Convert bbox person
            for track_elem in root.findall("track"):
                # group ID different => not the person to convert in this loop
                #if (not withBodyKeyPoints and not withDummyActions and int(track_elem.attrib["id"]) != xml_person_id):
                #    continue
                #if ((withBodyKeyPoints or withDummyActions) and ("group_id" not in track_elem.attrib or  int(track_elem.attrib["group_id"]) != xml_person_id)):
                #    continue
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
                    #actionsList = ['Daily Actions','Mutual Actions / Two Person Interactions','']
                    actions = []
                    if withDummyActions:
                        for track_elem2 in root.findall("track"):
                            if ("group_id" not in track_elem2.attrib or int(track_elem2.attrib["group_id"]) != xml_person_id):
                                continue
                            for points_elem in track_elem2.findall("points"):
                                if int(points_elem.attrib["frame"]) != frame_index:
                                    continue
                                if bool(int(points_elem.attrib["outside"])):
                                    continue
                                for attr_elem in points_elem.findall("attribute"):
                                    if attr_elem.text is not None and str(attr_elem.text.lower()) == "true":
                                        text = attr_elem.attrib["name"]
                                        if text == "hit with object":
                                            text = "hit other person with something"
                                        if text == "grab other person\u2019s stuff":
                                            text = "grab other person's stuff"
                                        actions.append(text)
                    else:
                        for attr_elem in box_elem.findall("attribute"):
                            if attr_elem.text is not None and str(attr_elem.text.lower()) == "true":
                                actions.append(attr_elem.attrib["name"])
                    annot_dict = {
                        "id": this_annot_id,
                        #"image_id": imgid,
                        "frame_id": frame_idx,
                        "category_id": 1,
                        "keypoints": key_points,
                        #"bbox": [x, y, r, b],
                        "bbox": [x, y, round(w, 2), round(h, 2)],
                        # "area": w * h,
                        # Is not a crowd (meaning it’s a single object)
                        # "iscrowd": 0,
                        "track_id": xml_person_id,
                        #"occluded": occluded,
                        #"keyframe": keyframe,
                        "activity": actions
                    }
                    this_annot_id += 1
                   # print("Added annotation for  ID %s" % this_annot_id)
                    coco_dict["annotations"].append(annot_dict)
                    #print("Processed, %s!, category %s" % (label_name, cat_name2id[label_name]))

    # Convert other bboxes
    used_track_ids = xml_person_ids
    coco_track_id = 1
    for track_elem in root.findall("track"):
        # generate new track_id
        while coco_track_id in used_track_ids:
            coco_track_id +=1
        #track_id = int(track_elem.attrib["id"])
        for frame_index in range(start_frame, stop_frame):
            convert_other_bboxes(img_root, start_frame, coco_dict, img_idx2id, this_annot_id, track_elem, coco_track_id, frame_index, cat_name2id)
        used_track_ids.append(coco_track_id)
        this_annot_id += 1

    write_json(out_json, coco_dict)

def convert_other_bboxes(img_root, start_frame, coco_dict, img_idx2id, this_annot_id, track_elem, track_id, frame_index, cat_name2id):
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
        annot_dict = {
            "id": this_annot_id,
            "image_id": imgid,
            "frame_id": frame_idx,
            "category_id": cat_name2id[label_name],
            #"bbox": [x, y, r, b],
            "bbox": [x, y, round(w, 2), round(h, 2)],
            # "area": w * h,
            # Is not a crowd (meaning it’s a single object)
            # "iscrowd": 0,
            "track_id": track_id,
            "occluded": occluded,
            "keyframe": keyframe
        }
        # print("Added annotation for  ID %s" % this_annot_id)
        coco_dict["annotations"].append(annot_dict)
        #print("Processed, %s!, category %s" % (label_name, cat_name2id[label_name]))

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
    parser.add_argument("--withBodyKeyPoints", default=False, action="store_true",
                    help="Flag to use body key points")

    parser.add_argument("--withDummyActions", default=False, action="store_true",
                    help="Flag to use dummy actions to extract activity")

    return parser.parse_args()


def main():
    args = parse_args()
    convert(args.cvat_xml, args.image_dir, args.coco, args.withBodyKeyPoints, args.withDummyActions)


if __name__ == '__main__':
    main()
