from concurrent import futures
import logging

import grpc
import oaisys_pb2
import oaisys_pb2_grpc



import argparse

import _thread

import numpy as np

import src.TSS_simulation_online as TSSStageSimulator

import sys
#print(sys.executable)
#print(sys.path)
sys.path.insert(0,'/opt/ros/melodic/lib/python2.7/dist-packages')
# import rospy

_run_simulation = True
_batch_step = False

class testit():
    def __init__(self,cfg_path):
        self._stage_simulator = TSSStageSimulator.TSS_OP_CStageSimulator()
        self._stage_simulator.execute(cfg_path)


    def execute(self):
        while _run_simulation:
            if _batch_step:
                _batch_step = False
                self._stage_simulator.step_batch(meta_data=None)


class Greeter(oaisys_pb2_grpc.Oaisys):
    def __init__(self):
        global batch_step
        self.batch_ID = 0
        self.sample_ID = 0
        global sample_offset
        sample_offset = 0
        global current_file_list
        current_file_list = []
    
    def SayHello(self, request, context):
        global batch_step
        global sample_step
        global rendering_state
        batch_step = True
        sample_step = True
        print("im here")
        return helloworld_pb2.HelloReply(message='Hello, %s!' % request.name)

    def SayHelloAgain(self, request, context):

        return helloworld_pb2.HelloReply(message='Hello again, %s!' % request.name)

    def _pre_process_step_meta_data(self,meta_data):
        global current_meta_data

        _local_meta_data = {}
        _local_sensor_module_data = {}

        if meta_data.sensorModuleRequest.HasField("pose"):

            _pose_val = np.zeros((8))
            _pose = meta_data.sensorModuleRequest.pose

            if hasattr(_pose,"x"):
                _pose_val[1] = _pose.x
            if hasattr(_pose,"y"):
                _pose_val[2] = _pose.y
            if hasattr(_pose,"z"):
                _pose_val[3] = _pose.z

            if hasattr(_pose,"q_w"):
                _pose_val[4] = _pose.q_w
            if hasattr(_pose,"q_x"):
                _pose_val[5] = _pose.q_x
            if hasattr(_pose,"q_y"):
                _pose_val[6] = _pose.q_y
            if hasattr(_pose,"q_z"):
                _pose_val[7] = _pose.q_z

            _local_sensor_module_data["sensor_pose"] = _pose_val

        _local_meta_data["sensor"] = _local_sensor_module_data

        current_meta_data = _local_meta_data


    def StepSample(self, request, context):
        global batch_step
        global sample_step
        global sample_offset
        
        self.sample_ID += 1

        print(request)
        self._pre_process_step_meta_data(meta_data=request)
        
        batch_step = False
        sample_step = True

        _return_msg = oaisys_pb2.StepSampleReply(  successRet=True,
                                                    batchID=self.batch_ID+sample_offset,
                                                    sampleID=self.sample_ID+sample_offset)

        return _return_msg

    def StepBatch(self, request, context):
        global batch_step
        global sample_step

        self.sample_ID = 0
        self.batch_ID += 1
        
        batch_step = True
        sample_step = False
        return oaisys_pb2.StepBatchReply(successRet=True)

    def RenderFinished(self, request, context):
        global rendering_state
        global current_file_list

        _return_msg = oaisys_pb2.RenderFinishedReply(state=rendering_state)

        _return_msg.filePathList.extend(current_file_list)

        current_file_list = []

        return _return_msg

    def BatchCreationFinished(self, request, context):
        global batch_state
        print("server", batch_state)
        return oaisys_pb2.BatchCreationFinishedReply(state=batch_state)

    def EndSimulation(self, request, context):
        global run_simulation
        run_simulation = False
        return oaisys_pb2.SuccessMsg(successRet=True)



class GRPCWrapper(oaisys_pb2_grpc.Oaisys):
    """docstring for GRPCWrapper"""
    def __init__(self, cfg_path):
        super(GRPCWrapper, self).__init__()

        global batch_step
        global sample_step
        global rendering_state
        global run_simulation
        global batch_state

        global sample_offset


        batch_step = False
        sample_step = False
        rendering_state = 0
        batch_state = 0

        
        self._stage_simulator = TSSStageSimulator.TSS_OP_CStageSimulator()
        self._stage_simulator.execute(cfg_path)

        # get offset ID
        sample_offset = self._stage_simulator.get_batch_offset()

        run_simulation = True

        '''
        self._stage_simulator = TSSStageSimulator.TSS_OP_CStageSimulator()
        self._stage_simulator.execute(cfg_path)

        self._run_simulation = True
        self._batch_step = False


        while self._run_simulation:
            if self._batch_step:
                self._batch_step = False
                self._stage_simulator.step_batch(meta_data=None)
        '''
        #self._stage_simulator.step_batch(meta_data=None)

        #_thread.start_new_thread( self.step_batch,())



    def rendering_ready(self,request,context):
        pass

    def get_rendering_output(self):
        pass

    def spin(self):
        global run_simulation
        global current_meta_data
        global batch_step
        global batch_state
        global sample_step
        global rendering_state
        global current_file_list


        while run_simulation:
            if batch_step:
                batch_step = False
                rendering_state = 0
                batch_state = 1
                self._stage_simulator.step_batch(meta_data=None)
                batch_state = 2

            if sample_step:
                batch_state = 0
                sample_step = False
                rendering_state = 1
                batchID, sampleID = self._stage_simulator.step_sample(meta_data=current_meta_data)

                # get all rendered files and save to list
                current_file_list = self._stage_simulator.get_latest_rendering_list()
                print("current_file_list: ", current_file_list)

                rendering_state = 2
                print("batchID: ", batchID)
                print("sampleID: ", sampleID)
                print(rendering_state)
                print("Done Rendering!")

        print("End the simulation!")
        self._stage_simulator.end_simulation()

    
    def execute(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
        oaisys_pb2_grpc.add_OaisysServicer_to_server(Greeter(), server)
        server.add_insecure_port('[::]:50051')
        server.start()
        self.spin()
        server.wait_for_termination()
    

    '''
    def step_batch(self):

        while self._run_simulation:
            if self._batch_step:
                print("Hello!")
                self._batch_step = False
                self._stage_simulator.step_batch(meta_data=None)
    '''

    def step_sample(self,request,context):
        pass

    def end_simulation(self,request,context):
        pass




if __name__ == "__main__":

    global batch_step
    batch_step = False
    
    import sys
    argv = sys.argv

    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--") + 1:]  # get all args after "--"

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', required=False, help="config json file.")
    args = parser.parse_args(argv)
    _configPath = args.c


    _obj = GRPCWrapper(_configPath)
    _obj.execute()

    '''
    testobj = testit(_configPath)
    # setup gRPC server
    _server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    helloworld_pb2_grpc.add_GreeterServicer_to_server(GRPCWrapper(_configPath), _server)
    _server.add_insecure_port('[::]:50051')
    _server.start()
    testobj.execute()
    _server.wait_for_termination()
    '''