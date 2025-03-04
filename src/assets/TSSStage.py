# blender imports
import bpy

# utility imports
import numpy as np
import csv
import random
import importlib

from src.assets.TSSAsset import TSSAsset
from src.assets.TSSModifieres import TSSModifieres

class TSSStage(TSSAsset,TSSModifieres):
    """docstring for TSSStage"""
    def __init__(self):
        super(TSSStage, self).__init__()
        # class vars ###################################################################################################
        self._stage = None
        self._num_instance_label_per_channel = 51
        self._num_labels_per_channel = 51
        ############################################################################################ end of class vars #


    def reset_module(self):
        """ reset all local vars
        Args:
            None
        Returns:
            None
        """

        self.reset_base()

        self._stage = None

        self.reset()


    def update_after_meshes(self):
        pass


    def apply_material(self,material):
        self._stage.data.materials.clear()
        self._stage.active_material = material


    def set_stage(self,stage):
        self._stage = stage

    def get_desired_material(self):
        """ get desired material
        Args:
            None
        Returns:
            desired material name [str]
        """
        if "assetMaterial" in self._cfg:
            return self._cfg["assetMaterial"]
        else:
            return None

    def get_stage(self):
        return self._stage


    def create(self):
        pass


    def step(self, keyframe):
        pass