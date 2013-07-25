
all: sensing_gui.py

gui_UI.py: gui_UI.ui
	pyuic4 gui_UI.ui -o gui_UI.py 

sensing_gui.py: gui_UI.py

clean:
	rm -rf gui_UI.py
	rm -rf *.pyc

.PHONY: all clean
