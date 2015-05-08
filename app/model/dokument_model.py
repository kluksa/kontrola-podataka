# -*- coding: utf-8 -*-
"""
Created on Wed Jan 21 14:45:37 2015

@author: User
"""

import pandas as pd
import datetime
from PyQt4 import QtCore
import numpy as np

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
    def __init__(self, reader = None, writer = None, agregator = None, parent = None):
        QtCore.QObject.__init__(self, parent)
        self.data = {}
        self.citac = reader
        self.pisac = writer
        self.agregator = agregator
        self.statusMap = {} #mapa statusa
        self.kontrolaBitPolozaj = None # polozaj bita statusa za predhodno validirane podatke
###############################################################################
    def set_statusMap(self, mapa):
        """
        Setter za opis bitova statusa.
        """
        self.statusMap = mapa
        for i in self.statusMap.keys():
            if self.statusMap[i] == 'KONTROLA_PROVEDENA':
                self.kontrolaBitPolozaj = i
###############################################################################
    def set_writer(self, writer):
        """
        Setter objekta writera u model.
        writer mora definirati metode:

        write_minutni(key = None, date = None, frejm = None)
            key --> kanal
            date --> string, datum formata 'YYYY-MM-DD'
            frejm --> slajs minutnog frejma

        write_agregirani(key = None, date = None, frejm = None)
            key --> kanal
            date --> string, datum formata 'YYYY-MM-DD'
            frejm --> slajs agregiranog frejma
        """
        self.pisac = writer
###############################################################################
    def set_reader(self, reader):
        """
        Setter objekta citaca u model.
        citac mora definirati:

        metodu: read(key = None, date = None)
            -uzima 2 keyword argumenta
            key --> kanal
            date --> datum string formata 'YYYY-MM-DD'
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
    def persist_minutne_podatke(self, key = None, date = None):
        """
        -key je kljuc pod kojim ce se spremiti podaci u mapu self.data
        -date je datum formata 'YYYY-MM-DD' koji se treba ucitati
        """
        #adapt time da uhvatis slajs (tmin, tmax)
        t = pd.to_datetime(date)
        tmin = t + datetime.timedelta(minutes=1)
        tmax = t + datetime.timedelta(days=1)
        #dohvati trazeni slajs
        frejm = self.get_frame(key = key, tmin = tmin, tmax = tmax)
#        testValidacije = frejm['flag'].map(self.test_stupnja_validacije)
#        lenSvih = len(testValidacije)
#        lenDobrih = len(testValidacije[testValidacije == True])
#        if lenSvih != lenDobrih:
#            tekst = 'Neki podaci nisu validirani.\nNije moguce spremiti minutne podatke na REST servis.'
#            raise pomocne_funkcije.AppExcept(tekst)
        #pozovi metodu pisaca za spremanje samo ako frejm nije prazan
        if len(frejm):
            self.pisac.write_minutni(key = key, date = date, frejm = frejm)
            #TODO! potrebno je promjeniti flag gdje treba u 1000 ili -1000 zbog vizualne identifikacije sto je otislo na rest?
        else:
            tekst = " ".join(['Podaci za', str(key), str(date), 'nisu ucitani. Prazan frejm'])
            raise pomocne_funkcije.AppExcept(tekst)
###############################################################################
    def pronadji_kontorlirane(self, x):
        """
        Pomocna funkcija da koja pronalazi podatke koji su predhodno validirani.
        Ulazni parametar x je status. Izlaz ja 1000 ako je kontrola prethodno
        obavljena, 1 ako nije.
        """
        value = int(x) & (1 << int(self.kontrolaBitPolozaj))
        if value > 0:
            return 1000
        else:
            return 1
###############################################################################
    def citaj(self, key = None, date = None):
        """
        -key je kljuc pod kojim ce se spremiti podaci u mapu self.data
        -date je datum formata 'YYYY-MM-DD' koji se treba ucitati
        """
        kljuc, df = self.citac.read(key = key, date = date)
        try:
            assert type(key) == int, 'Assert fail, ulazni kljuc nije tipa integer'
            self.dataframe_structure_test(df)
            df['status'] = df['status'].astype(np.int64)
            df['id'] = df['id'].astype(np.int64)
            if len(df):
                print(self.kontrolaBitPolozaj)
                print(self.statusMap.keys())
                if self.kontrolaBitPolozaj in self.statusMap.keys():
                    for i in df.index:
                        df.loc[i, 'flag'] = df.loc[i, 'flag'] * self.pronadji_kontorlirane(df.loc[i, 'status'])
                self.set_frame(key = kljuc, frame = df)
                #TODO!
                print(df)
            else:
                tekst = " ".join(['Podaci za', str(key), str(date), 'nisu ucitani. Prazan frejm'])
                raise pomocne_funkcije.AppExcept(tekst)
        except AssertionError as e:
            tekst = 'Frejm nije spremljen u model. DataModel.set_frame:Assert fail.\n{0}'.format(e)
            raise pomocne_funkcije.AppExcept(tekst) from e
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
        #BUG FIX approach 1.
        #recast 'statusString to str type
        frame['statusString'] = frame['statusString'].astype(str)
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
            #recast 'statusString to str type
            frame['statusString'] = frame['statusString'].astype(str)
            #create new key
            self.data[key] = frame
            self.data[key].sort()
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
            assert key is not None, 'dokument.get_frame:Assert fail, key = None'
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
    def test_stupnja_validacije(self, x):
        """
        Pomocna funkcija, provjerava da li je vrijednost 1000 ili -1000. Bitno za
        provjeru validacije stupca flag (da li su svi podaci validirani).
        """
        if abs(x) == 1000:
            return True
        else:
            return False
###############################################################################
###############################################################################