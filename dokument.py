# -*- coding: utf-8 -*-
'''
Created on Apr 21, 2014

@author: kraljevic
'''
import sys
import pandas as pd
import numpy as np

from PyQt4 import QtGui,QtCore
from datetime import timedelta

import uredjaj
import agregator
import auto_validacija

class Dokument(QtGui.QWidget):
    '''
    classdocs
    -sublkasa QWidgeta zbog emit metode
    -self.kljucSviFrejmovi je malo zbunjujuć (svi kljucevi osim 'Zone' i 'Flag')
    '''


    def __init__(self,parent=None):
        '''
        Constructor
        '''
        QtGui.QWidget.__init__(self,parent)
        #bitni memberi - varijable
        #svi dict bi trebali korisiti isti kljuc - komponentu (npr. SO2-ppb)
        #1. dict datafrejmova koji sadrze sve podatke
        self.frejmovi={}
        #2. dict satno agregiranih podataka
        self.agregirani={}
        #3. kljuc - trenutno aktivna komponenta (npr. SO2-ppb)
        self.aktivniFrame=None
        #4. trenutno odabrani satno agregirani podatak (sa satnog grafa)
        self.odabraniSatniPodatak=None
        #5. odabrani minutni podatak (sa minutnog grafa)
        self.odabraniMinutniPodatak=None
        #8. popis svih ključeva mape frejmovi
        self.kljucSviFrejmovi=[]
        #9. dict uredjaja za agregator?
        self.dictUredjaja={}
        
###############################################################################
    def set_frejmovi(self, frejmovi):
        """
        Metoda postavlja novi set frejmova u dokument
        """
        #emitiraj novi status        
        message = 'Agregiranje podataka u tjeku...'
        self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'), message)
        
        #emitiraj promjenu kursora u "pjescani sat"
        self.emit(QtCore.SIGNAL('change_cursor(PyQt_PyObject)'),True)        
        
        self.frejmovi = frejmovi
        self.kljucSviFrejmovi = sorted(list(self.frejmovi))
        self.set_uredjaji(self.kljucSviFrejmovi)
        self.agregiraj_sve(self.kljucSviFrejmovi)
        
        #emitiraj novi status        
        message = 'Agregacija gotova.'
        self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'), message)
        #emitiraj promjenu kursora u "strelicu"
        self.emit(QtCore.SIGNAL('change_cursor(PyQt_PyObject)'),False)        
###############################################################################
    def set_aktivni_frejm(self, kljuc):
        """
        Funkcija se poziva kada dokument dobije signal da je kanal promjenjen.
        -brise grafove, ponovo crta satni graf
        """
        self.aktivniFrame = str(kljuc)

        self.crtaj_satni_graf(self.aktivniFrame)
        
        #emitiraj novi status
        message = 'Promjena kanala. Trenutni kanal : {0}'.format(self.aktivniFrame)
        self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'), message)
###############################################################################
    def crtaj_satni_graf(self, kljuc):
        """
        Funkcija brise sve grafove te crta satno agregirane podatke na satnom
        grafu.
        """
        #brisanje grafova sa gui-a
        self.emit(QtCore.SIGNAL('brisi_grafove()'))   
        
        #zahtjev za crtanjem satno agregiranih podataka za aktivni frame
        self.emit(QtCore.SIGNAL('crtaj_satni(PyQt_PyObject)'), 
                  self.agregirani[kljuc])
###############################################################################
    def crtaj_minutni_graf(self, sat):
        """
        Funkcija za odabrani sat, priprema minutne podatke.
        Nakon pripreme podataka emitira signal za crtanje minutnog grafa
        """
        #sat je string
        sat = str(sat)
        #racunanje gornje i donje granice, castanje u string nakon racunice
        up = pd.to_datetime(sat)
        down = up-timedelta(minutes=59)
        down = pd.to_datetime(down)
        self.odabraniSatniPodatak = up
        #napravi listu data[all,flag>=0,flag<0]
        df=self.frejmovi[self.aktivniFrame]
        df=df.loc[down:up,:]
        dfOk=df[df.loc[:,u'flag']>=0]
        dfNo=df[df.loc[:,u'flag']<0]
        data=[df,dfOk,dfNo]

        #emit za crtanje minutnih podataka
        self.emit(QtCore.SIGNAL('crtaj_minutni(PyQt_PyObject)'), data)
###############################################################################
    def promjeni_flag(self, lista):
        """
        Opcenita promjena flaga.
        ulaz : [min vrijeme, max vrijeme, novi flag]
        izlaz : emit za crtanje novih grafova
        """
        timeMin = lista[0]
        timeMax = lista[1]
        flag = lista[2]
        #promjeni flag
        self.frejmovi[self.aktivniFrame].loc[timeMin:timeMax,u'flag'] = flag
        #reagregiraj podatke za aktivni frame
        self.agregiraj_odabir(self.frejmovi,self.aktivniFrame)
        #nacrtaj satni i minutni graf
        self.crtaj_satni_graf(self.aktivniFrame)
        if self.odabraniSatniPodatak != None:
            self.crtaj_minutni_graf(self.odabraniSatniPodatak)
###############################################################################
    def set_uredjaji(self,kljucevi):
        """
        Popunjavanje dicta s komponenta:uredjaj. Za sada su svi uredjaji M100C
        
        Manji problem je, nemam blage veze koji je uredjaj za koju komponentu
        i mislim da fali hrpa uredjaja u modulu uredjaj.py
        
        Direktno matchanje stringova zamjeniti regexom??
        """
        for kljuc in kljucevi:
            if kljuc=='1-S02-ppb':
                #nesto u ovom stilu...
                self.dictUredjaja[kljuc]=uredjaj.M100E()
            elif kljuc=='neki drugi':
                #drugi kljuc
                self.dictUredjaja[kljuc]=uredjaj.M100C()
            else:
                #neka generalna metoda???
                self.dictUredjaja[kljuc]=uredjaj.M100C()
###############################################################################
    def agregiraj_sve(self,frejmovi):
        """
        Agregiranje svih komponenata sa autovalidacijom.
        Ovu metodu je bitno pozvati nakon ucitavanja novih podataka barem jednom
        """
        for kljuc in list(frejmovi):
            ag=agregator.Agregator(self.dictUredjaja[kljuc])
            
            validator=auto_validacija.AutoValidacija()
            validator.dodaj_uredjaj(self.dictUredjaja[kljuc])
            validator.validiraj(self.frejmovi[kljuc])
            
            ag.setDataFrame(self.frejmovi[kljuc])
            self.agregirani[kljuc]=ag.agregirajNiz()
###############################################################################    
    def agregiraj_odabir(self,frejmovi,kljuc):
        """
        Agregiranje jedne komponente bez autovalidacije.
        Autovalidacija bi pregazila custom flagove.
        Nema smisla reagregirati sve ako je promjena samo na jednoj komponenti
        """
        #emitiraj promjenu kursora u "pjescani sat"
        self.emit(QtCore.SIGNAL('change_cursor(PyQt_PyObject)'),True)                
        
        ag=agregator.Agregator(self.dictUredjaja[kljuc])
        ag.setDataFrame(self.frejmovi[kljuc])
        self.agregirani[kljuc]=ag.agregirajNiz()
        
        #emitiraj promjenu kursora u "strelicu"
        self.emit(QtCore.SIGNAL('change_cursor(PyQt_PyObject)'),False)                

###############################################################################
###############################################################################