# -*- coding: utf-8 -*-
"""
Created on Fri Jul 11 08:44:06 2014

@author: velimir
"""

import pandas as pd
import re
from functools import wraps


###############################################################################
#def benchmark(func):
#    """
#    Dekorator, izbacuje van ime i vrijeme koliko je funkcija radila
#    Napisi @benchmark odmah iznad definicije funkcije da provjeris koliko je brza
#    """
#    import time
#    @wraps(func)
#    def wrapper(*args, **kwargs):
#        t = time.clock()
#        res = func(*args, **kwargs)
#        print(func.__name__, time.clock()-t)
#        return res
#    return wrapper
#
###############################################################################
###############################################################################
class WlReader:
    """
    Ova klasa odradjuje citanje weblogger csv fileova
    """
    def __init__(self):
        pass    
###############################################################################
    def citaj(self, path):
        """
        path = fullpath do filea
        funkcija cita weblogger csv fileove u dictionary pandas datafrejmova
        """
        if self.provjeri_headere(path):
            df = pd.read_csv(
                path, 
                na_values = '-999.00', 
                index_col = 0, 
                parse_dates = [[0,1]], 
                dayfirst = True, 
                header = 0, 
                sep = ',', 
                encoding = 'iso-8859-1')
        
            headerList = df.columns.values
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
    def citaj_listu(self, pathLista):
        """
        pathLista = lista svih pathova za otvaranje
        INPUT - lista stringova
        funkcija cita listu weblogger csv fileova u dictionary pandas datafrejmova
        """
        try:
            #raise IOError if argument is not list, or if list is empty
            if (type(pathLista) != type ([])) or (len(pathLista) == 0):
                raise IOError
            
            #ucitaj prvi valjani csv file, mici s liste one koji se ne ucitavaju
            while len(pathLista) != 0:
                file = pathLista.pop(0)
                print(file)
                frejmovi = self.citaj(file)
                if frejmovi != None:
                    break
            
            else:
                print('Svi fileovi ne valjaju. Tretiraj kao I/O error')
                raise IOError
            
            
            #petlja koja ucitava ostale fileove u listi (lista je sada kraca)
            for file in pathLista:
                frejmoviTemp = self.citaj(file)
                if frejmoviTemp != None:
                    #kod za spajanje datafrejma
                    for key in frejmoviTemp.keys():
                        if key in frejmovi.keys():
                            #ako postoji isti kljuc u oba datafrejma -  update/merge
                            #ovaj korak je nesto u stilu full outer join
                            frejmovi[key] = pd.merge(
                                frejmovi[key], 
                                frejmoviTemp[key], 
                                how = 'outer', 
                                left_index = True, 
                                right_index = True, 
                                sort = True, 
                                on = [u'koncentracija', u'status', u'flag'])
                            #update vrijednosti koje nisu np.NaN
                            frejmovi[key].update(frejmoviTemp[key])
                        else:
                            #ako ne postoji kljuc (novi stupac) - dodaj novi frame
                            frejmovi[key] = frejmoviTemp[key]
            return frejmovi
        
        except IOError:
            #implementiraj neki fail kod unosa prazne liste ili nekog drugog tipa podataka
            print('neko njesra sa input / output kod citanja liste csv weblog fileova')
            return

###############################################################################
    def provjeri_headere(self, path):
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
            #test ulaznih podataka
            if type(path) != type('string'):
                raise IOError
            
            ekstenzija = path[path.rfind('.')+1:]
            if ekstenzija != 'csv':
                raise IOError
            
            file = open(path)
            firstLine = file.readline()
            file.close()
            #makni \n na kraju linije
            firstLine = firstLine[:-1]
            headerList = firstLine.split(sep=',')
            """
            Index error moguc, dodan u exceptione:
            1. file je prazan ---> headerList[1] ne postoji
            2. file ima samo jedan column ---> headerList[1] ne postoji
            """
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
            return False
        except IndexError:
            return False
###############################################################################
            
if __name__ == '__main__':
#    #header test
#    print('\ntest nepostojeceg filea')
#    x = WlReader().provjeri_headere('pj123.csv')
#    print('\ntest postojeceg filea, pravilne strukture')
#    y = WlReader().provjeri_headere('pj.csv')
#    print('\ntest postojeceg filea, nepravilne strukture')
#    print('pogreska u Time, jednom statusu, jedom mjerenju')
#    z = WlReader().provjeri_headere('pj_corrupted.csv')
#    print('\ntest postojeceg filea, praznog')
#    k = WlReader().provjeri_headere('pj_empty.csv')
#    #citaj test
#    data1 = WlReader().citaj('pj.csv')
#    data2 = WlReader().citaj('pj123.csv')
#    data3 = WlReader().citaj('pj_corrupted.csv')
#    data4 = WlReader().citaj('pj_empty.csv')
    #citaj_listu test
    """
    Napravio par mock csv fileova da "rucno" provjerim join/merge liste
    Jedini "problem" je u cinjenici da spaja frame po frame, sto ima jednu caku.
    Frejmovi su dobro spojeni, ali ovisno o ulaznim fileovima nisu svi iste duljine.

    - Pojedini frame nezna kako je drugi frame indeksiran
    - Indeksi su istog formata, ali ako mjerenja komponente pocinju od 15:00
    u frameu nece biti indeksa od 00:00 do 14:59 sa np.NaN vrijednostima (osim 
    ako nisu eksplicitno zadana u csv fileu)
    
    Sve u biti ovisi o ulaznim fileovima...
    """
    data5 = WlReader().citaj_listu([
        'nepostojeci.csv', 
        'pj-20140715A.csv', 
        'pj-20140715B.csv', 
        'pj_corrupted.csv', 
        'pj-20140715C.csv', 
        'pj-20140715D.csv'])
    
    if len(data5['1-SO2']) == len(data5['PM1']):
        print('Broj indeksa je jednak')
    else:
        print('Broj indeksa u oba frejma je razlicit')
    
    