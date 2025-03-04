# blender imports
import bpy

# utility imports
import numpy as np
import csv
import random
import importlib

from src.TSSBase import TSSBase
from src.assets.handle.TSSMaterialHandle import TSSMaterialHandle
from src.assets.handle.TSSStageHandle import TSSStageHandle
from src.assets.handle.TSSMeshHandle import TSSMeshHandle


class TSSAssetHandle(TSSBase):
    """docstring for TSSAssetHandle"""

    def __init__(self):
        super(TSSAssetHandle, self).__init__()
        # class vars ###################################################################################################
        self._asset_list = []  # list of assets [list]
        self._material_handle = None
        self._stage_handle = None
        self._mesh_handle = None
        ############################################################################################ end of class vars #

    def reset_module(self):
        """ reset all local vars
        Args:
            None
        Returns:
            None
        """

        self._material_handle.reset_module()
        self._stage_handle.reset_module()
        self._mesh_handle.reset_module()

        self.reset_base()

        # reset vars ###################################################################################################
        self._asset_list = []
        self._material_handle = None
        self._stage_handle = None
        self._mesh_handle = None
        ############################################################################################ end of reset vars #

    def activate_pass(self, pass_name, pass_cfg, keyframe=-1):
        self._material_handle.activate_pass(pass_name=pass_name, pass_cfg=pass_cfg, keyframe=keyframe)
        self._mesh_handle.activate_pass(pass_name=pass_name, pass_cfg=pass_cfg, keyframe=keyframe)
        self._stage_handle.activate_pass(pass_name=pass_name, pass_cfg=pass_cfg, keyframe=keyframe)

    def get_stages(self):
        return self._stage_handle.get_stage_dict()

    def create(self):
        # create materials
        self._material_handle = TSSMaterialHandle()
        self._material_handle.update_cfg(cfg=self._cfg)
        self._material_handle.create()

        # create stages
        self._stage_handle = TSSStageHandle()
        self._stage_handle.update_cfg(cfg=self._cfg)
        self._stage_handle.create(materials=self._material_handle.get_materials())

        # create object assets / meshes
        self._mesh_handle = TSSMeshHandle()
        self._mesh_handle.update_cfg(cfg=self._cfg)
        _meshes = self._mesh_handle.create(stage_dict=self._stage_handle.get_stage_dict(),
                                 materials=self._material_handle.get_materials())

        # update stages after meshes applied
        self._stage_handle.update_after_meshes()

        return _meshes

    def step(self, keyframe=-1):
        """ step handle and modules
        Args:
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        self._material_handle.step(keyframe=keyframe)
        self._stage_handle.step(keyframe=keyframe)
        self._mesh_handle.step(keyframe=keyframe)

    def log_step(self, keyframe):
        """ log step function is called for every new sample in of the batch; should be overwritten by custom class
            OVERWRITE!
        Args:
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        self._material_handle.log_step(keyframe=keyframe)
        self._stage_handle.log_step(keyframe=keyframe)
        self._mesh_handle.log_step(keyframe=keyframe)

    def set_log_folder(self, log_folder_path):
        self._material_handle.set_log_folder(log_folder_path)
        self._stage_handle.set_log_folder(log_folder_path)
        self._mesh_handle.set_log_folder(log_folder_path)
