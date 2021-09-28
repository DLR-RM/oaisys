# blender imports
import bpy

# utility imports
import numpy as np
import csv
import random
import importlib

from src.TSSBase import TSSBase

class TSSMaterialHandle(TSSBase):
    """docstring for TSSMaterialHandle"""
    def __init__(self):
        super(TSSMaterialHandle, self).__init__()
        # class vars ###################################################################################################
        self._material_dict = {}                                            # list of materials [list]
        self._material_obj_list = []                                        # list of materials nodes [list]
        ############################################################################################ end of class vars #


    def _reset(self):
        """ reset all local vars
        Args:
            None
        Returns:
            None
        """

        pass
        

    def activate_pass(self,pass_name, pass_cfg, keyframe=-1):
        for material in self._material_obj_list:
            material.activate_pass(pass_name=pass_name,pass_cfg=pass_cfg,keyframe=keyframe)

    def create(self):
        self._create_materials(cfg=self._cfg["MATERIALS"],
                                general_cfg=self._cfg["GENERAL"])



    def _create_materials(self,cfg,general_cfg):

        for ii, material in enumerate(cfg):
            try:
                # import module and create class #######################################################################
                _module_name = "src.assets.materials." + material["type"]
                _module = importlib.import_module(_module_name)
                _class = getattr(_module, material["type"])
                _material = _class()
                ################################################################ end of import module and create class #

                # set pass params and create pass ######################################################################
                # set general cfg
                _material.set_general_cfg(cfg=general_cfg)

                # save name of material
                material["materialParams"]['name'] = material["name"]

                # update sensor cfg
                _material.update_cfg(cfg=material["materialParams"])

                # create material
                _material.create()
                ############################################################### end of set pass params and create pass #
                
                # add pass to list
                self._material_obj_list.append(_material)
                self._material_dict[material["name"]] = _material.get_material()

            except ImportError:
                # manage import error
                raise Exception("Cannot add material")
                return -1


        return 0


    def get_materials(self):
        return self._material_dict


    def get_material_objs(self):
        return self._material_obj_list
