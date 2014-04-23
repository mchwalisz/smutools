cmake_minimum_required(VERSION 2.8)
project(smutools)


find_package(PythonInterp REQUIRED)
include(find_python_module.cmake)
find_python_module(docopt REQUIRED)

add_custom_target(smut ALL
	COMMAND ${PYTHON_EXECUTABLE} -m compileall smut.py
)

add_subdirectory(smuts_gui)
add_subdirectory(wispy)
add_dependencies(smut wispy smuts_gui)

add_custom_target(
	crewcdf_toolbox
	COMMAND git submodule update --init
)
add_dependencies(smut crewcdf_toolbox)
