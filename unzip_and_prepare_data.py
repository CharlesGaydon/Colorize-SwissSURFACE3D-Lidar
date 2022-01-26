import os, glob
import os.path as osp
import re
from typing import AnyStr
from zipfile import ZipFile
import numpy as np
import pdal, json
from tqdm import tqdm


input_data_dir = "./data/download/"
colorized_data_dir = "./data/colorized/"
splitted_data_dir = "./data/splitted/"

SUBTILE_WIDTH_METERS: int = 50
RASTER_RESOLUTION: str = "0.1"  # either "0.1"or "2" meters

TRAIN_FRAC: float = 0.6
VAL_TEST_FRAC: float = 0.2  # Typically: (1-TRAIN_FRAC)/2


def main():
    # For now assume all las are downloaded a single las subfolder, and that
    # there is a orthos subfolder at the same level.
    las_list = glob.glob(osp.join(input_data_dir, "las", "*.las.zip"))
    np.random.shuffle(sorted(las_list))
    n_las = len(las_list)

    orthos_list = glob.glob(
        osp.join(input_data_dir, "orthos", f"*_{RASTER_RESOLUTION}_*.tif")
    )
    # input_orthos = glob.glob(osp.join(input_data_dir, "orthos", "*_0.1_*.tif"))
    orthos_list = match_all_with_ortho(las_list, orthos_list)
    print(f"Total input las n={n_las}")
    n_orthos = len(orthos_list)
    assert n_orthos == n_las
    print(f"Total input orthos n={n_orthos}")

    n_train = int(TRAIN_FRAC * n_las)
    n_val = int(VAL_TEST_FRAC * n_las)

    train_las_list = las_list[:n_train]
    val_las_list = las_list[n_train : (n_train + n_val)]
    test_las_list = las_list[(n_train + n_val) :]

    las_split_dict = {
        "train": train_las_list,
        "val": val_las_list,
        "test": test_las_list,
    }

    os.makedirs(colorized_data_dir, exist_ok=True)
    os.makedirs(splitted_data_dir, exist_ok=True)
    for phase, las_list in tqdm(las_split_dict.items(), desc="Phases"):
        print(phase)
        for las_path in tqdm(las_list, desc="Files"):
            print(las_path)
            las_id, ortho_path = match_with_ortho(las_path, orthos_list)

            output_las_path = unzip(las_path)

            colorize(output_las_path, ortho_path)

            splitted_las_path = get_splitted_las_path(phase, las_id)
            split(output_las_path, splitted_las_path)


def unzip(las_path):
    """Unzipping the las, returning its unzipped path as well."""
    with ZipFile(las_path, "r") as zipObj:
        for fileName in zipObj.namelist():
            zipObj.extract(fileName, path=colorized_data_dir)
            unziped_las_path = osp.join(colorized_data_dir, fileName)
    return unziped_las_path


def colorize(unziped_las_path: AnyStr, ortho_path: AnyStr):
    """Colorize las using an orthoimage (geotiff), returns colorized las path."""
    _reader = [{"type": "readers.las", "filename": unziped_las_path}]
    # https://pdal.io/stages/filters.colorization.html#filters-colorization
    _colorize = [
        {"type": "filters.colorization", "raster": ortho_path},
    ]
    _writer = [{"type": "writers.las", "filename": unziped_las_path}]
    pipeline = {"pipeline": _reader + _colorize + _writer}
    pipeline = json.dumps(pipeline)
    pipeline = pdal.Pipeline(pipeline)
    pipeline.execute()
    return unziped_las_path


def split(colorized_las_path, splitted_las_path):
    """
    Split data subtiles for training/validation/testing.
    buffer_for_overlap is useful to augment training data.
    """
    _reader = [{"type": "readers.las", "filename": colorized_las_path}]
    _splitter = [
        {
            "type": "filters.splitter",
            "length": SUBTILE_WIDTH_METERS,
        },
    ]
    _writer = [
        {
            "type": "writers.las",
            "filename": splitted_las_path,
            "forward": "all",  # keep all dimensions based on input format
            "extra_dims": "all",  # keep all extra dims as well
        }
    ]
    pipeline = {"pipeline": _reader + _splitter + _writer}
    pipeline = json.dumps(pipeline)
    pipeline = pdal.Pipeline(pipeline)
    pipeline.execute()


def match_all_with_ortho(las_list, orthos_list):
    """Returns the right ortho path based on a list of las paths"""
    matches = []
    for las_path in las_list:
        _, ortho_path = match_with_ortho(las_path, orthos_list)
        matches.append(ortho_path)
    return matches


def match_with_ortho(las_path, orthos_list):
    """Returns the las_id and the associated ortho path"""
    las_id = re.findall(r"[0-9]{4,10}-[0-9]{4,4}", las_path)[0]
    ortho_identifier = f"{las_id.replace('_', '-')}_{RASTER_RESOLUTION}"
    ortho_path = [o for o in orthos_list if ortho_identifier in o][0]
    return las_id, ortho_path


def get_splitted_las_path(phase, las_id):
    """Find the LAS identifier needed to cross las path with orthoimage path"""
    split_name = las_id + "_SUB_#.las"
    splitted_las_path = osp.join(splitted_data_dir, phase, las_id, split_name)
    os.makedirs(osp.dirname(splitted_las_path), exist_ok=True)
    return splitted_las_path


if __name__ == "__main__":
    main()
