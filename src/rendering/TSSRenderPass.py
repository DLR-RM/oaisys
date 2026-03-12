# blender imports
import bpy

# utility imports
import json
import os
import inspect

class TSSRenderPass(object):
    """docstring for TSSRenderPass"""
    def __init__(self,pass_name):
        super(TSSRenderPass, self).__init__()
        # class vars ###################################################################################################
        self._cfg = {}                              # cfg dict [dict]
        self._general_cfg = {}                      # general cfg dict [dict]
        self._render_layers_node = None             # basic blender node to get information about the passes [blObject]
        self._node_tree = None                      # node tree handle for compositor [blObject]
        self._node_offset = [0,0]                   # node offset [x,y]
        self._pass_name = pass_name                 # name of pass object [string]
        self._output_node = None                    # node for output
        self._global_step_index = 0                 # global index [uint]
        self._local_step_index = 0                  # global index [uint]
        self._compositor_pass_list = {}
        ############################################################################################ end of class vars #

        # load default cfg file if available
        self._load_default_cfg()

    def reset_module(self):
        """ reset all local vars
        Args:
            None
        Returns:
            None
        """

        self._render_layers_node = None
        self._node_tree = None
        self._node_offset = [0,0]
        self._output_node = None
        self._compositor_pass_list = {}

        self.reset()


    def reset(self):
        pass

    def _load_default_cfg(self):
        """ load default cfg dict for object
            DO NOT OVERWRITE!
        Args:
            None
        Returns:
            None
        """

        # compile default cfg path #####################################################################################
        _default_cfg_path = os.path.join(os.path.dirname(inspect.getfile(self.__class__)),"default_cfg")
        _default_cfg_path = os.path.join(_default_cfg_path,self.__class__.__name__+"_cfg.json")
        print(_default_cfg_path)
        ############################################################################## end of compile default cfg path #

        # load default cfg file ########################################################################################
        if os.path.isfile(_default_cfg_path):
            with open(_default_cfg_path, 'r') as f:
                self._cfg = json.load(f)
        ################################################################################# end of load default cfg file #


    def set_compositor_pass_list(self,compositor_pass_list):
        self._compositor_pass_list = compositor_pass_list

        if "CompositorNodeRLayers" in compositor_pass_list:
            self._render_layers_node = compositor_pass_list["CompositorNodeRLayers"]


    def _set_scene_keyframe_interpolation(self, interpolation='CONSTANT'):
        """ set keyframe interpolation for scene
            DO NOT OVERWRITE!
        Args:
            interpolation:  interploation type [string]
        Returns:
            None
        """

        _fcurves = bpy.context.scene.animation_data.action.fcurves
        for fcurve in _fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = interpolation


    def _set_render_samples(self, num_samples, keyframe):
        """ set number of samples for rendering in cycles
            DO NOT OVERWRITE!
        Args:
            num_samples:    number of samples [int]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        bpy.context.scene.cycles.samples = num_samples

        '''
        if keyframe > -1:
            bpy.context.scene.cycles.keyframe_insert('samples', frame=keyframe)

            self._set_scene_keyframe_interpolation(interpolation='CONSTANT')
        '''


    def _switch_On_AA(self,keyframe):
        """ switch on anti aliasing for cycles
            DO NOT OVERWRITE!
        Args:
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        bpy.context.scene.cycles.pixel_filter_type = 'BLACKMAN_HARRIS'

        '''
        if keyframe > -1:
            bpy.context.scene.cycles.keyframe_insert('pixel_filter_type', frame=keyframe)
        '''


    def _switch_Off_AA(self,keyframe=-1):
        """ switch off anti aliasing for cycles
            DO NOT OVERWRITE!
        Args:
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        bpy.context.scene.cycles.pixel_filter_type = 'BOX'

        '''
        if keyframe > -1:
            bpy.context.scene.cycles.keyframe_insert('pixel_filter_type', frame=keyframe)
        '''


    def _set_max_bounces(self, num_bounces, keyframe):
        """ set number of maximum light bounces for cycles
            DO NOT OVERWRITE!
        Args:
            num_bounces:    number of maximum light bounces [int]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        bpy.context.scene.cycles.max_bounces =  num_bounces

        '''
        if keyframe > -1:
            bpy.context.scene.cycles.keyframe_insert('max_bounces', frame=keyframe)

            self._set_scene_keyframe_interpolation(interpolation='CONSTANT')
        '''

    def _set_max_bounces_diffuse(self, num_bounces, keyframe):
        """ set number of maximum light bounces for cycles
            DO NOT OVERWRITE!
        Args:
            num_bounces:    number of maximum light bounces [int]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        bpy.context.scene.cycles.diffuse_bounces = num_bounces

    def _set_max_bounces_glossy(self, num_bounces, keyframe):
        """ set number of maximum light bounces for cycles
            DO NOT OVERWRITE!
        Args:
            num_bounces:    number of maximum light bounces [int]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        bpy.context.scene.cycles.glossy_bounces = num_bounces

    def _set_max_bounces_transmission(self, num_bounces, keyframe):
        """ set number of maximum light bounces for cycles
            DO NOT OVERWRITE!
        Args:
            num_bounces:    number of maximum light bounces [int]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        bpy.context.scene.cycles.transmission_bounces = num_bounces

    def _set_max_bounces_volume(self, num_bounces, keyframe):
        """ set number of maximum light bounces for cycles
            DO NOT OVERWRITE!
        Args:
            num_bounces:    number of maximum light bounces [int]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        bpy.context.scene.cycles.volume_bounces = num_bounces

    def _set_max_bounces_transparent(self, num_bounces, keyframe):
        """ set number of maximum light bounces for cycles
            DO NOT OVERWRITE!
        Args:
            num_bounces:    number of maximum light bounces [int]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        bpy.context.scene.cycles.transparent_max_bounces = num_bounces

    def _set_volume_step_rate(self, rate, keyframe):
        """ set number of maximum light bounces for cycles
            DO NOT OVERWRITE!
        Args:
            rate:           volume step rate [float]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        bpy.context.scene.cycles.volume_step_rate = rate

    def _set_volume_max_steps(self, steps, keyframe):
        """ set number of maximum light bounces for cycles
            DO NOT OVERWRITE!
        Args:
            steps:           volume max steps [int]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        bpy.context.scene.cycles.volume_step_rate = steps

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


    def get_name(self):
        """ get name of render pass
            DO NOT OVERWRITE!
        Args:
            None
        Returns:
            name of pass of object
        """

        return self._pass_name


    def get_general_cfg(self):
        """ get general cfg dict of object
            DO NOT OVERWRITE!
        Args:
            None
        Returns:
            cfg file of class [dict]
        """

        return self._general_cfg

    def update_cfg(self, cfg):
        """ update dict for object
            DO NOT OVERWRITE!
        Args:
            cfg:            cfg dict of class [dict]
        Returns:
            None
        """
        # update cfg file ##############################################################################################
        if "OVERWRITE_CFG" in cfg:
            # overwrite entire cfg
            self._cfg = cfg
        else:
            self._cfg.update(cfg)
        ####################################################################################### end of update cfg file #

    def get_cfg(self):
        """ get cfg dict of object
            DO NOT OVERWRITE!
        Args:
            None
        Returns:
            cfg file of class [dict]
        """

        return self._cfg


    def get_sub_render_cfg(self,sub_render_ID):
        """ get cfg of sub render; in default just return dict with activationID
            OVERWRITE IF NEEDED!
        Args:
            sub_render_ID       sub render ID [int]
        Returns:
            cfg file of sub render [dict]
        """

        return {"activationID": sub_render_ID}


    def get_num_sub_renderings(self):
        """ get number of sub renderings 
            DO NOT OVERWRITE!
        Args:
            None
        Returns:
            number of sub renderings [int]
        """

        return self._cfg["numIter"]


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


    def step(self, keyframe):
        """ step function
            OVERWRITE!
        Args:
            None
        Returns:
            None
        """

        pass

    def set_log_folder(self, log_folder_path):
        pass

    def log_step(self, keyframe):
        """ log step function is called for every new sample in of the batch; should be overwritten by custom class
            OVERWRITE!
        Args:
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
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


    def _print_msg(self,skk): print("\033[93m {}\033[00m" .format(skk)) 


    def render(self,sensor_data=None,keyframe=-1):
        """ execute rendering function
            OVERWRITE!
        Args:
            sensor_data:            optional sensor data [not defined]
        Returns:
            None
        """

        pass
