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
    df = citaj_probno(path)
    
    #cut the zone and flag columns from the end of dataframe            
    dfShort = df.iloc[:,:-2]
    
    #get names of all columns that do not have flag or status in name
    headerList = dfShort.columns.values
    lenListe = len(headerList)
    frejmovi = {}
    
    for colName in dfShort:
        match1 = re.search(r'status', colName, re.IGNORECASE)
        match2 = re.search(r'flag', colName, re.IGNORECASE)
        if (not match1) and (not match2):
            i = dfShort.columns.get_loc(colName)
            if ((i+2) < lenListe) and re.search(r'flag', dfShort.columns[i+2], re.IGNORECASE):
                #flag column postoji u dataframeu
                frejmovi[colName] = dfShort.iloc[:,i:i+3]
                frejmovi[colName].columns = [u'koncentracija', u'status', u'flag']
            else:
                #flag column ne postoji u dataframeu
                frejmovi[colName] = dfShort.iloc[:,i:i+2]
                frejmovi[colName][u'flag'] = pd.Series(0, index = frejmovi[colName].index)
                frejmovi[colName].columns = [u'koncentracija', u'status', u'flag']
    
    #dodaj stupce 'Flag' i 'Zone' u dictionary
    frejmovi[u'Flag'] = pd.DataFrame({u'Flag':df.loc[:,u'Flag']})
    frejmovi[u'Zone'] = pd.DataFrame({u'Zone':df.loc[:,u'Zone']})
    
    return frejmovi
###############################################################################
#@benchmark
def citaj_probno(filepath):
    """
    funkcija probno ucitava dataframe. Provjerava da li je prvi stupac
    Ako je prvi stupac 'Time' znaci da u csv tablici imamo 2 stupca ['Date','Time'].
    Ako je prvi stupac razlicit od 'Time' znaci da u csv tablici imamo 1 stupac
    [Date_Time], pa moramo drugacije ucitati dataframe.
    """
    #read from file
    _df = pd.read_csv(
        filepath, 
        index_col=0, 
        header=0, 
        encoding='latin-1')
    #slucaj [Date,Time]
    if _df.columns[0]==u'Time':
        _df = pd.read_csv(
            filepath, 
            na_values='-999.00', 
            index_col=0, 
            parse_dates=[[0,1]], 
            dayfirst=True, 
            header=0, 
            sep=',', 
            encoding='latin-1')
    #slucaj [Date_Time]
    else:
        _df=pd.read_csv(
            filepath, 
            na_values='-999.00', 
            index_col=0, 
            parse_dates=True, 
            header=0, 
            sep=',', 
            encoding='latin-1')
    
    return _df
    
###############################################################################
#benchmark
def save_work(frejmovi,filepath):
    """
    Sprema dictionary datafrejmova u csv file
    -benchchmark result je oko 1 sec kod mene
    """
    keyList = list(frejmovi.keys())
    indeks = frejmovi[keyList[0]].index
    
    dfAll = pd.DataFrame(index = indeks)
    i = 1
    for key in keyList:
        if (key != u'Flag') and (key != u'Zone'):
            dfCurrent = frejmovi[key]
            tmp = dfCurrent.columns.values
            tmp[0] = key
            tmp[1] = u'status'+str(i)
            tmp[2] = u'flag'+str(i)
            dfCurrent.columns = tmp
            i += 1
            dfAll = dfAll.merge(dfCurrent, 
                                how = 'outer', 
                                left_index = True, 
                                right_index = True)
            #jednostavnije (i brze) je vratiti imena nazad nego raditi deep copy
            tmp = dfCurrent.columns.values
            tmp[0] = u'koncentracija'
            tmp[1] = u'status'
            tmp[2] = u'flag'
            dfCurrent.columns = tmp
            
    dfAll = dfAll.merge(frejmovi[u'Flag'], 
                        how = 'outer', 
                        left_index = True, 
                        right_index = True)
    dfAll = dfAll.merge(frejmovi[u'Zone'], 
                        how = 'outer', 
                        left_index = True, 
                        right_index = True)

    
    #write to csv file
    dfAll.to_csv(
        filepath, 
        na_rep = '-999.00', 
        sep = ',', 
        encoding = 'latin-1')
###############################################################################
def load_work(filepath):
    """
    MAKNI U BUDUCNOSTI!!!!
    trenutni fix zbog GUI/kontroler interakcije
    """
    return citaj(filepath)
###############################################################################
#@benchmark
def citaj_listu(lista):
    """
    Cita cijelu listu element po element, dodajuci ucitane podatke na jedan
    izlazni dataframe.
    -koristi funkciju citaj za citanje jednog elementa
    -podatci se ili prepisuju iz originalnog datafrejma ili se updateaju po potrebi
    """
    izlaz = {}
    for element in lista:
        frejmovi = citaj(element)
        _temp = deepcopy(frejmovi)
        for kljuc in list(_temp.keys()):
            if kljuc not in izlaz:
                izlaz[kljuc]=_temp[kljuc]
            else:
                izlaz[kljuc].update(_temp[kljuc])
    return izlaz
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
    data2 = citaj_listu(['pj.csv','pj_saved.csv'])
    test_frames1(data,data1)
    test_frames2(data,data2)
    #test_frames2 je jako spor. treba mu oko 7 minuta za provjeru.
    #test_frames2(data,data1)
    #test_frames2(data,data2)