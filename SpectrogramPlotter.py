#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""SpectrogramPlotter.py: Description of what foobar does."""

__author__ = "Mikolaj Chwalisz"
__copyright__ = "Copyright (c) 2013, Technische Universität Berlin"
__version__ = "1.0.0"
__email__ = "chwalisz@tkn.tu-berlin.de"

from PyQt4 import Qt
import PyQt4.Qwt5 as Qwt
from PyQt4.Qwt5.anynumpy import *


class SpectrogramData(Qwt.QwtRasterData):
    """docstring for SpectrogramData"""
    def __init__(self):
        Qwt.QwtRasterData.__init__(self, Qt.QRectF(-1.5, -1.5, 3.0, 3.0))

    def copy(self):
        return self

    def range(self):
        return Qwt.QwtDoubleInterval(0.0, 10.0)

    def value(self, x, y):
        c = 0.842
        v1 = x * x + (y - c) * (y + c)
        v2 = x * (y + c) + x * (y + c)
        return 1.0 / (v1 * v1 + v2 * v2)


class SpectrogramPlotter(Qwt.QwtPlot):
    """docstring for SpectrogramPlotter"""
    def __init__(self, *args):
        Qwt.QwtPlot.__init__(self, *args)
        self.spectrogram = Qwt.QwtPlotSpectrogram()
        self.spectrogram.attach(self)

        colorMap = Qwt.QwtLinearColorMap(Qt.Qt.darkCyan, Qt.Qt.red)
        colorMap.addColorStop(0.1, Qt.Qt.cyan)
        colorMap.addColorStop(0.6, Qt.Qt.green)
        colorMap.addColorStop(0.95, Qt.Qt.yellow)

        self.spectrogram.setColorMap(colorMap)

        self.spectrogram.setData(SpectrogramData())

        self.plotLayout().setAlignCanvasToScales(True)

        self.setTitle("Spectrogram")

    # __init__()

    def updatePlot(self, fReader):
        if fReader.sweepCurrent is None:
            print("Missing value")
            return
        if fReader.frequencyList is None:
            freqList = range(fReader.sweepCurrent.shape[0])
        else:
            freqList = fReader.frequencyList
        # Update scale

        self.replot()

# class SpectrogramPlotter
