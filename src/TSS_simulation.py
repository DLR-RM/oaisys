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

# simulation imports
import src.tools.cfg_parser as cfg_parser
import src.handle.TSSSensorHandle as SensorHandle
import src.handle.TSSRenderHandle as RenderHandle
import src.handle.TSSEnvironmentEffectHandle as TSSEnvironmentEffectHandle
import src.handle.TSSAssetHandle as TSSAssetHandle
import src.handle.TSSRenderPostProcessingHandle as RenderPostProcessingHandle


class TSS_OP_CStageSimulator():
    bl_idname = "example.func_2"
    bl_label = "create Stage"

    def execute(self, cfg_path):

        self._print_welcome()

        # create path to custom start file #############################################################################
        _current_path = os.path.dirname(os.path.abspath(__file__))
        _start_file = os.path.join(_current_path, "../oaisys_data/blender_files/start_file/TSS_startfile.blend")
        ###################################################################### end of create path to custom start file #

        # read in cfg and distribute data ##############################################################################
        # create cfg parser
        self._cfg_parser = cfg_parser.CCfgParser()

        # read in cfg params
        self._cfg_parser.readInCfg(cfg_path)

        # get indv cfg dicts and distribute ############################################################################
        _simulation_setup_dict = self._cfg_parser.getSimulationSetupCFG()
        _sensor_setup_dict = self._cfg_parser.getSensorSetupCFG()
        _render_setup_dict = self._cfg_parser.getRenderSetupCFG()
        _post_effects_setup_dict = self._cfg_parser.getPostEffectSetupCFG()
        _env_setup_dict = self._cfg_parser.getEnvSetupCFG()
        _asset_setup_dict = self._cfg_parser.getAssetsCFG()
        ##################################################################### end of get indv cfg dicts and distribute #

        # TODO: move to cfg file
        _sensor_setup_dict["GENERAL"]["numSamples"] = _simulation_setup_dict["numSamplesPerBatch"]  # 10

        # retrieve sample information
        _num_batches = _simulation_setup_dict["numBatches"]
        _num_samples_per_batch = _simulation_setup_dict["numSamplesPerBatch"]

        # set render images flag
        _render_image = _simulation_setup_dict["renderImages"]

        # set save blender file flag
        _save_blender_files = _simulation_setup_dict["saveBlenderFiles"]
        ####################################################################### end of read in cfg and distribute data #

        # update output path
        if not _simulation_setup_dict['outputPath']:
            _simulation_setup_dict['outputPath'] = os.path.join(_current_path, "../oaisys_tmp/")

        # create base folder
        #_base_folder_path = self._create_output_folder(base_path=_simulation_setup_dict['outputPath'])



        # set logging folder for each module
        '''
        _sensor_setup_dict['GENERAL']['OAISYS_MODULE_LOGGING_FOLDER'] = os.path.join(_base_folder_path,
                                                                                     "sensor_data")
        _render_setup_dict['GENERAL']['OAISYS_MODULE_LOGGING_FOLDER'] = os.path.join(_base_folder_path,
                                                                                     "render_data")
        _post_effects_setup_dict['GENERAL']['OAISYS_MODULE_LOGGING_FOLDER'] = os.path.join(_base_folder_path,
                                                                                           "post_effects_data")
        _env_setup_dict['GENERAL']['OAISYS_MODULE_LOGGING_FOLDER'] = os.path.join(_base_folder_path,
                                                                                  "environment_effects_data")
        _asset_setup_dict['GENERAL']['OAISYS_MODULE_LOGGING_FOLDER'] = os.path.join(_base_folder_path,
                                                                                    "assets_data")
        '''

        # create all simulator classes #################################################################################

        _render_handle = RenderHandle.TSSRenderHandle()
        _post_effects_handle = RenderPostProcessingHandle.TSSRenderPostProcessingHandle()
        _env_handle = TSSEnvironmentEffectHandle.TSSEnvironmentEffectHandle()
        _asset_handle = TSSAssetHandle.TSSAssetHandle()
        _sensor_handle = SensorHandle.TSSSensorHandle()
        ########################################################################## end of create all simulator classes #

        # create output structure ######################################################################################
        # create base folder
        _base_folder_path = self._create_output_folder(base_path=_simulation_setup_dict['outputPath'])

        # save cfg files
        self._cfg_parser.save_cfg(outputPath=_base_folder_path)

        # update base folder
        _render_setup_dict["GENERAL"]["outputPath"] = _base_folder_path
        ############################################################################### end of create output structure #

        # init all classes #############################################################################################

        _sensor_handle.update_cfg(cfg=_sensor_setup_dict)
        _render_handle.update_cfg(cfg=_render_setup_dict)
        _post_effects_handle.update_cfg(cfg=_post_effects_setup_dict)
        _env_handle.update_cfg(cfg=_env_setup_dict)
        _asset_handle.update_cfg(cfg=_asset_setup_dict)
        ###################################################################################### end of init all classes #

        _batch_ID_offset = _simulation_setup_dict["outputIDOffset"]

        # iterate over all batches #####################################################################################
        for batch_ID in range(1, _num_batches + 1):
            self._prCyan("######################### NEXT BATCH #################################")
            sys.stdout.flush()

            # create new batch folder
            _batch_output_folder = self._create_batch_folder(base_path=_base_folder_path, batch_id= \
                batch_ID + _batch_ID_offset)

            # load start up file
            bpy.ops.wm.open_mainfile(filepath=_start_file)

            # reset frame counter
            _frame = 1

            # set new output path
            _render_handle.set_output_folder(output_folder_path=_batch_output_folder)

            # execute create functions
            _meshes = _asset_handle.create()
            _sensor_handle.create(mesh_list=_meshes)
            _post_effects_handle.create()
            _env_handle.create()


            # update render layers and create render handle
            _render_handle.set_compositor_pass_list(compositor_pass_list= \
                                                        _post_effects_handle.get_compositor_pass_list())
            _render_handle.create()

            # update sensors with stages
            _sensor_handle.set_stages(_asset_handle.get_stages())

            #_sensor_handle._create_sensor_movement()

            # set metadata output folder path
            _sensor_handle.set_log_folder(log_folder_path=os.path.join(_batch_output_folder, "meta_data/sensor_data"))
            _render_handle.set_log_folder(log_folder_path=os.path.join(_batch_output_folder, "meta_data/render_data"))
            _post_effects_handle.set_log_folder(
                log_folder_path=os.path.join(_batch_output_folder, "meta_data/post_effects_data"))
            _env_handle.set_log_folder(log_folder_path=os.path.join(_batch_output_folder, "meta_data/environment_data"))
            _asset_handle.set_log_folder(log_folder_path=os.path.join(_batch_output_folder, "meta_data/asset_data"))

            # iterate over all samples #################################################################################
            for sample in range(1, _num_samples_per_batch + 1):

                _time_1 = time.time()
                self._prCyan(
                    "Sample " + str((batch_ID - 1) * _num_samples_per_batch + sample + _batch_ID_offset) + " / " + \
                    str(_num_samples_per_batch * _num_batches + _batch_ID_offset))

                # step all instances
                _sensor_handle.step(keyframe=_frame)
                _env_handle.step(keyframe=_frame)
                _asset_handle.step(keyframe=_frame)
                _render_handle.step(keyframe=_frame)

                # get render pass list
                _render_pass_list = _render_handle.get_render_pass_list()

                # iterate over all render passes #######################################################################
                for render_pass in _render_pass_list:

                    # activate render pass
                    render_pass.activate_pass(keyframe=_frame)

                    # get current render pass name
                    _render_pass_name = render_pass.get_name()

                    # get number of subpasses to be rendered
                    _num_sub_renderings = render_pass.get_num_sub_renderings()

                    # iterate over sub render channels #################################################################
                    for sub_render_idx in range(0, _num_sub_renderings):

                        # get cfg file for sub channel pass
                        _pass_cfg = render_pass.get_sub_render_cfg(sub_render_ID=sub_render_idx)

                        # activate pass for env
                        _env_handle.activate_pass(pass_name=_render_pass_name,
                                                  pass_cfg=_pass_cfg,
                                                  keyframe=_frame)

                        # activate pass for assets
                        _asset_handle.activate_pass(pass_name=_render_pass_name,
                                                    pass_cfg=_pass_cfg,
                                                    keyframe=_frame)

                        # get list of all sensors
                        _sensor_list = _sensor_handle.get_sensor_list()

                        # iterate over sensors #########################################################################
                        for sensor in _sensor_list:
                            # activate sensor
                            _sensor_pass_data = sensor.activate_pass(pass_name=_render_pass_name,
                                                                     pass_cfg=_pass_cfg,
                                                                     keyframe=_frame)
                            if _sensor_pass_data is not None:

                                # render sub channel pass
                                if _render_image:
                                    render_pass.render(sensor_data=_sensor_pass_data,
                                                       sub_render_ID=sub_render_idx,
                                                       keyframe=_frame)

                                # increase frame counter
                                _frame += 1
                                bpy.context.scene.frame_set(_frame)
                        ################################################################## end of iterate over sensors #
                    ########################################################## end of iterate over sub render channels #
                ############################################################# end of go iterate over all render passes #

                # log step all instances
                if _simulation_setup_dict["saveMetaData"]:
                    _sensor_handle.log_step(keyframe=_frame)
                    _env_handle.log_step(keyframe=_frame)
                    _asset_handle.log_step(keyframe=_frame)
                    _render_handle.log_step(keyframe=_frame)

                _time_2 = time.time()
                self._prCyan("Computation Time for Batch: " + str(_time_2 - _time_1))
            ########################################################################## end of iterate over all samples #

            # reset frame counter for blender file
            bpy.context.scene.frame_set(1)

            # save file ################################################################################################
            if _save_blender_files:
                self._prCyan("SAVING BLENDER FILE!")
                _current_batch_id_str = "{:04d}".format(batch_ID + _batch_ID_offset)
                _blender_file_path = os.path.join(_batch_output_folder, "blender_file")
                pathlib.Path(_blender_file_path).mkdir(parents=True, exist_ok=True)
                _blender_file_path = os.path.join(_blender_file_path, "TSS_batch_" + _current_batch_id_str + '.blend')
                bpy.ops.wm.save_as_mainfile(filepath=_blender_file_path)
            ######################################################################################### end of save file #

            # reset modules ############################################################################################
            _sensor_handle.reset_module()
            _render_handle.reset_module()
            _env_handle.reset_module()
            _asset_handle.reset_module()
            ##################################################################################### end of reset modules #

        ############################################################################## end of iterate over all batches #

        # return
        return {'FINISHED'}

    def _create_output_folder(self, base_path):
        today = datetime.now()
        dateStampStr = today.strftime("%Y") + '-' + today.strftime("%m") + '-' + today.strftime("%d") + '-' + \
                       today.strftime("%H") + '-' + today.strftime("%M") + '-' + today.strftime("%S")
        _outputPath = os.path.join(base_path, dateStampStr)
        pathlib.Path(_outputPath).mkdir(parents=True, exist_ok=True)

        return _outputPath

    def _create_batch_folder(self, base_path, batch_id):
        _current_batch_id_str = "{:04d}".format(batch_id)
        _current_batch_sub_folder = "batch_" + _current_batch_id_str
        _outputPath = os.path.join(base_path, _current_batch_sub_folder)
        pathlib.Path(_outputPath).mkdir(parents=True, exist_ok=True)

        return _outputPath

    def _print_welcome(self):
        f = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), \
                              "../oaisys_data/banner/welcome_banner_oaisys_small.txt"), "r")
        self._prCyan(f.read())

    def _prCyan(self, skk):
        print("\033[96m {}\033[00m".format(skk))
