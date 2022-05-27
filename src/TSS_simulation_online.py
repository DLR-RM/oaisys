# blender imports
import bpy

# utility imports
import numpy as np

# system imports
import sys
import os
import pathlib
from datetime import datetime
import time
import random

# simulation imports
import src.tools.cfg_parser as cfg_parser
import src.handle.TSSSensorHandle as SensorHandle
import src.handle.TSSRenderHandle as RenderHandle
import src.handle.TSSEnvironmentEffectHandle as TSSEnvironmentEffectHandle
import src.handle.TSSAssetHandle as TSSAssetHandle
import src.handle.TSSRenderPostProcessingHandle as RenderPostProcessingHandle


from concurrent import futures
import logging

import grpc
import oaisys_pb2
import oaisys_pb2_grpc


class Greeter(oaisys_pb2_grpc.GreeterServicer):

    def SayHello(self, request, context):
        return oaisys_pb2.HelloReply(message='Hello, %s!' % request.name)

    def SayHelloAgain(self, request, context):
        return oaisys_pb2.HelloReply(message='Hello again, %s!' % request.name)


class TSS_OP_CStageSimulator():
    bl_idname = "example.func_2"
    bl_label = "create Stage"
    
    def execute3(self, cfg_path):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        oaisys_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
        server.add_insecure_port('[::]:50051')
        server.start()
        self.execute2(cfg_path)
        server.wait_for_termination()

    def execute(self, cfg_path):
        self._print_welcome()

        self._first_batch = True
        self._rendering_progress = 0

        # create path to custom start file #############################################################################
        self._current_path = os.path.dirname(os.path.abspath(__file__))
        self._start_file = os.path.join(self._current_path,"../oaisys_data/blender_files/start_file/TSS_startfile.blend")
        ###################################################################### end of create path to custom start file #

        #self._init_modules(cfg_path=cfg_path)
        #self.execute2(cfg_path=cfg_path)

        self._init_modules(cfg_path=cfg_path)


    def rendering_ready(self):
        return self._rendering_progress

    def get_rendering_output(self):

        if 1 == self._rendering_progress:
            # rendering still in progress
            return None

        if 2 == self._rendering_progress:
            # rendering is ready
            return None # TODO: implement

        if 0 == self._rendering_progress:
            # no rendering was triggered
            return None


    def _init_modules(self,cfg_path):

        self.batch_ID = 0
        self.sample_ID = 0
        self.latest_render_list = []

        # read in cfg and distribute data ##############################################################################
        # create cfg parser
        self._cfg_parser = cfg_parser.CCfgParser()

        # read in cfg params
        self._cfg_parser.readInCfg(cfg_path)

        # get indv cfg dicts and distribute ############################################################################
        self._simulation_setup_dict = self._cfg_parser.getSimulationSetupCFG()
        self._sensor_setup_dict = self._cfg_parser.getSensorSetupCFG()
        self._render_setup_dict = self._cfg_parser.getRenderSetupCFG()
        self._post_effects_setup_dict = self._cfg_parser.getPostEffectSetupCFG()
        self._env_setup_dict = self._cfg_parser.getEnvSetupCFG()
        self._asset_setup_dict = self._cfg_parser.getAssetsCFG()
        ##################################################################### end of get indv cfg dicts and distribute #

        # TODO: move to cfg file
        self._sensor_setup_dict["GENERAL"]["numSamples"] = self._simulation_setup_dict["numSamplesPerBatch"]#10

        # retrieve sample information
        self._num_batches = self._simulation_setup_dict["numBatches"]
        self._num_samples_per_batch = self._simulation_setup_dict["numSamplesPerBatch"]

        # set render images flag
        self._render_image = self._simulation_setup_dict["renderImages"]

        # set save blender file flag
        self._save_blender_files = self._simulation_setup_dict["saveBlenderFiles"]
        ####################################################################### end of read in cfg and distribute data #

        # update output path
        if not self._simulation_setup_dict['outputPath']:
            self._simulation_setup_dict['outputPath'] = os.path.join(self._current_path,"../oaisys_tmp/")


        # create base folder
        self._base_folder_path = self._create_output_folder(base_path=self._simulation_setup_dict['outputPath'])

        # create all simulator classes #################################################################################
        self._sensor_handle = SensorHandle.TSSSensorHandle()
        self._render_handle = RenderHandle.TSSRenderHandle()
        self._post_effects_handle = RenderPostProcessingHandle.TSSRenderPostProcessingHandle()
        self._env_handle = TSSEnvironmentEffectHandle.TSSEnvironmentEffectHandle()
        self._asset_handle = TSSAssetHandle.TSSAssetHandle()
        ########################################################################## end of create all simulator classes #

        # create output structure ######################################################################################
        # create base folder
        self._base_folder_path = self._create_output_folder(base_path=self._simulation_setup_dict['outputPath'])

        # update base folder
        self._render_setup_dict["GENERAL"]["outputPath"] = self._base_folder_path
        ############################################################################### end of create output structure #

        # init all classes #############################################################################################
        self._sensor_handle.update_cfg(cfg=self._sensor_setup_dict)
        self._render_handle.update_cfg(cfg=self._render_setup_dict)
        self._post_effects_handle.update_cfg(cfg=self._post_effects_setup_dict)
        self._env_handle.update_cfg(cfg=self._env_setup_dict)
        self._asset_handle.update_cfg(cfg=self._asset_setup_dict)
        ###################################################################################### end of init all classes #
        
        self._batch_ID_offset = self._simulation_setup_dict["outputIDOffset"]

    def _create_scene(self):
        # create new batch folder
        self._batch_output_folder = self._create_batch_folder(base_path=self._base_folder_path,batch_id=\
                                                                                            self.batch_ID+\
                                                                                            self._batch_ID_offset)

        # load start up file
        print(self._start_file)
        bpy.ops.wm.open_mainfile(filepath=self._start_file)
        # reset frame counter
        self._frame = 1

        # set new output path
        self._render_handle.set_output_folder(output_folder_path=self._batch_output_folder)

        # execute create functions
        self._sensor_handle.create()
        self._post_effects_handle.create()
        self._env_handle.create()
        self._asset_handle.create()

        # update render layers and create render handle
        self._render_handle.set_compositor_pass_list(compositor_pass_list=\
                                                    self._post_effects_handle.get_compositor_pass_list())
        self._render_handle.create()

        # update sensors with stages
        self._sensor_handle.set_stages(self._asset_handle.get_stages())

    def get_batch_offset(self):
        if self._batch_ID_offset:
            return self._batch_ID_offset
        else:
            return 0 

    def get_latest_rendering_list(self):
        return self.latest_render_list

    def step_sample(self,meta_data):

        self.latest_render_list = []

        # increase sample count
        self.sample_ID += 1

        print("META DATA: ", meta_data)
        self._rendering_progress = 1

        self._time_1 = time.time()
        #self._prCyan("Sample " + str((self.batch_ID-1)*self._num_samples_per_batch+self.sample) + " / " + \
        #                                                                str(self._num_samples_per_batch*\
        #                                                                    self._num_batches))

        # Middleware Interface
        #self._stepping_data = self._call_middleware()
        self._stepping_data = {}
        self._stepping_data["sensor"] = meta_data["sensor"] if "sensor" in meta_data else None
        self._stepping_data["env"] = meta_data["env"] if "env" in meta_data else None
        self._stepping_data["asset"] = meta_data["asset"] if "asset" in meta_data else None
        self._stepping_data["render"] = meta_data["render"] if "render" in meta_data else None

        # step all instances
        self._sensor_handle.step(meta_data=self._stepping_data["sensor"],keyframe=self._frame)
        self._env_handle.step(meta_data=self._stepping_data["env"],keyframe=self._frame)
        self._asset_handle.step(meta_data=self._stepping_data["asset"],keyframe=self._frame)
        self._render_handle.step(meta_data=self._stepping_data["render"],keyframe=self._frame)

        # get render pass list
        self._render_pass_list = self._render_handle.get_render_pass_list()
        
        # iterate over all render passes #######################################################################
        for render_pass in self._render_pass_list:

            # activate render pass
            render_pass.activate_pass(keyframe=self._frame)

            # get current render pass name
            _render_pass_name = render_pass.get_name()

            # get number of subpasses to be rendered
            _num_sub_renderings = render_pass.get_num_sub_renderings()

            # iterate over sub render channels #################################################################
            for sub_render_idx in range(0,_num_sub_renderings):

                # get cfg file for sub channel pass
                _pass_cfg = render_pass.get_sub_render_cfg(sub_render_ID=sub_render_idx)

                # activate pass for env
                self._env_handle.activate_pass(  pass_name=_render_pass_name,
                                            pass_cfg=_pass_cfg,
                                            keyframe=self._frame)

                # activate pass for assets
                self._asset_handle.activate_pass(pass_name=_render_pass_name,
                                            pass_cfg=_pass_cfg,
                                            keyframe=self._frame)

                # get list of all sensors
                _sensor_list = self._sensor_handle.get_sensor_list()

                # iterate over sensors #########################################################################
                for sensor in _sensor_list:
                    # activate sensor
                    _sensor_pass_data = sensor.activate_pass(   pass_name=_render_pass_name,
                                                                pass_cfg=_pass_cfg,
                                                                keyframe=self._frame)
                    if _sensor_pass_data is not None:
                        
                        # render sub channel pass
                        if self._render_image:
                            _output_path = render_pass.render(  sensor_data=_sensor_pass_data,
                                                                sub_render_ID=sub_render_idx,
                                                                keyframe=self._frame)

                            if isinstance(_output_path,list):
                                for path_sample in _output_path:
                                    self.latest_render_list.append(path_sample)
                            else:
                                self.latest_render_list.append(_output_path)

                        # increase frame counter
                        self._frame += 1
                        bpy.context.scene.frame_set(self._frame)
                ################################################################## end of iterate over sensors #
            ########################################################## end of iterate over sub render channels #
        ############################################################# end of go iterate over all render passes #
        
        self._time_2 = time.time()
        self._prCyan("Computation Time for Batch: " + str(self._time_2-self._time_1))

        self._rendering_progress = 2

        return (self.batch_ID+self._batch_ID_offset), self.sample_ID


    def end_simulation(self):
        if not self._first_batch:
            self._reset_scene()

        exit()
        return {'FINISHED'}


    def step_batch(self,meta_data):
        self._prCyan("######################### NEXT BATCH #################################")
        sys.stdout.flush()

        # reset sample ID
        self.sample_ID = 0

        # increase batch ID
        self.batch_ID += 1

        if not self._first_batch:
            self._reset_scene()
        else:
            self._first_batch = False

        self._create_scene()


    def _reset_scene(self):
        # reset frame counter for blender file
        bpy.context.scene.frame_set(1)

        # save file ################################################################################################
        if self._save_blender_files:
            self._prCyan("SAVING BLENDER FILE!")
            _current_batch_id_str = "{:04d}".format(self.batch_ID+self._batch_ID_offset)
            _blender_file_path = os.path.join(self._batch_output_folder,"blender_file")
            pathlib.Path(_blender_file_path).mkdir(parents=True, exist_ok=True)
            _blender_file_path = os.path.join(_blender_file_path,"TSS_batch_"+_current_batch_id_str+'.blend')
            bpy.ops.wm.save_as_mainfile(filepath=_blender_file_path)
        ######################################################################################### end of save file #

        # reset modules ############################################################################################
        self._sensor_handle.reset_module()
        self._render_handle.reset_module()
        self._env_handle.reset_module()
        self._asset_handle.reset_module()
        ##################################################################################### end of reset modules #

    def execute2(self, cfg_path):

        self._init_modules(cfg_path=cfg_path)

        # iterate over all batches #####################################################################################
        for batch_ID in range(1,self._num_batches+1):
            
            self.batch_ID = batch_ID
            self.step_batch(meta_data=None)


            # iterate over all samples #################################################################################
            for sample in range(1,self._num_samples_per_batch+1):
                self.sample = sample
                self._step_sample(meta_data=None)
                
            ########################################################################## end of iterate over all samples #

            

        ############################################################################## end of iterate over all batches #

        # return
        self.end_simulation()


    def _create_output_folder(self,base_path):
        today = datetime.now()
        dateStampStr = today.strftime("%Y") + '-' + today.strftime("%m") + '-' + today.strftime("%d") + '-' + \
                                        today.strftime("%H") + '-' + today.strftime("%M") + '-' + today.strftime("%S")
        _outputPath = os.path.join(base_path,dateStampStr)
        pathlib.Path(_outputPath).mkdir(parents=True, exist_ok=True)

        return _outputPath

    def _create_batch_folder(self,base_path,batch_id):
        _current_batch_id_str = "{:04d}".format(batch_id)
        _current_batch_sub_folder = "batch_" + _current_batch_id_str
        _outputPath = os.path.join(base_path,_current_batch_sub_folder)
        pathlib.Path(_outputPath).mkdir(parents=True, exist_ok=True)

        return _outputPath

    def _print_welcome(self):
        f = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),\
                                                        "../oaisys_data/banner/welcome_banner_oaisys_small.txt"), "r")
        self._prCyan(f.read())

    def _prCyan(self,skk): print("\033[96m {}\033[00m" .format(skk))



    def _call_middleware(self):

        _stepping_data = {}


        _tmp = {}
        _tmp["sensor_pose"] = [0,random.uniform(0, 10), random.uniform(0, 10),random.uniform(0, 10), 1, 0, 0, 0]

        _stepping_data["sensor"] = _tmp
        _stepping_data["env"] = None
        _stepping_data["asset"] = None
        _stepping_data["render"] = None

        return _stepping_data