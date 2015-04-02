# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 10:45:42 2015

@author: User
"""

import logging

from PyQt4 import QtGui, QtCore, uic

import pomocne_funkcije
from app.view import glavni_graf_widget
import zero_span_widget
import pomocni_grafovi_widget


###############################################################################
###############################################################################
base5, form5 = uic.loadUiType('./ui_files/glavni_dijalog.ui')
class GlavniIzbor(base5, form5):
    """
    Glavni dijalog za izbor opcija grafa
    sastoji se od 4 taba gdje se mogu mjenjati opcije za
    -glavni graf
    -pomocni grafovi
    -zero
    -span
    """
    def __init__(self, parent = None, defaulti = None, opiskanala = {}, stablo = None):
        """
        Inicijalizacija dijaloga
        parent
            --> parent widget prozora, default je None i moze tako ostati
        defaulti 
            --> GrafSettingsDTO objekt
            --> definira izgled grafova
        opiskanala 
            --> dict sa opisom programa mjerenja 
            --> kljuc je programMjerenjaId pod kojim su opisni podaci
            --> bitno za definiranje labela pomocnih kanala
        stablo sorted(list(self.__opis_to_komponenta.keys()))
            --> tree model koji sluzi da dodavanje pomocnih kanala 
            --> tree programa mjerenja (stanica, komponenta, usporedno...)

        - Neke akcije su povezane sa promjenama vise grafova (npr. markerSize je
        zajednicki za zero i span markere...)
        - Te akcije se inicijaliziraju sa jedim od defaulta
        
        #TODO!
        Moguce je promjeniti ini file na nacin da inicijalne postavke dijaloga
        ne odgovaraju nacrtanom stanju.
        Npr.
        - zero/span marker se biraju preko jednog comboboxa
        - taj podatak je zapisan na 4 razlicita mjesta u ini fileu.
            -[ZERO] VOK_markerStyle_   (taj se koristi za inicijalizaciju dijaloga)
            -[ZERO] VBAD_markerStyle_
            -[SPAN] VBAD_markerStyle_
            -[SPAN] VBAD_markerStyle_
        - u ini fileu su svi zapisani jednako, ali to je moguce promjeniti.
        - tek nakon promjene markera u dijalogu ce se svi "ujednaciti"
        """
        super(base5, self).__init__(parent)
        self.setupUi(self)
        
        #ZAPAMTI GLAVNE MEMBERE ZA INICIJALIZACIJU
        self.defaulti = defaulti
        self.mapaKanali = opiskanala
        self.drvo = stablo
        ###PRIPREMA ZA INICIJALIZACIJU POJEDINIH WIDGETA###
        self.definiraj_helper_mape()                
        #inicijalizacija widgeta za izbor i postavljanje u ciljani layout (vidi pojednine klase za detalje)
        self.glavni = glavni_graf_widget.GrafIzbor(defaulti = self.defaulti, listHelpera = self.konverzije)
        self.glavniLay.addWidget(self.glavni)
        
        self.zs = zero_span_widget.ZeroSpanIzbor(defaulti = self.defaulti, listHelpera = self.konverzije)
        self.zsLay.addWidget(self.zs)
        
        self.pomocni = pomocni_grafovi_widget.PomocniIzbor(defaulti = self.defaulti, stablo = self.drvo, cListe = self.comboListe, opisKanala = self.mapaKanali, listHelpera = self.konverzije)
        self.pomocniLay.addWidget(self.pomocni)

        self.veze()
###############################################################################
    def definiraj_helper_mape(self):
        """
        Definiranje pomocnih mapa za pretvaranje matplotlib keywordova u smisleni
        tekst i nazad.
        """
        #STIL MARKERA
        self.__marker_to_opis = {'None':'Bez markera', 
                                 'o':'Krug', 
                                 'v':'Trokut, dolje', 
                                 '^':'Trokut, gore', 
                                 '<':'Trokut, lijevo', 
                                 '>':'Trokut, desno', 
                                 's':'Kvadrat', 
                                 'p':'Pentagon', 
                                 '*':'Zvijezda', 
                                 'h':'Heksagon', 
                                 '+':'Plus', 
                                 'x':'X', 
                                 'd':'Dijamant', 
                                 '_':'Horizontalna linija', 
                                 '|':'Vertikalna linija'}

        self.__opis_to_marker = {'Bez markera':'None', 
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
        
        #STIL LINIJE                  
        self.__line_to_opis = {'None':'Bez linije', 
                               '-':'Puna linija',
                               '--':'Dash - Dash', 
                               '-.':'Dash - Dot', 
                               ':':'Dot'}
        
        self.__opis_to_line = {'Bez linije':'None', 
                               'Puna linija':'-',
                               'Dash - Dash':'--', 
                               'Dash - Dot':'-.', 
                               'Dot':':'}
        
        #KOMPONENTA                       
        self.__komponenta_to_opis = {'min':'Minimum', 
                                     'max':'Maksimum', 
                                     'avg':'Srednja vrijednost', 
                                     'medijan':'Medijan', 
                                     'q05':'5 percentil', 
                                     'q95':'95 percentil'}
        
        self.__opis_to_komponenta = {'Minimum':'min', 
                                     'Maksimum':'max', 
                                     'Srednja vrijednost':'avg', 
                                     'Medijan':'medijan', 
                                     '5 percentil':'q05', 
                                     '95 percentil':'q95'}
        
        self.comboListe = [sorted(list(self.__opis_to_marker.keys())), 
                           sorted(list(self.__opis_to_line.keys()))]
        
        #zapakiraj u listu          
        self.konverzije = [self.__marker_to_opis, 
                           self.__opis_to_marker,
                           self.__line_to_opis, 
                           self.__opis_to_line, 
                           self.__komponenta_to_opis, 
                           self.__opis_to_komponenta]
###############################################################################
    def apply_clicked(self, button):
        """
        Implementacija apply gubma. Emitira se naredba za crtanje grafova.
        """
        if button.text() == 'Apply':
            logging.info('Apply promjene stila grafova')
            #signaliziraj potrebu za promjenom
            self.emit(QtCore.SIGNAL('apply_promjene_izgleda'))
###############################################################################
    def veze(self):
        """
        Qt connectioni izmedju kontrolnih widgeta i funkcija koje mjenjaju
        stanje defaultnih grafova.
        """
        #implementacija apply gumba
        self.buttonBox.clicked.connect(self.apply_clicked)

        ###zero span opcije###
        self.zs.zeroMarker.currentIndexChanged.connect(self.promjena_zs_zeroMarker)
        self.zs.spanMarker.currentIndexChanged.connect(self.promjena_zs_spanMarker)
        self.zs.markerSize.valueChanged.connect(self.promjena_zs_markerSize)
        self.zs.bojaOK.clicked.connect(self.promjena_zs_bojaOK)
        self.zs.bojaBAD.clicked.connect(self.promjena_zs_bojaBAD)
        self.zs.markerAlpha.valueChanged.connect(self.promjena_zs_markerAlpha)
        self.zs.midlineStil.currentIndexChanged.connect(self.promjena_zs_midlineStil)
        self.zs.midlineWidth.valueChanged.connect(self.promjena_zs_midlineWidth)
        self.zs.midlineBoja.clicked.connect(self.promjena_zs_midlineBoja)
        self.zs.midlineAlpha.valueChanged.connect(self.promjena_zs_midlineAlpha)
        self.zs.warningCrtaj.clicked.connect(self.promjena_zs_warningCrtaj)
        self.zs.warningStil.currentIndexChanged.connect(self.promjena_zs_warningStil)
        self.zs.warningWidth.valueChanged.connect(self.promjena_zs_warningWidth)
        self.zs.warningBoja.clicked.connect(self.promjena_zs_warningBoja)
        self.zs.warningAlpha.valueChanged.connect(self.promjena_zs_warningAlpha)
        self.zs.fillCrtaj.clicked.connect(self.promjena_zs_fillCrtaj)
        self.zs.fillBojaOK.clicked.connect(self.promjena_zs_fillBojaOK)
        self.zs.fillBojaBAD.clicked.connect(self.promjena_zs_fillBojaBad)
        self.zs.fillAlpha.valueChanged.connect(self.promjena_zs_fillAlpha)

        ###glavni graf - za satni i minutni graf###
        self.glavni.normalMarker.currentIndexChanged.connect(self.promjena_glavni_normalMarker)
        self.glavni.validanMarker.currentIndexChanged.connect(self.promjena_glavni_validanMarker)
        self.glavni.glavniMarkerSize.valueChanged.connect(self.promjena_glavni_markerSize)
        self.glavni.bojaOK.clicked.connect(self.promjena_glavni_bojaOK)
        self.glavni.bojaBAD.clicked.connect(self.promjena_glavni_bojaBAD)
        self.glavni.glavniMarkerAlpha.valueChanged.connect(self.promjena_glavni_markerAlpha)
        self.glavni.midlineStil.currentIndexChanged.connect(self.promjena_glavni_midlineStil)
        self.glavni.midlineWidth.valueChanged.connect(self.promjena_glavni_midlineWidth)
        self.glavni.midlineBoja.clicked.connect(self.promjena_glavni_midlineBoja)
        self.glavni.midlineAlpha.valueChanged.connect(self.promjena_glavni_midlineAlpha)
        self.glavni.ekstremCrtaj.clicked.connect(self.promjena_glavni_ekstremCrtaj)
        self.glavni.ekstremMarker.currentIndexChanged.connect(self.promjena_glavni_ekstremMarker)
        self.glavni.ekstremSize.valueChanged.connect(self.promjena_glavni_ekstremSize)
        self.glavni.ekstremBoja.clicked.connect(self.promjena_glavni_ekstremBoja)
        self.glavni.ekstremAlpha.valueChanged.connect(self.promjena_glavni_ekstremAlpha)
        self.glavni.fillCrtaj.clicked.connect(self.promjena_glavni_fillCrtaj)
        self.glavni.fillKomponenta1.currentIndexChanged.connect(self.promjena_glavni_fillKomponenta1)
        self.glavni.fillKomponenta2.currentIndexChanged.connect(self.promjena_glavni_fillKomponenta2)
        self.glavni.fillBoja.clicked.connect(self.promjena_glavni_fillBoja)
        self.glavni.fillAlpha.valueChanged.connect(self.promjena_glavni_fillAlpha)
        
        ###dodavanje grafova###
        """
        pomocni_grafovi_widget se sam brine za povezivanje i update grafSettings
        DTO objekta.
        vidi pomocni_grafovi_widget.py za detalje.
        """
###############################################################################
    def promjena_zs_zeroMarker(self, x):
        marker = self.__opis_to_marker[self.zs.zeroMarker.currentText()]
        self.defaulti.zeroVOK.set_markerStyle(marker)
        self.defaulti.zeroVBAD.set_markerStyle(marker)
###############################################################################
    def promjena_zs_spanMarker(self, x):
        marker = self.__opis_to_marker[self.zs.spanMarker.currentText()]
        self.defaulti.spanVOK.set_markerStyle(marker)
        self.defaulti.spanVBAD.set_markerStyle(marker)
###############################################################################
    def promjena_zs_markerSize(self, x):
        out = round(x, 2)
        self.defaulti.zeroVOK.set_markerSize(out)
        self.defaulti.zeroVBAD.set_markerSize(out)
        self.defaulti.spanVOK.set_markerSize(out)
        self.defaulti.spanVBAD.set_markerSize(out)
###############################################################################
    def promjena_zs_bojaOK(self, x):
        #dohvati boju
        rgb = self.defaulti.zeroVOK.rgb
        a = self.defaulti.zeroVOK.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost za min i max ekstreme
            self.defaulti.zeroVOK.set_rgb(rgb)
            self.defaulti.zeroVOK.set_alpha(a)
            self.defaulti.spanVOK.set_rgb(rgb)
            self.defaulti.spanVOK.set_alpha(a)
            #promjeni boju gumba
            self.zs.set_widget_color_style(rgb, a, "QPushButton", self.zs.bojaOK)
            #update alpha vrijednost na displayu
            self.zs.markerAlpha.setValue(a)
###############################################################################
    def promjena_zs_bojaBAD(self, x):
        #dohvati boju
        rgb = self.defaulti.zeroVBAD.rgb
        a = self.defaulti.zeroVBAD.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost za min i max ekstreme
            self.defaulti.zeroVBAD.set_rgb(rgb)
            self.defaulti.zeroVBAD.set_alpha(a)
            self.defaulti.spanVBAD.set_rgb(rgb)
            self.defaulti.spanVBAD.set_alpha(a)
            #promjeni boju gumba
            self.zs.set_widget_color_style(rgb, a, "QPushButton", self.zs.bojaBAD)
            #update alpha vrijednost na displayu
            self.zs.markerAlpha.setValue(a)
###############################################################################
    def promjena_zs_markerAlpha(self, x):
        out = round(x, 2)
        self.defaulti.zeroVOK.set_alpha(out)
        self.defaulti.zeroVBAD.set_alpha(out)
        self.defaulti.spanVOK.set_alpha(out)
        self.defaulti.spanVBAD.set_alpha(out)
        #promjeni boju gumba
        self.zs.set_widget_color_style(self.defaulti.zeroVOK.rgb, out, "QPushButton", self.zs.bojaOK)
        self.zs.set_widget_color_style(self.defaulti.zeroVBAD.rgb, out, "QPushButton", self.zs.bojaBAD)
###############################################################################
    def promjena_zs_midlineStil(self ,x):
        ls = self.__opis_to_line[self.zs.midlineStil.currentText()]
        self.defaulti.zeroMidline.set_lineStyle(ls)
        self.defaulti.spanMidline.set_lineStyle(ls)
###############################################################################
    def promjena_zs_midlineWidth(self, x):
        out = round(x, 2)
        self.defaulti.zeroMidline.set_lineWidth(out)
        self.defaulti.spanMidline.set_lineWidth(out)
###############################################################################
    def promjena_zs_midlineBoja(self, x):
        #dohvati boju
        rgb = self.defaulti.zeroMidline.rgb
        a = self.defaulti.zeroMidline.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost za min i max ekstreme
            self.defaulti.zeroMidline.set_rgb(rgb)
            self.defaulti.zeroMidline.set_alpha(a)
            self.defaulti.spanMidline.set_rgb(rgb)
            self.defaulti.spanMidline.set_alpha(a)
            #promjeni boju gumba
            self.zs.set_widget_color_style(rgb, a, "QPushButton", self.zs.midlineBoja)
            #update alpha vrijednost na displayu
            self.zs.midlineAlpha.setValue(a)
###############################################################################
    def promjena_zs_midlineAlpha(self, x):
        out = round(x, 2)
        self.defaulti.zeroMidline.set_alpha(out)
        self.defaulti.spanMidline.set_alpha(out)
        #promjena boje gumba
        self.zs.set_widget_color_style(self.defaulti.zeroMidline.rgb, out, "QPushButton", self.zs.midlineAlpha)
###############################################################################
    def promjena_zs_warningCrtaj(self, x):
        self.defaulti.zeroWarning1.set_crtaj(x)
        self.defaulti.zeroWarning2.set_crtaj(x)
        self.defaulti.spanWarning1.set_crtaj(x)
        self.defaulti.spanWarning2.set_crtaj(x)
        if x:
            self.zs.warningStil.setEnabled(True)
            self.zs.warningWidth.setEnabled(True)
            self.zs.warningBoja.setEnabled(True)
            self.zs.warningAlpha.setEnabled(True)
        else:
            self.zs.warningStil.setEnabled(False)
            self.zs.warningWidth.setEnabled(False)
            self.zs.warningBoja.setEnabled(False)
            self.zs.warningAlpha.setEnabled(False)        
###############################################################################
    def promjena_zs_warningStil(self, x):
        ls = self.__opis_to_line[self.zs.warningStil.currentText()]
        self.defaulti.zeroWarning1.set_lineStyle(ls)
        self.defaulti.zeroWarning2.set_lineStyle(ls)
        self.defaulti.spanWarning1.set_lineStyle(ls)
        self.defaulti.spanWarning2.set_lineStyle(ls)
###############################################################################
    def promjena_zs_warningWidth(self, x):
        out = round(x, 2)
        self.defaulti.zeroWarning1.set_lineWidth(out)
        self.defaulti.zeroWarning2.set_lineWidth(out)
        self.defaulti.spanWarning1.set_lineWidth(out)
        self.defaulti.spanWarning2.set_lineWidth(out)
###############################################################################
    def promjena_zs_warningBoja(self, x):
        #dohvati boju
        rgb = self.defaulti.zeroWarning1.rgb
        a = self.defaulti.zeroWarning1.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost za min i max ekstreme
            self.defaulti.zeroWarning1.set_rgb(rgb)
            self.defaulti.zeroWarning1.set_alpha(a)
            self.defaulti.zeroWarning2.set_rgb(rgb)
            self.defaulti.zeroWarning2.set_alpha(a)
            self.defaulti.spanWarning1.set_rgb(rgb)
            self.defaulti.spanWarning1.set_alpha(a)
            self.defaulti.spanWarning2.set_rgb(rgb)
            self.defaulti.spanWarning2.set_alpha(a)
            #promjeni boju gumba
            self.zs.set_widget_color_style(rgb, a, "QPushButton", self.zs.warningBoja)
            #update alpha vrijednost na displayu
            self.zs.warningAlpha.setValue(a)        
###############################################################################
    def promjena_zs_warningAlpha(self, x):
        out = round(x, 2)
        self.defaulti.zeroWarning1.set_alpha(out)
        self.defaulti.zeroWarning2.set_alpha(out)
        self.defaulti.spanWarning1.set_alpha(out)
        self.defaulti.spanWarning2.set_alpha(out)
        #promjeni boju gumba
        self.zs.set_widget_color_style(self.defaulti.zeroWarning1.rgb, out, "QPushButton", self.zs.warningAlpha)
###############################################################################
    def promjena_zs_fillCrtaj(self, x):
        self.defaulti.zeroFill1.set_crtaj(x)
        self.defaulti.zeroFill2.set_crtaj(x)
        self.defaulti.spanFill1.set_crtaj(x)
        self.defaulti.spanFill2.set_crtaj(x)
        if x:
            self.zs.fillBojaOK.setEnabled(True)
            self.zs.fillBojaBAD.setEnabled(True)
            self.zs.fillAlpha.setEnabled(True)
        else:
            self.zs.fillBojaOK.setEnabled(False)
            self.zs.fillBojaBAD.setEnabled(False)
            self.zs.fillAlpha.setEnabled(False)            
###############################################################################
    def promjena_zs_fillBojaOK(self, x):
        #dohvati boju
        rgb = self.defaulti.zeroFill1.rgb
        a = self.defaulti.zeroFill1.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost za min i max ekstreme
            self.defaulti.zeroFill1.set_rgb(rgb)
            self.defaulti.zeroFill1.set_alpha(a)
            self.defaulti.spanFill1.set_rgb(rgb)
            self.defaulti.spanFill1.set_alpha(a)
            #promjeni boju gumba
            self.zs.set_widget_color_style(rgb, a, "QPushButton", self.zs.fillBojaOK)
            #update alpha vrijednost na displayu
            self.zs.fillAlpha.setValue(a)        
###############################################################################
    def promjena_zs_fillBojaBad(self, x):
        #dohvati boju
        rgb = self.defaulti.zeroFill2.rgb
        a = self.defaulti.zeroFill2.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost za min i max ekstreme
            self.defaulti.zeroFill2.set_rgb(rgb)
            self.defaulti.zeroFill2.set_alpha(a)
            self.defaulti.spanFill2.set_rgb(rgb)
            self.defaulti.spanFill2.set_alpha(a)
            #promjeni boju gumba
            self.zs.set_widget_color_style(rgb, a, "QPushButton", self.zs.fillBojaBAD)
            #update alpha vrijednost na displayu
            self.zs.fillAlpha.setValue(a)
###############################################################################
    def promjena_zs_fillAlpha(self, x):
        out = round(x, 2)
        self.defaulti.zeroFill1.set_alpha(out)
        self.defaulti.zeroFill2.set_alpha(out)
        self.defaulti.spanFill1.set_alpha(out)
        self.defaulti.spanFill2.set_alpha(out)
        #update color na gumbu
        self.zs.set_widget_color_style(self.defaulti.zeroFill1.rgb, out, "QPushButton", self.zs.fillBojaOK)
        self.zs.set_widget_color_style(self.defaulti.zeroFill2.rgb, out, "QPushButton", self.zs.fillBojaBAD)
###############################################################################
    def promjena_glavni_normalMarker(self, x):
        marker = self.__opis_to_marker[self.glavni.normalMarker.currentText()]
        self.defaulti.satniNVOK.set_markerStyle(marker)
        self.defaulti.satniNVBAD.set_markerStyle(marker)
###############################################################################
    def promjena_glavni_validanMarker(self, x):
        marker = self.__opis_to_marker[self.glavni.validanMarker.currentText()]
        self.defaulti.satniVOK.set_markerStyle(marker)
        self.defaulti.satniVBAD.set_markerStyle(marker)
###############################################################################
    def promjena_glavni_markerSize(self, x):
        out = int(x)
        self.defaulti.satniVOK.set_markerSize(out)
        self.defaulti.satniNVOK.set_markerSize(out)
        self.defaulti.satniVBAD.set_markerSize(out)
        self.defaulti.satniNVBAD.set_markerSize(out)
###############################################################################
    def promjena_glavni_bojaOK(self, x):
        #dohvati boju
        rgb = self.defaulti.satniVOK.rgb
        a = self.defaulti.satniVOK.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost za min i max ekstreme
            self.defaulti.satniVOK.set_rgb(rgb)
            self.defaulti.satniVOK.set_alpha(a)
            self.defaulti.satniNVOK.set_rgb(rgb)
            self.defaulti.satniNVOK.set_alpha(a)
            #promjeni boju gumba
            self.glavni.set_widget_color_style(rgb, a, "QPushButton", self.glavni.bojaOK)
            #update alpha vrijednost na displayu
            self.glavni.glavniMarkerAlpha.setValue(a)
###############################################################################
    def promjena_glavni_bojaBAD(self, x):
        #dohvati boju
        rgb = self.defaulti.satniVBAD.rgb
        a = self.defaulti.satniVBAD.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost za min i max ekstreme
            self.defaulti.satniVBAD.set_rgb(rgb)
            self.defaulti.satniVBAD.set_alpha(a)
            self.defaulti.satniNVBAD.set_rgb(rgb)
            self.defaulti.satniNVBAD.set_alpha(a)
            #promjeni boju gumba
            self.glavni.set_widget_color_style(rgb, a, "QPushButton", self.glavni.bojaBAD)
            #update alpha vrijednost na displayu
            self.glavni.glavniMarkerAlpha.setValue(a)
###############################################################################
    def promjena_glavni_markerAlpha(self, x):
        out = round(x, 2)
        self.defaulti.satniVOK.set_alpha(out)
        self.defaulti.satniNVOK.set_alpha(out)
        self.defaulti.satniVBAD.set_alpha(out)
        self.defaulti.satniNVBAD.set_alpha(out)
        #podesi boje na gumbima
        self.glavni.set_widget_color_style(self.defaulti.satniVOK.rgb, out, "QPushButton", self.glavni.bojaOK)
        self.glavni.set_widget_color_style(self.defaulti.satniVBAD.rgb, out, "QPushButton", self.glavni.bojaBAD)
###############################################################################
    def promjena_glavni_midlineStil(self, x):
        ls = self.__opis_to_line[self.glavni.midlineStil.currentText()]
        self.defaulti.satniMidline.set_lineStyle(ls)
        self.defaulti.minutniMidline.set_lineStyle(ls)
###############################################################################
    def promjena_glavni_midlineWidth(self, x):
        out = round(x, 2)
        self.defaulti.satniMidline.set_lineWidth(out)
        self.defaulti.minutniMidline.set_lineWidth(out)
###############################################################################
    def promjena_glavni_midlineBoja(self, x):
        #dohvati boju
        rgb = self.defaulti.satniMidline.rgb
        a = self.defaulti.satniMidline.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost za min i max ekstreme
            self.defaulti.satniMidline.set_rgb(rgb)
            self.defaulti.satniMidline.set_alpha(a)
            self.defaulti.minutniMidline.set_rgb(rgb)
            self.defaulti.minutniMidline.set_alpha(a)
            #promjeni boju gumba
            self.glavni.set_widget_color_style(rgb, a, "QPushButton", self.glavni.midlineBoja)
            #update alpha vrijednost na displayu
            self.glavni.midlineAlpha.setValue(a)        
###############################################################################
    def promjena_glavni_midlineAlpha(self, x):
        out = round(x, 2)
        self.defaulti.satniMidline.set_alpha(out)
        self.defaulti.minutniMidline.set_alpha(out)
        #promjeni boju gumba
        self.glavni.set_widget_color_style(self.defaulti.satniMidline.rgb, out, "QPushButton", self.glavni.midlineBoja)
###############################################################################
    def promjena_glavni_ekstremCrtaj(self, x):
        self.defaulti.satniEksMin.set_crtaj(x)
        self.defaulti.satniEksMax.set_crtaj(x)
        if x:
            self.glavni.ekstremMarker.setEnabled(True)
            self.glavni.ekstremSize.setEnabled(True)
            self.glavni.ekstremBoja.setEnabled(True)
            self.glavni.ekstremAlpha.setEnabled(True)
        else:
            self.glavni.ekstremMarker.setEnabled(False)
            self.glavni.ekstremSize.setEnabled(False)
            self.glavni.ekstremBoja.setEnabled(False)
            self.glavni.ekstremAlpha.setEnabled(False)            
###############################################################################
    def promjena_glavni_ekstremMarker(self, x):
        marker = self.__opis_to_marker[self.glavni.ekstremMarker.currentText()]
        self.defaulti.satniEksMin.set_markerStyle(marker)
        self.defaulti.satniEksMax.set_markerStyle(marker)
###############################################################################
    def promjena_glavni_ekstremSize(self, x):
        out = int(x)
        self.defaulti.satniEksMin.set_markerSize(out)
        self.defaulti.satniEksMax.set_markerSize(out)
###############################################################################
    def promjena_glavni_ekstremBoja(self, x):
        #dohvati boju
        rgb = self.defaulti.satniEksMin.rgb
        a = self.defaulti.satniEksMin.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost za min i max ekstreme
            self.defaulti.satniEksMin.set_rgb(rgb)
            self.defaulti.satniEksMin.set_alpha(a)
            self.defaulti.satniEksMax.set_rgb(rgb)
            self.defaulti.satniEksMax.set_alpha(a)
            #promjeni boju gumba
            self.glavni.set_widget_color_style(rgb, a, "QPushButton", self.glavni.ekstremBoja)
            #update alpha vrijednost na displayu
            self.glavni.ekstremAlpha.setValue(a)
###############################################################################
    def promjena_glavni_ekstremAlpha(self, x):
        out = round(x, 2)
        self.defaulti.satniEksMin.set_alpha(out)
        self.defaulti.satniEksMax.set_alpha(out)
        #promjeni boju gumba
        self.glavni.set_widget_color_style(self.defaulti.satniEksMin.rgb, out, "QPushButton", self.glavni.ekstremBoja)
###############################################################################
    def promjena_glavni_fillCrtaj(self, x):
        self.defaulti.satniFill.set_crtaj(x)
        if x:
            self.glavni.fillKomponenta1.setEnabled(True)
            self.glavni.fillKomponenta2.setEnabled(True)
            self.glavni.fillBoja.setEnabled(True)
            self.glavni.fillAlpha.setEnabled(True)
        else:
            self.glavni.fillKomponenta1.setEnabled(False)
            self.glavni.fillKomponenta2.setEnabled(False)
            self.glavni.fillBoja.setEnabled(False)
            self.glavni.fillAlpha.setEnabled(False)
###############################################################################
    def promjena_glavni_fillKomponenta1(self, x):
        komp = self.__opis_to_komponenta[self.glavni.fillKomponenta1.currentText()]
        self.defaulti.satniFill.set_komponenta1(komp)
###############################################################################
    def promjena_glavni_fillKomponenta2(self, x):
        komp = self.__opis_to_komponenta[self.glavni.fillKomponenta2.currentText()]
        self.defaulti.satniFill.set_komponenta2(komp)
###############################################################################
    def promjena_glavni_fillBoja(self, x):
        #dohvati boju filla
        rgb = self.defaulti.satniFill.rgb
        a = self.defaulti.satniFill.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost
            self.defaulti.satniFill.set_rgb(rgb)
            self.defaulti.satniFill.set_alpha(a)
            #promjeni boju gumba
            self.glavni.set_widget_color_style(rgb, a, "QPushButton", self.glavni.fillBoja)
            #update alpha vrijednost na displayu
            self.glavni.fillAlpha.setValue(a)
###############################################################################
    def promjena_glavni_fillAlpha(self, x):
        out = round(x, 2)
        self.defaulti.satniFill.set_alpha(out)
        #promjeni boju gumba
        self.glavni.set_widget_color_style(self.defaulti.satniFill.rgb, out, "QPushButton", self.glavni.fillBoja)
###############################################################################
###############################################################################