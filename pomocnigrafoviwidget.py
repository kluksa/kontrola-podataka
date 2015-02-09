# -*- coding: utf-8 -*-
"""
Created on Fri Feb  6 12:53:28 2015

@author: User
"""
from PyQt4 import QtGui, uic

import tableModel
import dodavanjepomocnih

###############################################################################
###############################################################################
base24, form24 = uic.loadUiType('POMOCNI_GRAFOVI_WIDGET.ui')
class PomocniIzbor(base24, form24):
    """
    Widget se sastoji od QtableView instance i dva gumba (za dodavanje i
    brisanje pomocnih grafova)
    
    inicijalizacija sa ulaznim keyword argumentima:
    
    defaulti
        --> nested dictionary sa opisom grafova
        
    stablo
        --> instanca tree modela programa mjerenja
        
    cListe
        --> nested lista
        --> lista sa svim dozvoljenim elementima za comboboxeve (u listama)
        --> [markeri, linije]
        
    opisKanala
        --> dict sa opisom programa mjerenja za svaki programMjerenjaId
        --> informacija o postaji, komponenti...
        
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
    def __init__(self, parent = None, defaulti = {}, stablo = None, cListe = [], opisKanala = {}, listHelpera = []):
        super(base24, self).__init__(parent)
        self.setupUi(self)
        
        #__init__ parametri
        self.defaulti = defaulti
        self.drvo = stablo
        self.comboListe = cListe
        self.mapaKanali = opisKanala
        self.dictHelperi = listHelpera
        
        #konstruiraj table model iz raspolozivih podataka
        self.tmodel = self.napravi_table_model()
        
        #inicijalizacija parametara za tablicu 
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
        
        self.veze()
###############################################################################
    def veze(self):
        """
        Povezivanje kontrolnih widgeta sa akcijama
        """
        self.dodajGrafGumb.clicked.connect(self.dodaj_graf)
        self.makniGrafGumb.clicked.connect(self.makni_pomocni_graf)

###############################################################################
    def napravi_table_model(self):
        """
        konstrukcija modela za QTableView
        """
        nLista = []
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
                        self.dictHelperi[0][pomocni[key]['marker']], 
                        pomocni[key]['markersize'], 
                        self.dictHelperi[2][pomocni[key]['line']], 
                        pomocni[key]['linewidth'], 
                        pomocni[key]['rgb'], 
                        pomocni[key]['alpha'], 
                        pomocni[key]['zorder'], 
                        pomocni[key]['label']]
                #dodaj element na nested listu
                nLista.append(temp)
        
        return tableModel.PomocniGrafovi(grafInfo = nLista)
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
                dijalog = dodavanjepomocnih.OpcijePomocnog(
                    default = [], 
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
    def vrati_pomocne_grafove(self):
        """
        metoda vraca dict strukturu pomocnih grafova za crtanje iz table modela
        """
        #dohvati nested listu u modelu
        nLista = self.tmodel.vrati_nested_listu()
        #priprema dicta u koji cemo spremiti podatke iz modela
        pomocni = {}
        #upisivanje u pomocni dict
        for i in range(len(nLista)):
            pomocni[nLista[i][0]] = {
                'kanal':nLista[i][0], 
                'marker':self.dictHelperi[1][nLista[i][4]], 
                'markersize':nLista[i][5], 
                'line':self.dictHelperi[3][nLista[i][6]], 
                'linewidth':nLista[i][7], 
                'rgb':nLista[i][8], 
                'alpha':nLista[i][9], 
                'zorder':nLista[i][10], 
                'label':nLista[i][11]
            }
        
        #vrati dict pomocnih kanala
        return pomocni
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
            dijalog = dodavanjepomocnih.OpcijePomocnog(
                parent = parent, 
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