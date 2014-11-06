# -*- coding: utf-8 -*-
"""
Created on Tue Nov  4 15:54:51 2014

@author: User
"""
from PyQt4 import QtGui, uic
import pomocneFunkcije

base2, form2 = uic.loadUiType('dodaj_pomocni_graf.ui')
class IzborPojedinacnogGrafa(base2, form2):
    """
    Klasa za izbor postavki pojedinog grafa
    inicijalizira se sa popisom svih dostupnih kanala
    """
    def __init__(self, parent = None, kanali = []):
        super(base2, self).__init__(parent)
        self.setupUi(self)

        #kanali
        self.__kanali = sorted(kanali)
        if len(self.__kanali) != 0:
            prviKanal = self.__kanali[0]
        else:
            prviKanal = None
        
        #STROGO DEFINIRAN REDOSLJED
        #[kanal, marker, linija, rgb, alpha, zorder, label]
        #defaultne vrijednosti s kojima se prikazuje izbornik
        self.__izlaz = [prviKanal, 'None', '-', (50,50,200), 0.9, 2, None]
               
        #tipovi linija i markera
        #pomocni dict za tip linije
        self.__linije = {'Bez linije':'None', 
                         'Puna linija':'-',
                         'Dash - Dash':'--', 
                         'Dash - Dot':'-.', 
                         'Dot':':'}
        #pomocni dict za tip markera
        self.__markeri = {'Bez markera':'None', 
                          'Krug':'o', 
                          'Trokut, dolje':'v', 
                          'Trokut, gore':'^', 
                          'Trokut, lijevo':'<', 
                          'Trokut, desno':'>', 
                          'Kvadrat':'s', 
                          'Pentagon':'p', 
                          'Zvijezda':'*', 
                          'Heksagon':'h', 
                          'Plus':'+', 
                          'X':'x', 
                          'Dijamant':'d', 
                          'Horizontalna linija':'_', 
                          'Vertikalna linija':'|'}
                          
        self.veze()
        self.initial_setup()
              
    def initial_setup(self):
        """
        inicijalno popunjavanje izbornika
        """
        #napravi sortirane liste s kojima populiras comboboxeve
        markeri = sorted(list((self.__markeri.keys())))
        linije = sorted(list((self.__linije.keys())))

        #popunjavanje comboBoxeva sa izborima
        self.comboKanal.addItems(self.__kanali)
        self.comboMarker.addItems(markeri)
        self.comboLine.addItems(linije)
        self.lineEdit.setText(str(self.comboKanal.currentText()))
        #default boja gumba
        rgb = self.__izlaz[3]
        alpha = self.__izlaz[4]
        self.__boja = pomocneFunkcije.default_color_to_qcolor(rgb, alpha)
        stil = pomocneFunkcije.color_to_style_string("QPushButton#gumbBoja", self.__boja)
        self.gumbBoja.setStyleSheet(stil)
        
    def veze(self):
        self.comboKanal.currentIndexChanged.connect(self.promjena_kanala)
        self.comboMarker.currentIndexChanged.connect(self.promjena_markera)
        self.comboLine.currentIndexChanged.connect(self.promjena_linije)
        self.gumbBoja.clicked.connect(self.promjena_boje)
        self.spinZ.valueChanged.connect(self.promjena_zordera)
        self.lineEdit.textChanged.connect(self.promjena_labela)

    def promjena_labela(self):
        """
        funkcija koja odradjuje mehanizam promjene labela
        -interakcija sa QLineEditom
        """
        self.__izlaz[6] = self.lineEdit.text()
        
    def promjena_boje(self):
        """
        funkcija koja odradjuje mehanizam promjene boje
        -interakcija sa gumbom
        """
        color, test = QtGui.QColorDialog.getRgba(self.__boja.rgba(), self)
        if test:
            color = QtGui.QColor.fromRgba(color)
            if color.isValid():
                boja, alpha = pomocneFunkcije.qcolor_to_default_color(color)
                #zapamti izabranu boju
                self.__boja = color
                self.__izlaz[3] = boja
                self.__izlaz[4] = alpha
                #promjeni boju gumba
                stil = pomocneFunkcije.color_to_style_string("QPushButton#gumbBoja", self.__boja)
                self.gumbBoja.setStyleSheet(stil)
               
    
    def promjena_kanala(self):
        """
        funkcija odradjuje promjenu kanala u comboboxu
        -promjena kanala povlaci promjenu liste self.__izlaz
        """
        self.__izlaz[0] = self.comboKanal.currentText()
    
    def promjena_markera(self):
        """
        funkcija odradjuje promjenu stila markera u comboboxu
        -promjena kanala povlaci promjenu liste self.__izlaz
        """
        self.__izlaz[1] = self.__markeri[self.comboMarker.currentText()]

    
    def promjena_linije(self):
        """
        funkcija odradjuje promjenu stila linije u comboboxu
        -promjena kanala povlaci promjenu liste self.__izlaz
        """
        self.__izlaz[2] = self.__linije[self.comboLine.currentText()]

    
    def promjena_zordera(self):
        """
        funkcija odradjuje promjenu vrijednosti zordera na grafu
        
        visa vrijednost zordera se crta preko nizih vrijednosti zordera
        """
        self.__izlaz[5] = self.spinZ.value()
        
    def vrati_listu_grafa(self):
        """
        mehanizam da se dohvati lista sa podacima o grafu
        """
        return self.__izlaz