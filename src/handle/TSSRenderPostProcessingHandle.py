# blender imports
import bpy

# utility imports
import numpy as np

# system imports
import sys
import os
import pathlib
import importlib
from datetime import datetime


class TSSRenderPostProcessingHandle(object):
    """docstring for TSSRenderPostProcessingHandle"""
    def __init__(self):
        super(TSSRenderPostProcessingHandle, self).__init__()
        # class vars ###################################################################################################
        self._post_processing_list = []
        self._cfg = {}
        self._outputPath = ""
        self._global_step_index = 1
        self._compositor_pass_list = {}
        ############################################################################################ end of class vars #


    def reset_module(self):
        """ reset main and sub module
        Args:
            None
        Returns:
            None
        """

        # reset all post_processing_obj ################################################################################
        for post_processing_obj in self._post_processing_list:
            # reset post_processing_obj
            post_processing_obj.reset_module()

            # maybe osbolete in future versions
            del post_processing_obj
        ######################################################################### end of reset all post_processing_obj # 

        # reset class vars
        self._post_processing_list = []
        self._compositor_pass_list = {}


    def _create_post_processing_effects(self,cfg,general_cfg,node_tree,compositor_pass_list):
        """ create sub modules/effects
        Args:
            cfg:                    cfg dict of class [dict]
            general_cfg:            general cfg dict of class [dict]
            node_tree:              compositor node tree [blObject]
            compositor_pass_list:   list of important compositor handles [dict]
        Returns:
            return error code
        """

        for ii, effect in enumerate(cfg):
            try:
                # import module and create class #######################################################################
                _moduleName = "src.render_post_processing.effects." + effect["type"]
                _module = importlib.import_module(_moduleName)
                _class = getattr(_module, effect["type"])
                _effect = _class(pass_name=effect["type"])
                ################################################################ end of import module and create class #

                # set post processing params and create pass ###########################################################
                # set general cfg
                _effect.set_general_cfg(cfg=general_cfg)

                # update sensor cfg
                _effect.update_cfg(cfg=effect["effectParams"])
                
                # set node offset for organized node tree
                _effect.set_node_offset(node_offset=[1000,2000*ii])

                # set node tree handle
                _effect.set_node_tree(node_tree=node_tree)

                # set global step index
                _effect.set_global_step_index(index=self._global_step_index)

                # set render pass
                _effect.set_compositor_pass_list(compositor_pass_list=self._compositor_pass_list)

                # create post processing obj
                _effect.create()

                # update render pass list
                self._compositor_pass_list = _effect.get_compositor_pass_list()
                #################################################### end of set post processing params and create pass #
                
                # add post processing obj to list
                self._post_processing_list.append(_effect)

            except ImportError:
                # manage import error
                raise Exception("Cannot add post processing object")
                return -1

        return 0


    def get_compositor_pass_list(self):
        """ get compositor pass list
        Args:
            None
        Returns:
            self._compositor_pass_list
        """

        return self._compositor_pass_list


    def update_cfg(self,cfg):
        """ set cfg dict for object
        Args:
            cfg:            cfg dict of class [dict]
        Returns:
            None
        """

        self._cfg = cfg


    def _pre_diffuse_channel(self):
        """ set cfg for pre effect of diffuse channel
        Args:
            None
        Returns:
            cfg [dict]
        """

        # init dicts ###################################################################################################
        _cfg = {}
        _params_cfg = {}
        ############################################################################################ end of init dicts #

        # specific cfg attributes ######################################################################################
        _params_cfg["combineInput1"] = "DiffCol"
        _params_cfg["combineInput2"] = "Env"
        _params_cfg["combineOption"] = "ADD"
        _params_cfg["combineFac"] = 1.0
        _params_cfg["outputName"] = "combined_diffuse"
        ############################################################################### end of specific cfg attributes #

        # main cfg attributes ##########################################################################################
        _cfg["type"] = "CombineEffect"
        _cfg["effectParams"] = _params_cfg
        ################################################################################### end of main cfg attributes #

        # return cfg
        return _cfg


    def _get_pre_fix_effects(self):
        """ prepare pre effects
        Args:
            None
        Returns:
            cfg [dict]
        """

        # add pre effects ##############################################################################################
        _pre_effect_cfg = []
        _pre_effect_cfg.append(self._pre_diffuse_channel())
        ####################################################################################### end of add pre effects #

        # return effect cfg
        return _pre_effect_cfg


    def _create_pre_fic_effects(self,node_tree,compositor_pass_list):
        """ create pre effects
        Args:
            node_tree:              compositor node tree [blObject]
            compositor_pass_list:   compositor pass list [dict]
        Returns:
            None
        """

        # get pre effects
        _pre_effect_cfg = self._get_pre_fix_effects()

        # create effects
        self._create_post_processing_effects(   cfg=_pre_effect_cfg,
                                                general_cfg={},
                                                node_tree=node_tree,
                                                compositor_pass_list=compositor_pass_list)

        
    def _set_render_settings(self,renderCfg):
        """ set render channels
        Args:
            renderCfg:              cfg file for render channels [dict]
        Returns:
            None
        """

        # activate renderChannels ######################################################################################
        bpy.context.scene.view_layers["View Layer"].use_pass_combined = False
        bpy.context.scene.view_layers["View Layer"].use_pass_z = True
        bpy.context.scene.view_layers["View Layer"].use_pass_mist = False
        bpy.context.scene.view_layers["View Layer"].use_pass_normal = False
        bpy.context.scene.view_layers["View Layer"].use_pass_vector = False
        bpy.context.scene.view_layers["View Layer"].use_pass_uv = False
        bpy.context.scene.view_layers["View Layer"].use_pass_object_index = False
        bpy.context.scene.view_layers["View Layer"].use_pass_material_index = False
        bpy.context.scene.view_layers["View Layer"].use_pass_diffuse_color = True
        ############################################################################### end of activate renderChannels #


    def create(self):
        """ create function
        Args:
            None
        Returns:
            None
        """
        
        self._set_render_settings(renderCfg=self._cfg["GENERAL"])

        # setup compositor #############################################################################################
        bpy.context.scene.use_nodes = True
        _tree = bpy.context.scene.node_tree

        # clear default nodes
        for node in _tree.nodes:
            _tree.nodes.remove(node)

        # create input image node
        _render_layers_node = _tree.nodes.new(type='CompositorNodeRLayers')
        _render_layers_node.name = 'TSSCompositorNodeRLayers'

        self._compositor_pass_list["CompositorNodeRLayers"] = _render_layers_node

        # add common render passes #####################################################################################
        self._compositor_pass_list["Image"] = _render_layers_node.outputs['Image']
        self._compositor_pass_list["combined_rgb"] = _render_layers_node.outputs['Image']
        self._compositor_pass_list["Env"] = _render_layers_node.outputs['Env']
        self._compositor_pass_list["Alpha"] = _render_layers_node.outputs['Alpha']
        ############################################################################## end of add common render passes #

        # optional render passes #######################################################################################
        if bpy.context.scene.view_layers["View Layer"].use_pass_z:
            self._compositor_pass_list["Depth"] = _render_layers_node.outputs['Depth']

        if bpy.context.scene.view_layers["View Layer"].use_pass_diffuse_color:
            self._compositor_pass_list["DiffCol"] = _render_layers_node.outputs['DiffCol']
        ################################################################################ end of optional render passes #
        ###################################################################################### end of setup compositor #

        self._create_pre_fic_effects(node_tree=_tree,compositor_pass_list=self._compositor_pass_list)

        # load render pass objects #####################################################################################
        self._create_post_processing_effects(   cfg=self._cfg["POST_EFFECTS"],
                                                general_cfg=self._cfg["GENERAL"],
                                                node_tree=_tree,
                                                compositor_pass_list=self._compositor_pass_list)
        ############################################################################## end of load render pass objects #


    def step(self, keyframe=-1):
        """ step function
        Args:
            keyframe:                               current frame number; if value > -1, this should enable also the
                                                    setting of a keyframe [int]
        Returns:
            None
        """

        self._global_step_index += 1

        for effect in self._post_processing_list:
            effect.increase_global_step_index()

    def set_log_folder(self, log_folder_path):
        for effect in self._post_processing_list:
            effect.set_log_folder(log_folder_path)

    def log_step(self, keyframe):
        """ log step function is called for every new sample in of the batch; should be overwritten by custom class
            OVERWRITE!
        Args:
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        for effect in self._post_processing_list:
            effect.log_step(keyframe)

    def activate_pass(self, pass_name, pass_cfg, keyframe = -1):
        """ step function
        Args:
            pass_name:                              name of pass which is suppose to be activated [str]
            pass_cfg:                               cfg of pass to be activated [dict]
            keyframe:                               current frame number; if value > -1, this should enable also the
                                                    setting of a keyframe [int]
        Returns:
            None
        """

        pass


    def deactivate_pass(self, pass_name, pass_cfg, keyframe = -1):
        """ deactive pass function
        Args:
            pass_name:                              name of pass which is suppose to be deactivated [str]
            pass_cfg:                               cfg of pass to be deactivated [dict]
            keyframe:                               current frame number; if value > -1, this should enable also the
                                                    setting of a keyframe [int]
        Returns:
            None
        """

        pass
