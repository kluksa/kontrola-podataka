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

import uredjaj
import agregator
import auto_validacija

class DataStorage:
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
        self.ucitaniDokumenti = []

        
    def dodaj_frejm(self, tip, frejmovi, filename):
        """
        dodavanje frejmova na member varijable
        
        input:
        tip = 'satni' ili 'minutni'
        frejmovi = dict frejmova sa datafrejmom za svaki kanal
        
        output:
        lokalni update member varijabli
        """
        if tip == 'minutni':
            #prati koje si datume ucitao?
            self.ucitaniDokumenti.append(filename)
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

class Dokument(QtGui.QWidget):
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        #memberi
        #1. dict svih postaja, elementi su DataStorage objekti definirani iznad        
        self.postaje = {}
        
        
    #TODO!
    #1. metoda koja postavlja novu postaju u dict
    #2. metoda koja vraca sve postaje koje postoje u dictu (lista)
    #3. metoda koja postavlja frejmove u DataStorage objekt
    #4. metoda koja, za postaju, vraca sve kanale koji postoje (lista)
    #5. metoda koja za postaju vraca popis svih ucitanih fileova (lista)
    #6. metoda koja za postaju i kanal vraca popis svih dana u frejmu (lista)
    #7. metoda koja za zadanu postaju, kanal vraca slice frejma
    #8. metoda koja agregira frejm
    #9. metoda koja updatea frejmove (reagregiranje isl...)