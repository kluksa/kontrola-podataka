#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 17 15:18:10 2014

@author: User
"""
import logging

import pandas as pd
import numpy as np


###############################################################################
###############################################################################
class RESTReader(object):
    """
    implementacija REST json citaca
    obavezno instanciraj citac sa modelom
    """
    def __init__(self, source = None):
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
        try:
            """
            TODO! moguce je prosljediti keyword argument dtype={column name : type}
            funkciji pd.read_json() koja ce castati stupce u odredjeni tip prilikom
            citanja. Svi stupci koji nisu navedeni u dictu ce se automatski castati
            u 'najprikladniji' tip.
            """
            #parse json i provjeri da li su svi relevantni stupci na broju
            df = pd.read_json(x, orient='records', convert_dates=['vrijeme'])
            assert 'vrijeme' in df.columns, 'ERROR - Nedostaje stupac: "vrijeme"'
            assert 'id' in df.columns, 'ERROR - Nedostaje stupac: "id"'
            assert 'vrijednost' in df.columns, 'ERROR - Nedostaje stupac: "vrijednost'
            assert 'statusString' in df.columns, 'ERROR - Nedostaje stupac: "statusString"'
            assert 'valjan' in df.columns, 'ERROR - Nedostaje stupac: "valjan"'
            assert 'statusInt' in df.columns, 'ERROR - Nedostaje stupac: "statusInt"'

            df = df.set_index(df['vrijeme'])
            df.rename(columns={'vrijednost' : 'koncentracija', 'valjan' : 'flag', 'statusInt':'status'}, inplace = True)
            df['koncentracija'] = df['koncentracija'].map(self.nan_conversion)
            df['flag'] = df['flag'].map(self.valjan_conversion)
            df.drop('vrijeme', inplace = True, axis = 1) #drop column vrijeme
            #TODO!
            """
            Postaviti flag na drugu vrijednost ako je tocka prije validirana?
            Ovisi o statusu...
            """
            #vrati adaptirani dataframe
            return df
        except (ValueError, TypeError, AssertionError):
            #javi error signalom kontroleru da nesto nije u redu?
            logging.info('Fail kod parsanja json stringa:\n'+str(x), exc_info = True)
            df = pd.DataFrame( columns = ['koncentracija','status','flag','id','statusString'] )
            df = df.set_index(df['id'].astype('datetime64[ns]'))
            #vrati prazan frejm frejm
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
class RESTWriter(object):
    """
    Klasa zaduzena za updateanje agregiranih podataka na REST web servis
    """
    def __init__(self, source = None):
        #instanca Web zahtjeva za rest servise
        self.source = source

    def write_minutni(self, key = None, date = None, frejm = None):
        """
        Write metoda za upis minutnih podataka na REST servis

        key --> kanal
        date --> string, datum formata 'YYYY-MM-DD'
        frejm --> slajs minutnog frejma
        """
        #test da li su 'bitni' stupci u frejmu
        assert key != None, 'ERROR - Nedostaje program mjerenja'
        assert 'id' in frejm.columns, 'ERROR - Nedostaje stupac: "id"'
        assert 'flag' in frejm.columns, 'ERROR - Nedostaje stupac: "flag"'
        #rename i adapt frejm
        frejm.rename(columns={'flag':'valjan'}, inplace = True)
        frejm['valjan'] = frejm['valjan'].map(self.int_to_boolean)
        frejm.drop(['status', 'koncentracija', 'statusString'], inplace = True, axis = 1)
        #convert to json string uz pomoc pandasa
        jstring = frejm.to_json(orient = 'records')
        #upload uz pomoc self.source objekta (networking_funkcjie.WebZahtjev)
        self.source.upload_json_minutnih(jstring=jstring, program=key, date=date)

    def int_to_boolean(self, x):
        """
        Pomocna funkcija koja adaptira stupac 'valjan' (integeri) u boolean
        vrijednost. Ako je x vrijednost veca ili jednaka 0 vraca True,
        ako nije, vraca False
        """
        if x >= 0:
            return True
        else:
            return False
###############################################################################
###############################################################################