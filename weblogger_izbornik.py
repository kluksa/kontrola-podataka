# -*- coding: utf-8 -*-
"""
Created on Wed Jul 16 13:22:35 2014

selektor fileova + navigacija

@author: velimir

U ovom modulu nalaze se sve stvari vezane za weblogger izbornik
"""

import sys

import copy
import dijalog1
import citac
from datetime import timedelta
import pandas as pd
from PyQt4 import QtCore, QtGui, uic
###############################################################################
###############################################################################
class dateCalendar(QtGui.QCalendarWidget):
    """
    Ovo je reimplementacija QCalendarWidgeta.
    Kalendar je reimplementiran da bi omogucio bojanje pozadine specificnih dana
    """
    def __init__(self, parent = None):
        """Konstruktor klase 
        
        Postavlja da je prvi stupac kalendara ponedjeljak
        Postavlja listu datuma koji se trebaju drugacije obojati
        Postavlja boju pozadine pojedinog datuma koji se treba drugacije obojati
        """
        QtGui.QCalendarWidget.__init__(self, parent)
        #set the calendar to have monday as first
        self.setFirstDayOfWeek(QtCore.Qt.Monday)
        #generalni set boje u lagano prozirno zelenu
        self.color = QtGui.QColor(0,200,0)
        self.color.setAlpha(50)
        self.colorSelected = QtGui.QColor(0,0,200)
        self.colorSelected.setAlpha(50)
        #connections
        self.selectionChanged.connect(self.updateCells)
        # lista datuma koji se trebaju drugacije obojati
        self.dateList = []
###############################################################################
    def paintCell(self, painter, rect, date):
        """
        overloadana metoda zaduzena za bojanje kalendara
        """
        #originalna metoda koja crta kalendar, overrideana
        QtGui.QCalendarWidget.paintCell(self, painter, rect, date)
        #override da se odredjeni datumi nacrtaju drugacije
        if date in self.dateList:
            painter.fillRect(rect, self.color)
        #override za boju trenutno selektiranog datuma
        izabrani = self.selectedDate()
        if date == izabrani:
            painter.fillRect(rect, self.colorSelected)
###############################################################################
    def selectDates(self, qdatesList):
        """
        Metoda preko koje se kalendaru mogu prosljediti datumi koje treba drugacije
        obojati.
        """
        self.dateList = qdatesList
        #updateCells, forsira ponovno iscrtavanje
        self.updateCells()
###############################################################################
###############################################################################
base4, form4 = uic.loadUiType('weblogger_izbornik.ui')
class WebloggerIzbornik(base4, form4):
    """
    inicijalizacija gui iz filea weblogger_izbornik.ui
    
    Klasa sluzi kao interface preko kojega korisnik moze odabrati:
    1. folder iz kojeg treba citati weblogger fileove
    2. stanicu od interesa
    3. datum od interesa
    4. kanal od interesa
    5. opcenite postavke grafa (opcije kako se prikazuje glavni kanal, pomocni
    grafovi...)
    """
    def __init__(self, parent=None):
        super(base4, self).__init__(parent)
        self.setupUi(self)
        
        #instanciranje kalendara
        self.kalendar = dateCalendar()
        #postavljanje kalendara u layout koji je pripremljen u ui fileu
        self.uiKalendarLayout.addWidget(self.kalendar)
        #disable navigacijske gumbe
        self.uiPrethodni.setDisabled(True)
        self.uiSljedeci.setDisabled(True)
        
        #memberi
        self.citac = None #instanca citaca weblogger fileova
        self.trenutniFolder = None #pamti trenutno aktivni folder
        self.trenutnaStanica = None #pamti trenutno aktivnu stanicu
        self.datumi = None #pamti koji se datumi trebaju drugacije obojati
        self.trenutniDatum = None #pamti koji je trenutno izabrani datum
        self.tmin = None #pamti "donji rub" slajsa frejma kojeg zahtjeva da se prikaze
        self.tmax = None #pamti "gornji rub" slajsa frejma kojeg zahtjeva da se prikaze
        self.__defaulti = None #dict postavki grafa
        self.kanali = []
        self.trenutniKanal = None #pamti zadnji glavni kanal
        
        #connections
        self.uiLoadFolder.clicked.connect(self.load_folder)
        self.uiStanicaCombo.currentIndexChanged.connect(self.combo_izbor_stanica)
        self.kalendar.selectionChanged.connect(self.kalendar_izbor_datuma)
        self.uiPrethodni.clicked.connect(self.klik_prethodni)
        self.uiSljedeci.clicked.connect(self.klik_sljedeci)
        self.uiOpcije.clicked.connect(self.promjeni_opcije_grafa)
        self.uiKanalCombo.currentIndexChanged.connect(self.izbor_kanala)
###############################################################################
    def set_defaulti(self, defaulti):
        """
        Metoda postavlja defaultni dict postavki grafova u privatni member.
        Potrebno zbog inicijalizacije postavki grafa
        -potencijalo prebaciti izbor glavnog kanala....
        """
        self.__defaulti = defaulti
###############################################################################        
    def get_defaulti(self):
        """
        Metoda vraca defaultni dict postavki grafova
        """
        return self.__defaulti
###############################################################################
    def postavi_kanale(self, data):
        """
        Metoda sluzi kao setter comboboxa sa dostupnim kanalima (self.uiKanalCombo)
        preko kojeg se bira glavni kanal.
        
        Metoda je "slot" preko kojeg kontolror vraca informaciju o dustupnim kanalima
        
        data je lista [trenutna satnica, tmin, tmax, [lista kanala]].
        tmin i tmax su rubovi slajsa koji definiraju datum, lista kanala sadrzi 
        samo one kanale koji imaju podatke (teoretski ima kanala gdje su sve
        koncentracije np.NaN ili -999, nih ignoriramo)
        """
        self.kanali = data[3]
        #blokiraj signale .. sprjecavanje okidanja izbora prije vremena
        self.uiKanalCombo.blockSignals(True)
        #zapamti odabir stanice kod promjene
        self.trenutniKanal = str(self.uiKanalCombo.currentText())
        #clear listu stanica, ne zelimo dodavati na vec postojecu
        self.uiKanalCombo.clear()
        #repopuliraj listu stanica, ponovno ispuni combobox sa novim stanicama
        self.uiKanalCombo.addItems(self.kanali)
        #probaj forsirati defaultni odabir (trebao bi biti jednak zadnjem izboru, ali moguce
        # je da se ucitavanjem preseta promjeni)
        defaultniKanal = self.__defaulti['glavniKanal']['midline']['kanal']
        
        if defaultniKanal in self.kanali:
            i = self.uiKanalCombo.findText(defaultniKanal)
            #odblokiraj signal za izbor
            self.uiKanalCombo.blockSignals(False)
            self.uiKanalCombo.setCurrentIndex(i)
        else:
            #ako iz nekog razloga nema stanice forsiraj prvi izbor
            #odblokiraj signal za izbor
            self.uiKanalCombo.blockSignals(False)
            self.uiKanalCombo.setCurrentIndex(0)
        #forsiraj izbor glavnog kanala preko metode izbor_kanala
        self.izbor_kanala()
###############################################################################
    def izbor_kanala(self):
        pass
        """
        Metodu (primarno) pokrece promjena indeksa u izborniku glavnog kanala
        
        Promjene glavnog kanala reflektira se u promjeni na odgovarajucem
        mjestu u self.__defaulti (postavlja se novi glavni kanal)
        
        Promjena u self.__defaulti se prenosi emitom kontroleru (koji je dalje
        zaduzen da informira panele sa grafovima).
        """
        #izabrani kanal postavi kao glavni
        gKanal = self.uiKanalCombo.currentText()
        if self.__defaulti != None:
            #promjeni self.__defaulti da reflektiraju novi izbor glavnog kanala
            self.__defaulti['glavniKanal']['midline']['kanal'] = gKanal
            self.__defaulti['glavniKanal']['validanOK']['kanal'] = gKanal
            self.__defaulti['glavniKanal']['validanNOK']['kanal'] = gKanal
            self.__defaulti['glavniKanal']['nevalidanOK']['kanal'] = gKanal
            self.__defaulti['glavniKanal']['nevalidanNOK']['kanal'] = gKanal
            self.__defaulti['glavniKanal']['fillsatni']['kanal'] = gKanal
            self.__defaulti['glavniKanal']['ekstremimin']['kanal'] = gKanal
            self.__defaulti['glavniKanal']['ekstremimax']['kanal'] = gKanal
            #emit promjene prema kontroloru        
            self.emit(QtCore.SIGNAL('wl_promjena_defaulta(PyQt_PyObject)'), self.__defaulti)
###############################################################################
    def promjeni_opcije_grafa(self):
        """
        Metoda se pokrece pritiskom na gumb "Postavke Grafa" (self.uiOpcije)
        
        Metoda poziva modalni dijalog za izbor postavki grafa.
        Ako se prihvati izbor, promjene se defaultne vrijednosti te se 
        informacija o promjeni javlja kontroloru.
        """
        #napravi kopiju dicta postavki grafa
        if self.__defaulti != None:
            postavke = copy.deepcopy(self.__defaulti)
            gKanal = self.__defaulti['glavniKanal']['validanOK']['kanal']
            dijalogDetalji = dijalog1.IzborStoSeCrta(kanali = self.kanali, glavniKanal = gKanal, info = postavke)
            if dijalogDetalji.exec_(): #ako je OK vraca 1, isto kao i True
                postavke = dijalogDetalji.dohvati_postavke()
                self.__defaulti = copy.deepcopy(postavke)
                
                #emit promjene prema kontroloru
                self.emit(QtCore.SIGNAL('wl_promjena_defaulta(PyQt_PyObject)'), self.__defaulti)
###############################################################################
    def load_folder(self):
        """
        Nakon pritiska na gumb za ucitavanje foldera...
        
        1. otvara se modalni dijalog za izbor foldera
        2. inicijalizira se citac
        3. path do foldera se postavlja na vidljivo mjesto u gui-u
        4. inicijalizirani citac se prosljedjuje kontroleru (kontroler ga dalje
        postavlja u dokument)
        """
        #dijalog za izbor foldera
        folderName = QtGui.QFileDialog.getExistingDirectory()
        folderName = str(folderName)
        #slucaj ako se stisne cancel... returns None, empty string
        #cilj je izbjegnuti krivu inicijalizaciju readera
        if folderName != '':
            self.citac = citac.WlReader(folderName)
            self.trenutniFolder = folderName
            #postavi ime foldera u gui textbox            
            self.uiCurrentFolder.setText(folderName)
            #emit inicijaliziranog citaca - kontroler ga hvata i prosljedjuje dokumentu
            self.emit(QtCore.SIGNAL('gui_set_citac(PyQt_PyObject)'), self.citac)
###############################################################################
    def set_stanice(self, stanice):
        """
        funkcija sluzi kao setter comboboxa sa stanicama
        
        Informacija o raspolozivim stanicama stize od kontrolora, te ova funkcija
        sluzi kao "slot" preko kojega kontrolor updatea combobox sa dostupnim
        stanicama.
        
        Klasa pamti koja je zadnja stanica bila izabrana te ce pokusati forsirati
        njen ponovni izbor (ako se nalazi na novom popisu)
        """
        #blokiraj signale .. sprjecavanje okidanja izbora prije vremena
        self.uiStanicaCombo.blockSignals(True)
        #zapamti odabir stanice kod promjene
        self.trenutnaStanica = str(self.uiStanicaCombo.currentText())
        #clear listu stanica, ne zelimo dodavati na vec postojecu
        self.uiStanicaCombo.clear()
        #repopuliraj listu stanica, ponovno ispuni combobox sa novim stanicama
        self.uiStanicaCombo.addItems(stanice)
        #probaj forsirati prethodni odabir
        if self.trenutnaStanica in stanice:
            i = self.uiStanicaCombo.findText(self.trenutnaStanica)
            #odblokiraj signal za izbor
            self.uiStanicaCombo.blockSignals(False)
            self.uiStanicaCombo.setCurrentIndex(i)
        else:
            #ako iz nekog razloga nema stanice forsiraj prvi izbor
            #odblokiraj signal za izbor
            self.uiStanicaCombo.blockSignals(False)
            self.uiStanicaCombo.setCurrentIndex(0)
###############################################################################
    def set_datumi(self, datumi):
        """
        funkcija sluzi kao setter dostupnih dana u kalendaru
        datumi su lista QtCore.QDate objekata
        
        Slicno kao i set_stanice, funkcija je "slot" preko kojeg kontrolor predaje
        informacije o raspolozivim datumima za izabranu stanicu. datumi su lista 
        datuma koji se trebaju drugacije obojati.
        """
        #zapamti zadnji datum
        self.trenutniDatum = self.kalendar.selectedDate()
        #postavi novi popis datuma
        self.datumi = sorted(datumi)
        #postavi boje dostupnih u kalendaru (radi ovoga smo subklasali QCalendar)
        self.kalendar.selectDates(self.datumi)
        #pokusaj forsirati zadnji izbor datuma
        self.kalendar_izbor_datuma()
###############################################################################
    def combo_izbor_stanica(self, indeks):
        """
        Funkcija koja se poziva svaki put kada se promjeni izbor stanice u comboboxu.
        
        Kontoloru se prosljedjuje informacija da je stanica promjenjena.
        Kontrolor je duzan vratiti informaciju o raspolozivim datumima - vidi set_datumi
        """
        self.trenutnaStanica = self.uiStanicaCombo.currentText()
        self.emit(QtCore.SIGNAL('gui_izbor_stanice(PyQt_PyObject)'), 
                  self.trenutnaStanica)
                  
###############################################################################
    def kalendar_izbor_datuma(self):
        """
        Funkcija se poziva svaki puta kada se izabrani datum promjeni
        (klik na kalendar ili programski)
        
        Funkcija provjerava da li treba disableati/enableati navigacijske gumbe
        (prethodni i sljedeci), te radi zahtjev koji prosljedjuje kontroloru.
        Zahtjev je lista [stanica, vrijeme od, vrijeme do]. Rubovi vremena su
        ukljuceni.
        
        Klasa ocekuje povratnu informaciju, popis kanala za tu stanicu i taj
        vremenski interval
        """
        #provjeri navigacijske gumbe
        self.test_nav_gumbe()
        #priprema i emit izbora datuma kontroleru
        if self.datumi != None:
            if self.trenutniDatum in self.datumi:
                dan = self.trenutniDatum.toPyDate()
                dan = pd.to_datetime(dan)
                #dan je timestamp "dan 00:00:00"
                self.tmin = dan + timedelta(minutes = 1)
                #tmiin je timestamp "dan 00:01:00"
                self.tmax = dan + timedelta(days = 1)
                #tmax je timestamp "dan+1 00:00:00"
                
                #pakiranje zahtjeva u listu
                data = [self.trenutnaStanica, self.tmin, self.tmax]
                #slanje zahtjeva
                self.emit(QtCore.SIGNAL('gui_vremenski_raspon(PyQt_PyObject)'), data)
###############################################################################
    def test_nav_gumbe(self):
        """
        -funkcija provjerava da li postoji prethodni/sljedeci dan
        -mjenja status gumba (enabled/disabled)
        """
        self.trenutniDatum = self.kalendar.selectedDate()
        if self.datumi != None:
            if self.trenutniDatum in self.datumi:
                pozicija = self.datumi.index(self.trenutniDatum)
                #gumb prethodni
                if pozicija == 0:
                    self.uiPrethodni.setDisabled(True)
                else:
                    self.uiPrethodni.setDisabled(False)
                #gumb sljedeci
                if (pozicija + 1) == (len(self.datumi)):
                    self.uiSljedeci.setDisabled(True)
                else:
                    self.uiSljedeci.setDisabled(False)
            else:
                #selected date is not valid, disable both buttons
                self.uiPrethodni.setDisabled(True)
                self.uiSljedeci.setDisabled(True)
###############################################################################
    def klik_prethodni(self):
        """
        Nakon klika na gumb prethodni
        
        Programersko prebacivanje datuma za jedno mjesto unazad od odabranog 
        datuma.
        """
        #trenutno izabrani datum
        datum = self.trenutniDatum
        #provjeri da li je datum u sortiranoj listi datuma
        if datum in self.datumi:
            #pronadji indeks datuma
            pozicija = self.datumi.index(datum)
            #pomakni ga za jedno mjesot unazad
            pozicija = pozicija - 1
            #pronadji koji je datum pod novim indeksom
            noviDatum = self.datumi[pozicija]
            self.trenutniDatum = noviDatum
            #postavi iduci datum u nizu
            self.kalendar.setSelectedDate(noviDatum)
            #setSelectedDate bi trebao pokrenuti signal selectionchanged...
###############################################################################
    def klik_sljedeci(self):
        """
        Nakon klika na gumb prethodni
        
        Programersko prebacivanje datuma za jedno mjesto unaprijed od odabranog
        datuma.
        """
        #isto kao i kod klik_prethodni, ali indeks povecavamo za 1
        datum = self.trenutniDatum
        if datum in self.datumi:
            pozicija = self.datumi.index(datum)
            pozicija = pozicija + 1
            noviDatum = self.datumi[pozicija]
            self.trenutniDatum = noviDatum            
            self.kalendar.setSelectedDate(noviDatum)
###############################################################################

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    x = WebloggerIzbornik()
    x.show()
    sys.exit(app.exec_())

