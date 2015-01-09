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

from PyQt4 import QtCore, uic #import djela Qt frejmworka
import satniCanvas
import minutniCanvas

base3, form3 = uic.loadUiType('panel_za_canvase.ui')
class GrafPanel(base3, form3):
    """
    Klasa za prikaz grafova
    Sadrzaj ovog panela je sljedeci (kako se prikazuje odozgo prema dolje):
    
    1. self.verticalLayoutSatni
        -placeholder definiran u QtDesigneru (layout)
        -sluzi da se u njega stavi satni canvas
        
    2. self.horizontalLayout
        -horiznotalni layout koji sadrzi 3 elementa
        2.1. self.pushButtonPrethodni
            -QPushButton koji sluzi za prebacivanje dana na prethodni dan
        2.2. self.label
            -QLabel koji sluzi za prikaz naziva glavnog kanala i vremenkog intervala
        2.3. self.pushButtonSljedeci
            -QPushButton koji slizi za prebacivanje dana na sljedeci dan
    
    3. self.verticalLayoutMinutni
        -placeholder definiran u QtDesigneru (QWidget)
        -sluzi da se u njega stavi minutni canvas
        

    
    self.satniGraf --> instanca satnog canvasa       
    self.minutniGraf --> instanca minutnog canvasa
    """
    def __init__(self, parent = None):
        super(base3, self).__init__(parent)
        self.setupUi(self)

        #sredi title panela
        self.setWindowTitle('Grafovi satno agregiranih podataka i minutnih podataka')
        #inicijalizacija canvasa
        self.satniGraf = satniCanvas.Graf(parent = None)
        self.minutniGraf = minutniCanvas.Graf(parent = None)
        #dodavanje canvasa u layout panela
        self.verticalLayoutSatni.addWidget(self.satniGraf)
        self.verticalLayoutMinutni.addWidget(self.minutniGraf)
        
        #gumbi zaduzeni za prebacivanje dana naprijed i nazad
        self.pushButtonSljedeci.clicked.connect(self.prebaci_dan_naprijed)
        self.pushButtonPrethodni.clicked.connect(self.prebaci_dan_nazad)
    
    def change_label(self, lista):
        """
        ova funkcija kao ulazni parametar uzima listu koja ima 3 elementa.
        -lista[0] = string, Naziv postaje i glavnog kanala (postaja::kanal)
        -lista[1] = string, timestamp (od)
        -lista[2] = string, timestamp (do)
        Rezultat je novi label sastavljen od tih elemenata.
        """
        naziv = str(lista[0])
        od = str(lista[1])
        do = str(lista[2])
        output = 'Glavni kanal: ' + naziv + '\nOd: ' + od + ' Do: ' + do
        self.label.setText(output)
        
    def prebaci_dan_naprijed(self):
        """
        Signaliziraj kontroleru da treba prebaciti kalendar 1 dan naprjed
        """
        self.emit(QtCore.SIGNAL('prebaci_dan(PyQt_PyObject)'), 1)
    
    def prebaci_dan_nazad(self):
        """
        Signaliziraj kontroleru da treba prebaciti kalendar 1 dan nazad
        """
        self.emit(QtCore.SIGNAL('prebaci_dan(PyQt_PyObject)'), -1)
###############################################################################
###############################################################################