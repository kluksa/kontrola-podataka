# -*- coding: utf-8 -*-
"""
Created on Fri Feb 13 12:01:41 2015

@author: User
"""
import pandas as pd

import pomocneFunkcije
from PyQt4 import QtCore, uic

###############################################################################
###############################################################################
base26, form26 = uic.loadUiType('dodavanje_referentnih.ui')
class DijalogDodajRefZS(base26, form26):
    """
    Dijalog za dodavanje novih referentnih vrijednosti za ZERO i SPAN.
    
    polja su:
    
    1. program mjerenja
        --> hardcoded (za sada) opisni string
        --> pokazuju na trenutno aktivni glavni kanal.
        --> potencijalno utrpati tree model za izbor kanala??
    
    2. Pocetak primjene
        --> QDateTimeEdit
        --> izbor vremena od kojega se primjenjuje 
        
    3. Vrsta
        --> combobox sa izborom ZERO ili SPAN
        
    4. Vrijednost
        --> QLineEdit
        --> nova referentna vrijednost
        
    5. Dozvoljeno odstupanje
        --> QLineEdit
        --> tolerancija odstupanja
        --> potencijalno nebitno, jer koliko sam shvatio server automatski racuna
        tu vrijednost???
    """
    
    def __init__(self, parent = None, opisKanal = None, idKanal = None):
        super(base26, self).__init__(parent)
        self.setupUi(self)
        
        #set int id kanala
        self.idKanal = idKanal
        #set program mjerenja opis
        self.programSelect.setText(opisKanal)        
        #set vrijeme da pokazuje trenutak kaada je dijalog inicijaliziran
        self.vrijemeSelect.setDateTime(QtCore.QDateTime.currentDateTime())
        
        self.vrijednostSelect.textEdited.connect(self.check_vrijednost)
###############################################################################
    def check_vrijednost(self, x):
        """
        provjera ispravnosti unosa vrijednosti... samo smisleni brojevi
        """
        self.vrijednostSelect.setStyleSheet('')
        test = self.convert_line_edit_to_float(x)
        if not test:
            self.vrijednostSelect.setStyleSheet('color : red')
###############################################################################
    def convert_line_edit_to_float(self, x):
        """
        pretvaranje line edit stringa u float vrijednost
        
        vrati valjani float ako se string da convertat
        vratni None ako se string ne moze prebaciti u float ili ako nema podataka
        """
        x = str(x)
        if x:
            x = x.replace(',', '.')
            try:
                return float(x)
            except ValueError:
                return None
        else:
            return None
###############################################################################
    def vrati_postavke(self):
        """
        mehanizam kojim dijalog vraca postavke
        """
        #QDateTime objekt
        vrijeme = self.vrijemeSelect.dateTime()
        #convert to python datetime
        vrijeme = vrijeme.toPyDateTime()
        #convert u pandas.tslib.Timestamp
        vrijeme = pd.to_datetime(vrijeme)
        #convert u unix timestamp
        vrijeme = pomocneFunkcije.time_to_int(vrijeme)

        vrsta = self.vrstaSelect.currentText()[0] #samo prvo slovo stringa.. 'Z' ili 'S'
               
        vrijednost = self.convert_line_edit_to_float(self.vrijednostSelect.text()) #float
        
        out = {'vrsta':vrsta, 
               'vrijednost':vrijednost, 
               'vrijeme':vrijeme, 
               'kanal':self.idKanal}
        return out
###############################################################################
###############################################################################