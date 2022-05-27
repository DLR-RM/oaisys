cmake_minimum_required(VERSION 2.8.12)
project(oaisys_client_ros)

add_definitions(-std=c++14)

find_package(catkin REQUIRED COMPONENTS
  roscpp
  rospy
  tf
  grpc
  eigen_catkin
)

catkin_package(
  INCLUDE_DIRS include
  CATKIN_DEPENDS grpc roscpp rospy
  LIBRARIES ${PROJECT_NAME} ${ALL_GRPC_LIBS} ${ALL_PROTOBUF_LIBS}
)

generate_proto(${PROJECT_NAME}_proto GRPC proto/oaisys.proto)

#############
# LIBRARIES #
#############
include_directories(
  include
  ${Boost_INCLUDE_DIR}
  ${catkin_INCLUDE_DIRS}
  ${Eigen_INCLUDE_DIRS}
  ${PROTO_HDRS}
)

add_library(${PROJECT_NAME}
  src/oaisys_client.cpp
)
add_dependencies(${PROJECT_NAME} ${PROJECT_NAME}_proto ${${PROJECT_NAME}_EXPORTED_TARGETS} ${catkin_EXPORTED_TARGETS})
target_link_libraries(${PROJECT_NAME} ${PROJECT_NAME}_proto ${catkin_LIBRARIES})

add_executable(oaisys_client_node
  src/oaisys_client_node.cpp
)
add_dependencies(oaisys_client_node ${PROJECT_NAME}  ${${PROJECT_NAME}_EXPORTED_TARGETS} ${catkin_EXPORTED_TARGETS})
target_link_libraries(oaisys_client_node ${PROJECT_NAME} ${catkin_LIBRARIES} pthread )
