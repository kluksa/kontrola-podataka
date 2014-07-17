# -*- coding: utf-8 -*-
"""
Created on Wed Jul 16 13:22:35 2014

selektor fileova + navigacija

@author: velimir
"""

import sys
import os
import re
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
###############################################################################
    def selectDates(self, qdatesList):
        self.dateList = qdatesList
        #updateCells, forsira ponovno iscrtavanje
        self.updateCells()
###############################################################################
###############################################################################
base, form = uic.loadUiType('dock3.ui')
class WebloggerIzbornik(base, form):
    """
    NEDOVRSENO!    
    
    -inicijalizacija gui iz .ui filea
    -IZBOR KANALA (combobox) nije implementiran. U principu, kanale mogu dobiti
    tek nakon sto se file ucita.
    """
    def __init__(self, parent=None):
        super(base, self).__init__(parent)
        self.setupUi(self)
        
        #set QWidget (postavi subklasani kalendar)
        self.uiWidget = dateCalendar(self.uiWidget)
        #disable navigacijske gumbe
        self.uiPrethodni.setDisabled(True)
        self.uiSljedeci.setDisabled(True)
        
        
        #memberi
        self.folderLoaded = False
        self.trenutniFolder = None
        self.trenutneStanice = []
        self.trenutniDatumi = []
        self.files = []
        self.files_C = []
        self.dictStanicaDatum = {}
        self.uiFileList.clear()
        
        #connections
        self.uiLoadFolder.clicked.connect(self.load_folder)
        self.uiStanicaCombo.currentIndexChanged.connect(self.combo_izbor_stanica)
        self.uiWidget.clicked.connect(self.l_click_kalendar)
        self.uiWidget.activated.connect(self.dbl_click_kalendar)
        self.uiWidget.selectionChanged.connect(self.l_click_kalendar)
        self.uiFileList.itemDoubleClicked.connect(self.dbl_click_lista)
        self.uiPrethodni.clicked.connect(self.klik_prethodni)
        self.uiSljedeci.clicked.connect(self.klik_sljedeci)
###############################################################################        
    def load_folder(self):
        """
        Nakon pritiska na gumb za ucitavanje foldera...
        """
        #dijalog za izbor foldera
        folderName = QtGui.QFileDialog.getExistingDirectory()
        folderName = unicode(folderName)
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
            stanica = unicode(stanica)
            self.trenutniDatumi = sorted(list(self.dictStanicaDatum[stanica].keys()))
            markeri = []
            for datum in self.trenutniDatumi:
                #moram convertati string datume u QDate objekte
                markeri.append(QtCore.QDate.fromString(datum,'yyyyMMdd'))
            self.uiWidget.selectDates(markeri)
            self.uiWidget.emit(QtCore.SIGNAL('selectionChanged()'))
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
            stanica = unicode(stanica)
            datum = self.get_odabrani_datum()
            if datum in self.trenutniDatumi:
                self.uiFileList.addItems(self.dictStanicaDatum[stanica][datum])
###############################################################################
    def dbl_click_kalendar(self):
        """
        Dupli klik na datum u kalendaru
        -PLACEHOLDER, samo ispis na outputu
        """
        if self.folderLoaded:
            datum = self.get_odabrani_datum()
            if datum in self.trenutniDatumi:
                print('\ndoubleclick na klendaru, datum : {0}'.format(datum))
        #TODO:
        #neka akcija za doubleclick? ucitavanje zadnjeg filea u listi?
###############################################################################
    def dbl_click_lista(self,item):
        """
        Dupli klik na element liste
        -PLACEHOLDER, samo ispis na outputu
        """
        if self.folderLoaded:
            izbor = item.text()
            izbor = unicode(izbor)
            #spoji ime foldera sa imenom filea - konstrukcija full path
            izbor = os.path.join(self.trenutniFolder, izbor)
            print('\ndoubleclick na listi')
            print(izbor)
            #TODO:
            #napisi neki specificni emit zahtjeva
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
        datum = item[loc+1:]
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
        datum = self.uiWidget.selectedDate()
        datum = datum.toPyDate()
        datum = unicode(datum)
        datum = datum[0:4]+datum[5:7]+datum[8:10]
        return datum
###############################################################################
    def klik_prethodni(self):
        """
        Nakon klika na gumb prethodni
        -NEDOVRSENO
        """
        #TODO:
        #2. emit za ucitavanje novih podataka - KOJIH?
        datum = self.get_odabrani_datum()
        if datum in self.trenutniDatumi:
            pozicija = self.trenutniDatumi.index(datum)
            pozicija = pozicija - 1
            noviDatum = self.trenutniDatumi[pozicija]
            #cast back to QDate
            noviDatum = QtCore.QDate.fromString(noviDatum,'yyyyMMdd')
            self.uiWidget.setSelectedDate(noviDatum)
###############################################################################
    def klik_sljedeci(self):
        """
        Nakon klika na gumb prethodni
        -NEDOVRSENO
        """
        #TODO:
        #2. emit za ucitavanje novih podataka - KOJIH?
        datum = self.get_odabrani_datum()
        if datum in self.trenutniDatumi:
            pozicija = self.trenutniDatumi.index(datum)
            pozicija = pozicija + 1
            noviDatum = self.trenutniDatumi[pozicija]
            #cast back to QDate
            noviDatum = QtCore.QDate.fromString(noviDatum,'yyyyMMdd')
            self.uiWidget.setSelectedDate(noviDatum)
###############################################################################
        
        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    x = WebloggerIzbornik()
    x.show()
    sys.exit(app.exec_())

