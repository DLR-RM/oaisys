# blender imports
import bpy

# utility imports
import numpy as np
import os
import random
import copy as cp
import warnings

from src.assets.TSSMesh import TSSMesh
from src.tools.mesh_loader import load_mesh

from mathutils import Matrix, Vector, Quaternion


def get_loc_matrix(location):
    return Matrix.Translation(location)


def get_rot_matrix(rotation):
    return rotation.to_matrix().to_4x4()


def get_sca_matrix(scale):
    scale_mx = Matrix()
    for i in range(3):
        scale_mx[i][i] = scale[i]
    return scale_mx


class MeshSingle(TSSMesh):
    """docstring for MeshSingle"""

    def __init__(self):
        super(MeshSingle, self).__init__()
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
        self.current_mesh_q = None
        self.oaisys_mat_drivers = {}
        self._stepping_counter = 0
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
        self.current_mesh_q = None
        self.oaisys_mat_drivers = {}
        self._stepping_counter = 0
        ############################################################################################ end of class vars #

    def create_mesh(self, idx, path, name=None):
        _mesh_object_file_name = os.path.basename(os.path.normpath(os.path.splitext(path)[0]))

        if name is not None:
            if not name == "":
                _mesh_object_file_name = name

        # build up full mesh name
        _local_mesh_name = f"mesh_MeshSingle_{_mesh_object_file_name}_{idx}"

        _mesh_name = load_mesh(path, obj_name=_mesh_object_file_name)[0]
        _mesh = bpy.context.scene.objects[_mesh_name]
        _mesh.name = _local_mesh_name

        return _mesh

    def create(self, instance_id_offset=0, materials=None):
        """ create function
        Args:
            instance_id_offset:                                     instance offset ID [int]

        """
        return self.create_oaisys_mesh(instance_id_offset=instance_id_offset, materials=materials)

    @staticmethod
    def translate_oaisys_object(mesh, cfg):
        # rotate object before using it, if requested
        if "location" in cfg:
            loc = [float(cfg["location"][0]),
                   float(cfg["location"][1]),
                   float(cfg["location"][2])]
        else:
            loc = None

        if "rotation_deg" in cfg:
            rot = [(float(cfg["rotation_deg"][0]) * np.pi) / 180,
                   (float(cfg["rotation_deg"][1]) * np.pi) / 180,
                   (float(cfg["rotation_deg"][2]) * np.pi) / 180]
        elif "rotation_rad" in cfg:
            rot = [float(cfg["rotation_rad"][0]),
                   float(cfg["rotation_rad"][1]),
                   float(cfg["rotation_rad"][2])]
        else:
            rot = None

        if "scale" in cfg:
            scale = [float(cfg["scale"][0]),
                     float(cfg["scale"][1]),
                     float(cfg["scale"][2])]
        else:
            scale = None

        return MeshSingle.translate_object( mesh=mesh,
                                            loc=loc,
                                            rot=rot,
                                            scale=scale)

    @staticmethod
    def translate_object(mesh, loc=None, rot=None, scale=None):

        # rotate object before using it, if requested
        if loc is not None:
            mesh.location = loc

        if rot is not None:
            mesh.rotation_euler = rot

        if scale is not None:
            mesh.scale = scale

        bpy.context.view_layer.update()

        # save current rotation
        mesh.rotation_mode = 'QUATERNION'
        current_mesh_q = cp.deepcopy(mesh.rotation_quaternion)

        # apply scale and rotation
        bpy.context.view_layer.objects.active = mesh
        mx = mesh.matrix_world
        loc_m, rot_m, sca_m = mx.decompose()
        applymx = get_loc_matrix(loc_m) @ get_rot_matrix(Quaternion(rot_m)) @ get_sca_matrix(sca_m)
        mesh.matrix_world = applymx

        if scale is not None:
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        return current_mesh_q

    @staticmethod
    def rotate_object(mesh, rot_rad):

        vec = Vector((0.0, 0.0, 1.0))
        mesh.rotation_mode = 'QUATERNION'
        vec.rotate(mesh.rotation_quaternion)
        quat_rot = Quaternion(vec, rot_rad)

        mx = mesh.matrix_world
        loc_m, rot_m, sca_m = mx.decompose()
        rot_m = quat_rot @ rot_m
        applymx = get_loc_matrix(loc_m) @ get_rot_matrix(Quaternion(rot_m)) @ get_sca_matrix(sca_m)
        mesh.matrix_world = applymx
        mesh.rotation_mode = 'QUATERNION'


    def add_displacement_to_mesh(self, mesh, disp_cfg):
        # create empty object for noise pattern
        empty_obj = bpy.data.objects.new(mesh.name + "_noise_Empty", None)
        bpy.context.scene.collection.objects.link(empty_obj)
        empty_obj.location[0] = random.uniform(-1000., 1000.)
        empty_obj.location[1] = random.uniform(-1000., 1000.)
        empty_obj.location[2] = random.uniform(-1000., 1000.)
        bpy.context.view_layer.update()

        # setup general disp properties ############################################################################
        _disp_modifier = self._add_displacement(bl_object=mesh)
        _disp_modifier.mid_level = disp_cfg['assetDisplacementMidLevel']
        _disp_modifier.strength = disp_cfg['assetDisplacementStrength']
        _disp_modifier.texture_coords = 'OBJECT'
        _disp_modifier.texture_coords_object = empty_obj
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = mesh
        bpy.ops.object.modifier_move_to_index(modifier=_disp_modifier.name, index=0)
        ##################################################################### end of setup general disp properties #
        # add new noise texture ####################################################################################
        bpy.ops.texture.new()
        text = bpy.data.textures[len(bpy.data.textures) - 1].name
        _texture_name = 'globalStageDisplacmentTexture_' + str(1)
        _texture = bpy.data.textures[text]
        _texture.name = _texture_name
        _texture.type = disp_cfg['assetDisplacementNoiseType']
        for p_k, p_v in disp_cfg['assetDisplacementNoiseParams'].items():
            try:
                eval("_texture." + p_k + "=" + str(p_v))
            except:
                print(f"Cannot find the requested noise parameter {p_k}! Skipping parameter!")
                ############################################################################# end of add new noise texture #
        # apply noise texture to stage
        _disp_modifier.texture = _texture

        bpy.ops.object.modifier_apply(modifier=_disp_modifier.name)

    def get_random_driver_value(self, ideal=0, clip=[0,1], jitter_value=0):
        x = ideal + jitter_value*(random.random())-0.5

        x = clip[0] if x < clip[0] else x
        x = clip[1] if x > clip[1] else x

        return x

    def add_oaisys_material_drivers(self, mesh, drivers):
        for material_ID, material_slot in enumerate(mesh.material_slots):
            material = material_slot.material

            # go through material nodes and search for drivers
            for n_k in material.node_tree.nodes.keys():
                if n_k.startswith("OAISYS_"):
                    for driver_k, driver_v in drivers["drivers"].items():
                        if f"OAISYS_{driver_k}" == n_k:
                            self.oaisys_mat_drivers[driver_k] = material.node_tree.nodes[n_k]
                            x = self.get_random_driver_value(ideal=driver_v["ideal"],
                                                             clip=[driver_v["clip_min"], driver_v["clip_max"]],
                                                             jitter_value=driver_v["jitter_variance"]
                                                                         *drivers["jitter_strength"])
                            self.oaisys_mat_drivers[driver_k].outputs[0].default_value = x

    def step_oasys_material_drivers(self, keyframe):
        for d_k, d_v in self.oaisys_mat_drivers.items():
            driver_v = self._cfg["oaisys_drivers"]["material_drivers"]["drivers"][d_k]
            x = self.get_random_driver_value(ideal=driver_v["ideal"],
                                             clip=[driver_v["clip_min"], driver_v["clip_max"]],
                                             jitter_value=driver_v["jitter_variance"]
                                                          * self._cfg["oaisys_drivers"]["material_drivers"]["jitter_strength"])
            d_v.outputs[0].default_value = x
            d_v.outputs[0].keyframe_insert('default_value', frame=keyframe)

    def create_render_pass_nodes(self, mesh, mesh_settings_cfg, instance_id_offset):
        _label_ID_mat = mesh_settings_cfg['passParams']['semantic_label']['labelIDVec']
        _label_ID = 0
        # go through all materials
        for material_ID, material_slot in enumerate(mesh.material_slots):
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

                # _label_node.inputs[0].default_value = 1

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

            if len(_material_output.inputs[1].links) > 0:
                # material contains volume shader
                _current_volume_output = _material_output.inputs[1].links[0].from_node

                _mix_shader_volume_node = material.node_tree.nodes.new('ShaderNodeMixShader')
                _mix_shader_volume_node.name = "volume-label-mix"
                _mix_shader_volume_node.inputs[0].default_value = 0
                _mix_shader_volume_node.location = (_global_Pos_GX + 2400, _global_Pos_GY + 300)

                material.node_tree.links.new(_mix_shader_volume_node.inputs[1], _current_volume_output.outputs[0])
                material.node_tree.links.new(_material_output.inputs[1], _mix_shader_volume_node.outputs[0])

                self._mix_shader_node_list.append(_mix_shader_volume_node)

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

    def create_oaisys_mesh(self, instance_id_offset=0, materials=None):
        """ create function
        Args:
            instance_id_offset:                                     instance offset ID [int]
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

        self._mesh_file_path = self._cfg['meshFilePath']
        mesh_settings_cfg = self._cfg

        # load/get objects #############################################################################################
        # get mesh name from cfg file
        _mesh_object_file_name = os.path.basename(os.path.normpath(os.path.splitext(self._mesh_file_path)[0]))
        if 'meshInstanceName' in self._cfg:
            if not self._cfg['meshInstanceName'] == "":
                _mesh_object_file_name = self._cfg['meshInstanceName']

        # build up full mesh name
        _local_mesh_name = 'mesh_MeshSingle_' + self._cfg["name"]
        _mesh = None

        if not _mesh:
            # load file
            _mesh = self.create_mesh(0, self._mesh_file_path, _mesh_object_file_name)
            self.mesh = _mesh
            print(f"self.mesh: {self.mesh}")
            _mesh.name = _local_mesh_name
            self.current_mesh_q = MeshSingle.translate_oaisys_object(mesh=self.mesh, cfg=self._cfg)

        # displacement
        if "assetDisplacementParams" in self._cfg:
            _disp_cfg = self._cfg['assetDisplacementParams']
            if _disp_cfg['assetDisplacementActive']:
                self.add_displacement_to_mesh(mesh= self.mesh, disp_cfg=_disp_cfg)

        if "oaisys_drivers" in self._cfg:
            if "material_drivers" in self._cfg["oaisys_drivers"]:
                self.add_oaisys_material_drivers(mesh=self.mesh,
                                                 drivers=self._cfg["oaisys_drivers"]["material_drivers"])

        self.create_render_pass_nodes(mesh = self.mesh,
                                      mesh_settings_cfg = mesh_settings_cfg,
                                      instance_id_offset = instance_id_offset)

        # TODO: it is not always 1,1!!!!
        return 1, 1

    def step(self, keyframe):
        """ stepping function
        Args:
            None
        Returns:
            None
        """
        if not self.module_active:
            return

        # move object if requested
        if "rotation_deg_step_v" in self._cfg:
            self.rotate_object(self.mesh, self._cfg["rotation_deg_step_v"])

            # set keyframe if requested
            if keyframe > -1:

                if (self._stepping_counter % self._trigger_interval) == 0:
                    self.step_oasys_material_drivers(keyframe=keyframe)

                self.mesh.keyframe_insert('rotation_quaternion', frame=keyframe)

                # set interpolation to constant
                fc = self.mesh.animation_data.action.fcurves
                for sfc in fc:
                    for kf in sfc.keyframe_points:
                        kf.interpolation = 'CONSTANT'


    def log_step(self, keyframe):
        if self.module_active:
            loc_m, rot_m, _ = self.mesh.matrix_world.decompose()
            pose = [str(loc_m[0]), str(loc_m[1]), str(loc_m[2]),
                    str(rot_m[0]), str(rot_m[1]), str(rot_m[2]), str(rot_m[3])]
            self._logger.log_pose(f"{self.mesh.name}", pose)

    def get_meshes(self):
        """ get mesh function
        Args:
            None
        Returns:
            return dict of objects
        """
        return {"main": self.mesh}

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
