# blender imports
import bpy

# utility imports
import numpy as np
import csv
import random
import importlib

from src.assets.TSSAsset import TSSAsset
from src.assets.TSSModifieres import TSSModifieres

class TSSMesh(TSSAsset,TSSModifieres):
    """docstring for TSSMesh"""
    def __init__(self):
        super(TSSMesh, self).__init__()
        # class vars ###################################################################################################
        self._stage_list = []
        self._stage_dict = {}
        self._node_tree = None
        self._num_labels_per_channel = 51
        self._num_instance_label_per_channel = 51
        ############################################################################################ end of class vars #


    def reset_module(self):
        """ reset all local vars
        Args:
            None
        Returns:
            None
        """

        self.reset()
        self.reset_base()

        self._stage_list = []
        self._stage_dict = {}
        self._node_tree = None


    def reset(self):
        pass
        

    def create(self):
        pass


    def step(self, keyframe):
        pass


    def set_stages(self,stages):
        self._stage_list = stages


    def set_stage_dict(self,stage_dict):
        self._stage_dict = stage_dict


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
            self._set_keyframe_interpolation(node_tree=self._node_tree,interpolation='CONSTANT')