cmake_minimum_required(VERSION 2.8)
project(smutools)


find_package(PythonInterp REQUIRED)

add_subdirectory(smuts_gui)
add_subdirectory(wispy)

add_custom_target(smut ALL
	COMMAND ${PYTHON_EXECUTABLE} -m compileall smut.py
)
add_dependencies(smut wispy smuts_gui)
