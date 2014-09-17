# -*- coding: utf-8 -*-
"""
Created on Mon Sep 15 10:25:09 2014

@author: User
"""

import sys
import pandas as pd
import numpy as np

from PyQt4 import QtGui,QtCore
from datetime import timedelta

import citac
import uredjaj
import agregator
import auto_validacija


###############################################################################
###############################################################################
class DataStorage(object):
    """
    Klasa za spremanje podataka sa JEDNE stanice
    -kod instanciranja navedi ime postaje kao jedini argument
    """
    def __init__(self, postaja):
        #inicijalizacija membera
        self.nazivPostaje = postaja
        self.ucitaniFrejmovi = {}
        self.agregiraniFrejmovi = {}
        self.zadnjiKanal = None
        self.zadnjiSlice = []

        
    def dodaj_frejm(self, tip, frejmovi):
        """
        dodavanje frejmova na member varijable
        
        input:
        tip = 'satni' ili 'minutni'
        frejmovi = dict frejmova sa datafrejmom za svaki kanal
        
        output:
        lokalni update member varijabli
        """
        if tip == 'minutni':
            for kanal in frejmovi:
                if kanal in self.ucitaniFrejmovi.keys():
                    #unija frejmova
                    self.ucitaniFrejmovi[kanal] = pd.merge(
                        self.ucitaniFrejmovi[kanal], 
                        frejmovi[kanal], 
                        how = 'outer', 
                        left_index = True, 
                        right_index = True, 
                        sort = True, 
                        on = [u'koncentracija', u'status', u'flag'])
                    #update vrijednosti iz frejmovi koje nisu NaN
                    self.ucitaniFrejmovi[kanal].update(frejmovi[kanal])
                else:
                    self.ucitaniFrejmovi[kanal] = frejmovi[kanal]
        
        elif tip == 'satni':
            for kanal in frejmovi:
                if kanal in self.agregiraniFrejmovi.keys():
                    #unija frejmova
                    self.agregiraniFrejmovi[kanal] = pd.merge(
                        self.agregiraniFrejmovi[kanal], 
                        frejmovi[kanal],
                        how = 'outer', 
                        left_index = True, 
                        right_index = True, 
                        sort = True, 
                        on = ['broj podataka','status','avg','std','min','max','q05','median','q95','count'])
                    #update vrijednosti
                    self.agregiraniFrejmovi[kanal].update(frejmovi[kanal])
                else:
                    self.agregiraniFrejmovi[kanal] = frejmovi[kanal]
    
    
    def update_frejm(self, tip, kanal, frejm):
        """
        update vec izvucenih dijelova frejmova        
        
        input:
        tip = 'satni' ili 'minutni'
        kanal = ime kanala
        frejm = dataframe koji sadrzi podatak o promjenama frejma
        
        output:
        lokalni update member varijable
        """
        if tip == 'satni':
            self.agregiraniFrejmovi[kanal].update(frejm)
            self.zadnjiKanal = kanal
        elif tip == 'minutni':
            self.ucitaniFrejmovi[kanal].update(frejm)
            self.zadnjiKanal = kanal

            
    def dohvati_slice(self, tip, kanal, granice):
        """
        input:
        tip = 'satni' ili 'minutni'
        kanal = ime kanala
        granice = [min_index, max_index]
        
        output:
        dataframe slice
        """
        if tip == 'satni':
            self.zadnjiKanal = kanal
            self.zadnjiSlice = granice
            df = self.agregiraniFrejmovi[kanal].copy()
            df = df[df.index >= granice[0]]
            df = df[df.index <= granice[1]]
            return df
        elif tip == 'minutni':
            self.zadnjiKanal = kanal
            self.zadnjiSlice = granice
            df = self.ucitaniFrejmovi[kanal].copy()
            df = df[df.index >= granice[0]]
            df = df[df.index <= granice[1]]
            return df
    
    def dohvati_kanale(self, tip):
        """
        dohvaca popis kananla koji trenutno postoje
        input:
        tip = 'satni' ili 'minutni'
        
        output:
        popis kanala u dictu
        """
        if tip == 'satni':
            return self.agregiraniFrejmovi.keys()
        elif tip == 'minutni':
            return self.ucitaniFrejmovi.keys()

###############################################################################
###############################################################################
class Dokument(QtGui.QWidget):
    def __init__(self, parent = None):
        """
        konstruktor
        """
        QtGui.QWidget.__init__(self, parent)
        
        self.postaje = {}
        self.aktivniSatni = None
        self.aktivniMinutni = None
        
        self.CSVcitac = citac.WlReader()
        self.ag = agregator.Agregator2()
        

    def set_frejmovi(self, postaja, frejmovi):
        """
        postavi ucitane frejmove u DataStorage
        """
        if postaja not in list(self.postaje.keys()):
            self.postaje[postaja] = DataStorage(postaja)
        
        #TODO!
        #validiraj podatke
        data = frejmovi
        
        #agregiraj podatke        
        agData = self.ag.agregiraj(data)
        #upisi podatke u frejm
        self.postaje[postaja].dodaj_frejm('minutni', data)
        self.postaje[postaja].dodaj_frejm('satni', agData)
        
    def citaj_csv(self, postaja, path):
        """
        read csv i set frejmove u dict
        """
        frejmovi = self.CSVcitac.citaj(path)
        self.set_frejmovi(postaja, frejmovi)
        
    def crtaj_satni_graf(self, postaja, kanal, granice):
        """
        treba srediti I/O iz grafova
        granice --> lista, [min index, max index]
        """

        #brisanje grafova sa gui-a
        self.emit(QtCore.SIGNAL('brisi_grafove()'))
        
        agSlice = self.postaje[postaja].dohvati_slice('satni', kanal, granice)
        self.aktivniSatni = agSlice
        
        if len(agSlice) != 0:
            #dataframe sa podatcima
            #emit prema GUI-u
            self.emit(QtCore.SIGNAL('crtaj_satni(PyQt_PyObject)'), agSlice)
        else:
            #dataframe bez valjanih podataka, agSlice je prazan
            #emit prema GUI-u
            self.emit(QtCore.SIGNAL('crtaj_satni(PyQt_PyObject)'), None)
        
    def crtaj_minutni_graf(self, postaja, kanal, sat):
        """
        treba srediti I/O iz grafova
        """
        sat = str(sat)
        #racunanje gornje i donje granice, castanje u string nakon racunice
        up = pd.to_datetime(sat)
        down = up-timedelta(minutes=59)
        down = pd.to_datetime(down)
                
        #dohvati slice sa minutnim podatcima
        df = self.postaje[postaja].dohvati_slice('minutni', kanal, [up,down])
        self.aktivniMinutni = df
        if len(df) != 0:
            dfOK = df[df['flag']>=0]
            dfNOT = df[df['flag']<0]
            data = [dfOK, dfNOT]
            #emit za crtanje minutnih podataka
            self.emit(QtCore.SIGNAL('crtaj_minutni(PyQt_PyObject)'), data)
        else:
            #dataframe je prazan
            self.emit(QtCore.SIGNAL('crtaj_minutni(PyQt_PyObject)'), None)
        
    def promjeni_flag(self, postaja, kanal, lista):
        """
        Opcenita promjena flaga.
        ulaz : [min vrijeme, max vrijeme, novi flag]
        izlaz : emit za crtanje novih grafova
        """
        timeMin = lista[0]
        timeMax = lista[1]
        flag = lista[2]
        #promjeni flag
        #reagregiraj podatke za aktivni frame
        #update podatke u glavnom frejmu
        #nacrtaj satni i minutni graf