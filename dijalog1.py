# -*- coding: utf-8 -*-
"""
Created on Tue Nov  4 15:49:31 2014

@author: User
"""
from PyQt4 import QtGui, QtCore, uic

import pomocneFunkcije #cesto koristene funkcije, adapteri...
import tableModel #specificna implementacija modela za dinamicko dodavanje pomocnih grafova

base1, form1 = uic.loadUiType('kontrola_crtanja_grafova.ui')
class IzborStoSeCrta(base1, form1):
    """
    Klasa je djalog preko kojeg se odredjuje sto se prikazuje na grafovima
    -prikaz pomocnih grafova
    -izbori boje i markera za glavni kanal
    -izbor fill opcije i crtanja ekstremnih vrijednosti glavnog kanala
    
    KOD INSTANCIRANJA DIJALOGA BITNO JE PROSLIJEDITI 3 KEYWORDA:
    kanali:
        -lista stringova dostupnih kanala (preferecijalno sortirana)
        -potrebna je za inicijalizaciju drugih dijaloga (prilikom dinamickog
        dodavanja drugih kanala)
    
    glavniKanal:
        -string
        -sadrzi informaciju koji je glavni kanal
        
    info:
        -dict koji sadrzi informacije o grafovima i postavkama vezanim za grafove
        -vanjski kljucevi : 'glavniKanal', 'pomocniKanali', 'ostalo'
        
        'glavniKanal' sadrzi dict, kljucevi su:
            -'midline' -> dict, postavke za crtanje centralne linije (average ili koncentracija)
            -'validanOK' -> dict, postavke za crtanje scatter plota validiranih podataka koji imaju dobar flag
            -'validanNOK' -> dict, postavke za crtanje scatter plota validiranih podataka koji nemaju dobar flag
            -'nevalidanOK' -> dict, postavke za crtanje scatter plota nevalidiranih podataka koji imaju dobar flag
            -'nevalidanNOK' -> dict, postavke za crtanje scatter plota nevalidiranih podataka koji nemaju dobar flag
            -'fillsatni' -> dict, postavke za sjencanje izmedju dva seta podataka na satnom grafu
            -'ekstremimin' -> dict, postavke za crtanje ekstremnih vrijednosti (minimuma) na satnom grafu
            -'ekstremimax' -> dict, postavke za crtanje ekstremnih vrijednosti (maksimuma) na satnom grafu
        
        'pomocniKanali' sadrzi dict, kljucevi su:
            -label grafa -> dict, postavke za crtanje (vrijednost pod kljucem 'label' je kljuc pod kojim
            se graf sprema u dict)
            
        'ostalo sadrzi dict, kljucevi su:
            -'opcijeminutni' -> dict, generalne postavke (span, cursor, grid, ticks...)
            -'opcijesatni' -> dict, generalne postavke (span, cursor, grid, ticks...)
            
    """
    def __init__(self, parent = None, kanali = [], glavniKanal = None, info = None):
        super(base1, self).__init__(parent)
        self.setupUi(self)
        
        self.__glavniKanal = glavniKanal #glavni kanal (string)
        self.__info = info #nested dict sa informacijom o postavkama grafova
        #TODO! srediti inicijalizaciju 
        #garant neki fale...
        self.__sviKanali = ['1-SO2-ppb', '10-NO-ppb', '11-NOx-ppb', '12-NO2-ppb', 
                            '13-NO-ug/m3', '14-NOx-ug/m3', '15-NO2-ug/m3', 
                            '3-SO2-ug/m3', '30-CO-ppm', '31-CO-mg/m3', 
                            '40-O3-ppb', '49-O3-ug/m3', '50-PM1-ug/m3', 
                            '51-PM2.5-ug/m3', '52-PM10-ug/m3', '53-AT-°C', 
                            '54-RH-%', '80-Enc.Temp-°C']
        #helper mape, za pretvaranje mpl vrijednosti u teskt i nazad
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
                                 
        self.__line_to_opis = {'None':'Bez linije', 
                               '-':'Puna linija',
                               '--':'Dash - Dash', 
                               '-.':'Dash - Dot', 
                               ':':'Dot'}

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
        
        self.__opis_to_line = {'Bez linije':'None', 
                               'Puna linija':'-',
                               'Dash - Dash':'--', 
                               'Dash - Dot':'-.', 
                               'Dot':':'}
        
        self.initial_setup()
        self.veze()
        
    def initial_setup(self):
        """
        Ova funkcija sluzi da se preko nje instancira dijalog.
        """

        """1. inicijalizacija modela, povezivanje sa QTableView"""
        #moramo iz dicta self.__info izvuci i konstruirati nested listu
        #informacija o pomocnim grafovima za inicijalizaciju modela
        nLista = []
        pomocni = self.__info['pomocniKanali']
        if len(pomocni) == 0:
            nLista = []
        else:
             for key in pomocni:
                """
                !!!redosljed je jako bitan da model zna gdje su elementi!!!
                slaganje liste, u zagradi je broj indeksa:
                
                kanal(0), marker(1), markersize(2), line(3), linewidth(4), 
                rgb(5), alpha(6), zorder(7), label(8)            
                """
                temp =[pomocni[key]['kanal'], 
                       self.__marker_to_opis[pomocni[key]['marker']], 
                       pomocni[key]['markersize'], 
                       self.__line_to_opis[pomocni[key]['line']], 
                       pomocni[key]['linewidth'], 
                       pomocni[key]['rgb'], 
                       pomocni[key]['alpha'], 
                       pomocni[key]['zorder'], 
                       pomocni[key]['label']]
                nLista.append(temp)
        #popis stilova markera i stilova linija
        markeri = sorted(list(self.__opis_to_marker.keys()))
        linije = sorted(list(self.__opis_to_line.keys()))
        #instanciranje modela i povezivanje sa QTableView-om
        #inicjalizacija modela
        self.model = tableModel.PomocniGrafovi(grafInfo = nLista, kanali = self.__sviKanali, markeri = markeri, linije = linije)
        #inicjalizacija tablice
        self.tableView = Tablica()
        #postavljanje tablice u layout dijaloga
        self.tableViewLayout.addWidget(self.tableView)
        #settanje modela u view
        self.tableView.setModel(self.model)

        #TODO! vidi popunjavanje comboboxeva sto i kako se pise
        """2. popunjavanje comboboxeva"""
        
        #nadji definirane vrijednosti markera
        validan = self.__marker_to_opis[self.__info['glavniKanal']['validanOK']['marker']]
        nevalidan = self.__marker_to_opis[self.__info['glavniKanal']['nevalidanOK']['marker']]
        ekstrem = self.__marker_to_opis[self.__info['glavniKanal']['ekstremimin']['marker']]
        msize = self.__info['glavniKanal']['validanOK']['markersize']
        
        self.spinBoxMarker.setValue(msize)
        
        markeri = sorted(list(self.__opis_to_marker.keys()))
        self.comboValidan.addItems(markeri)
        self.comboValidan.setCurrentIndex(self.comboValidan.findText(validan))
        self.comboNeValidan.addItems(markeri)
        self.comboNeValidan.setCurrentIndex(self.comboNeValidan.findText(nevalidan))
        self.comboEkstrem.addItems(markeri)
        self.comboEkstrem.setCurrentIndex(self.comboEkstrem.findText(ekstrem))
        
        agregiraniPodaci = sorted(['min', 'max', 'avg', 'q05', 'q95' ,'median'])
        self.comboData1.addItems(agregiraniPodaci)
        self.comboData1.setCurrentIndex(self.comboData1.findText('q05'))
        self.comboData2.addItems(agregiraniPodaci)
        self.comboData2.setCurrentIndex(self.comboData1.findText('q95'))
        
        """3. postavke boje, promjena boje QPushButtona"""
        #boja za ako je podatak flagan kao dobar (OK)
        rgb = self.__info['glavniKanal']['validanOK']['rgb']
        a = self.__info['glavniKanal']['validanOK']['alpha']
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        stil = pomocneFunkcije.color_to_style_string('QPushButton#gumbBojaOK', boja)
        self.gumbBojaOK.setStyleSheet(stil)
        #boja ako je podatak flagan kao los (Not OK)
        rgb = self.__info['glavniKanal']['validanNOK']['rgb']
        a = self.__info['glavniKanal']['validanNOK']['alpha']
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        stil = pomocneFunkcije.color_to_style_string('QPushButton#gumbBojaNOK', boja)
        self.gumbBojaNOK.setStyleSheet(stil)
        #boja ekstremnih vrijednosti (minimum i maksimum na satnom grafu)
        rgb = self.__info['glavniKanal']['ekstremimin']['rgb']
        a = self.__info['glavniKanal']['ekstremimin']['alpha']
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        stil = pomocneFunkcije.color_to_style_string('QPushButton#gumbBojaEkstrem', boja)
        self.gumbBojaEkstrem.setStyleSheet(stil)
        #boja sjencanog podrucja na satnom grafu (fill_between)
        rgb = self.__info['glavniKanal']['fillsatni']['rgb']
        a = self.__info['glavniKanal']['fillsatni']['alpha']
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        stil = pomocneFunkcije.color_to_style_string('QPushButton#gumbBojaFill', boja)
        self.gumbBojaFill.setStyleSheet(stil)
        
        """4. postavljanje checkboxeva te, disbleanje i enableanje opcija"""
        check1 = self.__info['glavniKanal']['ekstremimin']['crtaj']
        self.checkEkstrem.setChecked(check1)
        self.promjeni_status_ekstrem(check1)
        check2 = self.__info['glavniKanal']['fillsatni']['crtaj']
        self.checkFill.setChecked(check2)
        self.promjeni_status_fill(check2)
               
    def promjeni_status_fill(self, x):
        """
        pomocna funkcija za toggle sjencanja na satnom grafu.
        x je boolean koji javlja stanje checkboxa, True -> ima kvacicu
        
        Ovisno o stanju, treba promjeniti status kontrolnih widgeta (disable/enable)
        te promjeniti vrijednosti u dictu da ostali dijelovi aplikacije znaju sto
        je izabrano
        """
        if x:
            self.__info['glavniKanal']['fillsatni']['crtaj'] = True
            self.comboData1.setEnabled(True)
            self.comboData2.setEnabled(True)
            self.gumbBojaFill.setEnabled(True)
        else:
            self.__info['glavniKanal']['fillsatni']['crtaj'] = False
            self.comboData1.setEnabled(False)
            self.comboData2.setEnabled(False)
            self.gumbBojaFill.setEnabled(False)
            
    def promjeni_status_ekstrem(self, x):
        """
        pomocna funkcija za toggle prikaza ekstremnih vrijednosti na satnom grafu.
        x je boolean koji javlja stanje checkboxa, True -> ima kvacicu
        
        Ovisno o stanju, treba promjeniti status kontrolnih widgeta (disable/enable)
        te promjeniti vrijednosti u dictu da ostali dijelovi aplikacije znaju sto
        je izabrano
        """
        if x:
            self.__info['glavniKanal']['ekstremimin']['crtaj'] = True
            self.__info['glavniKanal']['ekstremimax']['crtaj'] = True
            self.comboEkstrem.setEnabled(True)
            self.gumbBojaEkstrem.setEnabled(True)
        else:
            self.__info['glavniKanal']['ekstremimin']['crtaj'] = False
            self.__info['glavniKanal']['ekstremimax']['crtaj'] = False
            self.comboEkstrem.setEnabled(False)
            self.gumbBojaEkstrem.setEnabled(False)
            
    def promjeni_marker_validan(self):
        """
        Funkcija odradjuje promjenu vrijednosti comboboxa za markere 
        validiranih vrijednosti
        """
        #dohvati trenutnu vrijednost comboboxa
        marker = self.__opis_to_marker[self.comboValidan.currentText()]
        #postavi vrijednost u self.__info na odgovarajuce mjesto
        self.__info['glavniKanal']['validanOK']['marker'] = marker
        self.__info['glavniKanal']['validanNOK']['marker'] = marker
    
    def promjeni_marker_nevalidan(self):
        """
        Funkcija odradjuje promjenu vrijednosti comboboxa za markere
        ne-validiranih vrijednosti
        """
        marker = self.__opis_to_marker[self.comboNeValidan.currentText()]
        #postavi vrijednost u self.__info na odgovarajuce mjesto
        self.__info['glavniKanal']['nevalidanOK']['marker'] = marker
        self.__info['glavniKanal']['nevalidanNOK']['marker'] = marker

    def promjeni_marker_ekstrem(self):
        """
        Funkcija odradjuje promjenu vrijednosti comboboxa za markere ekstremnih
        vrijednosti
        """
        marker = self.__opis_to_marker[self.comboEkstrem.currentText()]
        #postavi vrijednost u self.__info na odgovarajuce mjesto
        self.__info['glavniKanal']['ekstremimin']['marker'] = marker
        self.__info['glavniKanal']['ekstremimax']['marker'] = marker

    def promjeni_fill_komponenta1(self):
        """
        Funkcija odradjuje promjenu vrijednosti comboboxa za prvu komponentu
        argumenata za sjencanje na satnom grafu (sjencanje je izmedju 2 komponente)
        """
        data = self.comboData1.currentText()
        #postavi vrijednost u self.__info na odgovarajuce mjesto
        self.__info['glavniKanal']['fillsatni']['data1'] = data
    
    def promjeni_fill_komponenta2(self):
        """
        Funkcija odradjuje promjenu vrijednosti comboboxa za drugu komponentu
        argumenata za sjencanje na satnom grafu (sjencanje je izmedju 2 komponente)
        """
        data = self.comboData2.currentText()
        #postavi vrijednost u self.__info na odgovarajuce mjesto
        self.__info['glavniKanal']['fillsatni']['data2'] = data

    def promjeni_boju_fill(self):
        """
        Funkcija odradjuje promjenu boje osjencanog podrucja na satnom grafu.
        Dodatno, zaduzena je za update boje gumba s kojim se poziva.
        """
        #dohvati postojecu boju
        rgb = self.__info['glavniKanal']['fillsatni']['rgb']
        a = self.__info['glavniKanal']['fillsatni']['alpha']
        #convert u QColor
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test == True ako je boja ispravno definirana
            color = QtGui.QColor.fromRgba(color) #bitni adapter izlaza dijaloga
            rgb, a = pomocneFunkcije.qcolor_to_default_color(color)
            
            #zapamti novu boju, upisi u self.__info
            self.__info['glavniKanal']['fillsatni']['rgb'] = rgb
            self.__info['glavniKanal']['fillsatni']['alpha'] = a
            #promjeni boju gumba
            boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
            stil = pomocneFunkcije.color_to_style_string('QPushButton#gumbBojaFill', boja)
            self.gumbBojaFill.setStyleSheet(stil)
    
    def promjeni_boju_ekstrem(self):
        """
        Funkcija odradjuje promjenu boje ekstremnih vrijednosti na satnom grafu.
        Dodatno, zaduzena je za update boje gumba s kojim se poziva
        """
        #dohvati postojecu boju
        rgb = self.__info['glavniKanal']['ekstremimin']['rgb']
        a = self.__info['glavniKanal']['ekstremimin']['alpha']
        #convert u QColor
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test == True ako je boja ispravno definirana
            color = QtGui.QColor.fromRgba(color) #bitni adapter izlaza dijaloga
            rgb, a = pomocneFunkcije.qcolor_to_default_color(color)
            
            #zapamti novu boju, upisi u self.__info
            self.__info['glavniKanal']['ekstremimin']['rgb'] = rgb
            self.__info['glavniKanal']['ekstremimin']['alpha'] = a
            self.__info['glavniKanal']['ekstremimax']['rgb'] = rgb
            self.__info['glavniKanal']['ekstremimax']['alpha'] = a
            #promjeni boju gumba
            boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
            stil = pomocneFunkcije.color_to_style_string('QPushButton#gumbBojaEkstrem', boja)
            self.gumbBojaEkstrem.setStyleSheet(stil)

    
    def promjeni_boju_ok(self):
        """
        Funkcija odradjuje promjenu boje dobro flaganih podataka na satnom grafu.
        Dodatno, zaduzena je za update boje gumba s kojim se poziva
        """
        #dohvati postojecu boju
        rgb = self.__info['glavniKanal']['validanOK']['rgb']
        a = self.__info['glavniKanal']['validanOK']['alpha']
        #convert u QColor
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test == True ako je boja ispravno definirana
            color = QtGui.QColor.fromRgba(color) #bitni adapter izlaza dijaloga
            rgb, a = pomocneFunkcije.qcolor_to_default_color(color)
            
            #zapamti novu boju, upisi u self.__info
            self.__info['glavniKanal']['validanOK']['rgb'] = rgb
            self.__info['glavniKanal']['validanOK']['alpha'] = a
            self.__info['glavniKanal']['nevalidanOK']['rgb'] = rgb
            self.__info['glavniKanal']['nevalidanOK']['alpha'] = a
            #promjeni boju gumba
            boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
            stil = pomocneFunkcije.color_to_style_string('QPushButton#gumbBojaOK', boja)
            self.gumbBojaOK.setStyleSheet(stil)
    
    def promjeni_boju_nok(self):
        """
        Funkcija odradjuje promjenu boje lose flaganih podataka na satnom grafu.
        Dodatno, zaduzena je za update boje gumba s kojim se poziva
        """
        rgb = self.__info['glavniKanal']['validanNOK']['rgb']
        a = self.__info['glavniKanal']['validanNOK']['alpha']
        #convert u QColor
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test == True ako je boja ispravno definirana
            color = QtGui.QColor.fromRgba(color) #bitni adapter izlaza dijaloga
            rgb, a = pomocneFunkcije.qcolor_to_default_color(color)
            
            #zapamti novu boju, upisi u self.__info
            self.__info['glavniKanal']['validanNOK']['rgb'] = rgb
            self.__info['glavniKanal']['validanNOK']['alpha'] = a
            self.__info['glavniKanal']['nevalidanNOK']['rgb'] = rgb
            self.__info['glavniKanal']['nevalidanNOK']['alpha'] = a
            #promjeni boju gumba
            boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
            stil = pomocneFunkcije.color_to_style_string('QPushButton#gumbBojaNOK', boja)
            self.gumbBojaNOK.setStyleSheet(stil)
            
    def promjeni_velicinu_markera(self):
        """
        funkcija mjenja promjenu velicine svih markera za glavni graf.
        """
        #dohvati trenutnu vrijednost spinboxa
        msize = self.spinBoxMarker.value()
        #postavi vrijednost u self.__info na odgovarajuce mjesto
        self.__info['glavniKanal']['validanOK']['markersize'] = msize
        self.__info['glavniKanal']['validanNOK']['markersize'] = msize
        self.__info['glavniKanal']['nevalidanOK']['markersize'] = msize
        self.__info['glavniKanal']['nevalidanNOK']['markersize'] = msize
        self.__info['glavniKanal']['ekstremimin']['markersize'] = msize
        self.__info['glavniKanal']['ekstremimax']['markersize'] = msize

    def dohvati_postavke(self):
        """
        Ova funkcija sluzi da se preko nje dohvate postavke grafova za crtanje, 
        tj. izlazna vrijednost dijaloga.
        """
        #dohvati nested listu u modelu
        nLista = self.model.vrati_nested_listu()
        #priprema dicta u koji cemo spremiti podatke iz modela
        pomocni = {}
        #upisivanje u pomocni dict
        for i in range(len(nLista)):
            pomocni[nLista[i][0]] = {
                'kanal':nLista[i][0], 
                'marker':self.__opis_to_marker[nLista[i][1]], 
                'markersize':nLista[i][2], 
                'line':self.__opis_to_line[nLista[i][3]], 
                'linewidth':nLista[i][4], 
                'rgb':nLista[i][5], 
                'alpha':nLista[i][6], 
                'zorder':nLista[i][7], 
                'label':nLista[i][8]
            }
            
        #zamjeni dict u self.__info
        self.__info['pomocniKanali'] = pomocni
        #vrati cijeli dict sa postavkama
        return self.__info
    
    def veze(self):
        """
        funkcija sa connectionima izmedju widgeta. Wrapper da sve "lokalne" veze
        signala i slotova budu na jendnom mjestu
        """
        self.dodajGraf.clicked.connect(self.dodaj_graf) #gumb za dodavanje pomocnog grafa
        self.checkFill.clicked.connect(self.promjeni_status_fill) #checkbox za fill
        self.checkEkstrem.clicked.connect(self.promjeni_status_ekstrem) #checkbox za min/max
        self.gumbBojaOK.clicked.connect(self.promjeni_boju_ok) #gumb za boju ako je flag dobar
        self.gumbBojaNOK.clicked.connect(self.promjeni_boju_nok) #gumb za boju ako je flag los
        self.gumbBojaFill.clicked.connect(self.promjeni_boju_fill) #gumb za boju fill
        self.gumbBojaEkstrem.clicked.connect(self.promjeni_boju_ekstrem) #gumb za boju min/max
        self.comboNeValidan.currentIndexChanged.connect(self.promjeni_marker_nevalidan) #combobox za nevalidne markere
        self.comboValidan.currentIndexChanged.connect(self.promjeni_marker_validan) #combobox za validne markere
        self.comboEkstrem.currentIndexChanged.connect(self.promjeni_marker_ekstrem) #combobox za ekstremne markere
        self.comboData1.currentIndexChanged.connect(self.promjeni_fill_komponenta1) #izbor podataka za fill
        self.comboData2.currentIndexChanged.connect(self.promjeni_fill_komponenta2) #izbor podataka za fill
        self.spinBoxMarker.valueChanged.connect(self.promjeni_velicinu_markera) #izbor velicine markera za satni graf
    
    def dodaj_graf(self, lista):
        """
        Funkcija dodaje graf u model.
        graf je zadan kao lista parametara koji se kao cjelina upisuju u model
        uz pomoc funkcije modela insertRows
        """
        #TODO! samo treba insertati defaultni index u tablicu
        defaultGraf = ['1-SO2-ppb','Bez markera',12,'Puna linija',2,(0,0,255),1.0,4,'1-SO2-ppb']
        self.model.insertRows(0, 1, sto=[defaultGraf])
#        dijalog = dijalog2.IzborPojedinacnogGrafa(kanali = self.__dostupniKanali)
#        if dijalog.exec_():
#            lista = dijalog.vrati_listu_grafa()
#            self.model.insertRows(0,1,sto=[lista])
###############################################################################
###############################################################################
class Tablica(QtGui.QTableView):
    """
    Ova klasa je zaduzena za prikaz modela pomocnih grafova.
    Subklasani QTableView, ciljano zahtjevamo da se odredjeni stupci
    ponasaju drugacije. Delegiramo editiranje modela drugim klasama (
    inace je line edit, cilj je dozvoliti comboBoxeve, spinBoxeve, 
    ponasanje slicno gumbima...)
    
    incijalizacija sa kanalima
    kwd kanali = kanali
    """
    def __init__(self, parent = None):
        QtGui.QTableView.__init__(self, parent)
        
        # postavi delegate
        self.setItemDelegateForColumn(0, KanalComboBoxDelegate(self))
        self.setItemDelegateForColumn(1, MarkerComboBoxDelegate(self))
        self.setItemDelegateForColumn(2, SpinBoxDelegate(self))
        self.setItemDelegateForColumn(3, LinijaComboBoxDelegate(self))
        self.setItemDelegateForColumn(4, SpinBoxDelegate(self))
        self.setItemDelegateForColumn(5, ColorDialogDelegate(self))
        self.setItemDelegateForColumn(6, RemoveButtonDelegate(self))

###############################################################################
###############################################################################
class KanalComboBoxDelegate(QtGui.QItemDelegate):
    """
    Delegira editor za promjenu kanala u tablici u combobox.
    PARENT ARGUMENT JE OBAVEZAN KOD INICIJALIZACIJE. parent je tablica
    tj. subklasani QTableView.
    """
    def __init__(self, parent):
        QtGui.QItemDelegate.__init__(self, parent)
        
    def createEditor(self, parent, option, index):
        """
        ova funkcija stvara editor, tu definiramo combobox
        """
        editor = QtGui.QComboBox(parent) #definiramo combobox (parent je bitan)
        kanali = index.model().kanali #iz tablice dohvacamo kanale
        editor.clear() #clearamo combobox
        editor.addItems(kanali) #postavljamo kanale iz tablice u combobox
        return editor #vrati instancu editora

    def setEditorData(self, editor, index):
        """
        Ova metoda postavlja vrijednosti u editor (prilikom inicjalizacije)
        npr. trenutni izbor u comboboxu.
        """
        editor.blockSignals(True) #blokirajmo signale izbjegnemo akcije dok namjestamo combobox
        """
        treba dohvatiti trenutni kanal da ga postavimo kao trenutni
        izbor. index prati koji je redak i stupac u tablici kliknut ,
        takodjer index zna na koji se model referencira...
        index.model() -> vraca instancu modela
        index.model().data(index) -> vraca vrijednost koja je u modelu
        na tom indeksu.
        """
        kstring = index.model().data(index, QtCore.Qt.EditRole)
        ind = editor.findText(kstring) #nadjimo indeks pod kojim je kanal spremljen u combobox
        editor.setCurrentIndex(int(ind)) #postavimo index comboboxa da prikazuje gore dohvaceni indeks
        editor.blockSignals(False) #odblokiramo signale

    def setModelData(self, editor, model, index):
        """
        metoda je setter podataka iz editora u model
        """
        value = editor.currentText() #dohvati trenutni izbor comboboxa
        model.setData(index, value, QtCore.Qt.EditRole) #poziv metode setData modela
###############################################################################
###############################################################################
class MarkerComboBoxDelegate(QtGui.QItemDelegate):
    """
    Delegira editor za promjenu markera u tablici u combobox.
    vidi klasu KanalComboxDelegate za detalje rada
    """
    def __init__(self, parent):
        QtGui.QItemDelegate.__init__(self, parent)
        
    def createEditor(self, parent, option, index):
        editor = QtGui.QComboBox(parent)
        markeri = index.model().markeri
        editor.clear()
        editor.addItems(markeri)
        return editor

    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        mstring = index.model().data(index, QtCore.Qt.EditRole)
        ind = editor.findText(mstring)
        editor.setCurrentIndex(int(ind))
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, QtCore.Qt.EditRole)
###############################################################################
###############################################################################
class SpinBoxDelegate(QtGui.QItemDelegate):
    """
    Delegira editor za promjenu velicine markera u tablici
    Delegira editor za promjenu sirine linije u tablici
    Editor je QSpinBox
    vidi klasu KanalComboDelegate za detalje rada
    """
    def __init__(self, parent):
        QtGui.QItemDelegate.__init__(self, parent)
        
    def createEditor(self, parent, option, index):
        editor = QtGui.QSpinBox(parent)
        #granice spinboxa
        editor.setMinimum(1)
        editor.setMaximum(100)
        return editor

    def setEditorData(self, spinBox, index):
        value = index.model().data(index, QtCore.Qt.EditRole)
        spinBox.setValue(value)

    def setModelData(self, spinBox, model, index):
        spinBox.interpretText() #vraca uvijek string, adapter na int vrijednost
        value = spinBox.value()
        model.setData(index, value, QtCore.Qt.EditRole)
###############################################################################
###############################################################################
class LinijaComboBoxDelegate(QtGui.QItemDelegate):
    """
    Delegira editor za promjenu stila linije u tablici, combobox
    vidi klasu KanalComboDelegate za detalje rada
    """
    def __init__(self, parent):
        QtGui.QItemDelegate.__init__(self, parent)
        
    def createEditor(self, parent, option, index):
        editor = QtGui.QComboBox(parent)
        linije = index.model().linije
        editor.clear()
        editor.addItems(linije)
        return editor

    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        lstring = index.model().data(index, QtCore.Qt.EditRole)
        ind = editor.findText(lstring)
        editor.setCurrentIndex(int(ind))
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, QtCore.Qt.EditRole)    
###############################################################################
###############################################################################
class ColorDialogDelegate(QtGui.QItemDelegate):
    """
    Mali hack, u biti ne delegira nista, direktno poziva promjenu boje
    preko dijaloga i direktno mjenja model.
    Dupli klik na celiju u stupcu umjesto otvaranja editora otvara color
    dijalog.
    """
    def __init__(self, parent):
        QtGui.QItemDelegate.__init__(self, parent)
        
    def createEditor(self, parent, option, index):
        """
        hack dio...inicijalizacija dijaloga za izbor boje
        """
        self.indeks = index
        rgb = index.model().grafInfo[index.row()][5]
        a = index.model().grafInfo[index.row()][6]
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga (modalni dijalog)
        color, test = QtGui.QColorDialog.getRgba(boja.rgba())
        if test:
            color = QtGui.QColor.fromRgba(color) #bitni adapter izlaza dijaloga
            rgb, a = pomocneFunkcije.qcolor_to_default_color(color)
            
            #direktni setter na model mimo setData
            index.model().grafInfo[index.row()][5] = rgb
            index.model().grafInfo[index.row()][6] = a
###############################################################################
###############################################################################
class RemoveButtonDelegate(QtGui.QItemDelegate):
    """
    Mali hack, u biti ne delegira nista, direktno poziva removeRows metodu
    modela i brise cijeli redak pod tim indeksom.
    Dupli klik ne celiju u stupcu umjesto otvaranja editora u toj celiji
    brise cijeli taj redak
    """
    def __init__(self, parent):
        QtGui.QItemDelegate.__init__(self, parent)
        
    def createEditor(self, parent, option, index):
        """hack dio, umjsto stvaranja editora, 
        direktni remove reda"""
        index.model().removeRows(index.row(), 1)        
###############################################################################
###############################################################################

#test ispravnosti dijaloga
if __name__ == '__main__':
    import sys

    defaulti1 = {
        'glavniKanal':{
            'midline':{'kanal':None, 'line':'-', 'rgb':(0,0,0), 'alpha':1.0, 'zorder':100, 'label':'average'},
            'validanOK':{'kanal':None, 'marker':'d', 'rgb':(0,255,0), 'alpha':1.0, 'zorder':100, 'label':'validiran, dobar', 'markersize':12}, 
            'validanNOK':{'kanal':None, 'marker':'d', 'rgb':(255,0,0), 'alpha':1.0, 'zorder':100, 'label':'validiran, los', 'markersize':12}, 
            'nevalidanOK':{'kanal':None, 'marker':'o', 'rgb':(0,255,0), 'alpha':1.0, 'zorder':100, 'label':'nije validiran, dobar', 'markersize':12}, 
            'nevalidanNOK':{'kanal':None, 'marker':'o', 'rgb':(255,0,0), 'alpha':1.0, 'zorder':100, 'label':'nije validiran, los', 'markersize':12},
            'fillsatni':{'kanal':None, 'crtaj':True, 'data1':'q05', 'data2':'q95', 'rgb':(0,0,255), 'alpha':0.5, 'zorder':1}, 
            'ekstremimin':{'kanal':None, 'crtaj':True, 'marker':'+', 'rgb':(90,50,10), 'alpha':1.0, 'zorder':100, 'label':'min', 'markersize':12}, 
            'ekstremimax':{'kanal':None, 'crtaj':True, 'marker':'+', 'rgb':(90,50,10), 'alpha':1.0, 'zorder':100, 'label':'max', 'markersize':12}
                        },
        'pomocniKanali':{}, 
        'ostalo':{
            'opcijeminutni':{'cursor':False, 'span':True, 'ticks':True, 'grid':False, 'legend':False}, 
            'opcijesatni':{'cursor':False, 'span':False, 'ticks':True, 'grid':False, 'legend':False}
                }}


    app = QtGui.QApplication(sys.argv)
    x = IzborStoSeCrta(kanali = ['1-SO2-ppb','kanal2','kanal3'], glavniKanal = '1-SO2-ppb', info = defaulti1)
    x.show()
    sys.exit(app.exec_())
    