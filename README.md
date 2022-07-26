# CVAT UTILS
Utilities for CVAT

# COCO JSON to CVAT XML

Converts COCO JSON to CVAT XML.

## Usage

```bash
usage: coco2cvatxml.py [-h] --coco FILE --cvat-xml FILE 

positional arguments:
  coco             Path to COCO JSON
  cvat-xml         Path to CVAT XML

```

## Examples

```bash
python coco2cvatxml.py --coco task_1.json --cvat-xml annotations.xml
```

# CVAT XML to COCO JSON

Converts CVAT XML to COCO JSON.

## Usage

```bash
usage: cvatxml2coco.py [-h] --cvat-xml FILE [--image-dir DIRECTORY] --coco FILE

positional arguments:
  cvat-xml          Path to CVAT XML
  coco              Path to COCO JSON
  image-dir         Path to images root directory (optional)

```

## Examples

```bash
python cvatxml2coco.py --cvat-xml annotations.xml --coco out.json --image-dir \images\
```

# The Annotations

## key points person
There are 17 key points.


## COCO JSON
The annotation json file is in the format of MSCOCO dataset and is a collection of “info”, “images”, “annotations”, “categories”. There is one annotation file for one video which contains the annotations from the frames in the video. 

```bash
{
    "info": {...},
    "images": [...],
    "annotations": [...],
    "categories": [...], 
}
```

For the person object we have the following annotations:<br />
```bash
annotations:[{
  "id"           : int, → Each annotation also has an id (unique to all other annotations).
  "category_id"  : 1 → This ID 1 is for Human.
  "bbox"         : [top left x position, top left y position, width, height], → Denoting the bbox location of that person. Box coordinates are measured from the top left image corner and are 0-indexed.
  "keypoints"    : [x1,y1,v1,x2,y2,v2...], → x and y indicate pixel positions in the image. v indicates visibility— v=0: not labeled (in which case x=y=0), v=1: labeled but not visible, and v=2: labeled and visible.
  "track_id"    : int, → The tracking ID of the individual, This ID remains constant for that person/object in all the sequences of the video.
  "image_id"    : int, 
  "frame_id"    : int, → The frame id of this frame in the video.
  "activity"    : [action1,action2...] → The person's actions which are captured.
}]

"categories": [{
  supercategory": "person",
  "id": 1,
  "name": "person",
  "keypoints": [ "nose", "left_eye", "right_eye", "left_ear", "right_ear", "left_shoulder", "right_shoulder", "left_elbow", "right_elbow", "left_wrist", "right_wrist", "left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle" ], 
  "skeleton" = [[15, 13], [13, 11], [16, 14], [14, 12], [11, 12],
                        [5, 11], [6, 12], [5, 6], [5, 7], [6, 8], [7, 9],
                        [8, 10], [1, 2], [0, 1], [0, 2], [1, 3], [2, 4],
                        [3, 5], [4, 6]]→ defines connectivity
  "actions":["stand up"],["sit down"],["falling down"],["punch/slap other person"],["kicking other person"],["pushing other person"],...
}]
```


