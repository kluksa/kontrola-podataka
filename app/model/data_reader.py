#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 17 15:18:10 2014

@author: User
"""
import logging
import pandas as pd
import numpy as np
from PyQt4 import QtCore

import app.general.pomocne_funkcije as pomocne_funkcije

###############################################################################
###############################################################################
class RESTReader():
    """
    implementacija REST json citaca
    obavezno instanciraj citac sa modelom
    """
    def __init__(self, source = None):
        QtCore.QObject.__init__(self)
        #instanca Web zahtjeva za rest servise
        self.source = source
###############################################################################
    def valjan_conversion(self, x):
        """
        Adapter, funkcija uzima boolean vrijednost i pretvara je u
        1 (True) ili -1 (False)
        """
        if x:
            return 1
        else:
            return -1
###############################################################################
    def nan_conversion(self, x):
        """
        Adapter, funkcija mjenja besmisleno male vrijednosti u NaN. Sto je
        besmisleno malo? recimo sve vrijednosti ispod -99
        """
        if x > -99:
            return x
        else:
            return np.NaN
###############################################################################
    def adaptiraj_ulazni_json(self, x):
        """
        Adapter za ulazni jason string.
        Potrebno je lagano preurediti frame koji se ucitava iz jsona

        output je pandas dataframe (prazan frame ako nema podataka)
        """
        #prazan dobro formatirani dataframe
        df = pd.DataFrame( columns = ['koncentracija','status','flag','id','statusString'] )
        df = df.set_index(df['id'].astype('datetime64[ns]'))

        try:
            #parse json i provjeri da li su svi relevantni stupci na broju
            df = pd.read_json(x, orient='records', convert_dates=['vrijeme'])
            assert 'vrijeme' in df.columns, 'ERROR - Nedostaje stupac: "vrijeme"'
            assert 'id' in df.columns, 'ERROR - Nedostaje stupac: "id"'
            assert 'vrijednost' in df.columns, 'ERROR - Nedostaje stupac: "vrijednost'
            assert 'statusString' in df.columns, 'ERROR - Nedostaje stupac: "statusString"'
            assert 'valjan' in df.columns, 'ERROR - Nedostaje stupac: "valjan"'

            df = df.set_index(df['vrijeme'])
            df['status'] = pd.Series(0, df.index)
            df.rename(columns={'vrijednost' : 'koncentracija'})
            df['vrijednost'] = df['vrijednost'].map(self.nan_conversion)
            df['valjan'] = df['valjan'].map(self.valjan_conversion)
        except (ValueError, TypeError, AssertionError):
            #javi error signalom kontroleru da nesto nije u redu?
            logging.info('Fail kod parsanja json stringa:\n'+str(x), exc_info = True)
        #vrati adaptirani dataframe
        return df
###############################################################################
    def read(self, key = None, date = None):
        """
        ucitavanje json podataka sa rest servisa.
        key je programMjerenja
        date je trazeni datum

        P.S. self.source.get_sirovi(key, date) moze raisati exception (usljed loseg
        requesta, loseg responsea...), ali dopustamo da se pogreska propagira
        iznad
        """
        #pokusaj ucitati json string sa REST servisa
        jsonString = self.source.get_sirovi(key, date)
        #pretvori u dataframe
        df = self.adaptiraj_ulazni_json(jsonString)
        return key, df
###############################################################################
###############################################################################
class RESTWriterAgregiranih(QtCore.QObject):
    """
    Klasa zaduzena za updateanje agregiranih podataka na REST web servis
    """
    #TODO! visak... prebaciti funkcionalnost direktno na kontroler direktnim pozivom
    def __init__(self, source = None):
        #instanca Web zahtjeva za rest servise
        QtCore.QObject.__init__(self)
        self.source = source

    def upload_agregirane(self, jso = None):
        """
        Ova funkcija zaduzena je za upisivanje json stringa agregiranih u REST web servis.
        """
        try:
            self.source.upload_json_agregiranih(jso)
        except pomocne_funkcije.AppExcept as err:
            """
            Moguci razlozi za Exception
            -prilikom uploada na REST
            """
            logging.error('write data fail', exc_info = True)
            #potrebno je javiti problem kontroleru aplikacije
            self.emit(QtCore.SIGNAL('error_message(PyQt_PyObject)'), err)

    def upload_minutne(self, jso = None):
        """
        Ova funkcija zaduzena je za upisivanje json stringa minutnih u REST web servis.
        """
        try:
            self.source.upload_json_minutnih(jso)
        except pomocne_funkcije.AppExcept as err:
            """
            Moguci razlozi za Exception
            -prilikom uploada na REST
            """
            logging.error('write data fail', exc_info = True)
            #potrebno je javiti problem kontroleru aplikacije
            self.emit(QtCore.SIGNAL('error_message(PyQt_PyObject)'), err)
###############################################################################
###############################################################################