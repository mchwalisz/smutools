#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""WiSpyMonitor.py: Description of what foobar does."""

__author__ = "Mikolaj Chwalisz"
__copyright__ = "Copyright (c) 2013, Technische Universität Berlin"
__version__ = "1.0.0"
__email__ = "chwalisz@tkn.tu-berlin.de"

from PyQt4 import QtCore, QtGui, Qt, uic
import logging
import PowerPlotter
import PlotFileReader
import SpectrogramPlotter


class WiSpyMainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(WiSpyMainWindow, self).__init__(parent)
        uic.loadUi("WiSpyMonitorGUI.ui", self)
        self.log = logging.getLogger("measurement.WiSpyMonitor")
        # connect myaction_logic to myaction.toggled signal
        # self.myaction.toggled.connect(self.myaction_slot)
        #self.verticalLayout_2.removeWidget()
        self.qwtPlotPower = PowerPlotter.PowerPlotter(self.centralwidget)
        self.qwtPlotPower.setMinimumSize(QtCore.QSize(610, 250))
        #self.verticalPlts.removeWidget(self.)
        self.verticalPlts.addWidget(self.qwtPlotPower)
        self.labelPlotPower.close()

        self.qwtPlotSpectrogram = SpectrogramPlotter.SpectrogramPlotter(self.centralwidget)
        self.qwtPlotSpectrogram.setMinimumSize(QtCore.QSize(610, 250))
        self.verticalPlts.addWidget(self.qwtPlotSpectrogram)
        self.labelPlotSpectrogram.close()

        self.fileReader = PlotFileReader.PlotFileReader("/home/chwalisz/" +
            "Code/tkncrew.git/code/sensing_wrapper/" +
            "data_wispy_0_0.txt")

        #self.timerID = self.startTimer(20)
        self.hSliderTimer.setValue(300)

    timerID = None

    def WiSpyStart(self):
        self.log.debug("WiSpyStart")

    def WiSpyStop(self):
        self.log.debug("WiSpyStop")

    def WiSpyTest(self):
        self.log.debug("WiSpyTest")
        self.log.debug(self.fileReader.timeStamp[-1] - self.fileReader.timeStamp[0])

    def WiSpyGoToEnd(self):
        self.log.debug("WiSpyGoToEnd")
        self.fileReader.goToEnd()

    def timerEvent(self, e):
        self.fileReader.getData()
        if not self.fileReader.fileEnd:
            self.qwtPlotPower.updatePlot(self.fileReader)
        self.checkBoxEoF.setChecked(self.fileReader.fileEnd)
        self.labelHistorySize.setNum(self.fileReader.timeStamp[-1] - self.fileReader.timeStamp[0])

    def setTimer(self, val):
        self.log.debug("setTimer val = %i" % (val))
        if self.timerID is not None:
            self.killTimer(self.timerID)
        if val == 0:
            self.timerID = None
        else:
            self.timerID = self.startTimer(val)

    def setHistorySize(self, val):
        self.log.debug("setHistorySize val = %i" % (val))
        self.fileReader.historySize = val

    # def setHistorySize


def main(args):
    log = logging.getLogger("measurement")
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)
    app = QtGui.QApplication(args)
    MainWindow = WiSpyMainWindow()
    MainWindow.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    import sys
    main(sys.argv)
