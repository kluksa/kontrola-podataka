# -*- coding: utf-8 -*-
"""
Created on Fri Feb  6 12:48:25 2015

@author: User
"""

from PyQt4 import uic

import app.general.pomocne_funkcije as pomocne_funkcije
###############################################################################
###############################################################################
base6, form6 = uic.loadUiType('./app/view/ui_files/glavni_graf_widget.ui')


class GrafIzbor(base6, form6):
    """
    Prikaz kontrolnih widgeta za postavljanje opcija glavnog grafa
    npr. boja, tip markera, tip linije, fill, ekstremi itd.

    Inicjializira se sa:
    defaulti
        --> konfiguracijski objekt aplikacije (podaci o grafovima)

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

    def __init__(self, parent=None, defaulti=None, listHelpera=[]):
        super(base6, self).__init__(parent)
        self.setupUi(self)

        markeri = sorted(list(listHelpera[1].keys()))
        linije = sorted(list(listHelpera[3].keys()))
        agKanal = sorted(list(listHelpera[5].keys()))


        ###marker###
        # sirovi, nevalidirani podatak
        self.normalMarker.addItems(markeri)
        normal = listHelpera[0][defaulti.satni.NVOK.markerStyle]
        self.normalMarker.setCurrentIndex(self.normalMarker.findText(normal))
        #validirani podatak
        self.validanMarker.addItems(markeri)
        validan = listHelpera[0][defaulti.satni.VOK.markerStyle]
        self.validanMarker.setCurrentIndex(self.validanMarker.findText(validan))
        #velicina markera
        self.glavniMarkerSize.setValue(defaulti.satni.NVOK.markerSize)
        #boja dobro flagiranih podataka
        self.set_widget_color_style(defaulti.satni.VOK.rgb, defaulti.satni.VOK.alpha, "QPushButton", self.bojaOK)
        #boja lose flagiranih podataka
        self.set_widget_color_style(defaulti.satni.VBAD.rgb, defaulti.satni.VBAD.alpha, "QPushButton", self.bojaBAD)
        #prozirnost markera
        self.glavniMarkerAlpha.setValue(defaulti.satni.VOK.alpha)

        ###centralna linija###
        #stil linije
        self.midlineStil.addItems(linije)
        ml = listHelpera[2][defaulti.satni.Midline.lineStyle]
        self.midlineStil.setCurrentIndex(self.midlineStil.findText(ml))
        #sirina centralne linije
        self.midlineWidth.setValue(defaulti.satni.Midline.lineWidth)
        #boja centralne linije
        self.set_widget_color_style(defaulti.satni.Midline.rgb, defaulti.satni.Midline.alpha, "QPushButton",
                                    self.midlineBoja)
        #prozirnost centralne linije
        self.midlineAlpha.setValue(defaulti.satni.Midline.alpha)

        ###ekstremi###
        self.ekstremCrtaj.setChecked(defaulti.satni.EksMin.crtaj)
        #stil markera ekstremnih vrijednosti
        self.ekstremMarker.addItems(markeri)
        e = listHelpera[0][defaulti.satni.EksMin.markerStyle]
        self.ekstremMarker.setCurrentIndex(self.ekstremMarker.findText(e))
        #velicina markera ekstremnih vrijednosti
        self.ekstremSize.setValue(defaulti.satni.EksMin.markerSize)
        #boja markera ekstremnih vrijednosti
        self.set_widget_color_style(defaulti.satni.EksMin.rgb, defaulti.satni.EksMin.alpha, "QPushButton",
                                    self.ekstremBoja)
        #prozirnost markera ekstremnih vrijednosti
        self.ekstremAlpha.setValue(defaulti.satni.EksMin.alpha)
        #disable/enable kontrole ovisno o statusu checkboxa
        if defaulti.satni.EksMin.crtaj:
            self.ekstremMarker.setEnabled(True)
            self.ekstremSize.setEnabled(True)
            self.ekstremBoja.setEnabled(True)
            self.ekstremAlpha.setEnabled(True)
        else:
            self.ekstremMarker.setEnabled(False)
            self.ekstremSize.setEnabled(False)
            self.ekstremBoja.setEnabled(False)
            self.ekstremAlpha.setEnabled(False)

        ###fill###
        self.fillCrtaj.setChecked(defaulti.satni.Fill.crtaj)
        #izbor komponente1
        self.fillKomponenta1.addItems(agKanal)
        k1 = listHelpera[4][defaulti.satni.Fill.komponenta1]
        self.fillKomponenta1.setCurrentIndex(self.fillKomponenta1.findText(k1))
        #izbor komponente2
        self.fillKomponenta2.addItems(agKanal)
        k2 = listHelpera[4][defaulti.satni.Fill.komponenta2]
        self.fillKomponenta2.setCurrentIndex(self.fillKomponenta2.findText(k2))
        #izbor boje filla
        self.set_widget_color_style(defaulti.satni.Fill.rgb, defaulti.satni.Fill.alpha, "QPushButton", self.fillBoja)
        #izbor prozirnosti filla
        self.fillAlpha.setValue(defaulti.satni.Fill.alpha)
        #enable/disable ovisno o statusu crtanja
        if defaulti.satni.Fill.crtaj:
            self.fillKomponenta1.setEnabled(True)
            self.fillKomponenta2.setEnabled(True)
            self.fillBoja.setEnabled(True)
            self.fillAlpha.setEnabled(True)
        else:
            self.fillKomponenta1.setEnabled(False)
            self.fillKomponenta2.setEnabled(False)
            self.fillBoja.setEnabled(False)
            self.fillAlpha.setEnabled(False)

        #postavke za temperaturu kontejnera (izvan postavljenih granica min i max)
        #za inicijlalizaciju koristim satni graf (minutni je jednak, za sada...)
        #izbor min i max granice dobrih temeperatura
        tempMin = defaulti.satni.temperaturaKontejneraMin
        tempMax = defaulti.satni.temperaturaKontejneraMax
        self.kontejnerMin.setValue(defaulti.satni.temperaturaKontejneraMin)
        self.kontejnerMax.setValue(defaulti.satni.temperaturaKontejneraMax)
        #provjeri za los input (min > max)
        if tempMin > tempMax:
            self.glavni.kontejnerMin.setStyleSheet("QDoubleSpinBox#kontejnerMin {color:rgb(255,0,0)}")
            self.glavni.kontejnerMax.setStyleSheet("QDoubleSpinBox#kontejnerMax {color:rgb(255,0,0)}")

        #izbor stila markera
        self.kontejnerStil.addItems(markeri)
        tmark = listHelpera[0][defaulti.satni.temperaturaKontejnera.markerStyle]
        self.kontejnerStil.setCurrentIndex(self.kontejnerStil.findText(tmark))
        #izbor velicine markera
        self.kontejnerSize.setValue(defaulti.satni.temperaturaKontejnera.markerSize)
        #izbor boje temerature kontejnera
        self.set_widget_color_style(defaulti.satni.temperaturaKontejnera.rgb,
                                    defaulti.satni.temperaturaKontejnera.alpha,
                                    "QPushButton",
                                    self.kontejnerBoja)
        #izbor prozirnosti temperature kontejnera
        self.kontejnerAlpha.setValue(defaulti.satni.temperaturaKontejnera.alpha)
        #enable/disable ovisno o statusu crtanja
        self.kontejnerCrtaj.setChecked(defaulti.satni.temperaturaKontejnera.crtaj)
        if defaulti.satni.Fill.crtaj:
            self.kontejnerAlpha.setEnabled(True)
            self.kontejnerBoja.setEnabled(True)
            self.kontejnerMin.setEnabled(True)
            self.kontejnerMax.setEnabled(True)
            self.kontejnerSize.setEnabled(True)
            self.kontejnerStil.setEnabled(True)
        else:
            self.kontejnerAlpha.setEnabled(False)
            self.kontejnerBoja.setEnabled(False)
            self.kontejnerMin.setEnabled(False)
            self.kontejnerMax.setEnabled(False)
            self.kontejnerSize.setEnabled(False)
            self.kontejnerStil.setEnabled(False)

        ###############################################################################

    def set_widget_color_style(self, rgb, a, tip, target):
        """
        izrada stila widgeta
        tip - qwidget tip, npr "QPushButton"
        target - instanca widgeta kojem mjenjamo stil
        """
        # get string name of target object
        name = str(target.objectName())
        #napravi stil
        stil = pomocne_funkcije.rgba_to_style_string(rgb, a, tip, name)
        #set stil u target
        target.setStyleSheet(stil)
        ###############################################################################
        ###############################################################################