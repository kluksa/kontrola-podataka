#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 17 12:30:59 2014

@author: User
Model za aplikaciju.
Sto jednostavnije to bolje, zaduzen samo za prihvat datafrejmova, 
vracanje trazenih slajsova, promjene podataka u stupcu flag te slanje
opcenite informacije da je doslo do promjene na flagovima.

Cilj je totalno odvojiti model od ostatka aplikacije.
"""
import pandas as pd
from PyQt4 import QtCore

class DataModel(QtCore.QObject):
    """
    Data model aplikacije
    Podaci se spremaju u mapu datafrejmova {programMjerenja:DataFrame,...}
    
    struktura DataFrejma:
    index:
        -datetime index --> type : pd.tseries.index.DatetimeIndex
    stupci:
        -"koncentracija" --> dtype: np.float64
        -"status" --> dtype: np.float64
        -"flag" --> dtype: np.int64
    """
    def __init__(self, parent = None):
        QtCore.QObject.__init__(self, parent)
        self.data = {}
                        
    def dataframe_structure_test(self, frame = None):
        """
        Funkcija provjerava ispravnost strukture frejma.
        Vraca True ili False ovisno o rezultatu provjere.
        Provjerava:
        1. da li je frame tipa DataFrame
        2. da li je indeks framea datetime
        3. da li postoje stupci 'koncentracija', 'status', 'flag'
        """
        #1. frame mora biti DataFrame objekt
        if type(frame) != pd.core.frame.DataFrame:
            return False
        #2 indeks DataFrame objekta mora biti DatetimeIndex
        if type(frame.index) != pd.tseries.index.DatetimeIndex:
            return False
        #3 moraju postojati stupci 'koncentracija', 'status', 'flag'
        prisutniStupci = list(frame.columns)
        trazeniStupci = [u'koncentracija', u'status', u'flag']
        for stupac in trazeniStupci:
            if stupac not in prisutniStupci:
                return False
        #ako ga niti jedan test prije ne izbaci vrati da je sve u redu
        return True
        
    def set_frame(self, key = None, frame = None):
        """
        Za zadani kljuc (programMjerenjaId) i frame upisuje/updatea
        dict self.data.
        Vraca:
            -True : ako je frame uspjesno dodan u self.data
            -False: ako frame nije uspjesno dodan u self.data
        """
        #test za ispravnost ulaznog datafrejma
        if not self.dataframe_structure_test(frame):
            return False
        if key in self.data.keys():
            #merge
            self.data[key] = pd.merge(
                self.data[key], 
                frame, 
                how = 'outer', 
                left_index = True, 
                right_index = True, 
                sort = True, 
                on = ['koncentracija', 'status', 'flag'])
            #update values
            self.data[key].update(frame)
            self.data[key].sort()
            return True
        else:
            #create new key
            self.data[key] = frame
            self.data[key].sort()
            return True
            
    def get_frame(self, key = None, tmin = None, tmax = None):
        """
        Funkcija vraca kopiju slicea framea unutar vremenskih granica.
        Vremenske granice tmin i tmax su ukljucene u interval.
        
        tmin, tmax moraju biti pandas timestamp (pd.tslib.Timestamp)
        key mora biti valjan
        
        funkcija vraca trazeni slice ili None (ako su argumenti krivi)
        
        POTENCIJALNI OUTPUT!
        None --> krivi ulazni parametri
        dataframe --> moguce prazan dataframe ako nema podataka u intervalu
        """
        #validacija ulaznih parametara
        if type(tmin) != pd.tslib.Timestamp:
            return None
        if type(tmax) != pd.tslib.Timestamp:
            return None
        if key not in self.data.keys():
            return None
        #napravi kopiju cijelog frejma
        df = self.data[key].copy()
        #za svaki slucaj provjeri da li je min i max ok, ako nije zamjeni ih
        if tmin > tmax:
            tmin, tmax = tmax, tmin
        #makni sve podatke koji su manji od donje granice
        df = df[df.index >= tmin]
        #makni sve podatke koji su veci od tMax
        df = df[df.index <= tmax]
        #vrati dobiveni slice
        return df
        
    def notify_about_change(self):
        """
        Funkcija emitira specificni signal da je doslo do promjene u flagu.    
        """
        self.emit(QtCore.SIGNAL('model_flag_changed'))
                
    def change_flag(self, key = None, tmin = None, tmax = None, flag = 0):
        """        
        Funkcija mjenja vrijednost stupca flag unutar zadanog vremenskog 
        intervala.
        funkcija vraca True ako sve bude OK, False inace
        """
        #validacija ulaznih parametara
        if type(tmin) != pd.tslib.Timestamp:
            return False
        if type(tmax) != pd.tslib.Timestamp:
            return False
        if key not in self.data.keys():
            return False
        if type(flag) != int:
            return False        
        #za svaki slucaj provjeri da li je min i max ok, ako nije zamjeni ih
        if tmin > tmax:
            tmin, tmax = tmax, tmin        
        #direktno promjeni flag u zadanom intervalu
        self.data[key].loc[tmin:tmax, u'flag'] = flag
        #objavi svima koji slusaju da je doslo do promjene
        self.notify_about_change()
        return True