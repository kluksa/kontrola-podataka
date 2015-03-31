# -*- coding: utf-8 -*-
"""
Created on Mon Nov 10 08:50:02 2014

@author: User

Panel za grafove.
Wrapper koji sadrzi:
    1. label sa informacijom o glavnom kanalu te vremenskom slajsu.
    2. gumbe za navigaciju (prethodni i sljedeci dan)
    3. satni canvas (canvas za prikaz satno agregiranih podataka)
    4. minutni canvas (canvas za prikaz minutnih podataka)
"""

from PyQt4 import QtCore, uic 
import satni_canvas
import minutni_canvas
import zero_span_canvas
import logging
###############################################################################
###############################################################################
base2, form2 = uic.loadUiType('./ui_files/konc_graf_panel.ui')
class KoncPanel(base2, form2):
    """
    Klasa za prikaz grafova
    Sadrzaj ovog panela je sljedeci (kako se prikazuje odozgo prema dolje):
    
    1. self.glavniLabel
        -QLabel koji sluzi za prikaz trenutno aktivnog kanala
        (stanica, formula, kanal, mjerna jedinica...)
        
    2. self.verticalLayoutSatni
        -placeholder definiran u QtDesigneru (layout)
        -sluzi da se u njega stavi satni canvas
        
    3. self.horizontalLayout
        -horiznotalni layout koji sadrzi 3 elementa
        2.1. self.buttonPrethodni
            -QPushButton koji sluzi za prebacivanje dana na prethodni dan
        2.2. self.satLabel
            -QLabel koji sluzi za prikaz naziva glavnog kanala i vremenkog intervala
        2.3. self.buttonSljedeci
            -QPushButton koji slizi za prebacivanje dana na sljedeci dan
    
    4. self.verticalLayoutMinutni
        -placeholder definiran u QtDesigneru (QWidget)
        -sluzi da se u njega stavi minutni canvas
        

    
    self.satniGraf --> instanca satnog canvasa       
    self.minutniGraf --> instanca minutnog canvasa
    """
    def __init__(self, parent = None):
        """
        init ide sa appSettings zbog inicijalne postavke interakcije sa grafovima
        """
        super(base2, self).__init__(parent)
        self.setupUi(self)

        #inicijalizacija canvasa
        self.satniGraf = satni_canvas.Graf(parent = None)
        self.minutniGraf = minutni_canvas.Graf(parent = None)
        #dodavanje canvasa u layout panela
        self.verticalLayoutSatni.addWidget(self.satniGraf)
        self.verticalLayoutMinutni.addWidget(self.minutniGraf)
        
        #gumbi zaduzeni za prebacivanje dana naprijed i nazad
        self.buttonSljedeci.clicked.connect(self.prebaci_dan_naprijed)
        self.buttonPrethodni.clicked.connect(self.prebaci_dan_nazad)
###############################################################################
    def change_glavniLabel(self, lista):
        """
        ova funkcija kao ulazni parametar uzima listu koja ima 3 elementa.
        -lista[0] = mapa, opis kanala (naziv, mjerna jedinica, postaja...)
        -lista[1] = string, datum formata YYYY-MM-DD

        Informacija o izboru se postavlja u label.
        """
        mapa = lista[0]
        datum = lista[1]
        postaja = mapa['postajaNaziv']
        komponenta = mapa['komponentaNaziv']
        formula = mapa['komponentaFormula']
        mjernaJedinica = mapa['komponentaMjernaJedinica']
        opis = '{0}, {1}( {2} ) [{3}]. Datum : {4}'.format(postaja, komponenta, formula, mjernaJedinica, datum)
        self.glavniLabel.setText(opis)
        logging.info('glavniLabel promjenjen, value = {0}'.format(opis))
###############################################################################
    def change_satLabel(self, sat):
        """
        funkcija postavlja string izabranog sata sa satno agregiranog grafa u
        satLabel.
        """
        msg = str(sat)
        self.satLabel.setText(msg)
        logging.info('satLabel promjenjen, value = {0}'.format(msg))
###############################################################################
    def prebaci_dan_naprijed(self):
        """
        Signaliziraj kontroleru da treba prebaciti kalendar 1 dan naprjed
        """
        self.emit(QtCore.SIGNAL('prebaci_dan(PyQt_PyObject)'), 1)
        logging.info('request pomak dana unaprijed')
###############################################################################
    def prebaci_dan_nazad(self):
        """
        Signaliziraj kontroleru da treba prebaciti kalendar 1 dan nazad
        """
        self.emit(QtCore.SIGNAL('prebaci_dan(PyQt_PyObject)'), -1)
        logging.info('request pomak dana unazad')
###############################################################################
###############################################################################
base3, form3 = uic.loadUiType('./ui_files/zero_span_panel.ui')
class ZeroSpanPanel(base3, form3):
    def __init__(self, parent = None):
        super(base3, self).__init__(parent)
        self.setupUi(self)
        #TODO! nakon inicijalizacije canvasa inicijaliziraj interaction mode
        #inicijalizacija canvasa
        self.zeroGraf = zero_span_canvas.ZeroSpanGraf(parent = None, tip = 'zero', lok = 'bottom')
        self.spanGraf = zero_span_canvas.ZeroSpanGraf(parent = None, tip = 'span', lok = 'top')
        #dodavanje canvasa u layout panela
        self.zeroLayout.addWidget(self.zeroGraf)
        self.spanLayout.addWidget(self.spanGraf)

        self.veze()
###############################################################################
    def veze(self):
        """
        povezivanje akcija widgeta sa funkcijama
        """
        self.brojDana.currentIndexChanged.connect(self.promjeni_broj_dana)
        self.dodajZSRef.clicked.connect(self.dodaj_novu_zs_ref_vrijednost)
###############################################################################    
    def dodaj_novu_zs_ref_vrijednost(self):
        """
        Dodavanje nove referentne vrijednosti za zero/span
        """
        logging.info('Request za dodavanjem nove zero/span referentne vrijednosti')
        self.emit(QtCore.SIGNAL('dodaj_novi_zs_ref'))
###############################################################################
    def change_glavniLabel(self, lista):
        """
        ova funkcija kao ulazni parametar uzima listu
        
        -lista[0] = mapa, opis kanala (naziv, mjerna jedinica, postaja...)
        -lista[1] = datum u string formatu YYYY-MM-DD

        Rezultat je novi label sastavljen od tih elemenata.
        """
        mapa = lista[0]
        datum = lista[1]
        postaja = mapa['postajaNaziv']
        komponenta = mapa['komponentaNaziv']
        formula = mapa['komponentaFormula']
        mjernaJedinica = mapa['komponentaMjernaJedinica']
        opis = '{0}, {1}( {2} ) [{3}]. Datum : {4}'.format(postaja, komponenta, formula, mjernaJedinica, datum)
        self.glavniLabel.setText(opis)
        logging.info('glavniLabel promjenjen, value = {0}'.format(opis))
###############################################################################
    def promjeni_broj_dana(self, x):
        """
        -funkcija koja se poziva promjenom broja dana u comboboxu
        -update defaulte, pozovi na ponovno crtanje grafa
        """
        broj = int(self.brojDana.itemText(x))
        logging.info('request za prikazom drugog broja dana, novi = {0}'.format(str(broj)))
        self.emit(QtCore.SIGNAL('request_zs_broj_dana_change(PyQt_PyObject)'), broj)
###############################################################################
    def prikazi_info_zero(self, lista):
        """
        funkcija updatea labele sa informacijom o zero tocki koja je izabrana 
        na grafu [vrijeme, vrijednost, min, max, status]
        """
        self.zeroVrijeme.setText(lista[0])
        self.zeroValue.setText(lista[1])
        self.zeroMinD.setText(lista[2])
        self.zeroMaxD.setText(lista[3])
        self.zeroStatus.setText(lista[4])
###############################################################################
    def prikazi_info_span(self, lista):
        """
        funkcija updatea labele sa informacijom o span tocki koja je izabrana 
        na grafu [vrijeme, vrijednost, min, max, status]
        """
        self.spanVrijeme.setText(lista[0])
        self.spanValue.setText(lista[1])
        self.spanMinD.setText(lista[2])
        self.spanMaxD.setText(lista[3])
        self.spanStatus.setText(lista[4])
###############################################################################
###############################################################################