# blender imports
import bpy

# utility imports
import numpy as np
import csv
import random
import importlib
import os

from src.assets.TSSMesh import TSSMesh

class MeshMultipleRandom(TSSMesh):
    """docstring for MeshMultipleRandom"""
    def __init__(self):
        super(MeshMultipleRandom, self).__init__()
        # class vars ###################################################################################################
        self._single_stage = None                               # blender stage objcet [blObject]
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
        self._num_instance_label_per_channel = 51
        self._max_instances_labels = self._num_instance_label_per_channel*self._num_instance_label_per_channel\
                                                                    *self._num_instance_label_per_channel
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
        ############################################################################################ end of class vars #


    def reset(self):
        """ reset all local vars
        Args:
            None
        Returns:
            None
        """

        # class vars ###################################################################################################
        self._single_stage = None                               # blender stage objcet [blObject]
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
        self._num_instance_label_per_channel = 51
        self._max_instances_labels = self._num_instance_label_per_channel*self._num_instance_label_per_channel\
                                                                    *self._num_instance_label_per_channel
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
        ############################################################################################ end of class vars #


    def create(self,instance_id_offset=0):
        """ create function
        Args:
            instance_id_offset:                                     instance offset ID [int]
        Returns:
            _current_real_particle_count:                              particle count [int]
            _current_real_particle_label_count
        """

        # get emitter object
        _local_emitter = self._stage_dict[self._cfg["appliedOnStage"]]

        # update _num_instance_label_per_channel if provided
        if "numInstanceLabelPerChannel" in self._cfg:
            self._num_instance_label_per_channel = self._cfg["numInstanceLabelPerChannel"]
            self._max_instances_labels = self._num_instance_label_per_channel*self._num_instance_label_per_channel\
                                                                    *self._num_instance_label_per_channel

        # create particles and get number of particles
        _current_real_particle_count, _current_real_particle_label_count = self._create_particle_meshes(\
                                                                                    mesh_settings_cfg=self._cfg,
                                                                                    instance_ID_offset=instance_id_offset,
                                                                                    emitter=_local_emitter)

        # return number of created particles
        return _current_real_particle_count, _current_real_particle_label_count


    def step(self):
        """ settping function
        Args:
            None
        Returns:
            None
        """
        pass


    def get_meshes(self):
        """ get mesh function
        Args:
            None
        Returns:
            return list of meshes
        """
        # TODO: implement function to return objects
        return None


    def _create_particle_meshes(self,mesh_settings_cfg,local_color_vec=[],instance_ID_offset=0,emitter=None):
        """ function to create particle system
        Args:
            mesh_settings_cfg:
            local_color_vec:
            instance_ID_offset:
            emitter:
        Returns:
            _current_real_particle_count:                              particle count [int]
        """

        # store emitter ################################################################################################
        if emitter is not None:
            self._emitter = emitter
        ######################################################################################### end of store emitter #

        # save cfg parameters to variables #############################################################################
        # get path to file mesh
        self._mesh_file_path = mesh_settings_cfg['meshFilePath']

        # check if relative or absolute path is provided
        if not os.path.isabs(self._mesh_file_path):
            # create abs path
            _current_path = os.path.dirname(__file__)
            self._mesh_file_path = os.path.join(_current_path,"../../../",self._mesh_file_path)

        # get the number of desired instances
        if len(mesh_settings_cfg['numberInstances']) == 1:
            self._min_number_instances = int(mesh_settings_cfg['numberInstances'][0])
            self._max_number_instances = int(mesh_settings_cfg['numberInstances'][0])
        else:
            self._min_number_instances = int(mesh_settings_cfg['numberInstances'][0])
            self._max_number_instances = int(mesh_settings_cfg['numberInstances'][1])

        # switch var
        self._random_switch_on_off = mesh_settings_cfg['randomSwitchOnOff']
        
        # deformation and transformation parameters
        self._default_size = float(mesh_settings_cfg['defaultSize'])
        self._strength_random_scale = mesh_settings_cfg['strengthRandomScale']
        self._random_rotation_enabled = mesh_settings_cfg['randomRotationEnabled']
        if self._random_rotation_enabled:
            self._rotation_option_mode = mesh_settings_cfg['rotationOptionMode']
            self._rotation_option_factor = mesh_settings_cfg['rotationOptionFactor']
            self._rotation_option_phase = mesh_settings_cfg['rotationOptionPhase']
            self._rotation_option_phase_random = mesh_settings_cfg['rotationOptionPhaseRandom']

        # emitter type parameter
        if mesh_settings_cfg['meshEmitter'] == "CUSTOM":
            self._emitter_file_path = mesh_settings_cfg['emitterFilePath']
        ###################################################################### end of save cfg parameters to variables #

        # load/get objects #############################################################################################
        # get mesh name from cfg file
        _mesh_object_file_name = os.path.basename(os.path.normpath(os.path.splitext(self._mesh_file_path)[0]))
        if 'meshInstanceName' in mesh_settings_cfg:
            if not mesh_settings_cfg['meshInstanceName'] == "":
                _mesh_object_file_name = mesh_settings_cfg['meshInstanceName']

        # build up full mesh name
        _local_mesh_name = 'mesh_MeshMutipleRandom_' + mesh_settings_cfg["name"]


        # load particle object #########################################################################################
        # def mesh
        _mesh = None

        # check if mesh asset already exist; if not load it
        if not _mesh:
            bpy.ops.wm.append(  directory=os.path.join(self._mesh_file_path,"Object"),
                                link=False,
                                filename=_mesh_object_file_name)
            _mesh = bpy.context.scene.objects[_mesh_object_file_name]
            _mesh.name = _local_mesh_name

            # rotate object before using it, if requested
            if "preRotationDeg" in mesh_settings_cfg:
                _mesh.rotation_euler[0] = (mesh_settings_cfg["preRotationDeg"][0]*np.pi)/180
                _mesh.rotation_euler[1] = (mesh_settings_cfg["preRotationDeg"][1]*np.pi)/180
                _mesh.rotation_euler[2] = (mesh_settings_cfg["preRotationDeg"][2]*np.pi)/180

            # apply scale and roation
            bpy.context.view_layer.objects.active = _mesh
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
       ################################################################################### end of load particle object #

        if mesh_settings_cfg['meshEmitter'] == "CUSTOM":
            # load emitter object ######################################################################################
            emitterObjectFileName = os.path.basename(os.path.normpath(os.path.splitext(self._emitter_file_path)[0]))
            bpy.ops.wm.append(  directory=os.path.join(self._emitter_file_path,"Object"), 
                                link=False,
                                filename=emitterObjectFileName)
            self._emitter = bpy.context.scene.objects[emitterObjectFileName]
            self._emitter.name = 'mesh_MeshMutipleRandom_' + mesh_settings_cfg["name"] + '_emitter'
            ############################################################################### end of load emitter object #
        ###################################################################################### end of load/get objects #


        # adapt material of node to be useable for labeling ############################################################
        _label_ID_mat = mesh_settings_cfg['passParams']['semantic_label']['labelIDVec']
        _label_ID = 0
        # go trough all materials
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

            _label_ID_vec = _label_ID_mat[_label_ID-1]


            # create label node ######################################################################
            # calculate the corresponding label values and stack up to list
            # TODO: add condition if rendering label is even set?!
            self._instance_label_active = mesh_settings_cfg['instanceLabelActive']


            _label_node,_label_ID_Node = self.create_semantic_nodes(\
                                                                node_tree=material,
                                                                label_ID_vec=_label_ID_vec,
                                                                num_label_per_channel=self._num_instance_label_per_channel,
                                                                node_offset=[_global_Pos_GX,_global_Pos_GY+1500])
            ##########################################################################################
            
            self._label_ID_Node_list.append(_label_ID_Node)

            if self._instance_label_active:

                # add particle info node
                _particle_info_node = material.node_tree.nodes.new('ShaderNodeParticleInfo')
                _particle_info_node.location = (_global_Pos_GX-500,_global_Pos_GY+300)

                _instance_switch_node,_instance_add_node = \
                                self._create_id_to_rgb_node_tree(node_tree=material,
                                                                num_label_per_channel=self._num_instance_label_per_channel,
                                                                instance_ID_offset=instance_ID_offset,
                                                                node_offset=[_global_Pos_GX,_global_Pos_GY])


                self._instance_switch_node_list.append(_instance_switch_node)

                _label_node.inputs[0].default_value = 1

                material.node_tree.links.new(_instance_add_node.inputs[0], _particle_info_node.outputs[0])
                material.node_tree.links.new(_instance_switch_node.inputs[1], _label_node.outputs[0])
            else:

                # create default color node
                _default_instance_color = material.node_tree.nodes.new("ShaderNodeRGB")
                _default_instance_color.location = (_global_Pos_GX,_global_Pos_GY)
                _default_instance_color.outputs[0].default_value = (0,0,0,1)

                # combine label and instance channel ###########################################
                _instance_switch_node = material.node_tree.nodes.new('ShaderNodeMixRGB')
                _instance_switch_node.name = "instanceLabelsEnabled"
                _instance_switch_node.label = "instanceLabelsEnabled"
                _instance_switch_node.inputs[0].default_value = 0
                _instance_switch_node.location = (_global_Pos_GX+2000,_global_Pos_GY+300)
                material.node_tree.links.new(_instance_switch_node.inputs[2], _default_instance_color.outputs[0])
                material.node_tree.links.new(_instance_switch_node.inputs[1], _label_node.outputs[0])
                ###########################################

                self._instance_switch_node_list.append(_instance_switch_node)

            
            # add diffuse shader
            _diffuse_label_shader = material.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
            _diffuse_label_shader.location = (_global_Pos_GX+2200,_global_Pos_GY+300)
            material.node_tree.links.new(_diffuse_label_shader.inputs[0], _instance_switch_node.outputs[0])

            # get current material output and add mix shader
            _material_output = material.node_tree.nodes["Material Output"]
            _material_output.location = (_global_Pos_GX+2600,_global_Pos_GY+300)
            _mix_shader_node = material.node_tree.nodes.new('ShaderNodeMixShader')
            _mix_shader_node.name = "rgb-label-mix"
            _mix_shader_node.inputs[0].default_value = 0
            _mix_shader_node.location = (_global_Pos_GX+2400,_global_Pos_GY+300)
            self._mix_shader_node_list.append(_mix_shader_node)
            _current_material_output = _material_output.inputs[0].links[0].from_node
            
            material.node_tree.links.new(_mix_shader_node.inputs[1], _current_material_output.outputs[0])
            material.node_tree.links.new(_mix_shader_node.inputs[2], _diffuse_label_shader.outputs[0])
            material.node_tree.links.new(_material_output.inputs[0], _mix_shader_node.outputs[0])

            # add mix shader
        ################################################################################################

        # set particle options #########################################################################################
        # setup emitter object as particle emitter
        _modifier = self._emitter.modifiers.new(self._emitter.name, type='PARTICLE_SYSTEM')
        self._particle_system = _modifier.particle_system

        # adapt general options
        self._particle_system.settings.type = 'HAIR'
        self._particle_system.settings.use_advanced_hair = True

        # add density texture
        if mesh_settings_cfg['useDensityMap']:
            # update parameters
            if len(mesh_settings_cfg['densityMapSettings']['numberInstances']) == 1:
                self._min_number_instances = int(mesh_settings_cfg['densityMapSettings']['numberInstances'][0])
                self._max_number_instances = int(mesh_settings_cfg['densityMapSettings']['numberInstances'][0])
            else:
                self._min_number_instances = int(mesh_settings_cfg['densityMapSettings']['numberInstances'][0])
                self._max_number_instances = int(mesh_settings_cfg['densityMapSettings']['numberInstances'][1])

            _density_tex = bpy.data.textures.new(mesh_settings_cfg['name']+ "_DensityMap", \
                                                    mesh_settings_cfg['densityMapSettings']['densityMap']['noiseType'])
            
            if "VORONOI" == mesh_settings_cfg['densityMapSettings']['densityMap']['noiseType']:

                _density_tex.noise_intensity = float(mesh_settings_cfg['densityMapSettings']['densityMap']['intensity'])
                _density_tex.noise_scale = float(mesh_settings_cfg['densityMapSettings']['densityMap']['size'])

                _density_tex.use_color_ramp = True
                _density_tex.color_ramp.elements[0].position = mesh_settings_cfg['densityMapSettings']['densityMap']\
                                                                                                ['colorStopPosition_0']
                _density_tex.color_ramp.elements[1].position = mesh_settings_cfg['densityMapSettings']['densityMap']\
                                                                                                ['colorStopPosition_1']

                _density_tex.color_ramp.elements[0].color = (mesh_settings_cfg['densityMapSettings']['densityMap']\
                                                                                                ['colorStopColor_0'][0],
                                                            mesh_settings_cfg['densityMapSettings']['densityMap']\
                                                                                                ['colorStopColor_0'][1],
                                                            mesh_settings_cfg['densityMapSettings']['densityMap']\
                                                                                                ['colorStopColor_0'][2],
                                                            mesh_settings_cfg['densityMapSettings']['densityMap']\
                                                                                                ['colorStopColor_0'][3])

                _density_tex.color_ramp.elements[1].color = (mesh_settings_cfg['densityMapSettings']['densityMap']\
                                                                                                ['colorStopColor_1'][0],
                                                            mesh_settings_cfg['densityMapSettings']['densityMap']\
                                                                                                ['colorStopColor_1'][1],
                                                            mesh_settings_cfg['densityMapSettings']['densityMap']\
                                                                                                ['colorStopColor_1'][2],
                                                            mesh_settings_cfg['densityMapSettings']['densityMap']\
                                                                                                ['colorStopColor_1'][3])

            if "BLEND" == mesh_settings_cfg['densityMapSettings']['densityMap']['noiseType']:
                _density_tex.progression = mesh_settings_cfg['densityMapSettings']['densityMap']['progression']

            _particle_density_map = _modifier.particle_system.settings.texture_slots.add()
            _particle_density_map.texture = _density_tex
            _particle_density_map.texture_coords = 'UV'
            _particle_density_map.use_map_time = False
            _particle_density_map.use_map_density = True
            _particle_density_map.use_map_size = True
            _particle_density_map.density_factor = 1.0

            _particle_density_map.blend_type = 'MULTIPLY'

            # TODO: the mapping values should change for each step
            _particle_density_map.offset[0] = random.randint(-5.0,5.0)
            _particle_density_map.offset[1] = random.randint(-5.0,5.0)

            if "scale" in mesh_settings_cfg['densityMapSettings']['densityMap']:
                _particle_density_map.scale[0] = float(mesh_settings_cfg['densityMapSettings']['densityMap']["scale"])
                _particle_density_map.scale[1] = float(mesh_settings_cfg['densityMapSettings']['densityMap']["scale"])
                _particle_density_map.scale[2] = float(mesh_settings_cfg['densityMapSettings']['densityMap']["scale"])


        # setup options 'Emission'
        if self._random_switch_on_off:
            if bool(random.getrandbits(1)):
                self._particle_system.settings.count = random.randint(self._min_number_instances,self._max_number_instances)
            else:
                self._particle_system.settings.count = 0
        else:
            self._particle_system.settings.count = random.randint(self._min_number_instances,self._max_number_instances)
        self._currentSeed = random.randrange(1000000)
        self._particle_system.seed = self._currentSeed
        self._particle_system.settings.hair_length = 1
        self._particle_system.settings.hair_step = 1

        # setup options 'render'
        self._particle_system.settings.render_type = 'OBJECT'
        self._particle_system.settings.particle_size = self._default_size
        self._particle_system.settings.size_random = self._strength_random_scale

        # setup options 'rotation'
        if self._random_rotation_enabled:
            self._particle_system.settings.use_rotations = True
            self._particle_system.settings.rotation_mode = mesh_settings_cfg['rotationOptionMode']
            self._particle_system.settings.rotation_factor_random = mesh_settings_cfg['rotationOptionFactor']
            self._particle_system.settings.phase_factor = mesh_settings_cfg['rotationOptionPhase']
            self._particle_system.settings.phase_factor_random = mesh_settings_cfg['rotationOptionPhaseRandom']

        # setup options 'Viewport Display'
        if mesh_settings_cfg['meshEmitter'] == "CUSTOM":
            self._emitter.show_instancer_for_viewport = False
            self._emitter.show_instancer_for_render = False
        _mesh.hide_render = True
        _mesh.hide_set(True)
        ################################################################################################################

        # assign object as emitter object ##############################################################################
        self._particle_system.settings.instance_object = _mesh
        ################################################################################################################


        _depth_graph = bpy.context.evaluated_depsgraph_get()

        _current_real_particle_count = len(self._emitter.evaluated_get(_depth_graph).particle_systems[-1].particles)

        if _current_real_particle_count+instance_ID_offset >= self._max_instances_labels:
            self._print_msg('Exceeded max instance number for instance labels. Set instance count accordingly!')
            self._print_msg("self._max_instances_labels: " + str(self._max_instances_labels))
            self._print_msg("instance_ID_offset: " + str(instance_ID_offset))
            self._print_msg('old count value: ' + str(_current_real_particle_count))
            _newCount = self._max_instances_labels - instance_ID_offset
            self._particle_system.settings.count = _newCount
            _depth_graph = bpy.context.evaluated_depsgraph_get()
            _actualParticleCount = len(self._emitter.evaluated_get(_depth_graph).particle_systems[-1].particles)
            _current_real_particle_count = _actualParticleCount
            self._print_msg("new count value: " + str(_current_real_particle_count))

        _current_real_particle_label_count = 0
        if self._instance_label_active:
            _current_real_particle_label_count = _current_real_particle_count


        # Pass entries #################################################################################################
        # RGBDPass entries #############################################################################################
        for mix_shader_node in self._mix_shader_node_list:
            self.add_pass_entry(pass_name="RGBDPass",
                                node_handle=mix_shader_node,
                                value_type="inputs",
                                value=[0,0])
        for instance_switch_node in self._instance_switch_node_list:
            self.add_pass_entry(pass_name="RGBDPass",
                                node_handle=instance_switch_node,
                                value_type="inputs",
                                value=[0,0])
        ###################################################################################### end of RGBDPass entries #
        
        # SemanticPass entries #########################################################################################
        for mix_shader_node in self._mix_shader_node_list:
            self.add_pass_entry(pass_name="SemanticPass",
                                node_handle=mix_shader_node,
                                value_type="inputs",
                                value=[0,1])
        for instance_switch_node in self._instance_switch_node_list:
            self.add_pass_entry(pass_name="SemanticPass",
                                node_handle=instance_switch_node,
                                value_type="inputs",
                                value=[0,0])
        ################################################################################## end of SemanticPass entries #

        # SemanticPass entries #########################################################################################
        for mix_shader_node in self._mix_shader_node_list:
            self.add_pass_entry(pass_name="InstancePass",
                                node_handle=mix_shader_node,
                                value_type="inputs",
                                value=[0,1])
        for instance_switch_node in self._instance_switch_node_list:
            self.add_pass_entry(pass_name="InstancePass",
                                node_handle=instance_switch_node,
                                value_type="inputs",
                                value=[0,1])
        ################################################################################## end of SemanticPass entries #
        ########################################################################################## end of Pass entries #
        self._node_tree = self._node_tree

        return _current_real_particle_count, _current_real_particle_label_count



    def additional_pass_action(self,pass_name, pass_cfg, keyframe):
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
                label_ID_node.outputs[0].default_value = pass_cfg["activationID"]+1
                if keyframe > -1:
                    label_ID_node.outputs[0].keyframe_insert('default_value', frame=keyframe)
        ####################################################################################### end of set semantic ID #

        if keyframe > -1:
            self._set_keyframe_interpolation(node_tree=self._node_tree,interpolation='CONSTANT')
