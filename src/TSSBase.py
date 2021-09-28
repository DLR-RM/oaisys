# blender imports
#import bpy

# utility imports
import json
import os
import inspect


class TSSBase(object):
    """docstring for TSSBase"""
    def __init__(self):
        super(TSSBase, self).__init__()
        # common vars ##################################################################################################
        self._cfg = {}                      # cfg dict [dict]
        self._pass_dict = {}                # dict for TSS render passes [dict]
        self._trigger_option = -1           # triggering option [string]; 
                                            #            options: "LOCAL": higher level component takes care of it
                                            #                     "GLOBAL": the module itself takes care of it
        self._trigger_interval = 1          # interval of triggering [uint]     
        self._stepping_counter = 0          # counter which counts how often stepping function is executed [uint]
        self._module_type = 2               # module type   types:  1 -> main module
                                            #                       2 -> sub module
        ########################################################################################### end of common vars #

        # load default cfg file if available
        self._load_default_cfg()


    def reset_base(self):
        """ reset function
            DO NOT OVERWRITE!
        Args:
            None
        Returns:
            None
        """
        
        self._pass_dict = {}
        self._trigger_option = -1
        self._trigger_interval = 1
        self._stepping_counter = 0


    def create(self,cfg):
        """ function which is called in the beginning of TSS; should be overwritten by custom class
            OVERWRITE!
        Args:
            cfg:            cfg dict for particular class [dict]
        Returns:
            None
        """

        pass


    def set_module_type(self, type=2):
        """ function to set module type
            DO NOT OVERWRITE!
        Args:
            type:           module type   types:    1 -> main module
                                                    2 -> sub module
        Returns:
            None
        """

        # set module type
        self._module_type = type


    def step_module(self, keyframe=-1):
        """ step function is called by handle fucntion for every new sample in of the batch; should be overwritten by
            custom class
            DO NOT OVERWRITE!
        Args:
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        # increase stepping counter
        self._stepping_counter += 1

        if self._step_trigger_reached():

            # call stepping function
            self.step(keyframe=keyframe)


    def step(self, keyframe=-1):
        """ step function is called for every new sample in of the batch; should be overwritten by custom class
            OVERWRITE!
        Args:
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        pass


    def activate_pass(self,pass_name, pass_cfg, keyframe=-1):
        """ enables specific pass
            DO NOT OVERWRITE!
        Args:
            pass_name:      name of pass to activate [string]
            pass_cfg:       specific parameters for the pass [dict]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        # activate pass
        if pass_name in self._pass_dict:
            self.eval_pass_map(self._pass_dict[pass_name], keyframe)

        # additional pass action function call
        self.additional_pass_action(pass_name, pass_cfg, keyframe)


    def update_cfg(self,cfg):
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
            # update tpye 1 modules cfg
            if 1 == self._module_type:
                for k, v in cfg.items():
                    if k in self._cfg:
                        if isinstance(self._cfg[k], dict):
                            self._cfg[k].update(v)
                        else:
                            self._cfg[k] = v
                    else:
                        self._cfg[k] = v

            # update tpye 2 modules cfg
            if 2 == self._module_type:
                self._cfg.update(cfg)
        ####################################################################################### end of update cfg file #

        # set interval option ##########################################################################################
        if "stepIntervalOption" in self._cfg:
            if "stepInterval" in self._cfg:
                self._trigger_option = self._cfg["stepIntervalOption"]
                self._trigger_interval = self._cfg["stepInterval"]
            else:
                raise("Error: no interval specified!")
        else:
            self._trigger_option = 'GLOBAL'
        ################################################################################### end of set interval option #


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
        ############################################################################## end of compile default cfg path #

        # load default cfg file ########################################################################################
        if os.path.isfile(_default_cfg_path):
            with open(_default_cfg_path, 'r') as f:
                self._cfg = json.load(f)
        ################################################################################# end of load default cfg file #


    def get_cfg(self):
        """ get cfg dict of object
            DO NOT OVERWRITE!
        Args:
            None
        Returns:
            cfg [dict]
        """

        return self._cfg


    def get_trigger_type(self):
        """ get trigger tpye/option
            DO NOT OVERWRITE!
        Args:
            None
        Returns:
            trigger option [str]
        """

        return self._trigger_option


    def _step_trigger_reached(self):
        """ check if trigger limit is reached
            DO NOT OVERWRITE!
        Args:
            None
        Returns:
            status of trigger [boolean]
        """

        if "GLOBAL" == self._trigger_option:
            return True

        if "LOCAL" == self._trigger_option:
            return (((self._stepping_counter-1) % self._trigger_interval) == 0)


    def set_step_trigger_type(self,trigger_option):
        """ set trigger type
            DO NOT OVERWRITE!
        Args:
            trigger_option:     trigger option [str]; "GLOBAL" or "LOCAL"
        Returns:
            None
        """

        self._trigger_option = trigger_option


    def set_step_trigger_interval(self,trigger_interval):
        """ st trigger inveral
            DO NOT OVERWRITE!
        Args:
            trigger_interval:     trigger interval [int]
        Returns:
            None
        """

        self._trigger_interval = trigger_interval


    def set_general_cfg(self,cfg):
        """ set general cfg dict for object
            DO NOT OVERWRITE!
        Args:
            cfg:            cfg dict of class [dict]
        Returns:
            None
        """

        self._general_cfg = cfg


    def get_general_cfg(self):
        """ get genral cfg dict of object
            DO NOT OVERWRITE!
        Args:
            None
        Returns:
            general cfg [dict]
        """

        return self._general_cfg


    def add_pass_entry(self,pass_name,node_handle,value_type,value):
        """ add pass entry
            DO NOT OVERWRITE!
        Args:
            pass_name:      name of pass [string]
            node_handle:    handle of node [blObject]
            value_type:     type of the value, for instance "inputs" or "outputs" [string]
            value:          to be set value; two values of form [entry_ID,entry_value] [list] [int,float]
        Returns:
            None
        """

        # def local var
        _node_Found = False

        # check if pass name exist already #############################################################################
        if pass_name in self._pass_dict:
            # go through node handles ##################################################################################
            for handle in self._pass_dict[pass_name]:
                # assign value if node handle exist ####################################################################
                if node_handle == handle["nodeHandle"]:
                    if value_type in handle:
                        handle[value_type].append(value)
                    else:
                        handle[value_type] = [value]
                    _node_found = True
                    break
                ############################################################# end of assign value if node handle exist #
            ########################################################################### end of go through node handles #

            # create new list entry ####################################################################################
            if not _node_Found:
                _pass_entry = {}
                _pass_entry["nodeHandle"] = node_handle
                _pass_entry[value_type] = [value]
                self._pass_dict[pass_name].append(_pass_entry)
            ############################################################################# end of create new list entry #
        else:
            # create new list entry ####################################################################################
            _pass_entry = {}
            _pass_entry["nodeHandle"] = node_handle
            _pass_entry[value_type] = [value]
            self._pass_dict[pass_name] = [_pass_entry]
            ############################################################################# end of create new list entry #
        ###################################################################### end of check if pass name exist already #


    def set_pass_dict(self,pass_dict):
        """ set pass dict for object
            DO NOT OVERWRITE!
        Args:
            pass_dict:      pass dict of class [dict]
        Returns:
            None
        """

        self._pass_dict = pass_dict


    def additional_pass_action(self,pass_name, pass_cfg, keyframe):
        """ step function is called for every new sample in of the batch; should be overwritten by custom class.
            This function should be called by function activate_pass
            OVERWRITE!
        Args:
            pass_name:      name of pass to activate [string]
            pass_cfg:       specific parameters for the pass [dict]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        pass


    def eval_pass_map(self, pass_map, keyframe=-1):
        """ go through pass_map and set defined values. Set keyframes if desired.
            DO NOT OVERWRITE!
        Args:
            pass_map:       sub dict of self._pass_dict [dict]
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """

        # local vars ###################################################################################################
        _node_handle = None             # node handle [blender Object]
        ############################################################################################ end of local vars #

        # iterate through items in pass_map ############################################################################
        for pass_map_value in pass_map:#.items():
            # get node handle for setting params
            _node_handle = pass_map_value['nodeHandle']

            # set node inputs ##########################################################################################
            if 'inputs' in pass_map_value:
                for param in pass_map_value['inputs']:
                    # set node input value
                    _node_handle.inputs[param[0]].default_value = param[1]

                    # set keyframe if desired
                    if keyframe > -1:
                        _node_handle.inputs[param[0]].keyframe_insert('default_value', frame=keyframe)
            #################################################################################### end of set node inputs#

            # set node outputs #########################################################################################
            if 'outputs' in pass_map_value:
                for param in pass_map_value['outputs']:
                    # set node output value
                    _node_handle.outputs[param[0]].default_value = param[1]

                    # set keyframe if desired
                    if keyframe > -1:
                        _node_handle.outputs[param[0]].keyframe_insert('default_value', frame=keyframe)
            ################################################################################## end of set node outputs #

        ##################################################################### end of iterate through items in pass_map #


    def _set_keyframe_interpolation(self, node_tree, interpolation='CONSTANT'):
        """ set keyframe interpolation for given node tree
            DO NOT OVERWRITE!
        Args:
            node_tree:      node tree [blObject]
            interpolation:  interploation type [string]
        Returns:
            None
        """

        if node_tree is not None:
            _fcurves = node_tree.node_tree.animation_data.action.fcurves
            for fcurve in _fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = interpolation


    # define color scheme ##############################################################################################
    def _prRed(self,skk): print("\033[91m {}\033[00m" .format(skk)) 
    def _prGreen(self,skk): print("\033[92m {}\033[00m" .format(skk)) 
    def _prYellow(self,skk): print("\033[93m {}\033[00m" .format(skk)) 
    def _prLightPurple(self,skk): print("\033[94m {}\033[00m" .format(skk)) 
    def _prPurple(self,skk): print("\033[95m {}\033[00m" .format(skk)) 
    def _prCyan(self,skk): print("\033[96m {}\033[00m" .format(skk)) 
    def _prLightGray(self,skk): print("\033[97m {}\033[00m" .format(skk)) 
    def _prBlack(self,skk): print("\033[98m {}\033[00m" .format(skk))
    ####################################################################################### end of define color scheme #


if __name__ == '__main__':
    dummyBase = TSSBase()

    node = {'node1':{'nodeHandle': 'nix', 'inputs': [(0,'231'),(5,5)]}}

    dummyBase._pass_dict['rgb'] = node
    dummyBase.activate_pass('rgb',None)
