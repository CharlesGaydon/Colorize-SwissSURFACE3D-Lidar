import os, glob
import os.path as osp
import re
from typing import AnyStr
from zipfile import ZipFile
import numpy as np
import pandas as pd
import pdal, json
from tqdm import tqdm


input_data_dir = "./data/download/"
colorized_data_dir = "./data/colorized/"

RASTER_RESOLUTION: str = "0.1"  # either "0.1"or "2" meters

TRAIN_FRAC: float = 0.6
VAL_TEST_FRAC: float = 0.2  # Typically: (1-TRAIN_FRAC)/2


def main():
    # We assume all las are downloaded as zip files in a single folder "las", and
    # that there is an "orthos" folder containing related .tif files at the same level.
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
    df = pd.DataFrame(columns=["basename", "split"])

    os.makedirs(colorized_data_dir, exist_ok=True)
    for phase, las_list in tqdm(las_split_dict.items(), desc="Phases"):
        print(phase)
        for las_path in tqdm(las_list, desc="Files"):
            print(las_path)
            ortho_path = match_single_with_ortho(las_path, orthos_list)
            output_las_path = unzip(las_path)
            colorize(output_las_path, ortho_path)
            df = df.append(
                {
                    "basename": osp.basename(output_las_path),
                    "split": phase,
                },
                ignore_index=True,
            )

    df.to_csv(osp.join(colorized_data_dir, "dataset_split.csv"))


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


def match_all_with_ortho(las_list, orthos_list):
    """Returns the right ortho path based on a list of las paths"""
    matches = []
    for las_path in las_list:
        ortho_path = match_single_with_ortho(las_path, orthos_list)
        matches.append(ortho_path)
    return matches


def match_single_with_ortho(las_path, orthos_list):
    """Returns the las_id and the associated ortho path"""
    las_id = re.findall(r"[0-9]{4,10}-[0-9]{4,4}", las_path)[0]
    ortho_identifier = f"{las_id.replace('_', '-')}_{RASTER_RESOLUTION}"
    ortho_path = [o for o in orthos_list if ortho_identifier in o][0]
    return ortho_path


if __name__ == "__main__":
    main()
