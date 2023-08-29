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

class RGBDPass(TSSRenderPass):
    """docstring for RGBDPass"""
    def __init__(self,pass_name):
        super(RGBDPass, self).__init__(pass_name=pass_name)
        # class vars ###################################################################################################
        self._euclidean_depth_output_node = None
        self._pinhole_depth_output_node = None
        self._pinhole_converter_node = None

        # camera placeholders ##########################################################################################
        self._camera_resolution_X = None
        self._camera_resolution_Y = None
        self._camera_principle_point_U = None
        self._camera_principle_point_V = None
        self._camera_focal_length = None
        ################################################################################### end of camera placeholders #
        ############################################################################################ end of class vars #
        self._rgb_switch_node = None


    def reset(self):
        # class vars ###################################################################################################
        self._euclidean_depth_output_node = None
        self._pinhole_depth_output_node = None
        self._pinhole_converter_node = None

        # camera placeholders ##########################################################################################
        self._camera_resolution_X = None
        self._camera_resolution_Y = None
        self._camera_principle_point_U = None
        self._camera_principle_point_V = None
        self._camera_focal_length = None
        ################################################################################### end of camera placeholders #
        ############################################################################################ end of class vars #
        self._rgb_switch_node = None


    def _create_camera_parameter(self,node_offset=[0,0]):
        """ function to create camera nodes in blender
        Args:
            node_offset:                            offset position for nodes [list]
        Returns:
            None
        """

        # create nodes for image resolution ############################################################################
        self._camera_resolution_x = self._node_tree.nodes.new(type="CompositorNodeValue")
        self._camera_resolution_x.label = "camera_resolution_x"
        self._camera_resolution_x.location = (node_offset[0]+500,node_offset[1]+500)
        self._camera_resolution_y = self._node_tree.nodes.new(type="CompositorNodeValue")
        self._camera_resolution_y.label = "camera_resolution_y"
        self._camera_resolution_y.location = (node_offset[0]+500,node_offset[1]+100)
        ##################################################################### end of create nodes for image resolution #

        # create nodes for principle point #############################################################################
        self._camera_principle_point_u = self._node_tree.nodes.new(type="CompositorNodeValue")
        self._camera_principle_point_u.label = "camera_principle_point_u"
        self._camera_principle_point_u.location = (node_offset[0]+700,node_offset[1]+500)
        self._camera_principle_point_v = self._node_tree.nodes.new(type="CompositorNodeValue")
        self._camera_principle_point_v.label = "camera_principle_point_v"
        self._camera_principle_point_v.location = (node_offset[0]+700,node_offset[1]+100)
        ###################################################################### end of create nodes for principle point #

        # create nodes for focal length ################################################################################
        self._camera_focal_length = self._node_tree.nodes.new(type="CompositorNodeValue")
        self._camera_focal_length.label = "camera_focal_length"
        self._camera_focal_length.location = (node_offset[0]+1200,node_offset[1]+100)
        ######################################################################### end of create nodes for focal length #


    def _set_camera_parameters(self, 
                                camera_resolution, camera_focal_length, camera_principle_point=[-1,-1],
                                keyframe = -1):
        """ function to set camera parameters
        Args:
            camera_resolution:                      image resoultion [u,v] [list]
            camera_focal_length:                    focal length of image [float]
            camera_principle_point:                 principle point of camera [list]
            keyframe:                               current frame number; if value > -1, this should enable also the
                                                    setting of a keyframe [int]
        Returns:
            None
        """

        # set camera resolution
        self._camera_resolution_x.outputs[0].default_value = camera_resolution[0]
        self._camera_resolution_y.outputs[0].default_value = camera_resolution[1]

        # set camera principle point ###################################################################################
        if camera_principle_point[0] == -1:
            self._camera_principle_point_u.outputs[0].default_value = camera_resolution[0]/2.0
        else:
            self._camera_principle_point_u.outputs[0].default_value = camera_principle_point[0]

        if camera_principle_point[1] == -1:
            self._camera_principle_point_v.outputs[0].default_value = camera_resolution[0]/2.0
        else:
            self._camera_principle_point_v.outputs[0].default_value = camera_principle_point[1]
        ############################################################################ end of set camera principle point #

        # set camera focal length
        self._camera_focal_length.outputs[0].default_value = camera_focal_length

        # set keyframes if requested ###################################################################################
        if keyframe >= 0:
            # set keyframes for camera parameters
            self._camera_resolution_x.outputs[0].keyframe_insert('default_value', frame=keyframe)
            self._camera_resolution_y.outputs[0].keyframe_insert('default_value', frame=keyframe)

            self._camera_principle_point_u.outputs[0].keyframe_insert('default_value', frame=keyframe)
            self._camera_principle_point_v.outputs[0].keyframe_insert('default_value', frame=keyframe)

            self._camera_focal_length.outputs[0].keyframe_insert('default_value', frame=keyframe)
        ############################################################################ end of set keyframes if requested #


    def _create_rgb_nodes(self,node_offset=[0,0]):
        """ create nodes for rgb pass
        Args:
            node_offset:                            offset position for nodes [list]
        Returns:
            None
        """

        # create output node image
        self._image_output_node = self._node_tree.nodes.new(type="CompositorNodeOutputFile")
        self._image_output_node.name = 'TSSCompositorNodeOutputFileImage'
        self._image_output_node.location = (node_offset[0]+2500,node_offset[1])
        self._image_output_node.base_path = self._general_cfg["outputPath"]
        self._image_output_node.file_slots.new("rgbimage")


        # switch node
        self._rgb_switch_node = self._node_tree.nodes.new(type="CompositorNodeSwitch")
        self._rgb_switch_node.label = 'rgb_switch'
        self._rgb_switch_node.check = False
        self._node_tree.links.new(self._compositor_pass_list["combined_rgb"], self._rgb_switch_node.inputs[1])
        self._node_tree.links.new(self._rgb_switch_node.outputs[0], self._image_output_node.inputs["rgbimage"])
        self._rgb_switch_node.location = (node_offset[0]+2000,node_offset[1])

        return self._image_output_node


    def _create_depth_nodes(self,node_offset=[0,0]):
        """ create nodes for depth calculation; pinhole and eucleadin depth
        Args:
            node_offset:                            offset position for nodes [list]
        Returns:
            None
        """

        self._pinhole_switch_node = self._node_tree.nodes.new(type="CompositorNodeSwitch")
        self._pinhole_switch_node.label = 'depth_switch'
        self._pinhole_switch_node.check = False
        self._node_tree.links.new(self._render_layers_node.outputs['Depth'], self._pinhole_switch_node.inputs[1])
        self._pinhole_switch_node.location = (node_offset[0]+2300,node_offset[1]+500)

        # create output node pinhole depth
        self._pinhole_depth_output_node = self._node_tree.nodes.new(type="CompositorNodeOutputFile")
        self._pinhole_depth_output_node.name = 'TSSCompositorNodeOutputFileDepth'
        self._pinhole_depth_output_node.location = (node_offset[0]+2500,node_offset[1]+0)
        self._pinhole_depth_output_node.format.file_format = 'OPEN_EXR'
        self._pinhole_depth_output_node.base_path = self._general_cfg["outputPath"]
        self._pinhole_depth_output_node.file_slots.new('pinhole')
        bpy.context.scene.view_layers["View Layer"].use_pass_z = True
        self._pinhole_depth_output_node.format.compression = 0
        
        self._node_tree.links.new(
                self._pinhole_switch_node.outputs[0],
                self._pinhole_depth_output_node.inputs['pinhole'])


    def _create_depth_nodes_bak(self,node_offset=[0,0]):
        """ create nodes for depth calculation; pinhole and eucleadin depth
        Args:
            node_offset:                            offset position for nodes [list]
        Returns:
            None
        """

        # create node setup to get pinhole depth dp = (de * f)/sqrt(f*f + u*u + v*v)
        # create texture to obtain u and v information from blender
        _uv_texture = bpy.data.textures.new(name="uv_coordinate_texture", type="NONE")
        _uv_texture.use_nodes = True
        _uv_texture.node_tree.nodes.clear()
        _coordinate_texture_node = _uv_texture.node_tree.nodes.new(type="TextureNodeCoordinates")
        _output_texture_node = _uv_texture.node_tree.nodes.new(type="TextureNodeOutput")
        _uv_texture.node_tree.links.new(_coordinate_texture_node.outputs[0], _output_texture_node.inputs['Color'])

        # build up pinhole node tree
        _uv_texture_node = self._node_tree.nodes.new(type="CompositorNodeTexture")
        _uv_texture_node.texture = _uv_texture
        _uv_texture_node.location = (node_offset[0]+0,node_offset[1]+600)

        _coordinate_seperation_node = self._node_tree.nodes.new(type="CompositorNodeSepRGBA")
        _coordinate_seperation_node.label = "coordinate_seperation_node"
        self._node_tree.links.new(_uv_texture_node.outputs[1], _coordinate_seperation_node.inputs[0])
        _coordinate_seperation_node.location = (node_offset[0]+200,node_offset[1]+600)

        # get u*u #####################################################
        # get u values 
        _u_value = self._node_tree.nodes.new(type="CompositorNodeMath")
        _u_value.operation = 'MULTIPLY'
        _u_value.label = "u_value"
        self._node_tree.links.new(_coordinate_seperation_node.outputs['R'], _u_value.inputs[0])
        self._node_tree.links.new(self._camera_resolution_x.outputs[0], _u_value.inputs[1])
        _u_value.location = (node_offset[0]+700,node_offset[1]+700)

        # add principle points c_x
        _c_u_node = self._node_tree.nodes.new(type="CompositorNodeMath")
        _c_u_node.operation = 'SUBTRACT'
        _c_u_node.label = "c_u_node"
        self._node_tree.links.new(_u_value.outputs[0], _c_u_node.inputs[0])
        self._node_tree.links.new(self._camera_principle_point_u.outputs[0], _c_u_node.inputs[1])
        _c_u_node.location = (node_offset[0]+900,node_offset[1]+700)
            
        # square values
        _c_u_squared_node = self._node_tree.nodes.new(type="CompositorNodeMath")
        _c_u_squared_node.operation = 'MULTIPLY'
        _c_u_squared_node.label = "c_u_squared_node"
        self._node_tree.links.new(_c_u_node.outputs[0], _c_u_squared_node.inputs[0])
        self._node_tree.links.new(_c_u_node.outputs[0], _c_u_squared_node.inputs[1])
        _c_u_squared_node.location = (node_offset[0]+1100,node_offset[1]+700)
        #####################################################

        # get v*v #####################################################
        # get v values
        _v_value = self._node_tree.nodes.new(type="CompositorNodeMath")
        _v_value.operation = 'MULTIPLY'
        _v_value.label = "v_value"
        self._node_tree.links.new(_coordinate_seperation_node.outputs['G'], _v_value.inputs[0])
        self._node_tree.links.new(self._camera_resolution_y.outputs[0], _v_value.inputs[1])
        _v_value.location = (node_offset[0]+700,node_offset[1]+300)

        # add principle points c_x
        _c_v_node = self._node_tree.nodes.new(type="CompositorNodeMath")
        _c_v_node.operation = 'SUBTRACT'
        _c_v_node.label = "c_v_node"
        self._node_tree.links.new(_v_value.outputs[0], _c_v_node.inputs[0])
        self._node_tree.links.new(self._camera_principle_point_v.outputs[0], _c_v_node.inputs[1])
        _c_v_node.location = (node_offset[0]+900,node_offset[1]+300)
            
        # square values
        _c_v_squared_node = self._node_tree.nodes.new(type="CompositorNodeMath")
        _c_v_squared_node.operation = 'MULTIPLY'
        _c_v_squared_node.label = "c_v_squared_node"
        self._node_tree.links.new(_c_v_node.outputs[0], _c_v_squared_node.inputs[0])
        self._node_tree.links.new(_c_v_node.outputs[0], _c_v_squared_node.inputs[1])
        _c_v_squared_node.location = (node_offset[0]+1100,node_offset[1]+300)
        #####################################################

        # get 1/sqrt(f*f + u*u + v*v) ###############################
        # get u*u + v*v
        _u_and_v_node = self._node_tree.nodes.new(type="CompositorNodeMath")
        _u_and_v_node.operation = 'MULTIPLY'
        _u_and_v_node.label = "u_and_v_node"
        self._node_tree.links.new(_c_u_squared_node.outputs[0], _u_and_v_node.inputs[0])
        self._node_tree.links.new(_c_v_squared_node.outputs[0], _u_and_v_node.inputs[1])
        _u_and_v_node.location = (node_offset[0]+1300,node_offset[1]+500)

        # get u*u + v*v + f*f
        _u_and_v_and_f_node = self._node_tree.nodes.new(type="CompositorNodeMath")
        _u_and_v_and_f_node.operation = 'MULTIPLY'
        _u_and_v_and_f_node.label = "u_and_v_and_f_node"
        self._node_tree.links.new(_u_and_v_node.outputs[0], _u_and_v_and_f_node.inputs[0])
        self._node_tree.links.new(self._camera_focal_length.outputs[0], _u_and_v_and_f_node.inputs[1])
        _u_and_v_and_f_node.location = (node_offset[0]+1500,node_offset[1]+500)

        # get final product
        _one_over_node = self._node_tree.nodes.new(type="CompositorNodeMath")
        _one_over_node.operation = 'INVERSE_SQRT'
        _one_over_node.label = "one_over_node"
        self._node_tree.links.new(_u_and_v_and_f_node.outputs[0], _one_over_node.inputs[0])
        _one_over_node.location = (node_offset[0]+1700,node_offset[1]+500)
        ###############################

        # get (NODE*f)/sqrt(f*f + u*u + v*v) ###############################
        # get f/sqrt(f*f + u*u + v*v)
        _f_over_node = self._node_tree.nodes.new(type="CompositorNodeMath")
        _f_over_node.operation = 'MULTIPLY'
        _f_over_node.label = "f_over_node"
        self._node_tree.links.new(_one_over_node.outputs[0], _f_over_node.inputs[0])
        self._node_tree.links.new(self._camera_focal_length.outputs[0], _f_over_node.inputs[1])
        _f_over_node.location = (node_offset[0]+1900,node_offset[1]+500)

        # get NODE*f/sqrt(f*f + u*u + v*v)
        self._pinhole_converter_node = self._node_tree.nodes.new(type="CompositorNodeMath")
        self._pinhole_converter_node.operation = 'MULTIPLY'
        self._pinhole_converter_node.label = "pinhole_converter_node"
        self._node_tree.links.new(_f_over_node.outputs[0], self._pinhole_converter_node.inputs[0])
        self._pinhole_converter_node.location = (node_offset[0]+2100,node_offset[1]+500)

        # switch node
        self._depth_switch_node = self._node_tree.nodes.new(type="CompositorNodeSwitch")
        self._depth_switch_node.label = 'depth_switch'
        self._depth_switch_node.check = False
        self._node_tree.links.new(self._render_layers_node.outputs['Depth'], self._depth_switch_node.inputs[1])
        self._node_tree.links.new(self._render_layers_node.outputs['Depth'], self._pinhole_converter_node.inputs[1])
        self._depth_switch_node.location = (node_offset[0]+2300,node_offset[1]+500)

        self._pinhole_switch_node = self._node_tree.nodes.new(type="CompositorNodeSwitch")
        self._pinhole_switch_node.label = 'depth_switch'
        self._pinhole_switch_node.check = False
        self._node_tree.links.new(self._pinhole_converter_node.outputs[0], self._pinhole_switch_node.inputs[1])
        self._pinhole_switch_node.location = (node_offset[0]+2300,node_offset[1]+500)


        # create output node euclidean depth
        self._euclidean_depth_output_node = self._node_tree.nodes.new(type="CompositorNodeOutputFile")
        self._euclidean_depth_output_node.name = 'TSSCompositorNodeOutputFileDepth'
        self._euclidean_depth_output_node.location = (node_offset[0]+2500,node_offset[1]+300)
        self._euclidean_depth_output_node.format.file_format = 'OPEN_EXR'
        self._euclidean_depth_output_node.base_path = self._general_cfg["outputPath"]
        bpy.context.scene.view_layers["View Layer"].use_pass_z = True
        self._euclidean_depth_output_node.format.compression = 0
        self._euclidean_depth_output_node.file_slots.new('euclidean')
        self._node_tree.links.new(
                self._depth_switch_node.outputs[0],
                self._euclidean_depth_output_node.inputs['euclidean'])

        #self._euclidean_depth_output_node.file_slots['dummy_euclidean'].path = "asdfsafsd"

        # create output node pinhole depth
        self._pinhole_depth_output_node = self._node_tree.nodes.new(type="CompositorNodeOutputFile")
        self._pinhole_depth_output_node.name = 'TSSCompositorNodeOutputFileDepth'
        self._pinhole_depth_output_node.location = (node_offset[0]+2500,node_offset[1]+0)
        self._pinhole_depth_output_node.format.file_format = 'OPEN_EXR'
        self._pinhole_depth_output_node.base_path = self._general_cfg["outputPath"]
        self._pinhole_depth_output_node.file_slots.new('pinhole')
        bpy.context.scene.view_layers["View Layer"].use_pass_z = True
        self._pinhole_depth_output_node.format.compression = 0
        
        self._node_tree.links.new(
                self._pinhole_switch_node.outputs[0],
                self._pinhole_depth_output_node.inputs['pinhole'])


    def create(self):
        """ create function of RGBD
        Args:
            None
        Returns:
            None
        """

        self._create_camera_parameter(node_offset=self._node_offset)

        self._create_rgb_nodes(node_offset=self._node_offset)

        self._create_depth_nodes(node_offset=self._node_offset)


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

        # set params ###################################################################################################
        # set color managment to filmic
        bpy.context.scene.view_settings.view_transform = 'Filmic'
        bpy.context.scene.render.image_settings.color_mode = 'RGB'
        bpy.context.scene.render.film_transparent = False

        self._switch_On_AA(keyframe=keyframe)
        self._set_render_samples(num_samples=self._cfg['renderSamples'], keyframe=keyframe)
        self._set_max_bounces(num_bounces=self._cfg['lightPathesMaxBounces'], keyframe=keyframe)
        ############################################################################################ end of set params #



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

        # assemble file name ###########################################################################################
        _sensor_name = sensor_data["name"]
        _rgb_output_name = _sensor_name + "_rgb"
        _p_depth_output_name = _sensor_name + "_pinhole_depth"
        _e_depth_output_name = _sensor_name + "_euclidean_depth"
        #################################################################################### end of assemble file name #

        # update render settings #######################################################################################
        self._camera_resolution_x.outputs[0].default_value = sensor_data["imageResolution"][0]
        self._camera_resolution_y.outputs[0].default_value = sensor_data["imageResolution"][1]
        bpy.context.scene.render.resolution_x = sensor_data["imageResolution"][0]
        bpy.context.scene.render.resolution_y = sensor_data["imageResolution"][1]
        if sensor_data["DepthEnabled"]:
            self._pinhole_switch_node.check = True
            #self._depth_switch_node.check = True NOTE: depth not supported anymore
        self._rgb_switch_node.check = True
        ################################################################################ end of update render settings #

        # update filename

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
        self._print_msg("Render time (RGBD Pass): " + str(_time_2-_time_1))


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
        _old_file_name = _base_path+"/rgbimage"+_current_frame_number+".png"
        _new_file_name = _base_path+"/"+_new_frame_number+_rgb_output_name+"_"+_sub_render_ID_str+".png"
        _moved_file_name = _sensor_path+"/"+_new_frame_number+_rgb_output_name+"_"+_sub_render_ID_str+".png"
        os.rename(_old_file_name,_new_file_name)
        shutil.move(_new_file_name,_moved_file_name)
        _file1 = _moved_file_name
        ################################################################################ end of rename rgb output name #

        
        if sensor_data["DepthEnabled"]:
            # rename pinhole depth output name #########################################################################
            _old_file_name = _base_path+"/pinhole"+_current_frame_number+".exr"
            _new_file_name = _base_path+"/"+_new_frame_number+_p_depth_output_name+"_"+_sub_render_ID_str+".exr"
            _moved_file_name = _sensor_path+"/"+_new_frame_number+_p_depth_output_name+"_"+_sub_render_ID_str+".exr"
            os.rename(_old_file_name,_new_file_name)
            shutil.move(_new_file_name,_moved_file_name)
            _file2 = _moved_file_name
            ######################################################################## end of rename pinhole output name #
        #################################################################################### end of rename output name #

        self._pinhole_switch_node.check = False
        #self._depth_switch_node.check = False  NOTE: depth not supported anymore
        self._rgb_switch_node.check = False

        if _file2:
            return [_file1,_file2]
        else:
            return _file1 