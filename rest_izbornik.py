# -*- coding: utf-8 -*-
"""
Created on Thu Jan 22 10:55:55 2015

@author: User
"""
from PyQt4 import QtCore, uic
import datetime #potreban za provjeru da li je izabrani dan u buducnosti
import modeldrva #potreban samo za provjeru tipa modela
###############################################################################
###############################################################################
base5, form5 = uic.loadUiType('rest_izbornik_gui.ui')
class RestIzbornik(base5, form5):
    """
    REST izbornik (gumbi, treeView, kalendar...).    
    """
    def __init__(self, parent = None):
        super(base5, self).__init__(parent)
        self.setupUi(self)
        
        self.model = None
        
        self.veze()
###############################################################################
    def veze(self):
        """
        Povezivanje akcija (poput izbora datuma ili pritiska gumba) sa 
        funkcijama.
        """
        
        #prikaz dijaloga za postavke grafova
        self.postavkeGrafova.clicked.connect(self.prikazi_dijalog_postavki)
        
        #doubleclick/enter na kalendar
        self.calendarWidget.activated.connect(self.get_mjerenje_datum)
        
        #single click/select na kalendar
        self.calendarWidget.clicked.connect(self.get_mjerenje_datum)
        
        #doubleclick/enter na element u treeViewu (program mjerenja)
        self.treeView.activated.connect(self.get_mjerenje_datum)
###############################################################################
    def prikazi_dijalog_postavki(self):
        """Zahtjev kontoloru za promjenom postavki grafova."""
        self.emit(QtCore.SIGNAL('promjeni_postavke_grafova'))
###############################################################################
    def get_mjerenje_datum(self, x):
        """
        Funkcija se poziva prilikom:
            -doubleclicka na valjani program mjerenja
            -singleclick ili doubleclick datuma na kalendaru
            
        Emitira se signal sa izborom [programMjerenjaId, datum] kao listu
        Ne emitira listu ako je izabrani datum u "buducnosti" (jos nema podataka).
        
        P.S. ulazni argument x mora postojati radi signala activated/clicked
        prilikom pozivanja ove funkcije slobodno prosljedi True kao ulazni argument
        """
        #dohvacanje i formatiranje trenutno aktivnog datuma u kalendaru
        qdan = self.calendarWidget.selectedDate() #dohvaca QDate objekt
        pdan = qdan.toPyDate() #convert u datetime.datetime python objekt
        dan = pdan.strftime('%Y-%m-%d') #transformacija u zadani string format
        
        #provjeri datum, ako je u "buducnosti", zanemari naredbu
        danas = datetime.datetime.now()
        sutra = danas + datetime.timedelta(days = 1)
        sutra = sutra.date()
        #mozda je try block visak... stavljen just in case zbog potencijalnih
        #problema sa dohvacanjem prorama mjerenja sa self.treeViewa
        try:
            if (pdan < sutra and type(self.model) == modeldrva.ModelDrva):
                #dohvacanje programa mjerenja
                ind = self.treeView.currentIndex() #dohvati trenutni aktivni indeks
                item = self.model.getItem(ind) #dohvati specificni objekt pod tim indeksom
                prog = item._data[2] #dohvati program mjerenja iz liste podataka
    
                if prog != None:
                    output = [int(prog), dan]
                    #print('Izabrana kombinacija: {0}'.format(output))
                    self.emit(QtCore.SIGNAL('gui_izbornik_citaj(PyQt_PyObject)'), output)
                else:
                    print('Kriva kombinacija, nedostaje program mjerenja.')
            else:
                print('Kriva kombinacija, dan je u buducnosti.')
        except Exception as err:
            tekst = 'Opcenita pogreska, problem sa dohvacanjem programa mjerenja\n'+str(err)
            self.emit(QtCore.SIGNAL('error_message(PyQt_PyObject)'),tekst)
###############################################################################
    def sljedeci_dan(self):
        """
        Metoda "pomice dan" u kalendaru naprijed za 1 dan od trenutno selektiranog
        """
        #dohvati trenutno selektirani dan
        dan = self.calendarWidget.selectedDate()
        #uvecaj za 1
        dan2 = dan.addDays(1)
        #postavi novi dan kao trenutno selektirani
        self.calendarWidget.setSelectedDate(dan2)
        #informiraj kontroler o promjeni
        self.get_mjerenje_datum(True)
###############################################################################
    def prethodni_dan(self):
        """
        Metoda "pomice dan" u kalendaru nazad za 1 dan od trenutno selektiranog
        """
        #dohvati trenutno selektirani dan
        dan = self.calendarWidget.selectedDate()
        #smanji za 1
        dan2 = dan.addDays(-1)
        #postavi novi dan kao trenutno selektirani
        self.calendarWidget.setSelectedDate(dan2)
        #informiraj kontroler o promjeni
        self.get_mjerenje_datum(True)
###############################################################################
#    def pronadji_index_od_kanala(self, kanal):
#        """
#        Za zadani kanal (mjerenjeId) pronadji odgovarajuci QModelIndex u 
#        stablu.
#        ulaz je trazeni kanal, izlaz je QModelIndex
#        """
#        #TODO! try blok? ovo moze failati ako model nije dobro instanciran
#        #"proseci" stablom u potrazi za indeksom
#        for i in range(self.model.rowCount()):
#            ind = self.model.index(i, 0) #index stanice, (parent)
#            otac = self.model.getItem(ind)
#            for j in range(otac.childCount()):
#                ind2 = self.model.index(j, 0, parent = ind) #indeks djeteta
#                komponenta = self.model.getItem(ind2)
#                #provjera da li kanal u modelu odgovara zadanom kanalu
#                if int(komponenta.data(2)) == kanal:
#                    return ind2
#        return None
###############################################################################
#    def postavi_novi_glavni_kanal(self, kanal):
#        """
#        Metoda postavlja zadani kanal kao selektirani u treeView. Takodjer, 
#        javlja kontroloru da je doslo do promjene u izabranom kanalu.
#        """
#        #TODO! ako pronadji_index_od_kanala ne faila, ovo bi trebalo raditi 100%
#        noviIndex = self.pronadji_index_od_kanala(kanal)
#        if noviIndex != None:
#            #postavi novi indeks
#            self.treeView.setCurrentIndex(noviIndex)
#            #informiraj kontroler o promjeni, pokreni crtanje/izbor
#            self.get_mjerenje_datum(True)                   
###############################################################################
###############################################################################           