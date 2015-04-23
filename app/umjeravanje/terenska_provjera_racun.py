# -*- coding: utf-8 -*-
"""
Created on Tue Apr 21 08:31:06 2015

@author: DHMZ-Milic

Implementacija dijelova za read...
"""

from PyQt4 import QtGui, QtCore, uic
import pandas as pd
import numpy as np

BASE4, FORM4 = uic.loadUiType('terenska_provjera_racun.ui')
class TerenskaProvjeraRacun(BASE4, FORM4):
    """
    Klasa simulira sheet Terenska provjera - racun
    Jos u izradi...

    """
    def __init__(self, parent=None, tocke=None):
        super(BASE4, self).__init__(parent)
        self.setupUi(self)
        self.tocke = tocke #enum raspona za pojedine tocke
        self.workingFrejm = pd.DataFrame()

        self.komponenta = {}
        self.dilucija = {}
        self.cistiZrak = {}
        self.ostaliMeta = {}

        self.linearnostDa.toggled.connect(self.toggle_provjeru_linearnosti_on)
        self.linearnostNe.toggled.connect(self.toggle_provjeru_linearnosti_off)

    def toggle_provjeru_linearnosti_on(self):
        if self.linearnostDa.isChecked():
            print('ukljuci provjeru linearnosti')

    def toggle_provjeru_linearnosti_off(self):
        if self.linearnostNe.isChecked():
            print('iskljuci provjeru linearnosti')

    #TODO! setteri u tablicu bi se dali refactorat na pametniji nacin
    def calc_and_set_cref(self):
        """
        Metoda racuna i postavlja cref u tablicu
        """
        i = 0 #counter reda
        for tocka in self.tocke:
            value = self.izracunaj_cref(tocka=tocka)
            item = QtGui.QTableWidgetItem()
            item.setData(QtCore.Qt.DisplayRole, str(value))
            item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
            self.tableWidget.setItem(i, 0, item)
            i += 1 #move to next row

    def calc_and_set_c(self, stupac):
        """
        Metoda racuna i postavlja c u tablicu
        """
        i = 0 #counter reda
        for tocka in self.tocke:
            value = self.izracunaj_c(tocka=tocka, stupac=stupac)
            item = QtGui.QTableWidgetItem()
            item.setData(QtCore.Qt.DisplayRole, str(value))
            item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
            self.tableWidget.setItem(i, 1, item)
            print(i, 1, value) # TODO! WTF trenutak???
            i += 1 #move to next row

    def calc_and_set_delta(self, stupac):
        """
        Metoda racuna i postavlja deltu u tablicu
        """
        i = 0 #counter reda
        for tocka in self.tocke:
            value = self.izracunaj_odstupanje(tocka=tocka, stupac=stupac)
            item = QtGui.QTableWidgetItem()
            item.setData(QtCore.Qt.DisplayRole, str(value))
            item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
            self.tableWidget.setItem(i, 2, item)
            i += 1 #move to next row

    def calc_and_set_sr(self, stupac):
        """
        Metoda racuna i postavlja sr u tablicu
        """
        i = 0 #counter reda
        for tocka in self.tocke:
            value = self.izracunaj_sr(tocka=tocka, stupac=stupac)
            item = QtGui.QTableWidgetItem()
            item.setData(QtCore.Qt.DisplayRole, str(value))
            item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
            self.tableWidget.setItem(i, 3, item)
            i += 1 #move to next row

    def calc_and_set_r(self, stupac):
        """
        Metoda racuna i postavlja r u tablicu
        """
        i = 0 #counter reda
        for tocka in self.tocke:
            value = self.izracunaj_r(tocka=tocka, stupac=stupac)
            item = QtGui.QTableWidgetItem()
            item.setData(QtCore.Qt.DisplayRole, str(value))
            item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
            self.tableWidget.setItem(i, 4, item)
            i += 1 #move to next row

    def calc_and_set_UR(self):
        i = 0 #counter reda
        for tocka in self.tocke:
            value = self.izracunaj_UR(tocka=tocka)
            item = QtGui.QTableWidgetItem()
            item.setData(QtCore.Qt.DisplayRole, str(value))
            item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
            self.tableWidget.setItem(i, 5, item)
            i += 1 #move to next row

    def set_working_frejm(self, frejm):
        """
        Metoda postavlja tocno definirani pandas dataframe podataka za daljnje
        racunanje.
        """
        self.workingFrejm = frejm
        #TODO! napravi na pametniji nacin
        #populiraj tablicu sa rezultatima
        self.calc_and_set_cref()
        self.calc_and_set_c(0)
        self.calc_and_set_delta(0)
        self.calc_and_set_sr(0)
        self.calc_and_set_r(0)
        self.calc_and_set_UR()

    def set_metadata(self, komponenta, dilucija, cistiZrak, other):
        """
        Metoda salje metapodatke potrebne za racunanje iz norme i drugih izvora
        """
        self.komponenta = komponenta
        self.dilucija = dilucija
        self.cistiZrak = cistiZrak
        self.ostaliMeta = other
        #TODO! force recalculation

    def dohvati_rubove_working_slajsa_za_tocku(self, tocka):
        """
        Pomocna metoda:
        Metoda vraca tuple (min, max) koji su indeksi slajsa s kojim racunamo
        ostale statisticke parametre za zadanu tocku. Zanemarujemo prvih 5 tocaka
        unutar slajsa.
        """
        ind = list(tocka.value)[5:]
        return ind[0], ind[-1]

    def dohvati_working_slajs_za_tocku_i_stupac(self, tocka, stupac):
        """
        Pomocna metoda:
        Metoda vraca working slajs podataka (series), za zadanu tocku i indeks
        stupca.
        """
        if tocka is self.tocke.tocka1:
            low, high = self.dohvati_rubove_working_slajsa_za_tocku(self.tocke.tocka1)
        elif tocka is self.tocke.tocka2:
            low, high = self.dohvati_rubove_working_slajsa_za_tocku(self.tocke.tocka2)
        elif tocka is self.tocke.tocka3:
            low, high = self.dohvati_rubove_working_slajsa_za_tocku(self.tocke.tocka3)
        elif tocka is self.tocke.tocka4:
            low, high = self.dohvati_rubove_working_slajsa_za_tocku(self.tocke.tocka4)
        elif tocka is self.tocke.tocka5:
            low, high = self.dohvati_rubove_working_slajsa_za_tocku(self.tocke.tocka5)
        return self.workingFrejm.iloc[low:high, stupac]

    def izracunaj_cref(self, tocka=None):
        """
        Metoda racuna cref.

        ulazni parametri :
        tocka
        -->enum tocke
        stupac
        -->int indeks stupca working datafrejma za kojeg se racuna cref

        output:
        -->vrijednost cref (float)
        """
        if tocka is self.tocke.tocka1:
            return 0.8 * self.komponenta['opseg']
        elif tocka is self.tocke.tocka2:
            return 0
        elif tocka is self.tocke.tocka3:
            return 0.6 * self.komponenta['opseg']
        elif tocka is self.tocke.tocka4:
            return 0.2 * self.komponenta['opseg']
        elif tocka is self.tocke.tocka5:
            return 0.95 * self.komponenta['opseg']

    def izracunaj_c(self, tocka=None, stupac=0):
        """
        Metoda racuna c.

        ulaz:
        tocka
        --> enum tocke
        stupac
        --> int indeks stupca pod working frejma s kojim radimo

        output:
        --> vrijednost c (float)
        """
        podaci = self.dohvati_working_slajs_za_tocku_i_stupac(tocka, stupac)
        return np.average(podaci)

    def izracunaj_odstupanje(self, tocka=None, stupac=0):
        """
        Metoda racuna razliku cref i c.

        Ulaz:
        tocka
        --> enum tocke
        stupac
        --> int indeks stupca pod working frejma s kojim radimo

        output:
        --> vrijednost razlike cref od c (float)
        """
        cref = self.izracunaj_cref(tocka=tocka)
        c = self.izracunaj_c(tocka=tocka, stupac=stupac)
        return cref - c

    def izracunaj_sr(self, tocka=None, stupac=0):
        """
        Metoda racuna sr.

        Ulaz:
        tocka
        --> enum tocke
        stupac
        --> int indeks stupca pod working frejma s kojim radimo

        output:
        --> stdev podataka (float)

        !!WARNING!!
        numpy.std() funkcija pretpostavlja po defaultu 0 stupnjeva slobode,
        tj. radi std cijele populacije a ne uzorka. U pozivu funkcije moramo
        prosljediti keyword argument ddof=1.
        """
        podaci = self.dohvati_working_slajs_za_tocku_i_stupac(tocka, stupac)
        return np.std(podaci, ddof=1)

    def pripremi_liste_za_racunanje_slope_i_intercept(self, stupac=0):
        """
        Metoda priprema dvije liste za racunanje slope i intercept za provjeru
        linearnosti. Ignorira prvu tocku.

        Ulaz:
        stupac
        --> int indeks stupca pod working frejma s kojim radimo

        output:
        --> tuple koji sadrzi dvije liste (cList, crefList)
        """
        cList = []
        crefList = []
        for tocka in self.tocke:
            if tocka is not self.tocke.tocka1:
                cList.append(self.izracunaj_c(tocka=tocka, stupac=stupac))
                crefList.append(self.izracunaj_cref(tocka=tocka))
        return cList, crefList

    def izracunaj_slope(self, stupac=0):
        """
        Metoda racuna slope prilikom provjere linearnosti.

        Ulaz:
        stupac
        --> int indeks stupca pod working frejma s kojim radimo

        output:
        --> float vrijednost nagiba pravca
        """
        cList, crefList = self.pripremi_liste_za_racunanje_slope_i_intercept(stupac=stupac)
        return np.polyfit(crefList, cList, 1)[0]

    def izracunaj_intercept(self, stupac=0):
        """
        Metoda racuna intercept sa y-osi prilikom provjere linearnosti.

        Ulaz:
        stupac
        --> int indeks stupca pod working frejma s kojim radimo

        output:
        --> float vrijednost intercepta sa y-osi
        """
        cList, crefList = self.pripremi_liste_za_racunanje_slope_i_intercept(stupac=stupac)
        return np.polyfit(crefList, cList, 1)[1]

    def izracunaj_r(self, tocka=None, stupac=0):
        """
        Metoda racuna r.

        Ulaz:
        tocka
        --> enum tocke
        stupac
        --> int indeks stupca pod working frejma s kojim radimo

        output:
        --> float vrijednost r
        """
        if tocka is self.tocke.tocka1:
            return 0
        elif tocka is self.tocke.tocka2:
            c = self.izracunaj_c(tocka=tocka, stupac=stupac)
            cref = self.izracunaj_cref(tocka=tocka)
            slope = self.izracunaj_slope(stupac=stupac)
            intercept = self.izracunaj_intercept(stupac=stupac)
            return abs(c - (cref * slope + intercept))
        else:
            c = self.izracunaj_c(tocka=tocka, stupac=stupac)
            cref = self.izracunaj_cref(tocka=tocka)
            slope = self.izracunaj_slope(stupac=stupac)
            intercept = self.izracunaj_intercept(stupac=stupac)
            return abs((c - (cref * slope + intercept))/ cref)

    def izracunaj_UR(self, tocka=None):
        """
        skip midkorake i direktni racun UR
        """
        cref = self.izracunaj_cref(tocka=tocka)
        ufz = self.dilucija['MFC_NULL_PLIN_U']*(cref*(self.ostaliMeta['CRM_C']-cref)/self.ostaliMeta['CRM_C'])
        ufm = self.dilucija['MFC_KAL_PLIN_U']*(cref*(self.ostaliMeta['CRM_C']-cref)/self.ostaliMeta['CRM_C'])
        ucr = cref*self.ostaliMeta['CRM_sljedivost']/200
        ucz = (self.ostaliMeta['CRM_C']-cref)*(self.komponenta['srz'])*(self.ostaliMeta['CRM_C'])/np.sqrt(3)
        out = np.sqrt(ufz**2+ufm**2+ucr**2+(2*ucz)**2)
        return out
