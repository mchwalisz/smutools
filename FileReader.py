#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Foobar.py: Description of what foobar does."""

__author__ = "Mikolaj Chwalisz"
__copyright__ = "Copyright (c) 2013, Technische Universität Berlin"
__version__ = "1.0.0"
__email__ = "chwalisz@tkn.tu-berlin.de"

import numpy as np
import logging


class FileReader():

    def __init__(self, fileName):
        self.fileName = fileName
        self.log = logging.getLogger("measurement.FileReader")
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
        self.sweepAvg = 10 * np.log10(np.average(self.sweepPowers, 0))
        self.sweepMax = 10 * np.log10(np.amax(self.sweepPowers, 0))
        self.sweepMin = 10 * np.log10(np.amin(self.sweepPowers, 0))

    # def getData(self)

    def getLineFast(self):
        try:
            fileWhere = self.fileData.tell()
            line = self.fileData.readline()
        except Exception, e:
            self.log.error(e)
            return
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
        self.sweepCurrent = np.array(data)
        if self.sweepAll is None:
            self.sweepAll = np.array(data)
            self.sweepPowers = np.power(10, (np.array(data) / 10))
            self.timeStart = timeStamp
            self.timeStamp = timeStamp - self.timeStart
        else:
            self.sweepAll = np.vstack(
                [self.sweepAll, self.sweepCurrent])
            self.sweepPowers = np.vstack(
                [self.sweepPowers, np.power(10, self.sweepCurrent / 10)])
            self.timeStamp = np.vstack(
                [self.timeStamp, timeStamp - self.timeStart])
            while self.timeStamp[-1] - self.timeStamp[0] > self.historySize:
                self.sweepAll = np.delete(self.sweepAll, 0, 0)
                self.sweepPowers = np.delete(self.sweepPowers, 0, 0)
                self.timeStamp = np.delete(self.timeStamp, 0, 0)
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
            frequencyList = np.linspace(
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

    def closeFile(self):
        self.fileData.close()
        self.log.debug("Closing file: %s" % (self.fileName))

    # def closeFile

# class FileReader


def main(args):
    log = logging.getLogger("measurement")
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)
    pfr = FileReader("/home/chwalisz/" +
        "Code/tkncrew.git/code/sensing_wrapper/" +
        "data_wispy_0_0.txt")
    print(pfr.frequencyList)
    while not pfr.fileEnd:
        pfr.getData()
    print(pfr.sweepCurrent)
    pfr.closeFile()
    pfr.getData()


# def main

if __name__ == '__main__':
    import sys
    main(sys.argv)
