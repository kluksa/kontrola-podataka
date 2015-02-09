# -*- coding: utf-8 -*-
"""
Created on Fri Feb  6 12:59:37 2015

@author: User
"""

from PyQt4 import uic

import pomocneFunkcije

###############################################################################
###############################################################################
base23, form23 = uic.loadUiType('SPAN_GRAF_WIDGET.ui')
class SpanIzbor(base23, form23):
    """
    Izbornik za span graf opcije
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
        super(base23, self).__init__(parent)
        self.setupUi(self)

        markeri = sorted(list(listHelpera[1].keys()))
        linije = sorted(list(listHelpera[3].keys()))

        ###QComboBox###
        #napuni sve comboboxeve sa podacima
        self.stilMidline.addItems(linije)
        self.okMarker.addItems(markeri)
        self.badMarker.addItems(markeri)
        self.granicaLine.addItems(linije)

        #getter za vrijednosti iz defaulta
        glavnaLinija = listHelpera[2][defaulti['span']['midline']['line']]
        okM = listHelpera[0][defaulti['span']['ok']['marker']]
        badM = listHelpera[0][defaulti['span']['bad']['marker']]
        wLine = listHelpera[2][defaulti['span']['warning']['line']]
        
        #setter za vrijednosti iz defaulta
        self.stilMidline.setCurrentIndex(self.stilMidline.findText(glavnaLinija))
        self.okMarker.setCurrentIndex(self.okMarker.findText(okM))
        self.badMarker.setCurrentIndex(self.badMarker.findText(badM))
        self.granicaLine.setCurrentIndex(self.granicaLine.findText(wLine))
        
        ###QSpinBox###
        self.okSize.setValue(defaulti['span']['ok']['markersize'])
        self.badSize.setValue(defaulti['span']['bad']['markersize'])
        
        ###QDoubleSpinBox###
        self.sirinaMidline.setValue(defaulti['span']['midline']['linewidth'])
        self.pickMidline.setValue(defaulti['span']['midline']['picker'])
        self.granicaSirina.setValue(defaulti['span']['warning']['linewidth'])
        
        ###QPushButton###
        rgb = defaulti['span']['midline']['rgb']
        a = defaulti['span']['midline']['alpha']
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        stil = pomocneFunkcije.color_to_style_string('QPushButton#bojaMidline', boja)
        self.bojaMidline.setStyleSheet(stil)

        rgb = defaulti['span']['ok']['rgb']
        a = defaulti['span']['ok']['alpha']
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        stil = pomocneFunkcije.color_to_style_string('QPushButton#okBoja', boja)
        self.okBoja.setStyleSheet(stil)

        rgb = defaulti['span']['bad']['rgb']
        a = defaulti['span']['bad']['alpha']
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        stil = pomocneFunkcije.color_to_style_string('QPushButton#badBoja', boja)        
        self.badBoja.setStyleSheet(stil)

        rgb = defaulti['span']['warning']['rgb']
        a = defaulti['span']['warning']['alpha']
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        stil = pomocneFunkcije.color_to_style_string('QPushButton#granicaBoja', boja)        
        self.granicaBoja.setStyleSheet(stil)

        rgb = defaulti['span']['warning']['rgb']
        a = defaulti['span']['warning']['alpha']
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        stil = pomocneFunkcije.color_to_style_string('QPushButton#fillBoja', boja)
        self.fillBoja.setStyleSheet(stil)

        ###QCheckBox###
        self.granicaCheck.setChecked(defaulti['span']['warning']['crtaj'])
        self.fillCheck.setChecked(defaulti['span']['fill']['crtaj'])
###############################################################################
###############################################################################
