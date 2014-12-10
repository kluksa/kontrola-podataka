# -*- coding: utf-8 -*-
"""
Created on Mon Nov 17 08:36:27 2014

@author: User
BITNO!!!

-xml.etree.ElementTree je medju standardnim modulima pythona

-requests nije, treba ga instalirati.

https://pypi.python.org/pypi/requests/2.4.3

"""

import requests
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np

class WebZahtjev():
    """
    Ova klasa sluzi za komunikaciju sa restful web servisom.
    """
    def __init__(self, base, resursi):
        """
        inicijalizacija sa baznim url-om i dictom resursa, jer zelim izbjeci
        hardcodiranje zahtjeva
        """
        self._base = base
        self._resursi = resursi
                          
    def get_sve_programe_mjerenja(self):
        """
        funkcija vraca response od servera.
        cilj je response analizirati i prepakirati u nested dict "bitnih" 
        podataka.
        Kljuc vanjskog dicta je id programa mjerenja.
                
        npr.
        {'1':{'postajaNaziv':'Zagreb', 'komponentaNaziv':'Ozon'}, ...},...}

        
        TODO:
        -bolja komunikacija sa korisnikom prilikom failova, trenutno je
        print na output konzole
        -implementirati json slucaj
        """
        #pointaj url prema trazenom podatku iz wadl filea
        url = self._base + self._resursi['programMjerenja']
        #pripremi zahtjev metode
        payload = {"id":"findAll", "name":"GET"}
        try:
            r = requests.get(url, params = payload, timeout = 9.1)
            if r.ok:
                #xml response
                if r.headers['Content-Type'] == 'application/xml':
                    #inicijaliziraj output dictionary
                    rezultat = {}
                    #parsiraj xml
                    root = ET.fromstring(r.text)
                    #popuni dictionary sa ciljanim podacima
                    for programMjerenja in root:
                        i = programMjerenja.find('id').text
                        postajaId = programMjerenja.find('.postajaId/id').text
                        postajaNaziv = programMjerenja.find('.postajaId/nazivPostaje').text
                        komponentaId = programMjerenja.find('.komponentaId/id').text
                        komponentaNaziv = programMjerenja.find('.komponentaId/naziv').text
                        komponentaMjernaJedinica = programMjerenja.find('.komponentaId/mjerneJediniceId/oznaka').text
                        #dodavanje mjerenja u dictionary
                        rezultat[i] = {
                            'postajaId':postajaId, 
                            'postajaNaziv':postajaNaziv, 
                            'komponentaId':komponentaId, 
                            'komponentaNaziv':komponentaNaziv, 
                            'komponentaMjernaJedinica':komponentaMjernaJedinica}
                            
                    return rezultat
                #json response
                elif r.headers['Content-Type'] == 'application/json':
                    return r
                #response kada nije ni xml ili json
                else:
                    print('get_sve_programa_mjerenja nije xml ili json')
            else:
                #odradi slucajeve bad responseva
                print('get_sve_programe_mjerenja ', r.status_code, r.reason)
        except requests.exceptions.RequestException as e:
            #Ako se stvari stvarno raspadnu, printaj cijeli tracebak errora
            print(e)


    def get_sirovi(self, programMjerenja, datum):
        """
        Novi REST servis, za zadani program mjerenja (int) i datum (string, 
        u formatu YYYY-DD-MM) dohvati sirove podatke
        """
        url = self._base + self._resursi['siroviPodaci']+'/'+str(programMjerenja)+'/'+datum
        payload = {"id":"getJson", "name":"GET"}
        try:
            r = requests.get(url, params = payload, timeout = 9.1)
            if r.ok:
                if r.headers['Content-Type'] == 'application/xml':
                    return r
                elif r.headers['Content-Type'] == 'application/json':
                    #return r.text #ako treba samo cisti json string
                    x = pd.read_json(r.text)
                    #napravi prazan dataframe (izlazni)
                    df = pd.DataFrame(columns = ('koncentracija', 'status', 'flag'))
                    #adaptiraj frejm u izlazni, OVO TRAJE...pristupanje pojedinim elementima
                    for i in range(len(x)):
                        #buduci index, timestamp
                        vrijeme = pd.to_datetime(x.loc[i,'vrijeme'], format = '%Y-%d-%mT%H:%M:%S')
                        #koncentracija, zamjeniti sa np.NaN ako je ispod -900
                        koncentracija = x.loc[i,'vrijednost']
                        if koncentracija < -900:
                            koncentracija = np.NaN
                        #TODO! nisam 100% siguran kako adaptirati ovu vrijednost, prije je bila int
                        status = x.loc[i,'statusString']
                        #valjanost konvertiram u +1/-1, adaptiranje sa ostatkom
                        flag = x.loc[i, 'valjan']
                        if flag:
                            flag = 1
                        else:
                            flag = -1    
                        #upis u izlazni datafrejm
                        df.loc[vrijeme] = [koncentracija, status, flag]
                    #sorting, json nije nuzno poredan po redu
                    df.sort_index()
                    #vrati dataframe
                    return df
                else:
                    print('get_sirovi() response nije xml ili json')
            else:
                print('get_sirovi() bad response', r.status_code, r.reason)
                return r
        except requests.exceptions.RequestException as e:
            #Ako se nesto stvarno raspadne, trackeback errora
            print(e)

        
if __name__ == '__main__':
    #niicijalna definicija baze i resursa definiranih u wadl
    baza = "http://172.20.1.166:9090/WebApplication1/webresources/"
    resursi = {"programMjerenja":"test.entity.programmjerenja"}
    
    wz = WebZahtjev(baza, resursi)        
#    r = wz.get_sve_programe_mjerenja()    

    baza2 = "http://172.20.1.166:9090/SKZ-war/webresources/"
    resursi2 = {"siroviPodaci":"dhz.skz.rs.sirovipodaci"}    

    wz2 = WebZahtjev(baza2, resursi2)
    #primjer poziva funkcije    
    r = wz2.get_sirovi(161,'2014-09-12')
    """
    izlazni frejm ima datum formatiran YYYY-MM-DD HH:MM:SS
    """    
    #TODO! nesto ne radi kako spada sa datumima
    print(r.head())
    print(r.tail())

    