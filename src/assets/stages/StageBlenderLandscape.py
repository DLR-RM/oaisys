# blender imports
import bpy
import addon_utils

# utility imports
import numpy as np
import csv
import random
import importlib
import os
import inspect
import json

from src.assets.TSSStage import TSSStage

class StageBlenderLandscape(TSSStage):
    """docstring for StageBlenderLandscape"""
    def __init__(self):
        super(StageBlenderLandscape, self).__init__()
        # class vars ###################################################################################################
        self._single_stage = None                               # blender stage objcet [blObject]
        ############################################################################################ end of class vars #

        # import Another Noise Tool ####################################################################################
        try:
            addon_utils.enable('ant_landscape')
        except ImportError:
            # manage import error
            raise Exception("Cannot load landscape module")
            return -1
        ############################################################################# end of import Another Noise Tool #


    def reset(self):
        """ reset all local vars
        Args:
            None
        Returns:
            None
        """

        self._single_stage = None


    def update_after_meshes(self):
        """ update function after mesh placements
        Args:
            None
        Returns:
            None
        """

        # add sub surf modifier ########################################################################################
        self._single_stage.modifiers.new("lastSubsurf", type='SUBSURF')
        self._single_stage.cycles.use_adaptive_subdivision = True # TODO:maybe shift this to higher level
        ################################################################################# end of add sub surf modifier #


    def _get_random_number(self,min_max_array):
        """ get random number from array; use uniformal distribution
        Args:
            min_max_array:      define min and max value [min_value, max_value] [float,float]; if just one value is
                                added to list, the same value is returned
        Returns:
            return random value [float]
        """

        # check length of array and caluclate random number ############################################################
        if len(min_max_array) > 1:
            if min_max_array[1] >= min_max_array[0]:
                return random.uniform(min_max_array[0],min_max_array[1])
            else:
                raise Exception("[StageBlenderLandscape] Max >=! Min!")
        else:
            return min_max_array[0]
        ##################################################### end of check length of array and caluclate random number #


    def _prepare_landscape_cfg(self, cfg):
        """ prepare ant arguments
        Args:
            cfg:                cfg dict which contains the meta arguments for ant [dict]
        Returns:
            _landscape_cfg:     cfg dict which contains ant arguments [dict]
        """

        # cfg
        _landscape_cfg = {}
        _landscape_params = {}

        # general settings #############################################################################################
        if "stageLandscapePreset" in cfg:
            # compile default cfg path #################################################################################
            _default_cfg_path = os.path.join(os.path.dirname(inspect.getfile(self.__class__)),"default_cfg")
            _default_cfg_path = os.path.join(_default_cfg_path,cfg["stageLandscapePreset"]+".json")
            ########################################################################## end of compile default cfg path #

            # load default cfg file ####################################################################################
            if os.path.isfile(_default_cfg_path):
                with open(_default_cfg_path, 'r') as f:
                    _landscape_params = json.load(f)
            ############################################################################# end of load default cfg file #
        else:
            _landscape_cfg["refresh"] = True
            _landscape_cfg["mesh_size_x"] = 2.0
            _landscape_cfg["mesh_size_y"] = 2.0

        _landscape_cfg["ant_terrain_name"] = cfg["stageName"]
        ###################################################################################### end of general settings #

        # update params
        _landscape_params.update(cfg["landscapeParams"])

        # go through dict and set cfg ##################################################################################
        for key, value in _landscape_params.items():
            # check if all items in list are the same items
            for element in value:
                if not isinstance(element, type(value[0])):
                    raise Exception("[StageBlenderLandscape] Elements in list must be from same type!")

            # check if items of value are numbers or strings
            if type(element) == int or float:
                # value is a number -> choose radom sample between value[0] and value [1]
                _landscape_cfg[key] = self._get_random_number(value)
            else:
                _landscape_cfg[key] = radnom.choice(value)
        ########################################################################### end of go through dict and set cfg #

        # return cfg dict
        return _landscape_cfg


    def _create_single_stage(self):
        """ create landscape stage
        Args:
            None
        Returns:
            None
        """

        # def local vars ###############################################################################################
        self._single_stage = None
        ######################################################################################## end of def local vars #

        # create terrain ###############################################################################################
        # prepare cfg file for ant
        _landscape_cfg = self._prepare_landscape_cfg(self._cfg)

        # create landscape with ant
        bpy.ops.mesh.landscape_add(**_landscape_cfg)

        # get handle to created terrain
        self._single_stage = bpy.context.scene.objects.get(_landscape_cfg["ant_terrain_name"])
        ######################################################################################## end of create terrain #

        # resize terrain ###############################################################################################
        if "stageSizeX" in self._cfg:
            _mesh_size_x = _landscape_cfg["mesh_size_x"]
            _scaling_fac = self._cfg["stageSizeX"]/_mesh_size_x
            self._single_stage.scale = (_scaling_fac, _scaling_fac, _scaling_fac)

            # apply scale and roation
            bpy.context.view_layer.objects.active = self._single_stage
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        ######################################################################################## end of resize terrain #        

        # update stage var
        self._stage = self._single_stage


    def create(self):
        """ create function
        Args:
            None
        Returns:
            None
        """

        print(self._cfg)

        self._create_single_stage()