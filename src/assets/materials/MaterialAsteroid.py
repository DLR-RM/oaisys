# blender imports
import bpy

# utility imports
import numpy as np
import csv
import random
import importlib
import copy
import os
import json
import copy as cp
from pathlib import Path

from src.assets.TSSMaterial import TSSMaterial


class MaterialAsteroid(TSSMaterial):
    """docstring for MaterialAsteroid"""

    def __init__(self):
        super(MaterialAsteroid, self).__init__()
        # class vars ###################################################################################################
        self._material_list = []
        self._texture_dict = {}
        self._num_labels_per_channel = 15
        self._general_terrain_cfg = None
        self._terrain_cfg = None
        self._label_ID_node = None
        self._node_tree = None
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
        self._num_labels_per_channel = 15
        self._general_terrain_cfg = None
        self._terrain_cfg = None
        self._label_ID_node = None
        self._node_tree = None
        ############################################################################################ end of class vars #

    def load_template_for_assets(self, cfg):
        _cfg = []

        # TODO: find more generic solution
        for terrain_sample in cfg:
            if "templatePath" in terrain_sample:

                # check if relative or absolute path is provided
                if not os.path.isabs(terrain_sample["templatePath"]):
                    # create abs path
                    _rel_path = terrain_sample["templatePath"]
                    _current_path = os.path.dirname(__file__)
                    terrain_sample["templatePath"] = os.path.join(_current_path, "../../../", _rel_path)

                with open(terrain_sample["templatePath"], 'r') as f:
                    _terrain_sample_tmp = json.load(f)
                    _terrain_sample_tmp.update(terrain_sample)
                    terrain_sample = _terrain_sample_tmp
                    del _terrain_sample_tmp["templatePath"]
                    _cfg.append(_terrain_sample_tmp)
            else:
                _cfg.append(terrain_sample)

        return _cfg

    def create(self):
        """ create function
        Args:
            None
        Returns:
            None
        """

        # print info msg
        self._print_msg("Create Asteroid Material")

        # get cfgs #####################################################################################################
        _general_terrain_cfg = self._cfg["general"]

        _terrain_cfg = {}

        if "terrainTextureList" in self._cfg and "terrainTextureList1" not in self._cfg:
            _terrain_cfg[1] = self._cfg["terrainTextureList"]
            _terrain_cfg[1] = self.load_template_for_assets(_terrain_cfg[1])
        else:
            if "terrainTextureList" in self._cfg:
                del self._cfg["terrainTextureList"]
            for k, v in self._cfg.items():
                if 'terrainTextureList' in k:
                    _trunc_k = cp.deepcopy(k)
                    _trunc_k = int(_trunc_k.replace('terrainTextureList', ""))
                    _terrain_cfg[_trunc_k] = v
                    _terrain_cfg[_trunc_k] = self.load_template_for_assets(_terrain_cfg[_trunc_k])
        ############################################################################################# end of  get cfgs #
        # _terrain_cfg = self.load_template_for_assets(_terrain_cfg)

        # create material
        _terrain_material = \
            self._create_mix_terrain_material(material_name=self._cfg["name"],
                                              general_terrain_cfg=_general_terrain_cfg,
                                              terrain_cfg=_terrain_cfg,
                                              num_min_mix_terrains=_general_terrain_cfg["minNumMixTerrains"],
                                              num_max_mix_terrains=_general_terrain_cfg["maxNumMixTerrains"],
                                              hard_label_borders=_general_terrain_cfg["hardLabelBorders"],
                                              noise_phase_shift_enabled=False,
                                              noise_phase_rate=1.0,
                                              with_replacement=_general_terrain_cfg["withReplacement"])

        # assign created material to material var
        self._material = _terrain_material

    def _create_mix_terrain_material(self, material_name, general_terrain_cfg, terrain_cfg,
                                     num_max_mix_terrains, num_min_mix_terrains, hard_label_borders,
                                     noise_phase_shift_enabled, noise_phase_rate, with_replacement=True):
        """ create mix terrain material.
        Args:
            material_name:                              name of the resulting mixed terrain material [string]
            general_terrain_cfg:                        general cfg for terrain [dict]
            terrain_cfg:                                specific cfg for each pure terrain texture [dict]
            num_max_mix_terrains:                       number of max pure textures, which are merged together. If set
                                                        to -1, all textures are used [int]
            num_min_mix_terrains:                       number of min pure textures, which are merged together [int]
            hard_label_borders:                         if true, hard borders are provided for semantic labels [boolean]
            noise_phase_shift_enabled:                  noise phase shift flag [boolean]
            noise_phase_rate:                           noise shift rate [float]
            with_replacement:                           sampling with replacmenet (true) or without (false) from the
                                                        terrain list [boolean]
        Returns:
            mixed terrain material [blObject]
        """

        # create random selection of terrains ##########################################################################
        # list of terrain, which will be used
        _channel_list = []

        # deepcopy terrain list to alter it
        # _terrain_cfg_copy = copy.deepcopy(terrain_cfg)

        _min_is_list = isinstance(num_min_mix_terrains, list)
        _max_is_list = isinstance(num_max_mix_terrains, list)

        if _min_is_list or _max_is_list:
            if _min_is_list:
                if _max_is_list:
                    # take list from both
                    if len(num_min_mix_terrains) != len(num_max_mix_terrains):
                        raise Exception('Length of minNumMixTerrains and maxNumMixTerrains has to match!')
                    _num_min_mix_terrains_list = num_min_mix_terrains
                    _num_max_mix_terrains_list = num_max_mix_terrains
                else:
                    # take list from min, convert max to list
                    _num_min_mix_terrains_list = num_min_mix_terrains
                    _num_max_mix_terrains_list = [num_max_mix_terrains] * len(num_min_mix_terrains)
            else:
                # take list from max, convert min to list
                _num_min_mix_terrains_list = [num_min_mix_terrains] * len(num_max_mix_terrains)
                _num_max_mix_terrains_list = num_max_mix_terrains

        else:
            # convert max and min to single list
            _num_min_mix_terrains_list = [num_min_mix_terrains]
            _num_max_mix_terrains_list = [num_max_mix_terrains]

        for s in range(0, len(_num_min_mix_terrains_list)):
            if s + 1 not in terrain_cfg:
                raise Exception('Cannot find set of terrain!')
            _terrain_cfg_copy = copy.deepcopy(terrain_cfg[s + 1])
            _min_num = _num_min_mix_terrains_list[s]
            _max_num = _num_max_mix_terrains_list[s]
            # check if all terrains are supposed to be used
            if _max_num >= 0:

                # sample terrains num_max_mix_terrains times
                if _max_num == 0:
                    _max_num = 1
                    self._print_msg("Warning: adjusted num_max_mix_terrains!")

                if _min_num <= 0:
                    _min_num = 1
                    self._print_msg("Warning: adjusted num_min_mix_terrains!")

                if _min_num > _max_num:
                    _min_num = _max_num
                    self._print_msg("Warning: adjusted num_min_mix_terrains!")

                if _min_num > len(_terrain_cfg_copy):
                    _min_num = len(_terrain_cfg_copy)
                    self._print_msg("Warning: adjusted num_min_mix_terrains!")

                if _max_num <= len(_terrain_cfg_copy):
                    _num_terrain_samples = random.randint(_min_num, _max_num)
                else:
                    _num_terrain_samples = random.randint(_min_num, len(_terrain_cfg_copy))
                    self._print_msg("Warning: adjusted num_max_mix_terrains!")

                for jj in range(0, _num_terrain_samples):

                    # pick random sample
                    item = random.choice(_terrain_cfg_copy)

                    # add sample to terrain list
                    _channel_list.append(item)

                    # remove item, depending on sampling method
                    if not with_replacement:
                        _terrain_cfg_copy.remove(item)

            else:
                # take entire terrain list
                _channel_list = _terrain_cfg_copy
        ################################################################### end of create random selection of terrains #

        # raise warning if _channel_list is empty
        if not _channel_list:
            self._print_msg("Warning: _channel_list is empty!")

        # create mixed terrain material and return result
        return self._create_materials(general_terrain_cfg, material_name, _channel_list, hard_label_borders, \
                                      noise_phase_shift_enabled, noise_phase_rate)

    def _create_mix_terrain_materialbak(self, material_name, general_terrain_cfg, terrain_cfg,
                                        num_max_mix_terrains, num_min_mix_terrains, hard_label_borders,
                                        noise_phase_shift_enabled, noise_phase_rate, with_replacement=True):
        """ create mix terrain material.
        Args:
            material_name:                              name of the resulting mixed terrain material [string]
            general_terrain_cfg:                        general cfg for terrain [dict]
            terrain_cfg:                                specific cfg for each pure terrain texture [dict]
            num_max_mix_terrains:                       number of max pure textures, which are merged together. If set
                                                        to -1, all textures are used [int]
            num_min_mix_terrains:                       number of min pure textures, which are merged together [int]
            hard_label_borders:                         if true, hard borders are provided for semantic labels [boolean]
            noise_phase_shift_enabled:                  noise phase shift flag [boolean]
            noise_phase_rate:                           noise shift rate [float]
            with_replacement:                           sampling with replacement (true) or without (false) from the
                                                        terrain list [boolean]
        Returns:
            mixed terrain material [blObject]
        """

        # create random selection of terrains ##########################################################################
        # list of terrain, which will be used
        _channel_list = []

        # deepcopy terrain list to alter it
        _terrain_cfg_copy = copy.deepcopy(terrain_cfg)

        # check if all terrains are supposed to be used
        if num_max_mix_terrains >= 0:

            # sample terrains num_max_mix_terrains times
            if num_max_mix_terrains == 0:
                num_max_mix_terrains = 1
                self._print_msg("Warning: adjusted num_max_mix_terrains!")

            if num_min_mix_terrains <= 0:
                num_min_mix_terrains = 1
                self._print_msg("Warning: adjusted num_min_mix_terrains!")

            if num_min_mix_terrains > num_max_mix_terrains:
                num_min_mix_terrains = num_max_mix_terrains
                self._print_msg("Warning: adjusted num_min_mix_terrains!")

            if num_min_mix_terrains > len(_terrain_cfg_copy):
                num_min_mix_terrains = len(_terrain_cfg_copy)
                self._print_msg("Warning: adjusted num_min_mix_terrains!")

            if num_max_mix_terrains <= len(_terrain_cfg_copy):
                _num_terrain_samples = random.randint(num_min_mix_terrains, num_max_mix_terrains)
            else:
                _num_terrain_samples = random.randint(num_min_mix_terrains, len(_terrain_cfg_copy))
                self._print_msg("Warning: adjusted num_max_mix_terrains!")

            for jj in range(0, _num_terrain_samples):

                # pick random sample
                item = random.choice(_terrain_cfg_copy)

                # add sample to terrain list
                _channel_list.append(item)

                # remove item, depending on sampling method
                if not with_replacement:
                    _terrain_cfg_copy.remove(item)

        else:
            # take entire terrain list
            _channel_list = _terrain_cfg_copy
        ################################################################### end of create random selection of terrains #

        # raise warning if _channel_list is empty
        if not _channel_list:
            self._print_msg("Warning: _channel_list is empty!")

        # create mixed terrain material and return result
        return self._create_materials(general_terrain_cfg, material_name, _channel_list, hard_label_borders, \
                                      noise_phase_shift_enabled, noise_phase_rate)


    def _get_map_path(self, base_path, prefix, return_complete_list=False):
        """ function to get path to texture files
        Args:
            base_path:                                  base path of textures [string]
            prefix:                                     keyword, which has to be part of filename [string]
            return_complete_list:                       return all found files with prefix or only the first one [bool]
        Returns:
            path to file [string]
        """

        # search for file with prefix in it
        _map_file = None
        _map_file = [filename for filename in os.listdir(base_path) if prefix in filename]

        # check if any file was found ##################################################################################
        if _map_file == []:
            # no file was found
            _map_file = None

        else:
            # compose abs path
            _map_file = [os.path.join(base_path, x) for x in _map_file] if return_complete_list else \
                    os.path.join(base_path, _map_file[0])
        ########################################################################## end of  check if any file was found #

        # return found file
        return _map_file

    def _create_materials(self, general_terrain_cfg, material_name, material_cfg_list, hard_label_borders,
                          noise_phase_shift_enabled=False, noise_phase_rate=0.0):

        """ create mix terrain material.
        Args:
            general_terrain_cfg:                        sfafsaf
            material_name:
            material_cfg_list:
            hard_label_borders:
            noise_phase_shift_enabled:
            noise_phase_rate:
        Returns:
            mixed terrain material [blObject]
        """

        # define and prepare basic vars ################################################################################
        # create new material
        _terrain_material = bpy.data.materials.new(name=material_name)

        # use nodes
        _terrain_material.use_nodes = True

        # house keeping
        _terrain_material.node_tree.nodes.remove(_terrain_material.node_tree.nodes.get("Principled BSDF"))

        # get all nodes
        nodes = _terrain_material.node_tree.nodes
        _terrain_material.cycles.displacement_method = 'BOTH'

        # init nodePosBase
        _node_offset = [0, 0]

        # current channel outputs
        _latest_PBSDF_output = None
        _latest_col_output = None
        _latest_spec_output = None
        _latest_rough_output = None
        _latest_nrm_output = None
        _latest_disp_output = None
        _latest_emission_output = None
        _latest_label_output = None

        # get material output node
        _material_output = bpy.data.materials[material_name].node_tree.nodes["Material Output"]
        _material_output.location = (_node_offset[0] + 4300, _node_offset[1])

        _noise_phase_shift_add_node = None
        __noise_mapping_node_ist = []
        _instance_switching_node_list = []
        ######################################################################### end of define and prepare basic vars #

        # create mixed terrain material ################################################################################
        for material_cfg in material_cfg_list:

            # define map paths #########################################################################################
            _col_map_path = None
            _gloss_map_path = None
            _rough_map_path = None
            _spec_map_path = None
            _refl_map_path = None
            _normal_map_path = None
            _emission_map_path = None
            _disp_map_path = None
            _disp_crater_map_path = None
            _latest_emission_path = None
            ################################################################################## end of define map paths #
            if "baseTexturePathOverwriteEnabled" in general_terrain_cfg:
                if general_terrain_cfg["baseTexturePathOverwriteEnabled"]:
                    if "noPathOverwrite" in material_cfg:
                        if not material_cfg["noPathOverwrite"]:
                            # overwrite base path of texture
                            material_cfg['basePath'] = general_terrain_cfg["baseTexturePath"]
                    else:
                        # overwrite base path of texture
                        material_cfg['basePath'] = general_terrain_cfg["baseTexturePath"]

            if not os.path.isabs(material_cfg['path']):
                # check if base path is provided
                if "basePath" in material_cfg:
                    material_cfg['path'] = os.path.join(material_cfg['basePath'], material_cfg['path'])
                else:
                    if "noPathOverwrite" in material_cfg:
                        if not material_cfg["noPathOverwrite"]:
                            if "baseTexturePath" in general_terrain_cfg:
                                material_cfg['basePath'] = general_terrain_cfg["baseTexturePath"]
                                material_cfg['path'] = os.path.join(material_cfg['basePath'], material_cfg['path'])
                    else:
                        if "baseTexturePath" in general_terrain_cfg:
                            material_cfg['basePath'] = general_terrain_cfg["baseTexturePath"]
                            material_cfg['path'] = os.path.join(material_cfg['basePath'], material_cfg['path'])

                # create abs path
                _current_path = os.path.dirname(__file__)
                material_cfg['path'] = os.path.join(_current_path, "../../../", material_cfg['path'])

            # get texture paths ########################################################################################
            # get color map ############################################################################################
            if (material_cfg['diffuse']):
                _col_map_path = self._get_map_path(material_cfg['path'], "COL")
                if _col_map_path is None:
                    _col_map_path = self._get_map_path(material_cfg['path'], "col")
                if _col_map_path is None:
                    _col_map_path = self._get_map_path(material_cfg['path'], "DIFF")
                if _col_map_path is None:
                    _col_map_path = self._get_map_path(material_cfg['path'], "diff")
                if _col_map_path is None:
                    self._print_msg("WARNING: diffuse texture in folder " + material_cfg['path'] + \
                                    " cannot be found! Using default color!")
            ##################################################################################### end of get color map #

            # get reflectance map ######################################################################################
            if (material_cfg['ref']):
                _gloss_map_path = self._get_map_path(material_cfg['path'], "GLOSS")
                if _gloss_map_path is None:
                    _gloss_map_path = self._get_map_path(material_cfg['path'], "gloss")

                if _gloss_map_path is None:
                    _rough_map_path = self._get_map_path(material_cfg['path'], "rough")
                if _rough_map_path is None:
                    _rough_map_path = self._get_map_path(material_cfg['path'], "rough")
                if _rough_map_path is None:
                    self._print_msg("WARNING: roughness texture in folder " + material_cfg['path'] + \
                                    " cannot be found! Using default color!")
            ############################################################################### end of get reflectance map #

            # get specular map #########################################################################################
            if (material_cfg['spec']):
                _refl_map_path = self._get_map_path(material_cfg['path'], "REFL")
                if _refl_map_path is None:
                    _refl_map_path = self._get_map_path(material_cfg['path'], "refl")

                if _refl_map_path is None:
                    _spec_map_path = self._get_map_path(material_cfg['path'], "spec")
                if _spec_map_path is None:
                    _spec_map_path = self._get_map_path(material_cfg['path'], "SPEC")
                if _spec_map_path is None:
                    self._print_msg("WARNING: specular texture in folder " + material_cfg['path'] + \
                                    " cannot be found! Using default color!")
            ################################################################################# end of  get specular map #

            # get normal map ###########################################################################################
            if (material_cfg['normal']):
                _normal_map_path = self._get_map_path(material_cfg['path'], "NRM")
                if _normal_map_path is None:
                    _normal_map_path = self._get_map_path(material_cfg['path'], "nrm")
                if _normal_map_path is None:
                    _normal_map_path = self._get_map_path(material_cfg['path'], "nor")
                if _normal_map_path is None:
                    self._print_msg("WARNING: normal texture in folder " + material_cfg['path'] + \
                                    " cannot be found! Using default color!")
            #################################################################################### end of get normal map #

            # get emission map #########################################################################################
            if 'emission' in material_cfg:
                if material_cfg['emission']:
                    _emission_map_path = self._get_map_path(material_cfg['path'], "EMISSIVE")
                    if _emission_map_path is None:
                        _emission_map_path = self._get_map_path(material_cfg['path'], "emissive")
                    if _emission_map_path is None:
                        self._print_msg("WARNING: emission texture in folder " + material_cfg['path'] + \
                                        " cannot be found! Using default color!")
            ################################################################################## end of get emission map #

            # get displacement map #####################################################################################
            if (material_cfg['displacement']):
                _disp_maps_path = []
                _k = ["DISP", "HEIGHT", "disp", "height"]
                for k in _k:
                    x = self._get_map_path(material_cfg['path'], k, True)
                    if isinstance(x,list):
                        if len(x)>0:
                            _disp_maps_path += x
                # split into crater disp and normal disp
                for d in _disp_maps_path:
                    if "craters_disp" in d:
                        _disp_crater_map_path = d
                    else:
                        _disp_map_path = d
                if _disp_map_path is None:
                    self._print_msg("WARNING: displacement texture in folder " + material_cfg['path'] + \
                                    " cannot be found! Using default color!")
                if _disp_crater_map_path is None:
                    self._print_msg("WARNING: displacement crator texture in folder " + material_cfg['path'] + \
                                    " cannot be found!")
            ############################################################################## end of get displacement map #
            ################################################################################# end of get texture paths #

            # get tiling parameter #####################################################################################
            if 'imageTileX' in material_cfg:
                imageTileX = material_cfg['imageTileX']
            else:
                imageTileX = 1.0

            if 'imageTileY' in material_cfg:
                imageTileY = material_cfg['imageTileY']
            else:
                imageTileY = 1.0

            if 'size' in material_cfg:
                imageSize = material_cfg['size']
            else:
                imageSize = 1.0

            if 'mosaicRotation' in material_cfg:
                mosaicRotation = material_cfg['mosaicRotation']
                mosaicNoise = material_cfg['mosaicNoise']
            else:
                mosaicRotation = 0.0
                mosaicNoise = 0.0
            ############################################################################## end of get tiling parameter #

            # create texture for each channel ##########################################################################
            # create DIFFUSE texture channel ###########################################################################
            # load image and create basic shader #######################################################################
            # check if image is already in use for other material
            _current_col_output = None
            if _col_map_path is not None:

                if _col_map_path in self._texture_dict:
                    # reuse image
                    _img = self._texture_dict[_col_map_path]
                else:
                    # load image
                    _img = bpy.data.images.load(_col_map_path)
                    self._texture_dict[_col_map_path] = _img

                # create image shader node
                _rgb_image = _terrain_material.node_tree.nodes.new('ShaderNodeTexImage')
                _rgb_image.location = (_node_offset[0] - 470, _node_offset[1] + 400)

                # use loaded image
                _rgb_image.image = _img

                # store current last col node
                _current_col_output = _rgb_image
                ################################################################ end of load image and create basic shader #

                # create color adjustemt if needed #########################################################################
                if "colorAdjustment" in material_cfg:
                    # create RGB curve node
                    _color_adjustment_curve = _terrain_material.node_tree.nodes.new('ShaderNodeRGBCurve')
                    _color_adjustment_curve.location = (_node_offset[0], _node_offset[1] + 400)

                    # read in and adjust color ramp ########################################################################
                    # brigthess adjustment
                    if "cColorPoints" in material_cfg["colorAdjustment"]:
                        for point_Idx, point in enumerate(material_cfg["colorAdjustment"]["cColorPoints"]):
                            _color_adjustment_curve.mapping.curves[3].points.new(point[0], point[1])

                    # red adjustment
                    if "rColorPoints" in material_cfg["colorAdjustment"]:
                        for point_Idx, point in enumerate(material_cfg["colorAdjustment"]["rColorPoints"]):
                            _color_adjustment_curve.mapping.curves[0].points.new(point[0], point[1])

                    # green adjustment
                    if "gColorPoints" in material_cfg["colorAdjustment"]:
                        for point_Idx, point in enumerate(material_cfg["colorAdjustment"]["gColorPoints"]):
                            _color_adjustment_curve.mapping.curves[1].points.new(point[0], point[1])

                    # blue adjustment
                    if "bColorPoints" in material_cfg["colorAdjustment"]:
                        for point_Idx, point in enumerate(material_cfg["colorAdjustment"]["bColorPoints"]):
                            _color_adjustment_curve.mapping.curves[2].points.new(point[0], point[1])
                    ################################################################# end of read in and adjust color ramp #

                    # update color curve
                    _color_adjustment_curve.mapping.update()

                    # link rgb image to curve
                    _terrain_material.node_tree.links.new(_color_adjustment_curve.inputs[1],
                                                          _current_col_output.outputs[0])

                    # change color output reference
                    _current_col_output = _color_adjustment_curve
                ################################################################## end of create color adjustemt if needed #

                # add color variations if needed ###########################################################################
                if "colorVariation" in material_cfg:
                    # create saturation node
                    _color_variation_node = _terrain_material.node_tree.nodes.new('ShaderNodeHueSaturation')
                    _color_variation_node.location = (_node_offset[0] + 400, _node_offset[1] + 200)

                    # read in and adjust ramp ##############################################################################
                    if "hue" in material_cfg["colorVariation"]:
                        _color_variation_node.inputs[0].default_value = material_cfg["colorVariation"]["hue"]

                    if "saturation" in material_cfg["colorVariation"]:
                        _color_variation_node.inputs[1].default_value = material_cfg["colorVariation"]["saturation"]

                    if "brithness" in material_cfg["colorVariation"]:
                        _color_variation_node.inputs[2].default_value = material_cfg["colorVariation"]["brithness"]
                    ####################################################################### end of read in and adjust ramp #

                    # create merging noise for color variation
                    _color_variation_noise_node = _terrain_material.node_tree.nodes.new("ShaderNodeTexNoise")
                    _color_variation_noise_node.location = (_node_offset[0] + 400, _node_offset[1] + 700)
                    _color_variation_noise_node.noise_dimensions = '2D'

                    # read in and adjust noise #############################################################################
                    if "mergingNoiseScale" in material_cfg["colorVariation"]:
                        _color_variation_noise_node.inputs[2].default_value = \
                            material_cfg["colorVariation"]["mergingNoiseScale"]

                    if "mergingNoiseDetail" in material_cfg["colorVariation"]:
                        _color_variation_noise_node.inputs[3].default_value = \
                            material_cfg["colorVariation"]["mergingNoiseDetail"]

                    if "mergingNoiseRoughness" in material_cfg["colorVariation"]:
                        _color_variation_noise_node.inputs[4].default_value = \
                            material_cfg["colorVariation"]["mergingNoiseRoughness"]

                    if "mergingNoiseDistorion" in material_cfg["colorVariation"]:
                        _color_variation_noise_node.inputs[5].default_value = \
                            material_cfg["colorVariation"]["mergingNoiseDistorion"]
                    ###################################################################### end of read in and adjust noise #

                    # create color ramp for variation ######################################################################
                    if material_cfg["colorVariation"]["mergingcolorRampActivated"]:
                        _merging_color_ramp_node = _terrain_material.node_tree.nodes.new("ShaderNodeValToRGB")
                        _merging_color_ramp_node.color_ramp.elements[0].color = \
                            (material_cfg["colorVariation"]["mergingColorStopColor_0"][0], \
                             material_cfg["colorVariation"]["mergingColorStopColor_0"][1], \
                             material_cfg["colorVariation"]["mergingColorStopColor_0"][2], \
                             material_cfg["colorVariation"]["mergingColorStopColor_0"][3])
                        _merging_color_ramp_node.color_ramp.elements[0].position = \
                            material_cfg["colorVariation"]["mergingColorStopPosition_0"]
                        _merging_color_ramp_node.color_ramp.elements[1].color = \
                            (material_cfg["colorVariation"]["mergingColorStopColor_1"][0], \
                             material_cfg["colorVariation"]["mergingColorStopColor_1"][1], \
                             material_cfg["colorVariation"]["mergingColorStopColor_1"][2], \
                             material_cfg["colorVariation"]["mergingColorStopColor_1"][3])
                        _merging_color_ramp_node.color_ramp.elements[1].position = \
                            material_cfg["colorVariation"]["mergingColorStopPosition_1"]
                        _merging_color_ramp_node.location = (_node_offset[0] + 800, _node_offset[1] + 700)

                    _color_variation_mix_node = _terrain_material.node_tree.nodes.new("ShaderNodeMixRGB")
                    _color_variation_mix_node.location = (_node_offset[0] + 1200, _node_offset[1] + 400)
                    if "mergingMode" in material_cfg["colorVariation"]:
                        _color_variation_mix_node.blend_type = material_cfg["colorVariation"]["mergingMode"]
                    ############################################################### end of create color ramp for variation #

                    # link it ##############################################################################################
                    _terrain_material.node_tree.links.new(_color_variation_node.inputs[4],
                                                          _current_col_output.outputs[0])
                    _terrain_material.node_tree.links.new(_color_variation_mix_node.inputs[1],
                                                          _current_col_output.outputs[0])
                    _terrain_material.node_tree.links.new(_color_variation_mix_node.inputs[2],
                                                          _color_variation_node.outputs[0])

                    if material_cfg["colorVariation"]["mergingcolorRampActivated"]:
                        _terrain_material.node_tree.links.new(_merging_color_ramp_node.inputs[0],
                                                              _color_variation_noise_node.outputs[0])
                        _terrain_material.node_tree.links.new(_color_variation_mix_node.inputs[0],
                                                              _merging_color_ramp_node.outputs[0])
                    else:
                        _terrain_material.node_tree.links.new(_color_variation_mix_node.inputs[0],
                                                              _color_variation_noise_node.outputs[0])
                    ####################################################################################### end of link it #

                    # update current last color output reference
                    _current_col_output = _color_variation_mix_node
                #################################################################### end of add color variations if needed #

            if not _current_col_output:
                # provide default rgb value
                _col_default = _terrain_material.node_tree.nodes.new('ShaderNodeRGB')
                _col_default.location = (_node_offset[0] - 470, _node_offset[1] + 400)
                _col_default.outputs[0].default_value[0] = 0.5
                _col_default.outputs[0].default_value[1] = 0.5
                _col_default.outputs[0].default_value[2] = 0.5
                _col_default.outputs[0].default_value[3] = 1.0

                _current_col_output = _col_default
            #################################################################### end of create DIFFUSE texture channel #

            # create ROUGHNESS texture channel #########################################################################
            _current_rough_output = None
            # use roughness or glossy map ##############################################################################
            if _rough_map_path is not None:
                # check if image is already in use for other material
                if _rough_map_path in self._texture_dict:
                    _img = self._texture_dict[_rough_map_path]
                else:
                    _img = bpy.data.images.load(_rough_map_path)
                    self._texture_dict[_rough_map_path] = _img

                # create image shader node #############################################################################
                _roughness_image = _terrain_material.node_tree.nodes.new('ShaderNodeTexImage')
                _roughness_image.image = _img
                _roughness_image.image.colorspace_settings.name = 'Non-Color'
                _roughness_image.location = (_node_offset[0] - 470, _node_offset[1] - 200)
                ###################################################################### end of create image shader node #

                # update current last roughness node
                _current_rough_output = _roughness_image

            else:
                # create GLOSSY texture shader
                # TODO rename ref_map to glossy_map
                # check if image is already in use for other material
                if _gloss_map_path is not None:
                    if _gloss_map_path in self._texture_dict:
                        _img = self._texture_dict[_gloss_map_path]
                    else:
                        _img = bpy.data.images.load(_gloss_map_path)
                        self._texture_dict[_gloss_map_path] = _img

                    # create image shader node #########################################################################
                    _glossy_image = _terrain_material.node_tree.nodes.new('ShaderNodeTexImage')
                    _glossy_image.image = _img
                    _glossy_image.image.colorspace_settings.name = 'Non-Color'
                    _glossy_image.location = (_node_offset[0] - 470, _node_offset[1] - 200)
                    ################################################################## end of create image shader node #

                    # create invert map
                    _invert_node = _terrain_material.node_tree.nodes.new('ShaderNodeInvert')
                    _invert_node.location = (_node_offset[0] - 200, _node_offset[1] - 200)

                    # link nodes
                    _terrain_material.node_tree.links.new(_invert_node.inputs[1], _glossy_image.outputs[0])

                    # update current last roughness node
                    _current_rough_output = _invert_node
                ################################################################### end of use roughness or glossy map #

            ################################################################## end of create ROUGHNESS texture channel #

            # create SPECULAR texture channel ##########################################################################
            _current_spec_output = None
            if not _current_rough_output:

                if _spec_map_path is not None:
                    if _spec_map_path in self._texture_dict:
                        _img = self._texture_dict[_spec_map_path]
                    else:
                        _img = bpy.data.images.load(_spec_map_path)
                        self._texture_dict[_spec_map_path] = _img

                    # create image shader node #########################################################################
                    _specular_image = _terrain_material.node_tree.nodes.new('ShaderNodeTexImage')
                    _specular_image.image = _img
                    _specular_image.image.colorspace_settings.name = 'Non-Color'
                    _specular_image.location = (_node_offset[0] - 470, _node_offset[1] + 100)
                    ################################################################## end of create image shader node #

                    # create invert map
                    _invert_node = _terrain_material.node_tree.nodes.new('ShaderNodeInvert')
                    _invert_node.location = (_node_offset[0] - 200, _node_offset[1] + 100)

                    # link nodes
                    _terrain_material.node_tree.links.new(_invert_node.inputs[1], _specular_image.outputs[0])

                    # update current last spec node
                    _current_spec_output = _invert_node
                else:
                    # TODO: add reflectance code here!
                    pass

            if not _current_rough_output and not _current_spec_output:
                # provide default rgb value
                _glossy_default = _terrain_material.node_tree.nodes.new('ShaderNodeRGB')
                _glossy_default.location = (_node_offset[0] - 470, _node_offset[1] - 200)
                _glossy_default.outputs[0].default_value[0] = 0.5
                _glossy_default.outputs[0].default_value[1] = 0.5
                _glossy_default.outputs[0].default_value[2] = 0.5
                _glossy_default.outputs[0].default_value[3] = 1.0

                _current_rough_output = _glossy_default
            ################################################################### end of create SPECULAR texture channel #

            # create NORMAL image texture channel ######################################################################
            _current_nrm_output = None
            if _normal_map_path is not None:
                # check if image is already in use for other material
                if _normal_map_path in self._texture_dict:
                    _img = self._texture_dict[_normal_map_path]
                else:
                    _img = bpy.data.images.load(_normal_map_path)
                    self._texture_dict[_normal_map_path] = _img

                # create image shader node #############################################################################
                _normal_image = _terrain_material.node_tree.nodes.new('ShaderNodeTexImage')
                _normal_image.image = _img
                _normal_image.image.colorspace_settings.name = 'Non-Color'
                _normal_image.location = (_node_offset[0] - 470, _node_offset[1] - 500)
                ###################################################################### end of create image shader node #

                # update current last normal node
                _current_nrm_output = _normal_image

            if not _current_nrm_output:
                # provide default rgb value
                _nrm_default = _terrain_material.node_tree.nodes.new('ShaderNodeRGB')
                _nrm_default.location = (_node_offset[0] - 470, _node_offset[1] - 500)
                _nrm_default.outputs[0].default_value[0] = 0.5
                _nrm_default.outputs[0].default_value[1] = 0.5
                _nrm_default.outputs[0].default_value[2] = 0.5
                _nrm_default.outputs[0].default_value[3] = 1.0

                _current_nrm_output = _nrm_default
            ############################################################## end of  create NORMAL image texture channel #

            # create EMISSION texture channel ##########################################################################
            _current_emission_output = None
            if _emission_map_path is not None:
                # check if image is already in use for other material
                if _emission_map_path in self._texture_dict:
                    _img = self._texture_dict[_emission_map_path]
                else:
                    _img = bpy.data.images.load(_emission_map_path)
                    self._texture_dict[_emission_map_path] = _img

                # create image shader node #############################################################################
                _emission_image = _terrain_material.node_tree.nodes.new('ShaderNodeTexImage')
                _emission_image.image = _img
                _emission_image.image.colorspace_settings.name = 'Non-Color'
                _emission_image.location = (_node_offset[0] - 470, _node_offset[1] - 500)
                ###################################################################### end of create image shader node #

                # update current last normal node
                _current_emission_output = _emission_image

            if not _current_emission_output:
                # provide default rgb value
                _emission_default = _terrain_material.node_tree.nodes.new('ShaderNodeRGB')
                _emission_default.location = (_node_offset[0] - 470, _node_offset[1] - 500)
                _emission_default.outputs[0].default_value[0] = 0.0
                _emission_default.outputs[0].default_value[1] = 0.0
                _emission_default.outputs[0].default_value[2] = 0.0
                _emission_default.outputs[0].default_value[3] = 1.0

                _current_emission_output = _emission_default
            ################################################################### end of create EMISSION texture channel #

            # create DISPLACEMENT image texture channel ################################################################
            _current_disp_output = None
            if _disp_map_path is not None:
                # check if image is already in use for other material
                if _disp_map_path in self._texture_dict:
                    _img = self._texture_dict[_disp_map_path]
                else:
                    _img = bpy.data.images.load(_disp_map_path)
                    self._texture_dict[_disp_map_path] = _img

                # create image shader node #############################################################################
                _disp_image = _terrain_material.node_tree.nodes.new('ShaderNodeTexImage')
                _disp_image.image = _img
                _disp_image.image.colorspace_settings.name = 'Non-Color'
                _disp_image.location = (_node_offset[0], _node_offset[1] - 700)
                ###################################################################### end of create image shader node #

                # add color ramp node ##################################################################################
                dispColorRampNode = _terrain_material.node_tree.nodes.new("ShaderNodeMath")
                dispColorRampNode.operation = 'MULTIPLY'
                dispColorRampNode.inputs[1].default_value = random.uniform(material_cfg["dispmapStrength"][0][0],
                                                                           material_cfg["dispmapStrength"][0][1])

                # link it
                _terrain_material.node_tree.links.new(dispColorRampNode.inputs[0], _disp_image.outputs[0])

                # update current last disp node

            if _disp_crater_map_path is not None:
                ### add additional displacement
                disp_map = bpy.data.images.load(_disp_crater_map_path)
                add_disp_image = _terrain_material.node_tree.nodes.new('ShaderNodeTexImage')
                add_disp_image.image = disp_map
                add_disp_image.image.colorspace_settings.name = 'Non-Color'
                add_disp_image.location = (_node_offset[0], _node_offset[1] - 600)

                mul_node = _terrain_material.node_tree.nodes.new("ShaderNodeMath")
                mul_node.operation = 'MULTIPLY'
                mul_node.inputs[1].default_value = random.uniform(  material_cfg["dispmapStrength"][1][0],
                                                                    material_cfg["dispmapStrength"][1][1])
                mul_node.location = (_node_offset[0] + 100, _node_offset[1] + 600)
                _terrain_material.node_tree.links.new(mul_node.inputs[0], add_disp_image.outputs[0])

                add_node = _terrain_material.node_tree.nodes.new("ShaderNodeMath")
                add_node.operation = 'MULTIPLY'
                add_node.location = (_node_offset[0] + 200, _node_offset[1] + 600)
                _terrain_material.node_tree.links.new(add_node.inputs[0], mul_node.outputs[0])
                _terrain_material.node_tree.links.new(add_node.inputs[1], dispColorRampNode.outputs[0])

                _current_disp_output = add_node

            if not _current_disp_output:
                # provide default rgb value
                _disp_default = _terrain_material.node_tree.nodes.new('ShaderNodeRGB')
                _disp_default.location = (_node_offset[0], _node_offset[1] - 700)
                _disp_default.outputs[0].default_value[0] = 0.5
                _disp_default.outputs[0].default_value[1] = 0.5
                _disp_default.outputs[0].default_value[2] = 0.5
                _disp_default.outputs[0].default_value[3] = 1.0

                _current_disp_output = _disp_default
            #########################################
            ################################################################### end of create texture for each channel #

            # create mapping nodes for tiling textures #################################################################
            _tiling_mode_set = False

            if 'tilingMode' in material_cfg:
                if "VORONOI_STYLE" == material_cfg['tilingMode']:
                    _tiling_mode_set = True
                    _scale_to_tile_val = self._retrieve_parameter(cfg=material_cfg, key='scaleFileFac')
                    _y_x_scale_ratio = self._retrieve_parameter(cfg=material_cfg, key='scaleYXRatio')
                    if not _y_x_scale_ratio:
                        _y_x_scale_ratio = 1.0
                    if not _scale_to_tile_val:
                        _tiling_node_tree = self._create_voronoli_style_tiling_nodes(scale_to_tile_val= \
                                                                                         _scale_to_tile_val,
                                                                                     y_x_scale_ratio= \
                                                                                         _y_x_scale_ratio)
                    else:
                        _tiling_node_tree = self._create_voronoli_style_tiling_nodes(y_x_scale_ratio=_y_x_scale_ratio)
                    _node_group = _terrain_material.node_tree.nodes.new("ShaderNodeGroup")
                    _node_group.node_tree = _tiling_node_tree
                    _node_group.inputs[0].default_value = material_cfg['size']
                    _node_group.location = (_node_offset[0] - 700, _node_offset[1])

                    if _col_map_path is not None:
                        _tmp_list = []
                        for node_links in _rgb_image.outputs[0].links:
                            _tmp_list.append(node_links)
                        _rgb_image_mix = self._create_voronoli_style_merging(node_tree=_terrain_material,
                                                                             tiling_node=_node_group,
                                                                             texture_node=_rgb_image)
                        for node in _tmp_list:
                            _terrain_material.node_tree.links.new(node.to_node.inputs[node.to_socket.identifier],
                                                                  _rgb_image_mix.outputs[0])
                        if not _tmp_list:
                            _current_col_output = _rgb_image_mix

                    if _spec_map_path is not None:
                        _tmp_list = []
                        for node_links in _specular_image.outputs[0].links:
                            _tmp_list.append(node_links)
                        _specular_image_mix = self._create_voronoli_style_merging(node_tree=_terrain_material,
                                                                                  tiling_node=_node_group,
                                                                                  texture_node=_specular_image)
                        for node in _tmp_list:
                            _terrain_material.node_tree.links.new(node.to_node.inputs[node.to_socket.identifier],
                                                                  _specular_image_mix.outputs[0])
                        if not _tmp_list:
                            _current_spec_output = _specular_image_mix

                    if _gloss_map_path is not None:
                        _tmp_list = []
                        for node_links in _glossy_image.outputs[0].links:
                            _tmp_list.append(node_links)
                        _glossy_image_mix = self._create_voronoli_style_merging(node_tree=_terrain_material,
                                                                                tiling_node=_node_group,
                                                                                texture_node=_glossy_image)
                        for node in _tmp_list:
                            _terrain_material.node_tree.links.new(node.to_node.inputs[node.to_socket.identifier],
                                                                  _glossy_image_mix.outputs[0])
                        if not _tmp_list:
                            _current_spec_output = _glossy_image_mix

                    if _rough_map_path is not None:
                        _tmp_list = []
                        for node_links in _roughness_image.outputs[0].links:
                            _tmp_list.append(node_links)
                        _roughness_image_mix = self._create_voronoli_style_merging(node_tree=_terrain_material,
                                                                                   tiling_node=_node_group,
                                                                                   texture_node=_roughness_image)
                        for node in _tmp_list:
                            _terrain_material.node_tree.links.new(node.to_node.inputs[node.to_socket.identifier],
                                                                  _roughness_image_mix.outputs[0])
                        if not _tmp_list:
                            _current_rough_output = _roughness_image_mix

                    if _normal_map_path is not None:
                        _tmp_list = []
                        for node_links in _normal_image.outputs[0].links:
                            _tmp_list.append(node_links)
                        _nrm_image_mix = self._create_voronoli_style_merging(node_tree=_terrain_material,
                                                                             tiling_node=_node_group,
                                                                             texture_node=_normal_image)
                        for node in _tmp_list:
                            _terrain_material.node_tree.links.new(node.to_node.inputs[node.to_socket.identifier],
                                                                  _nrm_image_mix.outputs[0])
                        if not _tmp_list:
                            _current_nrm_output = _nrm_image_mix

                    if _emission_map_path is not None:
                        _tmp_list = []
                        for node_links in _emission_image.outputs[0].links:
                            _tmp_list.append(node_links)
                        _emission_image_mix = self._create_voronoli_style_merging(node_tree=_terrain_material,
                                                                                  tiling_node=_node_group,
                                                                                  texture_node=_emission_image)
                        for node in _tmp_list:
                            _terrain_material.node_tree.links.new(node.to_node.inputs[node.to_socket.identifier],
                                                                  _emission_image_mix.outputs[0])
                        if not _tmp_list:
                            _current_emission_output = _emission_image_mix

                    if _disp_map_path is not None:
                        _tmp_list = []
                        for node_links in _disp_image.outputs[0].links:
                            _tmp_list.append(node_links)
                        _disp_image_mix = self._create_voronoli_style_merging(node_tree=_terrain_material,
                                                                              tiling_node=_node_group,
                                                                              texture_node=_disp_image)
                        for node in _tmp_list:
                            _terrain_material.node_tree.links.new(node.to_node.inputs[node.to_socket.identifier],
                                                                  _disp_image_mix.outputs[0])
                        if not _tmp_list:
                            _current_disp_output = _disp_image_mix

            if not _tiling_mode_set:
                # TODO change!
                mat_config = self.load_nodegroup_config("uber_mapping")
                node_group = self.create_nodegroup_from_config(mat_config)

                _mapping_node = _terrain_material.node_tree.nodes.new(type='ShaderNodeGroup')
                _mapping_group = node_group

                # custom_mapping
                _mapping_node.node_tree = _mapping_group
                _mapping_node.name = _mapping_group.name
                _mapping_node.location = (_node_offset[0] - 700, _node_offset[1])

                _mapping_node.inputs[1].default_value = imageSize
                _mapping_node.inputs[6].default_value = mosaicRotation
                _mapping_node.inputs[7].default_value = mosaicNoise

                _tex_coord_node = _terrain_material.node_tree.nodes.new('ShaderNodeTexCoord')
                _tex_coord_node.location = (_node_offset[0] - 900, _node_offset[1])

                _terrain_material.node_tree.links.new(_mapping_node.inputs[0], _tex_coord_node.outputs[2])

                if _col_map_path is not None:
                    _terrain_material.node_tree.links.new(_rgb_image.inputs[0], _mapping_node.outputs[0])
                if _spec_map_path is not None:
                    _terrain_material.node_tree.links.new(_specular_image.inputs[0], _mapping_node.outputs[0])
                if _gloss_map_path is not None:
                    _terrain_material.node_tree.links.new(_glossy_image.inputs[0], _mapping_node.outputs[0])
                if _rough_map_path is not None:
                    _terrain_material.node_tree.links.new(_roughness_image.inputs[0], _mapping_node.outputs[0])
                if _normal_map_path is not None:
                    _terrain_material.node_tree.links.new(_normal_image.inputs[0], _mapping_node.outputs[0])
                if _emission_map_path is not None:
                    _terrain_material.node_tree.links.new(_emission_image.inputs[0], _mapping_node.outputs[0])
                if _disp_map_path is not None:
                    _terrain_material.node_tree.links.new(_disp_image.inputs[0], _mapping_node.outputs[0])
            ########################################################## end of create mapping nodes for tiling textures #

            # setup semantic nodes #####################################################################################
            _label_node = None
            if 'tilingMode' in material_cfg:
                if "VORONOI_STYLE" == material_cfg['tilingMode']:
                    _label_node, self._label_ID_node = self.create_semantic_nodes( \
                        node_tree=_terrain_material,
                        num_label_per_channel=self._num_labels_per_channel,
                        label_ID_vec=material_cfg['passParams'] \
                            ['semantic_label']['labelIDVec'][0],
                        uv_map=None,
                        node_offset=[_node_offset[0] - 500, _node_offset[1] - 1700])

            if not _label_node:
                _label_node, self._label_ID_node = self.create_semantic_nodes( \
                    node_tree=_terrain_material,
                    num_label_per_channel=self._num_labels_per_channel,
                    label_ID_vec=material_cfg['passParams'] \
                        ['semantic_label']['labelIDVec'][0],
                    uv_map=_mapping_node.outputs[0],
                    node_offset=[_node_offset[0] - 500, _node_offset[1] - 1700])

            # set default value
            _label_node.inputs[0].default_value = 1
            ############################################################################## end of setup semantic nodes #

            # setup instance nodes #####################################################################################
            # define default label ID vector
            # TODO: this parameter should be able to be overwitten
            _label_ID_vec = [0]

            # create switching nodes for semantics
            _instance_switching_node = self.create_single_semantic_node( \
                node_tree=_terrain_material,
                label_ID=_label_ID_vec[0],
                num_label_per_channel=15,
                node_offset=[_node_offset[0], _node_offset[1] - 2000])

            # link switching nodes with tree
            _terrain_material.node_tree.links.new(_instance_switching_node.inputs[1], _label_node.outputs[0])

            # update _instance_switching_node_list list
            _instance_switching_node_list.append(_instance_switching_node)

            # update current last output
            _label_node = _instance_switching_node
            ############################################################################## end of setup instance nodes #

            # mix current with last texture ############################################################################
            if _latest_col_output == None:
                # if no last texture is set, set current to last texture
                _latest_col_output = _current_col_output
                _latest_rough_output = _current_rough_output
                _latest_spec_output = _current_spec_output
                _latest_nrm_output = _current_nrm_output
                _latest_emission_output = _current_emission_output
                _latest_disp_output = _current_disp_output
                _latest_label_output = _label_node
            else:
                # create noise shader to mix terrains ##################################################################
                # add new noise shader
                _noise_tex_coord_node = _terrain_material.node_tree.nodes.new("ShaderNodeTexCoord")
                _noise_tex_coord_node.location = (_node_offset[0] + 600, _node_offset[1] - 100)
                _noise_mapping_node = _terrain_material.node_tree.nodes.new("ShaderNodeMapping")
                _noise_mapping_node.location = (_node_offset[0] + 1400, _node_offset[1] - 100)
                _noise_tex_node = _terrain_material.node_tree.nodes.new("ShaderNodeTexNoise")
                _noise_tex_node.location = (_node_offset[0] + 1800, _node_offset[1] - 100)
                _noise_color_ramp_node = _terrain_material.node_tree.nodes.new("ShaderNodeValToRGB")
                _noise_color_ramp_node.location = (_node_offset[0] + 2200, _node_offset[1] - 100)
                if hard_label_borders:
                    _noise_color_label_ramp_node = _terrain_material.node_tree.nodes.new("ShaderNodeValToRGB")
                    _noise_color_label_ramp_node.location = (_node_offset[0] + 2200, _node_offset[1] + 200)
                    _noise_color_label_ramp_node.color_ramp.interpolation = 'CONSTANT'

                # fill in noise values #################################################################################
                _noise_tex_node.inputs[2].default_value = \
                    random.uniform(general_terrain_cfg['mergingNoise']['Scale'][0], \
                                   general_terrain_cfg['mergingNoise']['Scale'][-1])
                _noise_tex_node.inputs[3].default_value = \
                    random.uniform(general_terrain_cfg['mergingNoise']['Detail'][0], \
                                   general_terrain_cfg['mergingNoise']['Detail'][-1])
                _noise_tex_node.inputs[4].default_value = \
                    random.uniform(general_terrain_cfg['mergingNoise']['Roughness'][0], \
                                   general_terrain_cfg['mergingNoise']['Roughness'][-1])
                _noise_tex_node.inputs[5].default_value = \
                    random.uniform(general_terrain_cfg['mergingNoise']['Distortion'][0], \
                                   general_terrain_cfg['mergingNoise']['Distortion'][-1])
                ########################################################################## end of fill in noise values #

                # even split of rgb textures
                _noise_color_ramp_node.color_ramp.elements[0].position = 0.48
                _noise_color_ramp_node.color_ramp.elements[1].position = 0.52

                # calculate split of label noise split
                if hard_label_borders:
                    middleSlot = 0.5 * (_noise_color_ramp_node.color_ramp.elements[1].position + \
                                        _noise_color_ramp_node.color_ramp.elements[0].position)
                    _noise_color_label_ramp_node.color_ramp.elements[0].position = middleSlot
                    _noise_color_label_ramp_node.color_ramp.elements[1].position = middleSlot + 0.00001

                # TODO: improve radnom sampling
                _noise_mapping_node.inputs[2].default_value[0] = random.random()
                _noise_mapping_node.inputs[2].default_value[1] = random.random()
                _noise_mapping_node.inputs[2].default_value[2] = random.random()
                ##################################################

                __noise_mapping_node_ist.append(_noise_mapping_node)

                # link noise nodes #####################################################################################
                _terrain_material.node_tree.links.new(_noise_mapping_node.inputs[0], _noise_tex_coord_node.outputs[0])
                # _terrain_material.node_tree.links.new(_noise_mapping_node.inputs[0], _noise_tex_coord_node.outputs[2])
                _terrain_material.node_tree.links.new(_noise_tex_node.inputs[0], _noise_mapping_node.outputs[0])
                _terrain_material.node_tree.links.new(_noise_color_ramp_node.inputs[0], _noise_tex_node.outputs[0])
                if hard_label_borders:
                    _terrain_material.node_tree.links.new(_noise_color_label_ramp_node.inputs[0], \
                                                          _noise_tex_node.outputs[0])
                ############################################################################## end of link noise nodes #
                ########################################################### end of create noise shader to mix terrains #

                ## COLOR MIX ####################################################################################
                # add new mix shaders
                mixShaderNode = _terrain_material.node_tree.nodes.new("ShaderNodeMixRGB")
                mixShaderNode.location = (_node_offset[0] + 3500, _node_offset[1] + 200)

                # combine shaders
                _terrain_material.node_tree.links.new(mixShaderNode.inputs[0], _noise_color_ramp_node.outputs[0])
                _terrain_material.node_tree.links.new(mixShaderNode.inputs[1], _latest_col_output.outputs[0])
                _terrain_material.node_tree.links.new(mixShaderNode.inputs[2], _current_col_output.outputs[0])

                # set new output
                _latest_col_output = mixShaderNode
                ####################################################################################

                ## SPEC MIX ####################################################################################
                # add new mix shaders
                if _latest_spec_output is None:
                    _latest_spec_output = _current_spec_output
                else:
                    mixShaderNode = _terrain_material.node_tree.nodes.new("ShaderNodeMixRGB")
                    mixShaderNode.location = (_node_offset[0] + 3500, _node_offset[1] + 500)

                    # combine shaders
                    _terrain_material.node_tree.links.new(mixShaderNode.inputs[0], _noise_color_ramp_node.outputs[0])
                    _terrain_material.node_tree.links.new(mixShaderNode.inputs[1], _latest_spec_output.outputs[0])
                    _terrain_material.node_tree.links.new(mixShaderNode.inputs[2], _current_spec_output.outputs[0])

                    # set new output
                    _latest_spec_output = mixShaderNode
                ####################################################################################

                ## ROUGHNESS MIX ####################################################################################
                # add new mix shaders
                if _latest_rough_output is None:
                    _latest_rough_output = _current_rough_output
                else:
                    mixShaderNode = _terrain_material.node_tree.nodes.new("ShaderNodeMixRGB")
                    mixShaderNode.location = (_node_offset[0] + 3500, _node_offset[1] + 800)

                    # combine shaders
                    _terrain_material.node_tree.links.new(mixShaderNode.inputs[0], _noise_color_ramp_node.outputs[0])
                    _terrain_material.node_tree.links.new(mixShaderNode.inputs[1], _latest_rough_output.outputs[0])
                    _terrain_material.node_tree.links.new(mixShaderNode.inputs[2], _current_rough_output.outputs[0])

                    # set new output
                    _latest_rough_output = mixShaderNode
                ####################################################################################

                ## NRM MIX ####################################################################################
                # add new mix shaders
                if _latest_nrm_output is None:
                    _latest_nrm_output = _current_nrm_output
                else:
                    mixShaderNode = _terrain_material.node_tree.nodes.new("ShaderNodeMixRGB")
                    mixShaderNode.location = (_node_offset[0] + 3500, _node_offset[1] + 1100)

                    # combine shaders
                    _terrain_material.node_tree.links.new(mixShaderNode.inputs[0], _noise_color_ramp_node.outputs[0])
                    _terrain_material.node_tree.links.new(mixShaderNode.inputs[1], _latest_nrm_output.outputs[0])
                    _terrain_material.node_tree.links.new(mixShaderNode.inputs[2], _current_nrm_output.outputs[0])

                    # set new output
                    _latest_nrm_output = mixShaderNode
                ####################################################################################

                ## EMISSION MIX ####################################################################################
                # add new mix shaders
                if _latest_emission_output is None:
                    _latest_emission_output = _current_rough_output
                else:
                    mixShaderNode = _terrain_material.node_tree.nodes.new("ShaderNodeMixRGB")
                    mixShaderNode.location = (_node_offset[0] + 3500, _node_offset[1] + 800)

                    # combine shaders
                    _terrain_material.node_tree.links.new(mixShaderNode.inputs[0], _noise_color_ramp_node.outputs[0])
                    _terrain_material.node_tree.links.new(mixShaderNode.inputs[1], _latest_emission_output.outputs[0])
                    _terrain_material.node_tree.links.new(mixShaderNode.inputs[2], _current_emission_output.outputs[0])

                    # set new output
                    _latest_emission_output = mixShaderNode
                ####################################################################################

                ## LABEL MIX ####################################################################################
                # add new mix shaders
                mixShaderNode = _terrain_material.node_tree.nodes.new("ShaderNodeMixRGB")
                mixShaderNode.location = (_node_offset[0] + 2500, _node_offset[1] + 300)

                # combine shaders
                if hard_label_borders:
                    _terrain_material.node_tree.links.new(mixShaderNode.inputs[0],
                                                          _noise_color_label_ramp_node.outputs[0])
                else:
                    _terrain_material.node_tree.links.new(mixShaderNode.inputs[0], _noise_color_ramp_node.outputs[0])
                _terrain_material.node_tree.links.new(mixShaderNode.inputs[1], _latest_label_output.outputs[0])
                _terrain_material.node_tree.links.new(mixShaderNode.inputs[2], _label_node.outputs[0])

                # set new output
                _latest_label_output = mixShaderNode
                ####################################################################################

                # DISPLACEMENT MIX ####################################################################################
                if _latest_disp_output is None:
                    _latest_disp_output = _current_disp_output
                else:
                    mixDISPShaderNode = _terrain_material.node_tree.nodes.new("ShaderNodeMixRGB")
                    mixDISPShaderNode.location = (_node_offset[0] + 2800, _node_offset[1] + 300)

                    # combine shaders
                    _terrain_material.node_tree.links.new(mixDISPShaderNode.inputs[0],
                                                          _noise_color_ramp_node.outputs[0])
                    _terrain_material.node_tree.links.new(mixDISPShaderNode.inputs[1], _latest_disp_output.outputs[0])
                    _terrain_material.node_tree.links.new(mixDISPShaderNode.inputs[2], _current_disp_output.outputs[0])

                    # set new output
                    _latest_disp_output = mixDISPShaderNode
                ####################################################################################

            # adapt base position
            _node_offset[1] = _node_offset[1] - 3000
            ##################################################################### end of mix current with last texture #
        ######################################################################### end of create mixed terrain material #

        # TODO: the z component of the mapping node does not allow values creater than 20000!!!!! Better change to 4D mapping!
        if (noise_phase_shift_enabled):
            # create phase shift driver nodes
            noisePhaseShiftOffset = _terrain_material.node_tree.nodes.new("ShaderNodeValue")
            noisePhaseShiftOffset.location = (_node_offset[0] + 700, _node_offset[1] - 300)
            noisePhaseShiftOffset.outputs[0].default_value = random.random()
            noisePhaseShiftRate = _terrain_material.node_tree.nodes.new("ShaderNodeValue")
            noisePhaseShiftRate.location = (_node_offset[0] + 700, _node_offset[1] - 500)
            noisePhaseShiftRate.outputs[0].default_value = noise_phase_rate
            noisePhaseShiftFrame = _terrain_material.node_tree.nodes.new("ShaderNodeValue")
            noisePhaseShiftFrame.name = "frameID"
            noisePhaseShiftFrame.location = (_node_offset[0] + 700, _node_offset[1] - 700)
            noisePhaseShiftFrame.outputs[0].default_value = 0

            # add logic ##########################################
            noisePhaseShiftMultipleNode = _terrain_material.node_tree.nodes.new("ShaderNodeMath")
            noisePhaseShiftMultipleNode.operation = 'MULTIPLY'
            noisePhaseShiftMultipleNode.location = (_node_offset[0] + 900, _node_offset[1] - 600)
            _terrain_material.node_tree.links.new(noisePhaseShiftMultipleNode.inputs[0], noisePhaseShiftRate.outputs[0])
            _terrain_material.node_tree.links.new(noisePhaseShiftMultipleNode.inputs[1],
                                                  noisePhaseShiftFrame.outputs[0])

            _noise_phase_shift_add_node = _terrain_material.node_tree.nodes.new("ShaderNodeMath")
            _noise_phase_shift_add_node.operation = 'ADD'
            _noise_phase_shift_add_node.location = (_node_offset[0] + 1100, _node_offset[1] - 400)
            _terrain_material.node_tree.links.new(_noise_phase_shift_add_node.inputs[0],
                                                  noisePhaseShiftOffset.outputs[0])
            _terrain_material.node_tree.links.new(_noise_phase_shift_add_node.inputs[1],
                                                  noisePhaseShiftMultipleNode.outputs[0])
            ##########################################

            # convert to vector ##############################################
            noisePhaseShiftVector = _terrain_material.node_tree.nodes.new("ShaderNodeCombineXYZ")
            noisePhaseShiftVector.location = (_node_offset[0] + 1200, _node_offset[1] - 600)
            noisePhaseShiftVector.inputs[0].default_value = 1
            noisePhaseShiftVector.inputs[1].default_value = 1
            _terrain_material.node_tree.links.new(noisePhaseShiftVector.inputs[2],
                                                  _noise_phase_shift_add_node.outputs[0])
            ####################################

            for _mapping_node in __noise_mapping_node_ist:
                # connect to noise mapping node
                _terrain_material.node_tree.links.new(_mapping_node.inputs[3], noisePhaseShiftVector.outputs[0])

        # creat diffuse shader for labels: IMPORANT, it has to be piped thorugh a shader, otherwise no information is getting trough the diffuse render channel!
        labelDiffuseNode = _terrain_material.node_tree.nodes.new("ShaderNodeBsdfDiffuse")
        # labelDiffuseNode = _terrain_material.node_tree.nodes.new("ShaderNodeBsdfDiffuse")
        labelDiffuseNode.location = (_node_offset[0] + 3700, 0)
        # labelDiffuseNode.inputs[1].default_value = 1.0  # set roughness to 1. no glossy!
        _terrain_material.node_tree.links.new(labelDiffuseNode.inputs[0], _latest_label_output.outputs[0])

        # create Pinciple Shade node and link it #############################################
        PBSDFNode = _terrain_material.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        PBSDFNode.location = (_node_offset[0] + 200, _node_offset[1])

        _terrain_material.node_tree.links.new(PBSDFNode.inputs[0], _latest_col_output.outputs[0])
        if _latest_spec_output is not None:
            _terrain_material.node_tree.links.new(PBSDFNode.inputs[5], _latest_spec_output.outputs[0])
        if _latest_rough_output is not None:
            _terrain_material.node_tree.links.new(PBSDFNode.inputs[7], _latest_rough_output.outputs[0])
        if _latest_nrm_output is not None:
            # add normal map
            normalMapNode = _terrain_material.node_tree.nodes.new('ShaderNodeNormalMap')
            normalMapNode.inputs[0].default_value = general_terrain_cfg['normalStrength']
            normalMapNode.location = (_node_offset[0], _node_offset[1])
            # link nodes
            _terrain_material.node_tree.links.new(normalMapNode.inputs[1], _latest_nrm_output.outputs[0])
            # _terrain_material.node_tree.links.new(PBSDFNode.inputs[19], normalMapNode.outputs[0])

            _terrain_material.node_tree.links.new(PBSDFNode.inputs[20], normalMapNode.outputs[0])
        ######################################################################################

        # link material output to last node ##################
        # add new mix shaders
        masterMixShaderNode = _terrain_material.node_tree.nodes.new("ShaderNodeMixShader")
        masterMixShaderNode.name = "rgb-label-mix"
        masterMixShaderNode.label = "rgb-label-mix"
        masterMixShaderNode.location = (_node_offset[0] + 4000, 0)
        masterMixShaderNode.inputs[
            0].default_value = 0  # set actual terrain material as default; 1 for gettnig its label
        ##################
        _terrain_material.node_tree.links.new(masterMixShaderNode.inputs[1], PBSDFNode.outputs[0])
        _terrain_material.node_tree.links.new(masterMixShaderNode.inputs[2], labelDiffuseNode.outputs[0])
        _terrain_material.node_tree.links.new(_material_output.inputs[0], masterMixShaderNode.outputs[0])
        ############################################################

        if _latest_emission_output is not None:
            _terrain_material.node_tree.links.new(PBSDFNode.inputs[17], _latest_emission_output.outputs[0])

        # add disp mapping node
        if _latest_disp_output is not None:
            disp_mapping_node = _terrain_material.node_tree.nodes.new("ShaderNodeDisplacement")
            disp_mapping_node.inputs[1].default_value = general_terrain_cfg['dispMidLevel']
            disp_mapping_node.inputs[2].default_value = general_terrain_cfg['dispScale']
            disp_mapping_node.location = (_node_offset[0] + 4000, -150)
            # link nodes
            _terrain_material.node_tree.links.new(disp_mapping_node.inputs[0], _latest_disp_output.outputs[0])
            _terrain_material.node_tree.links.new(_material_output.inputs[2], disp_mapping_node.outputs[0])

        self._node_tree = _terrain_material

        # Pass entries #################################################################################################
        # RGBDPass entries #############################################################################################
        self.add_pass_entry(pass_name="RGBDPass",
                            node_handle=masterMixShaderNode,
                            value_type="inputs",
                            value=[0, 0])
        for instance_node in _instance_switching_node_list:
            self.add_pass_entry(pass_name="RGBDPass",
                                node_handle=instance_node,
                                value_type="inputs",
                                value=[0, 0])
        ###################################################################################### end of RGBDPass entries #

        # SemanticPass entries #########################################################################################
        self.add_pass_entry(pass_name="SemanticPass",
                            node_handle=masterMixShaderNode,
                            value_type="inputs",
                            value=[0, 1])
        for instance_node in _instance_switching_node_list:
            self.add_pass_entry(pass_name="SemanticPass",
                                node_handle=instance_node,
                                value_type="inputs",
                                value=[0, 0])
        ################################################################################## end of SemanticPass entries #

        # InstancePass entries #########################################################################################
        for instance_node in _instance_switching_node_list:
            self.add_pass_entry(pass_name="InstancePass",
                                node_handle=instance_node,
                                value_type="inputs",
                                value=[0, 1])
        ################################################################################## end of SemanticPass entries #
        ########################################################################################## end of Pass entries #

        return _terrain_material

    def additional_pass_action(self, pass_name, pass_cfg, keyframe):
        """ overwrite base function
        Args:
            pass_name:      name of pass to activate [string]
            pass_cfg:       specific parameters for the pass [dict]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        # set semantic ID ##############################################################################################
        if "SemanticPass" == pass_name:
            self._label_ID_node.outputs[0].default_value = pass_cfg["activationID"] + 1
            if keyframe > -1:
                self._label_ID_node.outputs[0].keyframe_insert('default_value', frame=keyframe)
            ##################################################################### end of set interpolation to constant #
        ####################################################################################### end of set semantic ID #

        if keyframe > -1:
            # set interpolation to constant ############################################################################
            _fcurves = self._node_tree.node_tree.animation_data.action.fcurves
            for fcurve in _fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'CONSTANT'

    def getMaterials(self):
        return self._material_list

    def _create_voronoli_style_tiling_nodes(self,
                                            scale_to_tile_val=1.0,
                                            y_x_scale_ratio=1.0,
                                            trans_multi_val=1.0,
                                            trans_multi_x_val=-1.0,
                                            trans_multi_y_val=-1.0,
                                            trans_multi_z_val=-1.0,
                                            rot_multi_val=1.0,
                                            color_ramp_stop_1=0.191):

        # basic node group setup #######################################################################################
        # create node group
        _tiling_group = bpy.data.node_groups.new(type="ShaderNodeTree", name="voronoi_style_tiling")

        # inputs
        _group_input = _tiling_group.nodes.new("NodeGroupInput")
        _group_input.location = (0, -600)
        _tiling_group.inputs.new('NodeSocketValue', 'scale')

        # outputs
        _group_outputs = _tiling_group.nodes.new("NodeGroupOutput")
        _group_outputs.location = (3500, -800)
        _tiling_group.outputs.new('NodeSocketColor', 'blankFac')
        _tiling_group.outputs.new('NodeSocketVector', 'blankVec')
        _tiling_group.outputs.new('NodeSocketVector', 'tilingVec')
        ################################################################################ end of basic node group setup #

        # voronoi style tiling functionality ###########################################################################
        # create all needed nodes ######################################################################################
        # texture corrdinates node
        _tiling_tex_corrd_node = _tiling_group.nodes.new("ShaderNodeTexCoord")
        _tiling_tex_corrd_node.location = (400, 0)

        # [blank] mapping node
        _tiling_blank_mapping_node = _tiling_group.nodes.new("ShaderNodeMapping")
        _tiling_blank_mapping_node.location = (2400, -300)

        # [scale] combine node
        _tiling_scale_combine_math_node = _tiling_group.nodes.new("ShaderNodeCombineXYZ")
        _tiling_scale_combine_math_node.location = (1200, -300)

        # [scale] multiply node
        _tiling_scale_aspect_math_node = _tiling_group.nodes.new("ShaderNodeMath")
        _tiling_scale_aspect_math_node.location = (800, -300)
        _tiling_scale_aspect_math_node.operation = 'MULTIPLY'
        _tiling_scale_aspect_math_node.inputs[1].default_value = y_x_scale_ratio

        # [blank] voronoi texture node for filling the blanks
        _tiling_noise_tex_blanks_node = _tiling_group.nodes.new("ShaderNodeTexVoronoi")
        _tiling_noise_tex_blanks_node.location = (1200, 0)
        _tiling_noise_tex_blanks_node.feature = 'DISTANCE_TO_EDGE'

        # [blank] color ramp node
        _tiling_color_ramp_node = _tiling_group.nodes.new("ShaderNodeValToRGB")
        _tiling_color_ramp_node.location = (3200, 0)
        _tiling_color_ramp_node.color_ramp.elements[1].position = color_ramp_stop_1

        # voronoi texture node for tiling
        _tiling_noise_tex_node = _tiling_group.nodes.new("ShaderNodeTexVoronoi")
        _tiling_noise_tex_node.location = (1200, -1200)
        _tiling_noise_tex_node.feature = 'F1'
        _tiling_noise_tex_node.distance = 'EUCLIDEAN'

        # multiply node
        _tiling_math_node = _tiling_group.nodes.new("ShaderNodeMath")
        _tiling_math_node.location = (800, -800)
        _tiling_math_node.operation = 'MULTIPLY'
        _tiling_math_node.inputs[1].default_value = scale_to_tile_val

        # [translation] multiply node
        _tiling_translation_math_node = _tiling_group.nodes.new("ShaderNodeMath")
        _tiling_translation_math_node.location = (1600, -1000)
        _tiling_translation_math_node.operation = 'MULTIPLY'
        _tiling_translation_math_node.inputs[1].default_value = trans_multi_val

        # [translation] multiply node x
        _tiling_translation_math_x_node = _tiling_group.nodes.new("ShaderNodeMath")
        _tiling_translation_math_x_node.location = (2400, -800)
        _tiling_translation_math_x_node.operation = 'MULTIPLY'
        if trans_multi_x_val < 0:
            trans_multi_x_val = random.uniform(0.2, 3.0)
        _tiling_translation_math_x_node.inputs[1].default_value = trans_multi_x_val

        # [translation] multiply node y
        _tiling_translation_math_y_node = _tiling_group.nodes.new("ShaderNodeMath")
        _tiling_translation_math_y_node.location = (2400, -1000)
        _tiling_translation_math_y_node.operation = 'MULTIPLY'
        if trans_multi_y_val < 0:
            trans_multi_y_val = random.uniform(0.2, 3.0)
        _tiling_translation_math_y_node.inputs[1].default_value = trans_multi_y_val

        # [translation] multiply node z
        _tiling_translation_math_z_node = _tiling_group.nodes.new("ShaderNodeMath")
        _tiling_translation_math_z_node.location = (2400, -1200)
        _tiling_translation_math_z_node.operation = 'MULTIPLY'
        if trans_multi_z_val < 0:
            trans_multi_z_val = random.uniform(0.2, 3.0)
        _tiling_translation_math_z_node.inputs[1].default_value = trans_multi_z_val

        # [translation] separate node
        _tiling_translation_separate_node = _tiling_group.nodes.new("ShaderNodeSeparateXYZ")
        _tiling_translation_separate_node.location = (2000, -1000)

        # [translation] combine node z
        _tiling_translation_combine_node = _tiling_group.nodes.new("ShaderNodeCombineXYZ")
        _tiling_translation_combine_node.location = (2800, -1000)

        # [rotation] multiply node
        _tiling_rotation_math_node = _tiling_group.nodes.new("ShaderNodeMath")
        _tiling_rotation_math_node.location = (1600, -1400)
        _tiling_rotation_math_node.operation = 'MULTIPLY'
        _tiling_rotation_math_node.inputs[1].default_value = rot_multi_val

        # [rotation] combine node
        _tiling_rotation_combine_node = _tiling_group.nodes.new("ShaderNodeCombineXYZ")
        _tiling_rotation_combine_node.location = (2000, -1400)

        # mapping node
        _tiling_mapping_node = _tiling_group.nodes.new("ShaderNodeMapping")
        _tiling_mapping_node.location = (3200, -1200)

        ############################################################################### end of create all needed nodes #

        # link nodes ###################################################################################################
        _tiling_group.links.new(_tiling_noise_tex_blanks_node.inputs[0], _tiling_tex_corrd_node.outputs[0])
        _tiling_group.links.new(_tiling_noise_tex_node.inputs[0], _tiling_tex_corrd_node.outputs[0])
        _tiling_group.links.new(_tiling_blank_mapping_node.inputs[0], _tiling_tex_corrd_node.outputs[0])
        _tiling_group.links.new(_tiling_mapping_node.inputs[0], _tiling_tex_corrd_node.outputs[0])

        _tiling_group.links.new(_tiling_noise_tex_blanks_node.inputs[2], _tiling_math_node.outputs[0])
        _tiling_group.links.new(_tiling_noise_tex_node.inputs[2], _tiling_math_node.outputs[0])

        _tiling_group.links.new(_tiling_color_ramp_node.inputs[0], _tiling_noise_tex_blanks_node.outputs[0])

        _tiling_group.links.new(_tiling_translation_math_node.inputs[0], _tiling_noise_tex_node.outputs[1])
        _tiling_group.links.new(_tiling_rotation_math_node.inputs[0], _tiling_noise_tex_node.outputs[1])

        _tiling_group.links.new(_tiling_translation_separate_node.inputs[0], _tiling_translation_math_node.outputs[0])
        _tiling_group.links.new(_tiling_translation_math_x_node.inputs[0], _tiling_translation_separate_node.outputs[0])
        _tiling_group.links.new(_tiling_translation_math_y_node.inputs[0], _tiling_translation_separate_node.outputs[1])
        _tiling_group.links.new(_tiling_translation_math_z_node.inputs[0], _tiling_translation_separate_node.outputs[2])

        _tiling_group.links.new(_tiling_translation_combine_node.inputs[0], _tiling_translation_math_x_node.outputs[0])
        _tiling_group.links.new(_tiling_translation_combine_node.inputs[1], _tiling_translation_math_y_node.outputs[0])
        _tiling_group.links.new(_tiling_translation_combine_node.inputs[2], _tiling_translation_math_z_node.outputs[0])

        _tiling_group.links.new(_tiling_rotation_combine_node.inputs[2], _tiling_rotation_math_node.outputs[0])

        _tiling_group.links.new(_tiling_mapping_node.inputs[1], _tiling_translation_combine_node.outputs[0])
        _tiling_group.links.new(_tiling_mapping_node.inputs[2], _tiling_rotation_combine_node.outputs[0])

        _tiling_group.links.new(_tiling_math_node.inputs[0], _group_input.outputs[0])
        # _tiling_group.links.new(_tiling_blank_mapping_node.inputs[3], _group_input.outputs[0])
        # _tiling_group.links.new(_tiling_mapping_node.inputs[3], _group_input.outputs[0])
        _tiling_group.links.new(_tiling_scale_aspect_math_node.inputs[0], _group_input.outputs[0])
        _tiling_group.links.new(_tiling_scale_combine_math_node.inputs[0], _group_input.outputs[0])
        _tiling_group.links.new(_tiling_scale_combine_math_node.inputs[1], _tiling_scale_aspect_math_node.outputs[0])

        _tiling_group.links.new(_tiling_blank_mapping_node.inputs[3], _tiling_scale_combine_math_node.outputs[0])
        _tiling_group.links.new(_tiling_mapping_node.inputs[3], _tiling_scale_combine_math_node.outputs[0])

        _tiling_group.links.new(_group_outputs.inputs[0], _tiling_color_ramp_node.outputs[0])
        _tiling_group.links.new(_group_outputs.inputs[1], _tiling_blank_mapping_node.outputs[0])
        _tiling_group.links.new(_group_outputs.inputs[2], _tiling_mapping_node.outputs[0])

        ############################################################################################ end of link nodes #
        #################################################################### end of voronoi style tiling functionality #

        # return node group
        return _tiling_group

    def _create_voronoli_style_merging(self, node_tree, tiling_node, texture_node):

        # duplicate texture
        _duplicated_tex_node = node_tree.node_tree.nodes.new('ShaderNodeTexImage')
        _duplicated_tex_node.image = texture_node.image
        _duplicated_tex_node.image.colorspace_settings.name = texture_node.image.colorspace_settings.name
        _duplicated_tex_node.location = (texture_node.location[0] + 400, texture_node.location[1])

        # create mix node
        _tex_mix_node = node_tree.node_tree.nodes.new("ShaderNodeMixRGB")
        _tex_mix_node.location = (texture_node.location[0] + 600, texture_node.location[1])

        # link
        node_tree.node_tree.links.new(_duplicated_tex_node.inputs[0], tiling_node.outputs[1])
        node_tree.node_tree.links.new(texture_node.inputs[0], tiling_node.outputs[2])

        node_tree.node_tree.links.new(_tex_mix_node.inputs[0], tiling_node.outputs[0])
        node_tree.node_tree.links.new(_tex_mix_node.inputs[1], _duplicated_tex_node.outputs[0])
        node_tree.node_tree.links.new(_tex_mix_node.inputs[2], texture_node.outputs[0])

        # return mix node
        return _tex_mix_node

    def _retrieve_parameter(self, cfg, key):
        if key in cfg:
            return cfg[key]
        else:
            return None

    ### The following lines are from https://www.poliigon.com/

    """
    taken from Poliigon shader! >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    """

    @staticmethod
    def load_nodegroup_config(engine_template):
        """Load in json node config for material based on set engine"""

        jsonfile = os.path.join(
            os.path.dirname(__file__), "engines", engine_template + ".json")
        if not os.path.isfile(jsonfile):
            print("Missing json file for workflow " + engine_template)
            raise Exception("Missing json file for workflow")
        with open(jsonfile) as jsonread:
            mat_config = json.load(jsonread)
        # mat_config = {}

        # convert certain things,
        # e.g., convert all locations to mathutils.vector(value)
        # and turn the lists in the default values into sets/tuples

        return mat_config

    """
    taken from Poliigon shader! <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    """

    @staticmethod
    def socket_type_to_class(type_id):
        """Mapping of input types to class strings"""
        if type_id == 'RGBA':  # ??
            return 'NodeSocketColor'
        elif type_id == 'VALUE':
            return 'NodeSocketFloat'
        elif type_id == 'VECTOR':
            return 'NodeSocketVector'
        elif type_id == 'CUSTOM':
            print("WARNING! Mapping custom socket tupe to float")
            return 'NodeSocketFloat'
        else:
            raise Exception('Unknown node socket type: ' + type_id)

    @staticmethod
    def socket_index_from_identifier(node, name, identifier, mode):
        """Get the input or output socket index based on identifier name"""
        res = None

        # short circuit return for routes, as the identifier doesn't match well
        # (ie, identifier="output", but actual index available is "Output")
        if node.type == "REROUTE":
            return 0  # in either case, to or from

        if mode == 'from':
            iterset = node.outputs
        elif mode == 'to':
            iterset = node.inputs
        else:
            raise Exception('Invalid mode for socket identifier')

        sockets = [sock.name for sock in iterset
                   if sock.name]  # ignore empty string names... e.g. in principled shader

        if len(sockets) == len(set(sockets)):
            # all values are unique, we can use the Socket name directly
            res = name
        else:
            # print("Names not unique in: ", sockets)
            # Names not unique, fallback to using the identifier
            for i, socket in enumerate(iterset):
                # print(i, socket, socket.identifier, identifier)
                if socket.identifier == identifier:
                    res = i
                    break

        if res is None:
            print('Could not determine node socket from input:')
            print(node, identifier, mode)
            raise Exception('Could not determine node socket from input')
        return res

    """
    taken from Poliigon shader! >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    """

    def create_nodegroup_from_config(self, mat_config):
        """Given a dictionary json object, create a node group"""
        # self.material.name = 'blub'
        self.verbose = True
        nodegroup = bpy.data.node_groups.new(
            '_mapping_node', type='ShaderNodeTree')
        m_nodes = nodegroup.nodes
        m_links = nodegroup.links

        # cache nodes for applying color space, as with later 2.8 builds we
        # can only do this after the image has been assigned to the node
        apply_colorspaces = []

        frames_with_children = []

        for node_name, node_data in mat_config["nodes"].items():
            if not hasattr(bpy.types, node_data["type_id"]):
                if self.verbose:
                    print("Node not available here")
                mat_config["nodes"][node_name]["datablock"] = None
                continue
            node = m_nodes.new(node_data["type_id"])
            node.select = False
            mat_config["nodes"][node_name]["datablock"] = node
            node.name = node_name
            if 'reroute' not in node_name.lower():
                node.label = mat_config["nodes"][node_name]['label']
            for key, value in node_data.items():
                if key in {"type", "type_id", "datablock", "COMMENT_ONLY"}:
                    continue
                if hasattr(value, '__call__'):
                    value = value()

                if key == 'color_space':
                    # special apply cases, to support newer 2.8 builds
                    apply_colorspaces.append([node, value])
                elif key == 'parent':
                    frames_with_children.append(value)
                    # apply parent (frame) to node if any
                    # setattr(node, key, mat_config["nodes"][value]["datablock"])
                    pass  # TODO, get this working in 2.7
                elif key == 'text':
                    if node.name not in bpy.data.texts:
                        txtblock = bpy.data.texts.new(node.name)
                        txtblock.write(value)
                    else:
                        txtblock = bpy.data.texts[node.name]
                    node.text = txtblock
                else:  # general case
                    setattr(node, key, value)

            # TODO: remove if 2.8 special spacing no longer needed
            # # fix 2.8 node spacing
            # if bpy.app.version >= (2, 80):
            #   # image nodes are wider now, move farther left
            #   if node.location[0] <= -430:
            #       node.location[0] -= 200
            #   if node_name == "Principled BSDF":
            #       node.location[1] += 50
            #   #node.location[0] *= 1.2 # space out nodes some more

        # Apply the parents for nodes, now that all nodes exist
        for node_name, node_data in mat_config["nodes"].items():
            for key, value in node_data.items():
                node = mat_config["nodes"][node_name]["datablock"]
                if key != 'parent':
                    continue
                # apply parent (frame) to node if any
                setattr(node, key, mat_config["nodes"][value]["datablock"])

        # Repeat-apply location for frames
        for node_name, node_data in mat_config["nodes"].items():
            node = mat_config["nodes"][node_name]["datablock"]
            if node.type != 'FRAME':
                continue
            elif node_name in frames_with_children:
                # double coordinates for frames with children to show up right
                node.location = [node_data['location'][0] * 2, node_data['location'][1] * 2]
            else:
                node.location = [node_data['location'][0], node_data['location'][1]]

        # Create the group input and output sockets
        for i, socket in enumerate(mat_config["inputs"]):
            nodegroup.inputs.new(
                self.socket_type_to_class(socket['type']), socket['name'])
            if 'min' in socket:
                nodegroup.inputs[i].min_value = socket['min']
            if 'max' in socket:
                nodegroup.inputs[i].max_value = socket['max']
            nodegroup.inputs[i].default_value = socket['default']
        for i, socket in enumerate(mat_config["outputs"]):
            nodegroup.outputs.new(
                self.socket_type_to_class(socket['type']), socket['name'])
            if 'min' in socket:
                nodegroup.outputs[i].min_value = socket['min']
            if 'max' in socket:
                nodegroup.outputs[i].max_value = socket['max']
            nodegroup.outputs[i].default_value = socket['default']

        if "COLOR" in mat_config and mat_config["nodes"]["COLOR"]["datablock"]:
            # To set the diffuse color texture preview in cycles texture mode
            mat_config["nodes"]["COLOR"]["datablock"].select = True
            m_nodes.active = mat_config["nodes"]["COLOR"]["datablock"]

        # Linking
        for lnk in mat_config["links"]:
            from_node = lnk['from']
            from_socket = lnk['from_socket']
            to_node = lnk['to']
            to_socket = lnk['to_socket']

            if not mat_config["nodes"][from_node] or not mat_config["nodes"][to_node]:
                continue

            # resolve the to_socket and from_socket to *index* (not name) input
            # based on original key of '_socket.identifier' (uniquely named)
            from_index = self.socket_index_from_identifier(
                mat_config["nodes"][from_node]["datablock"],
                from_socket, lnk['from_id'], 'from')
            to_index = self.socket_index_from_identifier(
                mat_config["nodes"][to_node]["datablock"],
                to_socket, lnk['to_id'], 'to')

            if from_index is None or to_index is None:
                if self.verbose:
                    print("Skipping link, could not fetch index")
                continue

            m_links.new(
                # mat_config["nodes"][from_node]["datablock"].outputs[from_socket],
                # mat_config["nodes"][to_node]["datablock"].inputs[to_socket])
                mat_config["nodes"][from_node]["datablock"].outputs[from_index],
                mat_config["nodes"][to_node]["datablock"].inputs[to_index])

        # updating defaults
        for d_set in mat_config["defaults"]:
            node = d_set['node']
            socket = d_set['socket']
            value = d_set['value']

            socket_id = self.socket_index_from_identifier(
                mat_config["nodes"][node]["datablock"],
                d_set['socket'], d_set['socket_id'], 'to')

            try:
                mat_config["nodes"][node]["datablock"].inputs[socket_id].default_value = value
            except Exception as err:
                print("Poliigon: Error setting default node value: ", node, socket, socket_id, value, str(err))

        return nodegroup
        """
        taken from Poliigon shader! <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        """
