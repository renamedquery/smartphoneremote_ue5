cmake_minimum_required(VERSION 2.8)
project(DeviceTracking)

IF(NOT CMAKE_BUILD_TYPE)
  SET(CMAKE_BUILD_TYPE Release)
ENDIF()

MESSAGE("Build type: " ${CMAKE_BUILD_TYPE})

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS}  -Wall  -O3 -march=native ")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall   -O3 -march=native")

# Check C++11 or C++0x support
include(CheckCXXCompilerFlag)
CHECK_CXX_COMPILER_FLAG("-std=c++11" COMPILER_SUPPORTS_CXX11)
CHECK_CXX_COMPILER_FLAG("-std=c++0x" COMPILER_SUPPORTS_CXX0X)
if(COMPILER_SUPPORTS_CXX11)
   set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")
   add_definitions(-DCOMPILEDWITHC11)
   message(STATUS "Using flag -std=c++11.")
elseif(COMPILER_SUPPORTS_CXX0X)
   set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++0x")
   add_definitions(-DCOMPILEDWITHC0X)
   message(STATUS "Using flag -std=c++0x.")
else()
   message(FATAL_ERROR "The compiler ${CMAKE_CXX_COMPILER} has no C++11 support. Please use a different C++ compiler.")
endif()

LIST(APPEND CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/cmake_modules)
find_package( OpenCV REQUIRED )
find_package(Eigen3 3.1.0 REQUIRED)
find_package(Pangolin REQUIRED)

include_directories(
${OpenCV_INCLUDE_DIRS}
/home/slumber/Repos/ORB_SLAM2
/home/slumber/Repos/ORB_SLAM2/include
${EIGEN3_INCLUDE_DIR}
${Pangolin_INCLUDE_DIRS}
)

#add_library( ORB_SLAM2 STATIC IMPORTED )
#set_target_properties( ORB_SLAM2 PROPERTIES IMPORTED_LOCATION /home/slumber/Repos/ORB_SLAM2/lib/libORB_SLAM2.so )


add_executable( DeviceTracking DeviceTracking.cpp )
target_link_libraries( ${PROJECT_NAME}
  seasocks
  /home/slumber/Repos/ORB_SLAM2/lib/libORB_SLAM2.so
  ${OpenCV_LIBS}
  ${EIGEN3_LIBS}
  ${Pangolin_LIBRARIES}
  /home/slumber/Repos/ORB_SLAM2/Thirdparty/DBoW2/lib/libDBoW2.so
  /home/slumber/Repos/ORB_SLAM2/Thirdparty/g2o/lib/libg2o.so
)
add_executable( WSImageTest WSImageTest.cpp )
target_link_libraries( WSImageTest
  seasocks
  ${OpenCV_LIBS}
)
