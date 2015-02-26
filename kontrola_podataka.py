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

1. funkcionalnost sljedeci/prethodni dan za zero/span panel??

2. neovisni zoom/pick selektor za pojednini graf?

3. refactor crtanje grafova?

4. ikone za ostale menu bar i tool bar akcije?

5. multiple toolbars??

6. show hide toolbars??? (instanca_toolbara.hide(), instanca_toolbara.show())

7. LOGGING
"""