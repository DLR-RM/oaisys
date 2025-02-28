# blender imports
import bpy

# utility imports
import numpy as np
import csv
import random
import importlib

# TSS specific imports
from src.TSSBase import TSSBase
from src.tools.NodeTools import NodeTools

class TSSEnvironmentEffects(TSSBase,NodeTools):
    """docstring for TSSEnvironmentEffects
        
        base class for Environment Effects

    """
    def __init__(self):
        super(TSSEnvironmentEffects, self).__init__()
        # class vars ###################################################################################################
        self._world_node_tree = None                    # world node tree [blObject]
        self._render_layers_node = None                 # render passes node in compositor [blObject]
        self._node_offset = [0,0]                       # node offsets for nodes in compositor [blObject]
        self._num_labels_per_channel = 51
        ############################################################################################ end of class vars #


    def reset_module(self):
        """ reset all local vars
            DO NOT OVERWRITE!
        Args:
            None
        Returns:
            None
        """

        # call internal reset functions ################################################################################
        self.reset()
        self.reset_base()
        ######################################################################### end of call internal reset functions #

        # reset base class vars ########################################################################################
        self._world_node_tree = None
        self._render_layers_node = None
        self._node_offset = [0,0]
        ################################################################################# end of reset base class vars #


    def reset(self):
        """ specific reset function
            OVERWRITE!
        Args:
            None
        Returns:
            None
        """

        pass


    def set_world_node_tree(self,world_node_tree):
        """ set world node tree
            DO NOT OVERWRITE!
        Args:
            world_node_tree:            world node tree [blObject]
        Returns:
            None
        """

        self._world_node_tree = world_node_tree


    def set_render_layers_node(self,render_layers_node):
        """ set main render passes node
            DO NOT OVERWRITE!
        Args:
            render_layers_node:         render layer node [blObject]
        Returns:
            None
        """

        self._render_layers_node = render_layers_node


    def set_node_offset(self,node_offset):
        """ set node offset
            DO NOT OVERWRITE!
        Args:
            node_offset:                node offset [x,y]
        Returns:
            None
        """

        self._node_offset = node_offset


    def _print_msg(self,skk): print("\033[94m {}\033[00m" .format(skk))


    def create(self):
        """ create function
            OVERWRITE!
        Args:
            None
        Returns:
            None
        """

        pass


    def step(self, keyframe):
        """ step function
            OVERWRITE!
        Args:
            None
        Returns:
            None
        """

        pass