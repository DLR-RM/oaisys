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
        self._single_stage = None                               # blender stage objcet [blObject]
        ############################################################################################ end of class vars #


    def reset(self):
        """ reset all local vars
        Args:
            None
        Returns:
            None
        """

        self._single_stage = None


    def update_after_meshes(self):
        self._single_stage.modifiers.new("lastSubsurf", type='SUBSURF')


    def _create_single_stage(self, file_path, object_file_name):

        # def local vars ###############################################################################################
        self._single_stage = None
        ######################################################################################## end of def local vars #

        # check if relative or absolute path is provided
        if not os.path.isabs(file_path):
            # create abs path
            _current_path = os.path.dirname(__file__)
            file_path = os.path.join(_current_path,"../../../",file_path)

        # load/append object to scene ##################################################################################
        bpy.ops.wm.append(directory=os.path.join(file_path,"Object"), link=False, filename=object_file_name)
        self._single_stage = bpy.data.objects[object_file_name]
        _new_obj_name = 'stage_' + object_file_name + str(1)
        self._single_stage.name = _new_obj_name
        ########################################################################### end of load/append object to scene #

        # setup stage cfg parameters
        if self._cfg['stageDisplacementActive']:

            # setup general disp properties ############################################################################
            _disp_modifier = self._add_displacement(bl_object=self._single_stage)
            _disp_modifier.mid_level = self._cfg['stageDisplacementMidLevel']
            _disp_modifier.strength = self._cfg['stageDisplacementStrength']
            bpy.ops.object.select_all(action = 'DESELECT')
            bpy.context.view_layer.objects.active = self._single_stage
            bpy.ops.object.modifier_move_to_index(modifier=_disp_modifier.name, index=0)
            ##################################################################### end of setup general disp properties #

            # add new noise texture ####################################################################################
            bpy.ops.texture.new()
            text = bpy.data.textures[len(bpy.data.textures)-1].name
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


    def create(self):
        self._create_single_stage(file_path=self._cfg["stageFilePath"],object_file_name=self._cfg["meshInstanceName"])


    def step(self):
        pass