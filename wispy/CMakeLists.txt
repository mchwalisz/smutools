cmake_minimum_required(VERSION 2.8)
project(wispy)


include(ExternalProject)
ExternalProject_Add(
	spectools
	SOURCE_DIR spectools
	BINARY_DIR spectools
	CONFIGURE_COMMAND <SOURCE_DIR>/configure
	BUILD_COMMAND make
	INSTALL_COMMAND ""
)
ExternalProject_Add_Step(spectools "target check"
	COMMAND cat config.log | grep spectool_raw
	DEPENDEES configure
	DEPENDERS build
	WORKING_DIRECTORY <SOURCE_DIR>
)

install(FILES spectools/pkg-hildon/etc/udev/rules.d/99-wispy.rules DESTINATION /etc/udev/rules.d/)

add_custom_target(wispy ALL
	COMMAND ${PYTHON_EXECUTABLE} -m compileall wispy.py
)
add_dependencies(wispy spectools)
