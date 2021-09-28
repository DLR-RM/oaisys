import numpy as np
from numpy import save
import os
import fnmatch
import sys
import cv2
from PIL import Image
import time
import glob

import argparse
from math import floor, ceil

from default_config import get_cfg_defaults
from coco_config import get_cfg_coco
from hdf5_config import get_cfg_hdf5

np.set_printoptions(threshold=sys.maxsize)


def get_config():
    parser = argparse.ArgumentParser(
        description="TerrainStageSimulator tool for data conversion"
    )
    parser.add_argument(
        "--config-file",
        default="",
        metavar="FILE",
        help="path to config file",
        type=str,
    )

    parser.add_argument(
        "opts",
        help="Modify config options using the command-line",
        default=None,
        nargs=argparse.REMAINDER,
    )
    args = parser.parse_args()

    cfg = get_cfg_defaults()

    cfg.merge_from_list(args.opts)

    if cfg.FORMAT == 'coco':
        cfg.merge_from_other_cfg(get_cfg_coco())
    elif cfg.FORMAT == 'hdf5':
        cfg.merge_from_other_cfg(get_cfg_hdf5())

    if args.config_file:
        cfg.merge_from_file(args.config_file)
    else:
        print("WARNING: No config file to merge")

    cfg.freeze()

    return cfg

def convert_yacs2dict(cfg):
    """ converts yacs config format into internally used dictionary format

    Args:
        cfg: yacs config file

    Returns:
        dictionary with config entries
    """
    _cfg_out = {
        "height": cfg.OUT.HEIGHT,
        "width": cfg.OUT.WIDTH,
        "num_channels": cfg.OUT.NUM_CHANNELS,
        "base_path": cfg.OUT.BASE_PATH,
        "out_path": cfg.OUT.OUT_PATH,
        "data_def": cfg.OUT.DATA_DEF
    }
    return _cfg_out

if __name__ == "__main__":
    cfg = get_config()

    if cfg.FORMAT  == "hdf5":
        from hdf5_writer import HDF5Processor

        d_proc = HDF5Processor(cfg) # create one instance of hdf5-processor

    elif cfg.FORMAT == "coco":
        from coco_writer import CocoProcessor

        d_proc = CocoProcessor(cfg) # create one instance of coco-processor
    else:
        print(f" the FORMAT flag is not set or a wrong format is chosen")
        raise NotImplementedError()

    # process data and save it
    d_proc.run()

