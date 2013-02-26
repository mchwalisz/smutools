#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Foobar.py: Description of what foobar does."""

__author__ = "Mikolaj Chwalisz"
__copyright__ = "Copyright (c) 2013, Technische Universität Berlin"
__version__ = "1.0.0"
__email__ = "chwalisz@tkn.tu-berlin.de"

from PyQt4.Qwt5.anynumpy import *
import logging


class PlotFileReader():

    def __init__(self, fileName):
        self.fileName = fileName
        self.log = logging.getLogger("measurement.PlotFileReader")
        self.log.info(self.fileName)
        self.fileData = open(self.fileName)
        while self.frequencyList is None:
            self.getLineFast()

    # def __init__

    sweepCurrent = None
    sweepAll = None
    sweepPowers = None
    sweepAvg = None
    sweepMax = None
    sweepMin = None
    frequencyList = None
    fileEnd = False
    timeStamp = None
    timeStart = None
    historySize = 30  # Seconds

    def getData(self):
        while self.sweepCurrent is None:
            self.getLineFast()
        self.getLineFast()
        self.sweepAvg = 10 * log10(average(self.sweepPowers, 0))
        self.sweepMax = 10 * log10(amax(self.sweepPowers, 0))
        self.sweepMin = 10 * log10(amin(self.sweepPowers, 0))

    # def getData(self)

    def getLineFast(self):
        fileWhere = self.fileData.tell()
        line = self.fileData.readline()
        # Check for new line
        if (not line) or (not line.endswith('\n')):
            self.fileData.seek(fileWhere)
            self.fileEnd = True
            return
        line = line.strip()
        # Check for comment in the line
        if line.startswith('#'):
            # Check for existing frequency list
            if self.frequencyList is None:
                self.detectFrequencyList(line)
            return
        tokens = line.split(' ')
        data = map(float, tokens)
        if self.dataSource == "WiSpy":
            timeStamp = float('%d.%d' % (data[0], data[1]))
        elif self.dataSource == "Telos":
            timeStamp = data[0]
        else:
            timeStamp = None
        # Remove timeStamp
        while data[0] > 0:
            del data[0]
        if len(data) != len(self.frequencyList):
            self.log.warning("Wrong data length, skipping")
            return
        self.sweepCurrent = array(data)
        if self.sweepAll is None:
            self.sweepAll = array(data)
            self.sweepPowers = power(10, (array(data) / 10))
            self.timeStart = timeStamp
            self.timeStamp = timeStamp - self.timeStart
        else:
            self.sweepAll = vstack(
                [self.sweepAll, self.sweepCurrent])
            self.sweepPowers = vstack(
                [self.sweepPowers, power(10, self.sweepCurrent / 10)])
            self.timeStamp = vstack(
                [self.timeStamp, timeStamp - self.timeStart])
            while self.timeStamp[-1] - self.timeStamp[0] > self.historySize:
                self.sweepAll = delete(self.sweepAll, 0, 0)
                self.sweepPowers = delete(self.sweepPowers, 0, 0)
                self.timeStamp = delete(self.timeStamp, 0, 0)
        self.fileEnd = False

    # def getLineFast

    def goToEnd(self):
        while not self.fileEnd:
            self.getLineFast()
        # self.fileData.seek(0, 2)
        # self.sweepAll = self.sweepAll[-1:]
        # self.sweepPowers = self.sweepPowers[-1:]

    def detectFrequencyList(self, line):
        import re
        line = line.lstrip("#").lstrip()
        # Detect WiSpy
        restr = ("(?P<start>\d+)MHz-(?P<stop>\d+)MHz" +
            " @ (?P<rbw>\d+\.?\d*)KHz, (?P<samples>\d+) samples")
        p = re.compile(restr)
        m = p.match(line)
        if m:
            frequencyList = linspace(
                float(m.group('start')),
                float(m.group('stop')),
                int(m.group('samples')))
            self.frequencyList = frequencyList
            self.dataSource = "WiSpy"
            self.log.info("Detected WiSpy type Frequency list")
        # Detect Telos
        try:
            line = line.lstrip("Frequencies (in MHz): ")
            line = line.split(',')
            frequencyList = map(float, line)
            self.frequencyList = frequencyList
            self.dataSource = "Telos"
            self.log.info("Detected Telos type Frequency list")
        except:
            pass

    # def detectFrequencyList(...)

# class PlotFileReader
