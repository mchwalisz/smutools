#!/usr/bin/env python
'''
Created on 23-02-2012

@author: Mikolaj Chwalisz
'''
import time
import Gnuplot
import sys
import numpy
import threading


class lplot(threading.Thread):
    '''
    lplot
    '''

    def __init__(self, name, fileName):
        super(lplot, self).__init__(name=name)
        self.fileName = fileName
        self._stop = threading.Event()
        # Analyzer view
        self.gnuPlot = Gnuplot.Gnuplot()
        #self.gnuPlot('set yrange [-130:-40]')
        self.gnuPlot('set grid')
        self.gnuPlot('set terminal x11 noraise')
        self.gnuPlot('set terminal x11 size 400,300')
        self.gnuPlot('set hidden')
        self.gnuPlot('set contour base')
        self.gnuPlot('bind Close "exit gnuplot"')
        self.gnuPlot.title(name)
        self.gnuPlot.xlabel('Frequency [MHz]')
        self.gnuPlot.ylabel('Power [dBm]')
        # Spectrogram view
        self.gnusPlot = Gnuplot.Gnuplot()
        self.gnusPlot('set term x11 noraise')
        self.gnusPlot('set terminal x11 size 400,300')
        self.gnusPlot('set pm3d map')
        self.gnusPlot('set palette color')
        self.gnusPlot('set view map')
        self.gnusPlot('set hidden')
        self.gnusPlot("""set palette defined ( 0 '#000090',\
                      1 '#000fff',\
                      2 '#0090ff',\
                      3 '#0fffee',\
                      4 '#90ff70',\
                      5 '#ffee00',\
                      6 '#ff7000',\
                      7 '#ee0000',\
                      8 '#7f0000')""")
        self.gnusPlot('bind Close "exit gnuplot"')
        self.gnusPlot.title(name)
        self.gnusPlot.xlabel('Time')
        self.gnusPlot.ylabel('Frequency [MHz]')

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    refresh_rate = 1  # second

    def run(self):
        time.sleep(2)
        dataGen = self._getData()
        tstart = time.time() - self.refresh_rate
        #plt.figure()
        #plt.ion()
        while True:
            if not self.gnusPlot.gnuplot and not self.gnuPlot.gnuplot:
                self.stop()
            data, avg, maxval, minval, avglist, freq_list = dataGen.next()
            if self.stopped():
                break
            if (time.time() - tstart) > self.refresh_rate:
                tstart = time.time()
                try:
                    gpdata = Gnuplot.Data(freq_list, data, title='Current', with_='lines')
                    gpavg = Gnuplot.Data(freq_list, avg, title='Average', with_='lines')
                    gpminval = Gnuplot.Data(freq_list, minval, title='Min hold', with_='lines')
                    gpmaxval = Gnuplot.Data(freq_list, maxval, title='Max hold', with_='lines')
                #g('set data style linespoints')
                    self.gnuPlot('set xrange [{0}:{1}]'.format(int(freq_list[0]), int(freq_list[-1])))
                    self.gnuPlot.plot(gpdata, gpavg, gpminval, gpmaxval)
                except:
                    self.gnuPlot.close()
                try:
                    gpavglist = Gnuplot.GridData(avglist, range(avglist.shape[0]), freq_list, binary=0)
                    self.gnusPlot('set xrange [0:%d]' % avglist.shape[0])
                    self.gnusPlot('set yrange [{0}:{1}]'.format(int(freq_list[0]), int(freq_list[-1])))
                    self.gnusPlot.splot(gpavglist)
                except:
                    self.gnusPlot.close()

    avglen = 200

    def _getData(self):
        fileData = open(self.fileName)
        avglist = []
        avgall = []
        while True:
            if self.stopped():
                fileData.close()
                break
            where = fileData.tell()
            line = fileData.readline()
            if (not line) or (not line.endswith('\n')):
                time.sleep(0.1)  # seconds
                fileData.seek(where)
                continue
            if line.lstrip().startswith('#'):
                freq_list_temp = self.detect_freq_list(line.lstrip())
                if freq_list_temp != None:
                    freq_list = freq_list_temp
                continue
            line = line.rstrip()
            tokens = line.split(' ')
            data = map(float, tokens)
            while data[0] > 0:
                del data[0]
            data = numpy.array(data)
            if freq_list == None:
                freq_list = range(data.shape[0])
            try:
                avglist = numpy.vstack([avglist, [numpy.power(10, data / 10)]])
                avgall = numpy.vstack([avgall, [data]])
                avg = 10 * numpy.log10(numpy.average(avglist, 0))
                maxv = 10 * numpy.log10(numpy.max(avglist, 0))
                minv = 10 * numpy.log10(numpy.min(avglist, 0))
                if len(avglist) > self.avglen:
                    avglist = numpy.delete(avglist, 0, 0)
                    avgall = numpy.delete(avgall, 0, 0)
                yield data, avg, maxv, minv, avgall, freq_list
            except:
                avglist = numpy.copy(numpy.power(10, data / 10))
                avgall = numpy.copy(data)
        yield 0, 0, 0, 0, 0, 0

    def detect_freq_list(self, line):
        import re
        line = line.lstrip("#").lstrip()
        p = re.compile('(?P<start>\d+)MHz-(?P<stop>\d+)MHz @ (?P<rbw>\d+\.?\d*)KHz, (?P<samples>\d+) samples')
        m = p.match(line)
        if m:
            freq_list = numpy.linspace(float(m.group('start')), float(m.group('stop')), int(m.group('samples')))
            return freq_list
        try:
            line = line.lstrip("Frequencies (in MHz): ")
            line = line.split(',')
            freq_list = map(float, line)
            return freq_list
        except:
            return None

if __name__ == '__main__':
    #sys.argv.append('-dGTK')
    #print sys.argv[1]
    gnuplot = lplot(sys.argv[1], sys.argv[1])
    gnuplot.start()
    while True:
        try:
            line = raw_input('Type "stop" to end:')
        except KeyboardInterrupt:
            break
        if 'stop' in line:
            break
    gnuplot.stop()
