#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
plot_wispy.py: Wispy Summary Plot

Usage:
    plot_wispy.py [options] [-q | -v] FILE...
    plot_wispy.py -c CONFIG [options] [-q | -v] [FILE]
    plot_wispy.py --config

Arguments:
    FILE                      folder or filenames to process

Options:
    -s, --skip-existing       skip existing
    --pdf                     generate pdf instead of png

Other options:
    --config                  prints empty config file
    -c CONFIG                 loads config file
    -h, --help                show this help message and exit
    -q, --quiet               print less text
    -v, --verbose             print more text
    --version                 show version and exit
"""

__author__ = "Mikolaj Chwalisz"
__copyright__ = "Copyright (c) 2014, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "chwalisz@tkn.tu-berlin.de"

# coding: utf-8


#### Imports

import pandas as pd
import datetime
import math
from time import time
import numpy as np
import matplotlib.pyplot as plt
import pylab
import re
import os
import logging

#### Data parsing functions


def tail(fname, _buffer=4098, comment='#'):
    """Tail a file and get number of commented lines from the end"""
    f = open(fname)
    # place holder for the lines found
    lines_found = []

    # block counter will be multiplied by buffer
    # to get the block size from the end
    block_counter = -1

    # loop until we find X lines
    while True:
        try:
            f.seek(block_counter * _buffer, os.SEEK_END)
        except IOError:
            # either file is too small, or too many lines requested
            f.seek(0)
            lines_found = f.readlines()
            break

        lines_found = f.readlines()
        for indx, line in enumerate(reversed(lines_found[1:])):
            if not line.lstrip().startswith(comment):
                f.close()
                return indx
        # decrement the block counter to get the
        # next X bytes
        block_counter -= 1


def parse_run_parameters(fname, comment='#'):
    return_dict = {"num_rows_comment": 0,
        "skipfooter": tail(fname)}
    with open(fname) as f:
        restr = ("(?P<start>\d+)MHz-(?P<stop>\d+)MHz"
                 " @ (?P<rbw>\d+\.?\d*)(?P<rbwu>[KM]Hz), (?P<samples>\d+) samples")
        p = re.compile(restr)
        for line in f:
            if line.startswith(comment):
                return_dict["num_rows_comment"] = \
                    return_dict["num_rows_comment"] + 1
            else:
                return return_dict
            line = line.lstrip(comment).lstrip()
            m = p.match(line)
            if m:
                return_dict["start"] = float(m.group('start'))
                return_dict["stop"] = float(m.group('stop'))
                return_dict["samples"] = int(m.group('samples'))
                if m.group('rbwu') is "KHz":
                    return_dict["step"] = float(m.group('rbw'))
                else:
                    return_dict["step"] = float(m.group('rbw')) * 1000
                return_dict["freq_list"] = np.linspace(
                    float(m.group('start')),
                    float(m.group('stop')),
                    int(m.group('samples')),
                    endpoint=True).tolist()
# def parse_run_parameters


def get_wispy_data(filename):
    NROWS = None
    parse_time_func = lambda x, y: \
        datetime.datetime.fromtimestamp(float(x) + float(y) / 1000000)
    # column_types = {"start_s": np.uint32, "start_ns": np.uint32,
        # "stop_s": np.uint32, "stop_ns": np.uint32}

    run_params = parse_run_parameters(filename)

    column_names = ["start_s", "start_ns", "stop_s", "stop_ns"] + \
        run_params["freq_list"]
    df = pd.read_csv(filename, sep=" ", names=column_names,
        header=None, skiprows=run_params["num_rows_comment"],
        nrows=NROWS, index_col=False,
        parse_dates={"Datetime_start": ["start_s", "start_ns"],
            "Datetime_stop": ["stop_s", "stop_ns"]},
        date_parser=parse_time_func,
        warn_bad_lines=True,
        skipfooter=run_params["skipfooter"])
    df.dropna(how='all')
    df.pop('Datetime_stop')
    df.index = df.pop('Datetime_start')
    return df


def get_histogram(df):
    max_pwr = df.max().max()
    min_pwr = df.min().min()
    bins = np.linspace(min_pwr, max_pwr, (max_pwr - min_pwr)*4, endpoint=True)
    matrix = np.zeros(shape=(df.columns.shape[0], len(bins)-1), dtype=float)
    g = np.vectorize(lambda x: math.log10(x) if x != 0 else np.nan)
    for idx, freq in enumerate(df.columns):
        matrix[idx], bins = np.histogram(df[freq].values, bins=bins)
    matrix = np.transpose(g(matrix))
    bins = bins[~np.all(np.isnan(matrix), axis=1)]
    matrix = matrix[~np.all(np.isnan(matrix), axis=1)]
    return matrix, bins

#### Plotting function


def plot_summary(filename, df, hist, bins):
    color_map = plt.get_cmap("hot")
    fig = plt.figure(figsize=(10, 10))
    fig.suptitle(os.path.splitext(os.path.basename(filename))[0],
        fontsize=14, fontweight='bold')

    ax = fig.add_subplot(2, 1, 1)
    cax = ax.imshow(hist, cmap=color_map,
                    origin="lower", interpolation='none',
                    extent=[df.columns[0], df.columns[-1], bins[0], bins[-1]],
                    aspect='auto')
    cbar = fig.colorbar(cax)

    ax1 = fig.add_subplot(2, 1, 2)
    last = df.index[-1] - df.index[0]
    cax1 = ax1.imshow(df.T, cmap=color_map,
        aspect='auto', interpolation='nearest',
        extent=[0, last.total_seconds(), df.columns[0], df.columns[-1]],
        origin='lower')
    cbar1 = fig.colorbar(cax1)

    fig.canvas.draw()

    ax.set_title('Persistence Plot')
    # Move left and bottom spines outward by 10 points
    ax.spines['left'].set_position(('outward', 10))
    ax.spines['bottom'].set_position(('outward', 10))
    # Hide the right and top spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    # Only show ticks on the left and bottom spines
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')
    #ax.set_ylim([MIN_RSS_VAL,-20])
    ax.set_xlabel('Frequency (MHz)')
    ax.set_ylabel('Signal Power (dBm)')
    cbar.set_label('Time (s)')
    ticks = []
    stime = (df.index[-1] - df.index[0]).total_seconds() / len(df.index)
    for tick in cbar.ax.yaxis.get_ticklabels():
        ticks.append("%0.1f" % ((10**(float(tick.get_text())))*stime))
    #cbar.set_ticks(cbar.ax.yaxis.get_ticklocs())
    cbar.ax.yaxis.set_ticklabels(ticks)

    ax1.tick_params(axis='both', direction='out')
    # Move left and bottom spines outward by 10 points
    ax1.spines['left'].set_position(('outward', 10))
    ax1.spines['bottom'].set_position(('outward', 10))
    # Hide the right and top spines
    ax1.spines['right'].set_visible(False)
    ax1.spines['top'].set_visible(False)
    # Only show ticks on the left and bottom spines
    ax1.yaxis.set_ticks_position('left')
    ax1.xaxis.set_ticks_position('bottom')
    #ax1.set_yticks(range(len(df.columns)))
    #ax1.set_yticklabels(df.columns)
    #ax1.set_xticks(range(len(df.index)))
    #ax1.set_xticklabels(df.index)
    ax1.set_xlabel("Time (h:m's'')\nStarted at: %s" % df.index[0])
    ax1.set_ylabel('Frequency (MHz)')
    ax1.set_title('Spectrogram')

    cbar1.set_label('Signal Power (dBm)')

    ticks = []
    for tick in ax1.get_xticks().tolist():
        m, s = divmod(tick, 60)
        h, m = divmod(m, 60)
        if h == 0:
            ticks.append("%02d'%2.2f''" % (m, s))
        else:
            ticks.append("%d:%02d'%02.d''" % (h, m, s))
    ax1.xaxis.set_ticklabels(ticks)

    fig.tight_layout()
    fig.subplots_adjust(top=0.93)

    #plt.savefig(FILE_NAME + '.png', dpi=300, transparent=True)
    fig.savefig(''.join([os.path.splitext(filename)[0], '_summary', filetype]),
        dpi=300, bbox_inches='tight')
    plt.close(fig)


## Processing the data


def process_file(filename, skip=False):
    """process_file() -> docstring"""
    log = logging.getLogger('plot_wispy')
    if not 'wispy' in os.path.basename(filename).lower() or \
            not filename.endswith('.txt'):
        return
    log.info("processing: %s" % filename)
    if skip and os.path.isfile(''.join([os.path.splitext(filename)[0], '_summary', filetype])):
        log.info("exists, skipping.")
        return
    df = get_wispy_data(filename)
    log.debug("file loaded")
    hist, bins = get_histogram(df)
    log.debug("made histogram")
    plot_summary(filename, df, hist, bins)
    del df
    del hist
    del bins
    log.debug("done.")
# def process_file


def process_all(flist, skip=False):
    for fname in flist:
        if os.path.isfile(fname):
            process_file(fname, skip)
        if os.path.isdir(fname):
            for root, dirs, files in os.walk(fname, topdown=False):
                for name in files:
                    process_file(os.path.join(root, name), skip)

filetype = '.png'

def main(args):
    """Run the code for plot_wispy"""
    log = logging.getLogger('plot_wispy.main')
    log.info(args)
    if args['--pdf']:
        global filetype
        filetype = '.pdf'
    process_all(args['FILE'], args['--skip-existing'])
# def main


def parse_json_config(args):
    """
    Takes care of the correct configure file management.

    It either prints the empty json config structure or adds the
    parameters from the given one to the existing arguments (args)
    """
    if args['--config']:
        del args['-c']
        del args['--config']
        del args['--help']
        del args['--quiet']
        del args['--verbose']
        del args['--version']
        print(json.dumps(args, sort_keys=True, indent=4))
        sys.exit()
    if args['-c']:
        json_config = json.loads(open(args['-c']).read())
        return dict((str(key), args.get(key) or json_config.get(key))
            for key in set(json_config) | set(args))
    return args
# def parse_json_config

if __name__ == "__main__":
    try:
        from docopt import docopt
    except:
        print("""
        Please install docopt using:
            pip install docopt==0.6.1
        For more refer to:
        https://github.com/docopt/docopt
        """)
        raise
    import json
    import sys

    args = docopt(__doc__, version=__version__)
    args = parse_json_config(args)

    log_level = logging.INFO  # default
    if args['--verbose']:
        log_level = logging.DEBUG
    elif args['--quiet']:
        log_level = logging.ERROR
    logging.basicConfig(level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main(args)
