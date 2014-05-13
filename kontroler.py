# -*- coding: utf-8 -*-
"""
Created on Fri May  9 13:19:45 2014

@author: velimir

Problemi:
status:
-Kontroler dobro incijalizira i model i view, link na test output funkciju radi ok
-Iz nekog razloga, model.citaj_csv ne radi
"""

from PyQt4 import QtGui,QtCore

class KontrolerSignala(QtGui.QWidget):
    """
    Kontrolni dio aplikacije. Subklasa je QWidgeta zbog metode connect
    view je objekt displaya, model je objekt dokumenta
    """
    def __init__(self,parent=None,view=None,model=None):
        QtGui.QWidget.__init__(self,parent)
        
        self.display=view
        
        #connect1:qt akcija ucitavanja -> read csv u dokumentu
        self.connect(view,
                     QtCore.SIGNAL('request_read_csv(PyQt_PyObject)'),
                     model.citaj_csv)
        #connect2: trenutni kljucevi -> update QComboBox liste u view
        self.connect(model,
                     QtCore.SIGNAL('update_kljuc(PyQt_PyObject)'),
                     view.update_kljuc)
                    
        #connect3: view gumb crtaj -> view get_kanal
        self.connect(view.gumbCrtajSatni,
                     QtCore.SIGNAL('clicked()'),
                     view.get_kanal)
                     
        #connect4: view get_kanal -> model set_kanal
        self.connect(view,
                     QtCore.SIGNAL('kanal_odabran(PyQt_PyObject)'),
                     model.set_kanal)
                     
        #connect5: model(set_kanal) signal za crtanje -> view satni graf
        self.connect(model,
                     QtCore.SIGNAL('crtaj_satni(PyQt_PyObject)'),
                     view.canvasSatni.crtaj)

        
        

