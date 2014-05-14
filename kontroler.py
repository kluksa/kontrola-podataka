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
                     
        #connect6: model - popis satno agregiranih podataka -> view update combobox
        self.connect(model,
                     QtCore.SIGNAL('popis_satnih(PyQt_PyObject)'),
                     view.set_selektorSata)

        #connect7: view satni graf ljevi klik -> model priprema_crtanja_minutni
        self.connect(view.canvasSatni,
                     QtCore.SIGNAL('odabirSatni(PyQt_PyObject)'),
                     model.priprema_crtanja_minutni)
                     
        #connect8: priprema crtanja minutnih -> crtanje na minutnom canvasu
        self.connect(model,
                     QtCore.SIGNAL('crtaj_minutni(PyQt_PyObject)'),
                     view.canvasMinutni.crtaj)
                     
        #connect9: view crtaj minutni gumb -> view get sat
        self.connect(view.gumbCrtajMinutni,
                     QtCore.SIGNAL('clicked()'),
                     view.get_odabrani_sat)
                     
        #connect10: view get sat -> model set sat i crtaj graf
        self.connect(view,
                     QtCore.SIGNAL('set_odabrani_sat(PyQt_PyObject)'),
                     model.set_odabrani_sat)
                     
        #connect11: model -> set satni combobox preko set_odabrani_sat +crtanje
        #preko model.priprema_crtanja_minutni
        self.connect(model,
                     QtCore.SIGNAL('set_satni_combobox(PyQt_PyObject)'),
                     view.set_odabrani_sat)
                                      
                     
    