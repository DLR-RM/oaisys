# blender imports
import bpy

# utility imports
import random
import math

from src.TSSBase import TSSBase
from src.environment_effects.TSSEnvironmentEffects import TSSEnvironmentEffects

class EnvLightBlenderSky(TSSEnvironmentEffects):
    """docstring for EnvLightBlenderSky"""
    def __init__(self):
        super(EnvLightBlenderSky, self).__init__()
        # class vars ###################################################################################################
        self._sky_node = None
        self._label_ID_Node = None
        self._last_keyframe = -1
        ############################################################################################ end of class vars #


    def reset(self):
        """ reset function
        Args:
            None
        Returns:
            None
        """
        # class vars ###################################################################################################
        self._sky_node = None
        self._label_ID_Node = None
        self._last_keyframe = -1
        ############################################################################################ end of class vars #
        

    def _add_sky(self, last_element, node_offset=[0,0]):
        """ function to create sky
        Args:
            last_element:           last element of node tree [blObject]
            node_offset:            offset position for nodes [x,y] [list]
        Returns:
            None
        """
        # create sky shader ############################################################################################
        self._sky_node = self._world_node_tree.node_tree.nodes.new('ShaderNodeTexSky')
        self._sky_node.location = (node_offset[0]-2000,node_offset[1]+300)
        ##################################################################################### end of create sky shader #

        # attach last output to Background Shader node #################################################################
        _str = self._world_node_tree.node_tree.nodes["World Output"].inputs[0]
        _current_last_output = self._sky_node.outputs[0]
        ########################################################## end of attach last output to Background Shader node #

        # mix rgb to mix last_element with sky #########################################################################
        if last_element is not None:
            _mix_node = self._world_node_tree.node_tree.nodes.new('ShaderNodeMixRGB')
            _mix_node.location = (node_offset[0]-1500,node_offset[1]+300)

            self._world_node_tree.inputs[0].default_value = 1.0
            self._world_node_tree.blend_type = 'OVERLAY'
            self._world_node_tree.node_tree.links.new(_mix_node.inputs[1],last_element)
            self._world_node_tree.node_tree.links.new(_mix_node.inputs[2],self._sky_node.outputs[0])

            _current_last_output = _mix_node.outputs[0]
        ################################################################## end of mix rgb to mix last_element with sky #

        # set semantic nodes ###########################################################################################
        # get label vector from cfg
        _label_ID_vec = self._cfg["passParams"]["SemanticPass"]["semanticIDVec"]

        # create switching nodes for semantics
        _semantic_switching_node,self._label_ID_Node = self.create_semantic_nodes( node_tree=self._world_node_tree,
                                                                                    label_ID_vec=_label_ID_vec,
                                                                                    num_label_per_channel=15)

        # link switching nodes with tree
        self._world_node_tree.node_tree.links.new(_semantic_switching_node.inputs[1], _current_last_output)

        # update current last output
        _current_last_output = _semantic_switching_node.outputs[0]
        #################################################################################### end of set semantic nodes #

        # set instance nodes ###########################################################################################
        _label_ID_vec = [0]

        # create switching nodes for semantics
        _instance_switching_node = self.create_single_semantic_node(node_tree=self._world_node_tree,
                                                                    label_ID=_label_ID_vec[0],
                                                                    num_label_per_channel=15,
                                                                    node_offset=[-2000,-2000])

        # link switching nodes with tree
        self._world_node_tree.node_tree.links.new(_instance_switching_node.inputs[1], _current_last_output)

        # update current last output
        _current_last_output = _instance_switching_node.outputs[0]
        #################################################################################### end of set instance nodes #

        # Pass entries #################################################################################################
        # RGBDPass entries #############################################################################################
        self.add_pass_entry(pass_name="RGBDPass",
                            node_handle=_semantic_switching_node,
                            value_type="inputs",
                            value=[0,0])
        self.add_pass_entry(pass_name="RGBDPass",
                            node_handle=_instance_switching_node,
                            value_type="inputs",
                            value=[0,0])
        ###################################################################################### end of RGBDPass entries #
        
        # SemanticPass entries #########################################################################################
        self.add_pass_entry(pass_name="SemanticPass",
                            node_handle=_semantic_switching_node,
                            value_type="inputs",
                            value=[0,1])
        self.add_pass_entry(pass_name="SemanticPass",
                            node_handle=_instance_switching_node,
                            value_type="inputs",
                            value=[0,0])
        ################################################################################## end of SemanticPass entries #

        # SemanticPass entries #########################################################################################
        self.add_pass_entry(pass_name="InstancePass",
                            node_handle=_instance_switching_node,
                            value_type="inputs",
                            value=[0,1])
        ################################################################################## end of SemanticPass entries #
        ########################################################################################## end of Pass entries #
       
        # return handle to last output node
        return _current_last_output


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
            self._label_ID_Node.outputs[0].default_value = pass_cfg["activationID"]+1
            if keyframe > -1:
                self._label_ID_Node.outputs[0].keyframe_insert('default_value', frame=keyframe)
        ####################################################################################### end of set semantic ID #


    def _get_random_number(self,min_max_array):
        """ get random number from array; use uniformal distribution
        Args:
            min_max_array:      define min and max value [min_value, max_value] [float,float]; if just one value is
                                added to list, the same value is returned
        Returns:
            return random value [float]
        """

        # check length of array and caluclate random number ############################################################
        if len(min_max_array) > 1:
            return random.uniform(min_max_array[0],min_max_array[1])
        else:
            return min_max_array[0]
        ##################################################### end of check length of array and caluclate random number #


    def _set_sky_parameters_NISHITA(self,params,keyframe=-1):
        """ set sky NISHITA parameter for current frame
        Args:
            params:         params which are to be set for the sky node [dict]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            settings which are choosen for sky node [dict]
        """

        # local vars ###################################################################################################        
        _current_settings = {}
        ############################################################################################ end of local vars #

        # set sky type to NISHITA
        self._sky_node.sky_type = 'NISHITA'
        _current_settings['SkyType'] = 'NISHITA'

        # generate values for sky node and apply to node ###############################################################
        # set size of sun ##############################################################################################
        _current_settings['SunSize'] = self._get_random_number(params['SunSize'])
        self._sky_node.sun_size = math.radians(_current_settings['SunSize'])
        ####################################################################################### end of set size of sun #

        # set sun intensity ############################################################################################
        _current_settings['SunIntensity'] = self._get_random_number(params['SunIntensity'])
        self._sky_node.sun_intensity = _current_settings['SunIntensity']
        ##################################################################################### end of set sun intensity #

        # set evaluation of sun ########################################################################################
        _current_settings['SunElevation'] = self._get_random_number(params['SunElevation'])
        self._sky_node.sun_elevation =  math.radians(_current_settings['SunElevation'])
        ################################################################################# end of set evaluation of sun #

        # set rotation of sun ##########################################################################################
        _current_settings['SunRotation'] = self._get_random_number(params['SunRotation'])
        self._sky_node.sun_rotation = math.radians(_current_settings['SunRotation'])
        ################################################################################## end of set rotation of sun  #

        # set altitude of sun ##########################################################################################
        _current_settings['SunAltitude'] = self._get_random_number(params['SunAltitude'])
        self._sky_node.altitude = _current_settings['SunAltitude']
        ################################################################################### end of set altitude of sun #

        # set air density value ########################################################################################
        _current_settings['AirDensity'] = self._get_random_number(params['AirDensity'])
        self._sky_node.air_density = _current_settings['AirDensity']
        ################################################################################# end of set air density value #

        # set dust desnity value #######################################################################################
        _current_settings['DustDensity'] = self._get_random_number(params['DustDensity'])
        self._sky_node.dust_density = _current_settings['DustDensity']
        ################################################################################ end of set dust desnity value #

        # set ozone density value ######################################################################################
        _current_settings['OzoneDensity'] = self._get_random_number(params['OzoneDensity'])
        self._sky_node.ozone_density = _current_settings['OzoneDensity']
        ############################################################################### end of set ozone density value #
        ######################################################## end of generate values for sky node and apply to node #

        # set keyframe if requested ####################################################################################
        if keyframe > -1:

            self._sky_node.keyframe_insert('sun_size', frame=keyframe)
            self._sky_node.keyframe_insert('sun_intensity', frame=keyframe)
            self._sky_node.keyframe_insert('sun_elevation', frame=keyframe)
            self._sky_node.keyframe_insert('sun_rotation', frame=keyframe)
            self._sky_node.keyframe_insert('altitude', frame=keyframe)
            self._sky_node.keyframe_insert('air_density', frame=keyframe)
            self._sky_node.keyframe_insert('dust_density', frame=keyframe)
            self._sky_node.keyframe_insert('ozone_density', frame=keyframe)

            # set interpolation to constant ############################################################################
            _fcurves = self._world_node_tree.node_tree.animation_data.action.fcurves
            for fcurve in _fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'CONSTANT'
            ##################################################################### end of set interpolation to constant #
        ############################################################################# end of set keyframe if requested #

        # return choosen settings
        return _current_settings


    def create(self,last_element=None):
        """ create function
        Args:
            last_element:           current last element in node tree [blObject]
        Returns:
            return new last element [blObject]
        """

        # add sky
        return self._add_sky(last_element=last_element,node_offset=self._node_offset)


    def step(self,keyframe):
        """ step function
        Args:
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """
        self._set_sky_parameters_NISHITA(params=self._cfg, keyframe=keyframe)