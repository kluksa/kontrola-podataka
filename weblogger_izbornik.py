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
from datetime import timedelta
import pandas as pd
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
    
    ova klasa sluzi sa skupljanje dijela kontorlnih elemenata aplikacije
    koji se odnose na ucitavanje i dohvat podataka iz csv weblogger fileova    
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
        
        #memberi
        self.citac = None
        self.trenutniFolder = None
        self.trenutnaStanica = None
        self.datumi = None
        self.trenutniDatum = None
        self.tmin = None
        self.tmax = None
        
        #TODO!
        #pola naredbi ispod nece trebati ili je krivo
        
        #connections
        self.uiLoadFolder.clicked.connect(self.load_folder)
        self.uiStanicaCombo.currentIndexChanged.connect(self.combo_izbor_stanica)
        self.kalendar.selectionChanged.connect(self.kalendar_izbor_datuma)
        self.uiPrethodni.clicked.connect(self.klik_prethodni)
        self.uiSljedeci.clicked.connect(self.klik_sljedeci)
###############################################################################        
    def load_folder(self):
        """
        Nakon pritiska na gumb za ucitavanje foldera...
        inicijalizacija citaca, prosljedjivanje citaca dalje
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
        """
        #blokiraj signale .. sprjecavanje okidanja izbora prije vremena
        self.uiStanicaCombo.blockSignals(True)
        #zapamti odabir stanice kod promjene
        self.trenutnaStanica = str(self.uiStanicaCombo.currentText())
        #clear listu stanica        
        self.uiStanicaCombo.clear()
        #repopuliraj listu stanica
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
        """
        
        #zapamti zadnji datum
        self.trenutniDatum = self.kalendar.selectedDate()
        #postavi novi popis datuma
        self.datumi = sorted(datumi)
        #postavi boje dostupnih u kalendaru
        self.kalendar.selectDates(self.datumi)
        #pokusaj forsirati zadnji izbor datuma
        self.kalendar_izbor_datuma()
###############################################################################
    def combo_izbor_stanica(self, indeks):
        """
        Funkcija koja se poziva svaki put kada se promjeni izbor stanice u gui-u.
        
        Upit prema kontroleru da dohvati datume koji su na raspolaganju
        """
        self.trenutnaStanica = self.uiStanicaCombo.currentText()
        self.emit(QtCore.SIGNAL('gui_izbor_stanice(PyQt_PyObject)'), 
                  self.trenutnaStanica)
                  
###############################################################################
    def kalendar_izbor_datuma(self):
        """
        Funkcija se poziva svaki puta kada se izabrani datum promjeni
        (klik na kalendar ili programski)
        
        Upit prema kontroleru za dostupne kanale
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
                data = [self.trenutnaStanica, self.tmin, self.tmax]
                #TODO!
                #treba clearati minutni graf OVDJE, kada se prebacuju datumi, minutni bi trebao biti prazan
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
        """
        datum = self.trenutniDatum
        if datum in self.datumi:
            pozicija = self.datumi.index(datum)
            pozicija = pozicija - 1
            noviDatum = self.datumi[pozicija]
            self.trenutniDatum = noviDatum
            #postavi iduci datum u nizu
            self.kalendar.setSelectedDate(noviDatum)
            #setSelectedDate bi trebao pokrenuti signal selectionchanged...
###############################################################################
    def klik_sljedeci(self):
        """
        Nakon klika na gumb prethodni
        """
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

