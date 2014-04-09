# SMUTools - Spectrum MeasUrement Tools

Python scripts that aim to help running spectrum sensing experiments.

There are tools for different device types like:

- WiSpy
- TelosB with spectrum sensing application
- Rohde & Schwarz FSV Spectrum Analyser


# Installation

1. General tools:

        sudo apt-get install python-pip build-essential libusb-dev pyside-tools python-pyside python-matplotlib cmake
        sudo pip install docopt==0.6.1

2. Compile:

        cmake .
        make
        sudo make install


# Usage

The main script is called `smut.py`.
It will run spectrum sensing applications on all possible (connected) devices.
For further documentation refer to `./smut.py --help`.

Additionally to the smutools there is `crewcdf_toolbox` for processing the data.
To LOAD the toolbox run `crewcdf_toolbox_load.m` in Matlab.
Then it is possible to run  `crewcdf_plotall()` to generate summary plots for all data in given directory and its subdirectories.

## Telos devices

Do not forget to load TinyOS

    source /opt/tinyos-main/tinyos.sh
