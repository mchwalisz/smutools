#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""WiSpyMonitor.py: Description of what foobar does."""

__author__ = "Mikolaj Chwalisz"
__copyright__ = "Copyright (c) 2013, Technische Universität Berlin"
__version__ = "1.0.0"
__email__ = "chwalisz@tkn.tu-berlin.de"

from PyQt4 import QtCore, QtGui, Qt
from WiSpyMonitorGUI import Ui_WiSpyMonitorMain
import PyQt4.Qwt5 as Qwt
from PyQt4.Qwt5.anynumpy import *

import random




class WiSpyMainWindow(QtGui.QMainWindow, Ui_WiSpyMonitorMain):
    def __init__(self, parent=None):
        super(WiSpyMainWindow, self).__init__(parent)
        self.setupUi(self)
        # connect myaction_logic to myaction.toggled signal
        # self.myaction.toggled.connect(self.myaction_slot)

    def WiSpyStart(self):
        print "WiSpyStart"

    def WiSpyStop(self):
        print "WiSpyStop"
        self.qwtPlotSpectrogram.setCanvasBackground(Qt.Qt.white)

    def WiSpyTest(self):
        print "WiSpyTest"
        self.qwtPlotSpectrogram.setCanvasBackground(Qt.Qt.red)


def main(args):
    app = QtGui.QApplication(args)
    MainWindow = WiSpyMainWindow()
    MainWindow.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    import sys
    main(sys.argv)
