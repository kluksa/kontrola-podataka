# -*- coding: utf-8 -*-
"""
Created on Tue Nov  4 15:49:31 2014

@author: User
"""
from PyQt4 import QtGui, QtCore, uic

import pomocneFunkcije #cesto koristene funkcije, adapteri...
import tableModel #specificna implementacija modela za dinamicko dodavanje pomocnih grafova

###############################################################################
###############################################################################
base7, form7 = uic.loadUiType('opcije_pomocnih.ui')
class OpcijePomocnog(base7, form7):
    """
    Klasa je dijalog preko kojeg se bira i odredjuju postavke pomocnog
    grafa.
    """
###############################################################################
    def __init__(self, parent = None, default = [], stablo = None, copcije = None, mapa = {}):
        """
        inicijalizacija sa :
            -*listom defaultnih postavki za graf (postojeci izbor ili neki default)
            -stablo, instanca modela programa mjerenja (izbor stanice/kanala/usporedno)
            -copcije - lista combobox opcija [[markeri], [linije]]
            -opisna mapa (nested),  {programMjerenjaId:{stanica, kanal, usporedno....}}
            
        *lista sadrzi redom elemente:
        [kanal id, postaja, komponenta, usporedno, marker, markersize, line, 
        linewidth, rgb tuple, alpha, zorder, label]
        """
        super(base7, self).__init__(parent)
        self.setupUi(self)
        
        self.markeri = copcije[0] #popis svih stilova markera
        self.linije = copcije[1] #popis svih stilova linije
        self.transformMapa = mapa #nested dict, programMjerenjaId:info o tom mjerenju
                
        #provjeri da li je default zadan, spremi default u privatni member
        if default == []:
            #definiraj defaultnu vrijednost
            self.defaultGraf = [None, 
                            None, 
                            None, 
                            None, 
                            'Bez markera', 
                            12, 
                            'Puna linija', 
                            1.0, 
                            (0,0,255), 
                            1.0, 
                            5, 
                            '']
        else:
            self.defaultGraf = default
        
        #spremi stablo u privatni member
        self.stablo = stablo

        self.inicijaliziraj()
        self.veze()
###############################################################################
    def vrati_default_graf(self):
        """
        funkcija vraca member self.defaultGraf u kojemu su trenutne postavke
        pomocnog grafa
        """
        return self.defaultGraf
###############################################################################
    def inicijaliziraj(self):
        """
        Inicijaliztacija dijaloga.
        Postavljanje defaultnih vrijednosti u comboboxeve, spinboxeve...
        """
        #postavi model programa mjerenja u qtreeview
        self.treeView.setModel(self.stablo)
        
        #marker combo
        self.comboMarkerStil.clear()
        self.comboMarkerStil.addItems(self.markeri)
        self.comboMarkerStil.setCurrentIndex(self.comboMarkerStil.findText(self.defaultGraf[4]))
        
        #marker size
        self.spinMarker.setValue(self.defaultGraf[5])
        
        #linija combo
        self.comboLineStil.clear()
        self.comboLineStil.addItems(self.linije)
        self.comboLineStil.setCurrentIndex(self.comboLineStil.findText(self.defaultGraf[6]))
        
        #linija width
        self.doubleSpinLine.setValue(self.defaultGraf[7])
        
        #boja, stil gumba
        rgb = self.defaultGraf[8]
        a = self.defaultGraf[9]
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        stil = pomocneFunkcije.color_to_style_string('QPushButton#bojaButton', boja)
        self.bojaButton.setStyleSheet(stil)

        #label
        self.lineEditLabel.clear()
        postaja = str(self.defaultGraf[1])
        komponenta = str(self.defaultGraf[2])
        usporedno = str(self.defaultGraf[3])
        nazivGrafa = postaja+':'+komponenta+':'+usporedno
        self.lineEditLabel.setText(nazivGrafa)
        self.defaultGraf[11] = nazivGrafa
        
        #pokusaj izabrati isti element u stablu (ako je element izabran)
        if self.defaultGraf[0] != None:
            self.postavi_novi_glavni_kanal(self.defaultGraf[0])
###############################################################################
    def veze(self):
        """
        povezivanje signala koji se emitiraju prilikom interakcije sa widgetima
        sa funkcijama koje mjenjaju stanje grafa.
        """
        self.lineEditLabel.textChanged.connect(self.promjeni_label)
        self.comboMarkerStil.currentIndexChanged.connect(self.promjeni_marker_stil)
        self.spinMarker.valueChanged.connect(self.promjeni_marker_size)
        self.comboLineStil.currentIndexChanged.connect(self.promjeni_line_stil)
        self.doubleSpinLine.valueChanged.connect(self.promjeni_line_width)
        self.bojaButton.clicked.connect(self.promjeni_boju)
        self.treeView.clicked.connect(self.promjeni_izbor_stabla)
###############################################################################
    def pronadji_index_od_kanala(self, kanal):
        """
        Za zadani kanal (mjerenjeId) pronadji odgovarajuci QModelIndex u 
        stablu.
        ulaz je trazeni kanal, izlaz je QModelIndex
        """
        #"proseci" stablom u potrazi za indeksom
        for i in range(self.stablo.rowCount()):
            ind = self.stablo.index(i, 0) #index stanice, (parent)
            otac = self.stablo.getItem(ind)
            for j in range(otac.childCount()):
                ind2 = self.stablo.index(j, 0, parent = ind) #indeks djeteta
                komponenta = self.stablo.getItem(ind2)
                #provjera da li kanal u modelu odgovara zadanom kanalu
                if int(komponenta._data[2]) == kanal:
                    return ind2
        return None
###############################################################################
    def postavi_novi_glavni_kanal(self, kanal):
        """
        Metoda postavlja zadani kanal kao selektirani u treeView.
        Koristi se tijekom inicijalizacije
        """
        noviIndex = self.pronadji_index_od_kanala(kanal)
        if noviIndex != None:
            #postavi novi indeks
            self.treeView.setCurrentIndex(noviIndex)
            #javi za promjenu izbora stabla
            self.promjeni_izbor_stabla(True)
###############################################################################
    def promjeni_izbor_stabla(self, x):
        """
        promjena/izbor programa mjerenja sa stabla (Postaja/Kanal/Usporedno)
        """
        ind = self.treeView.currentIndex() #dohvati trenutni aktivni indeks
        item = self.stablo.getItem(ind) #dohvati specificni objekt pod tim indeksom
        prog = item._data[2] #dohvati program mjerenja iz liste podataka
        """
        Ako netko izabere stanicu u stablu, prog == None
        Ako netko izabere komponentu u stablu, prog == programMjerenjaId
        
        nastavi samo ako je izabrana komponenta!
        """
        if prog != None:
            prog = int(prog)
            #uz pomoc mape self.transformMapa dohvati postaju/komponentu/usporedno
            postaja = str(self.transformMapa[prog]['postajaNaziv'])
            komponenta = str(self.transformMapa[prog]['komponentaNaziv'])
            usporedno = str(self.transformMapa[prog]['usporednoMjerenje'])
            
            #promjeni self.defaultGraf ciljane vrijednosti
            self.defaultGraf[0] = prog
            self.defaultGraf[1] = postaja
            self.defaultGraf[2] = komponenta
            self.defaultGraf[3] = usporedno
            
            #promjeni label da odgovara izboru
            tekst = postaja+':'+komponenta+':'+usporedno
            self.lineEditLabel.clear()
            self.lineEditLabel.setText(tekst)
###############################################################################
    def promjeni_label(self, tekst):
        """
        promjeni/zamapti promjenu labela
        """
        self.defaultGraf[11] = str(tekst)
###############################################################################
    def promjeni_marker_stil(self):
        """
        promjeni/zapamti promjenu stila makrera
        """
        marker = self.comboMarkerStil.currentText()
        self.defaultGraf[4] = marker
###############################################################################
    def promjeni_line_stil(self):
        """
        promjeni/zapamti promjenu stila linije
        """
        marker = self.comboLineStil.currentText()
        self.defaultGraf[4] = marker
###############################################################################
    def promjeni_marker_size(self):
        """
        promjeni/zapamti promjenu velicine markera
        """
        self.defaultGraf[5] = self.spinMarker.value()
###############################################################################
    def promjeni_line_width(self):
        """
        promjeni/zapamti promjenu sirine linije
        """
        self.defaultGraf[7] = self.doubleSpinLine.value()
###############################################################################
    def promjeni_boju(self):
        """
        promjeni/zapamti promjenu boje grafa
        """
        #defaultni izbor
        rgb = self.defaultGraf[8]
        a = self.defaultGraf[9]
        #convert u QColor
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga za promjenu boje
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test == True ako je boja ispravno definirana
            color = QtGui.QColor.fromRgba(color) #bitni adapter izlaza dijaloga
            rgb, a = pomocneFunkcije.qcolor_to_default_color(color)
            #zapamti novu boju
            self.defaultGraf[8] = rgb
            self.defaultGraf[9] = a
            #promjeni boju gumba
            boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
            stil = pomocneFunkcije.color_to_style_string('QPushButton#bojaButton', boja)
            self.bojaButton.setStyleSheet(stil)
###############################################################################
###############################################################################
base1, form1 = uic.loadUiType('kontrola_crtanja_grafova.ui')
class OpcijeGrafova(base1, form1):
    """
    Klasa je djalog preko kojeg se odredjuje sto se prikazuje na grafovima
    Objekt vizualno sadrzi:
        -prikaz pomocnih grafova (QTableView)
        -izbori boje i markera za glavni kanal
        -izbor fill opcije i crtanja ekstremnih vrijednosti glavnog kanala
        -gumbi za dodavanje/brisanje pomocnih kanala
    """
###############################################################################
    def __init__(self, parent = None, defaulti = {}, opiskanala = {}, stablo = None):
        """
        inicijalizacija sa defaultnim vrijednostima grafova (self.graf_defaults)
        """
        super(base1, self).__init__(parent)
        self.setupUi(self)
        
        #model stabla programa mjerenja, treba za inicijalizaciju dijaloga za
        #dodavanje pomocnih grafova
        self.drvo = stablo
        
        #nested dict sa informacijom o postavkama grafova
        self.defaulti = defaulti
        
        #dictionary sa informacijom o stanici/kanalu/usporedno za programMjerenjaId
        self.mapaKanali = opiskanala
               
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
        
        #definiranje liste sa stilovima markera i stilovima linije
        self.comboListe = [sorted(list(self.__opis_to_marker.keys())),
                           sorted(list(self.__opis_to_line.keys()))]

        #inicijalizacija izbornika
        self.initial_setup()
        #povezivanje sa signalima
        self.veze()
###############################################################################
    def initial_setup(self):
        """
        Ova funkcija sluzi da se preko nje instancira dijalog.
        """
        """1. inicijalizacija modela, povezivanje sa QTableView"""
        #moramo iz dicta self.defaulti izvuci i konstruirati nested listu
        #informacija o pomocnim grafovima za inicijalizaciju modela
        nLista = [] #nested lista
        pomocni = self.defaulti['pomocniKanali']
        if len(pomocni) == 0:
            nLista = []
        else:
             for key in pomocni:
                """
                !!!redosljed je jako bitan da model zna gdje su elementi!!!
                slaganje liste, u zagradi je broj indeksa:
                
                kanal/programMjerenjaId (0),
                postaja (1), 
                komponenta naziv (2), 
                usporedno (3), 
                marker (4), 
                merkersize (5), 
                line (6), 
                linewidth (7), 
                rgb (8), 
                alpha (9), 
                zorder (10), 
                label (11)
                """
                programMjerenjaId = int(pomocni[key]['kanal'])
                postaja = self.mapaKanali[programMjerenjaId]['postajaNaziv']
                komponentaNaziv = self.mapaKanali[programMjerenjaId]['komponentaNaziv']
                usporedno = self.mapaKanali[programMjerenjaId]['usporednoMjerenje']
                #konstrukcija elementa nested liste
                temp = [programMjerenjaId, 
                        postaja, 
                        komponentaNaziv, 
                        usporedno, 
                        self.__marker_to_opis[pomocni[key]['marker']], 
                        pomocni[key]['markersize'], 
                        self.__line_to_opis[pomocni[key]['line']], 
                        pomocni[key]['linewidth'], 
                        pomocni[key]['rgb'], 
                        pomocni[key]['alpha'], 
                        pomocni[key]['zorder'], 
                        pomocni[key]['label']]
                #dodaj element na nested listu
                nLista.append(temp)

        #sortirane liste opcija za izgled markera i stil linije
        markeri = self.comboListe[0]
        linije = self.comboListe[1]
        
        
        #instanciranje modela i povezivanje sa QTableView-om
        #inicjalizacija modela
        self.tmodel = tableModel.PomocniGrafovi(grafInfo = nLista)
        
        #inicijalizacija parametara za tablicu (tablica instancira delegat kojemu su
        #potrebni sljedeci podaci)
        initlista = [self.drvo, 
                     self.comboListe, 
                     self.mapaKanali]
        #inicijalizacija tablice
        self.tableView = Tablica(lista = initlista)
        #postavljanje modela u qtablewiew
        self.tableView.setModel(self.tmodel)
        #set selecting by rows
        self.tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        #set selection mode, only one at a time
        self.tableView.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        #postavljanje tablice u layout dijaloga
        self.tableViewLayout.addWidget(self.tableView)
        #check za disable/enable gumba za brisanje grafova (ovisno da li su definirani)
        self.toggle_brisanje_pomocnog_grafa()

        """2. popunjavanje comboboxeva"""
        
        #nadji definirane vrijednosti markera
        validan = self.__marker_to_opis[self.defaulti['glavniKanal']['validanOK']['marker']]
        nevalidan = self.__marker_to_opis[self.defaulti['glavniKanal']['nevalidanOK']['marker']]
        ekstrem = self.__marker_to_opis[self.defaulti['glavniKanal']['ekstremimin']['marker']]
        msize = self.defaulti['glavniKanal']['validanOK']['markersize']
        
        #nadji opcije linije glavnog grafa
        stilLinije = self.__line_to_opis[self.defaulti['glavniKanal']['midline']['line']]
        sirinaLinije = self.defaulti['glavniKanal']['midline']['linewidth']
        
        #set spinbox velicine markera
        self.spinBoxMarker.setValue(msize)
        
        #set doublespinbox sirine linije
        self.doubleSpinBoxLine.setValue(sirinaLinije)
        
        #set markere
        markeri = sorted(list(self.__opis_to_marker.keys()))
        self.comboValidan.clear()
        self.comboValidan.addItems(markeri)
        self.comboValidan.setCurrentIndex(self.comboValidan.findText(validan))
        self.comboNeValidan.clear()
        self.comboNeValidan.addItems(markeri)
        self.comboNeValidan.setCurrentIndex(self.comboNeValidan.findText(nevalidan))
        self.comboEkstrem.clear()
        self.comboEkstrem.addItems(markeri)
        self.comboEkstrem.setCurrentIndex(self.comboEkstrem.findText(ekstrem))
        
        #set stil linije
        linije = sorted(list(self.__opis_to_line.keys()))
        self.comboStilLinije.clear()
        self.comboStilLinije.addItems(linije)
        self.comboStilLinije.setCurrentIndex(self.comboStilLinije.findText(stilLinije))
        
        #set comboboxeve vezane za fill
        agregiraniPodaci = sorted(['min', 'max', 'avg', 'q05', 'q95' ,'median'])
        self.comboData1.clear()
        self.comboData1.addItems(agregiraniPodaci)
        self.comboData1.setCurrentIndex(self.comboData1.findText(self.defaulti['glavniKanal']['fillsatni']['data1']))
        self.comboData2.clear()
        self.comboData2.addItems(agregiraniPodaci)
        self.comboData2.setCurrentIndex(self.comboData1.findText(self.defaulti['glavniKanal']['fillsatni']['data2']))
        
        """3. postavke boje, promjena boje QPushButtona"""
        #boja za ako je podatak flagan kao dobar (OK)
        rgb = self.defaulti['glavniKanal']['validanOK']['rgb']
        a = self.defaulti['glavniKanal']['validanOK']['alpha']
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        stil = pomocneFunkcije.color_to_style_string('QPushButton#gumbBojaOK', boja)
        self.gumbBojaOK.setStyleSheet(stil)
        #boja ako je podatak flagan kao los (Not OK)
        rgb = self.defaulti['glavniKanal']['validanNOK']['rgb']
        a = self.defaulti['glavniKanal']['validanNOK']['alpha']
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        stil = pomocneFunkcije.color_to_style_string('QPushButton#gumbBojaNOK', boja)
        self.gumbBojaNOK.setStyleSheet(stil)
        #boja ekstremnih vrijednosti (minimum i maksimum na satnom grafu)
        rgb = self.defaulti['glavniKanal']['ekstremimin']['rgb']
        a = self.defaulti['glavniKanal']['ekstremimin']['alpha']
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        stil = pomocneFunkcije.color_to_style_string('QPushButton#gumbBojaEkstrem', boja)
        self.gumbBojaEkstrem.setStyleSheet(stil)
        #boja sjencanog podrucja na satnom grafu (fill_between)
        rgb = self.defaulti['glavniKanal']['fillsatni']['rgb']
        a = self.defaulti['glavniKanal']['fillsatni']['alpha']
        boja = pomocneFunkcije.default_color_to_qcolor(rgb, a)
        stil = pomocneFunkcije.color_to_style_string('QPushButton#gumbBojaFill', boja)
        self.gumbBojaFill.setStyleSheet(stil)
        
        """4. postavljanje checkboxeva te, disbleanje i enableanje opcija"""
        check1 = self.defaulti['glavniKanal']['ekstremimin']['crtaj']
        self.checkEkstrem.setChecked(check1)
        self.promjeni_status_ekstrem(check1)
        check2 = self.defaulti['glavniKanal']['fillsatni']['crtaj']
        self.checkFill.setChecked(check2)
        self.promjeni_status_fill(check2)
###############################################################################
    def promjeni_status_fill(self, x):
        """
        pomocna funkcija za toggle sjencanja na satnom grafu.
        x je boolean koji javlja stanje checkboxa, True -> ima kvacicu
        
        Ovisno o stanju, treba promjeniti status kontrolnih widgeta (disable/enable)
        te promjeniti vrijednosti u dictu da ostali dijelovi aplikacije znaju sto
        je izabrano
        """
        if x:
            self.defaulti['glavniKanal']['fillsatni']['crtaj'] = True
            self.comboData1.setEnabled(True)
            self.comboData2.setEnabled(True)
            self.gumbBojaFill.setEnabled(True)
        else:
            self.defaulti['glavniKanal']['fillsatni']['crtaj'] = False
            self.comboData1.setEnabled(False)
            self.comboData2.setEnabled(False)
            self.gumbBojaFill.setEnabled(False)
###############################################################################
    def promjeni_status_ekstrem(self, x):
        """
        pomocna funkcija za toggle prikaza ekstremnih vrijednosti na satnom grafu.
        x je boolean koji javlja stanje checkboxa, True -> ima kvacicu
        
        Ovisno o stanju, treba promjeniti status kontrolnih widgeta (disable/enable)
        te promjeniti vrijednosti u dictu da ostali dijelovi aplikacije znaju sto
        je izabrano
        """
        if x:
            self.defaulti['glavniKanal']['ekstremimin']['crtaj'] = True
            self.defaulti['glavniKanal']['ekstremimax']['crtaj'] = True
            self.comboEkstrem.setEnabled(True)
            self.gumbBojaEkstrem.setEnabled(True)
        else:
            self.defaulti['glavniKanal']['ekstremimin']['crtaj'] = False
            self.defaulti['glavniKanal']['ekstremimax']['crtaj'] = False
            self.comboEkstrem.setEnabled(False)
            self.gumbBojaEkstrem.setEnabled(False)
###############################################################################
    def promjeni_marker_validan(self):
        """
        Funkcija odradjuje promjenu vrijednosti comboboxa za markere 
        validiranih vrijednosti
        """
        #dohvati trenutnu vrijednost comboboxa
        marker = self.__opis_to_marker[self.comboValidan.currentText()]
        #postavi novu vrijednost
        self.defaulti['glavniKanal']['validanOK']['marker'] = marker
        self.defaulti['glavniKanal']['validanNOK']['marker'] = marker
###############################################################################
    def promjeni_marker_nevalidan(self):
        """
        Funkcija odradjuje promjenu vrijednosti comboboxa za markere
        ne-validiranih vrijednosti
        """
        marker = self.__opis_to_marker[self.comboNeValidan.currentText()]
        #postavi novu vrijednost
        self.defaulti['glavniKanal']['nevalidanOK']['marker'] = marker
        self.defaulti['glavniKanal']['nevalidanNOK']['marker'] = marker
###############################################################################
    def promjeni_marker_ekstrem(self):
        """
        Funkcija odradjuje promjenu vrijednosti comboboxa za markere ekstremnih
        vrijednosti
        """
        marker = self.__opis_to_marker[self.comboEkstrem.currentText()]
        #postavi novu vrijednost
        self.defaulti['glavniKanal']['ekstremimin']['marker'] = marker
        self.defaulti['glavniKanal']['ekstremimax']['marker'] = marker
###############################################################################
    def promjeni_fill_komponenta1(self):
        """
        Funkcija odradjuje promjenu vrijednosti comboboxa za prvu komponentu
        argumenata za sjencanje na satnom grafu (sjencanje je izmedju 2 komponente)
        """
        data = self.comboData1.currentText()
        #postavi novu vrijednost
        self.defaulti['glavniKanal']['fillsatni']['data1'] = data
###############################################################################
    def promjeni_fill_komponenta2(self):
        """
        Funkcija odradjuje promjenu vrijednosti comboboxa za drugu komponentu
        argumenata za sjencanje na satnom grafu (sjencanje je izmedju 2 komponente)
        """
        data = self.comboData2.currentText()
        #postavi novu vrijednost
        self.defaulti['glavniKanal']['fillsatni']['data2'] = data
###############################################################################
    def promjeni_boju_fill(self):
        """
        Funkcija odradjuje promjenu boje osjencanog podrucja na satnom grafu.
        Dodatno, zaduzena je za update boje gumba s kojim se poziva.
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
            stil = pomocneFunkcije.color_to_style_string('QPushButton#gumbBojaFill', boja)
            self.gumbBojaFill.setStyleSheet(stil)
###############################################################################
    def promjeni_boju_ekstrem(self):
        """
        Funkcija odradjuje promjenu boje ekstremnih vrijednosti na satnom grafu.
        Dodatno, zaduzena je za update boje gumba s kojim se poziva
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
            stil = pomocneFunkcije.color_to_style_string('QPushButton#gumbBojaEkstrem', boja)
            self.gumbBojaEkstrem.setStyleSheet(stil)
###############################################################################
    def promjeni_boju_ok(self):
        """
        Funkcija odradjuje promjenu boje dobro flaganih podataka na satnom grafu.
        Dodatno, zaduzena je za update boje gumba s kojim se poziva
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
            stil = pomocneFunkcije.color_to_style_string('QPushButton#gumbBojaOK', boja)
            self.gumbBojaOK.setStyleSheet(stil)
###############################################################################
    def promjeni_boju_nok(self):
        """
        Funkcija odradjuje promjenu boje lose flaganih podataka na satnom grafu.
        Dodatno, zaduzena je za update boje gumba s kojim se poziva
        """
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
            stil = pomocneFunkcije.color_to_style_string('QPushButton#gumbBojaNOK', boja)
            self.gumbBojaNOK.setStyleSheet(stil)
###############################################################################
    def promjeni_velicinu_markera(self):
        """
        funkcija mjenja promjenu velicine svih markera za glavni graf.
        """
        #dohvati trenutnu vrijednost spinboxa
        msize = self.spinBoxMarker.value()
        #postavi novu vrijednost
        self.defaulti['glavniKanal']['validanOK']['markersize'] = msize
        self.defaulti['glavniKanal']['validanNOK']['markersize'] = msize
        self.defaulti['glavniKanal']['nevalidanOK']['markersize'] = msize
        self.defaulti['glavniKanal']['nevalidanNOK']['markersize'] = msize
        self.defaulti['glavniKanal']['ekstremimin']['markersize'] = msize
        self.defaulti['glavniKanal']['ekstremimax']['markersize'] = msize
###############################################################################
    def promjeni_stil_linije(self):
        """
        funkcije mjenja stil linije 'midline' glavnog grafa
        """
        #dohvati trenutnu vrijednost spinboxa
        ls = self.__opis_to_line[self.comboStilLinije.currentText()]
        #postavi novu vrijednost
        self.defaulti['glavniKanal']['midline']['line'] = str(ls)
###############################################################################
    def promjeni_sirinu_linije(self):
        """
        funkcije mjenja sirinu linije 'midline' glavnog grafa
        """
        #dohvati trenutnu vrijednost spinboxa
        lw = self.doubleSpinBoxLine.value()
        #postavi novu vrijednost
        self.defaulti['glavniKanal']['midline']['linewidth'] = round(float(lw),1)
###############################################################################
    def dohvati_postavke(self):
        """
        Ova funkcija sluzi da se preko nje dohvate postavke grafova za crtanje, 
        tj. izlazna vrijednost dijaloga (defaultni dictionary).
        """
        #dohvati nested listu u modelu
        nLista = self.tmodel.vrati_nested_listu()
        #priprema dicta u koji cemo spremiti podatke iz modela
        pomocni = {}
        #upisivanje u pomocni dict
        for i in range(len(nLista)):
            pomocni[nLista[i][0]] = {
                'kanal':nLista[i][0], 
                'marker':self.__opis_to_marker[nLista[i][4]], 
                'markersize':nLista[i][5], 
                'line':self.__opis_to_line[nLista[i][6]], 
                'linewidth':nLista[i][7], 
                'rgb':nLista[i][8], 
                'alpha':nLista[i][9], 
                'zorder':nLista[i][10], 
                'label':nLista[i][11]
            }
            
        #zamjeni dict u self.defaulti
        self.defaulti['pomocniKanali'] = pomocni
        #vrati cijeli dict sa postavkama
        return self.defaulti
###############################################################################
    def veze(self):
        """
        funkcija sa connectionima izmedju widgeta. Wrapper da sve "lokalne" veze
        signala i slotova budu na jendnom mjestu
        """
        self.dodajGraf.clicked.connect(self.dodaj_graf) #gumb za dodavanje pomocnog grafa
        self.makniGrafGumb.clicked.connect(self.makni_pomocni_graf) #gumb za brisanje sekeltiranog pomocnog grafa
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
        self.comboStilLinije.currentIndexChanged.connect(self.promjeni_stil_linije) #izbor stila linije glavnog grafa
        self.doubleSpinBoxLine.valueChanged.connect(self.promjeni_sirinu_linije) #izbor sirine linije glavnog grafa
        self.spinBoxMarker.valueChanged.connect(self.promjeni_velicinu_markera) #izbor velicine markera za satni graf
###############################################################################
    def dodaj_graf(self):
        """
        Funkcija dodaje graf u table model preko dijaloga za dodavanje pomocnih
        grafova. Dijalog za pomocne grafove definira neke defaultne postavke
        grafa (ne definira postaju/kanal...).
        """
        #dijalog za izbor grafa, inicijaliziraj, prikazi
        if self.mapaKanali != None:
            if len(self.mapaKanali.keys()) > 0:
                """self.mapaKanali mora biti pun - tree model mora imati elemente 
                inace dodavanje nema smisla (nema programa mjerenja)"""
                #poziv dijaloga
                """
                dijalog se instancira na kompliciran nacin, puno opcija...
                
                1. parent
                    -definira tko je parent modalnom dijalogu
                    -po defaultu je None
                2. default
                    -defaultna lista za pomocni graf, ako se zada prazna lista
                    dijalog OpcijePomocnog ce definirati defaultne vrijednosti
                    -moze se zadati default ako se konstuira lista:
                    [programMjerenjaId, postaja, komponenta, usporedno, marker, 
                    marker size, line, line width, rgb tuple, alpha, zorder, label]
                    -preciznije, jedan redak nested liste s kojom se instancira
                    self.tmodel
                3. stablo
                    	-instanca tree modela programa mjerenja
                     -sluzi da bi se unutar OpcijePomocnog mogao instancirati treeView
                     sa svim stanicama/komponentama
                4. copcije
                    -lista od 2 elementa [[lista svih markera], [lista svih linija]]
                    -sluzi za populiranje comboboxeva unutar OpcijePomocnog
                5. mapa
                    -pomocna mapa (nested) sa informacijom o stanici, komponenti, isl.
                    za svaki programMjerenjaId (glavni kljuc)
                    -sluzi da bi iz indeksa treeView-a mogli doci do podataka o stanici
                    komponenti i usprednom mjerenju
                """
                dijalog = OpcijePomocnog(default = [], 
                                         stablo = self.drvo, 
                                         copcije = self.comboListe, 
                                         mapa = self.mapaKanali)
                if dijalog.exec_():
                    pomocniKanal = dijalog.vrati_default_graf()
                    if pomocniKanal[0] != None: #neko mjerenje mora biti izabrano (programMjerenjaId != None)
                        #dodaj pomocniKanal u self.tmodel (table model)
                        self.tmodel.insertRows(0, 1, sto=[pomocniKanal])
                        self.toggle_brisanje_pomocnog_grafa()
        else:
            #javi problem, model dostupnih programa mjerenja nije uspjesno instanciran
            tekst = 'Mapa sa programima mjerenja nije instancirana.\nNije moguce dodati nove grafove.\nPokusaj obnoviti vezu sa REST servisom.'
            QtGui.QMessageBox.information(self, "Problem kod dodavanja grafova", tekst)
###############################################################################
    def makni_pomocni_graf(self):
        """Brisanje selektiranog reda u qtableview"""
        indeks = self.tableView.currentIndex()
        red = indeks.row()
        if red >= 0:
            self.tmodel.removeRows(red, 1)
            self.toggle_brisanje_pomocnog_grafa()
###############################################################################
    def toggle_brisanje_pomocnog_grafa(self):
        """toggle za enable/disable gumba za brisanje pomocnih grafova"""
        if self.tmodel.rowCount == 0:
            self.makniGrafGumb.setEnabled(False)
        else:
            self.makniGrafGumb.setEnabled(True)
###############################################################################
###############################################################################
class Tablica(QtGui.QTableView):
    """
    Ova klasa je zaduzena za prikaz modela pomocnih grafova.
    Subklasani QTableView, ciljano zahtjevamo da se odredjeni stupci
    ponasaju drugacije. Delegiramo editiranje modela drugoj klasi
    
    Cilj je umjesto line editora omoguciti poziv dijaloga za izbor opcija 
    pomocnih grafova.
    """
    def __init__(self, parent = None, lista = None):
        QtGui.QTableView.__init__(self, parent)
        
        self.initLista = lista
        
        # postavi isti delegate za sva 3 stupca [postaja, komponenta, usporedno]
        self.setItemDelegateForColumn(0, PromjeniPomocniDelegate(self, lista = self.initLista))
        self.setItemDelegateForColumn(1, PromjeniPomocniDelegate(self, lista = self.initLista))
        self.setItemDelegateForColumn(2, PromjeniPomocniDelegate(self, lista = self.initLista))
###############################################################################
###############################################################################
class PromjeniPomocniDelegate(QtGui.QItemDelegate):
    """
    Mali hack, u biti ne delegira nista, direktno poziva dijalog za
    pomocne grafove. Inicijalizira se sa defaultnim vrijednostima vezanim
    za 'editirani' redak u tablici
    """
    def __init__(self, parent, lista = None):
        QtGui.QItemDelegate.__init__(self, parent)
        
        if lista != None:
            self.lista = lista #[program mjerenja tree, combo liste za marker i line, info mapa o programima mjerenja]
        
    def createEditor(self, parent, option, index):
        """
        1. nadji defaultne podatke za redak
        2. inicijaliziraj i prikazi dijalog sa izabranim redkom
        3. ako je OK, postavi nove vrijednosti u tableModel
        """
        #pronadji defultni graf za izabrani redak
        red = index.row()
        grafRed = index.model().grafInfo[red]
        
        if self.lista != None:
            #inicijaliziraj i prikazi dijalog sa izabranim redkom
            dijalog = OpcijePomocnog(parent = parent, 
                                     default = grafRed, 
                                     stablo = self.lista[0], #tree programa mjerenja
                                     copcije = self.lista[1], #vijednosti za comboboxeve 
                                     mapa = self.lista[2]) #mapa koja povezuje program mjerenja i info (stanica, komponenta...)
            if dijalog.exec_():
                pomocniKanal = dijalog.vrati_default_graf()
                if pomocniKanal[0] != None: #neko mjerenje mora biti izabrano (programMjerenjaId != None)
                    #zamjeni pomocni Kanal sa updateanom verzijom
                    index.model().grafInfo[red] = pomocniKanal
###############################################################################
###############################################################################