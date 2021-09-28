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

class BloomEffect(TSSRenderPostProcessing):
    """docstring for BloomEffect"""
    def __init__(self,pass_name):
        super(BloomEffect, self).__init__(pass_name=pass_name)

        # class vars ###################################################################################################
        self._glare_node = None                         # glare node [blObject]
        ############################################################################################ end of class vars #


    def reset(self):
        """ reset module
        Args:
            None
        Returns:
            None
        """

        # reset class vars
        self._glare_node = None


    def _create_glare_node(self,node_offset=[0,0]):
        """ create glare node
        Args:
            node_offset:    offset of nodes in compositor [x,y] [int,int]
        Returns:
            None
        """

        # create glare node ############################################################################################
        self._glare_node = self._node_tree.nodes.new(type="CompositorNodeGlare")
        self._glare_node.location = (node_offset[0],node_offset[1])
        self._glare_node.glare_type = "FOG_GLOW"

        # set quality value ############################################################################################
        if "quality" in self._cfg:
            self._glare_node.quality = self._cfg["quality"]
        else:
            self._glare_node.quality = 0.8
        ##################################################################################### end of set quality value #

        # set mix value ################################################################################################
        if "mix" in self._cfg:
            self._glare_node.mix = self._cfg["mix"]
        else:
            self._glare_node.mix = 0.0
        ######################################################################################### end of set mix value #

        # set threshold value ##########################################################################################
        if "threshold" in self._cfg:
            self._glare_node.threshold = self._cfg["threshold"]
        else:
            self._glare_node.threshold = 8
        ################################################################################### end of set threshold value #

        # set size value ###############################################################################################
        if "size" in self._cfg:
            self._glare_node.size = self._cfg["size"]
        else:
            self._glare_node.size = 8
        ######################################################################################## end of set size value #

        # link nodes and update compositor list ########################################################################
        self._node_tree.links.new(  self._glare_node.inputs[0],
                                    self._compositor_pass_list["combined_rgb"])

        self._compositor_pass_list["combined_rgb"] = self._glare_node.outputs[0]
        ################################################################# end of link nodes and update compositor list #
        ##################################################################################### end of create glare node #


    def create(self):
        """ create function
        Args:
            None
        Returns:
            None
        """

        # create glare node
        self._create_glare_node(node_offset=self._node_offset)