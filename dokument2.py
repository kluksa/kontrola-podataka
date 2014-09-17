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

###############################################################################
###############################################################################
"""
PREBACI U DRUGI MODUL!

Primjer implementacije citaca. Ovisno o izvoru podataka GUI instancira citac i
postavlja ga u dokument.

Jedine metode koje zanimaju dokument, i koje moraju postojati su:

self.citaj(stanica, datum)
    --> vraca sve frejmove za stanicu i datum koje uspije ucitati
    --> frejmovi su dict {'kanal':dataframe sa podatcima}
    Cilj ove metode je ucitati podatke iz izvora na zahtjev dokumenta.

self.vrati_dostupne_fileove()
    --> vraca dict svih kombinacija stanica/datum koje se mogu ucitati
    Cilj ove metode je reci dokumentu sto se moze ucitati, Tada dokument moze
    dati smislene zahtjeve za citanjem i moze updateati GUI (populiranje izbornika...)
    
Po slicnom principu ce se raditi drugi tipovi citaca. Prilikom instanciranja
citacu se zada izvor podataka. Svaki konkretni citac ima svoj nacin kako
ce implementirati metode citaj(stanica,datum) i vrati_dostupne_fileove(), ali API
mora biti konzistentan.
"""
class TMReader(object):
    """
    ideja za weblogger citac.. instancira se zajedno sa izvorom podataka, 
    tj. folderom.U objekt su dodane metode za pronalazak dostupnih podataka.
    """    
    def __init__(self, folderPath):
        """inicijalizacija citaca ide zajedno sa inicijalizaciojm foldera.
        
        FolderPath treba biti tipa string i treba biti put do foldera u kojem
        se nalaze csv fileovi.
        """
        #TODO!
        #import potrebnih modula prilikom inicijalizacije???
        
        #import citac
        #import os
        #import re
    
        #inicijalizacija specificnog citaca csv fileova
        self.wlReader = citac.WlReader()
        
        self.folder = folderPath
        self.dostupniFileovi = {}
        self.files = []
        self.files_C = []
        
        #pronalazak i spremanje svih dostupnih fileova prilikom inicijalizacije
        #metoda populira dict self.dostupniFrejmovi iz kojeg se cita sa metodom
        #self.citaj(stanica, datum)
        self.get_files()
        
    def citaj(self, stanica, datum):
        """Procitaj sve fileove pod kljucevima stanica, datum iz dostupnih fileova
        te vrati ucitane frejmove.
        
        Ulazni podatci su stringovi.
        
        BITNA METODA ZA DOKUMENT!
        Dokument poziva ovu metodu kada pokusava ucitati podatke.
        Izlazna vrijednost ove metode su frejmovi, dictionary pandas datafrejmova
        za sve kanale. frejmovi = {'kanal':pd.DataFrame}
        """
        #dohvati listu fileova
        #TODO!
        #provjera ulaznih parametara? Potencijalni key error
        #dokument mora znati koji su dostupni fileovi da bi znao updateati gui,
        #pa se taj dio odgovornosti moze prebaciti na dokument
        files = self.dostupniFileovi[stanica][datum]
        #na svaki element liste treba nadodati folder path
        for index in list(range(len(files))):
            files[index]=os.path.join(self.folder, files[index])
        #iskoristi metodu specificnog citaca da procitas sve u listi i vratis frejmove
        return self.wlReader.citaj_listu(files)
        
    def vrati_dostupne_fileove(self):
        """vrati dict, za svaku stanicu, koji datumi postoje u folderu
        
        BITNA METODA ZA DOKUMENT!
        Ova metoda sluzi da dokumentu da informaciju do kojih sve fileova 
        citac moze doci. Bitno za update kontrole GUI-a.
        
        Izlaz je dict {stanica:[lista datuma]} -->bitno jer cemo na slican nacin
        pratiti sve fileove koji su ucitani i pohranjeni u dokumentu
        """
        izlaz ={}
        #dohvati sve stanice do kojih mozes doci
        stanice=list(self.dostupniFileovi.keys())
        #za svaku piojedinacnu stanicu, napravi listu svih datuma
        for stanica in stanice:
            izlaz[stanica]=list(self.dostupniFileovi[stanica].keys())
        #vrati rezultat
        return izlaz
    
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
        
###############################################################################
###############################################################################
"""
Definicija posebne klase koja sluzi za spremanje podataka u dukumentu.
Plan je da svaka stanica ima svoj objekt koji ce sadrzavati sve do tada ucitane
frejmove. Razlog izdvajanja u posebni objekt je radi lakseg spremanja rada.

npr. a=DataStorage('Bilogora')

Cilj je definirati membere i metode da se na jednom mjestu sredi konzistentno
updateanje frejmova prilikom ucitavanja novih podataka i dohvacanje vec ucitanih
"""    
class DataStorage(object):
    """
    Klasa za spremanje podataka sa JEDNE stanice.
    SPECIFICNU INSTANCU GENERIRA DOKUMENT!
    -kod instanciranja navedi ime postaje kao jedini argument tipa 'string'
    """
    def __init__(self, postaja):
        """Konstruktor
        
        self.nazivPostaje
            -definira kojoj stanici podatci pripadaju
        
        self.ucitaniFrejmovi
            -dictionary frejmova na koje se dodaju ucitani podatci
        
        self.ucitaniDatumi
            -lista koja prati koji su dani uneseni u ukupne frejmove
        """
        #inicijalizacija naziva postaje
        self.nazivPostaje = postaja
        #inicijalizacija praznog dicta gdje trebaju doci frejmovi
        self.ucitaniFrejmovi = {}
        #inicijalizacija ucitanih datuma (dana)
        self.ucitaniDatumi = []
        #inicijalizacija raspolozivih kanala
        self.kanali = []
                
    def dodaj_frejm(self, datum, frejmovi):
        """Dodaje frejmove na self.ucitaniFrejmovi
        
        ulaz:
        datum - string
        frejmovi - dict pandas datafrejmova {kanal:frejm minutnih podataka}
        
        BITNA METODA!
        Uz pomoc ove metode, dokument sprema ucitane podatke na jedinstveni
        dataframe.
        
        Metoda, za svaki kanal u frejmovi, radi update self.ucitaniFrejmovi.
        Nadodaje sve vrijednosti indeksa koji nedostaju, te zatim preslikava
        sve vrijednosti koje nisu NaN.
        
        Nakon updatea frejmova, appenda se datum na listu self.ucitaniDatumi.
        Ta lista je bitna jer preko nje Dokument moze pratiti ucitane dane
        """
        #za sve kanale u ulaznim frejmovima
        for kanal in frejmovi:
            #provjeri da li kanal postoji u self.ucitaniFrejmovi
            if kanal in self.ucitaniFrejmovi.keys():
                #ako kanal vec postoji, "pametno" spoji frejmove
                #1. dodaj sve indekse i vrijednosti koje nedostaju
                #ako ima preklapanja indeksa, ostaju stare vrijednosti
                self.ucitaniFrejmovi[kanal] = pd.merge(
                    self.ucitaniFrejmovi[kanal], 
                    frejmovi[kanal], 
                    how = 'outer', 
                    left_index = True, 
                    right_index = True, 
                    sort = True, 
                    on = [u'koncentracija', u'status', u'flag'])
                #2. updateaj frame sa svim vrijednostima koje nisu NaN
                #ova metoda osigurava ako ima preklapanja indeksa, da se
                #spreme novo ucitane vrijednosti
                self.ucitaniFrejmovi[kanal].update(frejmovi[kanal])
            else:
                #slucaj kada dodajemo novi kanal
                self.ucitaniFrejmovi[kanal] = frejmovi[kanal]
                #dodaj novi kanal u popis raspolozivih kanala
                self.kanali.append[kanal]
        
        #updateaj listu ucitanih datuma
        
        self.ucitaniDatumi.append(datum)
    
    def dohvati_slice(self, kanal, granice):
        """Metoda vraca slice frejmova unutar granica za odredjeni kanal
        
        BITNA METODA!
        Preko nje, dokument dohvaca dijelove slicea koje priprema za crtanje i
        obradu.

        ulaz:
        kanal - string, kljuc pod kojim se nalazi ciljani frejm
        granice - lista [tmin, tmax] koja definira rubove slicea
        
        NAPOMENA:
        -kanal mora biti valjan... inace, key error (odgovornost je na dokumentu
        da preda validan zahtjev, jer moze provjeriti da li je kanal OK)
        -tmin i tmax moraju biti pandas datetime timestampovi (tako su indeksi
        pohranjeni u datafrejmu)
        -tmin < tmax, inace izlaz je prazan dataframe
        
        izlaz: 
        dataframe minutnih podataka unutar zadanih parametara
        
        P.S. izbjegavam direktni slice sa df.loc[tmin:tmax] jer ako ne postoje
        indeksi tmin i tmax (situacija kada NEMA podataka), javlja se key error.
        Ovo je workaround koji radi
        """
        #kopiraj dataframe
        df = self.ucitaniFrejmovi[kanal].copy()
        #napravi slice svih indeksa vecih ili jednakih donjoj granici
        df = df[df.index >= granice[0]]
        #od ostatka frejma, napravi slice svih indeksa manjih ili jednakih gornjoj
        #granici
        df = df[df.index <= granice[1]]
        #vrati slice frejma        
        return df
    
    def update_frejm(self, kanal, frejm):
        """Update minutnih podataka samo jednog kanala
        
        BITNA METODA!
        Metoda sluzi dokumentu da updatea promjene flagova (bilo da ih inicira
        korisnik ili drugi dio programa). korisiti samo frejm kojeg si prije
        dohvatio metodom self.dohvati_slice()
        
        ulaz:
        kanal - string, kljuc pod kojim se nalazi ciljani frejm kojeg updateamo
        frejm - dataframe sa novim podatcima koje trebamo spremiti, u biti to je
        slajs frejma kojeg smo izvukli metodom self.dohvati_slice()
        
        izlaz:
        update self.ucitaniFrejmovi[kanal]
        """
        #direktni update, jer baratamo direktnim sliceom kojeg smo dohvatili
        self.ucitaniFrejmovi[kanal].update(frejm)
###############################################################################
###############################################################################
    

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

