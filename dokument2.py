# -*- coding: utf-8 -*-
"""
Created on Tue Sep 16 11:18:49 2014

@author: vmilic

Redesign dokument klase prema naputcima
"""

import pandas as pd
import numpy as np

from PyQt4 import QtCore
from PyQt4 import QtGui

import re
import os
import citac
import agregator

class TMReader(object):
    """
    ideja za weblogger citac.. instancira se zajedno sa izvorom podataka, 
    tj. folderom.U objekt su dodane metode za pronalazak dostupnih podataka.
    """    
    def __init__(self, folderPath):
        #import citac
        #import os
        #import re
    
        #inicijalizacija specificnog citaca csv fileova
        self.wlReader = citac.WlReader()
        
        self.folder = folderPath
        self.dostupniFileovi = {}
        self.files = []
        self.files_C = []
        
        #pronalazak i spremanje svih dostupnih fileova
        self.get_files()
        
    def citaj(self, stanica, datum):
        """Procitaj sve fileove pod kljucevima stanica, datum iz dostupnih fileova
        te vrati ucitane frejmove.
        
        BITNA METODA ZA DOKUMENT!
        Dokument poziva ovu metodu kada pokusava ucitati podatke.
        Izlazna vrijednost ove metode su frejmovi, dictionary pandas datafrejmova
        za sve kanale. frejmovi = {'kanal':pd.DataFrame}
        """
        #dohvati listu fileova
        files = self.dostupniFileovi[stanica][datum]
        #na svaki element liste treba nadodati folder path
        for index in list(range(len(files))):
            files[index]=os.path.join(self.folder, files[index])
        
        return self.wlReader.citaj_listu(files)
    
    #pomocne metode, samo priprema dostupnih podataka za citac
    def get_files(self):
        """Metoda pronalazi sve valjane csv fileove u folderu
        
        Podatci o fileovima su spremljeni na sljedeci nacin:
        Nested dictionary, {stanica:datum}, {datum:[csv files]}
        """
        #pronadji sve fileove u folderu s kojim je objekt inicijaliziran
        allFiles = os.listdir(self.folder)
        #selektiraj sve fileove od interesa (one koje matchaju regexp)
        for file in allFiles:
            reMatch = re.match(r'.*-\d{8}.?.csv', file, re.IGNORECASE)
            if reMatch:
                if file.find(u'_C') == -1:
                    self.files.append(file)
                else:
                    self.files_C.append(file)
        #izrada kompozitnog dicta uz pomoc funkcije
        #lista fileova je npr. self.dictStanicaDatum[stanica][datum]
        self.dostupniFileovi = self.napravi_mapu(self.files)
    
    def napravi_mapu(self, data):
        """Pomocna funkcija za izradu mape dostupnih fileova        
        
        Napravi mapu (dictionary) od ulaznih podataka
        Izlaz je kompozitni dictionary:
        Vanjski kljuc je ime stanice sa kojim je povezan dict datuma.
        Svaki pojedini datum je kljuc pod kojim se nalazi lista svih fileova
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
        
    def parsiraj(self,item):
        """Pomocna funkcija za izradu mape dostupnih fileova
        
        Parser da dobijemo ime i datum uz filename. Razdvaja ime stanice od
        datuma da bi dobili kljuceve za dictionary pod kojima spremamo lokaciju
        filea.
        """
        item = item[0:len(item)-4]
        loc = item.find('-')
        stanica = item[:loc]
        if stanica.find('_C') != -1:
            stanica = stanica[0:len(stanica)-2]
        datum = item[loc+1:loc+9]
        return stanica, datum
        
        
#    def citaj(self, stanica, datum):
#        """
#        PRVA BITNA metoda koju zanima dokument
#        
#        Mora procitati SVE dostupne podatke za kombinaciju stanica/datum.
#        Mora sklopiti frejmove dict{kanal:pandas dataframe}
#        Izlaz su frejmovi
#        """
#        pass
#    
#    def vrati_dostupne(self):
#        """
#        DRUGA BITNA metoda koju zanima dokument
#        
#        Mora vratiti sve dostupne stanice koje moze procitati
#        Mora vratiti sve dostupne datume koje moze dohvatiti za stanicu
#        
#        izlaz je dict {stanica:[datum1, datum2, ...]}
#        """
#        pass
    
    

class Dokument(QtGui.QWidget):
    """Sadrzi metode za prihvat i obradu podataka"""
    def __init__(self, parent = None):
        """Konstruktor klase.
        
        self.citac --> instanca klase trenutnog citaca podataka
        self.agregator --> instanca klase agregatora podataka
        self.ucitani --> dict ucitanih datuma {'stanica':[datum1, datum2, ...]}
        self.spremljeni --> instanca DataStorage objekta, tu se nalaze ucitani frejmovi
        self.trenutnaStanica --> string, ime stanice, npr. 'Bilogora'
        self.trenutniKanal --> string, ime kanala, npr. '1-SO2-ug/m3'
        self.trenutniMinutniFrame --> slice datafrejma sa minutnim podatcima
        self.trenutniAgregiraniFrame --> slice datafrejma satno agregiranih podataka
        """
        QtGui.QWidget.__init__(self, parent)
        self.citac = None
        self.agregator = None
        self.ucitani = None
        self.spremljeni = None
        self.trenutniKanal = None
        self.trenutnaStanica = None
        self.trenutniMinutniFrame = None
        self.trenutniAgregiraniFrame = None
        
    def set_citac(self, reader):
        """postavlja citac podataka u dokument.
        
        Metoda sluzi da kontroler postavi citac koji je preuzeo iz GUI-a.
        Citac mora sadrzavati metode za citanje podataka i lokaciju podataka
        """
        #TODO!
        #1.provjeri tip readera prije inicijalizacije
        self.citac = reader
        #update dostupnih podataka (vec ucitani + oni koji se jos mogu ucitati)
        #emit prema GUI-u sa ciljem populiranja dostupnih stanica
        
    def get_dostupne_stanice(self):
        """Vraca popis svih stanica do kojih citac moze doci."""
        pass
        
    def get_dostupni_datumi(self, stanica):
        """Vraca popis svih raspolozivih datuma za stanicu"""
        pass
    
    def pripremi_podatke(self, stanica, kanal, tMin, tMax):
        """
        Priprema minutnih podataka za crtanje.
        
        Funkcija za zaprimanje zahtjeva za crtanjem (po potrebi ucitavanjem) 
        podataka. Gui preko kontrolera triggera ovu metodu koja pokrece tjek
        za crtanje i interakciju sa grafovima.
        
        ulaz:
        stanica --> postaja koja nas zanima
        kanal --> kanal od interesa
        tMin --> donja granica intervala (ukljucena)
        tMax --> gornja granica intervala (ukljucena)
        
        izlaz:
        1. cleara nacrtane grafove
        
        2. Pokusava doci do slicea minutnih podataka i postavlja nekoliko membera.
        Preciznije: self.trenutniMinutniFrejm, self.trenutniKanal, self.trenutnaStanica
        
        -stanica i kanal su jednostavni, samo direktni set membera
        
        -minutni podatci postupak:
        *napravi listu svih dana izmedju tMin i tMax
        *kreni po toj listi element po element i provjeri da li je stanica/datum vec ucitan
        *ako nije, ucitaj dodaj u self.ucitani, dodaj stanica/datum u listu ucitanih
        *na kraju iteracije dohvati minutni slice (kakav god da bio)
        
        3. pokusava nacrtati satni graf sa metodom self.nacrtaj_agregirane()
        """
        pass

    
    def nacrtaj_agregirane(self):
        """Priprema satnih i minutnih podataka za crtanje.
                
        izlaz:
        Metoda nema return, ali emitira signale i postavlja member 
        self.trenutniAgregiraniFrejm
        
        Pozivom na metodu UVIJEK re-agregiramo podatke za prikazivanje i spremamo
        ih u za to predvidjeni member.
        """
        #nesto u ovom stilu
        #self.trenutniAgregiraniFrejm = agregator.agregiraj(self.trenutniMinutniFrejm)
        #self emit zahtjev za crtanjem satno agregiranih podataka
        #provjeri da li je izlazni frame prazan, ovisno o tome emitiraj poruku da nema podataka
        pass
        
    def nacrtaj_minutne(self, vrijeme):
        """Priprema minutnih podataka za crtanje.
        
        ulaz:
        vrijeme --> vrijeme agregiranog sata za koje nas zanimaju minutni podatci
        
        Crtanje minutnih podataka je moguce iskljucivo preko GUI-a (graf satno 
        agregiranih podataka za neku stanicu-kanal-interval). To znaci da smo vec
        dohvatili potrebne minutne podatke u memberu self.trenutniMinutniFrame.
        Samo treba dohvatiti slice od [vrijeme-59 min : vrijeme]
        """
        #1.dohvati tocan slice minutnih frejmova
        #2.podjeli frame na dva dijela (flag>=0, flag< 0)
        #3.emitiraj dva frejma prema kontroleru
        #provjeri da li je izlazni frame prazan, ovisno o tome emitiraj poruku da nema podataka
        pass
        
    def promjena_flaga(self, flag, tMin, tMax):
        """Promjena vrijednosti flaga u memberu self.trenutniMinutniFrame.
        
        ulaz:
        flag --> int, nova vrijednost flaga, OK je svaki int >=0, ostalo se ignorira
        tMin, tMax --> granice intervala gdje trebamo promjeniti flag
        
        Postupak:
        -direktno promjeni flag unutar slicea minutnih podataka
        -reagregiraj podatke
        -nacrtaj satni
        -nacrtaj minutni
        """
        pass

