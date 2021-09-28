# blender imports
import bpy

# utility imports
import numpy as np
import csv
import random
import os
import shutil
import pathlib

from src.render_post_processing.TSSRenderPostProcessing import TSSRenderPostProcessing

class CombineEffect(TSSRenderPostProcessing):
    """docstring for CombineEffect"""
    def __init__(self,pass_name):
        super(CombineEffect, self).__init__(pass_name=pass_name)

        # class vars ###################################################################################################
        self._combine_node = None                   # combine blender node [blObject]
        ############################################################################################ end of class vars #


    def reset(self):
        """ reset module
        Args:
            None
        Returns:
            None
        """

        # reset class vars
        self._combine_node = None


    def _create_combine_node(self,node_offset=[0,0]):
        """ create combine node
        Args:
            node_offset:    offset of nodes in compositor [x,y] [int,int]
        Returns:
            None
        """

        # create combine node ##########################################################################################
        self._combine_node = self._node_tree.nodes.new(type="CompositorNodeMixRGB")
        self._combine_node.location = (node_offset[0]+300,node_offset[1])
        self._combine_node.blend_type = self._cfg["combineOption"]
        self._combine_node.inputs[0].default_value = self._cfg['combineFac']
        try:
            self._node_tree.links.new(  self._combine_node.inputs[1],
                                        self._compositor_pass_list[self._cfg['combineInput1']])
            self._node_tree.links.new(  self._combine_node.inputs[2],
                                        self._compositor_pass_list[self._cfg['combineInput2']])

            self._compositor_pass_list[self._cfg["outputName"]] = self._combine_node.outputs[0]
        except:
            # manage import error
            raise Exception("Cannot combine inputs, maybe render pass does not exist!")
            return -1
        ################################################################################### end of create combine node #


    def create(self):
        """ create function
        Args:
            None
        Returns:
            None
        """

        self._create_combine_node(node_offset=self._node_offset)