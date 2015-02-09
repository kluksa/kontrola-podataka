# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 10:45:42 2015

@author: User
"""

from PyQt4 import QtGui, uic

import glavnigrafwidget
import pomocnigrafoviwidget
import zerografwidget
import spangrafwidget

import pomocneFunkcije
###############################################################################
###############################################################################
base25, form25 = uic.loadUiType('GLAVNIDIJALOG.ui')
class GlavniIzbor(base25, form25):
    """
    Glavni dijalog za izbor opcija grafa
    sastoji se od 4 taba gdje se mogu mjenjati opcije za
    -glavni graf
    -pomocni grafovi
    -zero
    -span
    """
    def __init__(self, parent = None, defaulti = {}, opiskanala = {}, stablo = None):
        """
        Inicijalizacija dijaloga
        parent
            --> parent widget prozora, default je None i moze tako ostati
        
        defaulti 
            --> nested dict sa informacijom o postavkama grafova
        opiskanala 
            --> dict sa opisom programa mjerenja 
            --> kljuc je programMjerenjaId pod kojim su opisni podaci
            
        stablo sorted(list(self.__opis_to_komponenta.keys()))
            --> tree model koji sluzi da dodavanje pomocnih kanala 
            --> tree programa mjerenja (stanica, komponenta, usporedno...)
        """
        super(base25, self).__init__(parent)
        self.setupUi(self)
        
        #ZAPAMTI GLAVNE MEMBERE ZA INICIJALIZACIJU
        self.defaulti = defaulti
        self.mapaKanali = opiskanala
        self.drvo = stablo
        
        ###PRIPREMA ZA INICIJALIZACIJU POJEDINIH WIDGETA###
        self.definiraj_helper_mape()
                
        #inicijalizacija widgeta za izbor (vidi pojednine klase za detalje)
        """
        Klase su zaduzene da se same inicijaliziraju i postave na defaultne postavke
        Dijalog se brine da svaki widget unutar klase ima odgovarajucu promjenu
        "stanja" kako se stvari crtaju.
        
        #TODO!
        stavi self kao parenta pomocnih widgeta za tabove?
        """
        self.glavni = glavnigrafwidget.GrafIzbor(defaulti = self.defaulti, listHelpera = self.konverzije)
        self.pomocni = pomocnigrafoviwidget.PomocniIzbor(defaulti = self.defaulti, stablo = self.drvo, cListe = self.comboListe, opisKanala = self.mapaKanali, listHelpera = self.konverzije)
        self.zero = zerografwidget.ZeroIzbor(defaulti = self.defaulti, listHelpera = self.konverzije)
        self.span = spangrafwidget.SpanIzbor(defaulti = self.defaulti, listHelpera = self.konverzije)
        
        #postavljanje inicijaliziranih izbornika u tabove dijaloga
        self.glavniLay.addWidget(self.glavni)
        self.pomocniLay.addWidget(self.pomocni)
        self.zeroLay.addWidget(self.zero)
        self.spanLay.addWidget(self.span)
        
        #spoji signale sa funkcijama koje updateaju state grafova
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
    def dohvati_postavke(self):
        """
        Mehanizam za vracanje promjenjenih defaulta calleru
        """
        #dohvati dodatne kanale iz table modela pomocnih
        dodatniGrafovi = self.pomocni.vrati_pomocne_grafove()
        #zamjeni pomocneKanale sa dopunjenom verzijom
        self.defaulti['pomocniKanali'] = dodatniGrafovi
        #vrati dict novih postavki (izlaz iz dijaloga)
        return self.defaulti
###############################################################################
    def veze(self):
        """
        Qt connectioni izmedju kontrolnih widgeta i funkcija koje mjenjaju
        stanje defaultnih grafova.
        Problem je precizno pratiti promjene stanja u 4 razlicita taba
        """
        ###glavni graf###
        #promjena izgleda nevalidiranog markera glavnog grafa
        self.glavni.normalMarker.currentIndexChanged.connect(self.glavni_marker_nevalidan)
        #promjena izgleda validiranog markera glavnog grafa
        self.glavni.validanMarker.currentIndexChanged.connect(self.glavni_marker_validan)
        #promjena velicine markera za validne i nevalidne podatke glavnog grafa
        self.glavni.markerSpin.valueChanged.connect(self.glavni_velicina_markera_validan)
        #promjena izgleda centralne linije (linestyle) glavnog grafa
        self.glavni.stilLinije.currentIndexChanged.connect(self.glavni_stil_centralne_linije)
        #promjena sirine centralne linije (linewidth) glavnog grafa
        self.glavni.doubleSpinLinije.valueChanged.connect(self.glavni_sirina_centralne_linije)
        #promjena boje dobro flagiranih markera glavnog grafa
        self.glavni.okFlagGumb.clicked.connect(self.glavni_boja_ok_flag)
        #promjena boje lose flagiranih markera glavnog grafa
        self.glavni.badFlagGumb.clicked.connect(self.glavni_boja_bad_flag)
        #checkbox za ekstremne vrijednosti na glavnom grafu
        self.glavni.crtajEkstrem.clicked.connect(self.glavni_checkbox_ekstremi)
        #promjena izgleda markera ekstremnih vrijednosti glavnog grafa
        self.glavni.markerEkstrem.currentIndexChanged.connect(self.glavni_ekstremi_marker)
        #promjena velicine markera ekstremnih vrijednosti glavnog grafa
        self.glavni.markerEkstremSpin.valueChanged.connect(self.glavni_ekstremi_velicina_markera)
        #promjena boje markera ekstremnih vrijednosti glavnoga grafa
        self.glavni.bojaEkstrem.clicked.connect(self.glavni_ekstemi_boja)
        #checkbox za fill na glavnom grafu
        self.glavni.crtajFill.clicked.connect(self.glavni_checkbox_fillsatni)
        #promjena prve komonente za fill graf na glavnom grafu
        self.glavni.fillKomponenta1.currentIndexChanged.connect(self.glanvni_fillsatni_komponenta1)
        #promjena druge komonente za fill graf na glavnom grafu
        self.glavni.fillKomponenta1.currentIndexChanged.connect(self.glanvni_fillsatni_komponenta2)
        #promjena boja fill na glavnom grafu
        self.glavni.bojaFill.clicked.connect(self.glavni_fillsatni_boja)
        
        ###pomocni grafovi###
        """
        self.pomocni odradjuje dodavanje i brisanje grafova. Povratna informacija
        o novom stanju dohvaca po potrebi preko metode : 
        
        self.pomocni.vrati_pomocne_grafove()
        
        Potrebno tek kod "izvoza" promjenjenih podataka
        """
        
        ###zero###
        #odredjivanje stila centralne linije zero grafa
        self.zero.stilMidline.currentIndexChanged.connect(self.zero_midline_stil)
        #odredjivanje sirine centralne linije zero grafa
        self.zero.sirinaMidline.valueChanged.connect(self.zero_midline_sirina)
        #odredjivanje boje centralne linije zero grafa
        self.zero.bojaMidline.clicked.connect(self.zero_midline_boja)
        #odredjivanje pick radijusa od tocke u kojoj je valjan izbor iste
        self.zero.pickMidline.valueChanged.connect(self.zero_midline_pick)
        #odredjivanje izgleda markera za dobre vrijednosti zero (unutar granica)
        self.zero.okMarker.currentIndexChanged.connect(self.zero_ok_marker_change)
        #odredjivanje velcina markera za dobre vrijednosti zero
        self.zero.okSize.valueChanged.connect(self.zero_ok_size_change)
        #odredjivanje boje markera za dobre vrijednosti zero
        self.zero.okBoja.clicked.connect(self.zero_ok_boja_change)
        #odredjivanje izgleda markera za lose vrijednosti zero (izvan granica)
        self.zero.badMarker.currentIndexChanged.connect(self.zero_bad_marker_change)
        #odredjivanje velcina markera za lose vrijednosti zero
        self.zero.badSize.valueChanged.connect(self.zero_bad_size_change)
        #odredjivanje boje markera za lose vrijednosti zero
        self.zero.badBoja.clicked.connect(self.zero_bad_boja_change)
        #odredjivanje stanja checkboxa za crtanje granica tolerancije
        self.zero.granicaCheck.clicked.connect(self.zero_granica_check)
        #odredjivanje stila linije granica tolerancije
        self.zero.granicaLine.currentIndexChanged.connect(self.zero_granica_line)
        #odredjivanje sirine linije granica tolerancije
        self.zero.granicaSirina.valueChanged.connect(self.zero_granica_sirina)
        #odredjivanje boje granica tolerancije
        self.zero.granicaBoja.clicked.connect(self.zero_granica_boja)
        #odredjivanje stanja crtanja sjencanja (fill) izmedju granica tolerancije
        self.zero.fillCheck.clicked.connect(self.zero_fill_check)
        #odredjivanje boje filla izmedju granica tolerancije
        self.zero.fillBoja.clicked.connect(self.zero_fill_boja)

        ###span###
        #odredjivanje stila centralne linije zero grafa
        self.span.stilMidline.currentIndexChanged.connect(self.span_midline_stil)
        #odredjivanje sirine centralne linije zero grafa
        self.span.sirinaMidline.valueChanged.connect(self.span_midline_sirina)
        #odredjivanje boje centralne linije zero grafa
        self.span.bojaMidline.clicked.connect(self.span_midline_boja)
        #odredjivanje pick radijusa od tocke u kojoj je valjan izbor iste
        self.span.pickMidline.valueChanged.connect(self.span_midline_pick)
        #odredjivanje izgleda markera za dobre vrijednosti zero (unutar granica)
        self.span.okMarker.currentIndexChanged.connect(self.span_ok_marker_change)
        #odredjivanje velcina markera za dobre vrijednosti zero
        self.span.okSize.valueChanged.connect(self.span_ok_size_change)
        #odredjivanje boje markera za dobre vrijednosti zero
        self.span.okBoja.clicked.connect(self.span_ok_boja_change)
        #odredjivanje izgleda markera za lose vrijednosti zero (izvan granica)
        self.span.badMarker.currentIndexChanged.connect(self.span_bad_marker_change)
        #odredjivanje velcina markera za lose vrijednosti zero
        self.span.badSize.valueChanged.connect(self.span_bad_size_change)
        #odredjivanje boje markera za lose vrijednosti zero
        self.span.badBoja.clicked.connect(self.span_bad_boja_change)
        #odredjivanje stanja checkboxa za crtanje granica tolerancije
        self.span.granicaCheck.clicked.connect(self.span_granica_check)
        #odredjivanje stila linije granica tolerancije
        self.span.granicaLine.currentIndexChanged.connect(self.span_granica_line)
        #odredjivanje sirine linije granica tolerancije
        self.span.granicaSirina.valueChanged.connect(self.span_granica_sirina)
        #odredjivanje boje granica tolerancije
        self.span.granicaBoja.clicked.connect(self.span_granica_boja)
        #odredjivanje stanja crtanja sjencanja (fill) izmedju granica tolerancije
        self.span.fillCheck.clicked.connect(self.span_fill_check)
        #odredjivanje boje filla izmedju granica tolerancije
        self.span.fillBoja.clicked.connect(self.span_fill_boja)


    """
    definicija callback funkcija
    
    Sve promjene se moraju reflektirati na glavnom dictu defaulti
    """
###############################################################################
    def glavni_marker_nevalidan(self, x):
        """
        promjena izgleda nevalidnog markera
        """
        marker = self.__opis_to_marker[self.glavni.normalMarker.currentText()]
        self.defaulti['glavniKanal']['nevalidanOK']['marker'] = marker
        self.defaulti['glavniKanal']['nevalidanNOK']['marker'] = marker
###############################################################################
    def glavni_marker_validan(self, x):
        """
        promjena izgleda validnog markera
        """
        marker = self.__opis_to_marker[self.glavni.validanMarker.currentText()]
        self.defaulti['glavniKanal']['nevalidanOK']['marker'] = marker
        self.defaulti['glavniKanal']['nevalidanNOK']['marker'] = marker
###############################################################################
    def glavni_velicina_markera_validan(self, x):
        """
        promjena velicine validnog i nevalidnog markera
        """
        msize = int(self.glavni.markerSpin.value())
        #postavi novu vrijednost
        self.defaulti['glavniKanal']['validanOK']['markersize'] = msize
        self.defaulti['glavniKanal']['validanNOK']['markersize'] = msize
        self.defaulti['glavniKanal']['nevalidanOK']['markersize'] = msize
        self.defaulti['glavniKanal']['nevalidanNOK']['markersize'] = msize
###############################################################################
    def glavni_stil_centralne_linije(self, x):
        """
        promjena stila centralne linije
        """
        linija = self.__opis_to_line[self.glavni.stilLinije.currentText()]
        self.defaulti['glavniKanal']['midline']['line'] = linija
###############################################################################
    def glavni_sirina_centralne_linije(self, x):
        """
        promjena sirine centralne linije
        """
        lwidth = round(float(self.glavni.doubleSpinLinije.value()),1)
        self.defaulti['glavniKanal']['midline']['linewidth'] = lwidth        
###############################################################################
    def glavni_boja_ok_flag(self, x):
        """
        promjena boje dobro flagiranih podataka
        """
        #dohvati postojecu boju
        rgb = self.defaulti['glavniKanal']['validanOK']['rgb']
        a = self.defaulti['glavniKanal']['validanOK']['alpha']
        #convert u QColor
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test == True ako je boja ispravno definirana
            color = QtGui.QColor.fromRgba(color) #bitni adapter izlaza dijaloga
            rgb, a = pomocneFunkcije.qcolor_to_default_color(color)
            
            #postavi novu vrijednost
            self.defaulti['glavniKanal']['validanOK']['rgb'] = rgb
            self.defaulti['glavniKanal']['validanOK']['alpha'] = a
            self.defaulti['glavniKanal']['nevalidanOK']['rgb'] = rgb
            self.defaulti['glavniKanal']['nevalidanOK']['alpha'] = a
            #promjeni boju gumba
            boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
            stil = pomocneFunkcije.color_to_style_string('QPushButton#okFlagGumb', boja)
            self.glavni.okFlagGumb.setStyleSheet(stil)
###############################################################################
    def glavni_boja_bad_flag(self, x):
        """
        promjena boje lose flagiranih podataka
        """
        #dohvati postojecu boju
        rgb = self.defaulti['glavniKanal']['validanNOK']['rgb']
        a = self.defaulti['glavniKanal']['validanNOK']['alpha']
        #convert u QColor
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test == True ako je boja ispravno definirana
            color = QtGui.QColor.fromRgba(color) #bitni adapter izlaza dijaloga
            rgb, a = pomocneFunkcije.qcolor_to_default_color(color)
            
            #postavi novu vrijednost
            self.defaulti['glavniKanal']['validanNOK']['rgb'] = rgb
            self.defaulti['glavniKanal']['validanNOK']['alpha'] = a
            self.defaulti['glavniKanal']['nevalidanNOK']['rgb'] = rgb
            self.defaulti['glavniKanal']['nevalidanNOK']['alpha'] = a
            #promjeni boju gumba
            boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
            stil = pomocneFunkcije.color_to_style_string('QPushButton#badFlagGumb', boja)
            self.glavni.badFlagGumb.setStyleSheet(stil)
###############################################################################
    def glavni_checkbox_ekstremi(self, x):
        """
        promjena stanja checkboxa za crtanje ekstremnih vrijednosti (min, max)
        
        x je boolean koji javlja stanje checkboxa, True -> ima kvacicu
        """
        if x:
            self.defaulti['glavniKanal']['fillsatni']['crtaj'] = True
            self.glavni.markerEkstrem.setEnabled(True)
            self.glavni.markerEkstremSpin.setEnabled(True)
            self.glavni.bojaEkstrem.setEnabled(True)
        else:
            self.defaulti['glavniKanal']['fillsatni']['crtaj'] = False
            self.glavni.markerEkstrem.setEnabled(False)
            self.glavni.markerEkstremSpin.setEnabled(False)
            self.glavni.bojaEkstrem.setEnabled(False)
###############################################################################
    def glavni_ekstremi_marker(self, x):
        """
        promjena izgleda markera ekstremnih vrijednosti
        """
        marker = self.__opis_to_marker[self.glavni.markerEkstrem.currentText()]
        self.defaulti['glavniKanal']['ekstremimin']['marker'] = marker
        self.defaulti['glavniKanal']['ekstremimax']['marker'] = marker
###############################################################################
    def glavni_ekstremi_velicina_markera(self, x):
        """
        promjena velicine markera ekstremnih vrijednosti
        """
        velicina = int(self.glavni.markerEkstremSpin.value())
        self.defaulti['glavniKanal']['ekstremimin']['markersize'] = velicina
        self.defaulti['glavniKanal']['ekstremimax']['markersize'] = velicina
###############################################################################
    def glavni_ekstemi_boja(self, x):
        """
        promjena boje markera ekstremnih vrijednosti
        """
        #dohvati postojecu boju
        rgb = self.defaulti['glavniKanal']['ekstremimin']['rgb']
        a = self.defaulti['glavniKanal']['ekstremimin']['alpha']
        #convert u QColor
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test == True ako je boja ispravno definirana
            color = QtGui.QColor.fromRgba(color) #bitni adapter izlaza dijaloga
            rgb, a = pomocneFunkcije.qcolor_to_default_color(color)
            
            #postavi novu vrijednost
            self.defaulti['glavniKanal']['ekstremimin']['rgb'] = rgb
            self.defaulti['glavniKanal']['ekstremimin']['alpha'] = a
            self.defaulti['glavniKanal']['ekstremimax']['rgb'] = rgb
            self.defaulti['glavniKanal']['ekstremimax']['alpha'] = a
            #promjeni boju gumba
            boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
            stil = pomocneFunkcije.color_to_style_string('QPushButton#bojaEkstrem', boja)
            self.glavni.bojaEkstrem.setStyleSheet(stil)
###############################################################################
    def glavni_checkbox_fillsatni(self, x):
        """
        promjena stanja checkboxa za crtanje filla izmedju zadanih tocaka
        
        x je boolean koji javlja stanje checkboxa, True -> ima kvacicu
        """
        if x:
            self.defaulti['glavniKanal']['fillsatni']['crtaj'] = True
            self.glavni.fillKomponenta1.setEnabled(True)
            self.glavni.fillKomponenta2.setEnabled(True)
            self.glavni.bojaFill.setEnabled(True)
        else:
            self.defaulti['glavniKanal']['fillsatni']['crtaj'] = False
            self.glavni.fillKomponenta1.setEnabled(False)
            self.glavni.fillKomponenta2.setEnabled(False)
            self.glavni.bojaFill.setEnabled(False)
###############################################################################
    def glanvni_fillsatni_komponenta1(self, x):
        """
        promjena prve komponente koja odredjuje granicu filla
        """
        komponenta = self.__opis_to_komponenta[self.glavni.fillKomponenta1.currentText()]
        self.defaulti['glavniKanal']['fillsatni']['data1'] = komponenta

###############################################################################
    def glanvni_fillsatni_komponenta2(self, x):
        """
        promjena druge komponente koja odredjuje granicu filla
        """
        komponenta = self.__opis_to_komponenta[self.glavni.fillKomponenta2.currentText()]
        self.defaulti['glavniKanal']['fillsatni']['data2'] = komponenta
###############################################################################
    def glavni_fillsatni_boja(self, x):
        """
        promjena boje fill-a izmedju komponenti
        """
        #dohvati postojecu boju
        rgb = self.defaulti['glavniKanal']['fillsatni']['rgb']
        a = self.defaulti['glavniKanal']['fillsatni']['alpha']
        #convert u QColor
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test == True ako je boja ispravno definirana
            color = QtGui.QColor.fromRgba(color) #bitni adapter izlaza dijaloga
            rgb, a = pomocneFunkcije.qcolor_to_default_color(color)
            
            #postavi novu vrijednost
            self.defaulti['glavniKanal']['fillsatni']['rgb'] = rgb
            self.defaulti['glavniKanal']['fillsatni']['alpha'] = a
            #promjeni boju gumba
            boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
            stil = pomocneFunkcije.color_to_style_string('QPushButton#bojaFill', boja)
            self.glavni.bojaFill.setStyleSheet(stil)
###############################################################################
    def zero_midline_stil(self, x):
        """
        promjena stila centralne linije za zero graf.
        """
        linija = self.__opis_to_line[self.zero.stilMidline.currentText()]
        self.defaulti['zero']['midline']['line'] = linija
###############################################################################
    def zero_midline_sirina(self, x):
        """
        promjena sirine centralne linije za zero graf
        """
        sirina = round(float(self.zero.sirinaMidline.value()), 1)
        self.defaulti['zero']['midline']['linewidth'] = sirina
###############################################################################
    def zero_midline_boja(self, x):
        """
        promjena boje centralne linije na zero grafu
        """
        #dohvati postojecu boju
        rgb = self.defaulti['zero']['midline']['rgb']
        a = self.defaulti['zero']['midline']['alpha']
        #convert u QColor
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test == True ako je boja ispravno definirana
            color = QtGui.QColor.fromRgba(color) #bitni adapter izlaza dijaloga
            rgb, a = pomocneFunkcije.qcolor_to_default_color(color)
            
            #postavi novu vrijednost
            self.defaulti['zero']['midline']['rgb'] = rgb
            self.defaulti['zero']['midline']['alpha'] = a
            #promjeni boju gumba
            boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
            stil = pomocneFunkcije.color_to_style_string('QPushButton#bojaMidline', boja)
            self.zero.bojaMidline.setStyleSheet(stil)        
###############################################################################
    def zero_midline_pick(self, x):
        """
        promjena pick radijusa (osjetljivost pickera) na zero grafu
        """
        r = round(float(self.zero.pickMidline.value()),1)
        self.defaulti['zero']['midline']['picker'] = r
###############################################################################
    def zero_ok_marker_change(self, x):
        """
        promjena "dobrih" markera na zero grafu
        """
        marker = self.__opis_to_marker[self.zero.okMarker.currentText()]
        self.defaulti['zero']['ok']['marker'] = marker
###############################################################################
    def zero_ok_size_change(self, x):
        """
        promjena velicine "dobrih" markera na zero grafu
        """
        velicina = int(self.zero.okSize.value())
        self.defaulti['zero']['ok']['markersize'] = velicina
###############################################################################
    def zero_ok_boja_change(self, x):
        """
        promjena boje "dobrih" markera na zero grafu
        """
        #dohvati postojecu boju
        rgb = self.defaulti['zero']['ok']['rgb']
        a = self.defaulti['zero']['ok']['alpha']
        #convert u QColor
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test == True ako je boja ispravno definirana
            color = QtGui.QColor.fromRgba(color) #bitni adapter izlaza dijaloga
            rgb, a = pomocneFunkcije.qcolor_to_default_color(color)
            
            #postavi novu vrijednost
            self.defaulti['zero']['ok']['rgb'] = rgb
            self.defaulti['zero']['ok']['alpha'] = a
            #promjeni boju gumba
            boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
            stil = pomocneFunkcije.color_to_style_string('QPushButton#okBoja', boja)
            self.zero.okBoja.setStyleSheet(stil)        
###############################################################################
    def zero_bad_marker_change(self, x):
        """
        promjena izgleda "losih" markera na zero grafu
        """
        marker = self.__opis_to_marker[self.zero.badMarker.currentText()]
        self.defaulti['zero']['bad']['marker'] = marker
###############################################################################
    def zero_bad_size_change(self, x):
        """
        promjena velicine "losih" markera na zero grafu
        """
        velicina = int(self.zero.badSize.value())
        self.defaulti['zero']['bad']['markersize'] = velicina
###############################################################################
    def zero_bad_boja_change(self, x):
        """
        promjena boje "losih" markera na zero grafu
        """
        #dohvati postojecu boju
        rgb = self.defaulti['zero']['bad']['rgb']
        a = self.defaulti['zero']['bad']['alpha']
        #convert u QColor
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test == True ako je boja ispravno definirana
            color = QtGui.QColor.fromRgba(color) #bitni adapter izlaza dijaloga
            rgb, a = pomocneFunkcije.qcolor_to_default_color(color)
            
            #postavi novu vrijednost
            self.defaulti['zero']['bad']['rgb'] = rgb
            self.defaulti['zero']['bad']['alpha'] = a
            #promjeni boju gumba
            boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
            stil = pomocneFunkcije.color_to_style_string('QPushButton#badBoja', boja)
            self.zero.badBoja.setStyleSheet(stil)        
###############################################################################
    def zero_granica_check(self, x):
        """
        promjena stanja checkboxa za crtanje granicne vrijednosti dobrih
        zero vrijednosti.
        
        x je boolean koji javlja stanje checkboxa, True -> ima kvacicu
        """
        if x:
            self.defaulti['zero']['warning']['crtaj'] = True
            self.zero.granicaLine.setEnabled(True)
            self.zero.granicaSirina.setEnabled(True)
            self.zero.granicaBoja.setEnabled(True)
        else:
            self.defaulti['zero']['warning']['crtaj'] = False
            self.zero.granicaLine.setEnabled(False)
            self.zero.granicaSirina.setEnabled(False)
            self.zero.granicaBoja.setEnabled(False)
###############################################################################
    def zero_granica_line(self, x):
        """
        promjena stila linije granice dobrih zero vrijednosti (warning line)
        """
        linija = self.__opis_to_line[self.zero.granicaLine.currentText()]
        self.defaulti['zero']['warning']['line'] = linija
###############################################################################
    def zero_granica_sirina(self, x):
        """
        promjena sirine linije granice dobrih zero vrijednosti (warning line)
        """
        sirina = round(float(self.zero.granicaSirina.value()), 1)
        self.defaulti['zero']['warning']['linewidth'] = sirina
###############################################################################
    def zero_granica_boja(self, x):
        """
        promjena boje linije granice dobrih zero vrijednosti(warning line)
        """
        #dohvati postojecu boju
        rgb = self.defaulti['zero']['warning']['rgb']
        a = self.defaulti['zero']['warning']['alpha']
        #convert u QColor
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test == True ako je boja ispravno definirana
            color = QtGui.QColor.fromRgba(color) #bitni adapter izlaza dijaloga
            rgb, a = pomocneFunkcije.qcolor_to_default_color(color)
            
            #postavi novu vrijednost
            self.defaulti['zero']['warning']['rgb'] = rgb
            self.defaulti['zero']['warning']['alpha'] = a
            #promjeni boju gumba
            boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
            stil = pomocneFunkcije.color_to_style_string('QPushButton#granicaBoja', boja)
            self.zero.granicaBoja.setStyleSheet(stil)
###############################################################################
    def zero_fill_check(self, x):
        """
        promjena stanja checkboxa za crtanje sjencanog dijela izmedju 
        "warning" granica zero grafa. Osjencano je podrucje gdje je zero
        vrijednost u dozvoljenom rasponu.
        
        x je boolean koji javlja stanje checkboxa, True -> ima kvacicu
        """
        if x:
            self.defaulti['zero']['fill']['crtaj'] = True
            self.zero.fillBoja.setEnabled(True)
        else:
            self.defaulti['zero']['fill']['crtaj'] = False
            self.zero.fillBoja.setEnabled(False)
###############################################################################
    def zero_fill_boja(self, x):
        """
        promjena boje sjencanog dijela izmedju "warning" granica zero grafa.
        Unutar osjencanog podrucja, zero vrijednost je u dozvoljenom rasponu
        """
        #dohvati postojecu boju
        rgb = self.defaulti['zero']['fill']['rgb']
        a = self.defaulti['zero']['fill']['alpha']
        #convert u QColor
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test == True ako je boja ispravno definirana
            color = QtGui.QColor.fromRgba(color) #bitni adapter izlaza dijaloga
            rgb, a = pomocneFunkcije.qcolor_to_default_color(color)
            
            #postavi novu vrijednost
            self.defaulti['zero']['fill']['rgb'] = rgb
            self.defaulti['zero']['fill']['alpha'] = a
            #promjeni boju gumba
            boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
            stil = pomocneFunkcije.color_to_style_string('QPushButton#fillBoja', boja)
            self.zero.fillBoja.setStyleSheet(stil)        
###############################################################################
    def span_midline_stil(self, x):
        """
        promjena stila centralne linije na span grafu
        """
        linija = self.__opis_to_line[self.span.stilMidline.currentText()]
        self.defaulti['span']['midline']['line'] = linija
###############################################################################
    def span_midline_sirina(self, x):
        """
        promjena sirina centralne linije na span grafu
        """
        sirina = round(float(self.span.sirinaMidline.value()), 1)
        self.defaulti['span']['midline']['linewidth'] = sirina
###############################################################################
    def span_midline_boja(self, x):
        """
        promjena boje centralne linije na span grafu
        """
        #dohvati postojecu boju
        rgb = self.defaulti['span']['midline']['rgb']
        a = self.defaulti['span']['midline']['alpha']
        #convert u QColor
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test == True ako je boja ispravno definirana
            color = QtGui.QColor.fromRgba(color) #bitni adapter izlaza dijaloga
            rgb, a = pomocneFunkcije.qcolor_to_default_color(color)
            
            #postavi novu vrijednost
            self.defaulti['span']['midline']['rgb'] = rgb
            self.defaulti['span']['midline']['alpha'] = a
            #promjeni boju gumba
            boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
            stil = pomocneFunkcije.color_to_style_string('QPushButton#bojaMidline', boja)
            self.span.bojaMidline.setStyleSheet(stil)
###############################################################################
    def span_midline_pick(self, x):
        """
        promjena pick radijusa (osjetljivost pickera) na zero grafu
        """
        r = round(float(self.span.pickMidline.value()), 1)
        self.defaulti['span']['midline']['picker'] = r
###############################################################################
    def span_ok_marker_change(self, x):
        """
        promjena "dobrih" markera na zero grafu
        """
        marker = self.__opis_to_marker[self.span.okMarker.currentText()]
        self.defaulti['span']['ok']['marker'] = marker
###############################################################################
    def span_ok_size_change(self, x):
        """
        promjena velicina "dobrih" markera na zero grafu
        """
        velicina = int(self.span.okSize.value())
        self.defaulti['span']['ok']['markersize'] = velicina
###############################################################################
    def span_ok_boja_change(self, x):
        """
        promjena boje "dobrih" markera na zero grafu
        """
        #dohvati postojecu boju
        rgb = self.defaulti['span']['ok']['rgb']
        a = self.defaulti['span']['ok']['alpha']
        #convert u QColor
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test == True ako je boja ispravno definirana
            color = QtGui.QColor.fromRgba(color) #bitni adapter izlaza dijaloga
            rgb, a = pomocneFunkcije.qcolor_to_default_color(color)
            
            #postavi novu vrijednost
            self.defaulti['span']['ok']['rgb'] = rgb
            self.defaulti['span']['ok']['alpha'] = a
            #promjeni boju gumba
            boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
            stil = pomocneFunkcije.color_to_style_string('QPushButton#okBoja', boja)
            self.span.okBoja.setStyleSheet(stil)
###############################################################################
    def span_bad_marker_change(self, x):
        """
        promjena "losih" markera na zero grafu
        """
        marker = self.__opis_to_marker[self.span.badMarker.currentText()]
        self.defaulti['span']['bad']['marker'] = marker
###############################################################################
    def span_bad_size_change(self, x):
        """
        promjena velicina "losih" markera na zero grafu
        """
        velicina = int(self.span.badSize.value())
        self.defaulti['span']['bad']['markersize'] = velicina
###############################################################################
    def span_bad_boja_change(self, x):
        """
        promjena boje "losih" markera na zero grafu
        """
        #dohvati postojecu boju
        rgb = self.defaulti['span']['bad']['rgb']
        a = self.defaulti['span']['bad']['alpha']
        #convert u QColor
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test == True ako je boja ispravno definirana
            color = QtGui.QColor.fromRgba(color) #bitni adapter izlaza dijaloga
            rgb, a = pomocneFunkcije.qcolor_to_default_color(color)
            
            #postavi novu vrijednost
            self.defaulti['span']['bad']['rgb'] = rgb
            self.defaulti['span']['bad']['alpha'] = a
            #promjeni boju gumba
            boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
            stil = pomocneFunkcije.color_to_style_string('QPushButton#badBoja', boja)
            self.span.badBoja.setStyleSheet(stil)
###############################################################################
    def span_granica_check(self, x):
        """
        promjena stanja checkboxa za crtanje granicne vrijednosti dobrih
        span vrijednosti.
        
        x je boolean koji javlja stanje checkboxa, True -> ima kvacicu
        """
        if x:
            self.defaulti['span']['warning']['crtaj'] = True
            self.span.granicaLine.setEnabled(True)
            self.span.granicaSirina.setEnabled(True)
            self.span.granicaBoja.setEnabled(True)
        else:
            self.defaulti['span']['warning']['crtaj'] = False
            self.span.granicaLine.setEnabled(False)
            self.span.granicaSirina.setEnabled(False)
            self.span.granicaBoja.setEnabled(False)
###############################################################################
    def span_granica_line(self, x):
        """
        promjena stila linije granice dobrih zero vrijednosti (warning line)
        """
        linija = self.__opis_to_line[self.span.granicaLine.currentText()]
        self.defaulti['span']['warning']['line'] = linija
###############################################################################
    def span_granica_sirina(self, x):
        """
        promjena sirine linije granice dobrih zero vrijednosti (warning line)
        """
        sirina = round(float(self.span.granicaSirina.value()), 1)
        self.defaulti['span']['warning']['linewidth'] = sirina
###############################################################################
    def span_granica_boja(self, x):
        """
        promjena boje linije granice dobrih zero vrijednosti(warning line)
        """
        #dohvati postojecu boju
        rgb = self.defaulti['span']['warning']['rgb']
        a = self.defaulti['span']['warning']['alpha']
        #convert u QColor
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test == True ako je boja ispravno definirana
            color = QtGui.QColor.fromRgba(color) #bitni adapter izlaza dijaloga
            rgb, a = pomocneFunkcije.qcolor_to_default_color(color)
            
            #postavi novu vrijednost
            self.defaulti['span']['warning']['rgb'] = rgb
            self.defaulti['span']['warning']['alpha'] = a
            #promjeni boju gumba
            boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
            stil = pomocneFunkcije.color_to_style_string('QPushButton#granicaBoja', boja)
            self.span.granicaBoja.setStyleSheet(stil)
###############################################################################
    def span_fill_check(self, x):
        """
        promjena stanja checkboxa za crtanje sjencanog dijela izmedju 
        "warning" granica span grafa. Osjencano je podrucje gdje je span
        vrijednost u dozvoljenom rasponu.
        
        x je boolean koji javlja stanje checkboxa, True -> ima kvacicu
        """
        if x:
            self.defaulti['span']['fill']['crtaj'] = True
            self.span.fillBoja.setEnabled(True)
        else:
            self.defaulti['span']['fill']['crtaj'] = False
            self.span.fillBoja.setEnabled(False)
###############################################################################
    def span_fill_boja(self, x):
        """
        promjena boje linije granice dobrih zero vrijednosti(warning line)
        """
        #dohvati postojecu boju
        rgb = self.defaulti['span']['fill']['rgb']
        a = self.defaulti['span']['fill']['alpha']
        #convert u QColor
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test == True ako je boja ispravno definirana
            color = QtGui.QColor.fromRgba(color) #bitni adapter izlaza dijaloga
            rgb, a = pomocneFunkcije.qcolor_to_default_color(color)            
            #postavi novu vrijednost
            self.defaulti['span']['fill']['rgb'] = rgb
            self.defaulti['span']['fill']['alpha'] = a
            #promjeni boju gumba
            boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
            stil = pomocneFunkcije.color_to_style_string('QPushButton#fillBoja', boja)
            self.span.fillBoja.setStyleSheet(stil)
###############################################################################
###############################################################################