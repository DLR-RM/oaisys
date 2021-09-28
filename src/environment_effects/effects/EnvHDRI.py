# blender imports
import bpy

# utility imports
import random
import math

from src.TSSBase import TSSBase
from src.environment_effects.TSSEnvironmentEffects import TSSEnvironmentEffects

class EnvHDRI(TSSEnvironmentEffects):
    """docstring for EnvHDRI"""
    def __init__(self):
        super(EnvHDRI, self).__init__()
        # class vars ###################################################################################################
        self._hdri_dict_list = []
        self._hdri_in_use_dict = {}
        self._last_keyframe = -1
        self._activation_list = []                          # list of HDRI IDs, which are activated in current batch
                                                            # for eacht stepping call [list]
        self._current_hdri_index = -1
        self._tmp_hdri_id_list = []
        self._num_hdris_in_use = 0
        self._last_image_element = None
        self._last_label_element = None
        self._image_ID_node = None
        self._label_ID_node = None
        self._current_hdri_id = -1
        self._semantic_switching_node = None
        self._semantic_pass_id = None
        self._instance_switching_node = None
        ############################################################################################ end of class vars #


    def reset(self):
        """ reset function
        Args:
            None
        Returns:
            None
        """

        # reset all vars ###############################################################################################
        self._hdri_node = None
        self._hdri_dict_list = []
        self._hdri_in_use_dict = {}
        self._last_keyframe = -1
        self._activation_list = []
        self._tmp_hdri_id_list = []
        self._num_hdris_in_use = 0
        self._last_image_element = None
        self._last_label_element = None
        self._image_ID_node = None
        self._label_ID_node = None
        self._current_hdri_id = -1
        self._semantic_switching_node = None
        self._semantic_pass_id = None
        self._instance_switching_node = None
        ######################################################################################## end of reset all vars #


    def _get_next_hdri_id(self,current_hdri_index,selection_option=-1):
        """ function to get id of next hdri
            selection_options:  -1      if set to -1, self._selection_option is taken
                                0       linear selection:   Get next hdri, which is in list. When last element is
                                                            reached, the selection starts from the beginnig again.
                                                            Therefore, this options representes a ring buffer.
                                1       random selection with replacement:  Random selection of hdri from list with
                                                                            replacement.
                                2       random selection without replacement:   Random selection of hdri from list
                                                                                without replacement.
        Args:
            current_hdri_index:             current hdri index [unsigned int]
            selection_option:               selection mode; see options in function description [int]
        Returns:
            current hdri id [unsigned int]
        """

        # get selection option #########################################################################################
        if -1 == selection_option:
            selection_option = self._selection_option
        ################################################################################## end of get selection option #

        # selection option 0 (linear selection) ########################################################################
        if 0 == selection_option:
            # increase counter
            current_hdri_index += 1

            # reset counter if needed
            if current_hdri_index >= len(self._hdri_dict_list):
                current_hdri_index = 0
        ################################################################# end of selection option 1 (linear selection) #

        # selection option 1 (random selection 1) ######################################################################
        if 1 == selection_option:
            current_hdri_index = randint(0, len(self._hdri_dict_list))
        ############################################################### end of selection option 1 (random selection 1) #

        # selection option 2 (random selection 2) ######################################################################
        if 2 == selection_option:
            if not self._tmp_hdri_id_list:
                self._tmp_hdri_id_list = list(range(0,len(self._hdri_dict_list)))
            
            _item = random.choice(self._tmp_hdri_id_list)
            current_hdri_index = _item
            self._tmp_hdri_id_list.remove(_item)
        ############################################################### end of selection option 2 (random selection 2) #

        # return new current hdri index
        return current_hdri_index


    def _create_base_hdri(self,last_element,node_offset=[0,0]):
        """ function to create base hdri
        Args:
            last_element                current last node of compositor [blObject]
            node_offset:                node offset for y and y [list] [int]
        Returns:
            _current_last_output new last element [blObject]
        """

        # store hdri list
        self._hdri_dict_list = self._cfg["HDRIList"]

        # attach last output to Background Shader node #################################################################
        self._semantic_switching_node = self._world_node_tree.node_tree.nodes.new('ShaderNodeMixRGB')
        self._semantic_switching_node.location = (node_offset[0]-400,node_offset[1]-400)
        self._semantic_switching_node.inputs[0].default_value = 0.0
        _current_last_output = self._semantic_switching_node.outputs[0]

        # mix rgb to mix last_element with sky #########################################################################
        if last_element is not None:
            _mix_node = self._world_node_tree.node_tree.nodes.new('ShaderNodeMixRGB')
            _mix_node.location = (node_offset[0],node_offset[1])

            self._world_node_tree.inputs[0].default_value = 1.0
            self._world_node_tree.blend_type = 'OVERLAY'
            self._world_node_tree.node_tree.links.new(_mix_node.inputs[1],last_element)

            self._world_node_tree.node_tree.links.new(_mix_node.inputs[2],self._semantic_switching_node.outputs[0])
            _current_last_output = _mix_node.outputs[0]
        ################################################################## end of mix rgb to mix last_element with sky #
        ########################################################## end of attach last output to Background Shader node #
        

        # return new last element
        return _current_last_output


    def _activate_hdri(self, hdri_id, keyframe):
        """ function to activate hdri with specific id
        Args:
            hdri_id:        id of hdri to be activated [int]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        # create hdri ##################################################################################################
        # check if id with node is not already used
        if not hdri_id in self._hdri_in_use_dict:
            # add image tree
            self._last_image_element, self._image_ID_node = self._add_image_switching_node(\
                                                                node_tree=self._world_node_tree,
                                                                image_path=self._hdri_dict_list[hdri_id]["filePath"],
                                                                last_element=self._last_image_element,
                                                                image_ID_node=self._image_ID_node,
                                                                node_index=self._num_hdris_in_use,
                                                                uv_map=None, 
                                                                node_offset=[self._node_offset[0]-2500,\
                                                                            self._node_offset[0]-1500])

            # add semantic tree
            self._last_label_element, self._label_ID_node = self._add_label_switching_node(\
                                                                node_tree=self._world_node_tree,
                                                                label_vec=self._hdri_dict_list[hdri_id]["labelIDVec"],
                                                                last_element=self._last_label_element,
                                                                label_ID_node=self._label_ID_node,
                                                                node_index=self._num_hdris_in_use,
                                                                uv_map=None, 
                                                                node_offset=[self._node_offset[0]-5000,\
                                                                            self._node_offset[0]-1500])
            
            # store hdri id value
            self._hdri_in_use_dict[hdri_id] = self._num_hdris_in_use

            # increase number of hdri ins use
            self._num_hdris_in_use += 1
        ########################################################################################### end of create hdri #

        # link nodes to global tree ####################################################################################
        self._world_node_tree.node_tree.links.new(  self._semantic_switching_node.inputs[1],
                                                    self._last_image_element.outputs[0])
        self._world_node_tree.node_tree.links.new(  self._semantic_switching_node.inputs[2],
                                                    self._last_label_element.outputs[0])
        ############################################################################# end of link nodes to global tree #

        # activate hdri ################################################################################################
        # store hdri id
        self._image_id = self._hdri_in_use_dict[hdri_id]
        self._label_id = self._hdri_in_use_dict[hdri_id]

        # set hdri id
        self._image_ID_node.outputs[0].default_value = self._image_id
        self._label_ID_node.outputs[0].default_value = self._label_id
        ######################################################################################### end of activate hdri #

        # set keyframes if requested ###################################################################################
        if keyframe > -1:
            
            # set keyframes for ids
            self._image_ID_node.outputs[0].keyframe_insert('default_value', frame=keyframe)
            self._label_ID_node.outputs[0].keyframe_insert('default_value', frame=keyframe)

            # set interpolation to constant ############################################################################
            _fcurves = self._world_node_tree.node_tree.animation_data.action.fcurves
            for fcurve in _fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'CONSTANT'
            ##################################################################### end of set interpolation to constant #
        ############################################################################ end of set keyframes if requested #


    def _add_image_switching_node(  self,
                                    node_tree,
                                    image_path,
                                    last_element,
                                    image_ID_node=None,
                                    node_index=0,
                                    uv_map=None, 
                                    node_offset=[0,0]):
        """ add switching nodes pipeline for images
        Args:
            node_tree:                              node tree handle [blObject]
            image_path:                             image file path; contains file path [str]
            last_element:                           previous last element [blObject]
            image_ID_node:                          node for storing current image ID [blObject]
            node_index:                             current index [int]
            uv_map:                                 uv map for textures if needed [blObject]
            node_offset:                            node offset for y and y [list] [int]
        Returns:
            handle to last node [blObject], handle to assign switch [blObject]
        """

        # define local variables #######################################################################################
        _step_node_width = 200                  # x seperation of nodes
        _step_node_height = 200                 # y seperation of nodes
        ################################################################################ end of define local variables #

        # create image ID handle #######################################################################################
        if image_ID_node is None:
            image_ID_node = node_tree.node_tree.nodes.new("ShaderNodeValue")
            image_ID_node.location = ((node_offset[0]-400,node_offset[1]-100))
            image_ID_node.name = "image_step_ID"
            image_ID_node.label = "image_step_ID"
            image_ID_node.outputs[0].default_value = 1
        ############################################################################### end of create image ID handle #

        # create image nodes ###########################################################################################
        _x_offset = (node_index+1)*_step_node_width + node_offset[0]
        _y_offset = (node_index+1)*_step_node_height + node_offset[1]
        _current_image_node = node_tree.node_tree.nodes.new('ShaderNodeTexEnvironment')
        _img = bpy.data.images.load(image_path)
        _current_image_node.image = _img
        _current_image_node.location = (((node_index+1)*_step_node_width*2 + node_offset[0] - 800,
                                        (node_index+1)*_step_node_height + node_offset[1]))

        # attach uv map if possible
        if uv_map is not None:
            node_tree.node_tree.links.new(_current_image_node.inputs[0], uv_map)

        # create new mix node ######################################################################################
        _current_mix_shader_node = node_tree.node_tree.nodes.new("ShaderNodeMixRGB")
        _current_mix_shader_node.location = (((node_index+1)*_step_node_width*2 + node_offset[0],
                                            (node_index+1)*_step_node_height + node_offset[1]))
        ############################################################################### end of create new mix node #

        # create compare node ######################################################################################
        _current_compare_node = node_tree.node_tree.nodes.new("ShaderNodeMath")
        _current_compare_node.location = (((node_index+1)*_step_node_width*2 + node_offset[0],
                                            node_offset[1]-_step_node_height))
        _current_compare_node.operation = 'COMPARE'
        _current_compare_node.inputs[0].default_value = node_index
        _current_compare_node.inputs[2].default_value = 0      # delta value should be zero for equal comparison
        ############################################################################### end of create compare node #


        # link nodes togther #######################################################################################
        node_tree.node_tree.links.new(_current_mix_shader_node.inputs[0], _current_compare_node.outputs[0])
        if last_element is not None:
            node_tree.node_tree.links.new(_current_mix_shader_node.inputs[1], last_element.outputs[0])
        node_tree.node_tree.links.new(_current_mix_shader_node.inputs[2], _current_image_node.outputs[0])
            
        node_tree.node_tree.links.new(_current_compare_node.inputs[1], image_ID_node.outputs[0])
        ################################################################################ end of link nodes togther #
        #################################################################################### end of create image nodes #

        # return last mix shader node
        return _current_mix_shader_node, image_ID_node


    def _add_label_switching_node(  self,
                                    node_tree,
                                    label_vec,
                                    last_element,
                                    label_ID_node=None,
                                    node_index=0,
                                    uv_map=None, 
                                    node_offset=[0,0]):
        """ add switching nodes pipeline for labels
        Args:
            node_tree:                              node tree handle [blObject]
            label_vec:                              list, which represents the label vector [list]
            last_element:                           previous last element [blObject]
            label_ID_node:                          node for storing current label ID [blObject]
            node_index:                             current index [int]
            uv_map:                                 uv map for textures if needed [blObject]
            node_offset:                            node offset for y and y [list] [int]
        Returns:
            handle to last node [blObject], handle to assign switch [blObject]
        """

        # define local variables #######################################################################################
        _step_node_width = 200                  # x seperation of nodes
        _step_node_height = 200                 # y seperation of nodes
        ################################################################################ end of define local variables #

        # create image ID handle #######################################################################################
        if label_ID_node is None:
            label_ID_node = node_tree.node_tree.nodes.new("ShaderNodeValue")
            label_ID_node.location = ((node_offset[0]-400,node_offset[1]-100))
            label_ID_node.name = "label_step_ID"
            label_ID_node.label = "label_step_ID"
            label_ID_node.outputs[0].default_value = 1
        ############################################################################### end of create image ID handle #

        # create image nodes ###########################################################################################
        _x_offset = (node_index+1)*_step_node_width + node_offset[0]
        _y_offset = (node_index+1)*_step_node_height + node_offset[1]

        _semantic_node_offset = [(node_index+1)*_step_node_width*2 + node_offset[0]-1000,(node_index+1)*\
                                                                                _step_node_height + node_offset[1]+200]

        _semantic_tree, self._semantic_pass_id = self.create_semantic_nodes(node_tree=self._world_node_tree,
                                                                        label_ID_vec=label_vec,
                                                                        num_label_per_channel=15, # TODO add in script
                                                                        env_mode=True,
                                                                        uv_map=uv_map,
                                                                        node_offset=_semantic_node_offset)

        _semantic_tree.inputs[0].default_value = 1

        # create new mix node ######################################################################################
        _current_mix_shader_node = node_tree.node_tree.nodes.new("ShaderNodeMixRGB")
        _current_mix_shader_node.location = (((node_index+1)*_step_node_width*2 + node_offset[0],
                                            (node_index+1)*_step_node_height + node_offset[1]))
        ############################################################################### end of create new mix node #

        # create compare node ######################################################################################
        _current_compare_node = node_tree.node_tree.nodes.new("ShaderNodeMath")
        _current_compare_node.location = (((node_index+1)*_step_node_width*2 + node_offset[0],
                                            node_offset[1]-_step_node_height))
        _current_compare_node.operation = 'COMPARE'
        _current_compare_node.inputs[0].default_value = node_index
        _current_compare_node.inputs[2].default_value = 0      # delta value should be zero for equal comparison
        ############################################################################### end of create compare node #


        # link nodes togther #######################################################################################
        node_tree.node_tree.links.new(_current_mix_shader_node.inputs[0], _current_compare_node.outputs[0])
        if last_element is not None:
            node_tree.node_tree.links.new(_current_mix_shader_node.inputs[1], last_element.outputs[0])
        node_tree.node_tree.links.new(_current_mix_shader_node.inputs[2], _semantic_tree.outputs[0])
            
        node_tree.node_tree.links.new(_current_compare_node.inputs[1], label_ID_node.outputs[0])
        ################################################################################ end of link nodes togther #
        #################################################################################### end of create image nodes #

        # return last mix shader node
        return _current_mix_shader_node, label_ID_node


    def step(self,keyframe):
        """ step function
        Args:
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        # get next hdri ID
        self._current_hdri_id = self._get_next_hdri_id(current_hdri_index=self._current_hdri_id)

        # activate hdri
        self._activate_hdri(hdri_id=self._current_hdri_id,keyframe=keyframe)


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
            self._semantic_pass_id.outputs[0].default_value = pass_cfg["activationID"]+1
            if keyframe > -1:
                self._semantic_pass_id.outputs[0].keyframe_insert('default_value', frame=keyframe)

                # set interpolation to constant ############################################################################
                _fcurves = self._world_node_tree.node_tree.animation_data.action.fcurves
                for fcurve in _fcurves:
                    for kf in fcurve.keyframe_points:
                        kf.interpolation = 'CONSTANT'
            ##################################################################### end of set interpolation to constant #
        ####################################################################################### end of set semantic ID #


    def _get_random_number(self,min_max_array):
        """ get random number from array; use uniformal distribution
        Args:
            min_max_array:      define min and max value [min_value, max_value] [float,float]; if just one value is
                                added to list, the same value is returned
        Returns:
            return random value [float]
        """

        # check length of array and caluclate random number ############################################################
        if len(min_max_array) > 1:
            return random.uniform(min_max_array[0],min_max_array[1])
        else:
            return min_max_array[0]
        ##################################################### end of check length of array and caluclate random number #


    def create(self,last_element=None):
        """ create function
        Args:
            last_element:           current last element in node tree [blObject]
        Returns:
            return new last element [blObject]
        """

        # init hdri selection list
        self._selection_option = self._cfg["selectionOption"]

        # add base hdri
        _current_last_output =  self._create_base_hdri(last_element=last_element,node_offset=self._node_offset)

        # set instance nodes ###########################################################################################
        _label_ID_vec = [0]

        # create switching nodes for semantics
        _instance_switching_node = self.create_single_semantic_node(node_tree=self._world_node_tree,
                                                                    label_ID=_label_ID_vec[0],
                                                                    num_label_per_channel=15,
                                                                    node_offset=[-2000,-2000])

        # link switching nodes with tree
        self._world_node_tree.node_tree.links.new(_instance_switching_node.inputs[1], _current_last_output)

        # update current last output
        _current_last_output = _instance_switching_node.outputs[0]
        #################################################################################### end of set instance nodes #

        # Pass entries #################################################################################################
        # RGBDPass entries #############################################################################################
        self.add_pass_entry(pass_name="RGBDPass",
                            node_handle=self._semantic_switching_node,
                            value_type="inputs",
                            value=[0,0])
        self.add_pass_entry(pass_name="RGBDPass",
                            node_handle=_instance_switching_node,
                            value_type="inputs",
                            value=[0,0])
        ###################################################################################### end of RGBDPass entries #
        
        # SemanticPass entries #########################################################################################
        self.add_pass_entry(pass_name="SemanticPass",
                            node_handle=self._semantic_switching_node,
                            value_type="inputs",
                            value=[0,1])
        self.add_pass_entry(pass_name="SemanticPass",
                            node_handle=_instance_switching_node,
                            value_type="inputs",
                            value=[0,0])
        ################################################################################## end of SemanticPass entries #

        # SemanticPass entries #########################################################################################
        self.add_pass_entry(pass_name="InstancePass",
                            node_handle=_instance_switching_node,
                            value_type="inputs",
                            value=[0,1])
        ################################################################################## end of SemanticPass entries #
        ########################################################################################## end of Pass entries #

        # return new last element
        return _current_last_output