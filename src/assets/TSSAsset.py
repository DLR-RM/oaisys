# blender imports
import bpy

# utility imports
import numpy as np
import csv
import random
import importlib

from src.TSSBase import TSSBase
from src.tools.NodeTools import NodeTools

class TSSAsset(TSSBase,NodeTools):
    """docstring for TSSAsset"""
    def __init__(self):
        super(TSSAsset, self).__init__()
        # class vars ###################################################################################################
        ############################################################################################ end of class vars #


    def _reset(self):
        """ reset all local vars
        Args:
            None
        Returns:
            None
        """

        pass


    def _print_msg(self,skk): print("\033[94m {}\033[00m" .format(skk))


    def create(self):
        pass


    def step(self):
        pass