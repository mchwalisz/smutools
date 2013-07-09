#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
rsfsv.py: Connects to the Rohde & Schwarz FSV Signal Analyzer


Usage: rsfsv.py [options]

Options:
  -p PREFIX, --prefix=PREFIX  select PREFIX as the file name
                    prefix for measurements [default: data]
  -n FSVHOST, --fsvhost=FSVHOST  host name [default: 192.168.10.250]
  -p FSVPORT, --fsvport=FSVPORT  port number [default: 5025]
  -F, --force-overwrite       force files with PREFIX to be
                    overwritten (POSSIBLE LOSS OF DATA)
  -l, --list                  list all available devices

Other options:
  -q, --quiet               print less text
  -v, --verbose             print more text
  -h, --help                show this help message and exit
  --version                 show version and exit
"""

__author__ = "Mikolaj Chwalisz"
__copyright__ = "Copyright (c) 2012-2013, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "chwalisz@tkn.tu-berlin.de"

import glob
import logging
import threading
import socket


class sensing(threading.Thread):
    '''
    classdocs
    '''

    def __init__(self, fsvhost='192.168.10.250', fsvport='5025', fileName='data'):
        threading.Thread.__init__(self, name=' '.join(['FSV', fsvhost]))
        self.fsvhost = fsvhost
        self.fsvport = int(fsvport)
        self.fileName = fileName
        self._stop = threading.Event()
        self.log_filename = '%s_fsv_%s.txt' % (self.fileName, self.fsvhost)
        self.meta_filename = '%s_fsv_%s_meta.txt' % (self.fileName, self.fsvhost)
        self.logger = logging.getLogger('sensing.fsv')
        self.sock = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.fsvhost, self.fsvport))
        # self.sockfile = self.sock.makefile("")
    # def __init__

    def stop(self):
        self._stop.set()
    # def stop

    def stopped(self):
        return self._stop.isSet()
    # def stopped

    def run(self):
        self.logger.info('START - file %s - device %s' % (self.log_filename, self.fsvhost))
        result = self.command("*IDN?")
        while not '0,"No error"' in result:
            result = self.command("SYSTem:ERRor?")
        self.getMeta()

        self.sock.close()
    # def run

    def getMeta(self):
        self.sock.send("INIT:CONT OFF\n")
        self.sock.send("SYST:Err:CLE:All\n")
        self.sock.send("FORMat ASCii\n")
        self.sock.send("MMEM:STOR:TRAC  1,'C:\TRACE.DAT'\n")
        self.sock.send("MMEM:DATA? 'C:\TRACE.DAT'\n")

        self.sock.settimeout(None)
        buf = self.sock.recv(2)
        self.logger.debug("Meta: Buf #: %i" % int(buf[1]))
        readsize = int(self.sock.recv(int(buf[1])))
        self.logger.debug("Meta: Buf size: %i" % readsize)

        f = open(self.meta_filename, 'w')
        readbytes = 0
        bufsize_def = 4096
        while readbytes < readsize:
            if (readbytes + bufsize_def) > readsize:
                bufs = readsize - readbytes
            else:
                bufs = bufsize_def
            buf = self.sock.recv(bufs)
            readbytes += bufs
            self.logger.debug("Meta: Just read: %i, already done: %i, todo: %i" % (bufs, readbytes, readsize))
            f.write(buf)
            f.flush()
        buf = []
        while True:
            try:
                data = self.sock.recv(1024)
                buf.append(data)
            except socket.timeout:
                break
            result = ''.join(buf).strip('\n').split('\n')
            for l in result:
                self.logger.info("Received: %s" % l)
        f.close()
    # def getMeta

    def command(self, cmd):
        self.logger.info("Send command: %s" % cmd)
        self.sock.send(cmd + "\n")
        if '?' in cmd:
            self.sock.settimeout(1)
            buf = []
            while True:
                try:
                    data = self.sock.recv(1024)
                    buf.append(data)
                except socket.timeout:
                    break
            result = ''.join(buf).strip('\n').split('\n')
            for l in result:
                self.logger.info("Received: %s" % l)
            return result
        else:
            return
    # def command


def main(args):
    flist = glob.glob("%s_*.txt" % (args['--prefix']))
    if flist and not args['--force-overwrite']:
        log.error("Data with selected prefix (%s) exist:\n%s\nExiting..." % (args['--prefix'], flist))
        exit(1)
    fsvdev = sensing(fsvhost=args['--fsvhost'], fsvport=args['--fsvport'], fileName=args['--prefix'])
    fsvdev.start()
    # TODO: check connection
    # if not threads:
    #     log.error("No devices found, exiting...")
    #     exit()
    while True:
        try:
            line = raw_input('Type "stop" to end:')
        except KeyboardInterrupt:
            break
        if 'stop' in line:
            break
    fsvdev.stop()
# def main


def getLogger(args):
    log = logging.getLogger('sensing')
    log.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    log_level = logging.INFO  # default
    if args['--verbose']:
        log_level = logging.DEBUG
    elif args['--quiet']:
        log_level = logging.ERROR
    ch.setLevel(log_level)
    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)
    return log
# def get_logger

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

    args = docopt(__doc__, version=__version__)
    log = getLogger(args)
    main(args)
