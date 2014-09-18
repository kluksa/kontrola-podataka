#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 11 08:44:06 2014

@author: velimir
"""
import sys
import os
import pandas as pd
import re
from functools import wraps

###############################################################################
def benchmark(func):
    """
    Dekorator, izbacuje van ime i vrijeme koliko je funkcija radila
    Napisi @benchmark odmah iznad definicije funkcije da provjeris koliko je brza
    """
    import time
    @wraps(func)
    def wrapper(*args, **kwargs):
        t = time.clock()
        res = func(*args, **kwargs)
        print(func.__name__, time.clock()-t)
        return res
    return wrapper
###############################################################################
###############################################################################
class WlReader(object):
    """Ova klasa odradjuje citanje weblogger csv fileova iz nekog direktorija.
    
    Inicijalizira se sa nekim valjanim pathom.
    """
    def __init__(self, path):
        """Konstruktor klase"""
        self.__direktorij = None
        if os.path.isdir(path):
            self.__direktorij = path
        else:
            raise IOError('Ne postoji zadani direktorij')
        
        self.__fileList =[]
        self.__fileList_C = []
        
        self.__dostupni = {}
        self.__files = {}

        self.__get_files()
        self.__nadji_dostupne()
        
###############################################################################
    def dohvati_sve_dostupne(self):
        """Metoda vraca dictionary svih fileova koje zna procitati
        
        BITNA METODA ZA DOKUMENT
        Izlaz je dictionary {'stanica':[lista datuma]}
        """
        return self.__dostupni
###############################################################################
    def citaj(self, stanica, datum):
        """
        Metoda vraca frejmove svih fileova koji se nalaze pod kljucevima stanica, 
        datum
        
        PAZI!!!
        -kljuc datuma je formata string 'yyyymmdd'
        -ulazni parametar datum je datetime.date objekt!
        njegova string reprezentacija je 'yyyy-mm-dd'
        """
        #adapter za kljuc
        date = str(datum)
        date = date[0:4]+date[5:7]+date[8:]
        #pozovi metodu da procita sve dostupne
        frejmovi = self.__citaj_listu(self.__files[stanica][date])
        
        return frejmovi
        
###############################################################################
    def __nadji_dostupne(self):
        """Metoda sklapa mapu dostupnih podataka{stanica:[lista datuma]}"""
        for stanica in self.__files:
            temp = map(pd.to_datetime, list(self.__files[stanica].keys()))
            datumi = []
            for datum in temp:
                datumi.append(datum.date())
            self.__dostupni[stanica] = datumi
###############################################################################
    def __parsiraj(self, item):
        """Pomocna funkcija za izradu mape dostupnih fileova
        
        Parser da dobijemo ime i datum uz filename. Razdvaja ime stanice od
        datuma da bi dobili kljuceve za dictionary pod kojima spremamo lokaciju
        filea.
        """
        item = item[0:len(item)-4]
        loc = item.find('-')
        stanica = item[:loc]
        #TODO!
        #malo nespretno..nadam se da su sve stanice pisane malim slovima
        #inace npr. 'Zagreb_Centar20140915.csv' nece biti ukljucen
        if stanica.find('_C') != -1:
            stanica = stanica[0:len(stanica)-2]
        datum = item[loc+1:loc+9]
        return stanica, datum
###############################################################################
    def __napravi_mapu(self, data):
        """Pomocna funkcija za izradu mape dostupnih fileova        
        
        Napravi mapu (dictionary) od ulaznih podataka
        Izlaz je kompozitni dictionary:
        Vanjski kljuc je ime stanice sa kojim je povezan dict datuma.
        Svaki pojedini datum je kljuc pod kojim se nalazi lista svih fileova
        """
        stanice={}
    
        for file in data:
            stanica,datum=self.__parsiraj(file)
            
            if stanica not in stanice:
                stanice[stanica]={datum:[file]}
            else:
                if datum not in stanice[stanica]:
                    stanice[stanica].update({datum:[file]})
                else:
                    stanice[stanica][datum].append(file)
        return stanice
###############################################################################
    def __get_files(self):
        """Metoda pronalazi sve valjane csv fileove u folderu
        
        Podatci o fileovima su spremljeni na sljedeci nacin:
        Nested dictionary, {'stanica':datum}, {'datum':[csv files]}
        """
        #pronadji sve fileove u folderu s kojim je objekt inicijaliziran
        allFiles = os.listdir(self.__direktorij)
        #selektiraj sve fileove od interesa (one koje matchaju regexp)
        for file in allFiles:
            reMatch = re.match(r'.*-\d{8}.?.csv', file, re.IGNORECASE)
            if reMatch:
                if file.find(u'_C') == -1:
                    self.__fileList.append(file)
                else:
                    self.__fileList_C.append(file)
        #izrada kompozitnog dicta uz pomoc funkcije
        self.__files = self.__napravi_mapu(self.__fileList)
###############################################################################
    def __citaj(self, file):
        """
        file = ime filea
        funkcija cita weblogger csv fileove u dictionary pandas datafrejmova
        """
        #dodaj aktivni direktorij ispred filea
        path = os.path.join(self.__direktorij, file)
        
        #ucitaj csv file
        df = pd.read_csv(
            path, 
            na_values = '-999.00', 
            index_col = 0, 
            parse_dates = [[0,1]], 
            dayfirst = True, 
            header = 0, 
            sep = ',', 
            encoding = 'iso-8859-1')
        
        #skloi frejmove za sve kanale
        headerList = df.columns.values
        frejmovi = {}
        for i in range(0,len(headerList)-2,2):
            colName = headerList[i]
            frejmovi[colName] = df.iloc[:,i:i+2]
            frejmovi[colName][u'flag'] = pd.Series(0, index = frejmovi[colName].index)
            frejmovi[colName].columns = [u'koncentracija', u'status', u'flag']
        
        return frejmovi

###############################################################################
    def __citaj_listu(self, pathLista):
        """
        pathLista = lista svih pathova za otvaranje
        INPUT - lista stringova
        funkcija cita listu weblogger csv fileova u dictionary pandas datafrejmova
        """
        #ucitaj prvi file
        file = pathLista.pop(0)
        frejmovi = self.__citaj(file)
        
        #petlja koja ucitava ostale fileove u listi (lista je sada kraca)
        for file in pathLista:
            frejmoviTemp = self.__citaj(file)
            if frejmoviTemp != None:
                #kod za spajanje datafrejma
                for key in frejmoviTemp.keys():
                    if key in frejmovi.keys():
                        #ako postoji isti kljuc u oba datafrejma -  update/merge
                        #ovaj korak je nesto u stilu full outer join
                        frejmovi[key] = pd.merge(
                            frejmovi[key], 
                            frejmoviTemp[key], 
                            how = 'outer', 
                            left_index = True, 
                            right_index = True, 
                            sort = True, 
                            on = [u'koncentracija', u'status', u'flag'])
                        #update vrijednosti koje nisu np.NaN
                        frejmovi[key].update(frejmoviTemp[key])
                    else:
                        #ako ne postoji kljuc (novi stupac) - dodaj novi frame
                        frejmovi[key] = frejmoviTemp[key]
        
        return frejmovi
###############################################################################
###############################################################################            
if __name__ == '__main__':
    #citac = WlReader('./data/')
    @benchmark
    def inicijalizacija_citaca(path):
        return WlReader(path)
        
    citac = inicijalizacija_citaca('./data/')
    print('\nSVI DOSTUPNI')    
    print(citac.dohvati_sve_dostupne())
    stanica = 'plitvicka jezera'
    print('\nkljuc stanice:',stanica)
    #treba mi datetime.date    
    datum = '20140604' #pod tim kljucem ga krece citati
    datum = pd.to_datetime(datum)
    datum = datum.date()
    print('\nkljuc datuma:',datum) #ovo se ocekuje kao imput iz drugih dijelova koda
    print('\ncitanje fileova')    
    frejmovi = citac.citaj(stanica, datum)
    print(frejmovi['1-SO2-ppb'].head())
    