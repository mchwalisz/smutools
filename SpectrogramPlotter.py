#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""SpectrogramPlotter.py: Description of what foobar does."""

__author__ = "Mikolaj Chwalisz"
__copyright__ = "Copyright (c) 2013, Technische Universität Berlin"
__version__ = "1.0.0"
__email__ = "chwalisz@tkn.tu-berlin.de"

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.cm as cm
import logging
import time


class SpectrogramPlotter(FigureCanvas):
    """docstring for SpectrogramPlotter"""
    def __init__(self, *args):
        self.figure = Figure()
        FigureCanvas.__init__(self, self.figure)
        self.axes = self.figure.add_subplot(111)
        self.log = logging.getLogger("measurement.SpectrogramPlotter")

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
        self.dBmMin = min(np.nanmin(fReader.sweepMin), self.dBmMin)
        self.dBmMax = max(np.nanmax(fReader.sweepMax), self.dBmMax)
        if self.image is None:
            self.image = self.axes.matshow(fReader.sweepAll, cmap=cm.spectral,
                                           vmax=self.dBmMax, vmin=self.dBmMin,
                                           animated=True, aspect="auto",
                                           extent=[freqList[0], freqList[-1], 0, 10])
        else:
            self.image.set_data(fReader.sweepAll)
            t0 = time.time() - (fReader.timeStart + fReader.timeStamp[-1])
            t1 = time.time() - (fReader.timeStart + fReader.timeStamp[0])
            self.image.set_extent([freqList[0], freqList[-1], t0, t1])
        self.figure.canvas.draw()

    # def updatePlot


# class SpectrogramPlotter
