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

import citac
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
        
        '''
        self.nizNizova = {}
        
        Gornji member u biti ne treba. Podatci za grafove su u drugom formatu
        -satni graf -> self.agregirani['self.aktivniFrame']
        -minutni graf -> self.frejmovi['self.aktivniFrame'].loc[min:max,u'koncentracija']
        '''
###############################################################################        
    def citaj_csv(self,path):
        """
        Ucitava podatke iz csv filea
        sprema sve kljuceve u member listu
        popunjava dict s uredjajima
        inicijalna agregacija sa autovalidacijom
        """
        self.frejmovi=citac.WlReader().citaj(path)
        self.kljucSviFrejmovi=list(self.frejmovi)
        self.set_uredjaji(self.kljucSviFrejmovi)
        self.agregiraj_sve(self.kljucSviFrejmovi)
        
        message='File load complete'
        #emitiraj nove podatke o kljucu i status
        self.emit(QtCore.SIGNAL('doc_get_kljucevi(PyQt_PyObject)'),self.kljucSviFrejmovi)
        self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),message)
###############################################################################
    def citaj_lista_csv(self,lista):
        """
        Ucitava podatke iz csv filea
        sprema sve kljuceve u member listu
        popunjava dict s uredjajima
        inicijalna agregacija sa autovalidacijom
        
        P.S. malo repetativno...valja srediti ovih par slicnih funkcija na bolji nacin
        """
        self.frejmovi=citac.WlReader().citaj_listu(lista)
        self.kljucSviFrejmovi=list(self.frejmovi)
        self.set_uredjaji(self.kljucSviFrejmovi)
        self.agregiraj_sve(self.kljucSviFrejmovi)
        
        message='Multiple file load complete'
        #emitiraj nove podatke o kljucu i status
        self.emit(QtCore.SIGNAL('doc_get_kljucevi(PyQt_PyObject)'),self.kljucSviFrejmovi)
        self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),message)        
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
        ag=agregator.Agregator(self.dictUredjaja[kljuc])
        ag.setDataFrame(self.frejmovi[kljuc])
        self.agregirani[kljuc]=ag.agregirajNiz()
###############################################################################
    def doc_pripremi_satne_podatke(self,kanal):
        """
        -set aktivni frame
        -emitiraj signal sa satno agregiranim podatcima
        -emitiraj listu satnih vrijednosti (stringova)
        """
        self.aktivniFrame = str(kanal)
        #za slucaj da netko stisne gumb prije nego ucita podatke
        try:
            data=self.agregirani[self.aktivniFrame]
            self.emit(QtCore.SIGNAL('doc_draw_satni(PyQt_PyObject)'),data)
            sati=[]
            for vrijeme in self.agregirani[self.aktivniFrame].index:
                sati.append(vrijeme)
            self.emit(QtCore.SIGNAL('doc_sati(PyQt_PyObject)'),sati)
        except KeyError:
            message='Unable to draw data, load some first'
            self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),message)
###############################################################################
    def doc_pripremi_minutne_podatke(self,sat):
        #sat je string
        self.odabraniSatniPodatak=sat
        #racunanje gornje i donje granice, castanje u string nakon racunice
        up=pd.to_datetime(sat)
        down=up-timedelta(minutes=59)
        
        #napravi listu data[all,flag>=0,flag<0]
        try:
            df=self.frejmovi[self.aktivniFrame]
            df=df.loc[down:up,:]
            dfOk=df[df.loc[:,u'flag']>=0]
            dfNo=df[df.loc[:,u'flag']<0]
            data=[df,dfOk,dfNo]
        
            #emit data prema kontroleru
            self.emit(QtCore.SIGNAL('doc_minutni_podatci(PyQt_PyObject)'),data)
        except KeyError:
            message='Unable to draw data, load some first1'
            self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),message)

###############################################################################
    def promjeni_flag_minutni(self,dic):
        """
        Promjena minutnog flaga
        """
        time=dic['time']
        flag=dic['flag']
        kanal=dic['kanal']
        sat=dic['sat']
        self.aktivniFrame=kanal
        self.odabraniSatniPodatak=sat

        #promjeni flag
        self.frejmovi[self.aktivniFrame].loc[time,u'flag']=flag
        
        #reagregiraj aktivni frame
        self.agregiraj_odabir(self.frejmovi,self.aktivniFrame)
        
        #emitiraj zahtjev za ponovnim crtanjem satnog i minutnog grafa
        data=[kanal,sat]
        self.emit(QtCore.SIGNAL('reagregiranje_gotovo(PyQt_PyObject)'),
                  data)
        message='Reaggregating done, displaying data'
        self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),message)
                  
###############################################################################
    def promjeni_flag_minutni_span(self,dic):
        """
        Promjenia minutnog flaga u rasponu
        """
        timeMin=dic['min']
        timeMax=dic['max']
        flag=dic['flag']
        kanal=dic['kanal']
        sat=dic['sat']
        self.aktivniFrame = str(kanal)
        self.odabraniSatniPodatak=sat
        
        #promjeni flag
        self.frejmovi[self.aktivniFrame].loc[timeMin:timeMax,u'flag']=flag
        
        #reagregiraj aktivni frame
        self.agregiraj_odabir(self.frejmovi,self.aktivniFrame)        
        
        #emitiraj zahtjev za ponovnim crtanjem satnog i minutnog grafa
        data=[kanal,sat]
        self.emit(QtCore.SIGNAL('reagregiranje_gotovo(PyQt_PyObject)'),
                  data)
        message='Reaggregating done, displaying data'
        self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),message)

###############################################################################
#    def save_trenutni_frejmovi(self,filepath):
#        """
#        Save self.frejmovi u csv file, report kada si gotov
#        """
#        if self.frejmovi!={}:
#            citac.WlReader().save_work(self.frejmovi,filepath)
#            message='Data saved as '+filepath
#            self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),message)
#        else:
#            message='Unable to save'
#            self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),message)
################################################################################
#    def load_frejmovi_iz_csv(self,filepath):
#        #clear grafova
#        self.emit(QtCore.SIGNAL('grafovi_clear()'))
#        #clear starih podataka
#        self.frejmovi=None
#        self.kljucSviFrejmovi=None
#        
#        okviri=citac.load_work(filepath)
#        self.frejmovi=okviri
#        self.kljucSviFrejmovi=list(self.frejmovi)
#        #remove FLag i Zone, (jedini nemaju stupce koncentracija,status,flag)        
#        self.kljucSviFrejmovi.remove('Flag')
#        self.kljucSviFrejmovi.remove('Zone')
#        
#        self.set_uredjaji(self.kljucSviFrejmovi)
#        #agregiranje bez autovalidacije? problem
#        for kljuc in self.kljucSviFrejmovi:
#            self.agregiraj_odabir(self.frejmovi,kljuc)
#        
#        message='File load complete'
#        #emitiraj nove podatke o kljucu i status
#        self.emit(QtCore.SIGNAL('doc_get_kljucevi(PyQt_PyObject)'),self.kljucSviFrejmovi)
#        self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),message)
################################################################################
