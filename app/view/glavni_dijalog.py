# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 10:45:42 2015

@author: User
"""

import logging
from PyQt4 import QtGui, QtCore, uic

import app.general.pomocne_funkcije as pomocne_funkcije
import app.view.glavni_graf_widget as glavni_graf_widget
import app.view.zero_span_widget as zero_span_widget
import app.view.pomocni_grafovi_widget as pomocni_grafovi_widget

###############################################################################
###############################################################################
base5, form5 = uic.loadUiType('./app/view/ui_files/glavni_dijalog.ui')
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
            --> konfiguracijski objekt aplikacije
            --> definira izgled grafova svih grafova
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
        #pomocni grafovi za temperaturu kontejnera
        self.glavni.kontejnerCrtaj.clicked.connect(self.promjena_glavni_kontejnerCrtaj)
        self.glavni.kontejnerAlpha.valueChanged.connect(self.promjena_glavni_kontejnerAlpha)
        self.glavni.kontejnerBoja.clicked.connect(self.promjena_glavni_kontejnerBoja)
        self.glavni.kontejnerSize.valueChanged.connect(self.promjena_glavni_kontejnerSize)
        self.glavni.kontejnerStil.currentIndexChanged.connect(self.promjena_glavni_kontejnerStil)
        self.glavni.kontejnerMax.valueChanged.connect(self.promjena_glavni_kontejnerMax)
        self.glavni.kontejnerMin.valueChanged.connect(self.promjena_glavni_kontejnerMin)
        ###dodavanje grafova###
        """
        pomocni_grafovi_widget se sam brine za povezivanje i update grafSettings
        DTO objekta.
        vidi pomocni_grafovi_widget.py za detalje.
        """
##############################################################################
    def promjena_glavni_kontejnerMin(self, x):
        """Promjena minimalne granice temperature 'dobrih' temperatura kontejnera
        za satni i minutni graf."""
        out = round(x, 2)
        self.defaulti.satni.temperaturaKontejneraMin = out
        self.defaulti.minutni.temperaturaKontejneraMin = out
        if out > self.defaulti.satni.temperaturaKontejneraMax:
            #promjeni boju pozadine widgeta u crvenu
            self.glavni.kontejnerMin.setStyleSheet("QDoubleSpinBox#kontejnerMin {color:rgb(255,0,0)}")
        else:
            #promjeni boju teksta widgeta u crnu
            self.glavni.kontejnerMin.setStyleSheet("QDoubleSpinBox#kontejnerMin {color:rgb(0,0,0)}")

###############################################################################
    def promjena_glavni_kontejnerMax(self, x):
        """Promjena maksimalne granice temperature 'dobrih' temperatura kontejnera
        za satni i minutni graf."""
        out = round(x, 2)
        self.defaulti.satni.temperaturaKontejneraMax = out
        self.defaulti.minutni.temperaturaKontejneraMax = out
        if out < self.defaulti.satni.temperaturaKontejneraMin:
            #promjeni boju teksta widgeta u crvenu
            self.glavni.kontejnerMax.setStyleSheet("QDoubleSpinBox#kontejnerMax {color:rgb(255,0,0)}")
        else:
            #promjeni boju teksta widgeta u crnu
            self.glavni.kontejnerMax.setStyleSheet("QDoubleSpinBox#kontejnerMax {color:rgb(0,0,0)}")
###############################################################################
    def promjena_glavni_kontejnerStil(self, x):
        """Promjena stila markera grafa temperature kontejnera za satni i minutni
        graf"""
        marker = self.__opis_to_marker[self.glavni.kontejnerStil.currentText()]
        self.defaulti.satni.temperaturaKontejnera.set_markerStyle(marker)
        self.defaulti.satni.temperaturaKontejnera.set_markerStyle(marker)
        self.defaulti.minutni.temperaturaKontejnera.set_markerStyle(marker)
        self.defaulti.minutni.temperaturaKontejnera.set_markerStyle(marker)
###############################################################################
    def promjena_glavni_kontejnerSize(self, x):
        """Promjena velicine markera grafa temperature kontejnera za satni i minutni
        graf."""
        out = int(x)
        self.defaulti.satni.temperaturaKontejnera.set_markerSize(out)
        self.defaulti.minutni.temperaturaKontejnera.set_markerSize(out)
###############################################################################
    def promjena_glavni_kontejnerBoja(self, x):
        """Promjena boje grafa temperature kontejnera za satni i minutni graf"""
        #dohvati boju
        rgb = self.defaulti.satni.temperaturaKontejnera.rgb
        a = self.defaulti.satni.temperaturaKontejnera.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost za min i max ekstreme
            self.defaulti.satni.temperaturaKontejnera.set_rgb(rgb)
            self.defaulti.satni.temperaturaKontejnera.set_alpha(a)
            self.defaulti.minutni.temperaturaKontejnera.set_rgb(rgb)
            self.defaulti.minutni.temperaturaKontejnera.set_alpha(a)
            #promjeni boju gumba
            self.glavni.set_widget_color_style(rgb, a, "QPushButton", self.glavni.kontejnerBoja)
            #update alpha vrijednost na displayu
            self.glavni.kontejnerAlpha.setValue(a)
###############################################################################
    def promjena_glavni_kontejnerAlpha(self, x):
        """Promjena transparentnosti grafa temperature kontejnera za satni i minutni
        graf"""
        out = round(x, 2)
        self.defaulti.satni.temperaturaKontejnera.set_alpha(out)
        self.defaulti.minutni.temperaturaKontejnera.set_alpha(out)
        #promjeni boju gumba
        self.glavni.set_widget_color_style(self.defaulti.satni.temperaturaKontejnera.rgb,
                                           out,
                                           "QPushButton",
                                           self.glavni.kontejnerBoja)
###############################################################################
    def promjena_glavni_kontejnerCrtaj(self, x):
        """Promjena statusa crtanja temperature kontejnera za temperature izvan granica
        na satnom i minutnom grafu"""
        if x:
            self.glavni.kontejnerAlpha.setEnabled(True)
            self.glavni.kontejnerBoja.setEnabled(True)
            self.glavni.kontejnerMin.setEnabled(True)
            self.glavni.kontejnerMax.setEnabled(True)
            self.glavni.kontejnerSize.setEnabled(True)
            self.glavni.kontejnerStil.setEnabled(True)
        else:
            self.glavni.kontejnerAlpha.setEnabled(False)
            self.glavni.kontejnerBoja.setEnabled(False)
            self.glavni.kontejnerMin.setEnabled(False)
            self.glavni.kontejnerMax.setEnabled(False)
            self.glavni.kontejnerSize.setEnabled(False)
            self.glavni.kontejnerStil.setEnabled(False)
###############################################################################
    def promjena_zs_zeroMarker(self, x):
        """Promjena tipa markera za zero graf"""
        marker = self.__opis_to_marker[self.zs.zeroMarker.currentText()]
        self.defaulti.zero.VOK.set_markerStyle(marker)
        self.defaulti.zero.VBAD.set_markerStyle(marker)
###############################################################################
    def promjena_zs_spanMarker(self, x):
        """Promjena tipa markera za span graf"""
        marker = self.__opis_to_marker[self.zs.spanMarker.currentText()]
        self.defaulti.span.VOK.set_markerStyle(marker)
        self.defaulti.span.VBAD.set_markerStyle(marker)
###############################################################################
    def promjena_zs_markerSize(self, x):
        """Promjena velicine markera za zero i span graf"""
        out = round(x, 2)
        self.defaulti.zero.VOK.set_markerSize(out)
        self.defaulti.zero.VBAD.set_markerSize(out)
        self.defaulti.span.VOK.set_markerSize(out)
        self.defaulti.span.VBAD.set_markerSize(out)
###############################################################################
    def promjena_zs_bojaOK(self, x):
        """Promjena boje markera za 'dobre' vrijednosti zero i span grafa"""
        #dohvati boju
        rgb = self.defaulti.zero.VOK.rgb
        a = self.defaulti.zero.VOK.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost za min i max ekstreme
            self.defaulti.zero.VOK.set_rgb(rgb)
            self.defaulti.zero.VOK.set_alpha(a)
            self.defaulti.span.VOK.set_rgb(rgb)
            self.defaulti.span.VOK.set_alpha(a)
            #promjeni boju gumba
            self.zs.set_widget_color_style(rgb, a, "QPushButton", self.zs.bojaOK)
            #update alpha vrijednost na displayu
            self.zs.markerAlpha.setValue(a)
###############################################################################
    def promjena_zs_bojaBAD(self, x):
        """Promjena boje markera za 'lose' vrijednosti zero i span grafa"""
        #dohvati boju
        rgb = self.defaulti.zero.VBAD.rgb
        a = self.defaulti.zero.VBAD.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost za min i max ekstreme
            self.defaulti.zero.VBAD.set_rgb(rgb)
            self.defaulti.zero.VBAD.set_alpha(a)
            self.defaulti.span.VBAD.set_rgb(rgb)
            self.defaulti.span.VBAD.set_alpha(a)
            #promjeni boju gumba
            self.zs.set_widget_color_style(rgb, a, "QPushButton", self.zs.bojaBAD)
            #update alpha vrijednost na displayu
            self.zs.markerAlpha.setValue(a)
###############################################################################
    def promjena_zs_markerAlpha(self, x):
        """Promjena transparentnosti markera za vrijednosti zero i span grafa"""
        out = round(x, 2)
        self.defaulti.zero.VOK.set_alpha(out)
        self.defaulti.zero.VBAD.set_alpha(out)
        self.defaulti.span.VOK.set_alpha(out)
        self.defaulti.span.VBAD.set_alpha(out)
        #promjeni boju gumba
        self.zs.set_widget_color_style(self.defaulti.zero.VOK.rgb, out, "QPushButton", self.zs.bojaOK)
        self.zs.set_widget_color_style(self.defaulti.zero.VBAD.rgb, out, "QPushButton", self.zs.bojaBAD)
###############################################################################
    def promjena_zs_midlineStil(self ,x):
        """Promjena stila centralne linije za zero i span graf"""
        ls = self.__opis_to_line[self.zs.midlineStil.currentText()]
        self.defaulti.zero.Midline.set_lineStyle(ls)
        self.defaulti.span.Midline.set_lineStyle(ls)
###############################################################################
    def promjena_zs_midlineWidth(self, x):
        """Promjena sirine centralne linije za zero i span graf"""
        out = round(x, 2)
        self.defaulti.zero.Midline.set_lineWidth(out)
        self.defaulti.span.Midline.set_lineWidth(out)
###############################################################################
    def promjena_zs_midlineBoja(self, x):
        """Promjena boje centralne linije za zero i span graf"""
        #dohvati boju
        rgb = self.defaulti.zero.Midline.rgb
        a = self.defaulti.zero.Midline.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost za min i max ekstreme
            self.defaulti.zero.Midline.set_rgb(rgb)
            self.defaulti.zero.Midline.set_alpha(a)
            self.defaulti.span.Midline.set_rgb(rgb)
            self.defaulti.span.Midline.set_alpha(a)
            #promjeni boju gumba
            self.zs.set_widget_color_style(rgb, a, "QPushButton", self.zs.midlineBoja)
            #update alpha vrijednost na displayu
            self.zs.midlineAlpha.setValue(a)
###############################################################################
    def promjena_zs_midlineAlpha(self, x):
        """Promjena transparentnosti centralne linije za zero i span graf"""
        out = round(x, 2)
        self.defaulti.zero.Midline.set_alpha(out)
        self.defaulti.span.Midline.set_alpha(out)
        #promjena boje gumba
        self.zs.set_widget_color_style(self.defaulti.zero.Midline.rgb, out, "QPushButton", self.zs.midlineBoja)
###############################################################################
    def promjena_zs_warningCrtaj(self, x):
        """Toggle opcije za crtanje granicnih linija za zero i span graf"""
        self.defaulti.zero.Warning1.set_crtaj(x)
        self.defaulti.zero.Warning2.set_crtaj(x)
        self.defaulti.span.Warning1.set_crtaj(x)
        self.defaulti.span.Warning2.set_crtaj(x)
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
        """Promjena stila granicnih linija za zero i span graf"""
        ls = self.__opis_to_line[self.zs.warningStil.currentText()]
        self.defaulti.zero.Warning1.set_lineStyle(ls)
        self.defaulti.zero.Warning2.set_lineStyle(ls)
        self.defaulti.span.Warning1.set_lineStyle(ls)
        self.defaulti.span.Warning2.set_lineStyle(ls)
###############################################################################
    def promjena_zs_warningWidth(self, x):
        """Promjena sirine granicnih linija za zero i span graf"""
        out = round(x, 2)
        self.defaulti.zero.Warning1.set_lineWidth(out)
        self.defaulti.zero.Warning2.set_lineWidth(out)
        self.defaulti.span.Warning1.set_lineWidth(out)
        self.defaulti.span.Warning2.set_lineWidth(out)
###############################################################################
    def promjena_zs_warningBoja(self, x):
        """Promjena boje warning linija za zero i span graf"""
        #dohvati boju
        rgb = self.defaulti.zero.Warning1.rgb
        a = self.defaulti.zero.Warning1.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost za min i max ekstreme
            self.defaulti.zero.Warning1.set_rgb(rgb)
            self.defaulti.zero.Warning1.set_alpha(a)
            self.defaulti.zero.Warning2.set_rgb(rgb)
            self.defaulti.zero.Warning2.set_alpha(a)
            self.defaulti.span.Warning1.set_rgb(rgb)
            self.defaulti.span.Warning1.set_alpha(a)
            self.defaulti.span.Warning2.set_rgb(rgb)
            self.defaulti.span.Warning2.set_alpha(a)
            #promjeni boju gumba
            self.zs.set_widget_color_style(rgb, a, "QPushButton", self.zs.warningBoja)
            #update alpha vrijednost na displayu
            self.zs.warningAlpha.setValue(a)
###############################################################################
    def promjena_zs_warningAlpha(self, x):
        """Promjena transparentnosti granicnih linija za zero i span graf"""
        out = round(x, 2)
        self.defaulti.zero.Warning1.set_alpha(out)
        self.defaulti.zero.Warning2.set_alpha(out)
        self.defaulti.span.Warning1.set_alpha(out)
        self.defaulti.span.Warning2.set_alpha(out)
        #promjeni boju gumba
        self.zs.set_widget_color_style(self.defaulti.zero.Warning1.rgb, out, "QPushButton", self.zs.warningBoja)
###############################################################################
    def promjena_zs_fillCrtaj(self, x):
        """Toggle crtanja sjencanih dijelova za zero i span graf"""
        self.defaulti.zero.Fill1.set_crtaj(x)
        self.defaulti.zero.Fill2.set_crtaj(x)
        self.defaulti.span.Fill1.set_crtaj(x)
        self.defaulti.span.Fill2.set_crtaj(x)
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
        """Promjena boje za fill izmedju warning linija za zero i span graf.
        (dobre vrijednosti)"""
        #dohvati boju
        rgb = self.defaulti.zero.Fill1.rgb
        a = self.defaulti.zero.Fill1.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost za min i max ekstreme
            self.defaulti.zero.Fill1.set_rgb(rgb)
            self.defaulti.zero.Fill1.set_alpha(a)
            self.defaulti.span.Fill1.set_rgb(rgb)
            self.defaulti.span.Fill1.set_alpha(a)
            #promjeni boju gumba
            self.zs.set_widget_color_style(rgb, a, "QPushButton", self.zs.fillBojaOK)
            #update alpha vrijednost na displayu
            self.zs.fillAlpha.setValue(a)
###############################################################################
    def promjena_zs_fillBojaBad(self, x):
        """Promjena boje za fill izvan warning linija za zero i span graf.
        (lose vrijednosti)"""
        #dohvati boju
        rgb = self.defaulti.zero.Fill2.rgb
        a = self.defaulti.zero.Fill2.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost za min i max ekstreme
            self.defaulti.zero.Fill2.set_rgb(rgb)
            self.defaulti.zero.Fill2.set_alpha(a)
            self.defaulti.span.Fill2.set_rgb(rgb)
            self.defaulti.span.Fill2.set_alpha(a)
            #promjeni boju gumba
            self.zs.set_widget_color_style(rgb, a, "QPushButton", self.zs.fillBojaBAD)
            #update alpha vrijednost na displayu
            self.zs.fillAlpha.setValue(a)
###############################################################################
    def promjena_zs_fillAlpha(self, x):
        """Promjena transparentnosti sjencanih podrucja za zero i span graf"""
        out = round(x, 2)
        self.defaulti.zero.Fill1.set_alpha(out)
        self.defaulti.zero.Fill2.set_alpha(out)
        self.defaulti.span.Fill1.set_alpha(out)
        self.defaulti.span.Fill2.set_alpha(out)
        #update color na gumbu
        self.zs.set_widget_color_style(self.defaulti.zero.Fill1.rgb, out, "QPushButton", self.zs.fillBojaOK)
        self.zs.set_widget_color_style(self.defaulti.zero.Fill2.rgb, out, "QPushButton", self.zs.fillBojaBAD)
###############################################################################
    def promjena_glavni_normalMarker(self, x):
        """Promjena tipa markera za satni i minutni graf. Marker je za nevalidirane podatke."""
        marker = self.__opis_to_marker[self.glavni.normalMarker.currentText()]
        self.defaulti.satni.NVOK.set_markerStyle(marker)
        self.defaulti.satni.NVBAD.set_markerStyle(marker)
        self.defaulti.minutni.NVOK.set_markerStyle(marker)
        self.defaulti.minutni.NVBAD.set_markerStyle(marker)
###############################################################################
    def promjena_glavni_validanMarker(self, x):
        """Promjena tipa markera za satni i minutni graf. Marker je za validirane podatke."""
        marker = self.__opis_to_marker[self.glavni.validanMarker.currentText()]
        self.defaulti.satni.VOK.set_markerStyle(marker)
        self.defaulti.satni.VBAD.set_markerStyle(marker)
        self.defaulti.minutni.VOK.set_markerStyle(marker)
        self.defaulti.minutni.VBAD.set_markerStyle(marker)
###############################################################################
    def promjena_glavni_markerSize(self, x):
        """Promjena velicine markera za satni i minutni graf"""
        out = int(x)
        self.defaulti.satni.VOK.set_markerSize(out)
        self.defaulti.satni.NVOK.set_markerSize(out)
        self.defaulti.satni.VBAD.set_markerSize(out)
        self.defaulti.satni.NVBAD.set_markerSize(out)
        self.defaulti.minutni.VOK.set_markerSize(out)
        self.defaulti.minutni.NVOK.set_markerSize(out)
        self.defaulti.minutni.VBAD.set_markerSize(out)
        self.defaulti.minutni.NVBAD.set_markerSize(out)
###############################################################################
    def promjena_glavni_bojaOK(self, x):
        """Promjena boje dobro flagiranih podataka na satnom i minutnom grafu"""
        #dohvati boju
        rgb = self.defaulti.satni.VOK.rgb
        a = self.defaulti.satni.VOK.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost za min i max ekstreme
            self.defaulti.satni.VOK.set_rgb(rgb)
            self.defaulti.satni.VOK.set_alpha(a)
            self.defaulti.satni.NVOK.set_rgb(rgb)
            self.defaulti.satni.NVOK.set_alpha(a)
            self.defaulti.minutni.VOK.set_rgb(rgb)
            self.defaulti.minutni.VOK.set_alpha(a)
            self.defaulti.minutni.NVOK.set_rgb(rgb)
            self.defaulti.minutni.NVOK.set_alpha(a)
            #promjeni boju gumba
            self.glavni.set_widget_color_style(rgb, a, "QPushButton", self.glavni.bojaOK)
            #update alpha vrijednost na displayu
            self.glavni.glavniMarkerAlpha.setValue(a)
###############################################################################
    def promjena_glavni_bojaBAD(self, x):
        """Promjena boje lose flagiranih podataka na satnom i minutnom grafu"""
        #dohvati boju
        rgb = self.defaulti.satni.VBAD.rgb
        a = self.defaulti.satni.VBAD.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost za min i max ekstreme
            self.defaulti.satni.VBAD.set_rgb(rgb)
            self.defaulti.satni.VBAD.set_alpha(a)
            self.defaulti.satni.NVBAD.set_rgb(rgb)
            self.defaulti.satni.NVBAD.set_alpha(a)
            self.defaulti.minutni.VBAD.set_rgb(rgb)
            self.defaulti.minutni.VBAD.set_alpha(a)
            self.defaulti.minutni.NVBAD.set_rgb(rgb)
            self.defaulti.minutni.NVBAD.set_alpha(a)
            #promjeni boju gumba
            self.glavni.set_widget_color_style(rgb, a, "QPushButton", self.glavni.bojaBAD)
            #update alpha vrijednost na displayu
            self.glavni.glavniMarkerAlpha.setValue(a)
###############################################################################
    def promjena_glavni_markerAlpha(self, x):
        """Promjena transparentnosti markera na satnom i minutnom grafu.
        Samo za 'midline' tocke (srednje vrijednosti koncentracije)."""
        out = round(x, 2)
        self.defaulti.satni.VOK.set_alpha(out)
        self.defaulti.satni.NVOK.set_alpha(out)
        self.defaulti.satni.VBAD.set_alpha(out)
        self.defaulti.satni.NVBAD.set_alpha(out)
        self.defaulti.minutni.VOK.set_alpha(out)
        self.defaulti.minutni.NVOK.set_alpha(out)
        self.defaulti.minutni.VBAD.set_alpha(out)
        self.defaulti.minutni.NVBAD.set_alpha(out)
        #podesi boje na gumbima
        self.glavni.set_widget_color_style(self.defaulti.satni.VOK.rgb, out, "QPushButton", self.glavni.bojaOK)
        self.glavni.set_widget_color_style(self.defaulti.satni.VBAD.rgb, out, "QPushButton", self.glavni.bojaBAD)
###############################################################################
    def promjena_glavni_midlineStil(self, x):
        """Promjena stila centralne linije za satni i minutni graf"""
        ls = self.__opis_to_line[self.glavni.midlineStil.currentText()]
        self.defaulti.satni.Midline.set_lineStyle(ls)
        self.defaulti.minutni.Midline.set_lineStyle(ls)
###############################################################################
    def promjena_glavni_midlineWidth(self, x):
        """Promjena sirine centralne linije za satni i minutni graf"""
        out = round(x, 2)
        self.defaulti.satni.Midline.set_lineWidth(out)
        self.defaulti.minutni.Midline.set_lineWidth(out)
###############################################################################
    def promjena_glavni_midlineBoja(self, x):
        """Promjena boje centralne linije za satni i minutni graf"""
        #dohvati boju
        rgb = self.defaulti.satni.Midline.rgb
        a = self.defaulti.satni.Midline.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost za min i max ekstreme
            self.defaulti.satni.Midline.set_rgb(rgb)
            self.defaulti.satni.Midline.set_alpha(a)
            self.defaulti.minutni.Midline.set_rgb(rgb)
            self.defaulti.minutni.Midline.set_alpha(a)
            #promjeni boju gumba
            self.glavni.set_widget_color_style(rgb, a, "QPushButton", self.glavni.midlineBoja)
            #update alpha vrijednost na displayu
            self.glavni.midlineAlpha.setValue(a)
###############################################################################
    def promjena_glavni_midlineAlpha(self, x):
        """Promjena transparentnosti centralne linije za satni i minutni graf"""
        out = round(x, 2)
        self.defaulti.satni.Midline.set_alpha(out)
        self.defaulti.minutni.Midline.set_alpha(out)
        #promjeni boju gumba
        self.glavni.set_widget_color_style(self.defaulti.satni.Midline.rgb, out, "QPushButton", self.glavni.midlineBoja)
###############################################################################
    def promjena_glavni_ekstremCrtaj(self, x):
        """Toggle crtanja ekstremnih vrijednosti za satni graf"""
        self.defaulti.satni.EksMin.set_crtaj(x)
        self.defaulti.satni.EksMax.set_crtaj(x)
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
        """Promjena tipa markera za ekstremne vrijednosti za satni graf"""
        marker = self.__opis_to_marker[self.glavni.ekstremMarker.currentText()]
        self.defaulti.satni.EksMin.set_markerStyle(marker)
        self.defaulti.satni.EksMax.set_markerStyle(marker)
###############################################################################
    def promjena_glavni_ekstremSize(self, x):
        """Promjena velicine markera za ekstremne vrijednosti za satni graf"""
        out = int(x)
        self.defaulti.satni.EksMin.set_markerSize(out)
        self.defaulti.satni.EksMax.set_markerSize(out)
###############################################################################
    def promjena_glavni_ekstremBoja(self, x):
        """Promjena boje markera za ekstremne vrijednosti za satni graf"""
        #dohvati boju
        rgb = self.defaulti.satni.EksMin.rgb
        a = self.defaulti.satni.EksMin.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost za min i max ekstreme
            self.defaulti.satni.EksMin.set_rgb(rgb)
            self.defaulti.satni.EksMin.set_alpha(a)
            self.defaulti.satni.EksMax.set_rgb(rgb)
            self.defaulti.satni.EksMax.set_alpha(a)
            #promjeni boju gumba
            self.glavni.set_widget_color_style(rgb, a, "QPushButton", self.glavni.ekstremBoja)
            #update alpha vrijednost na displayu
            self.glavni.ekstremAlpha.setValue(a)
###############################################################################
    def promjena_glavni_ekstremAlpha(self, x):
        """Promjena transparentnosti markera za ekstremne vrijednosti za satni graf"""
        out = round(x, 2)
        self.defaulti.satni.EksMin.set_alpha(out)
        self.defaulti.satni.EksMax.set_alpha(out)
        #promjeni boju gumba
        self.glavni.set_widget_color_style(self.defaulti.satni.EksMin.rgb, out, "QPushButton", self.glavni.ekstremBoja)
###############################################################################
    def promjena_glavni_fillCrtaj(self, x):
        """Toggle crtanja osjencanog dijela na satnom grafu"""
        self.defaulti.satni.Fill.set_crtaj(x)
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
        """Promjena komponente za sjencanje (avg, min, max, q05, q95) na satnom grafu"""
        komp = self.__opis_to_komponenta[self.glavni.fillKomponenta1.currentText()]
        self.defaulti.satni.Fill.set_komponenta1(komp)
###############################################################################
    def promjena_glavni_fillKomponenta2(self, x):
        """Promjena komponente za sjencanje (avg, min, max, q05, q95) na satnom grafu"""
        komp = self.__opis_to_komponenta[self.glavni.fillKomponenta2.currentText()]
        self.defaulti.satni.Fill.set_komponenta2(komp)
###############################################################################
    def promjena_glavni_fillBoja(self, x):
        """Promjena boje osjencanog dijela na satnom grafu"""
        #dohvati boju filla
        rgb = self.defaulti.satni.Fill.rgb
        a = self.defaulti.satni.Fill.alpha
        #convert u QColor zbog dijaloga
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test:
            #samo ako je boja dobro definirana
            color = QtGui.QColor.fromRgba(color)
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #set vrijednost
            self.defaulti.satni.Fill.set_rgb(rgb)
            self.defaulti.satni.Fill.set_alpha(a)
            #promjeni boju gumba
            self.glavni.set_widget_color_style(rgb, a, "QPushButton", self.glavni.fillBoja)
            #update alpha vrijednost na displayu
            self.glavni.fillAlpha.setValue(a)
###############################################################################
    def promjena_glavni_fillAlpha(self, x):
        """Promjena transparentnosti osjencanog dijela na satnom grafu"""
        out = round(x, 2)
        self.defaulti.satni.Fill.set_alpha(out)
        #promjeni boju gumba
        self.glavni.set_widget_color_style(self.defaulti.satni.Fill.rgb, out, "QPushButton", self.glavni.fillBoja)
###############################################################################
###############################################################################