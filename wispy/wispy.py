#!/usr/bin/env python
'''
Created on 10-02-2012

@author: Mikolaj Chwalisz
'''
import threading
import subprocess
import os
import logging


spectools_dir = "./spectools"  # Has to relative to the the wispy.py module


class sensing(threading.Thread):
    '''
    classdocs
    '''

    def __init__(self, name='0', wispy_nr='0', fileName='data', band='0'):
        threading.Thread.__init__(self, name=' '.join(['Wispy', name]))
        self.wispy_nr = wispy_nr
        self.band = band
        self._stop = threading.Event()
        self.filename = ''.join([fileName, '_wispy_%s_%s.txt' % (name, self.wispy_nr)])
        self.logger = logging.getLogger('sensing.wispy')

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    sema_install = threading.Semaphore()

    def run(self):
        self.sema_install.acquire()
        self.logger.info('START - file {0} - device {1}'.format(self.filename, self.wispy_nr))
        # Prepare log file
        log_file = open(self.filename, 'w')
        # Run sensing
        cmd_run = [
            '/'.join([os.path.dirname(__file__), spectools_dir, "spectool_raw"]),
            "-d", self.wispy_nr, "-r", self.band
        ]
        self.logger.debug(' '.join(cmd_run))
        proc = subprocess.Popen(cmd_run,
                                stdout=log_file,
                                stderr=log_file,
                                stdin=None,
                                close_fds=True)
        self.sema_install.release()
        self.logger.info('RUNNING - file {0} - device {1}'.format(self.filename, self.wispy_nr))
        self._stop.wait()
        self.sema_install.acquire()
        proc.terminate()
        proc.wait()
        log_file.close()
        self.logger.info('STOP - file {0} - device {1}'.format(self.filename, self.wispy_nr))
        self.sema_install.release()


def list_devs():
    cmd_grep_nodes = ''.join([
        '/'.join([os.path.dirname(__file__), spectools_dir, "spectool_raw"]),
        " -l ", " | grep Device | awk '{print $2}'"
    ])
    #print(cmd_grep_nodes)
    dev_nr = subprocess.Popen(cmd_grep_nodes, stdout=subprocess.PIPE, shell=True).stdout.read()
    mote_devs = str(dev_nr.decode('UTF-8'))
    mote_devs = mote_devs.split('\n')
    dev_list = []
    for x in mote_devs:
        x = x.replace(':', '')
        if not x == '':
            dev_list.append(x)
    return dev_list

def list_wispy():
    cmd_nodes = ''.join([
        '/'.join([os.path.dirname(__file__), spectools_dir, "spectool_raw"]),
        " -l "
    ])
    out = subprocess.Popen(cmd_nodes, stdout=subprocess.PIPE, shell=True).stdout.read()
    return out.split('\n')

def main():
    logger = logging.getLogger('sensing')
    logger.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    dev_list = list_devs()
    wispy_thr = []
    if not dev_list:
        logger.warning('No devices found, exiting...')
        return
    for x in dev_list:
        wispy_thr.append(sensing(name=str(x), wispy_nr=x))
        wispy_thr[-1].start()
    while True:
        try:
            line = raw_input('Type "stop" to end:')
        except KeyboardInterrupt:
            break
        if 'stop' in line:
            break
    for x in wispy_thr:
        x.stop()

if __name__ == '__main__':
    main()
