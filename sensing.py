#!/usr/bin/env python
'''
Created on 23-02-2012

@author: Mikolaj Chwalisz
'''
from optparse import OptionParser
import glob
import logging
from tools import wispy
try:
    from tools import telos
except:
    # There is no TinyOS Environment set up, skip TelosB support
    from tools import telos_fallback as telos


def run_telos(telos_devs, optplot):
    if not telos_devs:
        logger.warning("No telos device found.")
        return []
    telos_thr = []
    for tdev in telos_devs:
        telos_thr.append(telos.sensing(name=tdev[0], telos_dev=tdev[1], fileName=options.fileNamePrefix))
        telos_thr[-1].start()
    return telos_thr


def run_wispy(wispy_devs, optplot):
    if not wispy_devs:
        logger.warning("No wispy device found.")
        return []
    wispy_thr = []
    for wdev in wispy_devs:
        wispy_thr.append(wispy.sensing(name=str(wdev), wispy_nr=wdev, fileName=options.fileNamePrefix))
        wispy_thr[-1].start()
    return wispy_thr


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="fileNamePrefix", default="data",
                      help="select FILE as the file name prefix for measurements", metavar="FILE")
    parser.add_option("-V", "--visual",
                      action="store_true", dest="plot", default=False,
                      help="plot data during measurements")
    parser.add_option("-F", "--force",
                      action="store_true", dest="force_overwrite", default=False,
                      help="force data FILE overwrite")
    parser.add_option("-l", "--list",
                      action="store_true", dest="list", default=False,
                      help="list all available devices")
    parser.add_option('-v', '--verbose', dest='verbose', action='count',
                      help="Increase verbosity (specify multiple times for more)")

    (options, args) = parser.parse_args()

    logger = logging.getLogger('sensing')
    logger.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    log_level = logging.WARNING  # default
    if options.verbose == 1:
        log_level = logging.INFO
    elif options.verbose == 2:
        log_level = logging.DEBUG
    elif options.verbose >= 3:
        logger.setLevel(logging.DEBUG - 5)
        log_level = logging.DEBUG - 5
        logging.addLevelName(log_level, 'debug2')
    ch.setLevel(log_level)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    telos_devs = telos.list_devs()
    wispy_devs = wispy.list_devs()
    if options.list:
        for tdev in telos_devs:
            print("Telos node: id={0}, devive={1}".format(tdev[0], tdev[1]))
        for wdev in wispy_devs:
            print("Wispy node: id={0}".format(wdev))
        exit()
    #Check fileNamePrefix
    flist = glob.glob("{0}_*.txt".format(options.fileNamePrefix))
    if flist and not options.force_overwrite:
        logger.error("Data with selected prefix ({0}) exist:\n{1}\nExiting..."
              .format(options.fileNamePrefix, flist))
        exit(1)
    threads = []
    threads.extend(run_telos(telos_devs, options.plot))
    threads.extend(run_wispy(wispy_devs, options.plot))
    if not threads:
        logger.error("No devices found, exiting...")
        exit()
    while True:
        try:
            line = raw_input('Type "stop" to end:')
        except KeyboardInterrupt:
            break
        if 'stop' in line:
            break
    for x in threads:
        x.stop()
