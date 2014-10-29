# -*- coding: utf-8 -*-
'''
Created on Apr 21, 2014

@author: kraljevic
'''
import pandas as pd
import numpy as np

from PyQt4 import QtGui,QtCore

import agregator

class Dokument(QtGui.QWidget):
    """Sprema ucitane podatke, obradjuje ih te odgovara na zahtjeve kontrolora
    
    -sublkasa QWidgeta zbog emit metode
    
    INTERFACE:
    metode koje se "smiju" pozivati iz drugih modula:
    -self.dohvati_dostupne_podatke()
    -self.set_citac(citac)
    -self.dohvati_podatke(stanica, tMin, tMax)
    -self.update_frejm(stanica, kanal)
    """
###############################################################################
    def __init__(self,parent=None):
        """Konstruktor klase
        
        #struktura koja drzi podatke:
            -nested dictionary u self.stanice
            -prvi kljuc je 'stanica', drugi kljuc je 'kanal'
            self.__stanice --> mapa {'stanica':frejmovi}
                frejmovi --> mapa {'kanal':pandas dataframe}
                pandas dataframe --> pd.DataFrame objekt
                    index:datetime, columns:'koncentracija', 'status', 'flag'
        
        #memberi za pracenje stanja:
        self.__aktivnaStanica --> kljuc stanice
        self.__trenutniMinutniSlice --> dict minutnih podataka za stanicu
        self.__trenutniAgregiraniSlice -->dict satno agregiranih podataka za stanicu
        self.__tMin -->donja granica slicea minutnih podataka, pandas datetime objekt
        self.__tMax -->gornja granica slicea satnih podataka, pandas datetime objekt
        self.__dostupniPodaci --> dictionary {'stanica':[lista datuma]} koji se mogu ucitati
        self.__ucitaniPodaci -->dictionary {'stanica':[lista datuma]} koji su vec ucitani
        
        #memberi za obradu podataka
        self.__agregator --> instanca objekta za satno agregiranje minutnih podataka
        self.__validator --> instanca objekta za automatsku validaciju podataka
        self.__citac --> instanca objekta za pristup podatcima iz nekog izvora
        
        #bitne interface metode
        set_citac(self, objekt)
            -postavlja citac u dokument
            -upit prema citacu do kojih podataka moze doci (stanica/datum)
        
        dohvati_podatke(self, stanica, tMin, tMax)
            -vraca frejmove podataka i agregiranih podataka
            -po potrebi pokusava sa citacem ucitati podatke ako nedostaju
            
        dohvati_dostupne_podatke(self)
            -vraca do cega sve dokument moze doci
            -sluzi za populiranje kontrolnih elemenata
        """
        QtGui.QWidget.__init__(self,parent)
        self.__stanice = {}
        self.__aktivnaStanica = None
        self.__trenutniMinutniSlice = {}
        self.__trenutniAgregiraniSlice = {}
        self.__tMin = None
        self.__tMax = None
        self.__dostupniPodaci = {}
        self.__ucitaniPodaci ={}
        #dozvoliti mjenjanje agregatora i/ili validatora nekom setter metodom???
        self.__agregator = agregator.Agregator()
        self.__validator = None
        self.__citac = None
###############################################################################
    def dohvati_dostupne_podatke(self):
        """Vrati informaciju do kojih podataka dokument moze doci
        
        Sklapa sliku iz ucitanih i dostupnih podataka o dostupnim kombinacijama
        stanice i datuma.
        
        NE DAJE INFORMACIJE O KANALIMA!
        """
        data = {}
        #sklopi dict stanica:lista datuma
        for stanica in self.__dostupniPodaci:
            data[stanica] = list(self.__dostupniPodaci[stanica])
        for stanica in self.__ucitaniPodaci:
            if stanica not in list(data.keys()):
                data[stanica] = []
            for datum in list(self.__ucitaniPodaci[stanica]):
                data[stanica].append(datum)
        
        return data
###############################################################################
    def dohvati_ucitane_kanale(self, stanica):
        """
        Za zadanu stanicu, vraca sve ucitane kanale
        """
        if stanica in self.__stanice.keys():
            return sorted(list(self.__stanice[stanica].keys()))
###############################################################################
    def set_citac(self, citac):
        """Postavlja instancirani objekt citac u dokument
        
        Citac je zaduzen da po potrebi ucitava podatke koji nedostaju te da javi
        dokumentu do kojih podataka moze doci (kombinacija stanica/datum).
        
        Citac mora imati metodu citaj(stanica, datum) koja dohvaca sve kanale
        i sprema ih u dictionary pandas datafrejmova (kljuc dicta je 'ime kanala')
        
        Citac mora imati metodu dohvati_sve_dostupne() koja vraca dictionary
        {'stanica':[lista datuma]} koje moze ucitati.
        """
        #postavi citac
        self.__citac = citac
        #provjeri do cega citac moze doci
        self.__dostupniPodaci = self.__citac.dohvati_sve_dostupne()
###############################################################################
    def pripremi_podatke(self, stanica, tMin, tMax):
        """Vrati trazeni slice glavnog datafrejma i satno agregirani slice

        dosta opsirna metoda, mora odraditi sljedece        
        1. provjeri da li trazeni raspon pokriva sve ucitane podatke
        2. po potrebi ucitaj sto nedostaje, validiraj te dodaj na "glavni frame"
        """
        self.__aktivnaStanica = stanica
        self.__tMin = tMin
        self.__tMax = tMax

        #nadji raspon vremenskog intervala [tMin, tMax] izrazen kao lista dana
        raspon = []
        temp = pd.date_range(start = tMin.date(), end = tMax.date(), freq = 'D')
        for ind in temp:
            raspon.append(ind.date())
        #raspon sada sadrzi listu datuma, datetime.date objekata
        
        #ucitaj fileove po potrebi
        for datum in raspon:
            #combo stanica / datum moraju biti medju dostupnima
            test1 = False
            if stanica in list(self.__dostupniPodaci.keys()): #dostupnost stanice
                if datum in list(self.__dostupniPodaci[stanica]): #dostupnost datuma
                    test1 = True
            
            if stanica not in list(self.__ucitaniPodaci.keys()) and test1:
                #stanica nije prije ucitana, ali stanica i datum su dostupni
                frejmovi = self.__citac.citaj(stanica, datum)
                self.__dodaj_nove_frejmove(stanica, frejmovi)
                self.__ucitaniPodaci[stanica] = [datum]
            else:
                #stanica je prije ucitana, datum je dostupan
                if datum not in list(self.__ucitaniPodaci[stanica]) and test1:
                    frejmovi = self.__citac.citaj(stanica, datum)
                    self.__dodaj_nove_frejmove(stanica, frejmovi)
                    self.__ucitaniPodaci[stanica].append(datum)                
###############################################################################
    def dohvati_info_podataka(self, stanica, tMin, tMax):
        """
        metoda sluzi da se dohvate informacije o slajsu (primarno:valjani kanali)
        """
        kanali = self.dohvati_ucitane_kanale(stanica)
        popis = []
        for kanal in kanali:
            frejm = self.__get_slice(stanica, kanal, tMin, tMax)
            #broj np.NaN podataka u frejmu
            n1 = len(frejm[np.isnan(frejm[u'koncentracija']) == True])
            #ukupni broj podataka u frejmu
            n2 = len(frejm)
            if n2 != n1: #kreni dalje samo ako postoje koncentracije koji nisu np.NaN
                popis.append(kanal)
        #vrati info o stanici, granicama frejma, popisu "valjanih" kanala
        return [stanica, tMin, tMax, popis]
###############################################################################
    def dohvati_minutni_frejm(self, stanica, tMin, tMax, kanal):
        """
        funkcija vraca trazeni slice minutnih podataka
        tMin i tMax su granice slajsa (graniice su ukljucene)
        """
        frejm = self.__get_slice(stanica, kanal, tMin, tMax)
        return frejm
###############################################################################
    def dohvati_agregirani_frejm(self, stanica, tMin, tMax, kanal):
        """
        funkcija vraca trazeni slice minutnih podataka
        tMin i tMax su granice slajsa (graniice su ukljucene)
        """
        frejm = self.__get_slice(stanica, kanal, tMin, tMax)
        frejm = self.__agregator.agregiraj_kanal(frejm)
        return frejm
###############################################################################








    def dohvati_podatke(self, stanica, tMin, tMax):
        #TODO! treba ga prepisati na nesto jasnije
        """
        metoda dohvaca slice, agregira
        """
        self.__aktivnaStanica = stanica
        self.__tMin = tMin
        self.__tMax = tMax
        kanali = self.dohvati_ucitane_kanale(self.__aktivnaStanica)
        self.__trenutniMinutniSlice = {}
        self.__trenutniAgregiraniSlice = {}

        for kanal in kanali:
            minutni = self.__get_slice(stanica, kanal, tMin, tMax)
            #pokusaj izbacivanja kanala gdje su svi podaci koncentracije NaN
            #broj nan podataka
            n1 = len(minutni[np.isnan(minutni[u'koncentracija']) == True])
            #ukupni broj podataka
            n2 = len(minutni)
            if n2 > n1:
                self.__trenutniMinutniSlice[kanal] = minutni
                self.__trenutniAgregiraniSlice[kanal] = self.__agregator.agregiraj_kanal(minutni)
            
#            self.__trenutniMinutniSlice[kanal] = self.__get_slice(stanica, kanal, tMin, tMax)
#            self.__trenutniAgregiraniSlice[kanal] = self.__agregator.agregiraj_kanal(self.__trenutniMinutniSlice[kanal])

        #vrati minutne i satno agregirane frejmove
        return self.__trenutniMinutniSlice, self.__trenutniAgregiraniSlice
                
###############################################################################
    def update_frejm(self, stanica, kanal, frejm):
        """Nadodaje ili updatea jedan pandas datafame
        
        Metoda se primarno koristi kada neki drugi objekt zeli "pohraniti"
        izmjene frejma.
        """
        #zapakiraj frame u frejmove
        frejmovi = {}
        frejmovi[kanal]=frejm
        #pozovi funkciju koja ce dodati/izmjeniti frejmove
        self.__dodaj_nove_frejmove(stanica, frejmovi)
###############################################################################
    def __get_slice(self, stanica, kanal, tMin, tMax):
        """
        Metoda dohvaca trazeni slice podataka iz self.__stanice
        
        - iskljucivo je koristi self.dohvati_slice
        - izdvojeno samo radi preglednosti
        -RUBOVI tMin i tMax SU UKLJUCENI
        
        Slice ide u dva navrata. Direktni .loc[min:max] je potencijalni izvor
        key errora. U ekstremnom slucaju, cak i kada netko zariba min i max
        granice, izlaz je prazan dataframe
        """
        #napravi kopiju cijelog frejma
        df = self.__stanice[stanica][kanal].copy()
        #makni sve podatke koji su manji od donje granice
        df = df[df.index >= tMin]
        #makni sve podatke koji su veci od tMax
        df = df[df.index <= tMax]
        #vrati dobiveni slice
        return df
###############################################################################
    def __dodaj_nove_frejmove(self, stanica, frejmovi):
        """Metoda dodaje/updatea postojece frejmove u dokumentu
        
        Pomocna metoda za dodavanje frejmova u dokument
        
        Ulazni parametri:
        stanica --> kljuc pod kojim se nalaze ciljani frejmovi za merge
        frejmovi --> frejmvi koje mergamo na postojece
        """
        if stanica in list(self.__stanice.keys()):
            for kanal in frejmovi:
                #ako stanica postoji, provjeri postojanje knala
                if kanal in list(self.__stanice[stanica].keys()):
                    self.__stanice[stanica][kanal] = pd.merge(
                        self.__stanice[stanica][kanal], 
                        frejmovi[kanal], 
                        how = 'outer', 
                        left_index = True, 
                        right_index = True, 
                        sort = True, 
                        on = [u'koncentracija', u'status', u'flag'])
                    self.__stanice[stanica][kanal].update(frejmovi[kanal])
                else:
                    #slucaj kada dodajemo novi kanal na postojecu stanicu
                    self.__stanice[stanica][kanal] = frejmovi[kanal]
        else:
            #slucaj kada stanica ne postoji u dictu, dodaj sve frejmove
            self.__stanice[stanica] = frejmovi
                
                
###############################################################################
###############################################################################
#    def promjeni_flag(self, args):
#        """
#        Promjena flaga, args je lista argumenata koja opisuje sto se mjenja
#        """
#        tmin = args[0] #vrijeme od (ukljucijuci)
#        tmax = args[1] #vrijeme do (ukljucijuci)
#        flag = args[2] #vrijednost flaga, (1000 ako je ok, -1000 ako nije)
#        kanal = args[3] #informacija o kanalu
#        stanica = self.__aktivnaStanica
#        #TODO! test ispravnosti zahtjeva (visak??)
#        if kanal in list(self.__stanice[stanica].keys()):
#            t1 = tmin in self.__stanice[stanica][kanal].index
#            t2 = tmax in self.__stanice[stanica][kanal].index
#            if t1 and t2:
#                self.__stanice[stanica][kanal].loc[tmin:tmax, u'flag'] = flag

        
        




"""
Za sada sve ispod je tehnicki visak, izbrisi nakon sto app proradi kako spada
"""

        
#        self.frejmovi={}
#        #2. dict satno agregiranih podataka
#        self.agregirani={}
#        #3. kljuc - trenutno aktivna komponenta (npr. SO2-ppb)
#        self.aktivniFrame=None
#        #4. trenutno odabrani satno agregirani podatak (sa satnog grafa)
#        self.odabraniSatniPodatak=None
#        #5. odabrani minutni podatak (sa minutnog grafa)
#        self.odabraniMinutniPodatak=None
#        #8. popis svih ključeva mape frejmovi
#        self.kljucSviFrejmovi=[]
#        #9. dict uredjaja za agregator?
#        self.dictUredjaja={}
        
###############################################################################
#    def set_frejmovi(self, frejmovi):
#        """
#        Metoda postavlja novi set frejmova u dokument
#        """
#        #emitiraj novi status        
#        message = 'Agregiranje podataka u tjeku...'
#        self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'), message)
#        
#        self.frejmovi = frejmovi
#        self.kljucSviFrejmovi = sorted(list(self.frejmovi))
#        self.set_uredjaji(self.kljucSviFrejmovi)
#        self.agregiraj_sve(self.kljucSviFrejmovi)
#        
#        #emitiraj novi status        
#        message = 'Agregacija gotova.'
#        self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'), message)
################################################################################
#    def set_aktivni_frejm(self, kljuc):
#        """
#        Funkcija se poziva kada dokument dobije signal da je kanal promjenjen.
#        -brise grafove, ponovo crta satni graf
#        """
#        self.aktivniFrame = str(kljuc)
#
#        self.crtaj_satni_graf(self.aktivniFrame)
#        self.__dostupniPodaci 
#        #emitiraj novi status
#        message = 'Promjena kanala. Trenutni kanal : {0}'.format(self.aktivniFrame)
#        self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'), message)
################################################################################
#    def crtaj_satni_graf(self, kljuc):
#        """
#        Funkcija brise sve grafove te crta satno agregirane podatke na satnom
#        grafu.
#        """
#        #brisanje grafova sa gui-a
#        self.emit(QtCore.SIGNAL('brisi_grafove()'))   
#        
#        #zahtjev za crtanjem satno agregiranih podataka za aktivni frame
#        self.emit(QtCore.SIGNAL('crtaj_satni(PyQt_PyObject)'), 
#                  self.agregirani[kljuc])
################################################################################
#    def crtaj_minutni_graf(self, sat):
#        """
#        Funkcija za odabrani sat, priprema minutne podatke.
#        Nakon pripreme podataka emitira signal za crtanje minutnog grafa
#        """
#        #sat je string
#        sat = str(sat)
#        #racunanje gornje i donje granice, castanje u string nakon racunice
#        up = pd.to_datetime(sat)
#        down = up-timedelta(minutes=59)
#        down = pd.to_datetime(down)
#        self.odabraniSatniPodatak = up
#        #napravi listu data[all,flag>=0,flag<0]
#        df=self.frejmovi[self.aktivniFrame]
#        df=df.loc[down:up,:]
#        dfOk=df[df.loc[:,u'flag']>=0]
#        dfNo=df[df.loc[:,u'flag']<0]
#        data=[df,dfOk,dfNo]
#
#        #emit za crtanje minutnih podataka
#        self.emit(QtCore.SIGNAL('crtaj_minutni(PyQt_PyObject)'), data)
################################################################################
#    def promjeni_flag(self, lista):
#        """
#        Opcenita promjena flaga.
#        ulaz : [min vrijeme, max vrijeme, novi flag]
#        izlaz : emit za crtanje novih grafova
#        """
#        timeMin = lista[0]
#        timeMax = lista[1]
#        flag = lista[2]
#        #promjeni flag
#        self.frejmovi[self.aktivniFrame].loc[timeMin:timeMax,u'flag'] = flag
#        #reagregiraj podatke za aktivni frame
#        self.agregiraj_odabir(self.frejmovi,self.aktivniFrame)
#        #nacrtaj satni i minutni graf
#        self.crtaj_satni_graf(self.aktivniFrame)
#        if self.odabraniSatniPodatak != None:
#            self.crtaj_minutni_graf(self.odabraniSatniPodatak)
################################################################################
#    def set_uredjaji(self,kljucevi):
#        """
#        Popunjavanje dicta s komponenta:uredjaj. Za sada su svi uredjaji M100C
#        
#        Manji problem je, nemam blage veze koji je uredjaj za koju komponentu
#        i mislim da fali hrpa uredjaja u modulu uredjaj.py
#        
#        Direktno matchanje stringova zamjeniti regexom??
#        """
#        for kljuc in kljucevi:
#            if kljuc=='1-S02-ppb':
#                #nesto u ovom stilu...
#                self.dictUredjaja[kljuc]=uredjaj.M100E()
#            elif kljuc=='neki drugi':
#                #drugi kljuc
#                self.dictUredjaja[kljuc]=uredjaj.M100C()
#            else:
#                #neka generalna metoda???
#                self.dictUredjaja[kljuc]=uredjaj.M100C()
################################################################################
#    def agregiraj_sve(self,frejmovi):
#        """
#        Agregiranje svih komponenata sa autovalidacijom.
#        Ovu metodu je bitno pozvati nakon ucitavanja novih podataka barem jednom
#        """
#        for kljuc in list(frejmovi):
#            ag=agregator.Agregator(self.dictUredjaja[kljuc])
#            
#            validator=auto_validacija.AutoValidacija()
#            validator.dodaj_uredjaj(self.dictUredjaja[kljuc])
#            validator.validiraj(self.frejmovi[kljuc])
#            
#            ag.setDataFrame(self.frejmovi[kljuc])
#            self.agregirani[kljuc]=ag.agregirajNiz()
################################################################################    
#    def agregiraj_odabir(self,frejmovi,kljuc):
#        """
#        Agregiranje jedne komponente bez autovalidacije.
#        Autovalidacija bi pregazila custom flagove.
#        Nema smisla reagregirati sve ako je promjena samo na jednoj komponenti
#        """
#        ag=agregator.Agregator(self.dictUredjaja[kljuc])
#        ag.setDataFrame(self.frejmovi[kljuc])
#        self.agregirani[kljuc]=ag.agregirajNiz()
################################################################################
################################################################################