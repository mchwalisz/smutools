#!/usr/bin/env python
'''
Created on 23-02-2012

@author: Mikolaj Chwalisz
'''
import threading

class sensing(threading.Thread):
	sema_install = threading.Semaphore()
	
def list_devs():
	return []