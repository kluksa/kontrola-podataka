#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 31 14:06:55 2014

@author: User

Glavni pokretac aplikacije za kontrolu podataka
"""

import sys
from PyQt4 import QtGui
import display

aplikacija = QtGui.QApplication(sys.argv)
glavniProzor = display.Display()
glavniProzor.show()
sys.exit(aplikacija.exec_())



"""
TODO!
1. sredi toolbar za pick/zoom opcijama za sve grafove! (qtoolbar)

2. reimplementiraj neki zoom opciju zajednicku SVIM canvasima
    - dadaj metodu na opcenitiCanvas.py
"""