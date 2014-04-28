#!/usr/bin/env python
'''
Created on 23-02-2012

@author: Mikolaj Chwalisz
'''
import threading
import logging


class sensing(threading.Thread):
    sema_install = threading.Semaphore()


def list_devs():
    logger = logging.getLogger('sensing.telos')
    logger.warning(
        "Using telos_fallback module,"
        "no telos nodes will be detected"
        )
    return []
