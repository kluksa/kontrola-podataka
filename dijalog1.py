# -*- coding: utf-8 -*-
"""
Created on Tue Nov  4 15:49:31 2014

@author: User
"""
from PyQt4 import QtGui, uic

import pomocneFunkcije #cesto koristene funkcije, adapteri...
import dijalog2 #dijalog za izbor opcija pomocnog grafa
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
        
        self.__dostupniKanali = kanali #popis kanala (lista stringova)
        self.__glavniKanal = glavniKanal #glavni kanal (string)
        self.__info = info #nested dict sa informacijom o postavkama grafova
        
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
                kanal(0), marker(1), line(2), rgb(3), alpha(4), zorder(5), label(6)
                """
                temp = [pomocni[key]['kanal'], 
                        pomocni[key]['marker'], 
                        pomocni[key]['line'], 
                        pomocni[key]['rgb'], 
                        pomocni[key]['alpha'], 
                        pomocni[key]['zorder'], 
                        pomocni[key]['label']]
                nLista.append(temp)
                
        #instanciranje modela i povezivanje sa QTableView-om
        self.model = tableModel.PomocniGrafovi(grafInfo = nLista)
        self.tableView.setModel(self.model)

        """2. popunjavanje comboboxeva"""
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
                          
        #reverse dict markera, samo za potrebe inicijalizacije
        initmarkeri = {'None':'Bez markera', 
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
        
        #nadji definirane vrijednosti markera
        validan = initmarkeri[self.__info['glavniKanal']['validanOK']['marker']]
        nevalidan = initmarkeri[self.__info['glavniKanal']['nevalidanOK']['marker']]
        ekstrem = initmarkeri[self.__info['glavniKanal']['ekstremimin']['marker']]
        
        markeri = sorted(list(self.__markeri.keys()))
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
        marker = self.__markeri[self.comboValidan.currentText()]
        #postavi vrijednost u self.__info na odgovarajuce mjesto
        self.__info['glavniKanal']['validanOK']['marker'] = marker
        self.__info['glavniKanal']['validanNOK']['marker'] = marker
    
    def promjeni_marker_nevalidan(self):
        """
        Funkcija odradjuje promjenu vrijednosti comboboxa za markere
        ne-validiranih vrijednosti
        """
        marker = self.__markeri[self.comboNeValidan.currentText()]
        #postavi vrijednost u self.__info na odgovarajuce mjesto
        self.__info['glavniKanal']['nevalidanOK']['marker'] = marker
        self.__info['glavniKanal']['nevalidanNOK']['marker'] = marker

    def promjeni_marker_ekstrem(self):
        """
        Funkcija odradjuje promjenu vrijednosti comboboxa za markere ekstremnih
        vrijednosti
        """
        marker = self.__markeri[self.comboEkstrem.currentText()]
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
            pomocni[nLista[i][6]] = {
                'kanal':nLista[i][0], 
                'marker':nLista[i][1], 
                'line':nLista[i][2], 
                'rgb':nLista[i][3], 
                'alpha':nLista[i][4], 
                'zorder':nLista[i][5], 
                'label':nLista[i][6]}
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
        self.makniGraf.clicked.connect(self.makni_graf) #gumb za brisanje pomocnog grafa
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
    
    def dodaj_graf(self, lista):
        """
        Funkcija dodaje graf u model.
        graf je zadan kao lista parametara koji se kao cjelina upisuju u model
        uz pomoc funkcije modela insertRows
        """
        dijalog = dijalog2.IzborPojedinacnogGrafa(kanali = self.__dostupniKanali)
        if dijalog.exec_():
            lista = dijalog.vrati_listu_grafa()
            self.model.insertRows(0,1,sto=[lista])
            
    def makni_graf(self, ind):
        """
        Funkcija mice graf iz modela na indeksu ind
        """
        if self.model.rowCount() > 0:
            i, ok = QtGui.QInputDialog.getInteger(self, 
                                                  'Brisanje grafova.', 
                                                  'Odabari redni broj grafa za brisanje:', 
                                                  0,
                                                  0,
                                                  self.model.rowCount()-1, 
                                                  1)
            if ok:
                self.model.removeRows(i,1)
###############################################################################
###############################################################################
#test ispravnosti dijaloga
if __name__ == '__main__':
    import sys
    defaulti = {
    'glavniKanal':{
        'midline':{'kanal':None, 'line':'-', 'rgb':(0,0,0), 'alpha':1.0, 'zorder':100, 'label':'average'},
        'validanOK':{'kanal':None, 'marker':'d', 'rgb':(0,255,0), 'alpha':1.0, 'zorder':100, 'label':'validiran, dobar'}, 
        'validanNOK':{'kanal':None, 'marker':'d', 'rgb':(255,0,0), 'alpha':1.0, 'zorder':100, 'label':'validiran, los'}, 
        'nevalidanOK':{'kanal':None, 'marker':'o', 'rgb':(0,255,0), 'alpha':1.0, 'zorder':100, 'label':'nije validiran, dobar'}, 
        'nevalidanNOK':{'kanal':None, 'marker':'o', 'rgb':(255,0,0), 'alpha':1.0, 'zorder':100, 'label':'nije validiran, los'},
        'fillsatni':{'kanal':None, 'crtaj':True, 'data1':'q05', 'data2':'q95', 'rgb':(0,0,255), 'alpha':0.5, 'zorder':1}, 
        'ekstremimin':{'kanal':None, 'crtaj':True, 'marker':'+', 'rgb':(90,50,10), 'alpha':1.0, 'zorder':100, 'label':'min'}, 
        'ekstremimax':{'kanal':None, 'crtaj':True, 'marker':'+', 'rgb':(90,50,10), 'alpha':1.0, 'zorder':100, 'label':'max'}
                    },
    'pomocniKanali':{
        'graf1':{'kanal':'1-SO2-ppb', 'marker':'+', 'line':'-', 'rgb':(100, 0, 0), 'alpha':0.7, 'zorder':12, 'label':'graf1'}
                    }, 
    'ostalo':{
        'opcijeminutni':{'cursor':False, 'span':True, 'ticks':True, 'grid':False, 'legend':False}, 
        'opcijesatni':{'cursor':False, 'span':False, 'ticks':True, 'grid':False, 'legend':False}
            }
                    }

    #TODO! model umire kod inicijalizacije ako pomocni kanali ne posotje
    #hrpa index errora
    defaulti1 = {
    'glavniKanal':{
        'midline':{'kanal':None, 'line':'-', 'rgb':(0,0,0), 'alpha':1.0, 'zorder':100, 'label':'average'},
        'validanOK':{'kanal':None, 'marker':'d', 'rgb':(0,255,0), 'alpha':1.0, 'zorder':100, 'label':'validiran, dobar'}, 
        'validanNOK':{'kanal':None, 'marker':'d', 'rgb':(255,0,0), 'alpha':1.0, 'zorder':100, 'label':'validiran, los'}, 
        'nevalidanOK':{'kanal':None, 'marker':'o', 'rgb':(0,255,0), 'alpha':1.0, 'zorder':100, 'label':'nije validiran, dobar'}, 
        'nevalidanNOK':{'kanal':None, 'marker':'o', 'rgb':(255,0,0), 'alpha':1.0, 'zorder':100, 'label':'nije validiran, los'},
        'fillsatni':{'kanal':None, 'crtaj':True, 'data1':'q05', 'data2':'q95', 'rgb':(0,0,255), 'alpha':0.5, 'zorder':1}, 
        'ekstremimin':{'kanal':None, 'crtaj':True, 'marker':'+', 'rgb':(90,50,10), 'alpha':1.0, 'zorder':100, 'label':'min'}, 
        'ekstremimax':{'kanal':None, 'crtaj':True, 'marker':'+', 'rgb':(90,50,10), 'alpha':1.0, 'zorder':100, 'label':'max'}
                    },
    'pomocniKanali':{}, 
    'ostalo':{
        'opcijeminutni':{'cursor':False, 'span':True, 'ticks':True, 'grid':False, 'legend':False}, 
        'opcijesatni':{'cursor':False, 'span':False, 'ticks':True, 'grid':False, 'legend':False}
            }
                    }


    app = QtGui.QApplication(sys.argv)
    x = IzborStoSeCrta(kanali = ['1-SO2-ppb','kanal2','kanal3'], glavniKanal = '1-SO2-ppb', info = defaulti1)
    x.show()
    sys.exit(app.exec_())
    