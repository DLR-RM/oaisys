/****************************************************************************
 *
 *   Copyright (c) 2021 Jaeyoung Lim. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in
 *    the documentation and/or other materials provided with the
 *    distribution.
 * 3. Neither the name PX4 nor the names of its contributors may be
 *    used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 * COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
 * OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
 * AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 * ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 *
 ****************************************************************************/

#include "oaisys_client_ros/oaisys_client.h"

OaisysClient::OaisysClient() :
  stub_(oaisys::Oaisys::NewStub(grpc::CreateChannel("localhost:50051", grpc::InsecureChannelCredentials()))) {
}

OaisysClient::OaisysClient(std::shared_ptr<Channel> channel) : stub_(oaisys::Oaisys::NewStub(channel)) {}

OaisysClient::~OaisysClient(){};

bool OaisysClient::StepBatch() {
  grpc::ClientContext context;
  grpc::CompletionQueue cq;
  grpc::Status status;

  oaisys::StepBatchRequest request;
  oaisys::StepBatchReply reply;
  std::unique_ptr<grpc::ClientAsyncResponseReader<oaisys::StepBatchReply> > rpc(
      stub_->PrepareAsyncStepBatch(&context, request, &cq));
  rpc->StartCall();
  rpc->Finish(&reply, &status, (void *)1);
  void* got_tag;
  bool ok = false;
  cq.Next(&got_tag, &ok);
  if (ok && got_tag == (void*)1) {
  }
  bool successRet = reply.successret();

  if (status.ok() && successRet) {
    return true;
  } else {
    return false;
  }
}

bool OaisysClient::StepSample(const Eigen::Vector3d position, const Eigen::Quaterniond attitude, int &batch_id,
                              int &sample_id) {
  grpc::ClientContext context;
  grpc::CompletionQueue cq;
  grpc::Status status;

  oaisys::StepSampleRequest request;
  oaisys::SensorModuleRequest::PoseType pose;
  pose.set_x(position(0));
  pose.set_y(position(1));
  pose.set_z(position(2));
  pose.set_q_w(attitude.w());
  pose.set_q_x(attitude.x());
  pose.set_q_y(attitude.y());
  pose.set_q_z(attitude.z());

  oaisys::SensorModuleRequest sm_request;
  sm_request.set_allocated_pose(&pose);
  request.set_allocated_sensormodulerequest(&sm_request);

  oaisys::StepSampleReply reply;
  std::unique_ptr<grpc::ClientAsyncResponseReader<oaisys::StepSampleReply> > rpc(
      stub_->PrepareAsyncStepSample(&context, request, &cq));
  rpc->StartCall();
  rpc->Finish(&reply, &status, (void *)1);
  void* got_tag;
  bool ok = false;
  cq.Next(&got_tag, &ok);
  if (ok && got_tag == (void*)1) {
  }
  bool success = reply.successret();

  sm_request.release_pose();
  request.release_sensormodulerequest();

  if (status.ok() && success) {
    // Only copy batch and sample id if the request succeeded
    batch_id = static_cast<int>(reply.batchid());
    sample_id = static_cast<int>(reply.sampleid());
    return true;
  } else {
    return false;
  }
}

bool OaisysClient::RenderFinished(bool &finished, std::vector<std::string>& filepath_list) {
  grpc::ClientContext context;
  grpc::CompletionQueue cq;
  grpc::Status status;

  oaisys::Empty request;
  oaisys::RenderFinishedReply reply;

  std::unique_ptr<grpc::ClientAsyncResponseReader<oaisys::RenderFinishedReply> > rpc(
      stub_->PrepareAsyncRenderFinished(&context, request, &cq));
  rpc->StartCall();
  rpc->Finish(&reply, &status, (void *)1);
  void* got_tag;
  bool ok = false;
  cq.Next(&got_tag, &ok);
  if (ok && got_tag == (void*)1) {
  }

  finished = bool(OAISYS_STATUS::FINISHED == static_cast<OAISYS_STATUS>(reply.state()));

  if (finished) {
    int i{0};
    std::cout << "Attempting to read file list" << std::endl;
    for (auto filepath : reply.filepathlist()) {
      std::cout << "rendered file path: " << filepath << std::endl;
      filepath_list.push_back(filepath);
      i++;
    }
  }  

  if (status.ok() && finished) {
    return true;
  } else {
    return false;
  }
}

bool OaisysClient::BatchCreationFinished(int &finished) {
  grpc::ClientContext context;
  grpc::CompletionQueue cq;
  grpc::Status status;

  oaisys::Empty request;
  oaisys::BatchCreationFinishedReply reply;

  std::unique_ptr<grpc::ClientAsyncResponseReader<oaisys::BatchCreationFinishedReply> > rpc(
      stub_->PrepareAsyncBatchCreationFinished(&context, request, &cq));
  rpc->StartCall();
  rpc->Finish(&reply, &status, (void *)1);
  void* got_tag;
  bool ok = false;
  cq.Next(&got_tag, &ok);
  if (ok && got_tag == (void*)1) {
  }
  if (status.ok() && (reply.state() == 2)) {
    finished = reply.state();
    return true;
  } else {
    return false;
  }
}

bool OaisysClient::EndSimulation(bool &finished) {
  grpc::ClientContext context;
  grpc::CompletionQueue cq;
  grpc::Status status;

  oaisys::Empty request;
  oaisys::SuccessMsg reply;

  std::unique_ptr<grpc::ClientAsyncResponseReader<oaisys::SuccessMsg> > rpc(
      stub_->PrepareAsyncEndSimulation(&context, request, &cq));
  rpc->StartCall();
  rpc->Finish(&reply, &status, (void *)1);
  void *got_tag;
  bool ok = false;

  if (status.ok()) {
    finished = reply.successret();
    return true;
  } else {
    return false;
  }
}
