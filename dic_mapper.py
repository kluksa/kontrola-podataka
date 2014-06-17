# -*- coding: utf-8 -*-
"""
Created on Mon Jun  9 08:48:26 2014

@author: velimir

Mapiranje zadanog direktorija.

-ubacio izbornik u zasebnu klasu.
-umjesto liste sa svim fileovima, sredio sam izbor na drugi nacin:
    1. folder u kojem se naleze csv fileovi se moze dinamicki promjeniti
    2. nakon odabira foldera, combobox sa stanicama se napuni
    3. postavljen je kalendar widget za spretniji izbor datuma
    4. klikom na datum u kalendaru, klasa dohvaća sve csv fileove koji zadovoljavaju
    format (ime stanice)-(datum YYYYMMDD)(neka oznaka).csv i sprema ih u listu
    5. ako nema niti jednog csv filea, napisati ce se odgovarajuca poruka
- ideja je olaksati izbor csv fileova kada ih se nakupi jako puno u folderu

P.S. ako je ovaj pristup ok, krecem na promjenu citaca (treba ga modificirati
da kao ulaz uzima listu)
"""

import sys
import os

from PyQt4 import QtGui,QtCore

class FileSelektor(QtGui.QWidget):
    """
    Klasa, za zadanu mapu, pronalazi sve relevantne csv fileove i slaze ih na
    lagano dostupan nacin u mape (dictionary), te uz pomoc comboboxa i calendar
    widgeta omogucava lak pristup odredjenom fileu
    """
    def __init__(self,parent=None):
        QtGui.QWidget.__init__(self,parent)
        
        self.setWindowTitle('Odabir datoteka')
        
        #neki memberi
        self.loaded=False
        self.trenutniFolder=None
        self.stanice={}
        self.stanice_C={}
        
        self.gumb=QtGui.QPushButton('Potrvrdi izbor mape')
        self.path=QtGui.QLineEdit()
        self.comboStanica=QtGui.QComboBox()
        self.kalendar=QtGui.QCalendarWidget()        
        self.label=QtGui.QLabel('Zadaj mapu')
        
        basicLayout=QtGui.QVBoxLayout(self)
        basicLayout.addWidget(self.path)
        basicLayout.addWidget(self.gumb)
        basicLayout.addWidget(self.comboStanica)
        basicLayout.addWidget(self.kalendar)
        basicLayout.addWidget(self.label)
        
        self.connect(self.gumb,
                     QtCore.SIGNAL('clicked()'),
                     self.load_folder)
        
        self.kalendar.clicked[QtCore.QDate].connect(self.izbor_datuma)
                     
###############################################################################
    def izbor_datuma(self,datum):
        #pobrinuti se da je datum u strig formnatu YYYYMMDD
        x=datum.toPyDate()
        x=str(x)
        x=x[0:4]+x[5:7]+x[8:10]
        stanica=self.comboStanica.currentText()
        if self.loaded:
            #tu bi trebao biti emit sa podatcima ako je sve u redu.
            if x in self.stanice[stanica]:
                lista=self.stanice[stanica][x]
                self.label.setText(str(lista))
                print(lista)
                self.emit(QtCore.SIGNAL('read_lista(PyQt_PyObject)'),lista)
            else:
                self.label.setText('nema podataka za zadani dan')
                print('nema podataka za zadani dan')
###############################################################################
    def load_folder(self):
        self.comboStanica.clear()
        if self.path.text() is None:
            self.label.setText('unesi neki path foldera u gornji line edit')
        else:
            self.loaded=True
            self.trenutniFolder=self.path.text()
            #utrpaj funkciju koja radi dictionary strukturu. stanica, datum
            raw=self.find_all_csv(self.path.text())
            if raw=='dir ne postoji':
                self.label.setText('dir ne postoji, unesi valjani dir')
            else:
                data,data_C=self.separacija(raw)
                self.stanice=self.napravi_mapu(data)
                self.stanice_C=self.napravi_mapu(data_C)
                #populiraj combobox sa stanicama
                self.comboStanica.addItems(list(self.stanice.keys()))
                
###############################################################################
    def find_all_csv(self,direktorij):
        """
        Primarni filter za .csv fileove, ujedino provjera za postojanje mape
        """
        #provjera postojanja direktorija
        if os.path.isdir(direktorij):
            lista=[]
            for file in os.listdir(direktorij):
                if str(file).find('.csv')!=-1:
                    #svi u listi su castani u string
                    lista.append(str(file))
            return lista
        else:
            return 'dir ne postoji'
###############################################################################
    def separacija(self,listaSvih):
        """
        Odvajanje fileova na dvije liste (sa _C i bez _C u imenu)
        """
        data=[]
        data_C=[]
        for item in listaSvih:
            if item.find('_C')==-1:
                data.append(item)
            else:
                data_C.append(item)        
        return data,data_C
###############################################################################
    def spoji_file(self,file):
        """
        spaja ime mape sa imenom filea
        """
        return str(os.path.join(self.trenutniFolder,file))
###############################################################################
    def napravi_mapu(self,data):
        """
        od ulaznih podataka napravi mapu.
        """
        
        stanice={}
    
        for file in data:
            stanica,datum=self.parsiraj(file)

            if stanica not in stanice:
                stanice[stanica]={datum:[self.spoji_file(file)]}
            else:
                if datum not in stanice[stanica]:
                    stanice[stanica].update({datum:[self.spoji_file(file)]})
                else:
                    stanice[stanica][datum].append(self.spoji_file(file))
        
        return stanice
###############################################################################
    def parsiraj(self,item):
        """
        Parser da dobijemo ime i datum uz filename
        """
        item=item[0:len(item)-4]
        loc=item.find('-')
        stanica=item[:loc]
        if stanica.find('_C')!=-1:
            stanica=stanica[0:len(stanica)-2]
        datum=item[loc+1:]
        return stanica,datum
###############################################################################
    
if __name__=='__main__':
    aplikacija = QtGui.QApplication(sys.argv)
    glavni = FileSelektor()
    glavni.show()
    sys.exit(aplikacija.exec_())