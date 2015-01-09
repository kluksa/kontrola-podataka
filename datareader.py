#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 17 15:18:10 2014

@author: User
"""
import os
import pandas as pd
import numpy as np

import datamodel
import networking_funkcije
###############################################################################
###############################################################################
class RESTReader():
    """
    implementacija REST json citaca
    obavezno instanciraj citac sa modelom
    """
    def __init__(self, model = None, source = None):
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
        adapter za ulazni jason string.
        Potrebno je lagano preurediti frame koji se ucitava iz jsona
        """
        frame = pd.read_json(x, orient='records', convert_dates=['vrijeme'])
        #zamjeni index u pandas timestamp (prebaci stupac vrijeme u index)
        noviIndex = frame['vrijeme']
        frame.index = noviIndex
        #dohvati koncentraciju
        koncentracija = frame['vrijednost'].astype(np.float64)
        koncentracija = koncentracija.map(self.nan_conversion)
        #dohvati status i adaptiraj ga
        status = frame['statusString']
        status = status.map(self.status_string_conversion)
        status = status.astype(np.float64)
        #adapter za boolean vrijesnost valjan  (buduci flag)
        valjan = frame['valjan']
        valjan = valjan.map(self.valjan_conversion)
        valjan = valjan.astype(np.int64)
        #sklopi izlazni dataframe da odgovara API-u dokumenta
        df = pd.DataFrame({u'koncentracija':koncentracija, 
                           u'status':status, 
                           u'flag':valjan})
        #vrati adaptirani dataframe
        return df
###############################################################################
    def read(self, key = None, date = None):
        """
        key je programMjerenja
        date je trazeni datum
        
        vraca True ako je upis u model prosao OK, 
        False u suprotnom slucaju
        """
        if self.model == None or self.source == None:
            print('reader nije dobro inicijaliziran')
            return False
#        url = self.baza + self.resursi["siroviPodaci"] + '/' + str(key) + '/' + str(date)
#        payload = {"id":"getJson", "name":"GET"}        
        if (key, date) not in self.uspjesnoUcitani:
            #zahtjev prije nije odradjen, pokusaj ucitati
            json = self.source.get_sirovi(key, date)
            if json != None:
                #provjera da li json sadrzi podatke, moguci response '[]'
                if len(json) > 3:
                    df = self.adaptiraj_ulazni_json(json)
                else:
                    print("prazan json string tj. samo '[]', nije upisan u model")
                    return False
                
                test = self.model.set_frame(key = key, frame = df)
                if test:
                    self.uspjesnoUcitani.append((key, date))
                    print('uspjesno upisan u model')
                    return True
                else:
                    print('neki fail, nije upisan u model')
                    return False
            else:
                print('neki fail sa request.get_sirovi, vratio je None')
        else:
            print('zahtjev je prije odradjen i spremljenu dokument')
            return True
###############################################################################
###############################################################################
class FileReader():
    """
    Ovaj citac ucitava csv fileove, te ih pokusava smisleno dodati u model.
    Inicijalizira se sa instancom modela i sa dictom za pretvorbu.
    
    Dict za pretvorbu je nested. U prvom djelu naziv stanice je kljuc za drugi dict.
    Unutarnji dict za kljuc ima string dobiven kombinacijom formule i mjerne jedinice, 
    npr. 'SO2-ug/m3' ili 'RH-%'. Pod tim kljucem se nalazi int programaMjerenjaId.
    
    npr.
    {'Slavonski Brod 2':{'H2S-ug/m3':162, ...}, ...}
    
    """
    def __init__(self, model = None, mapa = None):
        #instanciranje sa modelom
        self.model = model
        #instanciranje sa mapom konverzije
        self.mapa = mapa
        #popis uspjesno ucitanih fileova
        self.uspjesnoUcitani = []
###############################################################################
    def read(self, path = None):
        """
        Ucitaj csv file sa filesistema. Path je full path do trazenog filea
        """
        #provjerava argument
        if path == None:
            print('zadaj full file path do filea')
            return False
        #provjera da li je file prije ucitan
        if path in self.uspjesnoUcitani:
            print('file je vec ucitan, skip rest')
            return True
        #dohvati ime postaje u lowercaseu
        direcotry, file = os.path.split(path)
        postaja = file.split('-')[0].lower()
        
        dozvoljenePostaje = list(self.mapa.keys())
        if postaja in dozvoljenePostaje:
            #ucitaj csv file
            df = pd.read_csv(
                path, 
                na_values = '-999.00', 
                index_col = 0, 
                parse_dates = [[0,1]], 
                dayfirst = True, 
                header = 0, 
                sep = ',', 
                encoding = 'iso-8859-1')        
            #sklopi frejmove za sve kanale
            headerList = df.columns.values
            frejmovi = {}
            for i in range(0,len(headerList)-2,2):
                colName = headerList[i]
                #test da li se frame moze upisati
                for plin in self.mapa[postaja].keys():
                    if plin in colName:
                        #dohvati program mjerenja
                        progMjer = self.mapa[postaja][plin]
                        frejm = df.iloc[:,i:i+2]
                        
                        indeks = frejm.index
                        flagSeries = pd.Series(0, index = indeks, dtype = np.int64)
                        koncentracija = frejm.iloc[:,0].astype(np.float64)
                        status = frejm.iloc[:,1].astype(np.float64)
                        #dodaj frame u dict ucitanih valjanih frejmova
                        frejmovi[progMjer] = pd.DataFrame({u'koncentracija':koncentracija, 
                                                           u'status':status, 
                                                           u'flag':flagSeries})
            #U ovom trenu frejmovi sadrze sve valjane datafrejmove
            upisani = []
            if len(frejmovi.keys()) == 0:
                print('niti jedan kanal nije uspjesno pretvoren u program mjerenja')
                return False

            for key in frejmovi:
                #dodavanje u model
                t = self.model.set_frame(key = int(key), frame = frejmovi[key])
                if t:
                    upisani.append(str(key))
            
            if len(upisani) > 0:
                print('uspjesno upisani programi mjerenja: ', upisani)
                self.uspjesnoUcitani.append(path)
                return True
            else:
                print('niti jedan kanal nije uspjesno upisan u model')
                return False                
        else:
            print('Postaju nije moguce upisati')
            return False        
###############################################################################
    def read_path_list(self, pathList = None):
        """
        Ucitavanje vise csv fileova, zadanih u listi pathList
        """
        for fajl in pathList:
            t = self.read(path = fajl)
            if t:
                print(fajl, ' -->uspjesno ucitan')
            
###############################################################################
###############################################################################
class RESTWriterAgregiranih():
    """
    Klasa zaduzena za updateanje agregiranih podataka na REST web servis
    """
    def __init__(self, source = None):
        #instanca Web zahtjeva za rest servise
        self.source = source
    def upload(self, jso = None):
        """
        ova funkcija zaduzena je za upisivanje json stringa u REST web servis.
        """
        provjera = self.source.upload_json_agregiranih(jso)
        if provjera:
            print('upjesno spremljen na rest')
###############################################################################
###############################################################################

if __name__ == '__main__':
    baza = "http://172.20.1.166:9090/SKZ-war/webresources/"
    resursi = {"siroviPodaci":"dhz.skz.rs.sirovipodaci", 
               "programMjerenja":"dhz.skz.aqdb.entity.programmjerenja"}
    #web zahtjev objekt!
    wz = networking_funkcije.WebZahtjev(baza, resursi)
    #pomocna funkcija, stvara transformacijsku mapu koja treba file readeru
    def make_transformation_dict(webzahtjev):
        """bitno za konverziju FileReadera, POSTAJA MORA BITI LOWERCASE!!!
       radi nekonzistentnog pisanja podataka u fileovima i u bazi"""        
        basemap = webzahtjev.get_sve_programe_mjerenja()
        mapa1 = {}
        mapa2 = {}       
        for key in basemap.keys():
            programMjerenja = int(key)
            formula = basemap[key]['komponentaFormula']
            mjernajedinica = basemap[key]['komponentaMjernaJedinica']
            postajaNaziv = basemap[key]['postajaNaziv'].lower()
            
            mapa1[programMjerenja] = formula+'-'+mjernajedinica
            
            mapa2[postajaNaziv] = {}        
        for key in basemap.keys():
            programMjerenja = int(key)
            postajaNaziv = basemap[key]['postajaNaziv'].lower()
            
            mapa2[postajaNaziv][mapa1[programMjerenja]] = programMjerenja
        return mapa2
    
    #data model, tu se spremaju podaci
    x = datamodel.DataModel()
    
    #test RESTReadera
    reader = RESTReader(model = x, source = wz)
    t1 = reader.read(key = 162, date = '2014-12-09')
    print(t1)
    #test FileReadera
    transformMapa = make_transformation_dict(wz)        
    reader2 = FileReader(model = x, mapa = transformMapa)
    t2 = reader2.read(path = 'plitvicka jezera-20140601.csv')
    print(t2)
    t3 = reader2.read(path = 'plitvicka jezera-20140601.csv')
    print(t3)
    t4 = reader.read(key = 162, date = '2014-12-09')
    print(t4)
    t5 = reader.read(key = 162, date = '2014-12-10')
    print(t5)
