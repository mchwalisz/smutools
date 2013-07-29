#!/usr/bin/env python
'''
Created on 10-02-2012

@author: Mikolaj Chwalisz
'''
import threading
import subprocess
import os
import tempfile
import shutil
import logging

sensing_dir = '../telos_spectrum_monitor/'  # Has to relative to the the telos.py module


class sensing(threading.Thread):
    '''
    classdocs
    '''

    cmd_make = 'make telosb  install bsl,'  # telos_dev missing
    cmd_make_clean = 'make clean'
    cmd_printf = ['java', '-cp', '.:./tinyos.jar', 'net.tinyos.tools.PrintfClient', '-comm', 'sf@localhost:{0}']  # 'serial@{0}:115200']
    cmd_sf = [''.join([os.environ['TOSDIR'], '/../support/sdk/c/sf/sf'])]  # port, dev, speed (115200)
    log_txt = '''#Frequencies (in MHz): {0}
# Data format: one line per sweep (scanning all frequencies in the order above), every entry represents
#              the average RF power (in dBm) measured on a frequency over a period of 192 microseconds.

'''
    sema_install = threading.Semaphore()

    def __init__(self,
            name='ttyUSB0',
            telos_dev='/dev/ttyUSB0',
            fileName='data'):
        super(sensing, self).__init__(name='Telos %s' % (name))
        self.id = name
        self.telos_dev = telos_dev
        self._stop = threading.Event()
        self.fileName = fileName
        self.log_filename = '%s_telos_%s.txt' % (self.fileName, name)
        self.logger = logging.getLogger('sensing.telos')

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        self.sema_install.acquire()
        #1. Make temp dir
        job_dir = tempfile.mkdtemp()
        work_dir = '%s/sensing' % job_dir
        self.logger.info("START - file %s - device %s - work dir %s" % (self.log_filename, self.telos_dev, work_dir))
        shutil.copytree('/'.join([os.path.dirname(__file__), sensing_dir]), work_dir,
            ignore=shutil.ignore_patterns('*.pyc', 'tmp*', '.*', 'build', 'pp'))
        #2. make clean
        self.logger.debug(self.cmd_make_clean)
        proc = subprocess.Popen(self.cmd_make_clean,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=work_dir)
        self.logger.log(logging.DEBUG-5, "%s - %s" % (self.id, proc.stdout.readline().rstrip()))
        self.logger.log(logging.DEBUG-5, "%s - %s" % (self.id, proc.stderr.readline().rstrip()))
        proc.wait()
        #3. make install
        freq = range(2400, 2481, 2)
        freq = ','.join(["%s" % el for el in freq])
        freq_vec = 'FREQUENCY_VECTOR={%s} ' % freq
        #self.cmd_make = self.cmd_make.format(self.telos_dev)
        cmd_make = ''.join([freq_vec, self.cmd_make, self.telos_dev])
        self.logger.debug(cmd_make)
        proc_done = False
        while not proc_done:
            proc = subprocess.Popen(cmd_make,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                cwd=work_dir)
            while True:
                self.logger.log(logging.DEBUG-5, "%s - %s" % (self.id, proc.stdout.readline().rstrip()))
                self.logger.log(logging.DEBUG-5, "%s - %s" % (self.id, proc.stderr.readline().rstrip()))
                if proc.poll() is not None:
                    if proc.poll() == 0:
                        proc_done = True
                    break
            if self.stopped():
                shutil.rmtree(job_dir)
                return
        # Prepare log file
        log_file = open(self.log_filename, 'w')
        log_file.write(self.log_txt.format(freq))
        log_file.seek(-1, 2)
        #4. Run serial forwarder and printf
        port = str(int(self.telos_dev.replace('/dev/ttyUSB', '')) + 9002)
        cmd_sf = self.cmd_sf[:]
        cmd_sf.append(port)
        cmd_sf.append(self.telos_dev)
        cmd_sf.append('115200')

        cmd_printf = self.cmd_printf[:]
        cmd_printf[-1] = cmd_printf[-1].format(port)

        self.logger.debug(' '.join(cmd_sf))
        self.logger.debug(' '.join(cmd_printf))

        proc = subprocess.Popen(cmd_sf,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=work_dir)
        proc_print = subprocess.Popen(cmd_printf,
            stdout=log_file,
            stderr=subprocess.PIPE,
            cwd=work_dir)
        self.logger.info("RUNNING - file %s - device %s - work dir %s" % (self.log_filename, self.telos_dev, work_dir))
        self.sema_install.release()
        self._stop.wait()
        proc.kill()
        proc_print.kill()
        proc.wait()
        log_file.close()
        shutil.rmtree(job_dir)
        self.logger.info("STOP - file %s - device %s - work dir %s" % (self.log_filename, self.telos_dev, work_dir))


def list_devs():
    cmd_grep_nodes = "motelist | grep /dev/ttyUSB"
    mote_devs = subprocess.Popen(cmd_grep_nodes, stdout=subprocess.PIPE, shell=True).stdout.read()
    mote_devs = mote_devs.split('\n')
    dev_list = []
    for x in mote_devs:
        x = x.split()
        if len(x) < 2:
            break
        dev_list.append((x[0], x[1]))
    return dev_list


def main():
    import plot
    logger = logging.getLogger('sensing')
    logger.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    telos_thr = []
    plot_thr = []
    for x in list_devs():
        telos_thr.append(sensing(name=x[0], telos_dev=x[1], fileName='data'))
        telos_thr[-1].start()
    if not telos_thr:
        logger.warning('No devices found, exiting...')
        return
    sensing.sema_install.acquire()
    logger.debug("All telos started...")
    for x in list_devs():
        plot_thr.append(plot.lplot(name='Telos %s' % (x[0]), fileName='data_telos_%s.txt' % (x[0])))
        plot_thr[-1].start()
    sensing.sema_install.release()
    while True:
        try:
            line = raw_input('Type "stop" to end:')
        except KeyboardInterrupt:
            break
        if 'stop' in line:
            break
    for x in plot_thr:
        x.stop()
    for x in telos_thr:
        x.stop()


if __name__ == '__main__':
    main()
