# -*- coding: utf-8 -*-
"""
Created on Fri Jul 11 08:44:06 2014

@author: velimir
"""

import pandas as pd
import re
from functools import wraps
from copy import deepcopy

###############################################################################
def benchmark(func):
    """
    Dekorator, izbacuje van ime i vrijeme koliko je funkcija radila
    Napisi @benchmark odmah iznad definicije funkcije da provjeris koliko je brza
    """
    import time
    @wraps(func)
    def wrapper(*args, **kwargs):
        t = time.clock()
        res = func(*args, **kwargs)
        print(func.__name__, time.clock()-t)
        return res
    return wrapper
###############################################################################
#@benchmark
def citaj(path):
    """
    Function reads from csv file into a dictionary of pandas dataframes
    -benchchmark result je oko 1 sec kod mene
    """
    #read from file, lagano usporava read, ali znatno ubrzava save
    df = pd.read_csv(
            path, 
            na_values='-999.00', 
            index_col=0, 
            parse_dates=[[0,1]], 
            dayfirst=True, 
            header=0, 
            sep=',', 
            encoding='iso-8859-1')
 
    #cut the zone and flag columns from the end of dataframe            
    #ovo je sve prekomplicirano. Dakle, ti ZNAS da su nulti i prvi stupac Time i Date (inace Wlreader ne radi)
    #znas da je 2*n stupac mjerenje, a 2*n+1 stupac uvijek status te da je stupac N-2 Flag, a N-1 Zone (n=1..N-3, N- broj stupaca) 
    # s obzirom da to ZNAS, trebalo bi provjeriti je li fajl u tom formatu, ako nije, onda WlReader baca iznimku jer je WlReader
    # klasa za citanje WL datoteka i nikojih drugih
    #
    # Dakle prema ovome sto sam rekao, dfShort je nepotrebanm matching je nepotreban, iteracija moze ici u klasicnoj for petlji
    # sto nas vodi do

    #get names of all columns that do not have flag or status in name
    headerList = df.columns.values

    provjeri_headere(headerList)

    lenListe = len(headerList)
    frejmovi = {}
    for i in range(2,len(headerList)-2,2):
        colName = headerList[i]
        frejmovi[colName] = df.iloc[:,i:i+2]
        frejmovi[colName][u'flag'] = pd.Series(0, index = frejmovi[colName].index)
        frejmovi[colName].columns = [u'koncentracija', u'status', u'flag']
    return frejmovi
    
def provjeri_headere(headerList):
    # TODO:
    # ovdje se provjera format datoteka, ako je dobar funkcija izadje, a ako nije
    # baca iznimku
    return

###############################################################################
#benchmark
def save_work(frejmovi,filepath):
    """
    Sprema dictionary datafrejmova u csv file
    -benchchmark result je oko 1 sec kod mene
    """
    return
###############################################################################
def load_work(filepath):
    return
###############################################################################
#benchmark    
def test_frames1(frames1,frames2):
    """
    -provjera kljuceva dictova u oba frejma
    """    
    ukupno = True
    if len(frames1.keys()) == len(frames2.keys()):
        print('OK!, isti broj frejmova')
        ukupno = ukupno and True
    else:
        print('ERROR!, broj frejmova ne odgovara')
        ukupno = ukupno and False
        
    f1=list(frames1.keys())
    f2=list(frames2.keys())
    for frame in f1:
        if frame in f2:
            print('OK!, {0} frame je u obje liste'.format(frame))
            ukupno = ukupno and True
        else:
            print('ERROR!, {0} nije u drugoj listi'.format(frame))
            ukupno = ukupno and False
    if ukupno:
        print('Test OK!')
    else:
        print('Error!')
###############################################################################
#@benchmark
def test_frames2(frames1,frames2):
    """
    Test_frames2 provjerava podatak po podatak da li je na dobram mjestu.
    -Provjera identiteta dva dicta datafrejmova (konzistencija read - read_saved)
    """    
    ukupno = True
    keys = frames1.keys()
    for key in keys:
        indeks = frames1[key].index
        cols = frames1[key].columns.values
        for i in indeks:
            for j in cols:
                #da izbjegnem np.nan... castam usporedbu u string
                if str(frames1[key].loc[i,j]) != str(frames2[key].loc[i,j]):
                    print('VALUE MISMATCH!:\nkey = {0}\nindeks = {1}\ncolumn = {2}'.format(key,i,j))
                    ukupno = False
                    break
    if ukupno:
        print('OK!')
    else:
        print('ERROR!')
            
###############################################################################
if __name__ == '__main__':
    data = citaj('pj.csv')
    save_work(data, 'pj_saved.csv')
    data1 = citaj('pj_saved.csv')
    test_frames1(data,data1)
    test_frames2(data,data2)
    #test_frames2 je jako spor. treba mu oko 7 minuta za provjeru.
    #test_frames2(data,data1)
    #test_frames2(data,data2)
