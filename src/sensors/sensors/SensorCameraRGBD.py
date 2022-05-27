# blender imports
import bpy

# utility imports
import numpy as np
import csv
import random
import math
#from itertools import cycle

# system imports
import sys
import os
import copy
import pathlib

from src.sensors.TSSSensor import TSSSensor

class SensorCameraRGBD(TSSSensor):
    """docstring for SensorCameraRGBD
        
        cfg option:

        {
        "type": "SensorCameraRGBD",
            "sensorParams": {   
                            "outputBaseName":                   base name of output file
                            "cameraFocalLength": 70             focal lenght of camera [float][mm]
                            "cameraFOVHorizontal": 10           horizontal field ov view []
                            "cameraFOVVertical": 10             vertical field ov view []
                            "cameraSensorWidth": 0.1            sensor chip width []
                            "cameraPrinciplePointU": -1         sensor principle point u [] 
                            "cameraPrinciplePointV": -1,        sensor principle point v []
                            "stereoBaseLine": 0.1,              stereo base line[]
                            "transformation": [0,0,0,1,0,0,0],  transformation to base [numpy]
                            "triggerInterval": 1,               defines in which interval the sensor is triggered [uint]
                            "renderPasses": {
                                            "0": {"offsetID": 0, "numSamples": 1},
                                            "1": {"offsetID": 0, "numSamples": 2},
                                            "2": {"offsetID": 0, "numSamples": 1}}
                                            }                   defines how sensor is rendered for render passes [dict]
                            }
            }
        }

        Example cfg:

        {
        "type": "SensorCameraRGBD",
            "sensorParams": {   
                            "outputBaseName":"rgbLeft",
                            "cameraFocalLength": 70,
                            "cameraFOVHorizontal": 10,
                            "cameraFOVVertical": 10,
                            "cameraSensorWidth": 0.1,
                            "cameraPrinciplePointU": -1,
                            "cameraPrinciplePointV": -1,
                            "stereoBaseLine": 0.1,
                            "transformation": [0,0,0,1,0,0,0],
                            "triggerInterval": 1,
                            "renderPasses": {
                                            "0": {"offsetID": 0, "numSamples": 1},
                                            "1": {"offsetID": 0, "numSamples": 2},
                                            "2": {"offsetID": 0, "numSamples": 1}}
                                            }
                            }
            }
        }

    """
    def __init__(self):
        super(SensorCameraRGBD, self).__init__()

        # class vars ###################################################################################################
        self._k_mat = np.zeros((3,3))                               # K matrix
        ############################################################################################ end of class vars #
        

    def reset(self):
        """ reset function
        Args:
            None
        Returns:
            None
        """

        # reset vars ###################################################################################################
        self._k_mat = np.zeros((3,3))
        ############################################################################################ end of reset vars #
        

    def create(self):
        """ create function
        Args:
            None
        Returns:
            None
        """

        # create camera
        self._create_single_camera()
        

    def _create_single_camera(self):
        """ create single camera object

        Args:
            None
        Returns:
            None
        """

        # obtian K matrix from cfg #####################################################################################
        for ii in range(0,3):
            for jj in range(0,3):
                self._k_mat[ii,jj] = self._cfg["KMatrix"][ii*3+jj]
        ############################################################################## end of obtian K matrix from cfg #

        # create camera
        bpy.ops.object.camera_add()

        # get camera object
        # TODO get without object name:
        self._sensor = bpy.data.objects['Camera']

        # change name of camera
        self._sensor.name = self._cfg["outputBaseName"] + '_Camera_RGBD'

        # use depth of field if requested ##############################################################################
        if "depthOfField" in self._cfg:

            # activate depth of field
            self._sensor.data.dof.use_dof = True

            # set up params ############################################################################################
            if "distance" in self._cfg["depthOfField"]:
                self._sensor.data.dof.focus_distance = self._cfg["depthOfField"]["distance"]
            else:
                self._sensor.data.dof.focus_distance = 10.0

            if "fStop" in self._cfg["depthOfField"]:
                self._sensor.data.dof.aperture_fstop = self._cfg["depthOfField"]["fStop"]
            else:
                self._sensor.data.dof.aperture_fstop = 1.5

            if "blades" in self._cfg["depthOfField"]:
                self._sensor.data.dof.aperture_blades = self._cfg["depthOfField"]["blades"]
            else:
                self._sensor.data.dof.aperture_blades = 0

            if "rotationDeg" in self._cfg["depthOfField"]:
                self._sensor.data.dof.aperture_rotation = self._cfg["depthOfField"]["rotationDeg"]*(math.pi/180.0)
            else:
                self._sensor.data.dof.aperture_rotation = 0

            if "ratio" in self._cfg["depthOfField"]:
                self._sensor.data.dof.aperture_ratio = self._cfg["depthOfField"]["ratio"]
            else:
                self._sensor.data.dof.aperture_ratio = 1.0
            #################################################################################### end of  set up params #
        else:
            # deactivate depth of field
            self._sensor.data.dof.use_dof = False
        ####################################################################### end of use depth of field if requested #

        # set camera params ############################################################################################
        # based on https://blender.stackexchange.com/a/120063

        # get focal lenght and principle point from K matrix
        _f_x = self._k_mat[0,0]
        _f_y = self._k_mat[1,1]
        _c_x = self._k_mat[0,2]
        _c_y = self._k_mat[1,2]

        # get image resolution
        _w = self._cfg["imageResolution"][0]
        _h = self._cfg["imageResolution"][1]

        # calc field of view
        # _fov = 2.0*math.atan(_w/(2*_f_x))
        # _fov_deg = _fov*(180./math.pi)

        # aspect ratio
        _a_x = 1
        _a_y = 1
        if _f_x > _f_y:
            _a_y = _f_x / _f_y
        elif _f_x < _f_y:
            _a_x = _f_y / _f_x

        # calc focal length ratio
        # _f_ratio = _f_x / _f_y
        _f_ratio = _f_y / _f_x
        _a_ratio = _a_y / _a_x

        # sensor fitting mode according to issue
        print(f"_f_ratio: {_f_ratio}")
        print(f"_f_x: {_f_x}")
        print(f"_f_y: {_f_y}")
        print(f" cam.sensor_fit: {self._sensor.data.sensor_fit}")
        print(f" cam.sensor_width: {self._sensor.data.sensor_width}")
        print(f" cam.sensor_height: {self._sensor.data.sensor_height}")
        # self._sensor.data.sensor_fit = 'HORIZONTAL'
        '''
        if 'AUTO' == self._sensor.data.sensor_fit:
            if _f_x*_w >= _f_y*_h:
                _v = _w
            else:
                _v = _f_ratio*_h #pixel_aspect_ratio * _h
        else:
            if 'HORIZONTAL' == self._sensor.data.sensor_fit:
                _v = _w
            else:
                _v = _f_ratio*_h  #pixel_aspect_ratio * _h
        '''
        if 'AUTO' == self._sensor.data.sensor_fit:
            if _a_x * _w >= _a_y * _h:
                self._sensor.data.sensor_fit = 'HORIZONTAL'
            else:
                self._sensor.data.sensor_fit = 'VERTICAL'

        if 'HORIZONTAL' == self._sensor.data.sensor_fit:
            _v = _w
        else:
            _v = _a_ratio * _h

        if self._sensor.data.sensor_fit == 'VERTICAL':
            _s_mm = self._sensor.data.sensor_height
        else:
            _s_mm = self._sensor.data.sensor_width

        _f = _f_x * _s_mm / _v

        print(f"_f: {_f}")
        print(f"_v: {_v}")
        print(f"_s_mm: {_s_mm}")
        print(f"_a_ratio: {_a_ratio}")

        # self._sensor.data.sensor_height = self._sensor.data.sensor_width
        print(f" cam.sensor_fit: {self._sensor.data.sensor_fit}")
        print(f" cam.sensor_width: {self._sensor.data.sensor_width}")
        print(f" cam.sensor_height: {self._sensor.data.sensor_height}")

        # Set shift
        self._sensor.data.shift_x = (_c_x - (_w - 1) / 2) / -_v  # ((_w/2.)-_c_x)/ _v
        self._sensor.data.shift_y = (_c_y - (_h - 1) / 2) / _v * _a_ratio  # ((_h/2.)-_c_y)/ _v * _f_ratio

        print(f"shift_x: {self._sensor.data.shift_x}")
        print(f"shift_y: {self._sensor.data.shift_y}")

        # set field of view for camera
        # self._sensor.data.lens_unit = 'FOV'
        # self._sensor.data.angle = _fov
        self._sensor.data.lens_unit = 'MILLIMETERS'
        self._sensor.data.lens = _f

        bpy.context.scene.render.pixel_aspect_x = _a_x
        bpy.context.scene.render.pixel_aspect_y = _a_y

        # set transformation for camera
        self._sensor.rotation_mode = 'QUATERNION'        
        self._base_to_sensor = self._cfg["transformation"]
        self._sensor.location = (self._base_to_sensor[0],self._base_to_sensor[1],self._base_to_sensor[2])
        self._sensor.rotation_quaternion = (self._base_to_sensor[3],
                                            self._base_to_sensor[4],
                                            self._base_to_sensor[5],
                                            self._base_to_sensor[6])
        ##################################################################################### end of set camera params #

        # set render pass dict #########################################################################################
        self._general_render_pass_dict = {}
        self._general_render_pass_dict["name"] = self._cfg["outputBaseName"]
        self._general_render_pass_dict["imageResolution"] = [int(self._cfg["imageResolution"][0]),\
                                                            int(self._cfg["imageResolution"][1])]
        ################################################################################## end of set render pass dict #

        # config RGBDPass ##############################################################################################
        if 'RGBDPass' in self._cfg["renderPasses"]:
            rgbd_info = {}
            rgbd_info["name"] = self._cfg["outputBaseName"]
            rgbd_info["imageResolution"] = [int(self._cfg["imageResolution"][0]),int(self._cfg["imageResolution"][1])]
            rgbd_info["DepthEnabled"] = self._cfg["renderPasses"]["RGBDPass"]["DepthEnabled"]
            self._render_pass_dict["RGBDPass"] = rgbd_info
        ####################################################################################### end of config RGBDPass #