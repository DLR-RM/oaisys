from __future__ import print_function

import logging

import grpc
import oaisys_pb2
import oaisys_pb2_grpc

import random

import time

def run():
    
    

    with grpc.insecure_channel('localhost:50051') as channel:
        stub = oaisys_pb2_grpc.OaisysStub(channel)

        for jj in range(0,2):
            print("Request batch stepping!")
            step_batch_request_msg = stub.StepBatch(oaisys_pb2.StepBatchRequest())
            
            _batch_creation = True
            while _batch_creation:
                time.sleep(0.5)
                _ret = stub.BatchCreationFinished(oaisys_pb2.Empty())
                if 2 == _ret.state:
                    _batch_creation = False
                    print("Done!")

            step_sample_request_msg = oaisys_pb2.StepSampleRequest()
            poseDummy = oaisys_pb2.SensorModuleRequest()

            poseDummy.pose.x = random.uniform(0, 20)
            poseDummy.pose.y = 0.0
            poseDummy.pose.z = 0.0

            poseDummy.pose.q_w = 1.0
            poseDummy.pose.q_x = 0.0
            poseDummy.pose.q_y = 0.0
            poseDummy.pose.q_z = 0.0

            for ii in range(0,3):

                print(ii)

                poseDummy.pose.x = random.uniform(0, 20)

                step_sample_request_msg.sensorModuleRequest.CopyFrom(poseDummy)
                print("Request stepping!")
                response = stub.StepSample(step_sample_request_msg)
                print("response: ", response)
                print("DONE")

                _rendering = True
                while _rendering:
                    print("Nothing yet!")
                    time.sleep(1.0)
                    _ret = stub.RenderFinished(oaisys_pb2.Empty())
                    print(_ret.state)
                    print(_ret)
                    if 2 == _ret.state:
                        _rendering = False
        end_request_msg = stub.EndSimulation(oaisys_pb2.Empty())

if __name__ == '__main__':
    logging.basicConfig()
    run()