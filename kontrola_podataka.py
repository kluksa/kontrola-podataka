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

3. refactor crtanje grafova

4. ikone za ostale menu bar i tool bar akcije?

5. multiple toolbars??

TESTING!
done:
toolbar reimplementiran

reimplementiraj neki zoom opciju zajednicku SVIM canvasima
    - dadaj metodu na opcenitiCanvas.py


save to rest implementiran.
    - sada je na gumbu koji je na centralnom dijelu panela sa grafovima
    - nije moguce saveati podatke koji nisu 100% validirani, pokusaj istog javlja
      error msg u obliku informacijskog dijaloga.
    - save updatea kalendar

in short za svaki kanal:
- kada se ucita, datum se sprema u listu 'bad'
- kada se spremi na rest, datum se sprema u listu 'ok'
- kalendar boja datume iz te dvije liste u razlicite boje, vizualno je moguce pratiti
  koji je datum spremljen a koji je samo ucitan u dokument.
"""