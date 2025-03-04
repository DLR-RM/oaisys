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


    def reset_module(self):
        """ reset all local vars
        Args:
            None
        Returns:
            None
        """

        # reset all sensors ############################################################################################
        for material in self._material_obj_list:
            # reset sensor
            material.reset_module()

            # maybe osbolete in future versions
            del material
        ##################################################################################### end of reset all sensors #

        self.reset_base()

        # reset vars ###################################################################################################
        self._material_dict = {}
        self._material_obj_list = []
        ############################################################################################ end of reset vars #


    def activate_pass(self,pass_name, pass_cfg, keyframe=-1):
        """ activate pass function
        Args:
            pass_name:      name of pass to activate [string]
            pass_cfg:       specific parameters for the pass [dict]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """
        for material in self._material_obj_list:
            material.activate_pass(pass_name=pass_name,pass_cfg=pass_cfg,keyframe=keyframe)


    def create(self):
        """ create function
        Args:
            None
        Returns:
            None
        """
        self._create_materials(cfg=self._cfg["MATERIALS"],
                                general_cfg=self._cfg["GENERAL"])



    def _create_materials(self, cfg, general_cfg):
        """ create function
        Args:
            cfg:                cfg list of material modules [list]
            general_cfg:        general cfg [dict]
        Returns:
            success code [boolean]
        """

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
        """ return all materials
        Args:
            None
        Returns:
            dict of materials [dict]
        """
        return self._material_dict


    def get_material_objs(self):
        """ get material objects
        Args:
            None
        Returns:
            list of material objects [list]
        """
        return self._material_obj_list

    def set_log_folder(self, log_folder_path):
        for material_obj in self._material_obj_list:
            material_obj.set_log_folder(log_folder_path)

    def step(self, keyframe):
        """ step handle and modules
        Args:
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        self._stepping_counter += 1

        # step for modules #############################################################################################
        for material_obj in self._material_obj_list:

            _trigger_option = material_obj.get_trigger_type()

            if "GLOBAL" == _trigger_option:
                if (self._stepping_counter % self._trigger_interval) == 0:
                    material_obj.step_module(keyframe=keyframe)

            if "LOCAL" == _trigger_option:
                material_obj.step_module(keyframe=keyframe)
        ###################################################################################### end of step for modules #