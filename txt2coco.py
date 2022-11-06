'''
@Created By Reginald Van Woensel
@Created Date 13 Apr 2022
@Copyright (c) 2022, AUTIMATIC

Convert TXT with bounding boxes to COCO JSON
'''


import json
from datetime import datetime, date
import argparse

def convert(input_txt_file, output_json_file):
    coco_dict = {}
    date_str = f"{date.today():%Y/%m/%d}"
    coco_dict['info'] = {"description": "extracted from %s" %input_txt_file, "data_created": date_str}
    coco_dict['categories'] = [{"id": 1, "name": "person", "supercategory": ""}]
    coco_dict['annotations'] = []
    
    with open(input_txt_file, "r") as filestream:
        annotation_id = 0
        for line in filestream:
            currentline = line.split(",")
            dict_obj = {
                    'track_id': int(currentline[1]),
                    'frame_id': int(currentline[0]),
                    'keypoints': [],
                    'bbox': [float(currentline[2]), float(currentline[3]), float(currentline[4]), float(currentline[5])],
                    'activity': [],
                    'category_id': 1
                }
            coco_dict['annotations'].append(dict_obj)
            annotation_id += 1

    with open(output_json_file, "w") as fobj:
        json.dump(coco_dict, fobj, indent=2)
        print(f"Wrote json to {output_json_file}")


def parse_args():
    """Parse arguments of command line"""
    parser = argparse.ArgumentParser(
        description='Convert TXT to COCO annotations'
    )
    parser.add_argument(
        '--input-txt-file', metavar='FILE', required=True,
        help='Input TXT file'
    )
    parser.add_argument(
        '--output-json-file', metavar='FILE', required=True,
        help='Output JSON file'
    )
    return parser.parse_args()

def main(): 
    args = parse_args()
    convert(args.input_txt_file, args.output_json_file)


if __name__ == '__main__':
    main()