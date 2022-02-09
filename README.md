# Merge SwissTopo Surface3D (aerial Lidar) and SwissImage10 (orthoimages) data


## Goal 
This code gives an example for obtaining _colorized_ point cloud dataset out of two SwissTopo sources:
- [SwissSurface3D](https://www.swisstopo.admin.ch/fr/geodata/height/surface3d.html): an aerial Lidar database, with the following highly accurate classification - Unclassified|Ground|Building|Vegetation|Bridges&Viaducs|Water
- [SwissImage10](https://www.swisstopo.admin.ch/en/geodata/images/ortho/swissimage10.html): an orthoimage database, with 10cm resolution.

The data comes in the form of 1km² square tiles, in CH1903+ / LV95 (EPSG:2056) CRS. See linked website for full documentation.

Running `unzip_and_prepare_data.py` (see below for instructions) will produce the following:

- Tiles separated into train, validation, and test sets (see `TRAIN_FRAC` and `VAL_TEST_FRAC` for their size), as documented in a csv file.
- Unziped point cloud with color information in `colorized/train/`, `colorized/val/`, and `colorized/test/` subfolders (see `RASTER_RESOLUTION` to choose color resolution among 2m and 0.1m).

## Process

### 1. Select you data
How to select data and download on SwissTopo website is explained [here (EN)](https://www.swisstopo.admin.ch/en/geodata/info.html) and [here (FR)])[https://www.swisstopo.admin.ch/fr/geodata/info.html].
Overall, the idea is to download point clouds (`.las` files) in the `./data/download/las/` folder, and orthoimages (`.tif` files) in the `./data/download/ortho/`.

SwissSurface3D: [Selection and download page](https://www.swisstopo.admin.ch/fr/geodata/height/surface3d.html)
SwissImage10: [Selection and download page](https://www.swisstopo.admin.ch/en/geodata/images/ortho/swissimage10.html)

Select your area of interest, click on "Export all links", and save as a `.csv` file with a meaningful name (e.g. `DATE_AREA_SwissIMAGE10cm_Links_LV95.csv` for orthoimages and `DATE_AREA_SwissSURFACE3D_Links_LV95.csv`).

Such files for the area of Lausanne are given under `./download_links/20220110_Lausanne` as an example.

Assumptions of filename convention:
- Download point cloud are expected to have filename format `swisssurface3d_YEAR_{X}-{Y}_2056_5728.las.zip`
- Downloaded orthoimages rasters are expected to have filename format `swissimage-dop10_YEAR_{X}-{Y}_0.1_2056`

XY pairs will be used to match point clouds with orthoimages and are expected to be unique. 

### 2. Download SwissSurface3D data

```
    wget --directory-prefix=./download/orthos/ --input-file=DATE_AREA_SwissIMAGE10cm_Links_LV95.csv
    wget --directory-prefix=./download/las/ --input-file=DATE_AREA_SwissSURFACE3D_Links_LV95.csv
```
### 3. Make a train/val/test split and colorize

In a virtual environment, you will need `pdal` (for installation see [here](https://pdal.io/quickstart.html) and [here](https://opensourceoptions.com/blog/install-pdal-for-python-with-anaconda/)) and `numpy` to be installed. Code was run using python `3.9` and PDAL `3.0.2`.

Activate the environement, then run:

```
    python unzip_and_colorize.py
```
There are a few harcoded arguments you can parameter in `unzip_and_prepare_data.py`.


