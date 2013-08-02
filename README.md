# SMUTS - Spectrum MeasUrement ToolS

Python scripts that aim to help running spectrum sensing experiments.

There are tools for different device types like:

- WiSpy
- TelosB with spectrum sensing application
- Rohde & Schwarz FSV Spectrum Analyser

# Running

## Telos

Do not forget to load TinyOS

    source /opt/tinyos-main/tinyos.sh


# Installation

1. General tools:

        sudo apt-get install pip build-essential libusb-dev
        pip install docopt==0.6.1
2. Telos
    - TinyOS
3. Wispy
    - spectools (included but not compiled)
    - compile with

            cd wispy/spectools
            ./configure
            make
            cd ../..
    - add udev rules

            sudo cp wispy/spectools/pkg-hildon/etc/udev/rules.d/99-wispy.rules /etc/udev/rules.d/99-wispy.rules
4. RS FSV
5. SMUTS_gui

        sudo apt-get install python-pyside python-matplotlib scons
        cd smuts_gui
        scons

# Development

Subtrees:

    git remote add spectools git@bitbucket.org:chwalisz/spectools.git
    git subtree add --prefix wispy/spectools spectools master

    git remote add specmonapp git@bitbucket.org:chwalisz/specmonapp.git
    git subtree add --prefix telos/specmonapp specmonapp master

The command to update the sub-project at a later date becomes:

    git fetch spectools master
    git subtree pull --prefix wispy/spectools spectools master

    git fetch specmonapp master
    git subtree pull --prefix telos/specmonapp specmonapp master

Now we can use the subtree push command like the following:

    git subtree push --prefix wispy/spectools spectools master

    git subtree push --prefix telos/specmonapp specmonapp master


## GUI update

Run:

    cd smuts_gui
    scons
