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
                
    def dodaj_frejmove(self, datum, frejmovi):
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
"""
Osnovni izgled dokumenta

Poslovi koje mora odraditi:
1. prihvat citaca
2. po potrebi, inicijalizacija objekta za pohranu podataka
3. informirati GUI- sto se moze ucitati, a sto je vec ucitano
4. uz pomoc trenutnog citaca, znati citati podatke koji nedostaju
5. validacija!
6. agregiranje podataka
7. rad sa grafovima (priprema podataka, update flagova, crtanje)
8. export podataka prema van u nekom smislenom izdanju (valjda preko nekog
objekta "pisac")

Primjer toka:
POSTAVLJANJE NOVOG CITACA U DOKUMENT
1. Gui dio aplikacije inicijalizira citac.
2. GUI proljedi citac dokumentu
3. Dokument iz citaca i svojih membera pokusava sastaviti sliku do kojih 
kombinacija stanica-datum moze doci. Idealno, razlikovati vec ucitane kombinacije
stanica-datum od onih koje se mogu ucitati. Na temelju tih podataka updateati
izbornike u GUI-u (combobox stanica i kalendar). Kada to odradi, čeka nove naredbe
od GUI-a. Na taj nacin izbjegavamo nesuvisle ulazne argumente jer smo sigurni do cega
dokument moze doci.

GUI ODABIR POSTOJECE KOMBINACIJE STANICE I DATUMA:
U gui dijelu, izbor stanice bi trebao updateati kalendar sa "valjanim" datumima.
Tek nakon izbora datuma (bilo direktni klik, ili gumbi sljedeci/prethodni) krece
priprema podataka za rad.

1. GUI javlja kombinaciju stanica-datum dokumentu. Dokument po potrebi instancira
DataStorage objekt. Ako objekt za tu stanicu vec postoji (ili ako je tek stvoren)
postavlja se kao aktivni objekt za rad.

2. Dokument provjerava da li je kombinacija medju vec ucitanim podatcima.
Takodjer provjerava da li citac moze doci do podataka.

Ako izbor nije prije ucitan, dokument koristi citac da ucita podatke, zatim ih
validira i nadodaje u objekt pod ucitaneFrejmove. Vraca nazad informaciju o svim
kanalima koje postoje za update GUI-a.

Ako je izbor prije ucitan, dokument vraca informaciju o postojecim kanalima za
update GUI-a.

GUI IZBOR NEKOG KANALA (CRTANJE SATNOG GRAFA):
Gui treba pamtiti zadnji kanal s kojim je radio. Prilikom updatea comboboxa za
kanal, treba ga pokusati postaviti kao aktivni kanal. Ako nema tog kanala, treba
dohvatiti prvi na raspolaganju. GUI-tada emitira podatak o izabranom kanalu
prema dokumentu.

1. Dokument treba dobiti sve informacije da moze pozvati dohvati_slice(kanal,granice)
metodu objekta koji drzi sve podatke
2. Dokument sprema slice u temp member sa frejmom minutnih podataka
3. Dokument agregira minutne podatke is temp slicea i sprema ih u drugi temp dataframe
4. Dokument salje naredbu za crtanje agregiranih podataka GUI-u


GUI CRTANJE MINUTNOG GRAFA:
odradjuje se izborom sa satnog grafa... emitira se signal koji sadrzi samo timestamp
odabranog satno agregiranog podatka.
1. Dokument direktno poziva metodu za crtanje minutnog grafa.
-dokument cuva referencu zadnje aktivnog slicea sa minutnim podatcima
-treba dohvatiti slice zadanog sata
-treba ga podjeliti u dva slicea (podatci koji su flagano OK i onih koji to nisu)
-emit tako dobivenih sliceovaprema GUI-u za crtanje minutnog grafa

GUI PROMJENA FLAGA:
Bez obzira o kojem se grafu radi postupak je identican.
1.Dokument zaprima zahtjev za promjenom flaga. Argumenti su novi flag, raspon za
kojeg flag treba promjeniti (min, max).
2.Na temp sliceu koji drzi minutne podatke promjeni se flag u zadanom rasponu (ili tocki)
3.Updatea se glavni frejm u dokumentu sa novim podatcima (u DataStorage objektu)
4.ponovno agregiramo temp frejm sa minutnim podatcima
5.prosljedimo naredbu za crtanje satnog grafa
6.prosljedimo naredbu za crtanje minutnog grafa
"""

class Dokument(QtGui.QWidget):
    """Sadrzi metode za prihvat i obradu podataka"""
    def __init__(self, parent = None):
        """Konstruktor klase.
        
        self.citac --> instanca klase trenutnog citaca podataka
        self.agregator --> instanca klase agregatora podataka
        self.dostupni --> dict {stanica:[lista datuma]} do kojih citac moze doci
        self.ucitani --> dict ucitanih datuma {stanica:[lista datuma]}
        self.spremljeni --> dict {stanica:DataStorage} , 
            tu se nalaze ucitani frejmovi za svaku stanicu.
        self.trenutnaStanica --> string, ime stanice, npr. 'Bilogora'
        self.trenutniKanal --> string, ime kanala, npr. '1-SO2-ug/m3'
        self.trenutniMinutniFrame --> slice datafrejma sa minutnim podatcima
        self.trenutniAgregiraniFrame --> slice datafrejma satno agregiranih podataka
        """
        QtGui.QWidget.__init__(self, parent)
        self.citac = None
        self.agregator = agregator.Agregator2()
        self.dostupni = {}
        self.ucitani = {}
        self.spremljeni = {}
        self.trenutniKanal = None
        self.trenutnaStanica = None
        self.trenutniMinutniFrame = None
        self.trenutniAgregiraniFrame = None
        
    def set_citac(self, reader):
        """Postavlja citac podataka u dokument.
        
        Metoda sluzi da kontroler postavi citac koji je preuzeo iz GUI-a.
        Citac mora sadrzavati metode za citanje podataka i lokaciju (ili 
        izvor) podataka.
        """
        #TODO!
        #1.provjeri tip readera prije inicijalizacije?
        self.citac = reader
        #obnovi dictionary dostupnih podataka
        self.dostupni = self.citac.vrati_dostupne_fileove()
        #dohvati popis svih ucitanih poadtaka (stanica-dan)
        for kljuc in self.spremljeni:
            #za svaku stanicu prepisi listu ucitanih datuma
            self.ucitani[kljuc] = self.spremljeni[kljuc].ucitaniDatumi
        
        #zanima nas popis svih raspolozivih stanica
        #sve koje su dostupne
        sveStanice = list(self.dostupni.keys())
        #sve koje su ucitane a da nisu na popisu dostupnih
        for stanica in list(self.ucitani.keys()):
            if stanica not in sveStanice:
                sveStanice.append(stanica)
        #TODO!  
        #EMIT - pazi sto salje i pod kojim nazivom
        #emit informacije o stanicama za GUI, abecedno sortirane
        self.emit(QtCore.SIGNAL('update_GUI_stanice(PyQt_PyObject)'),
                  sorted(sveStanice))
    
    
    def set_stanica(self, stanica):
        """
        Metoda mora napraviti sljedece:
        -zapamti izbor stanice
        -emitiraj listu dozvoljenih datuma za izbor stanice.
        """
        #zapamti izbor stanice
        self.trenutnaStanica = stanica
        #instanciraj DataStorage objekt ako vec ne postoji
        if stanica not in self.spremljeni.keys():
            self.spremljeni[stanica] = DataStorage(stanica)

        #svi datumi koje je moguce dohvatiti citacem -- lista datuma
        dostupniCitacu = self.dostupni[stanica]
        #vec ucitani datumi -- lista datuma
        ucitaniDatumi = self.ucitani[stanica]
        
        #TODO!
        #da se direktno asignat u listu, trenutno odvojeno radi preglednosti
        #EMIT - pazi sto salje i pod kojim nazivom
        #emit informacije o dostupnim datumima za stanicu za GUI
        self.emit(QtCore.SIGNAL('update_GUI_datumi(PyQt_PyObject)'), 
                  [dostupniCitacu, ucitaniDatumi])
        
    def pripremi_podatke(self, stanica, datum):
        """Priprema podataka za rad
        
        ulaz:
        stanica --> stanica od interesa
        datum --> datum od interesa
        
        Metoda zaprima zahtjev od GUI-a nakon izbora datuma (u ovom slucaju, 
        opcenito izbora vremenskog intervala). Metoda ucitava nove podatke po
        potrebi, i dodaje ih u DataStorage objekt za tu stanicu.
        
        GUI se treba pobrinuti za smislene zahtjeve!
        """
        self.trenutnaStanica = stanica
        if datum in self.ucitani[stanica]:
            #datum je predhodno ucitan za tu stanicu
            #dohvati sve kanale koji postoje u ucitanim frejmovima
            kanali = list(self.spremljeni[stanica].ucitaniFrejmovi.keys())
        else:
            #datum nije prethodno ucitan
            #iskoristi citac da procitas podatke za datum
            frejmovi = self.citac.citaj(stanica, datum)
            #TODO!
            #sredi validaciju ovdje, podaci trebaju biti auto-validirani
            #prije unosa u DataStorage objekt
            
            #dodaj frejmove na DataStorage objekt koristeci dodaj 
            self.spremljeni[stanica].dodaj_frejmove(datum, frejmovi)
            #ponovno dohvati popis ucitanih datuma
            self.ucitani[stanica] = self.spremljeni[stanica].ucitaniDatumi
            #dohvati sve kanale koji postoje u ucitanim frejmovima
            kanali = list(self.spremljeni[stanica].ucitaniFrejmovi.keys())
            #novi emit za update kalendara            
            #TODO!
            #EMIT - isti kao i kod self.set_stanica lista[dostupni, ucitani]
            self.emit(QtCore.SIGNAL('update_GUI_datumi(PyQt_PyObject)'), 
                      [self.dostupni[stanica], self.ucitani[stanica]])
        
        #TODO!
        #emit poopisa svih kanala u frejmovima
        #EMIT - pazi sto se salje i pod kojim imenom signala
        self.emit(QtCore.SIGNAL('update_GUI_kanali(PyQt_PyObject)'), 
                  kanali)
        
    def pripremi_slice(self, stanica, datum, kanal):
        """Priprema dnevnog slicea
        
        Metoda se poziva nakon izbora kanala u GUI-u
        -sprema se informacija o trenutnom kanalu
        -radi se slice podataka za odredjeni kanal i vremenski period i sprema se
        u self.trenutniMinutniFrejm
        -podatci se agregiraju i spremaju u self.trenutniAgregiraniFrejm
        -poziva se metoda za crtanje satno agregiranih podataka
        """
        self.trenutniKanal = kanal
        #TODO!
        #konvert datum u [tmin, tmax] timestampove radi sliceanja
        granice = None
        self.trenutniMinutniFrame = self.spremljeni[stanica].dohvati_slice(kanal, granice)
        #agregraj samo slice i spremi ga
        #pozovi metodu za crtanje satnog grafa
        