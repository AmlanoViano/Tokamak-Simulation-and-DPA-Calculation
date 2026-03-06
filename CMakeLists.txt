cmake_minimum_required(VERSION 3.16)
project(TokamakNeutronSim)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Geant4 REQUIRED ui_all vis_all)
include(${Geant4_USE_FILE})

find_package(cadmesh REQUIRED)

include_directories(
    ${PROJECT_SOURCE_DIR}/include
    ${Geant4_INCLUDE_DIRS}
    /home/amlan-halder/CADMesh/include
)

file(GLOB sources ${PROJECT_SOURCE_DIR}/src/*.cc)
file(GLOB headers ${PROJECT_SOURCE_DIR}/include/*.hh)

add_executable(tokamak_sim tokamak_sim.cc ${sources})

target_link_libraries(tokamak_sim
    ${Geant4_LIBRARIES}
    cadmesh
)

file(COPY ${PROJECT_SOURCE_DIR}/macros DESTINATION ${PROJECT_BINARY_DIR})
file(COPY ${PROJECT_SOURCE_DIR}/geometry DESTINATION ${PROJECT_BINARY_DIR})