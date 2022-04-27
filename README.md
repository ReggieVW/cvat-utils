# cvat-utils
Utilities for CVAT

# COCO JSON to CVAT XML

Converts COCO JSON to CVAT XML.

## Usage

```bash
usage: coco2cvatxml.py -i <inputfile> -o <outputfile>

positional arguments:
  inputfile          Path to COCO JSON
  outputfile         Path to CVAT XML

```

## Examples

```bash
python coco2cvatxml.py -i task_1.json -o annotations.xml
```

# CVAT XML to COCO JSON

Converts CVAT XML to COCO JSON.

## Usage

```bash
usage: cvatxml2coco.py -i <inputfile> -o <outputfile> -m <imageDir>

positional arguments:
  inputfile          Path to CVAT XML
  outputfile         Path to COCO JSON
  imageDir           Path to images root directory (optional)

```

## Examples

```bash
python cvatxml2coco.py -i annotations.xml -o out.json -m \images\
```

# The Annotations

## key points person
There are 17 key points annotated for each person.
![image](https://user-images.githubusercontent.com/35894891/165474348-1b7f7082-37db-4ff9-8cf8-0b5d3130565a.png)

## COCO JSON
The annotation json file is in the format of MSCOCO dataset. You can use pycoco tools to read the annotations.
There is one annotation file for one video which contains the annotations from the frames in the video. 

For the person we have the following annotations:<br />
```bash
annotation{
  "id"           : int, → Each annotation also has an id (unique to all other annotations)
  "bbox"         : [x,y,width,height], → Denoting the bbox location of that person. Box coordinates are measured from the top left image corner and are 0-indexed<br />
  "keypoints"    : [x1,y1,v1,x2,y2,v2...], → x and y indicate pixel positions in the image. v indicates visibility— v=0: not labeled (in which case x=y=0), v=1: labeled but not visible, and v=2: labeled and visible <br />
  "track_id"    : int, → The tracking ID of the individual/object, This ID remains constant for that person/object in all the sequences of the video<br />
  "image_id"    : int, 
  "frame_id"    : int, → the frame id of this frame in this video
  "activity"    : [action1,action2...] → actions
  "category_id" :1 → this ID 1 is for Human.<br />
}

categories[{
  supercategory": "person",
  "id": 1,
  "name": "person",
  "keypoints": ["nose","left_eye","right_eye","left_ear","right_ear","left_shoulder","right_shoulder","left_elbow","right_elbow","left_wrist","right_wrist",
  "left_hip","right_hip","left_knee","right_knee","left_ankle","right_ankle"], 
  "skeleton": [16,14],[14,12],[17,15],[15,13],[12,13],[6,12],[7,13],[6,7],[6,8],[7,9],[8,10],[9,11],[2,3],[1,2],[1,3],[2,4],[3,5],[4,6],[5,7], → defines connectivity                 via a list of keypoint edge pairs 
}]
```


