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
python coco2cvatxml.py -i \workspace\cvat-utils\out.json -o \workspace\cvat-utils\annotations.xml
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
python cvatxml2coco.py -i \workspace\cvat-utils\annotations.xml -o \workspace\cvat-utils\out.json -m \workspace\cvat-utils\images\
```

# The Annotations

## key points person
There are 17 key points annotated for each person.
![image](https://user-images.githubusercontent.com/35894891/165474348-1b7f7082-37db-4ff9-8cf8-0b5d3130565a.png)

## COCO JSON
The annotation json file is in the format of MSCOCO dataset and you can use pycoco tools to read the annotations.
There is one annotation file for one video which contains annotations for every frame in that video. 

For the person we have the following annotations:
“track_id”: 1. → the tracking ID of the individual/object, This ID remains constant for that person/object in all the sequences of the video<br />
“image_id”: 56. → This is the frame ID<br />
“bbox”: []. → List of 4 elements denoting the bbox location of that person<br />
“category_id”:1. → this ID 1 is for Human.<br />
“Keypoints”: []. → A list of 51 elements (17x3, for each key point -(x,y,v)) representing the 17 key points location mentioned above. The list is in format [x1,y1,v1,x2,y2,v2………….] , where 1 is first key point, 2 is second keypoint ans so on . For each (x,y,v), v is either 0 or 1. 0 denotes that the key point location is not available.<br />
"activity": ["Punch/slap other person","Stand up"] → actions

