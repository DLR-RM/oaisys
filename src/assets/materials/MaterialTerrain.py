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

from src.assets.TSSMaterial import TSSMaterial

class MaterialTerrain(TSSMaterial):
    """docstring for MaterialTerrain"""
    def __init__(self):
        super(MaterialTerrain, self).__init__()
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


    def load_template_for_assets(self,cfg):
        _cfg = []

        # TODO: find more generic solution
        for terrain_sample in cfg:
            if "templatePath" in terrain_sample:

                # check if relative or absolute path is provided
                if not os.path.isabs(terrain_sample["templatePath"]):
                    # create abs path
                    _rel_path = terrain_sample["templatePath"]
                    _current_path = os.path.dirname(__file__)
                    terrain_sample["templatePath"] = os.path.join(_current_path,"../../../",_rel_path)

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
        self._print_msg("Create Terrain Material")

        # get cfgs #####################################################################################################
        _terrain_cfg = self._cfg["terrainTextureList"]
        _general_terrain_cfg = self._cfg["general"]
        ############################################################################################# end of  get cfgs #
        _terrain_cfg = self.load_template_for_assets(_terrain_cfg)


        # create material
        _terrain_material =\
                    self._create_mix_terrain_material(  material_name=self._cfg["name"],
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


    def _create_mix_terrain_material(   self, material_name, general_terrain_cfg, terrain_cfg,
                                        num_max_mix_terrains, num_min_mix_terrains, hard_label_borders,
                                        noise_phase_shift_enabled,noise_phase_rate, with_replacement=True):
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
        _terrain_cfg_copy = copy.deepcopy(terrain_cfg)

        # check if all terrains are supposed to be used
        if num_max_mix_terrains >= 0:

            # sample terrrains num_max_mix_terrains times
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
                _num_terrain_samples = random.randint(num_min_mix_terrains,num_max_mix_terrains)
            else:
                _num_terrain_samples = random.randint(num_min_mix_terrains,len(_terrain_cfg_copy))
                self._print_msg("Warning: adjusted num_max_mix_terrains!")

            for  jj in range(0,_num_terrain_samples):

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
        return self._create_materials(general_terrain_cfg, material_name, _channel_list, hard_label_borders,\
                                                                            noise_phase_shift_enabled, noise_phase_rate)


    def _get_map_path(self, base_path, prefix):
        """ function to get path to texture files
        Args:
            base_path:                                  base path of textures [string]
            prefix:                                     keyword, which has to be part of filename [string]
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
            _map_file = os.path.join(base_path,_map_file[0])
        ########################################################################## end of  check if any file was found #

        # return found file
        return _map_file


    def _create_materials(  self, general_terrain_cfg, material_name, material_cfg_list, hard_label_borders,
                            noise_phase_shift_enabled = False, noise_phase_rate = 0.0):

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
        _node_offset = [0,0]

        # current channel outputs
        _latest_PBSDF_output = None
        _latest_col_output = None
        _latest_spec_output = None
        _latest_rough_output = None
        _latest_nrm_output = None
        _latest_disp_output = None
        _latest_label_output = None

        # get material output node
        _material_output = bpy.data.materials[material_name].node_tree.nodes["Material Output"]
        _material_output.location = (_node_offset[0]+4300,_node_offset[1])

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
            _disp_map_path = None
            ################################################################################## end of define map paths #

            if not os.path.isabs(material_cfg['path']):
                # create abs path
                _current_path = os.path.dirname(__file__)
                material_cfg['path'] = os.path.join(_current_path,"../../../",material_cfg['path'])

            # get texture paths ########################################################################################
            # get color map ############################################################################################
            if (material_cfg['diffuse']):
                _col_map_path = self._get_map_path(material_cfg['path'],"COL")
                if _col_map_path is None:
                    _col_map_path = self._get_map_path(material_cfg['path'],"col")
                if _col_map_path is None:
                    _col_map_path = self._get_map_path(material_cfg['path'],"DIFF")
                if _col_map_path is None:
                    _col_map_path = self._get_map_path(material_cfg['path'],"diff")
                if _col_map_path is None:
                    self._print_msg("WARNING: diffuse texture in folder " + material_cfg['path'] + \
                                                                            " cannot be found! Using default color!")
            ##################################################################################### end of get color map #

            # get reflectance map ######################################################################################
            if (material_cfg['ref']):
                _gloss_map_path = self._get_map_path(material_cfg['path'],"GLOSS")
                if _gloss_map_path is None:
                    _gloss_map_path = self._get_map_path(material_cfg['path'],"gloss")

                if _gloss_map_path is None:
                    _rough_map_path = self._get_map_path(material_cfg['path'],"rough")
                if _rough_map_path is None:
                    _rough_map_path = self._get_map_path(material_cfg['path'],"rough")
                if _rough_map_path is None:
                    self._print_msg("WARNING: roughness texture in folder " + material_cfg['path'] + \
                                                                            " cannot be found! Using default color!")
            ############################################################################### end of get reflectance map #

            # get specular map #########################################################################################
            if (material_cfg['spec']):
                _refl_map_path = self._get_map_path(material_cfg['path'],"REFL")
                if _refl_map_path is None:
                    _refl_map_path = self._get_map_path(material_cfg['path'],"refl")

                if _refl_map_path is None:
                    _spec_map_path = self._get_map_path(material_cfg['path'],"spec")
                if _spec_map_path is None:
                    _spec_map_path = self._get_map_path(material_cfg['path'],"SPEC")
                if _spec_map_path is None:
                    self._print_msg("WARNING: specular texture in folder " + material_cfg['path'] + \
                                                                            " cannot be found! Using default color!")
            ################################################################################# end of  get specular map #

            # get normal map ###########################################################################################
            if (material_cfg['normal']):
                _normal_map_path = self._get_map_path(material_cfg['path'],"NRM")
                if _normal_map_path is None:
                    _normal_map_path = self._get_map_path(material_cfg['path'],"nrm")
                if _normal_map_path is None:
                    _normal_map_path = self._get_map_path(material_cfg['path'],"nor")
                if _normal_map_path is None:
                    self._print_msg("WARNING: normal texture in folder " + material_cfg['path'] + \
                                                                            " cannot be found! Using default color!")
            #################################################################################### end of get normal map #

            # get displacement map #####################################################################################
            if (material_cfg['displacement']):
                _disp_map_path = self._get_map_path(material_cfg['path'],"DISP")
                if _disp_map_path is None:
                    _disp_map_path = self._get_map_path(material_cfg['path'],"HEIGHT")
                if _disp_map_path is None:
                    _disp_map_path = self._get_map_path(material_cfg['path'],"disp")
                if _disp_map_path is None:
                    _disp_map_path = self._get_map_path(material_cfg['path'],"height")
                if _disp_map_path is None:
                    self._print_msg("WARNING: displacement texture in folder " + material_cfg['path'] + \
                                                                            " cannot be found! Using default color!")
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
                _rgb_image.location = (_node_offset[0]-470,_node_offset[1]+400)

                # use loaded image
                _rgb_image.image = _img

                # store current last col node
                _current_col_output = _rgb_image
                ################################################################ end of load image and create basic shader #

                # create color adjustemt if needed #########################################################################
                if "colorAdjustment" in material_cfg:
                    # create RGB curve node
                    _color_adjustment_curve = _terrain_material.node_tree.nodes.new('ShaderNodeRGBCurve')
                    _color_adjustment_curve.location = (_node_offset[0],_node_offset[1]+400)

                    # read in and adjust color ramp ########################################################################
                    # brigthess adjustment
                    if "cColorPoints" in material_cfg["colorAdjustment"]:
                        for point_Idx, point in enumerate(material_cfg["colorAdjustment"]["cColorPoints"]):
                            _color_adjustment_curve.mapping.curves[3].points.new(point[0],point[1])

                    # red adjustment
                    if "rColorPoints" in material_cfg["colorAdjustment"]:
                        for point_Idx, point in enumerate(material_cfg["colorAdjustment"]["rColorPoints"]):
                            _color_adjustment_curve.mapping.curves[0].points.new(point[0],point[1])

                    # green adjustment
                    if "gColorPoints" in material_cfg["colorAdjustment"]:
                        for point_Idx, point in enumerate(material_cfg["colorAdjustment"]["gColorPoints"]):
                            _color_adjustment_curve.mapping.curves[1].points.new(point[0],point[1])

                    # blue adjustment
                    if "bColorPoints" in material_cfg["colorAdjustment"]:
                        for point_Idx, point in enumerate(material_cfg["colorAdjustment"]["bColorPoints"]):
                            _color_adjustment_curve.mapping.curves[2].points.new(point[0],point[1])
                    ################################################################# end of read in and adjust color ramp #

                    # update color curve
                    _color_adjustment_curve.mapping.update()

                    # link rgb image to curve
                    _terrain_material.node_tree.links.new(_color_adjustment_curve.inputs[1],_current_col_output.outputs[0])

                    # change color output reference
                    _current_col_output = _color_adjustment_curve
                ################################################################## end of create color adjustemt if needed #

                # add color variations if needed ###########################################################################
                if "colorVariation" in material_cfg:
                    # create saturation node
                    _color_variation_node = _terrain_material.node_tree.nodes.new('ShaderNodeHueSaturation')
                    _color_variation_node.location = (_node_offset[0]+400,_node_offset[1]+200)

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
                    _color_variation_noise_node.location = (_node_offset[0]+400,_node_offset[1]+700)
                    _color_variation_noise_node.noise_dimensions = '2D'

                    # read in and adjust noise #############################################################################
                    if "mergingNoiseScale" in material_cfg["colorVariation"]:
                        _color_variation_noise_node.inputs[2].default_value =\
                                                                    material_cfg["colorVariation"]["mergingNoiseScale"]

                    if "mergingNoiseDetail" in material_cfg["colorVariation"]:
                        _color_variation_noise_node.inputs[3].default_value =\
                                                                    material_cfg["colorVariation"]["mergingNoiseDetail"]

                    if "mergingNoiseRoughness" in material_cfg["colorVariation"]:
                        _color_variation_noise_node.inputs[4].default_value =\
                                                                    material_cfg["colorVariation"]["mergingNoiseRoughness"]

                    if "mergingNoiseDistorion" in material_cfg["colorVariation"]:
                        _color_variation_noise_node.inputs[5].default_value =\
                                                                    material_cfg["colorVariation"]["mergingNoiseDistorion"]
                    ###################################################################### end of read in and adjust noise #

                    # create color ramp for variation ######################################################################
                    if material_cfg["colorVariation"]["mergingcolorRampActivated"]:
                        _merging_color_ramp_node = _terrain_material.node_tree.nodes.new("ShaderNodeValToRGB")
                        _merging_color_ramp_node.color_ramp.elements[0].color =\
                                                        (   material_cfg["colorVariation"]["mergingColorStopColor_0"][0],\
                                                            material_cfg["colorVariation"]["mergingColorStopColor_0"][1],\
                                                            material_cfg["colorVariation"]["mergingColorStopColor_0"][2],\
                                                            material_cfg["colorVariation"]["mergingColorStopColor_0"][3])
                        _merging_color_ramp_node.color_ramp.elements[0].position =\
                                                            material_cfg["colorVariation"]["mergingColorStopPosition_0"]
                        _merging_color_ramp_node.color_ramp.elements[1].color =\
                                                        (   material_cfg["colorVariation"]["mergingColorStopColor_1"][0],\
                                                            material_cfg["colorVariation"]["mergingColorStopColor_1"][1],\
                                                            material_cfg["colorVariation"]["mergingColorStopColor_1"][2],\
                                                            material_cfg["colorVariation"]["mergingColorStopColor_1"][3])
                        _merging_color_ramp_node.color_ramp.elements[1].position =\
                                                            material_cfg["colorVariation"]["mergingColorStopPosition_1"]
                        _merging_color_ramp_node.location = (_node_offset[0]+800,_node_offset[1]+700)

                    _color_variation_mix_node = _terrain_material.node_tree.nodes.new("ShaderNodeMixRGB")
                    _color_variation_mix_node.location = (_node_offset[0]+1200,_node_offset[1]+400)
                    if "mergingMode" in material_cfg["colorVariation"]:
                        _color_variation_mix_node.blend_type = material_cfg["colorVariation"]["mergingMode"]
                    ############################################################### end of create color ramp for variation #

                    # link it ##############################################################################################
                    _terrain_material.node_tree.links.new(  _color_variation_node.inputs[4],
                                                            _current_col_output.outputs[0])
                    _terrain_material.node_tree.links.new(  _color_variation_mix_node.inputs[1],
                                                            _current_col_output.outputs[0])
                    _terrain_material.node_tree.links.new(  _color_variation_mix_node.inputs[2],
                                                            _color_variation_node.outputs[0])

                    if material_cfg["colorVariation"]["mergingcolorRampActivated"]:
                        _terrain_material.node_tree.links.new(  _merging_color_ramp_node.inputs[0],
                                                                _color_variation_noise_node.outputs[0])
                        _terrain_material.node_tree.links.new(  _color_variation_mix_node.inputs[0],
                                                                _merging_color_ramp_node.outputs[0])
                    else:
                        _terrain_material.node_tree.links.new(  _color_variation_mix_node.inputs[0],
                                                                _color_variation_noise_node.outputs[0])
                    ####################################################################################### end of link it #

                    # update current last color output reference
                    _current_col_output = _color_variation_mix_node
                #################################################################### end of add color variations if needed #

            if not _current_col_output:
                # provide default rgb value
                _col_default = _terrain_material.node_tree.nodes.new('ShaderNodeRGB')
                _col_default.location = (_node_offset[0]-470,_node_offset[1]+400)
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
                _roughness_image.location = (_node_offset[0]-470,_node_offset[1]-200)
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
                    _glossy_image.location = (_node_offset[0]-470,_node_offset[1]-200)
                    ################################################################## end of create image shader node #

                    # create invert map
                    _invert_node = _terrain_material.node_tree.nodes.new('ShaderNodeInvert')
                    _invert_node.location = (_node_offset[0]-200,_node_offset[1]-200)

                    # link nodes
                    _terrain_material.node_tree.links.new(_invert_node.inputs[1],_glossy_image.outputs[0])

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
                    _specular_image.location = (_node_offset[0]-470,_node_offset[1]+100)
                    ################################################################## end of create image shader node #

                    # create invert map
                    _invert_node = _terrain_material.node_tree.nodes.new('ShaderNodeInvert')
                    _invert_node.location = (_node_offset[0]-200,_node_offset[1]+100)

                    # link nodes
                    _terrain_material.node_tree.links.new(_invert_node.inputs[1],_specular_image.outputs[0])

                    # update current last spec node
                    _current_spec_output = _invert_node
                else:
                    # TODO: add reflectance code here!
                    pass


            if not _current_rough_output and not _current_spec_output:
                # provide default rgb value
                _glossy_default = _terrain_material.node_tree.nodes.new('ShaderNodeRGB')
                _glossy_default.location = (_node_offset[0]-470,_node_offset[1]-200)
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
                _normal_image.location = (_node_offset[0]-470,_node_offset[1]-500)
                ###################################################################### end of create image shader node #
                
                # update current last normal node
                _current_nrm_output = _normal_image

            if not _current_nrm_output:
                # provide default rgb value
                _nrm_default = _terrain_material.node_tree.nodes.new('ShaderNodeRGB')
                _nrm_default.location = (_node_offset[0]-470,_node_offset[1]-500)
                _nrm_default.outputs[0].default_value[0] = 0.5
                _nrm_default.outputs[0].default_value[1] = 0.5
                _nrm_default.outputs[0].default_value[2] = 0.5
                _nrm_default.outputs[0].default_value[3] = 1.0

                _current_nrm_output = _nrm_default
            ############################################################## end of  create NORMAL image texture channel #

            
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
                _disp_image.location = (_node_offset[0],_node_offset[1]-700)
                ###################################################################### end of create image shader node #

                # add color ramp node ##################################################################################
                dispColorRampNode = _terrain_material.node_tree.nodes.new("ShaderNodeValToRGB")
                if "dispStrength" in material_cfg:
                    _disp_strength = material_cfg["dispStrength"]

                    material_cfg['dispColorStopPosition_0'] = 0.0
                    material_cfg['dispColorStopPosition_1'] = 1.0
                    material_cfg['dispColorStopColor_0'] = [0.0,0.0,0.0,1.0]
                    material_cfg['dispColorStopColor_1'] = [_disp_strength,_disp_strength,_disp_strength,1.0]


                dispColorRampNode.color_ramp.elements[0].color = (  material_cfg['dispColorStopColor_0'][0],\
                                                                    material_cfg['dispColorStopColor_0'][1],\
                                                                    material_cfg['dispColorStopColor_0'][2],\
                                                                    material_cfg['dispColorStopColor_0'][3])
                dispColorRampNode.color_ramp.elements[0].position = material_cfg['dispColorStopPosition_0']
                dispColorRampNode.color_ramp.elements[1].color = (  material_cfg['dispColorStopColor_1'][0],\
                                                                    material_cfg['dispColorStopColor_1'][1],\
                                                                    material_cfg['dispColorStopColor_1'][2],\
                                                                    material_cfg['dispColorStopColor_1'][3])
                dispColorRampNode.color_ramp.elements[1].position = material_cfg['dispColorStopPosition_1']
                dispColorRampNode.location = (_node_offset[0]+400,_node_offset[1]-700)
                ########################################################################### end of add color ramp node #

                # link it
                _terrain_material.node_tree.links.new(dispColorRampNode.inputs[0], _disp_image.outputs[0])
                
                # update current last disü node
                _current_disp_output = dispColorRampNode

            if not _current_disp_output:
                # provide default rgb value
                _disp_default = _terrain_material.node_tree.nodes.new('ShaderNodeRGB')
                _disp_default.location = (_node_offset[0],_node_offset[1]-700)
                _disp_default.outputs[0].default_value[0] = 0.5
                _disp_default.outputs[0].default_value[1] = 0.5
                _disp_default.outputs[0].default_value[2] = 0.5
                _disp_default.outputs[0].default_value[3] = 1.0

                _current_disp_output = _disp_default
            #########################################
            ################################################################### end of create texture for each channel #

            # create mapping nodes for tiling textures #################################################################
            # TODO change!
            mat_config = self.load_nodegroup_config("uber_mapping")
            node_group = self.create_nodegroup_from_config(mat_config)

            _mapping_node = _terrain_material.node_tree.nodes.new(type='ShaderNodeGroup')
            _mapping_group = node_group

            # custom_mapping
            _mapping_node.node_tree = _mapping_group
            _mapping_node.name = _mapping_group.name
            _mapping_node.location = (_node_offset[0]-700,_node_offset[1])

            _mapping_node.inputs[1].default_value = imageSize
            _mapping_node.inputs[6].default_value = mosaicRotation
            _mapping_node.inputs[7].default_value = mosaicNoise

            _tex_coord_node = _terrain_material.node_tree.nodes.new('ShaderNodeTexCoord')
            _tex_coord_node.location = (_node_offset[0]-900,_node_offset[1])

            _terrain_material.node_tree.links.new(_mapping_node.inputs[0], _tex_coord_node.outputs[0])

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
            if _disp_map_path is not None: 
                _terrain_material.node_tree.links.new(_disp_image.inputs[0], _mapping_node.outputs[0])
            ########################################################## end of create mapping nodes for tiling textures #

            # setup semantic nodes #####################################################################################
            _label_node, self._label_ID_node = self.create_semantic_nodes(  \
                                                                node_tree=_terrain_material,
                                                                num_label_per_channel=self._num_labels_per_channel,
                                                                label_ID_vec=material_cfg['passParams']\
                                                                                    ['semantic_label']['labelIDVec'][0],
                                                                uv_map = _mapping_node.outputs[0],
                                                                node_offset=[_node_offset[0]-500, _node_offset[1]-1700])

            # set default value
            _label_node.inputs[0].default_value=1
            ############################################################################## end of setup semantic nodes #


            # setup instance nodes #####################################################################################
            # define default label ID vector
            # TODO: this parameter should be able to be overwitten
            _label_ID_vec = [0]

            # create switching nodes for semantics
            _instance_switching_node = self.create_single_semantic_node(\
                                                                node_tree=_terrain_material,
                                                                label_ID=_label_ID_vec[0],
                                                                num_label_per_channel=15,
                                                                node_offset=[_node_offset[0], _node_offset[1]-2000])

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
                _latest_disp_output = _current_disp_output
                _latest_label_output = _label_node
            else:
                # create noise shader to mix terrains ##################################################################
                # add new noise shader
                _noise_tex_coord_node = _terrain_material.node_tree.nodes.new("ShaderNodeTexCoord")
                _noise_tex_coord_node.location = (_node_offset[0]+600,_node_offset[1]-100)
                _noise_mapping_node = _terrain_material.node_tree.nodes.new("ShaderNodeMapping")
                _noise_mapping_node.location = (_node_offset[0]+1400,_node_offset[1]-100)
                _noise_tex_node = _terrain_material.node_tree.nodes.new("ShaderNodeTexNoise")
                _noise_tex_node.location = (_node_offset[0]+1800,_node_offset[1]-100)
                _noise_color_ramp_node = _terrain_material.node_tree.nodes.new("ShaderNodeValToRGB")
                _noise_color_ramp_node.location = (_node_offset[0]+2200,_node_offset[1]-100)
                if hard_label_borders:
                    _noise_color_label_ramp_node = _terrain_material.node_tree.nodes.new("ShaderNodeValToRGB")
                    _noise_color_label_ramp_node.location = (_node_offset[0]+2200,_node_offset[1]+200)
                    _noise_color_label_ramp_node.color_ramp.interpolation = 'CONSTANT'

                # fill in noise values #################################################################################
                _noise_tex_node.inputs[2].default_value = \
                            random.uniform(general_terrain_cfg['mergingNoise']['Scale'][0],\
                            general_terrain_cfg['mergingNoise']['Scale'][-1])
                _noise_tex_node.inputs[3].default_value = \
                            random.uniform(general_terrain_cfg['mergingNoise']['Detail'][0],\
                            general_terrain_cfg['mergingNoise']['Detail'][-1])
                _noise_tex_node.inputs[4].default_value = \
                            random.uniform(general_terrain_cfg['mergingNoise']['Roughness'][0],\
                            general_terrain_cfg['mergingNoise']['Roughness'][-1])
                _noise_tex_node.inputs[5].default_value = \
                            random.uniform(general_terrain_cfg['mergingNoise']['Distortion'][0],\
                            general_terrain_cfg['mergingNoise']['Distortion'][-1])
                ########################################################################## end of fill in noise values #

                # even split of rgb textures
                _noise_color_ramp_node.color_ramp.elements[0].position = 0.48
                _noise_color_ramp_node.color_ramp.elements[1].position = 0.52

                # calculate split of label noise split
                if hard_label_borders:
                    middleSlot = 0.5*(_noise_color_ramp_node.color_ramp.elements[1].position + \
                                                                _noise_color_ramp_node.color_ramp.elements[0].position)
                    _noise_color_label_ramp_node.color_ramp.elements[0].position = middleSlot
                    _noise_color_label_ramp_node.color_ramp.elements[1].position = middleSlot+0.00001

                # TODO: improve radnom sampling
                _noise_mapping_node.inputs[2].default_value[0] = random.random()
                _noise_mapping_node.inputs[2].default_value[1] = random.random()
                _noise_mapping_node.inputs[2].default_value[2] = random.random()
                ##################################################

                __noise_mapping_node_ist.append(_noise_mapping_node)

                # link noise nodes #####################################################################################
                _terrain_material.node_tree.links.new(_noise_mapping_node.inputs[0], _noise_tex_coord_node.outputs[0])
                #_terrain_material.node_tree.links.new(_noise_mapping_node.inputs[0], _noise_tex_coord_node.outputs[2])
                _terrain_material.node_tree.links.new(_noise_tex_node.inputs[0], _noise_mapping_node.outputs[0])
                _terrain_material.node_tree.links.new(_noise_color_ramp_node.inputs[0], _noise_tex_node.outputs[0])
                if hard_label_borders:
                    _terrain_material.node_tree.links.new(  _noise_color_label_ramp_node.inputs[0],\
                                                            _noise_tex_node.outputs[0])
                ############################################################################## end of link noise nodes #
                ########################################################### end of create noise shader to mix terrains #
                
                ## COLOR MIX ####################################################################################
                # add new mix shaders
                mixShaderNode = _terrain_material.node_tree.nodes.new("ShaderNodeMixRGB")
                mixShaderNode.location = (_node_offset[0]+3500,_node_offset[1]+200)

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
                    mixShaderNode.location = (_node_offset[0]+3500,_node_offset[1]+500)

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
                    mixShaderNode.location = (_node_offset[0]+3500,_node_offset[1]+800)

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
                    mixShaderNode.location = (_node_offset[0]+3500,_node_offset[1]+1100)

                    # combine shaders
                    _terrain_material.node_tree.links.new(mixShaderNode.inputs[0], _noise_color_ramp_node.outputs[0])
                    _terrain_material.node_tree.links.new(mixShaderNode.inputs[1], _latest_nrm_output.outputs[0])
                    _terrain_material.node_tree.links.new(mixShaderNode.inputs[2], _current_nrm_output.outputs[0])

                    # set new output
                    _latest_nrm_output = mixShaderNode
                ####################################################################################

                ## LABEL MIX ####################################################################################
                # add new mix shaders
                mixShaderNode = _terrain_material.node_tree.nodes.new("ShaderNodeMixRGB")
                mixShaderNode.location = (_node_offset[0]+2500,_node_offset[1]+300)

                # combine shaders
                if hard_label_borders:
                    _terrain_material.node_tree.links.new(mixShaderNode.inputs[0], _noise_color_label_ramp_node.outputs[0])
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
                    mixDISPShaderNode.location = (_node_offset[0]+2800,_node_offset[1]+300)

                    # combine shaders
                    _terrain_material.node_tree.links.new(mixDISPShaderNode.inputs[0], _noise_color_ramp_node.outputs[0])
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
            noisePhaseShiftOffset.location = (_node_offset[0]+700,_node_offset[1]-300)
            noisePhaseShiftOffset.outputs[0].default_value = random.random()
            noisePhaseShiftRate = _terrain_material.node_tree.nodes.new("ShaderNodeValue")
            noisePhaseShiftRate.location = (_node_offset[0]+700,_node_offset[1]-500)
            noisePhaseShiftRate.outputs[0].default_value = noise_phase_rate
            noisePhaseShiftFrame = _terrain_material.node_tree.nodes.new("ShaderNodeValue")
            noisePhaseShiftFrame.name = "frameID"
            noisePhaseShiftFrame.location = (_node_offset[0]+700,_node_offset[1]-700)
            noisePhaseShiftFrame.outputs[0].default_value = 0

            # add logic ##########################################
            noisePhaseShiftMultipleNode = _terrain_material.node_tree.nodes.new("ShaderNodeMath")
            noisePhaseShiftMultipleNode.operation = 'MULTIPLY'
            noisePhaseShiftMultipleNode.location = (_node_offset[0]+900,_node_offset[1]-600)
            _terrain_material.node_tree.links.new(noisePhaseShiftMultipleNode.inputs[0], noisePhaseShiftRate.outputs[0])
            _terrain_material.node_tree.links.new(noisePhaseShiftMultipleNode.inputs[1], noisePhaseShiftFrame.outputs[0])

            _noise_phase_shift_add_node = _terrain_material.node_tree.nodes.new("ShaderNodeMath")
            _noise_phase_shift_add_node.operation = 'ADD'
            _noise_phase_shift_add_node.location = (_node_offset[0]+1100,_node_offset[1]-400)
            _terrain_material.node_tree.links.new(_noise_phase_shift_add_node.inputs[0], noisePhaseShiftOffset.outputs[0])
            _terrain_material.node_tree.links.new(_noise_phase_shift_add_node.inputs[1], noisePhaseShiftMultipleNode.outputs[0])
            ##########################################

            # convert to vector ##############################################
            noisePhaseShiftVector = _terrain_material.node_tree.nodes.new("ShaderNodeCombineXYZ")
            noisePhaseShiftVector.location = (_node_offset[0]+1200,_node_offset[1]-600)
            noisePhaseShiftVector.inputs[0].default_value = 1
            noisePhaseShiftVector.inputs[1].default_value = 1
            _terrain_material.node_tree.links.new(noisePhaseShiftVector.inputs[2], _noise_phase_shift_add_node.outputs[0])
            ####################################

            for _mapping_node in __noise_mapping_node_ist:
                # connect to noise mapping node
                _terrain_material.node_tree.links.new(_mapping_node.inputs[3], noisePhaseShiftVector.outputs[0])

        # creat diffuse shader for labels: IMPORANT, it has to be piped thorugh a shader, otherwise no information is getting trough the diffuse render channel!
        labelDiffuseNode = _terrain_material.node_tree.nodes.new("ShaderNodeBsdfDiffuse")
        #labelDiffuseNode = _terrain_material.node_tree.nodes.new("ShaderNodeBsdfDiffuse")
        labelDiffuseNode.location = (_node_offset[0]+3700,0)
        #labelDiffuseNode.inputs[1].default_value = 1.0  # set roughness to 1. no glossy!
        _terrain_material.node_tree.links.new(labelDiffuseNode.inputs[0], _latest_label_output.outputs[0])

        # create Pinciple Shade node and link it #############################################
        PBSDFNode = _terrain_material.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        PBSDFNode.location = (_node_offset[0]+200,_node_offset[1])

        _terrain_material.node_tree.links.new(PBSDFNode.inputs[0], _latest_col_output.outputs[0])
        if _latest_spec_output is not None:
            _terrain_material.node_tree.links.new(PBSDFNode.inputs[5], _latest_spec_output.outputs[0])
        if _latest_rough_output is not None:
            _terrain_material.node_tree.links.new(PBSDFNode.inputs[7], _latest_rough_output.outputs[0])
        if _latest_nrm_output is not None:

            # add normal map
            normalMapNode = _terrain_material.node_tree.nodes.new('ShaderNodeNormalMap')
            normalMapNode.inputs[0].default_value = general_terrain_cfg['normalStrength']
            normalMapNode.location = (_node_offset[0],_node_offset[1])
            # link nodes
            _terrain_material.node_tree.links.new(normalMapNode.inputs[1], _latest_nrm_output.outputs[0])
            #_terrain_material.node_tree.links.new(PBSDFNode.inputs[19], normalMapNode.outputs[0])
            
            _terrain_material.node_tree.links.new(PBSDFNode.inputs[20], normalMapNode.outputs[0])
        ######################################################################################

        # link material output to last node ##################
        # add new mix shaders
        masterMixShaderNode = _terrain_material.node_tree.nodes.new("ShaderNodeMixShader")
        masterMixShaderNode.name = "rgb-label-mix"
        masterMixShaderNode.label = "rgb-label-mix"
        masterMixShaderNode.location = (_node_offset[0]+4000,0)
        masterMixShaderNode.inputs[0].default_value = 0 # set actual terrain material as default; 1 for gettnig its label
        ##################
        _terrain_material.node_tree.links.new(masterMixShaderNode.inputs[1], PBSDFNode.outputs[0])
        _terrain_material.node_tree.links.new(masterMixShaderNode.inputs[2], labelDiffuseNode.outputs[0])
        _terrain_material.node_tree.links.new(_material_output.inputs[0], masterMixShaderNode.outputs[0])
        ############################################################


        # add disp mapping node
        if _latest_disp_output is not None:
            disp_mapping_node = _terrain_material.node_tree.nodes.new("ShaderNodeDisplacement")
            disp_mapping_node.inputs[1].default_value = general_terrain_cfg['dispMidLevel']
            disp_mapping_node.inputs[2].default_value = general_terrain_cfg['dispScale']
            disp_mapping_node.location = (_node_offset[0]+4000,-150)
            # link nodes
            _terrain_material.node_tree.links.new(disp_mapping_node.inputs[0], _latest_disp_output.outputs[0])
            _terrain_material.node_tree.links.new(_material_output.inputs[2], disp_mapping_node.outputs[0])

        self._node_tree = _terrain_material

        # Pass entries #################################################################################################
        # RGBDPass entries #############################################################################################
        self.add_pass_entry(pass_name="RGBDPass",
                            node_handle=masterMixShaderNode,
                            value_type="inputs",
                            value=[0,0])
        for instance_node in _instance_switching_node_list:
            self.add_pass_entry(pass_name="RGBDPass",
                                node_handle=instance_node,
                                value_type="inputs",
                                value=[0,0])
        ###################################################################################### end of RGBDPass entries #

        # SemanticPass entries #########################################################################################
        self.add_pass_entry(pass_name="SemanticPass",
                            node_handle=masterMixShaderNode,
                            value_type="inputs",
                            value=[0,1])
        for instance_node in _instance_switching_node_list:
            self.add_pass_entry(pass_name="SemanticPass",
                                node_handle=instance_node,
                                value_type="inputs",
                                value=[0,0])
        ################################################################################## end of SemanticPass entries #

        # InstancePass entries #########################################################################################
        for instance_node in _instance_switching_node_list:
            self.add_pass_entry(pass_name="InstancePass",
                                node_handle=instance_node,
                                value_type="inputs",
                                value=[0,1])
        ################################################################################## end of SemanticPass entries #
        ########################################################################################## end of Pass entries #

        return _terrain_material



    def additional_pass_action(self,pass_name, pass_cfg, keyframe):
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
            self._label_ID_node.outputs[0].default_value = pass_cfg["activationID"]+1
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
            print("Missing json file for workflow "+engine_template)
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
        if type_id == 'RGBA': #??
            return 'NodeSocketColor'
        elif type_id == 'VALUE':
            return 'NodeSocketFloat'
        elif type_id == 'VECTOR':
            return 'NodeSocketVector'
        elif type_id == 'CUSTOM':
            print("WARNING! Mapping custom socket tupe to float")
            return 'NodeSocketFloat'
        else:
            raise Exception('Unknown node socket type: '+type_id)

    @staticmethod
    def socket_index_from_identifier(node, name, identifier, mode):
        """Get the input or output socket index based on identifier name"""
        res = None

        # short circuit return for routes, as the identifier doesn't match well
        # (ie, identifier="output", but actual index available is "Output")
        if node.type == "REROUTE":
            return 0 # in either case, to or from

        if mode == 'from':
            iterset = node.outputs
        elif mode == 'to':
            iterset = node.inputs
        else:
            raise Exception('Invalid mode for socket identifier')

        sockets = [sock.name for sock in iterset
            if sock.name] # ignore empty string names... e.g. in principled shader

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
        #self.material.name = 'blub'
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

                if key=='color_space':
                    # special apply cases, to support newer 2.8 builds
                    apply_colorspaces.append([node, value])
                elif key=='parent':
                    frames_with_children.append(value)
                    # apply parent (frame) to node if any
                    # setattr(node, key, mat_config["nodes"][value]["datablock"])
                    pass # TODO, get this working in 2.7
                elif key=='text':
                    if node.name not in bpy.data.texts:
                        txtblock = bpy.data.texts.new(node.name)
                        txtblock.write(value)
                    else:
                        txtblock = bpy.data.texts[node.name]
                    node.text = txtblock
                else: # general case
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
                if key!='parent':
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
                node.location = [node_data['location'][0]*2, node_data['location'][1]*2]
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

