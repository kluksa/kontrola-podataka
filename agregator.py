# -*- coding: utf-8 -*-
"""
Agregator dio


"""
import pandas as pd
import numpy as np

#sluzi samo za lokalnu provjeru modula
import citac


class Agregator(object):
    def __init__(self):
        """
        mozda u buducnosti dozvoliti iniicjalizaciju nekih parametara.

        """
        pass
    
    """
    def pomocnih funkcija za agregator
    ulaz --> numpy array ili neka lista
    izlaz --> broj
    """
    def test_validacije(self, x):
        """
        test da li su svi unutar intervala validirani
        validairani minutni podatci imaju flag 1000 ili -1000
        """
        if len(x) == 0:
            return np.NaN
        total = True
        for ind in x:
            if abs(ind) != 1000:
                #postoji barem jedan minutni podatak koji nije validiran
                total = False
        
        if total == True:
            return 1000 #slucaj kada su svi minutni validirani
        else:
            return 1 #slucaj kada postoje nevalidirani podaci
    
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
        #provjera da li ulazni frame ima podataka
        #tj. postupak u slucaju da agregatoru netko prosljedi prazan slice
        if len(frejm) == 0:
            return None
        
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
        temp = dfKonc.resample('H', how = self.h_size, closed = 'right', label = 'right')
        agregirani[u'broj podataka'] = temp
        
        """
        agregirani status
        """
        tempDf = df.copy()
        dfStatus = tempDf[u'status']
        temp = dfStatus.resample('H', how = self.h_binary_or, closed = 'right', label = 'right')
        agregirani[u'status'] = temp
        
        """
        test validacije
        """
        tempDf = df.copy()
        dfFlag = tempDf[u'flag']
        temp = dfFlag.resample('H', how = self.test_validacije, closed = 'right', label = 'right')
        agregirani[u'flag'] = temp
        
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
            temp = temp.resample('H', how = listaFunkcija[i], closed = 'right', label = 'right')
            temp.name = listaFunkcijaIme[i]
            agregirani[temp.name] = temp
        
        """
        ???
        -iz agregiranih makni sve gdje je broj podataka np.NaN
        -desava se kada nedostaju mjerenja u sredini intervala
        """
        
        agregirani = agregirani[np.isnan(agregirani[u'broj podataka']) == False]

        
        #TODO!
        #treba testirati kako prati status validiranih
        #validirani i OK - flag=1000
        #validirani i prekratak niz valjanih - flag=-1000
        #nevalidirani i OK - flag=1
        #nevalidirani i prekratak niz valjanih - flag)-1
        """
        -provjeri da li je broj valjanih podataka sa flagom vecim od 0 veci od 45
        -ako nije... flagaj interval kao nevaljan...umetni placeholder vrijednosti
        """
        for i in agregirani.index:
            if np.isnan(agregirani.loc[i, u'count']) or agregirani.loc[i,u'count']<45:
                if agregirani.loc[i, u'flag'] == 1000:
                    agregirani.loc[i, u'flag'] = -1000
                else:
                    agregirani.loc[i,u'flag'] = -1
               
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
    frejm.loc['2014-06-04 16:00:00':'2014-06-04 19:00:00','flag'] = 1000
    frejm.loc['2014-06-04 20:00:00':'2014-06-04 22:00:00','flag'] = -1000
    frejm.loc['2014-06-04 08:00:00':'2014-06-04 13:00:00','flag'] = -1000
    #frejm = frejmovi['49-O3-ug/m3']
    
    #Inicijaliziraj agregator
    agregator = Agregator()
    #frejm = pd.DataFrame()
    #print(frejm)
    #agregiraj frejm
    agregirani = agregator.agregiraj_kanal(frejm)
    print(agregirani)
    
    #random sample da provjerim valjanost agregiranja
    #barem sto se tice slicea i rubova istih
    test = frejm.loc['2014-06-04 04:01:00':'2014-06-04 05:00:00','koncentracija']
    avg_test = np.mean(test)
    res_test = agregirani.loc['2014-06-04 05:00:00','avg']
    
    print('treba biti True, ako je sve u redu')
    print(avg_test == res_test)
    
    #test ponasanja ako agregator dobije prazan slice
    test_prazan = pd.DataFrame()
    test_agreg = agregator.agregiraj_kanal(test_prazan)
    print('prazan frejm:')
    print(test_agreg)
    