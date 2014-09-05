# -*- coding: utf-8 -*-
"""
Created on Fri Aug  1 12:14:02 2014

@author: velimir

speed test agregatora
"""

import pandas as pd
import numpy as np
from functools import wraps
from datetime import timedelta, datetime


"""
Pokusaj agregiranja koristeci resample (metoda timeseries datafrejmova)
"""
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
@benchmark
def samo_citaj(path):
    """
    samo pandas read_csv
    """
    df = pd.read_csv(
        path, 
        na_values = '-999.00', 
        index_col = 0, 
        parse_dates = [[0,1]], 
        dayfirst = True, 
        header = 0, 
        sep = ',', 
        encoding = 'iso-8859-1')
    return df


@benchmark
def citaj(path):
    """
    identicna funkcija kao kod citaca (otprilike)
    """

    df = samo_citaj(path)
    #samo dio sa sklapanjem frejmova
    headerList = df.columns.values
    frejmovi = {}
    for i in range(0,len(headerList)-2,2):
        colName = headerList[i]
        frejmovi[colName] = df.iloc[:,i:i+2]
        frejmovi[colName][u'flag'] = pd.Series(0, index = frejmovi[colName].index)
        frejmovi[colName].columns = [u'koncentracija', u'status', u'flag']
    return frejmovi
###############################################################################
###############################################################################
class Agregator(object):
    """
    agregator je smanjen samo da racuna mean
    """    
    uredjaji=[]

    def __init__(self, uredjaji):
        self.uredjaj = uredjaji


    def dodajUredjaj(self, uredjaj):
        self.uredjaji.append(uredjaj)
        
          
    def setDataFrame(self, df):
        self.__df = df
        self.pocetak = df.index.min()+pd.DateOffset(hours=1) 
        self.kraj = df.index.max()
        self.sviSati=pd.date_range(self.pocetak, self.kraj, freq='H')

  
    def agreg(self, kraj):
        #modifikacija get slice kopira direktno, bez flag testa
        dds=self.getSlajs(kraj)
        
        #samo flagovi veci od 0
        ddd=dds[dds[u'flag']>=0]
        #samo mean
        avg=ddd.mean().iloc[0]

        data = avg
        return kraj, data

    def getSlajs(self, kraj):
        pocetak= kraj-timedelta(minutes=59)
        return self.__df[pocetak:kraj]
        
        
    #benchmark agregacije
    @benchmark
    def agregirajNiz(self):
        niz = []
        for sat in self.sviSati:
        	vrijeme, vrijednost = self.agreg(sat)
        	niz.append(vrijednost)
        return pd.DataFrame(niz, self.sviSati)
    
    def nizNiz(self):
        niz = []
        for sat in self.sviSati:
            fr = self.getSlajs(sat).iloc[:,0]
            niz.append(fr)
        return niz
###############################################################################
###############################################################################

@benchmark
def agreg_frejm(df):
    """
    za zadani dataframe, uzima sve vrijednosti >= 0 i racuna satni prosjek
    koristeci resample...
    """
    #TODO!
    #vidi ima li opcije how='average' ('q05', 'stdev'....)
    df1 = df[df['flag'] >= 0]
    avg = df1.resample('H', how = 'mean')    
    
    return avg


if __name__ == '__main__':
    #uciatavanje pj.csv i uzimanje samo jednog frejma za agregaciju (1-SO2-ppb)
    rawData = citaj('pj.csv')
    data = rawData['1-SO2-ppb']
    
    #usporedba... brzina agregatora / agreg_frejm
    
    #agregator
    print('\n\n!!Agregator!!')
    ag = Agregator(['u1','u2'])
    ag.setDataFrame(data)
    for i in range(10):
        agregirani1 = None
        agregirani1 = ag.agregirajNiz()
    
    #resample
    print('\n\n!!Resample!!')
    for i in range(10):
        agregirani2 = None
        agregirani2 = agreg_frejm(data)
    