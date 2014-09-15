# -*- coding: utf-8 -*-
"""
Created on Wed Jul 16 13:22:35 2014

selektor fileova + navigacija

@author: velimir
"""

import sys
import os
import re
import citac
from PyQt4 import QtCore, QtGui, uic

###############################################################################
###############################################################################
class dateCalendar(QtGui.QCalendarWidget):
    def __init__(self, parent = None):
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
        self.dateList = qdatesList
        #updateCells, forsira ponovno iscrtavanje
        self.updateCells()
###############################################################################
###############################################################################
base, form = uic.loadUiType('weblogger_izbornik.ui')
class WebloggerIzbornik(base, form):
    """
    inicijalizacija gui iz filea weblogger_izbornik.ui
    
    metode koje se smiju pozivati izvana:
    -self.set_mjerenje(string)
    -self.set_mjerenja(lista stringova)
    -self.get_mjerenje(string) ???
    
    metoda za komuniciranje sa vanjskim modulima
    -self.open_file() ---> 'ucitani_frejmovi(PyQt_PyObject)'
    -self.open_file_list() ---> 'ucitani_frejmovi(PyQt_PyObject)'
    -self.promjena_mjerenja() ---> 'promjena_mjerenja(PyQt_PyObject)'
    
    """
    def __init__(self, parent=None):
        super(base, self).__init__(parent)
        self.setupUi(self)
        
        #set QWidget (postavi subklasani kalendar)
        self.kalendar = dateCalendar()        
        #self.uiWidget = dateCalendar(self.uiWidget)
        self.uiKalendarLayout.addWidget(self.kalendar)
        #disable navigacijske gumbe
        self.uiPrethodni.setDisabled(True)
        self.uiSljedeci.setDisabled(True)
        
        #inicijalizacija citaca
        self.wlreader = citac.WlReader()
        self.frejmovi = None
                
        #memberi
        self.zadnjeMjerenje = None
        self.folderLoaded = False
        self.trenutniFolder = None
        self.trenutneStanice = []
        self.trenutniDatumi = []
        self.files = []
        self.files_C = []
        self.dictStanicaDatum = {}
        self.uiFileList.clear()
        self.ucitani = []
        
        #connections
        self.uiLoadFolder.clicked.connect(self.load_folder)
        self.uiStanicaCombo.currentIndexChanged.connect(self.combo_izbor_stanica)
        self.kalendar.clicked.connect(self.l_click_kalendar)
        self.kalendar.activated.connect(self.dbl_click_kalendar)
        self.kalendar.selectionChanged.connect(self.l_click_kalendar)
        self.uiFileList.itemDoubleClicked.connect(self.dbl_click_lista)
        self.uiPrethodni.clicked.connect(self.klik_prethodni)
        self.uiSljedeci.clicked.connect(self.klik_sljedeci)
        self.uiKanalCombo.currentIndexChanged.connect(self.promjena_mjerenja)
###############################################################################        
    def load_folder(self):
        """
        Nakon pritiska na gumb za ucitavanje foldera...
        """
        #dijalog za izbor foldera
        folderName = QtGui.QFileDialog.getExistingDirectory()
        folderName = str(folderName)
        #slucaj ako se stisne cancel... returns None, empty string
        #ideja je sacuvati prethodne postavke
        if folderName != '':
            self.folderLoaded = True
            self.trenutniFolder = folderName
            self.uiCurrentFolder.setText(folderName)
            self.get_files(folderName)
###############################################################################
    def get_files(self,folder):
        """
        Pronalazak i grupiranje svih bitnih fileova
        """
        #reset membera
        self.trenutneStanice.clear()
        self.files.clear()
        self.files_C.clear()
        self.dictStanicaDatum = {}
        #reset ui
        self.uiStanicaCombo.clear()
        
        allFiles = os.listdir(folder)
        #u folderu nalazi sve file koje matchaju regex
        for file in allFiles:
            reMatch = re.match(r'.*-\d{8}.?.csv', file, re.IGNORECASE)
            if reMatch:
                if file.find(u'_C') == -1:
                    self.files.append(file)
                else:
                    self.files_C.append(file)
        #izrada kompozitnog dicta kljuc1=stanica, kljuc2=datum
        #lista fileova je npr. self.dictStanicaDatum[stanica][datum]
        self.dictStanicaDatum = self.napravi_mapu(self.files)

        #sort kljuceva prije dodavanja u listu stanica
        self.trenutneStanice = sorted(self.dictStanicaDatum.keys())
        self.uiStanicaCombo.addItems(self.trenutneStanice)
###############################################################################
    def combo_izbor_stanica(self):
        """
        Promjena vrijednosti na comboboxu kod stanica
        """
        self.uiFileList.clear()
        if self.folderLoaded:
            stanica = self.uiStanicaCombo.currentText()
            stanica = str(stanica)
            self.trenutniDatumi = sorted(list(self.dictStanicaDatum[stanica].keys()))
            markeri = []
            for datum in self.trenutniDatumi:
                #moram convertati string datume u QDate objekte
                markeri.append(QtCore.QDate.fromString(datum,'yyyyMMdd'))
            self.kalendar.selectDates(markeri)
            self.kalendar.emit(QtCore.SIGNAL('selectionChanged()'))
###############################################################################
    def l_click_kalendar(self):
        """
        Odabir na kalendaru (left click misem) puni listu sa imenima
        fileova koji zadovoljavaju:
        -imaju izabranu stanicu u imenu
        -imaju izabran datum u imenu
        -nemaju _C ispred datuma
        """
        self.test_nav_gumbe()
        self.uiFileList.clear()
        if self.folderLoaded:
            stanica = self.uiStanicaCombo.currentText()
            stanica = str(stanica)
            datum = self.get_odabrani_datum()
            if datum in self.trenutniDatumi:
                self.uiFileList.addItems(self.dictStanicaDatum[stanica][datum])
###############################################################################
    def dbl_click_kalendar(self):
        """
        Dupli klik na datum u kalendaru
        """
        lista = []
        if self.folderLoaded:
            datum = self.get_odabrani_datum()
            if datum in self.trenutniDatumi:
                #caka... treba naljepiti path na svaki element liste...
                for indeks in range(self.uiFileList.count()):
                    imeFilea = self.uiFileList.item(indeks).text()
                    fullpath = os.path.join(self.trenutniFolder, imeFilea)
                    lista.append(fullpath)
                #emitiranje liste fileova
                self.open_file_list(lista)
###############################################################################
    def dbl_click_lista(self,item):
        """
        Dupli klik na element liste
        """
        if self.folderLoaded:
            izbor = item.text()
            izbor = str(izbor)
            #spoji ime foldera sa imenom filea - konstrukcija full path
            izbor = os.path.join(self.trenutniFolder, izbor)
            #emitiranje filea            
            self.open_file(izbor)
###############################################################################
    def parsiraj(self,item):
        """
        Parser da dobijemo ime i datum uz filename
        """
        item = item[0:len(item)-4]
        loc = item.find('-')
        stanica = item[:loc]
        if stanica.find('_C') != -1:
            stanica = stanica[0:len(stanica)-2]
        datum = item[loc+1:loc+9]
        return stanica, datum  
###############################################################################
    def napravi_mapu(self,data):
        """
        Napravi mapu (dictionary) od ulaznih podataka
        """
        stanice={}
    
        for file in data:
            stanica,datum=self.parsiraj(file)

            if stanica not in stanice:
                stanice[stanica]={datum:[file]}
            else:
                if datum not in stanice[stanica]:
                    stanice[stanica].update({datum:[file]})
                else:
                    stanice[stanica][datum].append(file)
        
        return stanice
###############################################################################
    def test_nav_gumbe(self):
        """
        -funkcija provjerava da li postoji prethodni/sljedeci dan
        -mjenja status gumba (enabled/disabled)
        """
        datum = self.get_odabrani_datum()
        if datum in self.trenutniDatumi:
            pozicija = self.trenutniDatumi.index(datum)
            #gumb prethodni
            if pozicija == 0:
                self.uiPrethodni.setDisabled(True)
            else:
                self.uiPrethodni.setDisabled(False)
            #gumb sljedeci
            if (pozicija + 1) == (len(self.trenutniDatumi)):
                self.uiSljedeci.setDisabled(True)
            else:
                self.uiSljedeci.setDisabled(False)
        else:
            #selected date is not valid, disable both buttons
            self.uiPrethodni.setDisabled(True)
            self.uiSljedeci.setDisabled(True)
###############################################################################
    def get_odabrani_datum(self):
        datum = self.kalendar.selectedDate()
        datum = datum.toPyDate()
        datum = str(datum)
        datum = datum[0:4]+datum[5:7]+datum[8:10]
        return datum
###############################################################################
    def klik_prethodni(self):
        """
        Nakon klika na gumb prethodni
        """
        datum = self.get_odabrani_datum()
        if datum in self.trenutniDatumi:
            pozicija = self.trenutniDatumi.index(datum)
            pozicija = pozicija - 1
            noviDatum = self.trenutniDatumi[pozicija]
            #cast back to QDate
            noviDatum = QtCore.QDate.fromString(noviDatum,'yyyyMMdd')
            self.kalendar.setSelectedDate(noviDatum)
            
            #tretiraj kao dupli klik na kalendaru (ucitavanje svih sa liste)
            self.dbl_click_kalendar()
###############################################################################
    def klik_sljedeci(self):
        """
        Nakon klika na gumb prethodni
        """
        datum = self.get_odabrani_datum()
        if datum in self.trenutniDatumi:
            pozicija = self.trenutniDatumi.index(datum)
            pozicija = pozicija + 1
            noviDatum = self.trenutniDatumi[pozicija]
            #cast back to QDate
            noviDatum = QtCore.QDate.fromString(noviDatum,'yyyyMMdd')
            self.kalendar.setSelectedDate(noviDatum)
            
            #tretiraj kao dupli klik na kalendaru (ucitavanje svih sa liste)
            self.dbl_click_kalendar()
###############################################################################
    def set_mjerenja(self, mjerenja):
        """
        Setter za populiranje comboboxa sa svim dostupnim kanalima nakon sto se 
        otvori neki file.
        """
        lista = sorted(mjerenja)
        self.uiKanalCombo.clear()
        #privremeno blokiraj sve signale uiKanalCombo widgeta
        self.uiKanalCombo.blockSignals(True)
        self.uiKanalCombo.addItems(lista)
        #provjeri da li ima prije ucitanih signala, i da li je u trenutnoj listi
        if self.zadnjeMjerenje != None:
            if self.zadnjeMjerenje in lista:
                #odblokiraj signal ranije da prodje signal currentIndexChanged (trigger izbora kanala)
                self.uiKanalCombo.blockSignals(False)
                indeks = self.uiKanalCombo.findText(self.zadnjeMjerenje)
                self.uiKanalCombo.setCurrentIndex(indeks)
        #odblokiraj sve signale uiKanalCombo widgeta
        self.uiKanalCombo.blockSignals(False)
###############################################################################
    def set_mjerenje(self, mjerenje):
        """
        Setter za odabir unutar comboboxa.
        """
        #test, da li mjerenje postoji u comboboxu
        indeks = self.uiKanalCombo.findText(mjerenje)
        if indeks != -1:
            self.zadnjeMjerenje = mjerenje
            self.uiKanalCombo.setCurrentIndex(indeks)      
###############################################################################
    def get_mjerenje(self):
        """
        getter za trenutno odabrano mjerenje ???        
        NOT IMPLEMENTED
        """
        return
###############################################################################
    def open_file(self, file):
        """
        citaj file i  emitiraj frejmove
        """        
        if file not in self.ucitani:
            self.frejmovi = self.wlreader.citaj(file)
            #zapamti sto si ucitao        
            self.ucitani.append(file)
            #TODO!            
            #emit prema dokumentu da merga ucitane frejmove
            #emit za postavljanje izbora kanala (moram ih preuzeti iz dokumenta)
            #na isti nacin sredi ucitavanje liste fileova
        else:
            pass
            #samo request za update liste kanala
            #pokusaj zapamtiti koji je kanal bio prije i forsiraj njegov izbor
        
        if self.frejmovi != None:
            
            self.emit(QtCore.SIGNAL('ucitani_frejmovi(PyQt_PyObject)'), self.frejmovi)
#            print('\nopen_file, kljucevi frejmova:')
#            print(self.frejmovi.keys())
            #set sortiranu listu kanala
            kanali = sorted(list(self.frejmovi.keys()))
            self.set_mjerenja(kanali)
        else:
            message = 'Pogreska kod ucitavanja. Krivi tip ili struktura csv datoteke'
            self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'), message)
###############################################################################
    def open_file_list(self, lista):
        """
        citaj iz liste fileova i emitiraj frejmove
        """
        self.frejmovi = self.wlreader.citaj_listu(lista)

        #zapamti sto si ucitao        
        #for file in lista:
        #    self.ucitani.append(file)
            
        if self.frejmovi != None:
            self.emit(QtCore.SIGNAL('ucitani_frejmovi(PyQt_PyObject)'), self.frejmovi)
#            print('\nopen_file_list, kljucevi frejmova:')
#            print(self.frejmovi.keys())
            #set sortiranu listu kanala
            kanali = sorted(list(self.frejmovi.keys()))
            self.set_mjerenja(kanali)
        else:
            message = 'Pogreska kod ucitavanja. Krivi tip ili struktura csv datoteka'
            self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'), message)
###############################################################################
    def promjena_mjerenja(self, mjerenje):
        """
        emit signal sa novim izborom mjerenja (kanala)
        """
        mjerenje = self.uiKanalCombo.itemText(mjerenje)
        if self.uiKanalCombo.findText(mjerenje) != -1:
            self.zadnjeMjerenje = mjerenje
            self.emit(QtCore.SIGNAL('promjena_mjerenja(PyQt_PyObject)'), mjerenje)
#            print('\npromjena_mjerenja :{0}'.format(mjerenje))
###############################################################################
###############################################################################
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    x = WebloggerIzbornik()
    x.show()
    sys.exit(app.exec_())

