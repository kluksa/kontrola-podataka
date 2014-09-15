# -*- coding: utf-8 -*-
"""
Agregator dio
"""

import pandas as pd
import numpy as np
from datetime import timedelta, datetime
import matplotlib.pyplot as plt

from functools import wraps

import citac
import auto_validacija
import uredjaj

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

class Agregator2(object):
    """
    def pomocnih funkcija za agregator
    ulaz --> numpy array ili neka lista
    izlaz --> broj
    """
    def h_q05(self, x):
        #5 percentil podataka
        return np.percentile(x,5)
        
    def h_q50(self, x):
        #median
        return np.percentile(x,50)
        
    def h_q95(self, x):
        #95 percentil podataka
        return np.percentile(x,95)
    
    def h_binary_or(self, x):
        #binarni or liste
        result = 0
        for i in x:
            result = result | int(i)
        return result
        
    def h_size(self, x):
        #broj podataka
        return len(x)
        
    def agregiraj_kanal(self, frejm):
        """
        input- pandasdataframe (datetime index, koncentracija, status, flag)
        output - pandas dataframe (datetime index, hrpa agregiranih vrijednosti)
        """
        agregirani = pd.DataFrame()
        
        """
        ukupni broj podataka koji postoje
        """
        df = frejm[np.isnan(frejm['koncentracija']) == False]
        tempDf = df.copy()
        dfKonc = tempDf['koncentracija']
        temp = dfKonc.resample('H', how = self.h_size)
        agregirani['broj podataka'] = temp
        
        """
        agregirani status
        """
        tempDf = df.copy()
        dfStatus = tempDf['status']
        temp = dfStatus.resample('H', how = self.h_binary_or)
        agregirani['status'] = temp
        
        """
        -definicija funkcija koje nas zanimaju
        -funkcije moraju imati kao ulaz listu ili numpy array, izlaz je broj
        """
        listaFunkcijaIme = ['avg', 'std', 'min', 'max', 'q05', 'median', 'q95', 'count']
        listaFunkcija = [np.mean, np.std, np.min, np.max, self.h_q05, self.h_q50, self.h_q95, self.h_size]
        
        """
        -kopija originalnog frejma
        -samo stupac koncentracije gdje je flag veci od 0
        """
        tempDf = df.copy()
        tempDf = tempDf[tempDf['flag']>=0]
        tempDf = tempDf['koncentracija']
        
        """
        -glavna petlja za agregiranje
        -loop preko lista funkcija
        """
        for i in range(len(listaFunkcija)):
            temp = tempDf.copy()
            temp = temp.resample('H', how = listaFunkcija[i])
            temp.name = listaFunkcijaIme[i]
            agregirani[temp.name] = temp
        
        """
        -provjeri da li je broj valjanih podataka sa flagom vecim od 0 veci od 45
        -ako nije... flagaj interval kao nevaljan...umetni placeholder vrijednosti
        """
        for i in agregirani.index:
            if agregirani.loc[i,'count']<45:
                agregirani.loc[i,'avg'] = -1
                agregirani.loc[i,'std'] = -1
                agregirani.loc[i,'min'] = -1
                agregirani.loc[i,'max'] = -1
                agregirani.loc[i,'q05'] = -1
                agregirani.loc[i,'q95'] = -1
                agregirani.loc[i,'median'] = -1
               
        return agregirani
        
    
    def agregiraj(self, frejmovi):
        """
        agregiraj rezultat kanal po kanal i spremaj u dict
        """
        rezultat = {}
        for i in frejmovi:
            frejm = frejmovi[i]
            rezultat[i] = self.agregiraj_kanal(frejm)
            
        return rezultat


class Agregator(object):
    
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
        
        #test da li su svi not nan flagovi negativni
        ddNan=dds[pd.isnull(dds[u'koncentracija'])==False]
        ddFlag=ddNan[ddNan[u'flag']<0]
        if len(ddNan)==len(ddFlag):
            #svi not nan flagovi su negativni
            allFlagStatus=True
        else:
            allFlagStatus=False
        
        ddd=dds[dds[u'flag']>=0]
        avg=ddd.mean().iloc[0]
        std=ddd.std().iloc[0]
        max=ddd.max().iloc[0]
        min=ddd.min().iloc[0]
        med=ddd.quantile(0.5).iloc[0]
        q95=ddd.quantile(0.05).iloc[0]
        q05=ddd.quantile(0.95).iloc[0]
        count=ddd.count().iloc[0]
            
        status=0
        for i in ddd[u'status']:
            try:
                status|=int(i)
            except ValueError:
                status|=int(0)
        
        #prikazi druge podatke ako su svi flagovi manji od nule jer ddd je prazan
        if allFlagStatus:
            #prikazi agregat cijelog slajsa?
            avg=dds.mean().iloc[0]
            std=dds.std().iloc[0]
            max=dds.max().iloc[0]
            min=dds.min().iloc[0]
            med=dds.quantile(0.5).iloc[0]
            q95=dds.quantile(0.05).iloc[0]
            q05=dds.quantile(0.95).iloc[0]
            count=dds.count().iloc[0]
            
            status=0
            for i in dds[u'status']:
                try:
                    status|=int(i)
                except ValueError:
                    status|=int(0)

        data = {'avg':avg,'std':std,'min':min,'max':max,'med':med,'q95':q95,
                'q05':q05,'count':count,'status':status,'flagstat':allFlagStatus}
        return kraj, data
    
    def getSlajs(self, kraj):
        pocetak= kraj-timedelta(minutes=59)
# koristimo iskljucivo flagove, a ne statuse. Flagove odredjuje AutoValidacija
        #return self.__df[pocetak:kraj][self.__df['flag']>0]
        return self.__df[pocetak:kraj]
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
    

if __name__ == "__main__":
    data = citac.WlReader().citaj('./data/pj.csv')
    u1 = uredjaj.M100E()
    u2 = uredjaj.M100C()
    u1.pocetak=datetime(2000,1,1)
    u2.pocetak=datetime(2014,2,24,0,10)
    u1.kraj=datetime(2014,2,24,0,10)
    u2.kraj=datetime(2015,1,1)
    
    a = auto_validacija.AutoValidacija()
    a.dodaj_uredjaj(u2)
    a.dodaj_uredjaj(u1)
    a.validiraj(data['1-SO2-ppb'])
    
    ag = Agregator([u1,u2])
    ag.setDataFrame(data['1-SO2-ppb'])
    agregirani = ag.agregirajNiz()
    nizNizova = ag.nizNiz()

    plt.boxplot(nizNizova)
    plt.plot(agregirani['avg'])
    plt.plot(agregirani['q05'])
    plt.plot(agregirani['q95'])
    plt.show()