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
 * @brief OAISYS Client node
 *
 *
 * @author Jaeyoung Lim <jalim@ethz.ch>
 */

#include "oaisys_client_ros/oaisys_client.h"
#include "ros/ros.h"

void requestSample(std::shared_ptr<OaisysClient> &client) {
  Eigen::Vector3d position{Eigen::Vector3d::Zero()};
  Eigen::Quaterniond attitude{Eigen::Quaterniond::Identity()};
  position(0) = 1.0;
  position(1) = 2.0;
  position(2) = 30.0;

  // attitude.w() = 4.0;
  // attitude.x = 5.0;
  // attitude.y = 6.0;
  // attitude.z = 7.0;

  int batch_id{0};
  int sample_id{0};
  if (!client->StepSample(position, attitude, batch_id, sample_id)) {
    std::cout << "StepSample service failed" << std::endl;
  }

  bool render_finished{false};
  std::vector<std::string> filepath_list;
  while (!client->RenderFinished(render_finished, filepath_list)) {
     std::cout << "Waiting for render creation fished true: " << render_finished << std::endl;
     ros::Duration(1.0).sleep();
  }
  std::cout << "RenderFinished service result: " << render_finished << std::endl;
}

int main(int argc, char **argv) {
  ros::init(argc, argv, "oaisys_client_ros");
  ros::NodeHandle nh("");
  ros::NodeHandle nh_private("~");

  std::cout << "Starting oaisys client node" << std::endl;
  std::shared_ptr<OaisysClient> oaisys_client =
      std::make_shared<OaisysClient>(grpc::CreateChannel("localhost:50051", grpc::InsecureChannelCredentials()));

  if (!oaisys_client->StepBatch()) {
    std::cout << "StepBatch service failed" << std::endl;
  }
  ros::Duration(5.0).sleep();

  int batch_finished{0};
  while (!oaisys_client->BatchCreationFinished(batch_finished)) {
     std::cout << "Waiting for batch creation fished true: " << batch_finished << std::endl;
     ros::Duration(1.0).sleep();
  }
  std::cout << "BatchCreationFinished service result: " << batch_finished << std::endl;

  requestSample(oaisys_client);

  requestSample(oaisys_client);

  bool simulation_ended{false};
  if (!oaisys_client->EndSimulation(simulation_ended)) {
    std::cout << "EndSimulation service failed" << std::endl;
  } else {
    std::cout << "EndSimulation service result: " << simulation_ended << std::endl;
  }

  ros::spin();
  return 0;
}
