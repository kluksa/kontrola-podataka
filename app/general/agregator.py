# -*- coding: utf-8 -*-
"""
Agregator dio
"""
import pandas as pd
import numpy as np

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

    def my_mean(self, x):
        #mean, srednja vrjednost
        if len(x) == 0:
            return np.NaN
        return np.mean(x)

    def my_std(self, x):
        #standardna devijacija
        if len(x) == 0:
            return np.NaN
        return np.std(x)

    def my_min(self, x):
        #min
        if len(x) == 0:
            return np.NaN
        return np.min(x)

    def my_max(self, x):
        #max
        if len(x) == 0:
            return np.NaN
        return np.max(x)


    def h_q05(self, x):
        #5 percentil podataka
        if len(x) == 0:
            return np.NaN
        return np.percentile(x,5)

    def h_q50(self, x):
        #median
        if len(x) == 0:
            return np.NaN
        return np.percentile(x,50)

    def h_q95(self, x):
        #95 percentil podataka
        if len(x) == 0:
            return np.NaN
        return np.percentile(x,95)

    def h_binary_or(self, x):
        #binarni or liste
        if len(x) == 0:
            #za prazni interval, vrati -1 (ocita greska)
            return np.NaN
        result = 0
        for i in x:
            result = result | int(i)
        return result

    def h_size(self, x):
        #broj podataka
        if len(x) == 0:
            return np.NaN
        return len(x)

    def agregiraj(self, frejm):
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
        listaFunkcija = [self.my_mean, self.my_std, self.my_min, self.my_max, self.h_q05, self.h_q50, self.h_q95, self.h_size]

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

        """
        Problem prilikom agregiranja. ako sve indekse unutar jednog sata prebacimo
        da su lose, funkcije koje racunaju srednje vrijednosti isl. ne reazlikuju
        taj slucaj od nepostojecih podataka te uvijek vrate np.NaN (not a number).
        Potrebno je postaviti te intervale na neku vrijednost (recimo 0) da bi se
        prikazali na grafu.
        """
        for i in agregirani.index:
            if np.isnan(agregirani.loc[i, u'avg']) and agregirani.loc[i, u'broj podataka'] > 0:
                #ako je average np.nan i ako je broj podataka u intevalu veci od 0 (ima podataka)
                #postavi vrijenosti na 0 da se mogu prikazati
                agregirani.loc[i, u'avg'] = 0
                agregirani.loc[i, u'min'] = 0
                agregirani.loc[i, u'max'] = 0
                agregirani.loc[i, u'q05'] = 0
                agregirani.loc[i, u'q95'] = 0
                agregirani.loc[i, u'count'] = 0
                agregirani.loc[i, u'median'] = 0
                agregirani.loc[i, u'std'] = 0



        return agregirani

    def agregiraj_frejmove(self, frejmovi):
        """
        agregiraj rezultat kanal po kanal i spremaj u dict
        """
        rezultat = {}
        for i in frejmovi:
            frejm = frejmovi[i]
            rezultat[i] = self.agregiraj_kanal(frejm)

        return rezultat
