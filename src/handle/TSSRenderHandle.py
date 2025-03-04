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

class TSSRenderHandle(object):
    """docstring for TSSRenderHandle"""
    def __init__(self):
        super(TSSRenderHandle, self).__init__()
        # class vars ###################################################################################################
        self._pass_list = []
        self._cfg = {}
        self._outputPath = ""
        self._global_step_index = 1
        self._compositor_pass_list = {}
        ############################################################################################ end of class vars #


    def reset_module(self):
        # reset all render_pass ########################################################################################
        for render_pass in self._pass_list:
            # reset render_pass
            render_pass.reset_module()

            # maybe osbolete in future versions
            del render_pass
        ################################################################################# end of reset all render_pass # 

        self._compositor_pass_list = {}
        self._pass_list = []


    def _create_passes(self,cfg,general_cfg,node_tree):

        for ii, render_pass in enumerate(cfg):
            try:
                # import module and create class #######################################################################
                _module_name = "src.rendering.passes." + render_pass["type"]
                _module = importlib.import_module(_module_name)
                _class = getattr(_module, render_pass["type"])
                _render_pass = _class(pass_name=render_pass["type"])
                ################################################################ end of import module and create class #

                # set pass params and create pass ######################################################################
                general_cfg["outputPath"] = self._outputPath

                # set general cfg
                _render_pass.set_general_cfg(cfg=general_cfg)

                # update sensor cfg
                _render_pass.update_cfg(cfg=render_pass["passParams"])
                
                # set node offset for organized node tree
                _render_pass.set_node_offset(node_offset=[1000,2000*ii])

                # set node tree handle
                _render_pass.set_node_tree(node_tree=node_tree)

                # set global step index
                _render_pass.set_global_step_index(index = self._global_step_index)

                # set compositor_pass_list
                _render_pass.set_compositor_pass_list(compositor_pass_list = self._compositor_pass_list)

                # create pass
                _render_pass.create()
                ############################################################### end of set pass params and create pass #
                
                # add pass to list
                self._pass_list.append(_render_pass)

            except ImportError:
                # manage import error
                raise Exception("Cannot add render pass")
                return -1

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


    def _set_render_settings(self,renderCfg):

        # setup render engine
        bpy.context.scene.render.engine = renderCfg['renderEngine']
        bpy.context.scene.cycles.feature_set = renderCfg['renderFeatureSet']
        if renderCfg['renderDevice'] == 'GPU':
            bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "CUDA"
            bpy.context.preferences.addons["cycles"].preferences.get_devices()
        bpy.context.scene.cycles.device = renderCfg['renderDevice'] # this is just for the GUI mode
        bpy.data.scenes["Scene"].cycles.device= renderCfg['renderDevice']  # this is for cmd mode


        # create output folder
        # TODO: shift this to button "render scene"

        # performance settings
        #bpy.context.scene.render.tile_x = renderCfg['performanceTilesX']
        #bpy.context.scene.render.tile_y = renderCfg['performanceTilesY']

        # activate renderChannels ###############################################################
        # deactive by default all render channels
        bpy.context.scene.view_layers["View Layer"].use_pass_combined = False
        bpy.context.scene.view_layers["View Layer"].use_pass_z = True
        bpy.context.scene.view_layers["View Layer"].use_pass_mist = False
        bpy.context.scene.view_layers["View Layer"].use_pass_normal = False
        bpy.context.scene.view_layers["View Layer"].use_pass_vector = False
        bpy.context.scene.view_layers["View Layer"].use_pass_uv = False
        bpy.context.scene.view_layers["View Layer"].use_pass_object_index = False
        bpy.context.scene.view_layers["View Layer"].use_pass_material_index = False
        bpy.context.scene.view_layers["View Layer"].use_pass_diffuse_color = True


    def set_compositor_pass_list(self,compositor_pass_list):
        self._compositor_pass_list = compositor_pass_list


    def set_output_folder(self,output_folder_path):
        self._outputPath = output_folder_path


    def create(self):
        
        # set basic parameter ##########################################################################################
        # bpy.context.scene.frame_end = numberFrames TODO what about that?
        bpy.context.scene.render.image_settings.color_mode = 'RGB'
        bpy.context.scene.render.film_transparent = False   # TODO: should be an option in cfg
        ################################################################################### end of set basic parameter #

        self._set_render_settings(renderCfg=self._cfg["GENERAL"])

        # setup compositor #############################################################################################
        #bpy.context.scene.use_nodes = True
        _tree = bpy.context.scene.node_tree

        # create input image node
        if not "CompositorNodeRLayers" in self._compositor_pass_list:
            _render_layers_node = _tree.nodes.new(type='CompositorNodeRLayers')
            _render_layers_node.name = 'TSSCompositorNodeRLayers'
            self._compositor_pass_list["CompositorNodeRLayers"] = _render_layers_node
        ###################################################################################### end of setup compositor #

        # load render pass objects #####################################################################################
        self._create_passes(cfg=self._cfg["RENDER_PASSES"],
                            general_cfg=self._cfg["GENERAL"],
                            node_tree=_tree)
        ############################################################################## end of load render pass objects #


    def set_log_folder(self, log_folder_path):
        for render_pass in self._pass_list:
            render_pass.set_log_folder(log_folder_path)

    def step(self, keyframe=-1):
        self._global_step_index += 1

        for render_pass in self._pass_list:
            render_pass.increase_global_step_index()


    def log_step(self, keyframe):
        """ log step function is called for every new sample in of the batch; should be overwritten by custom class
            OVERWRITE!
        Args:
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        for render_pass in self._pass_list:
            render_pass.log_step(keyframe)

    def activate_pass(self, pass_name, pass_cfg, keyframe = -1):
        pass


    def deactivate_pass(self, pass_name, pass_cfg, keyframe = -1):
        pass
