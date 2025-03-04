# blender imports
import bpy

# utility imports
import numpy as np
import csv
import random
import importlib

from src.assets.TSSAsset import TSSAsset
from src.assets.TSSModifieres import TSSModifieres

class TSSMaterial(TSSAsset,TSSModifieres):
    """docstring for TSSMaterial"""
    def __init__(self):
        super(TSSMaterial, self).__init__()
        # class vars ###################################################################################################
        self._material = None
        self._node_tree = None
        self._num_labels_per_channel = 51
        ############################################################################################ end of class vars #


    def reset_module(self):
        """ reset all local vars
        Args:
            None
        Returns:
            None
        """

        self._material = None
        self._node_tree = None

        self.reset()


    def set_material(self,material):
        self._material = material


    def get_material(self):
        return self._material


    def create(self):
        pass


    def step(self, keyframe):
        pass


    def additional_pass_action(self,pass_name, pass_cfg, keyframe):
        """ overwrite base function
        Args:
            pass_name:      name of pass to activate [string]
            pass_cfg:       specific parameters for the pass [dict]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        if keyframe > -1:
            # set interpolation to constant ############################################################################
            self._set_keyframe_interpolation(node_tree=self._node_tree,interpolation='CONSTANT')