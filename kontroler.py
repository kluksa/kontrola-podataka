# -*- coding: utf-8 -*-
"""
Created on Fri May  9 13:19:45 2014

@author: velimir
"""

from PyQt4 import QtGui,QtCore
from dokument import Dokument


class KontrolerSignala(QtGui.QWidget):
    """
    Kontrolni dio aplikacije. Subklasa je QWidgeta zbog metode connect
    """
    def __init__(self,parent=None):
        QtGui.QWidget.__init__(self,parent)
        
        """
        ideja je pospajati sve signale i metode sa npr.
        
        self.connect(Dokument.QObject,
                     QtCore.SIGNAL('određeni signal'),
                     GUI.QObject,
                     određena metoda tj. slot Qobjekta)
        """
        pass