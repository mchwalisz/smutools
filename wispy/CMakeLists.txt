cmake_minimum_required(VERSION 2.8)
project(wispy)


include(ExternalProject)
ExternalProject_Add(
	spectools
	SOURCE_DIR spectools
	BINARY_DIR spectools
	CONFIGURE_COMMAND <SOURCE_DIR>/configure
	BUILD_COMMAND $(MAKE)
	INSTALL_COMMAND ""
)
ExternalProject_Add_Step(spectools "'spectool_raw' target check"
	COMMAND grep spectool_raw config.log
	DEPENDEES configure
	DEPENDERS build
	WORKING_DIRECTORY <SOURCE_DIR>
)

install(FILES spectools/pkg-hildon/etc/udev/rules.d/99-wispy.rules DESTINATION /etc/udev/rules.d/)

add_custom_target(wispy ALL
	COMMAND ${PYTHON_EXECUTABLE} -m compileall wispy.py
)
add_dependencies(wispy spectools)
