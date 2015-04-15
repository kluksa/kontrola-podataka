#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 17 15:18:10 2014

@author: User
"""
import logging
import pandas as pd
import numpy as np
import datetime
from PyQt4 import QtCore

import app.general.pomocne_funkcije as pomocne_funkcije

###############################################################################
###############################################################################
class RESTReader(QtCore.QObject):
    """
    implementacija REST json citaca
    obavezno instanciraj citac sa modelom
    """
    def __init__(self, model = None, source = None):
        QtCore.QObject.__init__(self)
        #instance of model
        self.model = model
        #instanca Web zahtjeva za rest servise
        self.source = source
        #cache uspjesnih zahtjeva za citanjem podataka
        self.uspjesnoUcitani = []
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
    def status_string_conversion(self, x):
        """
        Adapter, funkcija uzima string vrijednost status stringa i pretvara je
        u ????
        U nedostatku bolje ideje... string je formata 'a;b;c;d'
        funkcija ce vratiti int(d)
        """
        ind = x.rfind(';')
        x = x[ind+1:]
        return int(x)
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
        df.index = df['id'].astype('datetime64[ns]')

        try:
            #parse json i provjeri da li su svi relevantni stupci na broju
            df = pd.read_json(x, orient='records', convert_dates=['vrijeme'])
            assert 'vrijeme' in frame.columns, 'ERROR - Nedostaje stupac: "vrijeme"'
            assert 'id' in frame.columns, 'ERROR - Nedostaje stupac: "id"'
            assert 'vrijednost' in frame.columns, 'ERROR - Nedostaje stupac: "vrijednost'
            assert 'statusString' in frame.columns, 'ERROR - Nedostaje stupac: "statusString"'
            assert 'valjan' in frame.columns, 'ERROR - Nedostaje stupac: "valjan"'

            df = df.set_index(df['vrijeme'])
            df['status'] = pd.Series(0, df.index)
            df.rename(columns={'vrijednost' : 'koncentracija'})
            df['vrijednost'] = df['vrijednost'].map(self.nan_conversion)
            df['valjan'] = df['valjan'].map(self.valjan_conversion)

            # #zamjeni index u pandas timestamp (prebaci stupac vrijeme u index)
            # noviIndex = frame['vrijeme']
            # frame.index = noviIndex
            # #sacuvaj originalni id podatka (pod kojim je spremljen u bazu)
            # podatakId = frame['id']
            # #dohvati koncentraciju, zamjeni niske koncentracije sa np.nan
            # koncentracija = frame['vrijednost'].astype(np.float64)
            # koncentracija = koncentracija.map(self.nan_conversion)
            # #dohvati status i adaptiraj ga (sacuvaj i originalnu kopiju)
            # statusString = frame['statusString']
            # status = 0
            # #adapter za boolean vrijesnost valjan  (buduci flag)
            # valjan = frame['valjan']
            # valjan = valjan.map(self.valjan_conversion)
            # valjan = valjan.astype(np.int64)
            #
            # #sklopi izlazni dataframe da odgovara API-u dokumenta
            # df = pd.DataFrame({'koncentracija':koncentracija,
            #                    'status':status,
            #                    'flag':valjan,
            #                    'id':podatakId,
            #                    'statusString':statusString})

        except (ValueError, AssertionError):
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
        """
        sada = datetime.datetime.now()
        sada = str(sada.date()) #samo trenutni datum u string formatu
        if (key, date) not in self.uspjesnoUcitani:
            try:
                #pokusaj ucitati json string sa REST servisa
                jsonString = self.source.get_sirovi(key, date) #!potencijalni AppExcept!
                #pretvori u dataframe
                df = self.adaptiraj_ulazni_json(jsonString)
                #upisi frejm u model
                self.model.set_frame(key = key, frame = df)
                #dodaj na popis uspjesno ucitanih date nije danas
                if date is not sada and len(df):
                    #dodaj na uspjesno ucitane samo ako je datum manji od danas
                    #i ako frejm nije prazan
                    self.uspjesnoUcitani.append((key, date))
            except pomocne_funkcije.AppExcept as err:
                """
                Moguci razlozi za Exception
                - prilikom ucitavanja jsona (self.source.get_sirovi)
                - prilikom upisa datafrejma u model (self.model.set_frame)
                """
                logging.error('read data fail', exc_info = True)
                #potrebno je javiti problem kontroleru aplikacije
                self.emit(QtCore.SIGNAL('error_message(PyQt_PyObject)'), err)
###############################################################################
###############################################################################
class RESTWriterAgregiranih(QtCore.QObject):
    """
    Klasa zaduzena za updateanje agregiranih podataka na REST web servis
    """
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