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
            #parse json i provjeri da li su svi relevantni stupci na broju
            df = pd.read_json(x, orient='records', convert_dates=['vrijeme'])
            assert 'vrijeme' in df.columns, 'ERROR - Nedostaje stupac: "vrijeme"'
            assert 'id' in df.columns, 'ERROR - Nedostaje stupac: "id"'
            assert 'vrijednost' in df.columns, 'ERROR - Nedostaje stupac: "vrijednost'
            assert 'statusString' in df.columns, 'ERROR - Nedostaje stupac: "statusString"'
            assert 'valjan' in df.columns, 'ERROR - Nedostaje stupac: "valjan"'

            df = df.set_index(df['vrijeme'])
            df['status'] = pd.Series(0, df.index)
            df.rename(columns={'vrijednost' : 'koncentracija', 'valjan' : 'flag'}, inplace = True)
            df['koncentracija'] = df['koncentracija'].map(self.nan_conversion)
            df['flag'] = df['flag'].map(self.valjan_conversion)
            df.drop('vrijeme', inplace = True, axis = 1) #drop column vrijeme
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
        #test da li su svi stupci u frejmu
        assert 'id' in frejm.columns, 'ERROR - Nedostaje stupac: "id"'
        assert 'koncentracija' in frejm.columns, 'ERROR - Nedostaje stupac: "koncentracija'
        assert 'statusString' in frejm.columns, 'ERROR - Nedostaje stupac: "statusString"'
        assert 'flag' in frejm.columns, 'ERROR - Nedostaje stupac: "flag"'
        assert 'status' in frejm.columns, 'ERROR - Nedostaje stupac: "status"'
        #rename i adapt frejm
        frejm['vrijeme'] = frejm.index
        frejm.rename(columns={'koncentracija':'vrijednost', 'flag':'valjan'}, inplace = True)
        frejm['valjan'] = frejm['valjan'].map(self.int_to_boolean) #TODO! missing func... check kontroler
        frejm.drop('status', inplace = True, axis = 1) #drop column status
        #convert to json string uz pomoc pandasa
        jstring = frejm.to_json(orient = 'records')
        #upload uz pomoc self.source objekta (networking_funkcjie.WebZahtjev)
        self.source.upload_json_minutnih(jstring)

    def write_agregirani(self, key = None, date = None, frejm = None):
        """
        Write metoda za upis agregiranih podataka na REST servis

        key --> kanal
        date --> string, datum formata 'YYYY-MM-DD'
        frejm --> slajs minutnog frejma
        """
        #test da li su svi stupci u frejmu
        assert 'broj podataka' in frejm.columns, 'ERROR - Nedostaje stupac: "broj podataka"'
        assert 'status' in frejm.columns, 'ERROR - Nedostaje stupac: "status"'
        assert 'flag' in frejm.columns, 'ERROR - Nedostaje stupac: "flag"'
        assert 'avg' in frejm.columns, 'ERROR - Nedostaje stupac: "avg"'
        assert 'std' in frejm.columns, 'ERROR - Nedostaje stupac: "std"'
        assert 'min' in frejm.columns, 'ERROR - Nedostaje stupac: "min"'
        assert 'max' in frejm.columns, 'ERROR - Nedostaje stupac: "max"'
        assert 'q05' in frejm.columns, 'ERROR - Nedostaje stupac: "q05"'
        assert 'q95' in frejm.columns, 'ERROR - Nedostaje stupac: "q95"'
        assert 'median' in frejm.columns, 'ERROR - Nedostaje stupac: "median"'
        assert 'count' in frejm.columns, 'ERROR - Nedostaje stupac: "count"'
        #rename and adapt frejm
        #frejm.drop([], inplace = True, axis = 1) #drop nebitne stupce
        frejm = frejm[['avg','status','count']] #zadrzi samo te stupce
        frejm['vrijeme'] = frejm.index
        frejm['programMjerenjaId'] = pd.Series(key, index=frejm.index)
        frejm.rename(columns = {'avg':'vrijednost', 'count':'obuhvat'}, inplace = True)
        frejm['obuhvat'] = frejm['obuhvat'].map(self.agregirani_count_to_postotak)
        #convert to json string uz pomoc pandasa
        jstring = frejm.to_json(orient = 'records')
        #upload uz pomoc self.source objekta (networking_funkcije.WebZahtjev)
        self.source.upload_json_agregiranih(jstring)

    def agregirani_count_to_postotak(self, x):
        """
        Pomocna funkcija za racunanje obuhvata agregiranih podataka
        P.S. definiran kao funkcija za koristenje u metodi map
        """
        return int(x*100/60)

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