# blender imports
import bpy

# utility imports
import numpy as np
import csv
import random
import importlib

from src.TSSBase import TSSBase

class TSSMeshHandle(TSSBase):
    """docstring for TSSMeshHandle"""
    def __init__(self):
        super(TSSMeshHandle, self).__init__()
        # class vars ###################################################################################################
        self._mesh_list = []                                            # list of mesh [list]
        self._mesh_obj_list = []                                        # list of mesh nodes [list]
        ############################################################################################ end of class vars #


    def reset_module(self):
        """ reset all local vars
        Args:
            None
        Returns:
            None
        """

        # reset all mesh ############################################################################################
        for mesh in self._mesh_obj_list:
            # reset mesh
            mesh.reset_module()

            # maybe obsolete in future versions
            del mesh
        ##################################################################################### end of reset all mesh #

        self.reset_base()
        self._mesh_list = []
        self._mesh_obj_list = []


    def activate_pass(self,pass_name, pass_cfg, keyframe=-1):
        """ enables specific pass
        Args:
            pass_name:      name of pass to activate [string]
            pass_cfg:       specific parameters for the pass [dict]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        for mesh in self._mesh_obj_list:
            mesh.activate_pass(pass_name=pass_name,pass_cfg=pass_cfg,keyframe=keyframe)


    def create(self,stage_dict):
        """  create function
        Args:
            stage_dict:     dict of stages [dict]
        Returns:
            None
        """

        self._create_meshes(cfg=self._cfg["MESHES"],
                            general_cfg=self._cfg["GENERAL"],
                            stage_dict=stage_dict)


    def _create_meshes(self,cfg,general_cfg,stage_dict):
        """  create function
        Args:
            cfg:            list of mesh cfgs [list]
            general_cfg:    general cfg [dict]
            stage_dict:     dict of stages [dict]
        Returns:
            success code [boolean]
        """

        _current_instance_label_count = 0

        for ii, mesh in enumerate(cfg):
            try:
                # import module and create class #######################################################################
                _module_name = "src.assets.meshes." + mesh["type"]
                _module = importlib.import_module(_module_name)
                _class = getattr(_module, mesh["type"])
                _mesh = _class()
                ################################################################ end of import module and create class #

                # set pass params and create pass ######################################################################
                # set general cfg
                _mesh.set_general_cfg(cfg=general_cfg)

                _mesh.set_stage_dict(stage_dict=stage_dict)

                # save name of material
                mesh['meshParams']['name'] = mesh["name"]

                # update mesh cfg
                _mesh.update_cfg(cfg=mesh["meshParams"])

                # create material
                _instance_count, _instance_label_count = _mesh.create(instance_id_offset=_current_instance_label_count)

                _current_instance_label_count += _instance_label_count
                ############################################################### end of set pass params and create pass #
                
                # add pass to list
                self._mesh_obj_list.append(_mesh)
                self._mesh_list.append(_mesh.get_meshes())



            except ImportError:
                # manage import error
                raise Exception("Cannot add mesh")
                return -1


        return 0


    def get_meshes(self):
        """  get all meshes
        Args:
            None
        Returns:
            list of meshes [list]
        """

        return self._mesh_list


    def get_mesh_objs(self):
        """  get all mesh objects
        Args:
            None
        Returns:
            list of mesh objects [list]
        """

        return self._mesh_obj_list