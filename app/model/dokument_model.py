# -*- coding: utf-8 -*-
"""
Created on Wed Jan 21 14:45:37 2015

@author: User
"""

import pandas as pd
from PyQt4 import QtCore

import app.general.pomocne_funkcije as pomocne_funkcije
###############################################################################
###############################################################################
class DataModel(QtCore.QObject):
    """
    Subklasan QtCore.QObject radi emita u metodi self.change_flag()

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
        -"id" --> dtype : int
        -"statusString" -->dtype : string
    """
###############################################################################
    def __init__(self, reader = None, agregator = None, parent = None):
        QtCore.QObject.__init__(self, parent)
        self.data = {}
        self.citac = reader
        self.agregator = agregator
###############################################################################
    def set_reader(self, reader):
        """
        Setter objekta citaca u model.
        citac mora definirati:

        metodu: read(*args, **kwargs)
            -uzima varijiablini broj ulaznih podataka
            -MORA vratiti tuple
                (kljuc pod kojim se podatak zapisuje u dokument, dobro formatirani dataframe)
        """
        self.citac = reader
###############################################################################
    def set_agregator(self, agreg):
        """
        Setter objekta agregatora u model. Agregator mora imati metodu agregiraj
        koja uzima 'minutni' frejm i vraca satno agregirani frame.
        """
        self.agregator = agreg
###############################################################################
    def citaj(self, key = None, date = None):
        """
        -key je kljuc pod kojim ce se spremiti podaci u mapu self.data
        -date je datum formata 'YYYY-MM-DD' koji se treba ucitati

        Ovisno o tipu citaca koji je trenutno aktivan, razlikuje se i poziv metode
        """
        kljuc, df = self.citac.read(key = key, date = date)
        if len(df):
            self.set_frame(key = kljuc, frame = df)
###############################################################################
    def dataframe_structure_test(self, frame):
        """provjera da li je dataframe dobre strukture"""
        assert type(frame) == pd.core.frame.DataFrame, 'Assert fail, ulaz nije DataFrame objekt'
        assert type(frame.index) == pd.tseries.index.DatetimeIndex, 'Assert fail, DataFrame nema vremenski indeks'
        assert 'koncentracija' in list(frame.columns), 'Assert fail, nedostaje stupac koncentracija'
        assert 'status' in list(frame.columns), 'Assert fail, nedostaje stupac status'
        assert 'flag' in list(frame.columns), 'Assert fail, nedostaje stupac flag'
        assert 'id' in list(frame.columns), 'Assert fail, nedostaje stupac id'
        assert 'statusString' in list(frame.columns), 'Assert fail, nedostaje stupac statusString'
###############################################################################
    def set_frame(self, key = None, frame = None):
        """postavi frame u self.data pod kljucem key"""
        try:
            #provjera ulaznog parametra key
            assert type(key) == int, 'Assert fail, ulazni kljuc nije tipa integer'
            #provjeri ulazni frame
            self.dataframe_structure_test(frame)
            #SORT DATAFRAME
            frame.sort_index(inplace = True)
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
                    on = ['koncentracija', 'status', 'flag', 'id', 'statusString'])
                #update values
                self.data[key].update(frame)
                self.data[key].sort()
            else:
                #create new key
                self.data[key] = frame
                self.data[key].sort()
        except AssertionError as e:
            tekst = 'DataModel.set_frame:Assert fail.\n{0}'.format(e)
            raise pomocne_funkcije.AppExcept(tekst) from e
###############################################################################
    def dohvati_minutne_frejmove(self, lista = None, tmin = None, tmax = None):
        """
        Funkcija vraca mapu minutnih slajsova. Ulazni parametar je lista kljuceva
        i vremenske granice slajsa.
        """
        out = {}
        for kljuc in lista:
            if kljuc in self.data.keys():
                out[kljuc] = self.get_frame(key = kljuc, tmin = tmin, tmax = tmax)
        return out
###############################################################################
    def dohvati_agregirane_frejmove(self, lista = None, tmin = None, tmax = None):
        """
        Funkcija vraca mapu minutnih slajsova. Ulazni parametar je lista kljuceva
        i vremenske granice slajsa.
        """
        out = {}
        for kljuc in lista:
            if kljuc in self.data.keys():
                out[kljuc] = self.get_agregirani_frame(key = kljuc, tmin = tmin, tmax = tmax)
        return out
###############################################################################
    def get_frame(self, key = None, tmin = None, tmax = None):
        """funkcija dohvaca trazeni slice frejma"""
        try:
            assert key != None, 'dokument.get_frame:Assert fail, key = None'
            assert isinstance(tmin, pd.tslib.Timestamp), 'dokument.get_frame:Assert fail, krivi tip tmin'
            assert isinstance(tmax, pd.tslib.Timestamp), 'dokument.get_frame:Assert fail, krivi tip tmin'
            #za svaki slucaj provjeri da li je min i max ok, ako nije zamjeni ih
            if tmin > tmax:
                tmin, tmax = tmax, tmin
            #napravi kopiju cijelog frejma
            df = self.data[key].copy()
            #makni sve podatke koji su manji od donje granice
            df = df[df.index >= tmin]
            #makni sve podatke koji su veci od tMax
            df = df[df.index <= tmax]
            #vrati dobiveni slice - potencijalo prazan dataframe
            return df
        except (LookupError, TypeError, AssertionError) as e1:
            tekst = 'DataModel.get_frame:Lookup/Type fail.\n{0}'.format(e1)
            raise pomocne_funkcije.AppExcept(tekst) from e1
###############################################################################
    def get_agregirani_frame(self, key = None, tmin = None, tmax = None):
        """metoda dohvaca trazeni slajs, agregira ga te vraca agregirani frejm"""
        frejm = self.get_frame(key = key, tmin = tmin, tmax = tmax)
        return self.agregator.agregiraj(frejm)
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
            raise pomocne_funkcije.AppExcept(tekst) from e1
###############################################################################
###############################################################################