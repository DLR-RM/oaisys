# blender imports
import bpy

# utility imports
import numpy as np
import csv
import random
import os
import shutil
import pathlib
import sys
import time

from src.rendering.TSSRenderPass import TSSRenderPass

class SemanticPass(TSSRenderPass):
    """docstring for SemanticPass"""
    def __init__(self,pass_name):
        super(SemanticPass, self).__init__(pass_name=pass_name)
        # class vars ###################################################################################################
        self._output_node = None
        self._label_combine_node = None
        self._label_switch_node = None
        ############################################################################################ end of class vars #


    def reset(self):
        self._output_node = None
        self._label_combine_node = None
        self._label_switch_node = None


    def create(self):
        """ create function of Semantic Pass
        Args:
            None
        Returns:
            None
        """

        # create output node ###########################################################################################
        self._output_node = self._node_tree.nodes.new(type="CompositorNodeOutputFile")
        self._output_node.name = 'SemanticOutputNode'
        self._output_node.label = 'SemanticOutputNode'
        self._output_node.location = (self._node_offset[0]+2300,self._node_offset[1]+0)
        if "imageFileType" in self._cfg:
            self._output_node.format.file_format = self._cfg["imageFileType"]
        else:
            self._output_node.format.file_format = "PNG"
        self._output_node.base_path = self._general_cfg["outputPath"]
        self._output_node.file_slots.new('semantic')
        self._output_node.format.compression = 0
        #################################################################################### end of create output node #

        # activate render layers which are needed for semantics ########################################################
        bpy.context.scene.view_layers["View Layer"].use_pass_diffuse_color = True
        bpy.context.scene.view_layers["View Layer"].use_pass_environment = True
        ################################################# end of activate render layers which are needed for semantics #

        # create switch node ###########################################################################################
        self._label_switch_node = self._node_tree.nodes.new(type="CompositorNodeSwitch")
        self._label_switch_node.label = 'semantic_switch'
        self._label_switch_node.check = False
        self._label_switch_node.location = (self._node_offset[0]+2300,self._node_offset[1]+500)
        #################################################################################### end of create switch node #

        # link nodes together ##########################################################################################
        self._node_tree.links.new(
            self._compositor_pass_list["combined_diffuse"],
            self._label_switch_node.inputs[1])

        self._node_tree.links.new(
            self._label_switch_node.outputs[0],
            self._output_node.inputs['semantic'])
        ################################################################################### end of link nodes together #
        


    def activate_pass(self, keyframe = -1): #pass_name, pass_cfg, keyframe = -1):
        """ active pass function
        Args:
            pass_name:                              name of pass which is suppose to be activated [str]
            pass_cfg:                               cfg of pass to be activated [dict]
            keyframe:                               current frame number; if value > -1, this should enable also the
                                                    setting of a keyframe [int]
        Returns:
            None
        """

        # set color managment to raw; we want the unprocessed color data
        bpy.context.scene.view_settings.view_transform = 'Raw'

        # set general rendering settings ###############################################################################
        # switch of AA, we want crisp edges for semantics
        self._switch_Off_AA(keyframe=keyframe)

        # set samples to minimum; just one light sample is needed to evalute object
        self._set_render_samples(num_samples=1,keyframe=keyframe)
        self._set_max_bounces(num_bounces=1,keyframe=keyframe)
        ######################################################################## end of set general rendering settings #

        # activate semantic pass
        


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

    def render(self,sensor_data=None,sub_render_ID=0,keyframe=-1):
        """ execute rendering function
            OVERWRITE!
        Args:
            sensor_data:            optional sensor data [not defined]
        Returns:
            None
        """

        # rename output name
        _sensor_name = sensor_data["name"]
        _semantic_output_name = _sensor_name + "_semantic_label"
        self._label_switch_node.check = True

        # render image
        logfile = 'blender_render.log'
        open(logfile, 'a').close()
        old = os.dup(1)
        sys.stdout.flush()
        os.close(1)
        os.open(logfile, os.O_WRONLY)
        _time_1 = time.time()
        bpy.ops.render.render(write_still = True)
        _time_2 = time.time()
        os.close(1)
        os.dup(old)
        os.close(old)
        sys.stdout.write('\r')
        self._print_msg("Render time (Semantic pass): " + str(_time_2-_time_1))

        # rename output name ###########################################################################################
        _current_frame_number = "{:04d}".format(keyframe)
        _new_frame_number = "{:04d}".format(self._global_step_index)
        _sub_render_ID_str = "{:02d}".format(sub_render_ID)
        _base_path = self._general_cfg["outputPath"]
        _sensor_path = os.path.join(_base_path,_sensor_name)

        # shift file ###################################################################################################
        # check if folder is available
        if not os.path.exists(_sensor_path):
            pathlib.Path(_sensor_path).mkdir(parents=True, exist_ok=True)
        ############################################################################################ end of shift file #

        # rename rgb output name #######################################################################################
        _old_file_name = _base_path+"/semantic"+_current_frame_number+".png"
        _new_file_name = _base_path+"/"+_new_frame_number+_semantic_output_name+"_"+_sub_render_ID_str+".png"
        _moved_file_name = _sensor_path+"/"+_new_frame_number+_semantic_output_name+"_"+_sub_render_ID_str+".png"
        os.rename(_old_file_name,_new_file_name)
        shutil.move(_new_file_name,_moved_file_name)
        ################################################################################ end of rename rgb output name #
        
        
        #################################################################################### end of rename output name #
        
        self._label_switch_node.check = False

        return _moved_file_name