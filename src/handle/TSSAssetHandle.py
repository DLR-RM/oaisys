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
        self._asset_list = []                                       # list of assets [list]
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

    def activate_pass(self,pass_name, pass_cfg, keyframe=-1):
        self._material_handle.activate_pass(pass_name=pass_name,pass_cfg=pass_cfg,keyframe=keyframe)
        self._mesh_handle.activate_pass(pass_name=pass_name,pass_cfg=pass_cfg,keyframe=keyframe)


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
        self._mesh_handle.create(stage_dict=self._stage_handle.get_stage_dict())

        # update stages after meshes applied
        self._stage_handle.update_after_meshes()
