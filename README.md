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
    
        pip install docopt==0.6.1
2. Telos
    - TinyOS
3. Wispy
    - spectools (included but not compiled)
4. RS FSV
5. SMUTS_gui

        sudo apt-get install python-pyside python-matplotlib

# Development

Subtrees:

    git remote add spectools git@bitbucket.org:chwalisz/spectools.git
    git subtree add --prefix wispy/spectools spectools master
    git subtree pull --prefix wispy/spectools spectools master
    
    git remote add specmonapp git@bitbucket.org:chwalisz/specmonapp.git
    git subtree add --prefix telos/specmonapp specmonapp master
    git subtree pull --prefix telos/specmonapp specmonapp master

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
