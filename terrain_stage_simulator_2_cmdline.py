# blender imports
import bpy

# system imports
import json


import sys
import os
import pathlib

# import files from TSS
import src.tools.cfgParser
import src.TSS_simulation_online as TSSStageSimulator

from bpy.types import (
    AddonPreferences,
    Operator,
    Panel,
    PropertyGroup,
)

import argparse

# utility imports
import numpy as np

if __name__ == "__main__":
    
    import sys
    argv = sys.argv

    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--") + 1:]  # get all args after "--"

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', required=False, help="config json file.")
    args = parser.parse_args(argv)
    _configPath = args.c

    # setup stage simulator
    stage_simulator = TSSStageSimulator.TSS_OP_CStageSimulator()
    stage_simulator.execute(_configPath)

