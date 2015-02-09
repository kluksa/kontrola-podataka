# -*- coding: utf-8 -*-
"""
Created on Fri Feb  6 12:48:25 2015

@author: User
"""

from PyQt4 import uic

import pomocneFunkcije

###############################################################################
###############################################################################
base21, form21 = uic.loadUiType('GLAVNI_GRAF_WIDGET.ui')
class GrafIzbor(base21, form21):
    """
    Prikaz kontrolnih widgeta za postavljanje opcija glavnog grafa
    npr. boja, tip markera, tip linije, fill, ekstremi itd.
    
    Inicjializira se sa:
    defaulti
        --> dict podataka sa opisom grafova
    
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
    def __init__(self, parent = None, defaulti = {}, listHelpera = []):
        super(base21, self).__init__(parent)
        self.setupUi(self)
        
        markeri = sorted(list(listHelpera[1].keys()))
        linije = sorted(list(listHelpera[3].keys()))
        agKanal = sorted(list(listHelpera[5].keys()))
        
        ###QComboBox###
        #popunjavanje comboboxeva sa izborima
        self.normalMarker.addItems(markeri)
        self.validanMarker.addItems(markeri)
        self.stilLinije.addItems(linije)
        self.markerEkstrem.addItems(markeri)
        self.fillKomponenta1.addItems(agKanal)
        self.fillKomponenta2.addItems(agKanal)
        
        #getter i konverzija parametara iz defaulta
        validan = listHelpera[0][defaulti['glavniKanal']['validanOK']['marker']]
        normal = listHelpera[0][defaulti['glavniKanal']['nevalidanOK']['marker']]
        ekstrem = listHelpera[0][defaulti['glavniKanal']['ekstremimin']['marker']]
        fill1 = listHelpera[4][defaulti['glavniKanal']['fillsatni']['data1']]
        fill2 = listHelpera[4][defaulti['glavniKanal']['fillsatni']['data2']]
        linija = listHelpera[2][defaulti['glavniKanal']['midline']['line']]
        
        #setter konvertiranih parametara
        self.normalMarker.setCurrentIndex(self.normalMarker.findText(normal))
        self.validanMarker.setCurrentIndex(self.validanMarker.findText(validan))
        self.markerEkstrem.setCurrentIndex(self.markerEkstrem.findText(ekstrem))
        self.fillKomponenta1.setCurrentIndex(self.fillKomponenta1.findText(fill1))
        self.fillKomponenta2.setCurrentIndex(self.fillKomponenta2.findText(fill2))
        self.stilLinije.setCurrentIndex(self.stilLinije.findText(linija))
        
        ###QCheckBox###
        self.crtajEkstrem.setChecked(defaulti['glavniKanal']['ekstremimin']['crtaj'])
        self.crtajFill.setChecked(defaulti['glavniKanal']['fillsatni']['crtaj'])
        
        ###QSpinBox###
        self.markerSpin.setValue(defaulti['glavniKanal']['validanOK']['markersize'])
        self.markerEkstremSpin.setValue(defaulti['glavniKanal']['ekstremimin']['markersize'])
        
        ###QDoubleSpinBox###
        self.doubleSpinLinije.setValue(defaulti['glavniKanal']['midline']['linewidth'])
        
        ####QPushButton###
        #BOJA OK FLAG
        rgb = defaulti['glavniKanal']['validanOK']['rgb']
        a = defaulti['glavniKanal']['validanOK']['alpha']
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        stil = pomocneFunkcije.color_to_style_string('QPushButton#okFlagGumb', boja)
        self.okFlagGumb.setStyleSheet(stil)
        
        #BOJA BAD FLAG
        rgb = defaulti['glavniKanal']['validanNOK']['rgb']
        a = defaulti['glavniKanal']['validanNOK']['alpha']
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        stil = pomocneFunkcije.color_to_style_string('QPushButton#badFlagGumb', boja)
        self.badFlagGumb.setStyleSheet(stil)
        
        #BOJA EKSTREMA
        rgb = defaulti['glavniKanal']['ekstremimin']['rgb']
        a = defaulti['glavniKanal']['ekstremimin']['alpha']
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        stil = pomocneFunkcije.color_to_style_string('QPushButton#bojaEkstrem', boja)
        self.bojaEkstrem.setStyleSheet(stil)
        
        #BOJA FILL (osjencano podrucje)
        rgb = defaulti['glavniKanal']['fillsatni']['rgb']
        a = defaulti['glavniKanal']['fillsatni']['alpha']
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        stil = pomocneFunkcije.color_to_style_string('QPushButton#bojaFill', boja)
        self.bojaFill.setStyleSheet(stil)
###############################################################################
###############################################################################