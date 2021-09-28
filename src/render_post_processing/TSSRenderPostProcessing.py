# blender imports
import bpy

# utility imports
import numpy as np
import csv
import random

class TSSRenderPostProcessing(object):
    """docstring for TSSRenderPostProcessing"""
    def __init__(self,pass_name):
        super(TSSRenderPostProcessing, self).__init__()
        # class vars ###################################################################################################
        self._cfg = {}                              # cfg dict [dict]
        self._general_cfg = {}                      # general cfg dict [dict]
        self._global_step_index = 0                 # global index [uint]
        self._local_step_index = 0                  # global index [uint]
        self._node_offset = [0,0]
        self._render_pass_list = {}
        self._pass_name = pass_name                 # name of pass object [string]
        ############################################################################################ end of class vars #

    def reset_module(self):
        """ reset all local vars
        Args:
            None
        Returns:
            None
        """

        self.reset()


    def reset():
        pass


    def set_compositor_pass_list(self,compositor_pass_list):
        self._compositor_pass_list = compositor_pass_list


    def get_compositor_pass_list(self):
        return self._compositor_pass_list


    def set_node_offset(self,node_offset):
        """ set node offset of nodes in compositor
            DO NOT OVERWRITE!
        Args:
            node_offset:    offset of nodes in compositor [x,y] [int,int]
        Returns:
            None
        """

        self._node_offset = node_offset


    def set_general_cfg(self,cfg):
        """ set general cfg dict for object
            DO NOT OVERWRITE!
        Args:
            cfg:            cfg dict of class [dict]
        Returns:
            None
        """
 
        self._general_cfg = cfg


    def get_general_cfg(self):
        """ get general cfg dict of object
            DO NOT OVERWRITE!
        Args:
            None
        Returns:
            cfg file of class [dict]
        """

        return self._general_cfg


    def update_cfg(self,cfg):
        """ set cfg dict for object
            DO NOT OVERWRITE!
        Args:
            cfg:            cfg dict of class [dict]
        Returns:
            None
        """

        self._cfg = cfg


    def get_cfg(self):
        """ get cfg dict of object
            DO NOT OVERWRITE!
        Args:
            None
        Returns:
            cfg file of class [dict]
        """

        return self._cfg


    def set_render_layers_node(self,render_layers_node):
        """ set render layers node
            DO NOT OVERWRITE!
        Args:
            render_layers_node:     basic blender node to get information about the passes [blObject]
        Returns:
            None
        """

        self._render_layers_node = render_layers_node


    def set_node_tree(self,node_tree):
        """ set render layers node
            DO NOT OVERWRITE!
        Args:
            node_tree:              node tree handle for compositor [blObject]
        Returns:
            None
        """

        self._node_tree = node_tree
        

    def increase_global_step_index(self):
        """ set render layers node
            DO NOT OVERWRITE!
        Args:
            node_tree:              node tree handle for compositor [blObject]
        Returns:
            None
        """
        self._global_step_index += 1
        self._local_step_index += 1


    def reset_global_step_index(self):
        """ set render layers node
            DO NOT OVERWRITE!
        Args:
            node_tree:              node tree handle for compositor [blObject]
        Returns:
            None
        """
        self._global_step_index = 0


    def set_global_step_index(self,index):
        """ set global step index
            DO NOT OVERWRITE!
        Args:
            node_tree:              node tree handle for compositor [blObject]
        Returns:
            None
        """
        self._global_step_index = index


    def create(self):
        """ create function
            OVERWRITE!
        Args:
            None
        Returns:
            None
        """

        pass


    def step(self):
        """ step function
            OVERWRITE!
        Args:
            None
        Returns:
            None
        """

        pass


    def activate_pass(self):
        """ activate function
            OVERWRITE!
        Args:
            None
        Returns:
            return None
        """

        return None


    def deactivate_pass(self):
        """ deactivate function
            OVERWRITE!
        Args:
            None
        Returns:
            None
        """

        pass