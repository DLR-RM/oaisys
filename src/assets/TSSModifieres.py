# blender imports
import bpy

# utility imports
import numpy as np
import csv
import random
import importlib

class TSSModifieres(object):
    """docstring for TSSModifieres"""
    def __init__(self):
        super(TSSModifieres, self).__init__()
        # class vars ###################################################################################################
        ############################################################################################ end of class vars #


    def _add_sub_div(self,bl_object):
        _modifier = bl_object.modifiers.new(bl_object.name + "subsurf", type='SUBSURF')

        return _modifier


    def _add_deform(self):
        pass

    def _add_displacement(self,bl_object):
        _modifier = bl_object.modifiers.new(bl_object.name + "globalStageDisplacment", type='DISPLACE')
        
        return _modifier