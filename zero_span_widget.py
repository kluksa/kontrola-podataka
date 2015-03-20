# -*- coding: utf-8 -*-
"""
Created on Fri Feb  6 12:59:14 2015

@author: User
"""

from PyQt4 import uic

import pomocne_funkcije

###############################################################################
###############################################################################
base7, form7 = uic.loadUiType('./ui_files/zero_span_widget.ui')
class ZeroSpanIzbor(base7, form7):
    """
    Opcije za ZERO i SPAN graf (koristi se ista shema)
    """
    def __init__(self, parent = None, defaulti = {}, listHelpera = []):
        """
        Inicijalizacija sa 
        
        defaulti
            --> nested dictom opcija grafova
            
        listHelpera
        --> lista koja sadrzi dictove sa konverziju matplotlib vrijednositi
            u smislenije podatke i nazad .. npr '-' : 'Puna linija'
            
        --> struktura liste je definirana na sljedeci nacin po poziciji:
            element 0 : mpl.marker --> opisni marker
            element 1 : opisni marker --> mpl.marker
            element 2 : mpl.linestyle --> opis stila linije
            element 3 : opis stila linije --> mpl.linestyle
            element 4 : agregirani kanal --> dulji opis kanala
            element 5 : dulji opis kanala --> agregirani kanal            
        """
        super(base7, self).__init__(parent)
        self.setupUi(self)
        
        markeri = sorted(list(listHelpera[1].keys()))
        linije = sorted(list(listHelpera[3].keys()))
        
        ###MARKER###
        #zero
        self.zeroMarker.addItems(markeri)
        mk = listHelpera[0][defaulti.zeroVOK.markerStyle]
        self.zeroMarker.setCurrentIndex(self.zeroMarker.findText(mk))
        #span
        self.spanMarker.addItems(markeri)
        mk = listHelpera[0][defaulti.spanVOK.markerStyle]
        self.spanMarker.setCurrentIndex(self.spanMarker.findText(mk))
        #size zero i span markera
        self.markerSize.setValue(defaulti.zeroVOK.markerSize)
        #boja dobrih markera
        self.set_widget_color_style(defaulti.zeroVOK.rgb, defaulti.zeroVOK.alpha, "QPushButton", self.bojaOK)
        #boja losih markera
        self.set_widget_color_style(defaulti.zeroVBAD.rgb, defaulti.zeroVBAD.alpha, "QPushButton", self.bojaBAD)
        #prozirnost markera
        self.markerAlpha.setValue(defaulti.zeroVOK.alpha)
        ###midline###
        #stil linije
        self.midlineStil.addItems(linije)
        ls = listHelpera[2][defaulti.zeroMidline.lineStyle]
        self.midlineStil.setCurrentIndex(self.midlineStil.findText(ls))
        #sirina linije
        self.midlineWidth.setValue(defaulti.zeroMidline.lineWidth)
        #boja centralne linije
        self.set_widget_color_style(defaulti.zeroMidline.rgb, defaulti.zeroMidline.alpha, "QPushButton", self.midlineBoja)
        #alpha vrijednost centralne linije
        self.midlineAlpha.setValue(defaulti.zeroMidline.alpha)
        ###warning lnija###
        #stil linije
        self.warningStil.addItems(linije)
        ls = listHelpera[2][defaulti.zeroWarning1.lineStyle]
        self.warningStil.setCurrentIndex(self.warningStil.findText(ls))
        #sirina linije
        self.warningWidth.setValue(defaulti.zeroWarning1.lineWidth)
        #boja linije
        self.set_widget_color_style(defaulti.zeroWarning1.rgb, defaulti.zeroWarning1.alpha, "QPushButton", self.warningBoja)
        #prozirnost
        self.warningAlpha.setValue(defaulti.zeroWarning1.alpha)
        #test za crtanje
        self.warningCrtaj.setChecked(defaulti.zeroWarning1.crtaj)
        if defaulti.zeroWarning1.crtaj:
            self.warningStil.setEnabled(True)
            self.warningWidth.setEnabled(True)
            self.warningBoja.setEnabled(True)
            self.warningAlpha.setEnabled(True)
        else:
            self.warningStil.setEnabled(False)
            self.warningWidth.setEnabled(False)
            self.warningBoja.setEnabled(False)
            self.warningAlpha.setEnabled(False)
        ###fill###
        #fill OK
        self.set_widget_color_style(defaulti.zeroFill1.rgb, defaulti.zeroFill1.alpha, "QPushButton", self.fillBojaOK)
        #fill BAD
        self.set_widget_color_style(defaulti.zeroFill2.rgb, defaulti.zeroFill2.alpha, "QPushButton", self.fillBojaBAD)
        #aplha
        self.fillAlpha.setValue(defaulti.zeroFill1.alpha)
        #test za crtanje
        self.fillCrtaj.setChecked(defaulti.zeroFill1.crtaj)
        if defaulti.zeroFill1.crtaj:
            self.fillBojaOK.setEnabled(True)
            self.fillBojaBAD.setEnabled(True)
            self.fillAlpha.setEnabled(True)
        else:
            self.fillBojaOK.setEnabled(False)
            self.fillBojaBAD.setEnabled(False)
            self.fillAlpha.setEnabled(False)
###############################################################################
    def set_widget_color_style(self, rgb, a, tip, target):
        """
        izrada stila widgeta
        tip - qwidget tip, npr "QPushButton"
        target - instanca widgeta kojem mjenjamo stil
        """
        #get string name of target object
        name = str(target.objectName())
        #napravi stil
        stil = pomocne_funkcije.rgba_to_style_string(rgb, a , tip, name)
        #set stil u target
        target.setStyleSheet(stil)
###############################################################################
###############################################################################