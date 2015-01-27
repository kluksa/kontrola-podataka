# -*- coding: utf-8 -*-
"""
Created on Wed Jan 21 14:45:37 2015

@author: User
"""

import pandas as pd
from PyQt4 import QtCore

import pomocneFunkcije
###############################################################################
###############################################################################
class DataModel(QtCore.QObject):
    """
    Data model aplikacije
    Podaci se spremaju u mapu datafrejmova {programMjerenja:DataFrame,...}
    programMjerenja je tipa int - vezan za programMjerenjaId u bazi
    
    struktura DataFrejma:
    index:
        -datetime index --> type : pd.tseries.index.DatetimeIndex
    stupci:
        -"koncentracija" --> dtype: np.float64
        -"status" --> dtype: np.float64
        -"flag" --> dtype: np.int64
    """
###############################################################################
    def __init__(self, parent = None):
        QtCore.QObject.__init__(self, parent)
        self.data = {}
###############################################################################
    def dataframe_structure_test(self, frame = None):
        """provjera da li je dataframe dobre strukture"""
        assert type(frame) == pd.core.frame.DataFrame, 'Assert fail, ulaz nije DataFrame objekt'
        assert type(frame.index) == pd.tseries.index.DatetimeIndex, 'Assert fail, DataFrame nema vremenski indeks'
        assert 'koncentracija' in list(frame.columns), 'Assert fail, nedostaje stupac koncentracija'
        assert 'status' in list(frame.columns), 'Assert fail, nedostaje stupac status'
        assert 'flag' in list(frame.columns), 'Assert fail, nedostaje stupac flag'
###############################################################################
    def set_frame(self, key = None, frame = None):
        """postavi frame u self.data pod kljucem key"""
        try:
            #provjera ulaznog parametra key
            assert type(key) == int, 'Assert fail, ulazni kljuc nije tipa integer'
            #provjeri ulazni frame
            self.dataframe_structure_test(frame)
            #dodaj na self.data
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
            else:
                #create new key
                self.data[key] = frame
                self.data[key].sort()
        except AssertionError as e:
            tekst = 'DataModel.set_frame:Assert fail.\n{0}'.format(e)
            raise pomocneFunkcije.AppExcept(tekst) from e
###############################################################################
    def get_frame(self, key = None, tmin = None, tmax = None):
        """funkcija dohvaca trazeni slice frejma"""
        try:
            assert key != None, 'dokument.get_frame:Assert fail, key = None'
            assert isinstance(tmin, pd.tslib.Timestamp), 'dokument.get_frame:Assert fail, krivi tip tmin'
            assert isinstance(tmax, pd.tslib.Timestamp), 'dokument.get_frame:Assert fail, krivi tip tmin'
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
        except (LookupError, TypeError, AssertionError) as e1:
            tekst = 'DataModel.get_frame:Lookup/Type fail.\n{0}'.format(e1)
            raise pomocneFunkcije.AppExcept(tekst) from e1
###############################################################################
    def notify_about_change(self):
        """Funkcija emitira specificni signal da je doslo do promjene u flaga."""
        self.emit(QtCore.SIGNAL('model_flag_changed'))
###############################################################################
    def change_flag(self, key = None, tmin = None, tmax = None, flag = 0):
        """Promjena flaga za zadani vremenski interval"""
        try:
            if tmin > tmax:
                tmin, tmax = tmax, tmin        
            #direktno promjeni flag u zadanom intervalu
            self.data[key].loc[tmin:tmax, u'flag'] = flag
            #objavi svima koji slusaju da je doslo do promjene
            self.notify_about_change()
        except (LookupError, TypeError) as e1:
            tekst = 'DataModel.change_flag:Lookup/Type fail.\n{0}'.format(e1)
            raise pomocneFunkcije.AppExcept(tekst) from e1
###############################################################################
###############################################################################