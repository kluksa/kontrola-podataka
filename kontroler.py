# -*- coding: utf-8 -*-
"""
Created on Fri May  9 13:19:45 2014

@author: velimir

Problemi:
connect1 prima dobar signal, slot radi problem. citaj() missing 1 requred positional argument :'path'
"""

from PyQt4 import QtGui,QtCore

class KontrolerSignala(QtGui.QWidget):
    """
    Kontrolni dio aplikacije. Subklasa je QWidgeta zbog metode connect
    view je objekt displaya, model je objekt dokumenta
    """
    def __init__(self,parent=None,view=None,model=None):
        QtGui.QWidget.__init__(self,parent)
        
        #connect1:qt akcija ucitavanja - read csv u dokumentu
        self.connect(view,
                    QtCore.SIGNAL('request_read_csv(PyQt_PyObject)'),
                    model.citaj_csv)
        #connect2: trenutni kljucevi - update QComboBox liste u view
        self.connect(model,
                    QtCore.SIGNAL('update_kljuc(PyQt_PyObject)'),
                    view.update_kljuc)
                    
    def test(self,x):
        print(x)
        
