#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Foobar.py: Description of what foobar does."""

__author__ = "Mikolaj Chwalisz"
__copyright__ = "Copyright (c) 2013, Technische Universität Berlin"
__version__ = "1.0.0"
__email__ = "chwalisz@tkn.tu-berlin.de"

import numpy as np
import logging
import re
import struct


def FileReaderLoader(fileName):
    supported_types = {
        'telos': FileReaderTelos,
        'wispy': FileReaderWiSpy,
        'fsv': FileReaderFsv}
    log = logging.getLogger("sensing.FileReaderLoader")
    for type in supported_types:
        if type in fileName:
            log.info("Loading %s" % type)
            return supported_types[type](fileName)
# def FileReaderLoader


class FileReader():
    def __init__(self, fileName):
        self.fileName = fileName
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

    def goToEnd(self):
        while not self.fileEnd:
            self.getLineFast()
    # def goToEnd

    def closeFile(self):
        self.fileData.close()
        self.log.debug("Closing file: %s" % (self.fileName))
    # def closeFile

# class FileReader


class FileReaderWiSpy(FileReader):
    """docstring for FileReaderWiSpy"""
    def __init__(self, fileName):
        FileReader.__init__(self, fileName)
        self.log = logging.getLogger("sensing.FileReaderWiSpy")
        self.log.info(self.fileName)
        self.fileData = open(self.fileName)
        while self.frequencyList is None:
            self.getLineFast()
    # def __init__

    def detectFrequencyList(self, line):
        line = line.lstrip("#").lstrip()
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
    # def detectFrequencyList

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

        timeStamp = float('%d.%d' % (data[0], data[1]))

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
# class FileReaderWiSpy


class FileReaderTelos(FileReader):
    """docstring for FileReaderTelos"""
    def __init__(self, fileName):
        FileReader.__init__(self, fileName)
        self.log = logging.getLogger("sensing.FileReaderTelos")
        self.log.info(self.fileName)
        self.fileData = open(self.fileName)
        while self.frequencyList is None:
            self.getLineFast()
    # def __init__

    def detectFrequencyList(self, line):
        line = line.lstrip("#").lstrip()
        try:
            line = line.lstrip("Frequencies (in MHz): ")
            line = line.split(',')
            frequencyList = map(float, line)
            self.frequencyList = frequencyList
        except:
            pass
    # def detectFrequencyList

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
        timeStamp = data[0]
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
# class FileReaderTelos


class FileReaderFsv(FileReader):
    """docstring for FileReaderFsv"""
    def __init__(self, fileName):
        FileReader.__init__(self, fileName)
        self.log = logging.getLogger("sensing.FileReaderFsv")
        self.log.info(self.fileName)
        self.fileData = open(self.fileName)
        while self.frequencyList is None:
            self.getLineFast()
    # def __init__

    def detectFrequencyList(self):
        frequencyList = [0]*self.values
        ii = 0
        while ii < len(frequencyList):
            try:
                fileWhere = self.fileData.tell()
                line = self.fileData.readline()
                if (not line) or (not line.endswith('\n')):
                    self.fileData.seek(fileWhere)
                    continue
                line = line.strip()
                line = line.rstrip(';')
                tokens = line.split(';')
                frequencyList[ii] = float(tokens[0])
                ii += 1
            except Exception, e:
                self.log.error(e)
                pass
        self.frequencyList = frequencyList
    # def detectFrequencyList

    meta = False
    metaData = {}

    def getMetaData(self):
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
        line = line.rstrip(';')
        tokens = line.split(';')
        if len(tokens) > 1:
            self.metaData[tokens[0]] = tokens[1]
        if len(tokens) > 2:
            self.metaData['%s_Unit' % tokens[0]] = tokens[2]
        if tokens[0] == 'Values':
            self.values = int(tokens[1])
            self.detectFrequencyList()
        if tokens[0] == 'Binary Format':
            # Have read the whole meta data
            self.chunksize = (64 + self.values * 32)/8
            self.log.debug("Meta Data: %s" % str(self.metaData))
            self.meta = True
    # def getMetaData

    def getLineFast(self):
        if not self.meta:
            self.getMetaData()
            self.fileEnd = False
            return
        try:
            fileWhere = self.fileData.tell()
            bytes_read = self.fileData.read(self.chunksize)
            if len(bytes_read) != self.chunksize:
                self.fileData.seek(fileWhere)
                self.fileEnd = True
                return
        except Exception, e:
            self.log.error(e)
            self.fileEnd = True
            return
        # Parse correct data
        data = struct.unpack('d%if' % self.values, bytes_read)
        timeStamp = data[0]
        self.sweepCurrent = np.array(data[1:])
        if self.sweepAll is None:
            self.sweepAll = np.array(data[1:])
            self.sweepPowers = np.power(10, (np.array(data[1:]) / 10))
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
# class FileReaderFsv


def main(args):
    log = logging.getLogger("sensing")
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)
    pfr = FileReaderLoader("data_fsv_192.168.10.250.fsv")
    print(pfr.frequencyList)
    while not pfr.fileEnd:
        pfr.getData()
    print(pfr.sweepCurrent)
    pfr.closeFile()
    # pfr.getData()
# def main

if __name__ == '__main__':
    import sys
    main(sys.argv)
