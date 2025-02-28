# blender imports
import bpy

# utility imports
import numpy as np
import csv
import random
import importlib
import os

from src.TSSBase import TSSBase

from src.tools.trajectory.ObjectTrajectory import get_single_mesh_data, compute_center_of_mass, find_furthest_point
import src.tools.trajectory.ObjectTrajectory as ot


class TSSSensorHandle(TSSBase):
    """docstring for TSSSensorHandle"""

    def __init__(self):
        super(TSSSensorHandle, self).__init__()
        # class vars ###################################################################################################
        self._sensor_list = []  # list of sensors [list]
        self._target_pose_list = []  # list of target poses [list]
        self._target_object_active = False  # flag whether target object is active [bool]
        self._sensor_movement_type = -1  # movement type [int]
        self._sensor_pose_list = []  # list of sensor poses [list]
        self._pose_index = 0  # current pose index [int]
        self._sensor_base = None  # sensor base of all sensors [blObject]
        self._sensor_base_constraint = None  # sensor base constraint object of all sensors
        #                                    [blObject]
        self._target_object = None  # target object of sensor base [blObject]
        self._hover_base_constraint = None  # hover constraint for base [blObject]
        self._hover_target_constraint = None  # hover constraint for target [blObject]
        self._sensor_movement_type_mapping = {  # mapping to movement functions [dict]
            "deterministic": self._deterministic,
            "randomEuclidean": self._random_euclidean,
            "randomEuclideanTarget": self._random_euclidean_target,
            "centeredTarget": self._centered_target
        }
        self._roll_limits = [0, 0]
        ############################################################################################ end of class vars #

        # set correct module type
        self.set_module_type(type=1)

    def reset_module(self):
        """ reset all local vars
        Args:
            None
        Returns:
            None
        """

        # reset all sensors ############################################################################################
        for sensor in self._sensor_list:
            # reset sensor
            sensor.reset_module()

            # maybe obsolete in future versions
            del sensor
        ##################################################################################### end of reset all sensors #

        self.reset_base()

        # reset vars ###################################################################################################
        self._sensor_list = []
        self._target_pose_list = []
        self._target_object_active = False
        self._sensor_movement_type = -1
        self._sensor_pose_list = []
        self._pose_index = 0
        self._sensor_base = None
        self._target_object = None
        self._sensor_base_constraint = None
        self._roll_limits = [0, 0]
        ############################################################################################ end of reset vars #

    def _create_base_object(self, cfg, mesh_list):
        """ create base object
        Args:
            cfg:            general part of cfg from sensor handle [dict]
            mesh_list:      list of meshes created by OAISYS [list]
        Returns:
            ErrorCode:      error code; 0 if sucessful
        """
        if "stepInterval" in cfg:
            self._trigger_interval = cfg["stepInterval"]

        if len(cfg['hoverBaseDistance']) <= 1:
            hover_min = cfg['hoverBaseDistance'][0]
            hover_max = cfg['hoverBaseDistance'][0]
        else:
            hover_min = cfg['hoverBaseDistance'][0]
            hover_max = cfg['hoverBaseDistance'][1]
        _hover_base_distance = random.uniform(hover_min, hover_max)

        # create empty blender object ##################################################################################
        self._sensor_base = bpy.data.objects.new("empty", None)
        self._sensor_base.name = "sensor_base"
        self._sensor_base.empty_display_type = 'PLAIN_AXES'
        self._sensor_base.empty_display_size = 0.5
        bpy.context.scene.collection.objects.link(self._sensor_base)
        ########################################################################### end of create empty blender object #

        # create empty blender object for sensor base to apply constraints #############################################
        self._sensor_base_constraint = bpy.data.objects.new("empty", None)
        self._sensor_base_constraint.name = "dummy_object"
        self._sensor_base_constraint.empty_display_type = 'PLAIN_AXES'
        self._sensor_base_constraint.empty_display_size = 0.5
        bpy.context.scene.collection.objects.link(self._sensor_base_constraint)
        ###################################### end of create empty blender object for sensor base to apply constraints #

        # store roll values ############################################################################################
        if "randomTargetRollRad" in cfg:
            self._roll_limits = cfg["randomTargetRollDeg"]
        else:
            if "randomTargetRollDeg" in self._cfg["GENERAL"]:
                self._roll_limits[0] = (np.pi / 180.) * cfg["randomTargetRollDeg"][0]
                self._roll_limits[1] = (np.pi / 180.) * cfg["randomTargetRollDeg"][1]
            else:
                self._roll_limits = [0, 0]
        ##################################################################################### end of store roll values #

        # create movement pattern of sensor base
        self._sensor_pose_list, self._target_pose_list = self._sensor_movement_type_mapping[cfg["sensorMovementType"]](
            cfg,mesh_list)

        # interpolate pose frames if needed ############################################################################
        if "interpolationMode" in cfg:

            # interpolate base poses
            self._sensor_pose_list = self._pose_interpolate(pose_list=self._sensor_pose_list,
                                                            interpolation_mode=cfg["interpolationMode"])

            # interpolate target object poses if exist
            if self._target_pose_list is not None:
                self._target_pose_list = self._pose_interpolate(pose_list=self._target_pose_list,
                                                                interpolation_mode=cfg["interpolationMode"])
        ##################################################################### end of interpolate pose frames if needed #

        # target object creation #######################################################################################
        # check if target object shall be active and create it if needed
        if self._target_pose_list is not None:

            # enable target object flag
            self._target_object_active = True
            # create target object #####################################################################################
            self._target_object = bpy.data.objects.new("empty", None)
            self._target_object.name = "target_object"
            self._target_object.empty_display_type = 'PLAIN_AXES'
            self._target_object.empty_display_size = 0.5
            self._target_object.rotation_mode = 'QUATERNION'
            bpy.context.scene.collection.objects.link(self._target_object)
            ############################################################################## end of create target object #

            # create hover constraint ##################################################################################
            if "hoverBaseModeEnabled" in cfg:
                if cfg["hoverBaseModeEnabled"]:
                    self._hover_base_constraint = self._sensor_base_constraint.constraints.new(type='SHRINKWRAP')
                    self._hover_base_constraint.shrinkwrap_type = 'NEAREST_SURFACE'
                    self._hover_base_constraint.wrap_mode = 'ABOVE_SURFACE'
                    self._hover_base_constraint.track_axis = 'TRACK_Z'
                    self._hover_base_constraint.distance = _hover_base_distance  # float(cfg['hoverBaseDistance'])

            if "hoverTargetModeEnabled" in cfg:
                if cfg["hoverTargetModeEnabled"]:
                    self._hover_target_constraint = self._target_object.constraints.new(type='SHRINKWRAP')
                    self._hover_target_constraint.shrinkwrap_type = 'NEAREST_SURFACE'
                    self._hover_target_constraint.wrap_mode = 'ABOVE_SURFACE'
                    self._hover_target_constraint.distance = float(cfg['hoverTargetDistance'])
            ########################################################################### end of create hover constraint #

            # create target object to sensor base ######################################################################
            self._sensor_base_constraint.constraints.new(type='TRACK_TO')
            self._sensor_base_constraint.constraints["Track To"].target = self._target_object
            if self._cfg["GENERAL"]["sensorMovementType"] == "centeredTarget":
                self._sensor_base_constraint.constraints["Track To"].track_axis = 'TRACK_Z'
            else:
                self._sensor_base_constraint.constraints["Track To"].track_axis = 'TRACK_NEGATIVE_Z'
            self._sensor_base_constraint.constraints["Track To"].up_axis = 'UP_Y'
            ############################################################### end of create target object to sensor base #
        else:
            # create hover constraint ##################################################################################
            if "hoverBaseModeEnabled" in cfg:
                if cfg["hoverBaseModeEnabled"]:
                    self._hover_base_constraint = self._sensor_base_constraint.constraints.new(type='SHRINKWRAP')
                    self._hover_base_constraint.shrinkwrap_type = 'NEAREST_SURFACE'
                    self._hover_base_constraint.wrap_mode = 'ABOVE_SURFACE'
                    self._hover_base_constraint.track_axis = 'TRACK_Z'
                    self._hover_base_constraint.distance = _hover_base_distance
                    # float(cfg['hoverBaseDistance'])
        ####################################################################################### target object creation #

        bpy.context.scene['OAISYS_SENSOR_BASE_LOCATION'] = self._sensor_base.location
        bpy.context.scene['OAISYS_SENSOR_BASE_QUATERNION'] = self._sensor_base.rotation_quaternion

    def set_stages(self, stages):
        if self._hover_base_constraint is not None:
            _stage = stages[self._cfg["GENERAL"]["hoverBaseStage"]]
            if _stage is not None:
                self._hover_base_constraint.target = _stage
            else:
                raise ("Stage for base hovering mode was not found!")

        if self._hover_target_constraint is not None:
            _stage = stages[self._cfg["GENERAL"]["hoverTargetStage"]]
            if _stage is not None:
                self._hover_target_constraint.target = _stage
            else:
                raise ("Stage for target hovering mode was not found!")

        bpy.context.scene['OAISYS_SENSOR_BASE_LOCATION'] = self._sensor_base.location
        bpy.context.scene['OAISYS_SENSOR_BASE_QUATERNION'] = self._sensor_base.rotation_quaternion

    def set_assets(self, assets):
        if self._hover_base_constraint is not None:
            _assets = assets[self._cfg["GENERAL"]["baseAsset"]]
            if _assets is not None:
                self._hover_base_constraint.target = _assets
            else:
                raise ("Assets for trajectory generation mode was not found!")

    def _create_sensors(self, cfg):
        """ create all sensors defined in cfg
        Args:
            cfg:            sensors part of cfg from sensor handle [dict]
        Returns:
            ErrorCode:      error code; 0 if sucessful
        """

        # go through cfg and add sensors ###############################################################################
        for sensor in cfg:
            try:
                # import module and create class #######################################################################
                _module_name = "src.sensors.sensors." + sensor["type"]
                _module = importlib.import_module(_module_name)
                _class = getattr(_module, sensor["type"])
                _sensor = _class()
                ################################################################ end of import module and create class #

                # update sensor cfg
                _sensor.update_cfg(cfg=sensor["sensorParams"])

                # create sensor
                _sensor.create()

                # add sensor to list
                self._sensor_list.append(_sensor)

            except ImportError:
                # manage import error
                raise Exception("Cannot add sensor")
                return -1

        return 0
        ######################################################################## end of go through cfg and add sensors #

    def _attach_sensors_to_base(self):
        """ parent sensors to base
            Better option would be to use child of modifier, however CHILD_OF modifier has a bug and creates an offset;
            offset can be delete by setting inverse and reset of the modifier
            _child_constraint = _sensor.constraints.new(type = 'CHILD_OF')
            _child_constraint.target = self._sensor_base

            using parenting instead; not so much flexability, but gets the job done

        Args:
            None
        Returns:
            None
        """

        # go through all sensors and attach to base ####################################################################
        for sensor_obj in self._sensor_list:
            # get sensor handle
            _sensor = sensor_obj.get_sensor()

            # set parent
            _sensor.parent = self._sensor_base
        ############################################################# end of go through all sensors and attach to base #

    def _create_robot_mesh(self, cfg):
        """ create robot mesh and attach to sensor base

        Args:
            cfg:        information about robot mesh
        Returns:
            None
        """

        if "MESH_FOLLOWER" in cfg:
            mesh_follower_cfg = cfg["MESH_FOLLOWER"]
            mesh_file_path = mesh_follower_cfg["meshFilePath"]

            # load/get objects
            # get mesh name from cfg file
            _mesh_object_file_name = os.path.basename(os.path.normpath(os.path.splitext(mesh_file_path)[0]))
            if 'meshInstanceName' in mesh_follower_cfg:
                if not mesh_follower_cfg['meshInstanceName'] == "":
                    _mesh_object_file_name = mesh_follower_cfg['meshInstanceName']
            _local_mesh_name = 'mesh_MeshFollow_' + _mesh_object_file_name

            # def mesh
            _mesh = None

            if not _mesh:
                bpy.ops.wm.append(directory=os.path.join(mesh_file_path, "Object"),
                                  link=False,
                                  filename=_mesh_object_file_name)
                _mesh = bpy.context.scene.objects[_mesh_object_file_name]
                self.mesh = _mesh
                _mesh.name = _local_mesh_name

            # pose of robot mesh
            _mesh.rotation_mode = 'QUATERNION'
            _mesh.location = mesh_follower_cfg["transformation"][:3]
            _mesh.rotation_quaternion = mesh_follower_cfg["transformation"][3:]

            # attach to sensor base
            _mesh.parent = self._sensor_base

    def _read_pose_from_CSV(self, csv_file_path):

        # def local var
        _pose_list = []

        # go through csv file and get data #############################################################################
        with open(csv_file_path) as csv_file:
            # define csv reader
            _csv_reader = csv.reader(csv_file, delimiter=',')

            # local csv line counter
            _line_count = 0

            # iterate through csv lines ################################################################################
            for row in _csv_reader:
                # def local pose var
                _pose = np.zeros((8))

                # read frame ID
                _pose[0] = int(row[0])

                # read position
                _pose[1] = float(row[1])  # posX
                _pose[2] = float(row[2])  # posY
                _pose[3] = float(row[3])  # posZ

                # read quaternion
                _pose[4] = float(row[4])  # quatW
                _pose[5] = float(row[5])  # quatX
                _pose[6] = float(row[6])  # quatY
                _pose[7] = float(row[7])  # quatZ

                # append retrieved pose sample to list
                _pose_list.append(_pose)
            ######################################################################### end of iterate through csv lines #
        ###################################################################### end of go through csv file and get data #

        # return pose list
        return _pose_list

    def quaternion_multiply(Q0, Q1):
        """
        Multiplies two quaternions.

        Input
        :param Q0: A 4 element array containing the first quaternion (q01,q11,q21,q31)
        :param Q1: A 4 element array containing the second quaternion (q02,q12,q22,q32)

        Output
        :return: A 4 element array containing the final quaternion (q03,q13,q23,q33)

        """
        # Extract the values from Q0
        w0 = Q0[0]
        x0 = Q0[1]
        y0 = Q0[2]
        z0 = Q0[3]

        # Extract the values from Q1
        w1 = Q1[0]
        x1 = Q1[1]
        y1 = Q1[2]
        z1 = Q1[3]

        # Computer the product of the two quaternions, term by term
        Q0Q1_w = w0 * w1 - x0 * x1 - y0 * y1 - z0 * z1
        Q0Q1_x = w0 * x1 + x0 * w1 + y0 * z1 - z0 * y1
        Q0Q1_y = w0 * y1 - x0 * z1 + y0 * w1 + z0 * x1
        Q0Q1_z = w0 * z1 + x0 * y1 - y0 * x1 + z0 * w1

        # Create a 4 element array containing the final quaternion
        final_quaternion = np.array([Q0Q1_w, Q0Q1_x, Q0Q1_y, Q0Q1_z])

        # Return a 4 element array containing the final quaternion (q02,q12,q22,q32)
        return final_quaternion

    Q0 = np.random.rand(4)  # First quaternion
    Q1 = np.random.rand(4)  # Second quaternion
    Q = quaternion_multiply(Q0, Q1)

    # print("{0} x {1} = {2}".format(Q0, Q1, Q))

    def quaternion_multiply(self, q1, q2):
        w0, x0, y0, z0 = q1

    def _deterministic(self, cfg, mesh_list):
        """ deterministic movement option; read movement from csv file
        Args:
            cfg:                        general part of cfg from sensor handle [dict]
            mesh_list:                  list of all meshes created by OAISYS [list]
        Returns:
            pose_list:                  list of random poses [list]
            target_pose_list:           No target pose list, therefore return None [None]
        """

        # read pose from csv file
        _pose_list = self._read_pose_from_CSV(cfg["sensorMovementPose"])

        # add static offset if requested
        if "deterministicSensorOffsetPos" in cfg:
            for idx, pose in enumerate(_pose_list):
                pose[1:4] += cfg["deterministicSensorOffsetPos"]
                _pose_list[idx] = pose

        # interpolate between poses
        if "interpolationMode" in cfg:
            _pose_list = self._pose_interpolate(pose_list=_pose_list, interpolation_mode=cfg["interpolationMode"])

        # return movement lists
        return _pose_list, None

    def _centered_target(self, cfg, mesh_list):
        """
        Create a deterministic position with respect to the object dealt with,
        so that the object is within the FOV of the sensor.

        Args:
        =
            - cfg (dict):                       general part of cfg from sensor handle
            mesh_list:                          list of all meshes created by OAISYS [list]
            - scale_factor ():

        Returns:
        =
            - _pose_list (list):                6D random pose determined from distance to object
        """
        for mesh in mesh_list:
            if mesh["name"] == cfg["targetObject"]:
                target_obj = mesh["mesh_handle"]

        _pose_list, _target_list = self._create_origin_centered_sensor(
            target_obj=target_obj,
            scale_factor=cfg["sensorDistanceScale"],
            num_samples=cfg["numSamples"],
            landing_mode=cfg["landingMode"],
            final_approach_distance=cfg["finalApproachDistance"]
        )

        return _pose_list, _target_list

    def _create_origin_centered_sensor(self, target_obj, scale_factor, num_samples, landing_mode, final_approach_distance=1.0):
        """
        Create sensor positions centered around the origin based on object geometry and trajectory type.

        Args:
        =
        - target_obj (blender object) object to use as center
        - scale_factor (tuple): Range for scaling the sensor distance.
        - num_samples (int): Number of pose samples to generate.
        - landing_mode (bool): Whether to use landing mode for sensor positioning.
        - final_approach_distance (float): Final approach distance as a factor of the asteroid's max diameter.

        Returns:
        =
        - pose_list (list): List of pose samples for sensor position.
        - target_list (list): List of pose samples for target position.
        """

        vertices, faces = get_single_mesh_data(target_obj)
        origin = np.array([0, 0, 0])
        center_of_mass = compute_center_of_mass(vertices, faces, density=1)
        furthest_point, furthest_distance = find_furthest_point(vertices, center_of_mass)
        furthest_point = np.abs(furthest_point)

        print(f"Landing MODE? {landing_mode}")
        print(f"Landign Distance Scale? {final_approach_distance}")

        # Determine the sign of the coordinates based on the trajectory type
        if ot.trajectory_mode == "direct":
            signs = np.array([1, -1, np.random.uniform(-1, 1)])
        elif ot.trajectory_mode == "retrograde":
            signs = np.array([-1, 1, np.random.uniform(-1, 1)])
        elif ot.trajectory_mode == "polar":
            signs = np.array([1, -1, np.random.uniform(-1, 1)])
        else:
            print(f"Unexpected trajectory mode: {ot.trajectory_mode}")
        signs = np.array([-1, 1, np.random.uniform(-1, 1)])
        # Apply the signs to the furthest point
        furthest_point *= signs

        # Calculate initial sensor position
        initial_scale = random.uniform(scale_factor[0], scale_factor[1])
        initial_distance = furthest_distance * initial_scale
        direction_vector = furthest_point - origin
        direction_vector_normalized = direction_vector / np.linalg.norm(direction_vector)
        initial_sensor_position = origin + direction_vector_normalized * initial_distance

        # Calculate rotation to face the origin
        angle = np.arccos(np.dot(direction_vector_normalized, np.array([0, 0, 1])))
        axis = np.cross(np.array([0, 0, 1]), direction_vector_normalized)
        axis /= np.linalg.norm(axis)
        half_angle = -angle / 2
        qw = np.cos(half_angle)
        qx, qy, qz = np.sin(half_angle) * axis

        _pose_list, _target_list = [], []

        for i in range(num_samples):
            _pose, _target = np.zeros((8)), np.zeros((8))
            pose_index = i + 1  # frame ID
            _pose[0], _target[0] = pose_index, pose_index

            if landing_mode:
                # Calculate current sensor position
                progress = i / (num_samples - 1)
                final_distance = furthest_distance * final_approach_distance
                current_distance = initial_distance + (final_distance - initial_distance) * progress
                current_sensor_position = origin + direction_vector_normalized * current_distance

                _pose[1:4] = current_sensor_position
            else:
                # Keep the same initial position for all samples
                _pose[1:4] = initial_sensor_position

            # Set rotation (same for all poses)
            _pose[4:] = [qx, qy, qz, qw]

            # Set target position (always at origin)
            _target[1:] = [0, 0, 0, qx, qy, qz, qw]

            # Add pose sample to list
            _pose_list.append(_pose)
            _target_list.append(_target)

        return _pose_list, _target_list

    def _random_euclidean(self, cfg, mesh_list):
        """ random euclidean movement option;  create random pose within box
        Args:
            cfg:                        general part of cfg from sensor handle [dict]
            mesh_list:                  list of all meshes created by OAISYS [list]
        Returns:
            pose_list:                  list of random poses [list]
            target_pose_list:           No target pose list, therefore return None [None]
        """

        # create random poses
        _pose_list = self._create_euclidean_random_sensor_movements(min_pos=cfg["randomEuclideanPosMin"],
                                                                    max_pos=cfg["randomEuclideanPosMax"],
                                                                    num_samples=cfg["numSamples"],
                                                                    min_euler=cfg["randomEuclideanEulerMin"],
                                                                    max_euler=cfg["randomEuclideanEulerMax"])

        # return movement lists
        return _pose_list, None

    def log_step(self, keyframe):
        """ log step function is called for every new sample in of the batch; should be overwritten by custom class
            OVERWRITE!
        Args:
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        if ((self._stepping_counter - 1) % self._trigger_interval) == 0:
            # go through all sensors and execute step function
            for sensor_obj in self._sensor_list:
                # self.current_sensor_q = cp.deepcopy(sensor_obj.rotation_quaternion)
                self.current_sensor_q = self._sensor_base_constraint.rotation_euler.to_quaternion()
                self.current_sensor_q2 = self._sensor_base.rotation_quaternion

                # sensor_obj.log_step(keyframe=keyframe)
                pose = [str(self._sensor_base_constraint.location[0]), str(self._sensor_base_constraint.location[1]),
                        str(self._sensor_base_constraint.location[2]),
                        str(self.current_sensor_q[0]), str(self.current_sensor_q[1]),
                        str(self.current_sensor_q[2]), str(self.current_sensor_q[3])]
                # sensor_obj.log_step(keyframe=keyframe)
                pose2 = [str(self._sensor_base.location[0]), str(self._sensor_base.location[1]),
                         str(self._sensor_base.location[2]),
                         str(self.current_sensor_q2[0]), str(self.current_sensor_q2[1]),
                         str(self.current_sensor_q2[2]), str(self.current_sensor_q2[3])]

                # self._logger.log_pose(f"{self._sensor_base.name}", pose)

    def _random_euclidean_target(self, cfg, mesh_list):
        """ random euclidean target movement option;  create random pose for base and target object within box
        Args:
            cfg:                        general part of cfg from sensor handle [dict]
            mesh_list:                  list of all meshes created by OAISYS [list]
        Returns:
            pose_list:                  list of random poses [list]
            target_pose_list:           list of target poses [list]
        """

        # create random poses for base and target
        _pose_list, _target_pose_list = self._create_euclidean_random_sensor_movements( \
            min_pos=cfg["randomEuclideanPosMin"],
            max_pos=cfg["randomEuclideanPosMax"],
            num_samples=cfg["numSamples"],
            target_active=True,
            min_target_pos=cfg["randomTargetPosMin"],
            max_target_pos=cfg["randomTargetPosMax"],
            min_target_euler=cfg["randomTargetEulerMin"],
            max_target_euler=cfg["randomTargetEulerMax"])

        # return movement lists
        return _pose_list, _target_pose_list

    def _euler_to_quaternion(self, angles):

        roll = angles[0]
        pitch = angles[1]
        yaw = angles[2]

        qx = np.sin(roll / 2) * np.cos(pitch / 2) * np.cos(yaw / 2) - np.cos(roll / 2) * np.sin(pitch / 2) * np.sin(
            yaw / 2)
        qy = np.cos(roll / 2) * np.sin(pitch / 2) * np.cos(yaw / 2) + np.sin(roll / 2) * np.cos(pitch / 2) * np.sin(
            yaw / 2)
        qz = np.cos(roll / 2) * np.cos(pitch / 2) * np.sin(yaw / 2) - np.sin(roll / 2) * np.sin(pitch / 2) * np.cos(
            yaw / 2)
        qw = np.cos(roll / 2) * np.cos(pitch / 2) * np.cos(yaw / 2) + np.sin(roll / 2) * np.sin(pitch / 2) * np.sin(
            yaw / 2)

        return [qx, qy, qz, qw]

    def _create_random_pose_sample(self, min_pos, max_pos, min_euler, max_euler):
        """ create random pose
        Args:
            min_pos:        boundary values for minimum position [x,y,z] [numpy]
            max_pos:        boundary values for maximum position [x,y,z] [numpy]
            min_euler:       boundary values for minimum quaternion [angle_x,angle_y,angle_z] [numpy]
            max_euler:       boundary values for maximum quaternion [angle_x,angle_y,angle_z] [numpy]
        Returns:
            _pose:          6D random pose vector (7 dim) [numpy]
        """

        # def local var
        _pose = np.zeros((7))
        _euler = np.zeros((3))

        # random positions
        _pose[0] = random.uniform(min_pos[0], max_pos[0])
        _pose[1] = random.uniform(min_pos[1], max_pos[1])
        _pose[2] = random.uniform(min_pos[2], max_pos[2])

        # random angles
        _euler[0] = random.uniform(min_euler[0], max_euler[0])
        _euler[1] = random.uniform(min_euler[1], max_euler[1])
        _euler[2] = random.uniform(min_euler[2], max_euler[2])

        # convert to quaternion
        _pose[3:7] = self._euler_to_quaternion(angles=_euler)

        # return random pose sample
        return _pose

    def _create_euclidean_random_sensor_movements(self,
                                                  min_pos, max_pos,
                                                  num_samples,
                                                  min_euler=[0, 0, 0], max_euler=[0, 0, 0],
                                                  target_active=False,
                                                  min_target_pos=[0, 0, 0], max_target_pos=[0, 0, 0],
                                                  min_target_euler=[0, 0, 0], max_target_euler=[0, 0, 0]):
        """ create list of random poses, with or without random target pose list
        Args:
            min_pos:                            boundary values for minimum position [x,y,z] [numpy]
            max_pos:                            boundary values for maximum position [x,y,z] [numpy]
            num_samples:                        number of pose samples [uint]
            min_euler (optional):               boundary values for minimum quaternion [angle_x,angle_y,angle_z] [numpy]
            max_euler (optional):               boundary values for maximum quaternion [angle_x,angle_y,angle_z] [numpy]
            target_active (optional):           should target be calculated as well [boolean]
            min_target_pos:                     boundary values for minimum target position [x,y,z] [numpy]
            max_target_pos:                     boundary values for maximum target position [x,y,z] [numpy]
            min_target_euler (optional):        boundary values for minimum target quaternion [angle_x,angle_y,angle_z]
                                                                                                                [numpy]
            max_target_euler (optional):        boundary values for maximum target quaternion [angle_x,angle_y,angle_z]
                                                                                                                [numpy]
        Returns:
            _pose, _target_pose (optional):     return random list of poses [numpy]
        """

        # def of local vars ############################################################################################
        _pose_list = []
        _target_pose_list = []
        ##################################################################################### end of def of local vars #

        # create num_samples samples of random poses ###################################################################
        for pose_index in range(0, num_samples):
            # create var
            _pose = np.zeros((8))

            # frame ID
            _pose[0] = pose_index + 1

            # create random pose sample for base
            _pose[1:] = self._create_random_pose_sample(min_pos=min_pos,
                                                        max_pos=max_pos,
                                                        min_euler=min_euler,
                                                        max_euler=max_euler)

            # add pose sample to list
            _pose_list.append(_pose)

            # create random target poses, if requested
            if target_active:
                # create var
                _target_pose = np.zeros((8))

                # frame ID
                _target_pose[0] = pose_index + 1

                # create random pose sample for target
                _target_pose[1:] = self._create_random_pose_sample(min_pos=min_target_pos,
                                                                   max_pos=max_target_pos,
                                                                   min_euler=min_target_euler,
                                                                   max_euler=max_target_euler)

                # set offset
                _target_pose[1:4] += _pose[1:4]

                # add pose sample to list
                _target_pose_list.append(_target_pose)
        ############################################################ end of create num_samples samples of random poses #

        # return requested values
        if target_active:
            return _pose_list, _target_pose_list
        else:
            return _pose_list, None

    def _pose_interpolate(self, pose_list, interpolation_mode="static"):
        """ interpolate missing poses in pose_list with a variety of options
        Args:
            pose_list:              list of poses to be interpolated [list]
            interpolation_mode:     mode of interpolation [string]
                                        possible modes: "none":     return same pose_list as inputed
                                                        "static":   copy value from previous pose in gaps
                                                        "step":     copy value from previous pose till the half, the
                                                                    other half copy pose of next pose in it
                                                        "linear":   linear interpolation of two poses
        Returns:
            _pose_list:             interpolated pose list [list]
        """

        # def local var
        _pose_list = None

        # use interpolation mode as requested ##########################################################################
        if "none" == interpolation_mode:
            _pose_list = pose_list

        if "static" == interpolation_mode:
            raise Exception("Not implemented yet!")

        if "step" == interpolation_mode:
            raise Exception("Not implemented yet!")

        if "linear" == interpolation_mode:
            raise Exception("Not implemented yet!")
        ################################################################### end of use interpolation mode as requested #

        # return interpolated pose list
        return _pose_list

    def create(self, mesh_list):
        """ create function
        Args:
            mesh_list:      list of all meshes created by OAISYS [list]
        Returns:
            ErrorCode:      error code; 0 if sucessful
        """

        # reset all local vars
        # self._reset()

        # create sensor base
        self._create_base_object(self._cfg["GENERAL"], mesh_list)

        # create sensors
        self._create_sensors(self._cfg["SENSORS"])

        # create robot msh
        self._create_robot_mesh(self._cfg["GENERAL"])

        # attach sensors to base
        self._attach_sensors_to_base()

    def step(self, keyframe):
        """ overwrite step function
        Args:
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        self._stepping_counter += 1

        if (((self._stepping_counter - 1) % self._trigger_interval) == 0):

            # increase pose counter
            self._pose_index += 1

            # move base pose one position forward ##########################################################################
            # get pose at pose_index
            _pose = self._sensor_pose_list[self._pose_index - 1]
            # update location and rotation of base sensor
            self._sensor_base_constraint.rotation_mode = 'QUATERNION'
            self._sensor_base.rotation_mode = 'QUATERNION'
            self._sensor_base_constraint.location = (_pose[1], _pose[2], _pose[3])
            self._sensor_base_constraint.rotation_quaternion = (_pose[4], _pose[5], _pose[6], _pose[7])
            ################################################################### end of move base pose one position forward #

            # update location and rotation of target sensor ################################################################
            if self._target_object_active:
                # move target pose one position forward
                _target_object_pose = self._target_pose_list[self._pose_index - 1]

                # set position of target object
                self._target_object.location = (_target_object_pose[1],
                                                _target_object_pose[2],
                                                _target_object_pose[3])

                # set quaternion of target object
                self._target_object.rotation_quaternion = (_target_object_pose[4],
                                                           _target_object_pose[5],
                                                           _target_object_pose[6],
                                                           _target_object_pose[7])
            ######################################################### end of update locaiton and rotation of target sensor #

            # calc hover base z noise ######################################################################################
            if self._hover_target_constraint is not None:
                if "hoverBaseDistanceNoise" in self._cfg["GENERAL"]:
                    if len(self._cfg["GENERAL"]['hoverBaseDistance']) <= 1:
                        hover_min = self._cfg["GENERAL"]['hoverBaseDistance'][0]
                    else:
                        hover_min = self._cfg["GENERAL"]['hoverBaseDistance'][0]
                        hover_max = self._cfg["GENERAL"]['hoverBaseDistance'][1]
                    _hover_base_distance = random.uniform(hover_min, hover_max)
                    _noise_value = float(_hover_base_distance)
                    _distance_random = random.uniform(0, _noise_value)
                    _distance_offset_value = _hover_base_distance - _distance_random / 2.0
                    self._hover_base_constraint.distance = _distance_offset_value
            ############################################################################### end of calc hover base z noise #

            # set sensor base ##############################################################################################
            bpy.context.view_layer.update()
            self._sensor_base.matrix_world = self._sensor_base_constraint.matrix_world
            ####################################################################################### end of set sensor base #

            # add roll angle ###############################################################################################
            if self._cfg["GENERAL"]["sensorMovementType"] != "deterministic":  # TODO fix
                _roll_angle = random.uniform(self._roll_limits[0], self._roll_limits[1])
                self._sensor_base.rotation_euler.rotate_axis("Z", _roll_angle)
                bpy.context.view_layer.update()
            ######################################################################################## end of add roll angle #

            # go through all sensors and execute step function
            for sensor_obj in self._sensor_list:
                sensor_obj.step(keyframe=keyframe)

            # set keyframes if requested ###################################################################################
            if keyframe >= 0:
                # set keyframe for location and rotation of base sensor
                self._sensor_base.keyframe_insert('location', frame=keyframe)
                self._sensor_base.keyframe_insert('rotation_euler', frame=keyframe)
                self._sensor_base.keyframe_insert('rotation_quaternion', frame=keyframe)
                self._sensor_base_constraint.keyframe_insert('location', frame=keyframe)
                self._sensor_base_constraint.keyframe_insert('rotation_euler', frame=keyframe)
                self._sensor_base_constraint.keyframe_insert('rotation_quaternion', frame=keyframe)

                # set keyframe for hover constraint
                if self._hover_base_constraint is not None:
                    self._hover_base_constraint.keyframe_insert('distance', frame=keyframe)

                # set interpolation of all keyframes #######################################################################
                _fcurves = self._sensor_base.animation_data.action.fcurves
                for fcurve in _fcurves:
                    for kf in fcurve.keyframe_points:
                        kf.interpolation = 'CONSTANT'

                _fcurves = self._sensor_base_constraint.animation_data.action.fcurves
                for fcurve in _fcurves:
                    for kf in fcurve.keyframe_points:
                        kf.interpolation = 'CONSTANT'
                # set interpolation of all keyframes########################################################################

                # set keyframe for target ##################################################################################
                if self._target_object_active:
                    self._target_object.keyframe_insert('location', frame=keyframe)
                    self._target_object.keyframe_insert('rotation_quaternion', frame=keyframe)

                    # set interpolation of all keyframes ###################################################################
                    _fcurves = self._target_object.animation_data.action.fcurves
                    for fcurve in _fcurves:
                        for kf in fcurve.keyframe_points:
                            kf.interpolation = 'CONSTANT'
                    # set interpolation of all keyframes####################################################################
                ########################################################################### end of set keyframe for target #
            ############################################################################ end of set keyframes if requested #

        # update blender sensor env
        bpy.context.scene['OAISYS_SENSOR_BASE_LOCATION'] = self._sensor_base.location
        bpy.context.scene['OAISYS_SENSOR_BASE_QUATERNION'] = self._sensor_base.rotation_quaternion

    def set_log_folder(self, log_folder_path):
        for sensor_obj in self._sensor_list:
            sensor_obj.set_log_folder(log_folder_path)

    def get_sensor_list(self):
        """ return self._sensor_list
        Args:
            None
        Returns:
            return self._sensor_list
        """

        return self._sensor_list
