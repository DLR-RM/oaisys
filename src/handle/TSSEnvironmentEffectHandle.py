# blender imports
import bpy

# utility imports
import numpy as np
import random

# system imports
import sys
import os
import pathlib
import importlib
from datetime import datetime

class TSSEnvironmentEffectHandle(object):
    """docstring for TSSEnvironmentEffectHandle"""
    def __init__(self):
        super(TSSEnvironmentEffectHandle, self).__init__()
        # class vars ###################################################################################################
        self._effect_list = []
        self._cfg = {}
        self._trigger_interval = 1000          # interval of triggering [uint]
        self._stepping_counter = 0          # counter which counts how often stepping function is executed [uint]
        self._background_strength = [1,1]
        self._tree = None
        ############################################################################################ end of class vars #


    def reset_module(self):
        """ reset all local vars
        Args:
            None
        Returns:
            None
        """

        # reset all effect ############################################################################################
        for effect in self._effect_list:
            # reset effect
            effect.reset_module()

            # maybe osbolete in future versions
            del effect
        ##################################################################################### end of reset all effect #

        # reset vars ###################################################################################################
        self._effect_list = []
        self._trigger_interval = 1000
        self._stepping_counter = 0
        self._background_strength = [1,1]
        self._tree = None
        ############################################################################################ end of reset vars #


    def _create_effects(self,cfg,general_cfg,world_node_tree,render_layers_node):

        _output_node = None

        for ii, effect in enumerate(cfg):
            try:
                # import module and create class #######################################################################
                _module_name = "src.environment_effects.effects." + effect["type"]
                _module = importlib.import_module(_module_name)
                _class = getattr(_module, effect["type"])
                _effect = _class()
                ################################################################ end of import module and create class #
                # set pass params and create pass ######################################################################
                # set general cfg
                _effect.set_general_cfg(cfg=general_cfg)

                # update sensor cfg
                _effect.update_cfg(cfg=effect["environmentEffectsParams"])
                
                # set node offset for organized node tree
                _effect.set_node_offset(node_offset=[-100,-1500*ii])

                # set node tree handle
                _effect.set_world_node_tree(world_node_tree=world_node_tree)

                # set render layer nodes
                _effect.set_render_layers_node(render_layers_node=render_layers_node)

                # create pass
                _output_node = _effect.create(last_element=_output_node)
                ############################################################### end of set pass params and create pass #
                
                # add pass to list
                self._effect_list.append(_effect)

            except ImportError:
                # manage import error
                raise Exception("Cannot add effect")
                return -1

        # connect last output node to inout of world output
        if _output_node is not None:
            world_node_tree.node_tree.links.new(world_node_tree.node_tree.nodes["Background"].inputs[0],_output_node)

        return 0


    def get_render_pass_list(self):

        return self._pass_list


    def update_cfg(self,cfg):
        """ set cfg dict for object
            DO NOT OVERWRITE!
        Args:
            cfg:            cfg dict of class [dict]
        Returns:
            None
        """

        self._cfg = cfg

        if "stepInterval" in self._cfg:
            self._trigger_interval = self._cfg["stepInterval"]


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
            return random.uniform(min_max_array[0],min_max_array[1])
        else:
            return min_max_array[0]
        ##################################################### end of check length of array and caluclate random number #

        
    def create(self):
        """ create function
        Args:
            None
        Returns:
            None
        """

        # save data fro background strength
        if "backgroundStrength" in self._cfg["GENERAL"]:
            self._background_strength = self._cfg["GENERAL"]["backgroundStrength"]

        # setup compositor #############################################################################################
        self._tree = bpy.data.worlds["World"]

        # create input image node
        _render_layers_node = None # TODO get this one from render setup

        # create specific effects
        self._create_effects(cfg=self._cfg["ENVIRONMENT_EFFECTS"],
                            general_cfg=self._cfg["GENERAL"],
                            world_node_tree=self._tree,
                            render_layers_node=_render_layers_node)
        ###################################################################################### end of setup compositor #



    def activate_pass(self, pass_name, pass_cfg, keyframe = -1):
        """ activate pass of modules
        Args:
            pass_name:      name of pass to activate [string]
            pass_cfg:       specific parameters for the pass [dict]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        # semantic pass parameters #####################################################################################
        if "SemanticPass" == pass_name:
            self._tree.node_tree.nodes["Background"].inputs[1].default_value = 1.0
        ############################################################################## end of semantic pass parameters #

        # instance pass parameters #####################################################################################
        if "InstancePass" == pass_name:
            self._tree.node_tree.nodes["Background"].inputs[1].default_value = 1.0
        ############################################################################## end of instance pass parameters #

        # set keyframes ################################################################################################
        if keyframe: 
            self._tree.node_tree.nodes["Background"].inputs[1].keyframe_insert('default_value', frame=keyframe)

        for effect_handle in self._effect_list:
            effect_handle.activate_pass( pass_name=pass_name,pass_cfg=pass_cfg,keyframe=keyframe)
        ######################################################################################### end of set keyframes #


    def deactivate_pass(self, pass_name, pass_cfg, keyframe = -1):
        pass


    def step(self,meta_data,keyframe):
        """ step handle and modules
        Args:
            meta_data:      meta data which is passed to modules [dict]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        self._stepping_counter += 1

        # step for handle function #####################################################################################
        if (self._stepping_counter % self._trigger_interval) == 0:

            # get random number for background strength
            self._tree.node_tree.nodes["Background"].inputs[1].default_value = self._get_random_number(\
                                                                                            self._background_strength)

            # set keframes #############################################################################################
            if keyframe: 
                self._tree.node_tree.nodes["Background"].inputs[1].keyframe_insert('default_value', frame=keyframe)

                # set interpolation to constant ########################################################################
                _fcurves = self._tree.node_tree.animation_data.action.fcurves
                for fcurve in _fcurves:
                    for kf in fcurve.keyframe_points:
                        kf.interpolation = 'CONSTANT'
                ################################################################# end of set interpolation to constant #
            ###################################################################################### end of set keframes #
        ############################################################################## end of step for handle function #

        # step for modules #############################################################################################
        for effect_handle in self._effect_list:

            _trigger_option = effect_handle.get_trigger_type()

            if "GLOBAL" == _trigger_option:
                if (self._stepping_counter % self._trigger_interval) == 0:
                    effect_handle.step_module(meta_data=meta_data,keyframe=keyframe)

            if "LOCAL" == _trigger_option:
                effect_handle.step_module(meta_data=meta_data,keyframe=keyframe)
        ###################################################################################### end of step for modules #