"""
Convert from CVAT Video XML to COCO JSON
"""

import xml.etree.ElementTree as ET
import json
import sys, getopt

from datetime import datetime, date
from pathlib import Path

from PIL import Image
from tqdm import tqdm

from cocojson.utils.common import path, get_imgs_from_dir


def convert(argv):
    inputfile = ''
    outputfile = ''
    try:
      opts, args = getopt.getopt(argv,"hi:o:m:",["ifile=","ofile=","mdir="])
    except getopt.GetoptError:
      print ('cvatvid2coco.py -i <inputfile> -o <outputfile> -m <imageDir>')
      sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('cvatvid2coco.py -i <inputfile> -o <outputfile> -m <imageDir>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
        elif opt in ("-m", "--mdir"):
            img_root = arg

    tree = ET.parse(inputfile)
    root = tree.getroot()
    meta = root.find("meta")

    task = meta.find("task")
    taskname = task.find("name")
    if taskname is None:
        taskname = ""
    else:
        taskname = taskname.text

    if outputfile:
        out_json = outputfile
    else:
        json_file_name = taskname if taskname else Path(inputfile).stem
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

    coco_dict = {
        "info": {"description": taskname, "data_created": date_str},
        "annotations": [],
        "categories": [],
        "images": [],
    }

    key_body_labels = ["nose", "", "", "", "" , "leftShoulder","rightShoulder", "leftElbow", "rightElbow", "leftWrist", "rightWrist",
     "leftHip", "rightHip", "leftKnee", "rightKnee", "leftAnkle", "rightAnkle"]

    labels = meta.find("task").find("labels")
    this_cat_id = 2
    cat_name2id = {}
    for label in labels.findall("label"):
        label_name = label.find("name").text
        if label_name in key_body_labels:
            continue
        cat_name2id[label_name] = this_cat_id
        cat_dict = {"id": this_cat_id, "name": label_name, "supercategory": ""}
        this_cat_id += 1
        coco_dict["categories"].append(cat_dict)

    cat_dict = {"id": 1, "name": "person",
    "keypoints": ["nose", "head_bottom", "head_top", "left_ear", "right_ear", "left_shoulder", "right_shoulder",  "left_elbow", "right_elbow",  "left_wrist", "right_wrist", "left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle"],
    "skeleton": [[16, 14], [14, 12], [17, 15], [15, 13], [12, 13], [6, 12], [7, 13], [6, 7], [6, 8], [7, 9], [8, 10], [9, 11], [2, 3], [1, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7]],
    "supercategory": "person"}
    coco_dict["categories"].append(cat_dict)

    img_root = path(img_root, is_dir=True)
    img_paths = get_imgs_from_dir(img_root)
    this_img_id = 1
    img_idx2id = {}
    for i, img_path in enumerate(img_paths):
        w, h = Image.open(img_path).size
        img_idx2id[i] = this_img_id
        img_dict = {
            "id": this_img_id,
            "file_name": str(img_path.relative_to(img_root)),
            "height": h,
            "width": w,
        }
        this_img_id += 1
        coco_dict["images"].append(img_dict)

    this_annot_id = 1

    groupIds = []
    for track_elem in root.findall("track"):
        if ('group_id' in track_elem.attrib):
            group_id = int(track_elem.attrib["group_id"])
            if group_id not in groupIds:
                groupIds.append(group_id)

    for groupId in groupIds:
        for frameIndex in range(start_frame,stop_frame):
            keyPoints = []
            prevLoc = []
            for labelIndex in range(17):
                pointAvailable = False
                for track_elem in root.findall("track"):
                    if (not ('group_id' in track_elem.attrib)) or int(track_elem.attrib["group_id"]) != groupId:
                        continue
                    if key_body_labels[labelIndex] != track_elem.attrib["label"]:
                        continue
                    tid = int(track_elem.attrib["id"])
                    #catid = cat_name2id[track_elem.attrib["label"]]
                    for point_elem in track_elem.findall("points"):
                        if bool(int(point_elem.attrib["outside"])):
                            visibil = 0
                        else:
                            visibil = 1
                        frame_id = int(point_elem.attrib["frame"])
                        if int(frame_id) != frameIndex:
                            continue
                        outside = int(point_elem.attrib["outside"])
                        occluded = bool(int(point_elem.attrib["occluded"]))
                        keyframe = bool(int(point_elem.attrib["keyframe"]))
                        points = point_elem.attrib["points"]
                        locArr = points.split(',')
                        keyPoint = []
                        for loc in locArr:
                            keyPoint.append(float(loc))
                        keyPoint.append(visibil)
                        keyPoints.extend(keyPoint)
                        prevLoc = locArr
                        pointAvailable = True
                if not pointAvailable and len(prevLoc) > 0:
                    print(prevLoc)
                    keyPoint = []
                    for loc in prevLoc:
                        keyPoint.append(float(loc))
                    keyPoint.append(0)
                    keyPoints.extend(keyPoint)


            if img_root is None:
                img_id = 0
            else:
                img_id = img_idx2id[frameIndex - start_frame]
            for track_elem in root.findall("track"):
                if (not ('group_id' in track_elem.attrib)) or int(track_elem.attrib["group_id"]) != groupId:
                    continue
                tid = int(track_elem.attrib["id"])
                label_elem = track_elem.attrib["label"]
                label_name = str(label_elem)
                if label_name in key_body_labels:
                    continue
                catid = cat_name2id[label_elem]
                for box_elem in track_elem.findall("box"):
                    if int(box_elem.attrib["frame"]) != frameIndex:
                            continue
                    if bool(int(box_elem.attrib["outside"])):
                        continue
                    frame_idx = int(box_elem.attrib["frame"])
                    #imgid = img_idx2id[frame_idx - start_frame]
                    imgId = 0
                    occluded = bool(int(box_elem.attrib["occluded"]))
                    keyframe = bool(int(box_elem.attrib["keyframe"]))
                    l = float(box_elem.attrib["xtl"])
                    t = float(box_elem.attrib["ytl"])
                    r = float(box_elem.attrib["xbr"])
                    b = float(box_elem.attrib["ybr"])
                    w = r - l
                    h = b - t
                    annot_dict = {
                        "id": this_annot_id,
                        "image_id": img_id,
                        "frame_id": frameIndex,
                        "category_id": 1,
                        "keypoints": keyPoints,
                        "bbox": [l, t, w, h],
                        "area": w * h,
                        "iscrowd": 0,
                        "attributes": {
                            "occluded": occluded,
                            "track_id":groupId,
                            "keyframe": keyframe,
                        },
                    }
                    this_annot_id += 1
                    coco_dict["annotations"].append(annot_dict)
    write_json(out_json, coco_dict)

def write_json(json_path, dic):
    with open(json_path, "w") as f:
        json.dump(dic, f, indent=2)
    print(f"Wrote json to {json_path}")

#python cvatvid2coco.py -i D:\Autimatic\workspace\transformer\annotations.xml -o D:\Autimatic\workspace\transformer\data_Test.json -m D:\Autimatic\workspace\transformer\images
convert(sys.argv[1:])