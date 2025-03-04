# blender imports
import bpy

# utility imports
import numpy as np
import csv
import random

from src.TSSBase import TSSBase

class TSSSensor(TSSBase):
    """docstring for TSSSensor"""
    def __init__(self):
        super(TSSSensor, self).__init__()
        # class vars ###################################################################################################
        self._sensor = None                                             # blender sensor handle [blObject]
        self._base_to_sensor = np.array([0.0,0.0,0.0,1.0,0.0,0.0,0.0])  # transformation vector base to sensor [numpy]
                                                                        # format: pos_x,pos_y,pos_z,q_w,q_x,q_y,q_z
        self._sensor_movement_type = -1                                 # movement type [int]
        self._sensor_pose_list = []                                     # list of sensor poses [list]
        self._pose_index = 0                                            # current pose index [int]
        self._render_pass_dict = {}                                     # additional information about sensor for render
                                                                        # pass [dict]
        self._general_render_pass_dict = {}                             # additional general information about sensor
                                                                        # for render pass [dict]
        ############################################################################################ end of class vars #


    def reset_module(self):

        self._sensor = None
        self._base_to_sensor = np.array([0.0,0.0,0.0,1.0,0.0,0.0,0.0])
        self._sensor_movement_type = -1
        self._sensor_pose_list = []
        self._pose_index = 0
        self._render_pass_dict = {}
        self._general_render_pass_dict = {}

        self.reset_base()
        self.reset()


    def reset(self):
        """ specific reset function
            OVERWRITE!
        Args:
            None
        Returns:
            None
        """

        pass


    def _set_sensor_to_active(self):
        """ set current sensor as active
        Args:
            None
        Returns:
            None
        """

        # set sensor as active camera
        bpy.context.scene.camera = self._sensor

        # set sensor as dicing camera; needed for cycles displacment
        bpy.context.scene.cycles.dicing_camera = self._sensor


    def reset_pose_index(self, pose_index=0):
        """ reset pose index variable
        Args:
            pose_index:     value to which pose_index should be set [int]
        Returns:
            None
        """

        self._pose_index = pose_index


    def get_pose_at(self, pose_index=-1):
        """ get pose at specific index
        Args:
            pose_index:     index from which pose is requested; if set to -1, current pose is sent back [int]
        Returns:
            pose to specific index [numpy]
        """

        # check if current pose is requested
        if -1 == pose_index:
            return self._sensor_pose_list[self._pose_index]
        else:
            return self._sensor_pose_list[pose_index]


    def get_sensor(self):
        """ get sensor blender handle
        Args:
            None
        Returns:
            sensor handle [blObject]
        """

        return self._sensor

    def activate_pass(self, pass_name, pass_cfg, keyframe = -1):

        if pass_name in self._cfg["renderPasses"]:
            # get activation slot and current activation ID
            _activation_slot = self._cfg["renderPasses"][pass_name]["activationSlot"]
            _activation_ID = pass_cfg["activationID"]

            if _activation_ID < len(_activation_slot):

                if 1 == _activation_slot[_activation_ID]:
                    
                    self._set_sensor_to_active()

                    if pass_name in self._render_pass_dict:
                        return self._render_pass_dict[pass_name]
                    else:
                        if bool(self._general_render_pass_dict):
                            return self._general_render_pass_dict

        return None


    def _print_msg(self,skk): print("\033[93m {}\033[00m" .format(skk))