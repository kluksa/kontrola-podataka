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

bug sa glavnim dijalogom za postavke grafova...

ZERO SPAN!
promjena u zero span DTO

{"maxDozvoljeno":float, "minDozvoljeno":float, "vrijednost":float,
"vrijeme":int unix timestamp, "vrsta":char "Z" ili "S"}

primam listu takvih
saljem jenda json, sa dodatnim programMjerenjaId

plot fill izmedju dozvoljenih zeleno (default)
plot fill izvan dozvoljenih crveno (default)
tocke unutar -- zeleno
tocke izvan -- crveno



1. funkcionalnost sljedeci/prethodni dan za zero/span panel??

2. neovisni zoom/pick selektor za pojednini graf?

3. refactor crtanje grafova?

4. ikone za ostale menu bar i tool bar akcije?

5. multiple toolbars??

6. show hide toolbars??? (instanca_toolbara.hide(), instanca_toolbara.show())
"""