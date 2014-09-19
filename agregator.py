# -*- coding: utf-8 -*-
"""
Agregator dio


"""
import pandas as pd
import numpy as np

#sluzi samo za lokalnu provjeru modula
import citac


class Agregator(object):
    """
    def pomocnih funkcija za agregator
    ulaz --> numpy array ili neka lista
    izlaz --> broj
    """
    def h_q05(self, x):
        #5 percentil podataka
        if len(x) == 0:
            #za prazni interval, vrati NaN vrijednost
            return np.NaN
        return np.percentile(x,5)
        
    def h_q50(self, x):
        #median
        if len(x) == 0:
            #za prazni interval, vrati NaN vrijednost
            return np.NaN
        return np.percentile(x,50)
        
    def h_q95(self, x):
        #95 percentil podataka
        if len(x) == 0:
            #za prazni interval, vrati NaN vrijednost
            return np.NaN
        return np.percentile(x,95)
    
    def h_binary_or(self, x):
        #binarni or liste
        if len(x) == 0:
            #za prazni interval, vrati NaN vrijednost
            return np.NaN
        result = 0
        for i in x:
            result = result | int(i)
        return result
        
    def h_size(self, x):
        #broj podataka
        if len(x) == 0:
            #za prazni interval, vrati NaN vrijednost
            return np.NaN
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
        #izbaci sve indekse gdje je koncentracija NaN
        df = frejm[np.isnan(frejm[u'koncentracija']) == False]
        
        tempDf = df.copy()
        #uzmi samo pandas series koncentracije
        dfKonc = tempDf[u'koncentracija']
        #resample series, prebroji koliko ima podataka
        temp = dfKonc.resample('H', how = self.h_size)
        agregirani[u'broj podataka'] = temp
        
        """
        agregirani status
        """
        tempDf = df.copy()
        dfStatus = tempDf[u'status']
        temp = dfStatus.resample('H', how = self.h_binary_or)
        agregirani[u'status'] = temp
        
        """
        -definicija funkcija koje nas zanimaju
        -funkcije moraju imati kao ulaz listu ili numpy array, izlaz je broj
        """
        listaFunkcijaIme = [u'avg', u'std', u'min', u'max', u'q05', u'median', u'q95', u'count']
        listaFunkcija = [np.mean, np.std, np.min, np.max, self.h_q05, self.h_q50, self.h_q95, self.h_size]
        
        """
        -kopija originalnog frejma
        -samo stupac koncentracije gdje je flag veci od 0
        """
        tempDf = df.copy()
        tempDf = tempDf[tempDf[u'flag']>=0]
        tempDf = tempDf[u'koncentracija']
        
        """
        -glavna petlja za agregiranje
        -loop preko lista funkcija
        """
        for i in list(range(len(listaFunkcija))):
            temp = tempDf.copy()
            temp = temp.resample('H', how = listaFunkcija[i])
            temp.name = listaFunkcijaIme[i]
            agregirani[temp.name] = temp
        
        """
        ???
        -iz agregiranih makni sve gdje je broj podataka np.NaN
        -desava se kada nedostaju mjerenja u sredini intervala
        """
        
        agregirani = agregirani[np.isnan(agregirani[u'broj podataka']) == False]
        
        """
        -provjeri da li je broj valjanih podataka sa flagom vecim od 0 veci od 45
        -ako nije... flagaj interval kao nevaljan...umetni placeholder vrijednosti
        """
        for i in agregirani.index:
            if agregirani.loc[i,u'count']<45:
                agregirani.loc[i,u'avg'] = -1
                agregirani.loc[i,u'std'] = -1
                agregirani.loc[i,u'min'] = -1
                agregirani.loc[i,u'max'] = -1
                agregirani.loc[i,u'q05'] = -1
                agregirani.loc[i,u'q95'] = -1
                agregirani.loc[i,u'median'] = -1
               
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


if __name__ == "__main__":
    citac = citac.WlReader('./data/')
    citac.dohvati_sve_dostupne()
    stanica = 'plitvicka jezera'
    datum = '20140604'
    datum = pd.to_datetime(datum)
    datum = datum.date()
    frejmovi = citac.citaj(stanica, datum)
    #jedan frejm    
    frejm = frejmovi['1-SO2-ppb']
    #frejm = frejmovi['49-O3-ug/m3']
    
    #Inicijaliziraj agregator
    agregator = Agregator()
    
    #agregiraj frejm
    agregirani = agregator.agregiraj_kanal(frejm)
    print(agregirani)