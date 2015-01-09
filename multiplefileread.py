#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 19 10:49:32 2014

@author: User

USELESS HERE!!!! REMOVE
"""

from PyQt4 import QtGui
import sys

class MultipleFileRead(QtGui.QWidget):
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        
        self.gumb = QtGui.QPushButton("gumb za testing")
        
        self.gumb.clicked.connect(self.bleh)
        
        self.lay = QtGui.QVBoxLayout()
        self.lay.addWidget(self.gumb)
        
        self.setLayout(self.lay)
        
        
    def bleh(self):
        x = QtGui.QFileDialog()
        
        #dat = x.getOpenFileNames(caption='Open files', filter='CSV Weblogger (*.csv);;All files(*.*)')
        dat = x.getOpenFileNames(caption='Open files', filter='CSV Weblogger (*.csv)')
        for i in dat:
            print(i)

class KalendarStuff(QtGui.QWidget):
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        
        self.kalendar = QtGui.QCalendarWidget()
        self.gnext = QtGui.QPushButton('NEXT')
        self.gprev = QtGui.QPushButton('PREV')
        
        self.kalendar.activated.connect(self.trenutni)
        self.gnext.clicked.connect(self.iduci)
        self.gprev.clicked.connect(self.pred)
        
        self.lay = QtGui.QVBoxLayout()
        self.lay.addWidget(self.kalendar)
        self.lay.addWidget(self.gnext)
        self.lay.addWidget(self.gprev)
        
        self.setLayout(self.lay)
        
    def trenutni(self):
        print(self.kalendar.selectedDate())

    def iduci(self):
        dan = self.kalendar.selectedDate()
        dan2 = dan.addDays(1)
        self.kalendar.setSelectedDate(dan2)
    
    def pred(self):
        dan = self.kalendar.selectedDate()
        dan2 = dan.addDays(-1)
        self.kalendar.setSelectedDate(dan2)


if __name__ == '__main__':
#    app = QtGui.QApplication(sys.argv)
#    w = MultipleFileRead()
#    w.show()
#    sys.exit(app.exec_())
    app = QtGui.QApplication(sys.argv)
    w = KalendarStuff()
    w.show()
    sys.exit(app.exec_())