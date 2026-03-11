# blender imports
import bpy

# utility imports
import random
import copy
import os
import json
import glob

from src.assets.TSSMaterial import TSSMaterial
from src.tools.utils import *

class BlenderNode():
    def __init__(self, cfg, mat_cfg_list):
        self.cfg = cfg
        self.mat_cfg_list = mat_cfg_list
        self.mat_cfg_files_list_selection = self.mat_cfg_list
        self.mat_cfg_list_selection = self.read_cfgs(cfg_paths=self.mat_cfg_files_list_selection)

        self.node_groups = []

    def read_cfgs(self, cfg_paths):
        cfg_list = []
        for cfg in cfg_paths:
            print(f"cfg: {cfg}")
            with open(cfg, 'r') as f:
                # load jso  n file
                cfg_list.append(json.load(f))
                f.close()
        return cfg_list

    def get_random_value(self, ideal=0, clip=[0,1], jitter_value=0):
        x = ideal + jitter_value*(random.random())-0.5

        x = clip[0] if x < clip[0] else x
        x = clip[1] if x > clip[1] else x

        return x

    def create_material_node_tree(self):
        print(f"CREATE NODE TREE")
        for mat_cfg in self.mat_cfg_list_selection:
            print(f"mat_cfg: {mat_cfg}")
            bpy.ops.wm.append(  directory=os.path.join(mat_cfg["blend_material_path"], "Material"),
                                link=False,
                                filename=mat_cfg["blend_material_name"])

            material = bpy.data.materials[mat_cfg["blend_material_name"]]
            _new_obj_name = f"OAISYS_{mat_cfg['blend_material_name']}"
            material.name = _new_obj_name

            _material_output = None
            for nn in material.node_tree.nodes.keys():
                if "Material Output" in nn:
                    _material_output = material.node_tree.nodes[nn]
                    break

            ## go through OAISYS driver
            if "oaisys_drivers" in mat_cfg:
                if "drivers" in mat_cfg["oaisys_drivers"]:
                    for driver_k, driver_v in mat_cfg["oaisys_drivers"]["drivers"].items():
                        # go through node tree and find node with key as name
                        for n_k, n_v in material.node_tree.nodes.items():
                            if f"OAISYS_{driver_k}" == n_k:
                                x = self.get_random_value(ideal=driver_v["ideal"],
                                                          clip=[driver_v["clip_min"], driver_v["clip_max"]],
                                                          jitter_value=driver_v["jitter_variance"]
                                                                       *mat_cfg["oaisys_drivers"]["jitter_strength"])

                                n_v.outputs[0].default_value = x


            self.node_groups.append(material)

            # return node tree
            return self.node_groups[0]

class MaterialBlenderNode(TSSMaterial):
    """docstring for MaterialBlenderNode"""

    def __init__(self):
        super(MaterialBlenderNode, self).__init__()
        # class vars ###################################################################################################
        self._material_list = []
        self._texture_dict = {}
        self._general_terrain_cfg = None
        self._terrain_cfg = None
        self._label_ID_node = None
        self._node_tree = None
        self._label_ID_Node_list = []
        self.material_cfg = None
        self.mat_cfg_list = None
        self.node_group_list = []
        ############################################################################################ end of class vars #

    def reset(self):
        """ reset function
        Args:
            None
        Returns:
            None
        """

        # class vars ###################################################################################################
        self._material_list = []
        self._texture_dict = {}
        self._general_terrain_cfg = None
        self._terrain_cfg = None
        self._label_ID_node = None
        self._node_tree = None
        self._label_ID_Node_list = []
        self.material_cfg = None
        self.mat_cfg_list = None
        self.node_group_list = []
        ############################################################################################ end of class vars #

    def setup_material_instance(self):
        node_group = BlenderNode(self.material_cfg,self.mat_cfg_list)
        self.node_group_list.append(node_group)
        return node_group.create_material_node_tree()

    def create(self):
        """ create function
        Args:
            None
        Returns:
            None
        """

        self._material = self
        self.material_cfg = self._cfg

        # search all json files in folder or use specific json file
        self.mat_cfg_list = [self.material_cfg["material_path"]] if os.path.isfile(self.material_cfg["material_path"])\
            else get_files_with_ext(self.material_cfg["material_path"], ext=".json")
