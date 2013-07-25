#!/usr/bin/env python
'''
Created on 17-02-2012

@author: Mikolaj Chwalisz
'''

import sys
from PyQt4 import QtGui
from gui_UI import Ui_MainWindow
import telos

class MyForm(QtGui.QMainWindow, Ui_MainWindow): #
    
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
    
    def telos_list(self):
        self.ui.telos_listWidget.clear()
        devs = telos.list_devs()
        devs = sorted(devs, key=lambda dev: dev[1])   # sort by USB
        for x in devs:
            desc = ' on '.join(x)
            item = QtGui.QListWidgetItem()
            item.setText(desc)
            item.telos_id = x[0]
            item.telos_dev = x[1]
            item.thread = telos.sensing(item.telos_id,item.telos_dev)
            self.ui.telos_listWidget.addItem(item)
    
    def telos_run_selected(self):
        for item in self.ui.telos_listWidget.selectedItems():
            if not item.thread.is_alive():
                item.thread.start()
    
    def telos_stop_selected(self):
        for item in self.ui.telos_listWidget.selectedItems():
            item.thread.stop()
            item.thread = telos.sensing(item.telos_id,item.telos_dev)
    
    def telos_stop_all(self):
        for ii in range(self.ui.telos_listWidget.count()):
            item = self.ui.telos_listWidget.item(ii)
            item.thread.stop()
            item.thread = telos.sensing(item.telos_id,item.telos_dev)

        

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MyForm()
    myapp.show()
    sys.exit(app.exec_())