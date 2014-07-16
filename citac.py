# -*- coding: utf-8 -*-
"""
Created on Fri Jul 11 08:44:06 2014

@author: velimir
"""

import pandas as pd
import re
from functools import wraps


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
@benchmark
def citaj_weblog(path):
    """
    path = fullpath do filea
    funkcija cita weblogger csv fileove u dictionary pandas datafrejmova
    """
    if provjeri_headere_weblog(path):
        df = pd.read_csv(
            path, 
            na_values='-999.00', 
            index_col=0, 
            parse_dates=[[0,1]], 
            dayfirst=True, 
            header=0, 
            sep=',', 
            encoding='iso-8859-1')
    
        headerList = df.columns.values
        print(headerList)
        frejmovi = {}
        for i in range(0,len(headerList)-2,2):
            colName = headerList[i]
            frejmovi[colName] = df.iloc[:,i:i+2]
            frejmovi[colName][u'flag'] = pd.Series(0, index = frejmovi[colName].index)
            frejmovi[colName].columns = [u'koncentracija', u'status', u'flag']
        return frejmovi
    else:
        #trenutno bez implementacije
        print('\nNekakvo njesra s fileom, implementiraj neki msg da je akcija failala')
        return

###############################################################################
@benchmark
def provjeri_headere_weblog(path):
    """
    Testna funkcija za provjeru headera csv filea na lokaciji path.
    Ne koristim dataframe headere, direktno citam prvi redak iz filea!
        - ne treba ucitati cijeli file i upisati ga u dataframe za test
        - u headeru iz datafrejma nema Date, Time (to je index stupac Date_Time)
        
    OK struktura je:
    Date,Time,mjerenje1,status1,...mjerenjeN,statusN,Flag,Zone
    
    Vraca True ako je struktura dobra, inace vraca False cim naleti na neko odstupanje
    """
    try:
        file = open(path)
        firstLine = file.readline()
        file.close()
        #makni \n na kraju linije
        firstLine = firstLine[:-1]
        headerList = firstLine.split(sep=',')
        
        #dio za provjeru prva dva stupca...('Date', 'Time')
        if (headerList[0],headerList[1]) != ('Date', 'Time'):
            return False
        #dio za provjeru zadnja dva stupca... ('Flag', 'Zone')
        if (headerList[-2],headerList[-1]) != ('Flag','Zone'):
            return False
        #svi parni stupci moraju biti razliciti od "status"
        for i in range(2,len(headerList)-2,2):
            statusMatch = re.search(r'status', headerList[i], re.IGNORECASE)
            if statusMatch:
                return False
        #svi neparni stupci moraju biti "status"
        for i in range(3,len(headerList)-2,2):
            statusMatch = re.search(r'status', headerList[i], re.IGNORECASE)
            if not statusMatch:
                return False
        return True
    
    except IOError:
        print('Problem with reading file {0}'.format(path))
        return False
###############################################################################
def save_work(frejmovi,filepath):
    print('save_work not implemented')
    return
###############################################################################
def load_work(filepath):
    print('load_work not implemented')
    return
###############################################################################
if __name__ == '__main__':
    print('\ntest nepostojeceg filea')
    x = provjeri_headere_weblog('pj123.csv')
    print('\ntest postojeceg filea, pravilne strukture')
    y = provjeri_headere_weblog('pj.csv')
    print('\ntest postojeceg filea, nepravilne strukture')
    print('pogreska u Time, jednom statusu, jedom mjerenju')
    z = provjeri_headere_weblog('pj_corrupted.csv')
    #ucitavanje
    data1 = citaj_weblog('pj.csv')
    data2 = citaj_weblog('pj123.csv')
    data3 = citaj_weblog('pj_corrupted.csv')
    
    