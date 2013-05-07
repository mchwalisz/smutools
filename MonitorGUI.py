#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MonitorGUI.py: Description of what foobar does.

Usage:
  MonitorGUI.py [options] [--quiet | --verbose]

Other options:
  -q, --quiet               print less text
  -v, --verbose             print more text
  -h, --help                show this help message and exit
  --version                 show version and exit
"""

__author__ = "Mikolaj Chwalisz"
__copyright__ = "Copyright (c) 2013, Technische Universität Berlin"
__version__ = "1.0.0"
__email__ = "chwalisz@tkn.tu-berlin.de"

import logging
from time import gmtime, strftime
import sys
try:
    from PySide import QtCore, QtGui
    from tools import MonitorMainUI
    from tools import FileReader
    from tools import PlotPower
    from tools import PlotSpectrogram
except:
    print """
    Requirements installation (on ubuntu):
    sudo apt-get install python-pyside python-matplotlib
    """
    raise


class MonitorMainWindow(QtGui.QMainWindow, MonitorMainUI.Ui_MonitorMainUI):
    def __init__(self, parent=None):
        super(MonitorMainWindow, self).__init__(parent)
        self.setupUi(self)
        self.log = logging.getLogger("measurement.MonitorGUI")
        # connect myaction_logic to myaction.toggled signal
        # self.myaction.toggled.connect(self.myaction_slot)
        #self.verticalLayout_2.removeWidget()
        self.qwtPlotPower = PlotPower.PlotPower(self.centralwidget)
        self.qwtPlotPower.setMinimumSize(QtCore.QSize(610, 250))
        #self.verticalPlts.removeWidget(self.)
        self.verticalPlts.addWidget(self.qwtPlotPower)
        self.labelPlotPower.close()

        self.qwtPlotSpectrogram = PlotSpectrogram.PlotSpectrogram(self.centralwidget)
        self.qwtPlotSpectrogram.setMinimumSize(QtCore.QSize(610, 250))
        self.verticalPlts.addWidget(self.qwtPlotSpectrogram)
        self.labelPlotSpectrogram.close()

        #self.timerID = self.startTimer(20)
        self.hSliderTimer.setValue(300)
        self.hSliderHistory.setValue(30)

        self.actionOpen.triggered.connect(self.actionOpen_slot)

    timerID = None
    fileReader = None

    def WiSpyStart(self):
        self.log.debug("WiSpyStart")
        if self.fileReader is None:
            self.log.warning("No file opened")
        if self.timerID is None:
            self.timerID = self.startTimer(self.hSliderTimer.value())

    def WiSpyStop(self):
        self.log.debug("WiSpyStop")
        if self.timerID is not None:
            self.killTimer(self.timerID)
        self.timerID = None

    def WiSpyTest(self):
        self.log.debug("WiSpyTest")
        self.openFile("/home/chwalisz/Dropbox/Projects/pyTools/measurement/data_wispy_0_0.txt")
        self.log.debug(self.fileReader.timeStamp[-1] - self.fileReader.timeStamp[0])

    def WiSpyGoToEnd(self):
        self.log.debug("WiSpyGoToEnd")
        self.fileReader.goToEnd()

    def timerEvent(self, e):
        if self.fileReader is None:
            return
        else:
            self.fileReader.getData()
        if not self.fileReader.fileEnd:
            self.qwtPlotPower.updatePlot(self.fileReader)
            self.qwtPlotSpectrogram.updatePlot(self.fileReader)
        self.checkBoxEoF.setChecked(self.fileReader.fileEnd)
        self.labelHistorySize.setNum(self.fileReader.timeStamp[-1] - self.fileReader.timeStamp[0])
        self.labelDpS.setText("%f" %
            (len(self.fileReader.timeStamp)/(self.fileReader.timeStamp[-1] - self.fileReader.timeStamp[0])))

    def setTimer(self, val):
        # self.log.debug("setTimer val = %i" % (val))
        if self.timerID is not None:
            self.killTimer(self.timerID)
            self.timerID = self.startTimer(val)

    def setHistorySize(self, val):
        # self.log.debug("setHistorySize val = %i" % (val))
        if self.fileReader is not None:
            self.fileReader.historySize = val

    # def setHistorySize

    def closeEvent(self, e):
        self.log.debug("Exit registered")
        if self.timerID is not None:
            self.killTimer(self.timerID)
        if self.fileReader is not None:
            self.fileReader.closeFile()
    # def close

    def actionOpen_slot(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open file')[0]
        self.log.debug("Selected file: %s" % filename)
        self.openFile(filename)

    # def actionOpen

    def openFile(self, filename):
        if len(filename) > 21:
            self.labelFileName.setText("...%s" % filename[-21:])
        else:
            self.labelFileName.setText(filename)
        if self.timerID is not None:
            self.killTimer(self.timerID)
        if self.fileReader is not None:
            self.fileReader.closeFile()
        self.fileReader = FileReader.FileReader(filename)
        self.fileReader.historySize = self.hSliderHistory.value()
        self.labelTimeStart.setText(strftime("%Y-%m-%d %H:%M:%S", gmtime(self.fileReader.timeStart)))

    # def openFile


def main(sargs):
    app = QtGui.QApplication(sys.argv)
    MainWindow = MonitorMainWindow()
    MainWindow.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        from docopt import docopt
    except:
        print """
        Please install docopt using:
          pip install docopt==0.6.1
        For more refer to:
        https://github.com/docopt/docopt
        """
        raise

    dargs = docopt(__doc__, version=__version__)

    log = logging.getLogger('measurement')
    log.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    log_level = logging.INFO  # default
    if dargs['--verbose']:
        log_level = logging.DEBUG
    elif dargs['--quiet']:
        log_level = logging.ERROR
    ch.setLevel(log_level)
    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)
    main(dargs)
