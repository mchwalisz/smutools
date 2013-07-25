#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""PlotSpectrogram.py: Spectrogram back-end
"""

__author__ = "Mikolaj Chwalisz"
__copyright__ = "Copyright (c) 2013, Technische Universität Berlin"
__version__ = "1.0.0"
__email__ = "chwalisz@tkn.tu-berlin.de"

try:
    import matplotlib
    from PySide import QtCore
    matplotlib.rcParams['backend.qt4'] = 'PySide'
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
    import matplotlib.cm as cm
except:
    print """
    Requirements installation (on ubuntu):
    sudo apt-get install python-numpy python-pyside python-matplotlib
    """
    raise
import logging
import time


class PlotSpectrogram(FigureCanvas):
    """docstring for PlotSpectrogram"""
    def __init__(self, *args):
        self.figure = Figure()
        FigureCanvas.__init__(self, self.figure)
        self.axes = self.figure.add_subplot(111)
        self.log = logging.getLogger("measurement.PlotSpectrogram")

    # __init__()

    dBmMin = float("Inf")
    dBmMax = -float("Inf")
    image = None

    def updatePlot(self, fReader):
        if fReader.sweepCurrent is None:
            self.log.warning("Missing data to plot")
            return
        if fReader.frequencyList is None:
            self.log.warning("Missing frequency list")
            freqList = range(fReader.sweepCurrent.shape[0])
        else:
            freqList = fReader.frequencyList
        t0 = time.time() - (fReader.timeStart + fReader.timeStamp[-1])
        t1 = time.time() - (fReader.timeStart + fReader.timeStamp[0])
        if self.image is None:
            self.image = self.axes.matshow(fReader.sweepAll, cmap=cm.jet,
                                           animated=True, aspect="auto",
                                           extent=[freqList[0], freqList[-1], t0, t1])
            self.figure.colorbar(self.image)
        else:
            self.image.set_extent([freqList[0], freqList[-1], t0, t1])
            self.image.set_data(fReader.sweepAll)
            self.image.autoscale()
        self.figure.canvas.draw()

    # def updatePlot

    def initUI(self):
        self.setMinimumSize(QtCore.QSize(610, 250))

    # def initUI

# class PlotSpectrogram
