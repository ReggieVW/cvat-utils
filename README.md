# cvat-utils
Utilities for CVAT

# CVAT XML to COCO JSON

Converts CVAT XML to COCO JSON.

## Usage

```bash
usage: cvatxml2coco.py -i <inputfile> -o <outputfile> -m <imageDir>

positional arguments:
  inputfile          Path to CVAT XML
  imageDir           Path to images root directory
  outputfile         Path to COCO JSON

```

## Examples

```bash
python cvatxml2coco.py -i \workspace\cvat-utils\annotations.xml -o \workspace\cvat-utils\out.json -m \workspace\cvat-utils\images\
```


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
