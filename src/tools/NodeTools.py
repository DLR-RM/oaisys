# blender imports
import bpy

# utility imports
import numpy as np
import csv
import random
import importlib

class NodeTools(object):
    """docstring for NodeTools"""
    def __init__(self):
        super(NodeTools, self).__init__()
        # class vars ###################################################################################################
        ############################################################################################ end of class vars #

    def create_switching_node(self, node_tree, label_list, env_mode=False, uv_map=None, node_offset=[0,0]):
        """ create switching nodes pipeline
        Args:
            node_tree:                              node tree handle [blObject]
            label_list:                             label ID list; contains RGB labels [list] [R,G,B]
            node_offset:                            node offset for y and y [list] [int]
        Returns:
            handle to last node [blObject], handle to assign switch [blObject]
        """

        # define local variables #######################################################################################
        _prev_mix_node = None                   # helper var to store previous mix node
        _current_mix_shader_node = None         # helper var to store current mix shader
        _step_node_width = 200                  # x seperation of nodes
        _step_node_height = 200                 # y seperation of nodes
        _num_labels = len(label_list)           # number of labels
        ################################################################################ end of define local variables #

        # create labelID handle ########################################################################################
        _label_ID_Node = node_tree.node_tree.nodes.get("semantic_pass_ID", None)
        if _label_ID_Node is None:
            _label_ID_Node = node_tree.node_tree.nodes.new("ShaderNodeValue")
            _label_ID_Node.location = ((node_offset[0]-1000,node_offset[1]))
            _label_ID_Node.name = "semantic_pass_ID"
            _label_ID_Node.label = "semantic_pass_ID"
            _label_ID_Node.outputs[0].default_value = 1
        ################################################################################# end of create labelID handle #

        # create label nodes ###########################################################################################
        for labelIdx, label in enumerate(label_list):

            label_ID = labelIdx + 1
            _mapping_name = "mapping"
            if isinstance(label, dict):
                _x_offset = label_ID*_step_node_width + node_offset[0]
                _y_offset = (_num_labels-label_ID)*_step_node_height + node_offset[1]
                _current_color_node = self.create_label_remap_node( node_tree=node_tree,
                                                                    label_map=label,
                                                                    group_name=_mapping_name,
                                                                    env_mode=env_mode,
                                                                    num_label_per_channel=15.0,
                                                                    node_offset=[_x_offset,_y_offset])
                if uv_map is not None:
                    node_tree.node_tree.links.new(_current_color_node.inputs[0], uv_map)
            else:
                # create color node ####################################################################################
                _current_color_node = node_tree.node_tree.nodes.new("ShaderNodeRGB")
                _current_color_node.location = ((label_ID*_step_node_width + node_offset[0],
                                                (_num_labels-label_ID)*_step_node_height + node_offset[1]))
                _current_color_node.outputs[0].default_value = (label[0],label[1],label[2], 1)
                ############################################################################# end of create color node #

            # create new mix node ######################################################################################
            _current_mix_shader_node = node_tree.node_tree.nodes.new("ShaderNodeMixRGB")
            _current_mix_shader_node.location = ((label_ID*_step_node_width*2 + node_offset[0],
                                                (_num_labels-label_ID)*_step_node_height + node_offset[1]))
            ############################################################################### end of create new mix node #

            # create compare node ######################################################################################
            _current_compare_node = node_tree.node_tree.nodes.new("ShaderNodeMath")
            _current_compare_node.location = ((label_ID*_step_node_width*2 + node_offset[0],
                                                node_offset[1]-_step_node_height))
            _current_compare_node.operation = 'COMPARE'
            _current_compare_node.inputs[0].default_value = label_ID
            _current_compare_node.inputs[2].default_value = 0      # delta value should be zero for equal comparison
            ############################################################################### end of create compare node #


            # link nodes togther #######################################################################################
            node_tree.node_tree.links.new(_current_mix_shader_node.inputs[0], _current_compare_node.outputs[0])
            if _prev_mix_node is not None:
                node_tree.node_tree.links.new(_current_mix_shader_node.inputs[1], _prev_mix_node.outputs[0])
            node_tree.node_tree.links.new(_current_mix_shader_node.inputs[2], _current_color_node.outputs[0])
            
            node_tree.node_tree.links.new(_current_compare_node.inputs[1], _label_ID_Node.outputs[0])
            ################################################################################ end of link nodes togther #

            # update _prev_mix_node
            _prev_mix_node = _current_mix_shader_node
        #################################################################################### end of create label nodes #

        # return last mix shader node
        return _current_mix_shader_node, _label_ID_Node


    def create_pbr_texture_nodes(self):
        pass


    def _id_to_rgb(self, id_value, num_label_per_channel, step_label_classes):
        # calc RGB value for label level ###########################################################################
        # TODO: add formula here!
        # first devision step
        _devision1 = id_value // (num_label_per_channel*num_label_per_channel)
        _residual1 = id_value % (num_label_per_channel*num_label_per_channel)

        # second devision step
        _devision2 = _residual1 // num_label_per_channel
        _residual2 = _residual1 % num_label_per_channel

        # check if numbers are in boundary
        if _devision1*step_label_classes > num_label_per_channel:
            _devision1 = num_label_per_channel
            print('WARNING: Label class exceeded limit of class ID! TSS sets highest label level value to 255')

        # calculate resulting RGB vec
        _rgb_value = [_devision1*step_label_classes,_devision2*step_label_classes,_residual2*step_label_classes]

        # return RGB value
        return _rgb_value
        #################################################################### end of calc RGB value for label level #


    def create_single_semantic_node(self,
                                    node_tree,
                                    label_ID,
                                    num_label_per_channel,
                                    step_label_classes=None,
                                    node_offset=[0,0]):
        """ create semantic nodes
        Args:
            node_tree:                              node tree handle [blObject]
            label_ID_vec:                           label ID vector; contains labels which are mapped to
                                                    RGB values [list] [int]
            num_label_per_channel:                  number of labels per RGB channel [int]
            step_label_classes:                     stepping size per channel; usually 1/num_label_per_channel; [float]
            node_offset:                            node offset for y and y [list] [int]
        Returns:
            semantic switching node [blObject], handle to assign switch [blObject]
        """

        # set stepping if not assigned #################################################################################
        if step_label_classes is None:
            step_label_classes = 1./num_label_per_channel
        ########################################################################## end of set stepping if not assigned #

        # calc RGB value for label level
        _rgb_value = self._id_to_rgb(   id_value=label_ID,
                                        num_label_per_channel=num_label_per_channel,
                                        step_label_classes=step_label_classes)

        _label_node = node_tree.node_tree.nodes.new("ShaderNodeRGB")
        _label_node.location = (node_offset[0]-500,node_offset[1])
        _label_node.outputs[0].default_value = (_rgb_value[0],_rgb_value[1],_rgb_value[2], 1)

        # create label switching node ##################################################################################
        _label_active_node = node_tree.node_tree.nodes.new("ShaderNodeMixRGB")
        _label_active_node.inputs[0].default_value = 0
        _label_active_node.location = (node_offset[0],node_offset[1])
        ########################################################################### end of create label switching node #

        # link nodes
        node_tree.node_tree.links.new(_label_active_node.inputs[2], _label_node.outputs[0])

        # return switching node
        return _label_active_node


    def create_semantic_nodes(  self,
                                node_tree,
                                label_ID_vec,
                                num_label_per_channel,
                                env_mode=False,
                                step_label_classes=None,
                                uv_map=None,
                                node_offset=[0,0]):
        """ create semantic nodes
        Args:
            node_tree:                              node tree handle [blObject]
            label_ID_vec:                           label ID vector; contains labels which are mapped to
                                                    RGB values [list] [int]
            num_label_per_channel:                  number of labels per RGB channel [int]
            step_label_classes:                     stepping size per channel; usually 1/num_label_per_channel; [float]
            uv_map:                                 uv map [blObject]
            node_offset:                            node offset for y and y [list] [int]
        Returns:
            semantic switching node [blObject], handle to assign switch [blObject]
        """

        # set stepping if not assigned #################################################################################
        if step_label_classes is None:
            step_label_classes = 1./num_label_per_channel
        ########################################################################## end of set stepping if not assigned #

        # define local vars ############################################################################################
        _label_vec = []
        ##################################################################################### end of define local vars #

        # calculate RGB value for each label ###########################################################################
        for label_channel in label_ID_vec:

            if isinstance(label_channel, dict):
                _rgb_value = label_channel
            else:
                # calc RGB value for label level
                _rgb_value = self._id_to_rgb(   id_value=label_channel,
                                                num_label_per_channel=num_label_per_channel,
                                                step_label_classes=step_label_classes)

            # store calculated RGB label value
            _label_vec.append(_rgb_value)
        #################################################################### end of calculate RGB value for each label #

        # create RGB label nodes
        _label_node,_label_ID_Node = self.create_switching_node(node_tree=node_tree,
                                                                label_list=_label_vec,
                                                                env_mode=env_mode,
                                                                uv_map=uv_map,
                                                                node_offset=[node_offset[0]-3000, node_offset[1]+0])

        # create label switching node ##################################################################################
        _label_active_node = node_tree.node_tree.nodes.new("ShaderNodeMixRGB")
        _label_active_node.inputs[0].default_value = 0
        _label_active_node.location = (node_offset[0]-500,node_offset[1]+0)
        ########################################################################### end of create label switching node #

        # link nodes
        node_tree.node_tree.links.new(_label_active_node.inputs[2], _label_node.outputs[0])

        # return switching node
        return _label_active_node,_label_ID_Node


    def create_image_switching_node(self, node_tree, image_list, uv_map=None, node_offset=[0,0]):
        """ create switching nodes pipeline for images
        Args:
            node_tree:                              node tree handle [blObject]
            image_list:                             image file path list; contains file paths [list]
            node_offset:                            node offset for y and y [list] [int]
        Returns:
            handle to last node [blObject], handle to assign switch [blObject]
        """

        # define local variables #######################################################################################
        _prev_mix_node = None                   # helper var to store previous mix node
        _current_mix_shader_node = None         # helper var to store current mix shader
        _step_node_width = 200                  # x seperation of nodes
        _step_node_height = 200                 # y seperation of nodes
        _num_images = len(image_list)           # number of images
        ################################################################################ end of define local variables #

        # create image ID handle #######################################################################################
        _image_ID_Node = node_tree.node_tree.nodes.get("semantic_pass_ID", None)
        if _image_ID_Node is None:
            _image_ID_Node = node_tree.node_tree.nodes.new("ShaderNodeValue")
            _image_ID_Node.location = ((node_offset[0]-1000,node_offset[1]))
            _image_ID_Node.name = "image_pass_ID"
            _image_ID_Node.label = "image_pass_ID"
            _image_ID_Node.outputs[0].default_value = 1
        ############################################################################### end of create image ID handle #

        # create image nodes ###########################################################################################
        for imageIdx, image in enumerate(image_list):

            image_ID = imageIdx + 1
            _x_offset = image_ID*_step_node_width + node_offset[0]
            _y_offset = (_num_images-image_ID)*_step_node_height + node_offset[1]
            _current_image_node = node_tree.node_tree.nodes.new('ShaderNodeTexEnvironment')
            _current_image_node.location = (node_offset[0]-2000,node_offset[1]+300)

            if uv_map is not None:
                node_tree.node_tree.links.new(_current_color_node.inputs[0], uv_map)

            # create new mix node ######################################################################################
            _current_mix_shader_node = node_tree.node_tree.nodes.new("ShaderNodeMixRGB")
            _current_mix_shader_node.location = ((image_ID*_step_node_width*2 + node_offset[0],
                                                (_num_images-image_ID)*_step_node_height + node_offset[1]))
            ############################################################################### end of create new mix node #

            # create compare node ######################################################################################
            _current_compare_node = node_tree.node_tree.nodes.new("ShaderNodeMath")
            _current_compare_node.location = ((image_ID*_step_node_width*2 + node_offset[0],
                                                node_offset[1]-_step_node_height))
            _current_compare_node.operation = 'COMPARE'
            _current_compare_node.inputs[0].default_value = image_ID
            _current_compare_node.inputs[2].default_value = 0      # delta value should be zero for equal comparison
            ############################################################################### end of create compare node #


            # link nodes togther #######################################################################################
            node_tree.node_tree.links.new(_current_mix_shader_node.inputs[0], _current_compare_node.outputs[0])
            if _prev_mix_node is not None:
                node_tree.node_tree.links.new(_current_mix_shader_node.inputs[1], _prev_mix_node.outputs[0])
            node_tree.node_tree.links.new(_current_mix_shader_node.inputs[2], _current_color_node.outputs[0])
            
            node_tree.node_tree.links.new(_current_compare_node.inputs[1], _image_ID_Node.outputs[0])
            ################################################################################ end of link nodes togther #

            # update _prev_mix_node
            _prev_mix_node = _current_mix_shader_node
        #################################################################################### end of create image nodes #

        # return last mix shader node
        return _current_mix_shader_node, _image_ID_Node


    def create_instance_nodes(self):
        pass


    def _create_id_to_rgb_node_tree(self,
                                    node_tree,
                                    num_label_per_channel,
                                    step_label_classes=None,
                                    instance_ID_offset=0,
                                    node_offset=[0,0]):


        if step_label_classes is None:
            step_label_classes = 1./num_label_per_channel

        _instance_add_node = node_tree.node_tree.nodes.new('ShaderNodeMath')
        _instance_add_node.label = "instance_add_node"
        _instance_add_node.operation = 'ADD'
        _instance_add_node.location = (0+node_offset[0],200+node_offset[1])
        _instance_add_node.inputs[1].default_value = instance_ID_offset

        # division node for R channel
        _division_node_1 = node_tree.node_tree.nodes.new('ShaderNodeMath')
        _division_node_1.label = "division_node_1"
        _division_node_1.operation = 'DIVIDE'
        _division_node_1.location = (200+node_offset[0],200+node_offset[1])
        _division_node_1.inputs[1].default_value = num_label_per_channel*num_label_per_channel

        # floor node for R channel
        _floor_node_1 = node_tree.node_tree.nodes.new('ShaderNodeMath')
        _floor_node_1.label = "floor_node_1"
        _floor_node_1.operation = 'FLOOR'
        _floor_node_1.location = (400+node_offset[0],200+node_offset[1])

        # modulo division node for R channel
        _modulo_node_1 = node_tree.node_tree.nodes.new('ShaderNodeMath')
        _modulo_node_1.label = "modulo_node_1"
        _modulo_node_1.operation = 'MODULO'
        _modulo_node_1.location = (200+node_offset[0],0+node_offset[1])
        _modulo_node_1.inputs[1].default_value = num_label_per_channel*num_label_per_channel

        # multiple stepwide node for R channel
        _mult_node_1 = node_tree.node_tree.nodes.new('ShaderNodeMath')
        _mult_node_1.label = "mult_node_1"
        _mult_node_1.operation = 'MULTIPLY'
        _mult_node_1.location = (600+node_offset[0],node_offset[1]-200)
        _mult_node_1.inputs[1].default_value = step_label_classes

        # division node for R channel
        _division_node_2 = node_tree.node_tree.nodes.new('ShaderNodeMath')
        _division_node_2.label = "division_node_2"
        _division_node_2.operation = 'DIVIDE'
        _division_node_2.location = (600+node_offset[0],node_offset[1]-200)
        _division_node_2.inputs[1].default_value = num_label_per_channel

        # floor node for R channel
        _floor_node_2 = node_tree.node_tree.nodes.new('ShaderNodeMath')
        _floor_node_2.label = "_floor_node_2"
        _floor_node_2.operation = 'FLOOR'
        _floor_node_2.location = (800+node_offset[0],node_offset[1]-200)

        # modlulo division node for B channel
        _modulo_node_2 = node_tree.node_tree.nodes.new('ShaderNodeMath')
        _modulo_node_2.label = "modulo_node_2"
        _modulo_node_2.operation = 'MODULO'
        _modulo_node_2.location = (400+node_offset[0],node_offset[1]-600)
        _modulo_node_2.inputs[1].default_value = num_label_per_channel

        # multiple stepwide node for G channel
        _mult_node_2 = node_tree.node_tree.nodes.new('ShaderNodeMath')
        _mult_node_2.label ="mult_node_2"
        _mult_node_2.operation = 'MULTIPLY'
        _mult_node_2.location = (1000+node_offset[0],node_offset[1]-200)
        _mult_node_2.inputs[1].default_value = step_label_classes

        # multiple stepwide node for B channel
        _mult_node_3 = node_tree.node_tree.nodes.new('ShaderNodeMath')
        _mult_node_3.label = "mult_node_3"
        _mult_node_3.operation = 'MULTIPLY'
        _mult_node_3.location = (600+node_offset[0],node_offset[1]-600)
        _mult_node_3.inputs[1].default_value = step_label_classes


        # combine nodes
        #node_tree.node_tree.links.new(_instance_add_node.inputs[0], particleInfoNode.outputs[0])
        # R channel
        node_tree.node_tree.links.new(_division_node_1.inputs[0], _instance_add_node.outputs[0])
        node_tree.node_tree.links.new(_floor_node_1.inputs[0], _division_node_1.outputs[0])
        node_tree.node_tree.links.new(_modulo_node_1.inputs[0], _instance_add_node.outputs[0])
        node_tree.node_tree.links.new(_mult_node_1.inputs[0], _floor_node_1.outputs[0])
        # G&B channel
        node_tree.node_tree.links.new(_division_node_2.inputs[0], _modulo_node_1.outputs[0])
        node_tree.node_tree.links.new(_floor_node_2.inputs[0], _division_node_2.outputs[0])
        node_tree.node_tree.links.new(_modulo_node_2.inputs[0], _modulo_node_1.outputs[0])
        node_tree.node_tree.links.new(_mult_node_2.inputs[0], _floor_node_2.outputs[0])
        node_tree.node_tree.links.new(_mult_node_3.inputs[0], _modulo_node_2.outputs[0])
        ##############################################################################


        # combine channels ###########################################
        _combine_shader_node = node_tree.node_tree.nodes.new('ShaderNodeCombineRGB')
        _combine_shader_node.location = (node_offset[0]+1200,node_offset[1]+300)
        node_tree.node_tree.links.new(_combine_shader_node.inputs[0], _mult_node_1.outputs[0])
        node_tree.node_tree.links.new(_combine_shader_node.inputs[1], _mult_node_2.outputs[0])
        node_tree.node_tree.links.new(_combine_shader_node.inputs[2], _mult_node_3.outputs[0])
        ###########################################

        # combine label and instance channel ###########################################
        _instance_switch_node = node_tree.node_tree.nodes.new('ShaderNodeMixRGB')
        _instance_switch_node.name = "instanceLabelsEnabled"
        _instance_switch_node.label = "instanceLabelsEnabled"
        _instance_switch_node.inputs[0].default_value = 0
        _instance_switch_node.location = (node_offset[0]+2000,node_offset[1]+300)
        #node_tree.node_tree.links.new(_instance_switch_node.inputs[1], _label_node.outputs[0])
        node_tree.node_tree.links.new(_instance_switch_node.inputs[2], _combine_shader_node.outputs[0])
        ###########################################

        return _instance_switch_node, _instance_add_node


    def _multiple_255_node(self,sub_tree,node_name,node_offset=[0,0]):
        _mult_node = sub_tree.nodes.new('ShaderNodeMath')
        _mult_node.label = node_name
        _mult_node.operation = 'MULTIPLY'
        _mult_node.location = (node_offset[0],node_offset[1])
        _mult_node.inputs[0].default_value = 255.0

        return _mult_node


    def _compare_node(self,sub_tree,value,epsilon,node_name,node_offset=[0,0]):
        _compare_node = sub_tree.nodes.new('ShaderNodeMath')
        _compare_node.label = node_name
        _compare_node.operation = 'COMPARE'
        _compare_node.location = (node_offset[0],node_offset[1])
        _compare_node.inputs[0].default_value = value
        _compare_node.inputs[2].default_value = epsilon

        return _compare_node


    def create_label_remap_node(self,
                                node_tree,
                                label_map,
                                group_name,
                                num_label_per_channel,
                                env_mode = False,
                                step_label_classes=None,
                                tolerance_value=10.0,
                                node_offset=[0,0]):

        # set stepping if not assigned #################################################################################
        if step_label_classes is None:
            step_label_classes = 1./num_label_per_channel
        ########################################################################## end of set stepping if not assigned #

        # create node group
        _sub_tree = bpy.data.node_groups.new(type="ShaderNodeTree", name=group_name)

        # inputs
        _group_input = _sub_tree.nodes.new("NodeGroupInput")
        _sub_tree.inputs.new('NodeSocketVector','Mapping')
        _group_input.location = (-900,-500)

        # outputs
        _group_output = _sub_tree.nodes.new("NodeGroupOutput")
        _sub_tree.outputs.new('NodeSocketColor','color_id')


        # build up general node logic part #############################################################################
        # load mapping image
        if env_mode:
            _mapping_image = _sub_tree.nodes.new('ShaderNodeTexEnvironment')
        else:
            _mapping_image = _sub_tree.nodes.new('ShaderNodeTexImage')
        _mapping_image.label = "mapping_texture"
        _mapping_image.location = (-500,-500)
        _mapping_image.image = bpy.data.images.load(label_map["filePath"])
        _mapping_image.image.colorspace_settings.name = 'Non-Color'
        _mapping_image.interpolation = 'Closest'
        _sub_tree.links.new(_mapping_image.inputs[0], _group_input.outputs[0])
        ################################################################################### end of build up node logic #
        
        _mapping_dict = None

        if "mappingTable" in label_map:
            _mapping_dict = label_map["mappingTable"]


        _last_mix_shader_node = _mapping_image
        if _mapping_dict is not None:
            _color_seperation_node = _sub_tree.nodes.new(type="ShaderNodeSeparateRGB")
            _color_seperation_node.label = "color_seperation_node"
            _color_seperation_node.location = (400, 0)
            _sub_tree.links.new(_color_seperation_node.inputs[0], _mapping_image.outputs[0])

            # create multiple nodes ################################################################################
            # red channel
            _mult_R = self._multiple_255_node(  sub_tree=_sub_tree,
                                                node_name="mult_red",
                                                node_offset=[800,700])
            _sub_tree.links.new(_mult_R.inputs[1], _color_seperation_node.outputs[0])

            # green channel
            _mult_G = self._multiple_255_node(  sub_tree=_sub_tree,
                                                node_name="mult_green",
                                                node_offset=[800,400])
            _sub_tree.links.new(_mult_G.inputs[1], _color_seperation_node.outputs[1])

            # blue channel
            _mult_B = self._multiple_255_node(  sub_tree=_sub_tree,
                                                node_name="mult_blue",
                                                node_offset=[800,100])
            _sub_tree.links.new(_mult_B.inputs[1], _color_seperation_node.outputs[2])
            ######################################################################### end of create multiple nodes #

            _map_ID = 0
            _map_offset = [0,2000]

            for key, value in _mapping_dict.items():

                _prev_color = value[0]
                print("_prev_color: ", _prev_color)

                # create compare nodes #################################################################################
                # red channel
                _compare_R = self._compare_node(sub_tree=_sub_tree,
                                                value=_prev_color[0],
                                                epsilon=tolerance_value,
                                                node_name="compare_red",
                                                node_offset=[1300,700+_map_ID*_map_offset[1]])
                _sub_tree.links.new(_compare_R.inputs[1], _mult_R.outputs[0])

                # green channel
                _compare_G = self._compare_node(sub_tree=_sub_tree,
                                                value=_prev_color[1],
                                                epsilon=tolerance_value,
                                                node_name="compare_green",
                                                node_offset=[1300,400+_map_ID*_map_offset[1]])
                _sub_tree.links.new(_compare_G.inputs[1], _mult_G.outputs[0])

                # blue channel
                _compare_B = self._compare_node(sub_tree=_sub_tree,
                                                value=_prev_color[2],
                                                epsilon=tolerance_value,
                                                node_name="compare_blue",
                                                node_offset=[1300,100+_map_ID*_map_offset[1]])
                _sub_tree.links.new(_compare_B.inputs[1], _mult_B.outputs[0])
                ########################################################################## end of create compare nodes #

                # combine results ######################################################################################
                # combine output of red and green channel
                _add_node1 = _sub_tree.nodes.new('ShaderNodeMath')
                _add_node1.label = "combine_red_and_green"
                _add_node1.operation = 'ADD'
                _add_node1.location = (1800,500+_map_ID*_map_offset[1])
                _sub_tree.links.new(_add_node1.inputs[0], _compare_R.outputs[0])
                _sub_tree.links.new(_add_node1.inputs[1], _compare_G.outputs[0])

                # combine output of red/green and blue channel
                _add_node2 = _sub_tree.nodes.new('ShaderNodeMath')
                _add_node2.label = "combine_all_channels"
                _add_node2.operation = 'ADD'
                _add_node2.location = (1800,100+_map_ID*_map_offset[1])
                _sub_tree.links.new(_add_node2.inputs[0], _add_node1.outputs[0])
                _sub_tree.links.new(_add_node2.inputs[1], _compare_B.outputs[0])
                ############################################################################### end of combine results #

                # compare result #######################################################################################
                _compare_node = _sub_tree.nodes.new('ShaderNodeMath')
                _compare_node.label = "combine_red_and_green"
                _compare_node.operation = 'ADD'
                _compare_node.location = (2300,700+_map_ID*_map_offset[1])
                _compare_node.operation = 'COMPARE'
                _compare_node.inputs[1].default_value = 3
                _compare_node.inputs[2].default_value = 0
                _sub_tree.links.new(_compare_node.inputs[0], _add_node2.outputs[0])
                ############################################################################### end of compare results #

                # get or calculate label value #########################################################################
                _label_value = _sub_tree.nodes.new("ShaderNodeRGB")
                _label_value.location = (2300,300+_map_ID*_map_offset[1])

                _rgb_value = None

                if len(value[1]) > 1:
                    _rgb_value = value[1]
                else:
                    _rgb_value = self._id_to_rgb( id_value=value[1][0],
                                                num_label_per_channel=num_label_per_channel,
                                                step_label_classes=step_label_classes)

                _label_value.outputs[0].default_value = (_rgb_value[0],_rgb_value[1],_rgb_value[2], 1)
                ################################################################## end of get or calculate label value #

                # combine overlay ######################################################################################
                _current_mix_shader_node = _sub_tree.nodes.new("ShaderNodeMixRGB")
                _current_mix_shader_node.location = (2800+_map_ID*500,_map_ID*_map_offset[1])
                _sub_tree.links.new(_current_mix_shader_node.inputs[0], _compare_node.outputs[0])
                _sub_tree.links.new(_current_mix_shader_node.inputs[1], _last_mix_shader_node.outputs[0])
                _sub_tree.links.new(_current_mix_shader_node.inputs[2], _label_value.outputs[0])
                ############################################################################### end of combine overlay #

                # update loop vars #####################################################################################
                _last_mix_shader_node = _current_mix_shader_node
                _map_ID += 1
                ############################################################################## end of update loop vars #

        else:
            pass
            # connect iamge to output

        _sub_tree.links.new(_group_output.inputs[0], _last_mix_shader_node.outputs[0])
        _group_output.location = (_last_mix_shader_node.location[0]+500,_last_mix_shader_node.location[1])
        

        # attach group to node tree ####################################################################################
        _node_group = node_tree.node_tree.nodes.new("ShaderNodeGroup")
        _node_group.node_tree = _sub_tree
        _node_group.location = (node_offset[0],node_offset[1])
        ###################################################################### end of build up general node logic part #

        # return node group
        return _node_group
