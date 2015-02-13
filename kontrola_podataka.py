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

2. sredi dodavanje novih referentnih vrjednosti za zero/span
    -pazi kod rest servisa, put mora imati programmjerenjaid
    -izbornik za zero i span! dijalog na gumb? ili toolbar?
    -verify type prije nego sto dodas na servis..typecheck!
    
3. REFACTOR CRTANJE GRAFOVA.... zero i span su skoro pa identicni!

4. sredi crtanje zero i span do kraja
     - flagiranje valjanih...
     - problem sa step funkcijom (zadnja tocka neka bude rub x kooridinate)
     - odmakni tocke od ruba!

5. sort incoming dataframe data????
"""