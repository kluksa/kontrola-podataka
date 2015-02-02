# -*- coding: utf-8 -*-
"""
Created on Mon Feb  2 11:22:25 2015

@author: User

Klasa (canvas) za prikaz Zero vrijednosti (zero/span).
"""
from PyQt4 import QtGui, QtCore

import matplotlib

import pandas as pd

import datetime

import pomocneFunkcije #import pomocnih funkcija
import opcenitiCanvas #import opcenitog (abstract) canvasa
###############################################################################
###############################################################################
class Graf(opcenitiCanvas.MPLCanvas):
    """
    Klasa za prikaz Zero vrijednosti
    """
    def __init__(self, *args, **kwargs):
        """konstruktor"""
        opcenitiCanvas.MPLCanvas.__init__(self, *args, **kwargs)

        self.data = {} #privremeni spremnik za frejmove (ucitane)
###############################################################################
    def crtaj(self, frejm):
        """
        crtanje frejma Zero na canvasu
        """
        self.axes.clear()
        
        x = list(frejm.index)
        y = list(frejm['vrijednost'])
        
        #sredi tickove
        tickLoc, tickLab = pomocneFunkcije.sredi_xtickove_zerospan(x)
        self.axes.set_xticks(tickLoc)
        self.axes.set_xticklabels(tickLab)
        
        self.axes.plot(x, y)
        self.axes.set_xlabel('Vrijeme')
        self.axes.set_ylabel('Zero')
        
        xLabels = self.axes.get_xticklabels()
        for label in xLabels:
            #cilj je lagano zaokrenuti labele da nisu jedan preko drugog
            label.set_rotation(30)
            label.set_fontsize(8)
        
        self.draw()
###############################################################################
###############################################################################
