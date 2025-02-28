# blender imports
import bpy

# utility imports
import numpy as np
import os
import random
import copy as cp

from src.assets.TSSMesh import TSSMesh
from src.tools.mesh_loader import load_mesh

from mathutils import Matrix, Vector, Quaternion

# trajectory generation imports
from src.tools.trajectory.ObjectTrajectory import *
import src.tools.trajectory.ObjectTrajectory as ot

def get_loc_matrix(location):
    return Matrix.Translation(location)


def get_rot_matrix(rotation):
    return rotation.to_matrix().to_4x4()


def get_sca_matrix(scale):
    scale_mx = Matrix()
    for i in range(3):
        scale_mx[i][i] = scale[i]
    return scale_mx

def get_random_value(x):
    if not isinstance(x, list):
        return x
    else:
        if isinstance(x[0], int):
            return random.randint(x[0], x[1])
        elif isinstance(x[0], float):
            return random.uniform(x[0], x[1])
        else:
            NotImplementedError("Type not suitable for random number generator!")

class MeshAsteroid(TSSMesh):
    """docstring for MeshAsteroid"""

    def __init__(self):
        super(MeshAsteroid, self).__init__()
        # class vars ###################################################################################################
        self._single_stage = None
        self._mesh_file_path = None
        self._min_number_instances = None
        self._max_number_instances = None
        self._instance_size_variation_min = None
        self._instance_size_variation_max = None
        self._default_size = None
        self._strength_random_scale = False
        self._random_rotation_enabled = False
        self._emitter_file_path = None
        self._emitter = None
        self._rotation_option_mode = None
        self._rotation_option_factor = None
        self._rotation_option_phase = None
        self._rotation_option_phase_random = None
        self._mix_shader_node = None
        self._num_labels_per_channel = 15
        self._num_instance_label_per_channel = 51
        self._max_instances_labels = self._num_instance_label_per_channel * self._num_instance_label_per_channel \
                                     * self._num_instance_label_per_channel
        self._node_tree = None
        self._particle_system = None
        self._instance_label_active = False
        self._random_switch_on_off = False
        self._instance_add_node = None
        self._label_ID_Node = None
        self._instance_switch_node = None

        self._mix_shader_node_list = []
        self._instance_switch_node_list = []
        self._label_ID_Node_list = []
        self.mesh = None
        self.module_active = True

        # trajectory parameters
        self._trajectory_type = None
        self._trajectory_probability_list = []       
        self._trajectory_mode = None
        self._rotational_period = None
        self._observation_time = None
        self.current_mesh_q = None
        self._initial_point = None
        self.distance = None
        self.landing_mode = False               # Unless specified, no landing
        self.final_approach_distance = 1.1      # At 10% of the asteroid's size, from the surface 
        ############################################################################################ end of class vars #

    def reset(self):
        """ reset all local vars
        Args:
            None
        Returns:
            None
        """

        # class vars ###################################################################################################
        self._single_stage = None  # blender stage object [blObject]
        self._mesh_file_path = None
        self._min_number_instances = None
        self._max_number_instances = None
        self._instance_size_variation_min = None
        self._instance_size_variation_max = None
        self._default_size = None
        self._strength_random_scale = False
        self._random_rotation_enabled = False
        self._emitter_file_path = None
        self._emitter = None
        self._rotation_option_mode = None
        self._rotation_option_factor = None
        self._rotation_option_phase = None
        self._rotation_option_phase_random = None
        self._mix_shader_node = None
        self._num_labels_per_channel = 15
        self._num_instance_label_per_channel = 51
        self._max_instances_labels = self._num_instance_label_per_channel * self._num_instance_label_per_channel \
                                     * self._num_instance_label_per_channel
        self._node_tree = None
        self._particle_system = None
        self._instance_label_active = False
        self._random_switch_on_off = False
        self._instance_add_node = None
        self._label_ID_Node = None
        self._instance_switch_node = None

        self._mix_shader_node_list = []
        self._instance_switch_node_list = []
        self._label_ID_Node_list = []
        self.mesh = None
        self.module_active = True

        # trajectory parameters
        self._trajectory_type = None
        self._trajectory_probability_list = []       
        self._trajectory_mode = None
        self._rotational_period = None
        self._observation_time = None
        self.current_mesh_q = None
        self._initial_point = None
        self.distance = None
        ############################################################################################ end of class vars #

    def create_mesh(self, idx, path, name=None):
        _mesh_object_file_name = os.path.basename(os.path.normpath(os.path.splitext(path)[0]))

        if name is not None:
            if not name == "":
                _mesh_object_file_name = name

        # build up full mesh name
        _local_mesh_name = f"mesh_Asteroid_{_mesh_object_file_name}_{idx}"

        _mesh_name = load_mesh(path, obj_name=_mesh_object_file_name)[0]
        _mesh = bpy.context.scene.objects[_mesh_name]
        # scale
        max_dim = max(np.array(_mesh.dimensions))

        scale = random.randint(400, 600) / max_dim
        self._scale_factor = scale
        _mesh.scale = Vector((scale, scale, scale))
        bpy.ops.object.transform_apply(scale=True)
        _mesh.name = _local_mesh_name
        print(f"mesh name: {_mesh.name}")

        return _mesh


    def create(self, instance_id_offset=0, materials=None):
        """ create function
        Args:
            instance_id_offset:                                     instance offset ID [int]
            materials:                                              list of all OAISYS materials [list]
        Returns:
            _current_real_particle_count:                              particle count [int]
            _current_real_particle_label_count
        """

        if "randomSwitchOnOff" in self._cfg:
            if self._cfg["randomSwitchOnOff"]:
                if "activationProbability" in self._cfg:
                    _activation_p = self._cfg["activationProbability"]
                else:
                    _activation_p = 0.5

                # gamble
                if not random.random() < _activation_p:
                    self.module_active = False
                    return 0, 0

        self.module_active = True
        # TODO: research module_active

        self._mesh_file_path = self._cfg['meshFilePath']
        mesh_settings_cfg = self._cfg

        # load/get objects #############################################################################################
        # get mesh name from cfg file
        _mesh_object_file_name = os.path.basename(os.path.normpath(os.path.splitext(self._mesh_file_path)[0]))
        if 'meshInstanceName' in self._cfg:
            if not self._cfg['meshInstanceName'] == "":
                _mesh_object_file_name = self._cfg['meshInstanceName']

        # build up full mesh name
        # Split the file path by '/'
        path_parts = self._mesh_file_path.split('/')[-1].split('.')[0]
        # # Get the last part of the path which contains the file name
        # file_name_with_extension = path_parts[-1]
        # # Split the file name by '.' to separate the name and extension
        # name_parts = file_name_with_extension.split('.')
        # # Get the name of the object
        # object_name = name_parts[0]
        _local_mesh_name = 'mesh_MeshAsteroid_' + _mesh_object_file_name # self._cfg["name"]

        # load particle object #########################################################################################
        # def mesh
        _mesh = None

        if not _mesh:
            # load obj file
            _mesh = self.create_mesh(0, self._mesh_file_path, _mesh_object_file_name)
            self.mesh = _mesh
            _mesh.name = _local_mesh_name

            # rotate object before using it, if requested
            if "location" in self._cfg:
                if isinstance(self._cfg["location"], list):
                    _mesh.location[0] = float(self._cfg["location"][0])
                    _mesh.location[1] = float(self._cfg["location"][1])
                    _mesh.location[2] = float(self._cfg["location"][2])
                elif self._cfg["location"] == "origin":
                    # Set location to origin (0, 0, 0)
                    _mesh.location[0] = 0.0
                    _mesh.location[1] = 0.0
                    _mesh.location[2] = 0.0
                elif self._cfg["location"] == "trajectory_simulation":
                    # Handle trajectory simulation
                    # Assuming trajectorySimulation is a list of six numbers [min_x, max_x, min_y, max_y, min_z, max_z]
                    if isinstance(self._cfg["trajectorySimulation"], list) and len(self._cfg["trajectorySimulation"]) == 6:
                        min_x, max_x, min_y, max_y, min_z, max_z = map(float, self._cfg["trajectorySimulation"])

                        # Generate random coordinates within the specified range
                        random_x = np.random.uniform(min_x, max_x)
                        random_y = np.random.uniform(min_y, max_y)
                        random_z = np.random.uniform(min_z, max_z)

                        # Set the object's location to the generated random coordinates
                        _mesh.location[0] = random_x
                        _mesh.location[1] = random_y
                        _mesh.location[2] = random_z
                    else:
                        print("Invalid configuration for 'trajectorySimulation'. Please specify a list of 6 numbers [min_x, max_x, min_y, max_y, min_z, max_z].")
                else:
                    print("\nIncorrect assignment of object's initial position. Make sure you specify 'origin', 'trajectory_simulation', or specific coordinates.")

            if "random_rotation" in self._cfg:
                _mesh.rotation_euler[0] = np.radians(np.random.uniform(0, 360))
                _mesh.rotation_euler[1] = np.radians(np.random.uniform(0, 360))
                _mesh.rotation_euler[2] = np.radians(np.random.uniform(0, 360))

            # TODO: check if random_rotation requires an additional if statement for how it will rotate

            if "rotation_deg" in self._cfg:
                _mesh.rotation_euler[0] = (float(self._cfg["rotation_deg"][0]) * np.pi) / 180
                _mesh.rotation_euler[1] = (float(self._cfg["rotation_deg"][1]) * np.pi) / 180
                _mesh.rotation_euler[2] = (float(self._cfg["rotation_deg"][2]) * np.pi) / 180

            if "rotation_rad" in self._cfg:
                _mesh.rotation_euler[0] = float(self._cfg["rotation_rad"][0])
                _mesh.rotation_euler[1] = float(self._cfg["rotation_rad"][1])
                _mesh.rotation_euler[2] = float(self._cfg["rotation_rad"][2])

            if "scale" in self._cfg:
                raise "scale does not work!"
                _mesh.dimensions[0] = float(self._cfg["scale"][0])
                _mesh.dimensions[1] = float(self._cfg["scale"][1])
                _mesh.dimensions[2] = float(self._cfg["scale"][2])

            bpy.context.view_layer.update()

                        # save current rotation
            self.mesh.rotation_mode = 'QUATERNION'
            self.current_mesh_q = cp.deepcopy(self.mesh.rotation_quaternion)

            # apply scale and rotation
            bpy.context.view_layer.objects.active = _mesh
            mx = _mesh.matrix_world
            loc, rot, sca = mx.decompose()
            # _mesh.transform_apply(location=False, rotation=False, scale=True)
            # bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            applymx = get_loc_matrix(loc) @ get_rot_matrix(Quaternion(rot)) @ get_sca_matrix(Vector.Fill(3, 1))

            _mesh.matrix_world = applymx
            # bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
        ################################################################################### end of load particle object #       

        # displacement
        if "assetDisplacementParams" in self._cfg:
            _disp_cfg = self._cfg['assetDisplacementParams']
            if _disp_cfg['assetDisplacementActive']:

                # create empty object for noise pattern
                empty_obj = bpy.data.objects.new(self.mesh.name + "_noise_Empty", None)
                bpy.context.scene.collection.objects.link(empty_obj)
                empty_obj.location[0] = random.uniform(-1000., 1000.)
                empty_obj.location[1] = random.uniform(-1000., 1000.)
                empty_obj.location[2] = random.uniform(-1000., 1000.)
                bpy.context.view_layer.update()

                # setup general disp properties ############################################################################
                _disp_modifier = self._add_displacement(bl_object=self.mesh)
                _disp_modifier.mid_level = _disp_cfg['assetDisplacementMidLevel']
                _disp_modifier.strength = get_random_value(_disp_cfg['assetDisplacementStrength'])
                _disp_modifier.texture_coords = 'OBJECT'
                _disp_modifier.texture_coords_object = empty_obj
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = self.mesh
                bpy.ops.object.modifier_move_to_index(modifier=_disp_modifier.name, index=0)

                ##################################################################### end of setup general disp properties #
                # add new noise texture ####################################################################################
                _texture = bpy.data.textures.new('globalStageDisplacementTexture_' + str(1), 'MUSGRAVE')
                _noise_params = _disp_cfg['assetDisplacementNoiseParams']

                if "intensity" in _noise_params:
                    try:
                        _texture.noise_intensity = get_random_value(_noise_params["intensity"])
                    except:
                        print(f"param intensity does not exist for noise texture. Skipping param!")
                if "noise_depth" in _noise_params:
                    try:
                        _texture.noise_depth = get_random_value(_noise_params["noise_depth"])
                    except:
                        print(f"param intensity does not exist for noise texture. Skipping param!")
                if "nabla" in _noise_params:
                    try:
                        _texture.nabla = get_random_value(_noise_params["nabla"])
                    except:
                        print(f"param intensity does not exist for noise texture. Skipping param!")
                if "noise_scale" in _noise_params:
                    try:
                        _texture.noise_scale = get_random_value(_noise_params["noise_scale"])
                    except:
                        print(f"param intensity does not exist for noise texture. Skipping param!")
                # apply noise texture to stage
                _disp_modifier.texture = _texture

                bpy.ops.object.modifier_apply(modifier=_disp_modifier.name)
        else:
            print("No 'assetDisplacementParams' parameter found in cfg file!")


        # Set trajectory parameters ##############################################################################
        if "trajectoryParams" in self._cfg:
            trajectory_params = self._cfg["trajectoryParams"]
            # print("Trajectory parameters:", trajectory_params)
            if "trajectoryType" in trajectory_params:
                self._trajectory_type = trajectory_params["trajectoryType"].get("mode", None)
                # print("Trajectory type:", self._trajectory_type)
                if self._trajectory_type == "predefinedProbability":
                    self._trajectory_probability_list = trajectory_params["trajectoryType"].get("probability", [])
                    # print("Trajectory probability list:", self._trajectory_probability_list)
            if "trajectoryMode" in trajectory_params:
                self._trajectory_mode = trajectory_params["trajectoryMode"]
                print("Trajectory mode:", self._trajectory_mode)

            if "rotationPeriod" in trajectory_params:
                self._rotational_period = trajectory_params["rotationPeriod"]
                print("Rotation Period:", self._rotational_period, " h")

            if "observationTime" in trajectory_params:
                self._observation_time = trajectory_params["observationTime"]
                print("Observation Time:", self._observation_time, " h")                    
            if "landingMode" in trajectory_params:
                self.landing_mode = trajectory_params["landingMode"]
            if "finalApproachDistance" in trajectory_params:
                self.final_approach_distance = trajectory_params["finalApproachDistance"]

        else:   
            raise Exception("Trajectory parameters not found in configuration file. \n\
                            Make sure 'trajectoryParams' dictionary is present in 'meshParams' of the asset.")

        # Call set_trajectory_params here
        self._trajectory_mode = self.set_trajectory_params()

        # Set up initial and final points
        self._initial_point, self.final_point, self.distance = self.setup_initial_point()

        # add remesh modifier
        remesh_modifier = self.mesh.modifiers.new("asteroid_remesh", type='REMESH')
        remesh_modifier.mode = 'SMOOTH'
        remesh_modifier.octree_depth = 4
        remesh_modifier.use_smooth_shade = True
        bpy.ops.object.modifier_apply(modifier="asteroid_remesh")

        subdiv_modifier = self.mesh.modifiers.new("asteroid_subdiv", type="SUBSURF")
        subdiv_modifier.levels = 3
        subdiv_modifier.render_levels = 3
        bpy.ops.object.modifier_apply(modifier="asteroid_subdiv")

        self.create_material(mesh=_mesh, mesh_settings_cfg=mesh_settings_cfg, materials=materials)

        ##################################################################### end of set trajectory parameters #

        # add sub surf modifier ########################################################################################
        if "NOSUBSURF" not in self._cfg:
            subsurf_modifier = self.mesh.modifiers.new("lastSubsurf", type='SUBSURF')
            #subsurf_modifier.levels = 3  # TODO: Change to adaptive for automatic level
            self.mesh.cycles.use_adaptive_subdivision = True  # TODO:maybe shift this to higher level
            subsurf_modifier.subdivision_type = 'SIMPLE'

        ################################################################################# end of add sub surf modifier #

        # project and scale uv maps
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = _mesh
        _mesh.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.cube_project()
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.update()
        uv_layer = _mesh.data.uv_layers.active
        scale = random.uniform(2., 3.)
        for loop in _mesh.data.loops:
            uv_layer.data[loop.index].uv *= scale  #todo

        #uv_map = self.mesh.data.uv_layers['UVMap']
        #pivot = Vector((0.5, 0.5))
        #scale = Vector((5, 5))
        #for uv_index in range(len(uv_map.data)):
        #    uv_map.data[uv_index].uv = Scale2D(uv_map.data[uv_index].uv, scale, pivot)

        # TODO: it is not always 1,1!!!!

        bpy.data.materials["mesh_material_01"].node_tree.nodes["Normal Map"].inputs[0].default_value = random.uniform(0.75, 0.75)
        return 1, 1


    def create_material(self, mesh, mesh_settings_cfg, materials):
        if "assetMaterial" in mesh_settings_cfg:
            # use created material
            mesh.data.materials.clear()
            mesh.active_material = materials[mesh_settings_cfg["assetMaterial"]]
        else:
            # use material, which already comes with asset and add semantic channels
            self.create_semantic_channels(mesh=mesh, mesh_settings_cfg=mesh_settings_cfg)

    def create_semantic_channels(self, mesh, mesh_settings_cfg):
        _mesh = mesh
        _label_ID_mat = mesh_settings_cfg['passParams']['semantic_label']['labelIDVec']
        _label_ID = 0
        # go through all materials
        for material_ID, material_slot in enumerate(_mesh.material_slots):
            material = material_slot.material
            self._node_tree = material
            _global_Pos_RX = -300
            _global_Pos_RY = 2600
            _global_Pos_GX = -300
            _global_Pos_GY = 1800
            _global_Pos_BX = -300
            _global_Pos_BX = 1000

            if _label_ID < len(_label_ID_mat):
                _label_ID += 1
            else:
                _label_ID = 1

            _label_ID_vec = _label_ID_mat[_label_ID - 1]

            # create label node ######################################################################
            # calculate the corresponding label values and stack up to list
            # TODO: add condition if rendering label is even set?!
            self._instance_label_active = mesh_settings_cfg['instanceLabelActive']

            # TODO: bug? should it be _num_labels_per_channel? also in other mesh files
            _label_node, _label_ID_Node = self.create_semantic_nodes( \
                node_tree=material,
                label_ID_vec=_label_ID_vec,
                num_label_per_channel=self._num_labels_per_channel,
                node_offset=[_global_Pos_GX, _global_Pos_GY + 1500])
            ##########################################################################################

            self._label_ID_Node_list.append(_label_ID_Node)
            _label_node.inputs[0].default_value = 1
            if self._instance_label_active:

                # add particle info node
                _particle_info_node = material.node_tree.nodes.new('ShaderNodeParticleInfo')
                _particle_info_node.location = (_global_Pos_GX - 500, _global_Pos_GY + 300)

                _instance_switch_node, _instance_add_node = \
                    self._create_id_to_rgb_node_tree(node_tree=material,
                                                     num_label_per_channel=self._num_instance_label_per_channel,
                                                     instance_ID_offset=instance_id_offset,
                                                     node_offset=[_global_Pos_GX, _global_Pos_GY])

                self._instance_switch_node_list.append(_instance_switch_node)

                #_label_node.inputs[0].default_value = 1

                material.node_tree.links.new(_instance_add_node.inputs[0], _particle_info_node.outputs[0])
                material.node_tree.links.new(_instance_switch_node.inputs[1], _label_node.outputs[0])
            else:

                # create default color node
                _default_instance_color = material.node_tree.nodes.new("ShaderNodeRGB")
                _default_instance_color.location = (_global_Pos_GX, _global_Pos_GY)
                _default_instance_color.outputs[0].default_value = (0, 0, 0, 1)

                # combine label and instance channel ###########################################
                _instance_switch_node = material.node_tree.nodes.new('ShaderNodeMixRGB')
                _instance_switch_node.name = "instanceLabelsEnabled"
                _instance_switch_node.label = "instanceLabelsEnabled"
                _instance_switch_node.inputs[0].default_value = 0
                _instance_switch_node.location = (_global_Pos_GX + 2000, _global_Pos_GY + 300)
                material.node_tree.links.new(_instance_switch_node.inputs[2], _default_instance_color.outputs[0])
                material.node_tree.links.new(_instance_switch_node.inputs[1], _label_node.outputs[0])
                ###########################################

                self._instance_switch_node_list.append(_instance_switch_node)

            # add diffuse shader
            _diffuse_label_shader = material.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
            _diffuse_label_shader.location = (_global_Pos_GX + 2200, _global_Pos_GY + 300)
            material.node_tree.links.new(_diffuse_label_shader.inputs[0], _instance_switch_node.outputs[0])

            # get current material output and add mix shader
            _material_output = material.node_tree.nodes["Material Output"]
            _material_output.location = (_global_Pos_GX + 2600, _global_Pos_GY + 300)
            _mix_shader_node = material.node_tree.nodes.new('ShaderNodeMixShader')
            _mix_shader_node.name = "rgb-label-mix"
            _mix_shader_node.inputs[0].default_value = 0
            _mix_shader_node.location = (_global_Pos_GX + 2400, _global_Pos_GY + 300)
            self._mix_shader_node_list.append(_mix_shader_node)
            _current_material_output = _material_output.inputs[0].links[0].from_node

            material.node_tree.links.new(_mix_shader_node.inputs[1], _current_material_output.outputs[0])
            material.node_tree.links.new(_mix_shader_node.inputs[2], _diffuse_label_shader.outputs[0])
            material.node_tree.links.new(_material_output.inputs[0], _mix_shader_node.outputs[0])

            # add mix shader
            ################################################################################################

            # Pass entries #############################################################################################
            # RGBDPass entries #########################################################################################
            for mix_shader_node in self._mix_shader_node_list:
                self.add_pass_entry(pass_name="RGBDPass",
                                    node_handle=mix_shader_node,
                                    value_type="inputs",
                                    value=[0, 0])
            for instance_switch_node in self._instance_switch_node_list:
                self.add_pass_entry(pass_name="RGBDPass",
                                    node_handle=instance_switch_node,
                                    value_type="inputs",
                                    value=[0, 0])
            ################################################################################## end of RGBDPass entries #

            # SemanticPass entries #####################################################################################
            for mix_shader_node in self._mix_shader_node_list:
                self.add_pass_entry(pass_name="SemanticPass",
                                    node_handle=mix_shader_node,
                                    value_type="inputs",
                                    value=[0, 1])
            for instance_switch_node in self._instance_switch_node_list:
                self.add_pass_entry(pass_name="SemanticPass",
                                    node_handle=instance_switch_node,
                                    value_type="inputs",
                                    value=[0, 0])
            ############################################################################## end of SemanticPass entries #

            # InstancePass entries #####################################################################################
            for mix_shader_node in self._mix_shader_node_list:
                self.add_pass_entry(pass_name="InstancePass",
                                    node_handle=mix_shader_node,
                                    value_type="inputs",
                                    value=[0, 1])
            for instance_switch_node in self._instance_switch_node_list:
                self.add_pass_entry(pass_name="InstancePass",
                                    node_handle=instance_switch_node,
                                    value_type="inputs",
                                    value=[0, 1])
            ############################################################################## end of SemanticPass entries #
            ###################################################################################### end of Pass entries #
            self._node_tree = self._node_tree


            # add sub surf modifier ########################################################################################
            if "NOSUBSURF" not in self._cfg:
                subsurf_modifier = self.mesh.modifiers.new("lastSubsurf", type='SUBSURF')
                subsurf_modifier.levels = 3 # TODO: Change to adaptive for automatic level
                # self.mesh.cycles.use_adaptive_subdivision = True  # TODO:maybe shift this to higher level
            ################################################################################# end of add sub surf modifier #



        # TODO: it is not always 1,1!!!!
        return 1, 1

    def setup_initial_point(self):
        """
        Setup the initial point for the trajectory based on configuration settings.

        Returns:
        =
        - initial_point (numpy.ndarray): Coordinates of the initial point.
        - final_point (numpy.ndarray): Coordinates of the final point.
        - distance (numpy.ndarray): Vector representing the distance between initial and final points.
        """
        image_resolution = self._cfg['SENSOR_SETUP']['SENSORS'][0]['sensorParams']['imageResolution']
        k_matrix = self._cfg['SENSOR_SETUP']['SENSORS'][0]['sensorParams']['KMatrix']
        asset_distance_scale = self._cfg['assetDistanceScale']

        sensor_width, sensor_height = image_resolution
        focal_length = k_matrix[0]  # fx

        vertices, faces = get_single_mesh_data(self.mesh)
        center_of_mass = compute_center_of_mass(vertices, faces, density=1)
        _, furthest_distance = find_furthest_point(vertices, center_of_mass)
        scale_factor = random.uniform(asset_distance_scale[0], asset_distance_scale[1])
        sensor_distance = furthest_distance * scale_factor

        horizontal_fov, vertical_fov = calculate_fov(sensor_width, sensor_height, focal_length)
        projected_width, projected_height = calculate_projected_dimensions(sensor_distance, horizontal_fov, vertical_fov)
        initial_point = calculate_initial_point(projected_width, projected_height, self.landing_mode)
        final_point = calculate_final_point(projected_width, projected_height, self.landing_mode)
    
        if self.landing_mode:
            # final_point = np.array([0,0,0])         # Asteroid ends at the origin
            print("Landing Mode activated")
        else:
            pass
            # final_point = calculate_final_point(projected_width, projected_height, self.landing_mode)
        
        
        distance = final_point - initial_point 
        
        print(f"Initial point: {initial_point}")
        print(f"Final point: {final_point}")
        print(f"Distance: {distance}")

        return initial_point, final_point, distance


    keyframe = 1
    def step(self, keyframe):
        """ 
        Stepping function for trajectory generation of object.
        
        Args:
        =
            None

        Returns:
        =
            None
        """
        if not self.module_active:
            return
        
        num_samples = self._cfg["numSamples"]

        if keyframe == 1:
            # self._initial_point, self.final_point, self.distance = setup_initial_point()
            self.mesh.location = self._initial_point
        else:                
            loc = self.mesh.location[0], self.mesh.location[1], self.mesh.location[2]
            rot = self.mesh.rotation_euler[0], self.mesh.rotation_euler[1], self.mesh.rotation_euler[2]

            # Calculate next rotation
            new_rot = step_rotation(self._rotational_period, self._observation_time, rot, self.mesh)
            self.mesh.rotation_euler = new_rot

            # Calculate next location
            new_loc = step_location(loc, self.final_point, self._initial_point, num_samples)
            self.mesh.location = new_loc

        keyframe += 1
        
        
    def set_trajectory_params(self):
        """
        Set trajectory parameters based on configuration.

        Returns:
        =
        - trajectory_mode (str): Selected trajectory mode.
        """
        if "trajectoryParams" in self._cfg:
            trajectory_params = self._cfg["trajectoryParams"]
            if "trajectoryType" in trajectory_params:
                trajectory_type = trajectory_params["trajectoryType"]
                mode = trajectory_type.get("mode")
                # print("Trajectory mode:", mode)  # Print mode for debugging
                
                if mode == "random":
                    chosen_mode = np.random.choice(["direct", "retrograde", "polar"])
                    ot.trajectory_mode = chosen_mode
                elif mode == "predefinedProbability":
                    probabilities = trajectory_type.get("probability", [])
                    ot.trajectory_mode = np.random.choice(["direct", "retrograde", "polar"], p=probabilities) if probabilities else "direct"
                elif mode in ["direct", "retrograde", "polar"]:
                    ot.trajectory_mode = mode
                else:
                    raise Exception("Invalid trajectory mode specified. Check spelling mistakes. \n \
                                    Available modes are 'direct', 'retrograde', 'polar', 'random', 'predefinedProbability'.")
        
        print("Trajectory mode:", ot.trajectory_mode)
        
        return ot.trajectory_mode


    def log_step(self, keyframe):
        self.current_mesh_q = self.mesh.rotation_euler.to_quaternion()
        pose = [str(self.mesh.location[0]), str(self.mesh.location[1]), str(self.mesh.location[2]),
                str(self.current_mesh_q[0]), str(self.current_mesh_q[1]),
                str(self.current_mesh_q[2]), str(self.current_mesh_q[3])]
        self._logger.log_pose(f"{self.mesh.name}", pose)

    
    def get_meshes(self):
        """ get mesh function
        Args:
            None
        Returns:
            return list of meshes
        """
        # TODO: implement function to return objects
        return {"name": self._cfg["name"], "mesh_handle": self.mesh}

    def additional_pass_action(self, pass_name, pass_cfg, keyframe):
        """ overwrite base function
        Args:
            pass_name:      name of pass to activate [string]
            pass_cfg:       specific parameters for the pass [dict]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        # set semantic ID ##############################################################################################
        if "SemanticPass" == pass_name:
            for label_ID_node in self._label_ID_Node_list:
                label_ID_node.outputs[0].default_value = pass_cfg["activationID"] + 1
                if keyframe > -1:
                    label_ID_node.outputs[0].keyframe_insert('default_value', frame=keyframe)
        ####################################################################################### end of set semantic ID #

        if keyframe > -1:
            self._set_keyframe_interpolation(node_tree=self._node_tree, interpolation='CONSTANT')