# blender imports
import bpy

# utility imports
import numpy as np
import csv
import random
import importlib

from src.TSSBase import TSSBase


class TSSStageHandle(TSSBase):
    """docstring for TSSStageHandle"""

    def __init__(self):
        super(TSSStageHandle, self).__init__()
        # class vars ###################################################################################################
        self._stage_list = []  # list of stage [list]
        self._stage_obj_list = []  # list of stage nodes [list]
        self._stage_dict = {}  # dict of stages [dict]
        ############################################################################################ end of class vars #

    def reset_module(self):
        """ reset all local vars
        Args:
            None
        Returns:
            None
        """

        # reset all stages ############################################################################################
        for stage in self._stage_obj_list:
            # reset sensor
            stage.reset_module()

            # maybe obsolete in future versions
            del stage
        ##################################################################################### end of reset all stages #

        self.reset_base()
        self._stage_list = []
        self._stage_obj_list = []
        self._stage_dict = {}

    def create(self, materials):
        """ create function
        Args:
            materials:          list of all materials [list]
        Returns:
            None
        """

        self._create_stages(cfg=self._cfg["STAGES"],
                            general_cfg=self._cfg["GENERAL"],
                            materials=materials)

    def update_after_meshes(self):
        """ update mesh function
        Args:
            None
        Returns:
            None
        """

        for stage in self._stage_obj_list:
            stage.update_after_meshes()

    def _create_stages(self, cfg, general_cfg, materials):
        """ create function
        Args:
            cfg:            list of stage cfgs [list]
            general_cfg:    general cfg [dict]
            materials:      list of all materials [list]
        Returns:
            None
        """

        for ii, stage in enumerate(cfg):
            try:
                # import module and create class #######################################################################
                _module_name = "src.assets.stages." + stage["type"]
                _module = importlib.import_module(_module_name)
                _class = getattr(_module, stage["type"])
                _stage = _class()
                ################################################################ end of import module and create class #

                # set pass params and create pass ######################################################################
                # set general cfg
                _stage.set_general_cfg(cfg=general_cfg)

                # save name of stage
                stage["stageParams"]['name'] = stage["name"]

                # update stage cfg
                _stage.update_cfg(cfg=stage["stageParams"])

                # create material
                _stage.create()

                # return desired material
                _material = _stage.get_desired_material()
                ############################################################### end of set pass params and create pass #

                if _material:
                    if _material in materials:
                        _stage.apply_material(material=materials[_material])
                    else:
                        raise Exception("Material not found!")

                # add pass to list
                self._stage_obj_list.append(_stage)
                self._stage_list.append(_stage.get_stage())
                self._stage_dict[stage["name"]] = _stage.get_stage()



            except ImportError:
                # manage import error
                raise Exception("Cannot add stage")
                return -1

        return 0

    def get_stages(self):
        """  get all stages
        Args:
            None
        Returns:
            list of stage [list]
        """

        return self._stage_list

    def get_stage_objs(self):
        """  get all stage objects
        Args:
            None
        Returns:
            list of stage objects [list]
        """

        return self._stage_obj_list

    def get_stage_dict(self):
        """  get all stage dict
        Args:
            None
        Returns:
            list of stage dict [dict]
        """

        return self._stage_dict

    def activate_pass(self, pass_name, pass_cfg, keyframe=-1):
        """ enables specific pass
        Args:
            pass_name:      name of pass to activate [string]
            pass_cfg:       specific parameters for the pass [dict]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        for stage in self._stage_obj_list:
            stage.activate_pass(pass_name=pass_name, pass_cfg=pass_cfg, keyframe=keyframe)

    def set_log_folder(self, log_folder_path):
        for stage_obj in self._stage_obj_list:
            stage_obj.set_log_folder(log_folder_path)

    def step(self, keyframe):
        """ step handle and modules
        Args:
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        self._stepping_counter += 1

        # step for modules #############################################################################################
        for stage_obj in self._stage_obj_list:

            _trigger_option = stage_obj.get_trigger_type()

            if "GLOBAL" == _trigger_option:
                if (self._stepping_counter % self._trigger_interval) == 0:
                    stage_obj.step_module(keyframe=keyframe)

            if "LOCAL" == _trigger_option:
                stage_obj.step_module(keyframe=keyframe)
        ###################################################################################### end of step for modules #
