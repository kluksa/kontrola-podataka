# -*- coding: utf-8 -*-
"""
Created on Mon Jun  9 08:48:26 2014

@author: velimir

Mapiranje zadanog direktorija.

-treba srediti citac da kao argument uzima listu imena fileova (te da ih spoji u
jedan izlazni)??
"""

import glob
    
def mapiraj(path):
    """
    ULAZ:    
        -path je ime direktorija. npr. D:\nekidirektorij\
    IZLAZ:
        -stanice su dictionary svih stanica u direktoriju (kljuc je ime stanice)
        -vrijednosti od stanice su datumi (takodjer dictionary, kljuc je datum,
        formatiran kao YYYYMMDD)
        -vrijednosti dictionarija datumi su liste fileova koje zadovoljavaju
        kombinaciju stanica-datum
    """
    stanice={}
    stanice_C={}
    #provjera za ispravnost argumenta
    if type(path)!=type('blah'):
        raise ValueError
    #provjera da li path zavrsava sa \    
    if path[::-1]!='\\':
        path=path+'\\'

    raw=glob.glob(path+'*.csv')
    data,data_C=separacija(raw)    
    stanice=napravi_mapu(data)
    stanice_C=napravi_mapu(data_C)
    
    return stanice,stanice_C
    
    
def napravi_mapu(data):
    """
    od ulaznih podataka napravi mapu.
    dict stanica koji sadrzi dict datuma, koji sadrzi imena fileova
    """
    stanice={}
    
    for file in data:
        
        stanica,datum=parsiraj(file)

        if stanica not in stanice:
            stanice[stanica]={datum:[file]}
        else:
            if datum not in stanice[stanica]:
                stanice[stanica].update({datum:[file]})
            else:
                stanice[stanica][datum].append(file)
        
    return stanice

def separacija(listaSvih):
    """
    Odvajanje fileova na dvije liste (sa _C i bez _C u imenu)
    """
    data=[]
    data_C=[]
    for item in listaSvih:
        if item.find('_C')==-1:
            data.append(item)
        else:
            data_C.append(item)
            
    return data,data_C


def parsiraj(item):
    """
    Parser da dobijemo ime i datum uz filename
    """
    while item.find('\\')!=-1:
        loc=item.find('\\')
        item=item[loc+1:]
    item=item[0:len(item)-4]
    loc=item.find('-')
    stanica=item[:loc]
    if stanica.find('_C')!=-1:
        stanica=stanica[0:len(stanica)-2]
    datum=item[loc+1:]
    return stanica,datum
        
    
if __name__=='__main__':
    mapa,mapa_C=mapiraj('D:\\kontrolapodataka\\')
    
    