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
/**
 * @brief Oaisys client
 *
 *
 * @author Jaeyoung Lim <jalim@ethz.ch>
 */

#ifndef OAISYS_CLIENT_H
#define OAISYS_CLIENT_H

#include <iostream>
#include <memory>
#include <string>

#include <Eigen/Dense>

#include <grpc++/grpc++.h>

#include "oaisys_client_ros/proto/oaisys.grpc.pb.h"
#include "oaisys_client_ros/proto/oaisys.pb.h"

using grpc::Channel;
using grpc::Status;

enum class OAISYS_STATUS {
  IN_PROGRESS=1,
  FINISHED=2
};

class OaisysClient {
 public:
  OaisysClient();
  OaisysClient(std::shared_ptr<Channel> channel);
  virtual ~OaisysClient();
  bool StepBatch();
  bool StepSample(const Eigen::Vector3d position, const Eigen::Quaterniond attitude, int &batch_id, int &sample_id);
  bool RenderFinished(bool &finished, std::vector<std::string>& filepath_list);
  bool BatchCreationFinished(int &finished);
  bool EndSimulation(bool &finished);

 private:
  std::unique_ptr<oaisys::Oaisys::Stub> stub_;
};

#endif
