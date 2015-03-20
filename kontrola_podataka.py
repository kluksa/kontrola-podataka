#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 31 14:06:55 2014

@author: User
"""
import sys
from PyQt4 import QtGui
import display
#instancira QApplication objekt i starta main event loop
aplikacija = QtGui.QApplication(sys.argv)
#inicijaliziraj aplikaciju sa config fileom
glavniProzor = display.Display(configfile = 'config.ini')
#prikaz GUI na ekran
glavniProzor.show()
#clean exit iz aplikacije
sys.exit(aplikacija.exec_())

"""
potencijalni problemi
1. unresponsive gui.
- Implementacija thredova??
- implemetacija je malo komplicirana
    -instanciram QThreadObject()
    -taj thread pokrece svoj event loop nakon poziva start metode
    -bilo koji QObject mogu gurnuti u taj thread
    -signali imaju protokol pomocu kojih mogu komunicirati sa drugim threadovima

    -display i kontroler drzati u jednom threadu
    -blocking I/O prebaciti u drugi thread? (networking, dokument..)
    -potrebno je jos refaktorirati kod

2. dokument nema mehanizam da oslobodi memoriju.
- kako se dodaju podaci prostor u memoriji raste...
- test pandas dataframe od 512640 redaka (1 god minutnih podataka) sa
  180 stupaca sa random float podacima zauzima oko 700MB memorije.
- procjena memorije se moze izracunati preko sljedece funkcije
  memsize = df.index.nbytes+df.values.nbytes+df.columns.nbytes
"""