# blender imports
import bpy

# utility imports
import numpy as np
import csv
import random
import importlib
import os

from src.assets.TSSStage import TSSStage


class StageBlenderObject(TSSStage):
    """docstring for StageBlenderObject"""

    def __init__(self):
        super(StageBlenderObject, self).__init__()
        # class vars ###################################################################################################
        self._single_stage = None  # blender stage objcet [blObject]
        self._do_cleaning = True
        self._max_instances_labels = self._num_instance_label_per_channel * self._num_instance_label_per_channel \
                                     * self._num_instance_label_per_channel
        self._label_ID_Node_list = []
        self._instance_switch_node_list = []
        self._mix_shader_node_list = []
        self._node_tree = None
        ############################################################################################ end of class vars #

    def reset(self):
        """ reset all local vars
        Args:
            None
        Returns:
            None
        """

        self._single_stage = None
        self._label_ID_Node_list = []
        self._instance_switch_node_list = []
        self._mix_shader_node_list = []
        self._node_tree = None

    #def update_after_meshes(self):
    #    if self._do_cleaning:
    #        self._single_stage.modifiers.new("lastSubsurf", type='SUBSURF')

    def update_after_meshes(self):
        """ update function after mesh placements
        Args:
            None
        Returns:
            None
        """

        # add sub surf modifier ########################################################################################
        if "NOSUBSURF" not in self._cfg:
            self._single_stage.modifiers.new("lastSubsurf", type='SUBSURF')
            self._single_stage.cycles.use_adaptive_subdivision = True  # TODO:maybe shift this to higher level
        ################################################################################# end of add sub surf modifier #

    def _create_single_stage(self, file_path, object_file_name):

        # def local vars ###############################################################################################
        self._single_stage = None
        ######################################################################################## end of def local vars #

        # check if relative or absolute path is provided
        if not os.path.isabs(file_path):
            # create abs path
            _current_path = os.path.dirname(__file__)
            file_path = os.path.join(_current_path, "../../../", file_path)

        # load/append object to scene ##################################################################################
        bpy.ops.wm.append(directory=os.path.join(file_path, "Object"), link=False, filename=object_file_name)
        self._single_stage = bpy.data.objects[object_file_name]
        _new_obj_name = 'stage_' + object_file_name + str(1)
        self._single_stage.name = _new_obj_name
        ########################################################################### end of load/append object to scene #

        # clean object #################################################################################################
        if "noCleaning" in self._cfg:
            if self._cfg["noCleaning"]:
                self._do_cleaning = False

        if self._do_cleaning:
            _mat_list = bpy.data.materials

            # go through material slot and delete material
            for mat_slot in self._single_stage.material_slots:
                bpy.data.materials.remove(mat_slot.material)

            # go through particle systems, delete system and object with it
            for par_system in self._single_stage.particle_systems:
                # check if object is attached with it
                if hasattr(par_system.settings, 'instance_object'):
                    _par_obj = par_system.settings.instance_object
                    for mat_slot in _par_obj.material_slots:
                        bpy.data.materials.remove(mat_slot.material)
                    bpy.data.objects.remove(_par_obj, do_unlink=True)

            # TODO: improve!
            _particle_exist = True

            while _particle_exist:
                for mod in self._single_stage.modifiers:
                    if mod.type == "PARTICLE_SYSTEM":
                        self._single_stage.modifiers.remove(mod)
                        break
                _particle_exist = False
                for mod in self._single_stage.modifiers:
                    if mod.type == "PARTICLE_SYSTEM":
                        _particle_exist = True
                        break

            # remove lastSubsurf
            for mod in self._single_stage.modifiers:
                if mod.name == "lastSubsurf":
                    self._single_stage.modifiers.remove(mod)
        else:
            # clean all keyframes from materials
            # TODO: clean all keyframes from materials
            # clean all keyframes from objects
            # TODO: clean all keyframes from objects
            pass
        ########################################################################################## end of clean object #

        # setup stage cfg parameters

        if self._cfg['stageDisplacementActive']: # and self._do_cleaning:
            # setup general disp properties ############################################################################
            _disp_modifier = self._add_displacement(bl_object=self._single_stage)
            _disp_modifier.mid_level = self._cfg['stageDisplacementMidLevel']
            _disp_modifier.strength = self._cfg['stageDisplacementStrength']
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = self._single_stage
            bpy.ops.object.modifier_move_to_index(modifier=_disp_modifier.name, index=0)
            ##################################################################### end of setup general disp properties #
            # add new noise texture ####################################################################################
            bpy.ops.texture.new()
            text = bpy.data.textures[len(bpy.data.textures) - 1].name
            _texture_name = 'globalStageDisplacmentTexture_' + str(1)
            _texture = bpy.data.textures[text]
            _texture.name = _texture_name
            _texture.type = self._cfg['stageDisplacementNoiseType']
            ############################################################################# end of add new noise texture #
            # apply noise texture to stage
            _disp_modifier.texture = _texture

        # viewport options #############################################################################################
        self._single_stage.hide_viewport = False
        self._single_stage.hide_render = False
        ###################################################################################### end of viewport options #

        self._stage = self._single_stage

        '''
                passParamsDict = {"ParticleSystem": {
                    "rgb": {},
                    "semantic_label": {"labelIDVec": [[5000, 500, 5, 2]]},
                    "instance_label": {}
                }}
                '''
        passParamsDict = self._cfg["particleSystems"]

        self._prepare_particle_systems(stage=self._stage, passParamsDict=passParamsDict)

    def _create_semantic_pass(self, mesh, passParams, prepared_materials_list=[]):

        _label_ID_mat = passParams['semantic_label']['labelIDVec']
        _label_ID = 0

        for material_ID, material_slot in enumerate(mesh.material_slots):
            if material_slot.name in prepared_materials_list:
                continue

            prepared_materials_list.append(material_slot.name)
            material = material_slot.material
            _node_tree = material
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
            _label_node, _label_ID_Node = self.create_semantic_nodes( \
                node_tree=material,
                label_ID_vec=_label_ID_vec,
                num_label_per_channel=self._num_labels_per_channel,
                node_offset=[_global_Pos_GX, _global_Pos_GY + 1500])
            ##########################################################################################

            self._label_ID_Node_list.append(_label_ID_Node)

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
            self._instance_switch_node_list.append(_instance_switch_node)
            _label_node.inputs[0].default_value = 1
            ###########################################

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

            # Pass entries #################################################################################################
            # RGBDPass entries #############################################################################################
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
            ###################################################################################### end of RGBDPass entries #

            # SemanticPass entries #########################################################################################
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
            ################################################################################## end of SemanticPass entries #

            # SemanticPass entries #########################################################################################
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
            ################################################################################## end of SemanticPass entries #
            ########################################################################################## end of Pass entries #
            self._node_tree = _node_tree
        return prepared_materials_list

    def _prepare_particle_systems(self, stage, passParamsDict):
        _particle_systems = []
        _prepared_materials_list = []

        for p in stage.particle_systems:
            _particle_objects = []
            if "COLLECTION" == p.settings.render_type:
                for collection_obj in p.settings.instance_collection.all_objects:
                    _prepared_materials_list = self._create_semantic_pass(
                                                                    mesh=collection_obj,
                                                                    passParams=passParamsDict[p.name]["passParams"],
                                                                    prepared_materials_list=_prepared_materials_list)

            if "OBJECT" == p.settings.render_type:
                print(p.settings.instance_object)

    def create(self):
        self._create_single_stage(file_path=self._cfg["stageFilePath"], object_file_name=self._cfg["meshInstanceName"])

    def step(self, keyframe):
        pass

    def additional_pass_action(self, pass_name, pass_cfg, keyframe):
        """ overwrite base function
        Args:
            pass_name:      name of pass to activate [string]
            pass_cfg:       specific parameters for the pass [dict]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """
        print()
        # set semantic ID ##############################################################################################
        if "SemanticPass" == pass_name:
            for label_ID_node in self._label_ID_Node_list:
                label_ID_node.outputs[0].default_value = pass_cfg["activationID"]+1
                if keyframe > -1:
                    label_ID_node.outputs[0].keyframe_insert('default_value', frame=keyframe)
        ####################################################################################### end of set semantic ID #

        if keyframe > -1:
            self._set_keyframe_interpolation(node_tree=self._node_tree, interpolation='CONSTANT')

