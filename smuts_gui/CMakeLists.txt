cmake_minimum_required(VERSION 2.8)
project(smuts_gui)

find_package(PythonInterp REQUIRED)
# PySide-compatible .ui -> .py generation
find_program(PYUIC "pyside-uic")
if(NOT PYUIC)
	message(FATAL_ERROR "pyside-uic not found. On Ubuntu install 'pyside-tools' to get it.")
endif(NOT PYUIC)

find_python_module(PySide.QtGui REQUIRED)

add_custom_command(
	OUTPUT tools/MonitorMainUI.py
	COMMAND ${PYUIC}
		${CMAKE_CURRENT_SOURCE_DIR}/tools/MonitorMainUI.ui >
		${CMAKE_CURRENT_SOURCE_DIR}/tools/MonitorMainUI.py
	DEPENDS tools/MonitorMainUI.ui
)

add_custom_target(MonitorMainUI ALL DEPENDS tools/MonitorMainUI.py)
