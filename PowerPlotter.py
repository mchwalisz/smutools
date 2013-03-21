#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""PowerPlotter.py: Description of what foobar does."""

__author__ = "Mikolaj Chwalisz"
__copyright__ = "Copyright (c) 2013, Technische Universität Berlin"
__version__ = "1.0.0"
__email__ = "chwalisz@tkn.tu-berlin.de"

import numpy as np
import matplotlib

matplotlib.rcParams['backend.qt4'] = 'PySide'
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import logging


class PowerPlotter(FigureCanvas):
    """docstring for PowerPlotter"""
    def __init__(self, *args):
        self.figure = Figure()
        FigureCanvas.__init__(self, self.figure)
        self.axes = self.figure.add_subplot(111)
        self.curveCurrent, = self.axes.plot([], [], label="Current")
        self.curveAvg, = self.axes.plot([], [], label="Average")
        self.curveMax, = self.axes.plot([], [], label="Maximum")
        self.curveMin, = self.axes.plot([], [], label="Minimum")
        leg = self.axes.legend(loc='upper right', bbox_to_anchor=(1.1, 1))
        frame = leg.get_frame()
        frame.set_facecolor('0.95')    # set the frame face color to light gray
        for t in leg.get_texts():
            t.set_fontsize('x-small')    # the legend text fontsize
        self.axes.autoscale(enable=False, axis='both')
        self.figure.canvas.draw()

        self.log = logging.getLogger("measurement.PowerPlotter")

    # __init__()

    dBmMin = float("Inf")
    dBmMax = -float("Inf")

    def updatePlot(self, fReader):
        if fReader.sweepCurrent is None:
            self.log.warning("Missing data to plot")
            return
        if fReader.frequencyList is None:
            self.log.warning("Missing frequency list")
            freqList = range(fReader.sweepCurrent.shape[0])
        else:
            freqList = fReader.frequencyList
        # Update scale
        self.dBmMin = min(np.nanmin(fReader.sweepMin), self.dBmMin)
        self.dBmMax = max(np.nanmax(fReader.sweepMax), self.dBmMax)
        self.axes.set_ylim([self.dBmMin, self.dBmMax])
        self.axes.set_xlim([freqList[0], freqList[-1]])
        self.curveCurrent.set_data(freqList, fReader.sweepCurrent)
        self.curveAvg.set_data(freqList, fReader.sweepAvg)
        self.curveMax.set_data(freqList, fReader.sweepMax)
        self.curveMin.set_data(freqList, fReader.sweepMin)
        self.figure.canvas.draw()

# class PowerPlotter
