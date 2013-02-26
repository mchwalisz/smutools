#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""PowerPlotter.py: Description of what foobar does."""

__author__ = "Mikolaj Chwalisz"
__copyright__ = "Copyright (c) 2013, Technische Universität Berlin"
__version__ = "1.0.0"
__email__ = "chwalisz@tkn.tu-berlin.de"

from PyQt4 import Qt
import PyQt4.Qwt5 as Qwt
from PyQt4.Qwt5.anynumpy import *


class PowerPlotter(Qwt.QwtPlot):
    """docstring for PowerPlotter"""
    def __init__(self, *args):
        Qwt.QwtPlot.__init__(self, *args)

        self.setCanvasBackground(Qt.Qt.white)
        self.alignScales()

        self.setTitle("Power Spectrum Density")
        self.insertLegend(Qwt.QwtLegend(), Qwt.QwtPlot.BottomLegend)

        self.curveCurrent = Qwt.QwtPlotCurve("Current")
        self.curveCurrent.attach(self)
        self.curveCurrent.setPen(Qt.QPen(Qt.Qt.red))

        self.curveAvg = Qwt.QwtPlotCurve("Average")
        self.curveAvg.attach(self)
        self.curveAvg.setPen(Qt.QPen(Qt.Qt.blue))

        self.curveMin = Qwt.QwtPlotCurve("Minimum")
        self.curveMin.attach(self)
        self.curveMin.setPen(Qt.QPen(Qt.Qt.magenta))

        self.curveMax = Qwt.QwtPlotCurve("Maximum")
        self.curveMax.attach(self)
        self.curveMax.setPen(Qt.QPen(Qt.Qt.green))

        # self.curveL.setSymbol(Qwt.QwtSymbol(Qwt.QwtSymbol.Ellipse,
        #                                 Qt.QBrush(),
        #                                 Qt.QPen(Qt.Qt.yellow),
        #                                 Qt.QSize(7, 7)))
        # mY = Qwt.QwtPlotMarker()
        # mY.setLabelAlignment(Qt.Qt.AlignRight | Qt.Qt.AlignTop)
        # mY.setLineStyle(Qwt.QwtPlotMarker.HLine)
        # mY.setYValue(0.0)
        # mY.attach(self)

        self.setAxisTitle(Qwt.QwtPlot.xBottom, "Frequency")
        self.setAxisTitle(Qwt.QwtPlot.yLeft, "Power")

    # __init__()

    dBmMin = float("Inf")
    dBmMax = -float("Inf")

    def alignScales(self):
        self.canvas().setFrameStyle(Qt.QFrame.Box | Qt.QFrame.Plain)
        self.canvas().setLineWidth(1)
        for i in range(Qwt.QwtPlot.axisCnt):
            scaleWidget = self.axisWidget(i)
            if scaleWidget:
                scaleWidget.setMargin(0)
            scaleDraw = self.axisScaleDraw(i)
            if scaleDraw:
                scaleDraw.enableComponent(
                    Qwt.QwtAbstractScaleDraw.Backbone, False)

    # alignScales()

    def updatePlot(self, fReader):
        if fReader.sweepCurrent is None:
            print("Missing value")
            return
        if fReader.frequencyList is None:
            freqList = range(fReader.sweepCurrent.shape[0])
        else:
            freqList = fReader.frequencyList
        # Update scale
        self.setAxisScale(Qwt.QwtPlot.xBottom, freqList[0], freqList[-1])
        self.dBmMin = min(nanmin(fReader.sweepMin), self.dBmMin)
        self.dBmMax = max(nanmax(fReader.sweepMax), self.dBmMax)
        self.setAxisScale(Qwt.QwtPlot.yLeft, self.dBmMin, self.dBmMax)
        self.curveCurrent.setData(freqList, fReader.sweepCurrent)
        self.curveAvg.setData(freqList, fReader.sweepAvg)
        self.curveMax.setData(freqList, fReader.sweepMax)
        self.curveMin.setData(freqList, fReader.sweepMin)
        self.replot()

# class PowerPlotter
