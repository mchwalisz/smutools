#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
smut.py: Starts sensing process for all connected devices

Supports:
- WiSpy
- Telos
- R&S FSV


Usage:
  smut.py [options] [<prefix>]
  smut.py --plot

Arguments:
  <prefix>                       select <prefix> as the file name
                                   prefix for measurements [default: data]

Options:
  -F, --force-overwrite          force files with given <prefix> to be
                                   overwritten (POSSIBLE LOSS OF DATA)
  -f <fsvhost>, --fsv=<fsvhost>  connect to R&S FSV
  --fsvport=<fsvport>            port number [default: 5025]
  -g, --gui                      run monitor gui
  -l, --list                     list all available devices
  --wispy-band=<band>            band range to use for WiSpy [default: 0]
  --plot                         use Matlab to plot summaries of all data in
                                   current and all sub-folders

Other options:
  -q, --quiet               print less text
  -v, --verbose             print more text
  -h, --help                show this help message and exit
  --version                 show version and exit
"""

__author__ = "Mikolaj Chwalisz"
__copyright__ = "Copyright (c) 2012-2013, Technische Universität Berlin"
__version__ = "0.3.0"
__email__ = "chwalisz@tkn.tu-berlin.de"

import glob
import logging
import time
from wispy import wispy
from rohdeschwarz import rsfsv
try:
    from telos import telos
except:
    # There is no TinyOS Environment set up, skip TelosB support
    from telos import telos_fallback as telos
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


def run_telos(telos_devs):
    if not telos_devs:
        log.warning("No telos device found.")
        return []
    telos_thr = []
    for tdev in telos_devs:
        telos_thr.append(telos.sensing(name=tdev[0], telos_dev=tdev[1],
            fileName=args['<prefix>']))
        telos_thr[-1].start()
    return telos_thr


def run_wispy(wispy_devs):
    if not wispy_devs:
        log.warning("No wispy device found.")
        return []
    wispy_thr = []
    for wdev in wispy_devs:
        wispy_thr.append(wispy.sensing(name=str(wdev), wispy_nr=wdev,
            fileName=args['<prefix>'], band=args['--wispy-band']))
        wispy_thr[-1].start()
    return wispy_thr


def matlab_plot():
    """matlab_plot() -> docstring"""
    from os.path import realpath, dirname
    import subprocess
    matcmd = (
        "run('%s/crewcdf_toolbox/crewcdf_toolbox_load.m');"
        "set(0, 'DefaultFigureVisible', 'off');"
        "crewcdf_plotall();"
        "quit();"
        ) % dirname(realpath(__file__.rstrip("c")))
    # matlab -nodesktop -nodisplay -nosplash
    cmd = "matlab -nodesktop -nosplash -r \"%s\"" % matcmd
    print(cmd)
    p = subprocess.Popen(cmd, shell=True)
    p.wait()
# def matlab_plot


def main(args):
    telos_devs = telos.list_devs()
    wispy_devs = wispy.list_devs()
    if args['--list']:  # List and exit
        for tdev in telos_devs:
            print("Telos node: id={0}, devive={1}".format(tdev[0], tdev[1]))
        for wdev in wispy_devs:
            print("Wispy node: id={0}".format(wdev))
            for msg in wispy.list_wispy():
                log.info(msg)
        if not telos_devs and not wispy_devs:
            log.info("No devices found. Exiting...")
        exit()
    if args['--plot']:
        matlab_plot()
        exit()
    if not telos_devs and not wispy_devs and not args['--fsv']:
        log.warning("No devices found. Exiting...")
        print "Please connect any device and run with:"
        print __doc__
        exit()
    if args['<prefix>'] is None:
        args['<prefix>'] = 'data'
    flist = glob.glob("%s_*.txt" % (args['<prefix>']))
    if flist and not args['--force-overwrite']:
        log.error("Data with selected prefix (%s) exist:\n%s\nExiting..."
            % (args['<prefix>'], flist))
        exit(1)
    threads = []
    threads.extend(run_telos(telos_devs))
    threads.extend(run_wispy(wispy_devs))
    if args['--fsv'] is not None:
        log.info("Starting FSV on host: %s" % args['--fsv'])
        threads.append(rsfsv.sensing(
            fsvhost=args['--fsv'],
            fsvport=args['--fsvport'],
            fileName=args['<prefix>']))
        threads[-1].start()
    if not threads:
        log.error("No devices found, exiting...")
        exit()
    if args['--gui']:
        import sys
        from PySide import QtGui
        from smuts_gui import smut_mon
        time.sleep(2)
        app = QtGui.QApplication(sys.argv)
        apps = []
        for x in threads:
            log.info("Starting GUI")
            apps.append(smut_mon.MonitorMainWindow(filename=x.log_filename))
            apps[-1].show()
        app.exec_()
    else:
        while True:
            try:
                line = raw_input('Type "stop" to end:')
            except KeyboardInterrupt:
                break
            if 'stop' in line:
                break
    for x in threads:
        x.stop()
# def main


if __name__ == "__main__":
    args = docopt(__doc__, version=__version__)

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
    main(args)
