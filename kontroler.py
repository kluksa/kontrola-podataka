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
        
        
        #GUI read csv
        self.connect(gui,
                     QtCore.SIGNAL('gui_request_read_csv(PyQt_PyObject)'),
                    self.med_read_csv)
        
        
    """
    Definicije akcija tj. kontrola
    """
    def med_read_csv(self,filepath):
        """
        -set filepath?
        -test some stuff..to verify input
        -emit filepath to model method to read it
        """
        pass
    
        