#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
rsfsv.py: Connects to the Rohde & Schwarz FSV Signal Analyzer


Usage: rsfsv.py [options]

Options:
  -p PREFIX, --prefix=PREFIX  select PREFIX as the file name
                    prefix for measurements [default: data]
  -n FSVHOST, --fsvhost=FSVHOST  host name [default: 192.168.10.250]
  -P FSVPORT, --fsvport=FSVPORT  port number [default: 5025]
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
import time
import struct


class sensing(threading.Thread):
    '''
    classdocs
    '''
    BUF_SIZE_DEFAULT = 8*4096

    def __init__(self, fsvhost='192.168.10.250', fsvport='5025', fileName='data'):
        threading.Thread.__init__(self, name=' '.join(['FSV', fsvhost]))
        self.fsvhost = fsvhost
        self.fsvport = int(fsvport)
        self.fileName = fileName
        self._stop = threading.Event()
        self.log_filename = '%s_fsv_%s.fsv' % (self.fileName, self.fsvhost)
        self.logger = logging.getLogger('sensing.fsv')
        self.sock = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
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
        idn = self.command("*IDN?")
        idn = ' '.join(idn.split(',')[0:3])
        self.logger.info('START - file %s - %s' % (self.log_filename, idn))
        self.getErrors()
        outfile = open(self.log_filename, 'w')

        self.getMeta(outfile)
        self.sock.settimeout(10)
        self.sock.send("FORMat REAL,32\n")
        self.logger.info('RUNNING - file %s - %s' % (self.log_filename, idn))
        while not self.stopped():
            # self.command("SWE:TIME?")
            self.getData(outfile)
        self.logger.info('STOP - file %s - %s' % (self.log_filename, idn))
        outfile.close()
        self.close()
    # def run

    def getMeta(self, of):
        self.sock.send("INIT:CONT OFF\n")  # Disable continuous sweep
        self.sock.send("SYST:Err:CLE:All\n")  # Clear all previous errors
        # self.sock.send("SYSTem:DISPlay:UPDate OFF\n")  # Disable display update (should make everything faster)
        self.sock.send("FORMat ASCii\n")  # Get meta data in ASCii mode (human readable, slower)
        self.sock.send("MMEM:STOR:TRAC  1,'C:\TRACE.DAT'\n")  # Store one trace to the file
        self.sock.send("MMEM:DATA? 'C:\TRACE.DAT'\n")  # Download this trace, it also has all the settings stored

        self.sock.settimeout(None)
        buf = self.sock.recv(2)
        self.logger.debug("Meta: Buf #: %i" % int(buf[1]))
        toread = int(self.sock.recv(int(buf[1])))
        self.logger.debug("Meta: Buf size: %i" % toread)

        dread = 0
        while toread:
            if self.BUF_SIZE_DEFAULT > toread:
                bufs = toread - dread
            else:
                bufs = self.BUF_SIZE_DEFAULT
            buf = self.sock.recv(bufs)
            toread -= len(buf)
            # self.logger.debug("Meta: Just read: %i, todo: %i" % (len(buf), toread))
            of.write(buf)
        of.write("Binary Format;double(UnixTimeStamp)float32(Value)*#Values;\n")
        of.flush()
    # def getMeta

    def getData(self, of):
        self.sock.send("INIT:IMM; *WAI\n")
        self.sock.send("TRAC? TRACE1; *WAI\n")

        # self.sock.send("FORMat ASCii\n")

        # self.sock.settimeout(None)
        while self.sock.recv(1) != "#":
            pass
        buf = self.sock.recv(1)
        toread = int(self.sock.recv(int(buf)))
        # self.logger.debug("Data: Buf len %i, Buf size %i" % (int(buf), toread))

        dread = 0
        of.write(struct.pack('d', time.time()))
        while toread:
            if self.BUF_SIZE_DEFAULT > toread:
                bufs = toread - dread
            else:
                bufs = self.BUF_SIZE_DEFAULT
            buf = self.sock.recv(bufs)
            toread -= len(buf)
            # self.logger.debug("Meta: Just read: %i, todo: %i" % (len(buf), toread))
            of.write(buf)
        of.flush()
    # # def getData

    def command(self, cmd):
        self.logger.debug("Send command: %s" % cmd)
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
            result = ''.join(buf).strip('\n')
            self.logger.debug("Received rsp: %s" % result)
            return result
        else:
            return
    # def command

    def close(self):
        self.getErrors()
        self.command("INIT:CONT ON")
        self.command("SYSTem:DISPlay:UPDate ON")
        # self.command("SYSTem:​KLOCk OFF")
        self.sock.close()
    # def close

    def getErrors(self):
        result = ""
        i = 0
        while (not '0,"No error"' in result) and i < 10:
            result = self.command("SYSTem:ERRor?")
            i += 1
    # def getErrors


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
    time.sleep(5)
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
