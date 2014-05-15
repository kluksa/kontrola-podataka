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

class Mediator(QtGui.QWidget):
    """
    Pokusaj implementacije Mediator patterna
    
    Inicijalizacija mediatora:
        -kao argumente mu treba prosljediti gui instancu i instancu modela
    """
    def __init__(self,parent=None,gui=None,model=None):
        QtGui.QWidget.__init__(self,parent)
        """
        Nekoliko membera
        """
        self.lastLoadedFile=None
        self.trenutnaListaKanala=None
        self.trenutnaListaSati=None
        self.lastKanal=None
        self.lastSat=None
        
        """
        Connections
        """
        #status bar updates (jedino direktno spajanje modela i gui)
        self.connect(self,
                     QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),
                     gui.set_status_bar)

        self.connect(gui,
                     QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),
                     gui.set_status_bar)

        self.connect(model,
                     QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),
                     gui.set_status_bar)
        
        #read csv procedure
        self.connect(gui,
                     QtCore.SIGNAL('gui_request_read_csv(PyQt_PyObject)'),
                     self.med_read_csv)

        self.connect(self,
                     QtCore.SIGNAL('med_request_read_csv(PyQt_PyObject)'),
                     model.citaj_csv)

        self.connect(model,
                     QtCore.SIGNAL('doc_get_kljucevi(PyQt_PyObject)'),
                     self.set_trenutnaListaKanala)

        self.connect(self,
                     QtCore.SIGNAL('med_update_kanali(PyQt_PyObject)'),
                     gui.set_kanali)

        
        #crtaj satni procedure
        self.connect(gui,
                     QtCore.SIGNAL('gui_request_crtaj_satni(PyQt_PyObject)'),
                     self.med_request_crtaj_satni)
        
        self.connect(self,
                     QtCore.SIGNAL('med_request_draw_satni(PyQt_PyObject)'),
                     model.doc_pripremi_satne_podatke)
                     
        self.connect(model,
                     QtCore.SIGNAL('doc_draw_satni(PyQt_PyObject)'),
                     self.med_naredi_crtaj_satni)

        self.connect(self,
                     QtCore.SIGNAL('med_draw_satni(PyQt_PyObject)'),
                     gui.canvasSatni.crtaj)
                     

###############################################################################

    def med_read_csv(self,filepath):
        self.lastLoadedFile=filepath
        message='Loading and preparing file '+filepath
        self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),message)
        self.emit(QtCore.SIGNAL('med_request_read_csv(PyQt_PyObject)'),filepath)
    
    
    def med_request_crtaj_satni(self,kanal):
        self.lastKanal=kanal
        message='Drawing aggregated data for '+kanal
        self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),message)
        self.emit(QtCore.SIGNAL('med_request_draw_satni(PyQt_PyObject)'),
                  kanal)
        
    def med_naredi_crtaj_satni(self,dataframe):
        self.emit(QtCore.SIGNAL('med_draw_satni(PyQt_PyObject)'),dataframe)
        
###############################################################################
    def set_lastLoadedFile(self,filepath):
        self.lastLoadedFile=filepath
        
    def set_trenutnaListaKanala(self,kanali):
        self.trenutnaListaKanala=kanali
        self.emit(QtCore.SIGNAL('med_update_kanali(PyQt_PyObject)'),kanali)
        
    def set_trenutnaListaSati(self,sati):
        self.trenutnaListaSati=sati
        self.emit(QtCore.SIGNAL('med_update_sati(PyQt_PyObject)'),sati)
        
    def set_lastKanal(self,kanal):
        self.lastKanal=kanal
        self.emit(QtCore.SIGNAL('med_update_kanal(PyQt_PyObject)'),kanal)
        
    def set_lastSat(self,sat):
        self.lastSat=sat
        self.emit(QtCore.SIGNAL('med_update_sat(PyQt_PyObject)'),sat)
        
        

