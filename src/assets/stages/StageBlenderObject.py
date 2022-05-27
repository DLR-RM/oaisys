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
        
        # clean object #################################################################################################
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

        ########################################################################################## end of clean object #

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





'''
            print("par_system.name): ", par_system.name)
            print(self._single_stage.modifiers.get(par_system.name))
            print(par_system)
            #print(self._single_stage.modifiers.get(par_system))
            if self._single_stage.modifiers.get(par_system.name):
                self._single_stage.modifiers.remove(self._single_stage.modifiers.get(par_system.name))
            

            





        for mod in self._single_stage.modifiers:
            #print(mod.type)
            #print("mod1: ", mod)
            #print(mod.index)
            #for mod2 in self._single_stage.modifiers:
                #print("mod2: ", mod2)
            print(type(mod))
            if mod.type == "SUBSURF":#"PARTICLE_SYSTEM":
                print(mod.name)
                _t1.append(mod.name)
                #print()
                #print("remove me")
                #self._single_stage.modifiers.remove(mod)

        for t1 in _t1:
            print("remove")
            self._single_stage.modifiers.remove(self._single_stage.modifiers.get(t1))

        for par_system in self._single_stage.particle_systems:
            for mod in self._single_stage.modifiers:
                print("mod: ", mod)
                print("mod: ", mod.name)
                print("par_system.name: ", par_system.name)
                print("mod.type: ", mod.type)
                if mod.name == par_system.name:
                    print("remove me")
                    _t1.append(mod)
                    #self._single_stage.modifiers.remove(mod)            

        print(_t1)
        self._single_stageremove(remesh_mods[-1])
        for t in _t1:
            self._single_stage.modifiers.remove(t)

        for par_system in self._single_stage.particle_systems:
            print("ajsiklajfklsajfö: ", self._single_stage.modifiers.get(par_system.name))
            self._single_stage.modifiers.remove(self._single_stage.modifiers.get(par_system.name))
'''