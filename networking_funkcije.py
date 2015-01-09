#!/usr/bin/python3
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

###############################################################################
###############################################################################
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
###############################################################################
    def get_sve_programe_mjerenja(self):
        """
        funkcija vraca response od servera.
        cilj je response analizirati i prepakirati u nested dict "bitnih" 
        podataka.
        Kljuc vanjskog dicta je id programa mjerenja.
                
        npr.
        {'1':{'postajaNaziv':'Zagreb', 'komponentaNaziv':'Ozon'}, ...},...}
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
                        komponentaFormula = programMjerenja.find('.komponentaId/formula').text
                        #dodavanje mjerenja u dictionary
                        rezultat[i] = {
                            'postajaId':postajaId, 
                            'postajaNaziv':postajaNaziv, 
                            'komponentaId':komponentaId, 
                            'komponentaNaziv':komponentaNaziv, 
                            'komponentaMjernaJedinica':komponentaMjernaJedinica, 
                            'komponentaFormula':komponentaFormula}
                            
                    return rezultat
                #json response
                elif r.headers['Content-Type'] == 'application/json':
                    print('JSON NOT IMPLEMENTED')
                    return None
                #response kada nije ni xml ili json
                else:
                    print('get_sve_programa_mjerenja nije xml ili json')
                    return None
            else:
                #odradi slucajeve bad responseva
                print('get_sve_programe_mjerenja ', r.status_code, r.reason)
                return None
        except requests.exceptions.RequestException as e:
            #Ako se stvari stvarno raspadnu, printaj cijeli tracebak errora
            print(e)
            return None
###############################################################################
    def get_sirovi(self, programMjerenja, datum):
        """
        Novi REST servis, za zadani program mjerenja (int) i datum (string, 
        u formatu YYYY-MM-DD) dohvati sirove podatke
        """
        url = self._base + self._resursi['siroviPodaci']+'/'+str(programMjerenja)+'/'+datum
        payload = {"id":"getJson", "name":"GET"}
        try:
            r = requests.get(url, params = payload, timeout = 9.1)
            if r.ok:
                if r.headers['Content-Type'] == 'application/xml':
                    print('XML NOT IMPLEMENTED')
                    return None
                elif r.headers['Content-Type'] == 'application/json':
                    return r.text #ako treba samo cisti json string
                else:
                    print('get_sirovi() response nije xml ili json')
                    return None
            else:
                print('get_sirovi() bad response', r.status_code, r.reason)
                return None
        except requests.exceptions.RequestException as e:
            #Ako se nesto stvarno raspadne, trackeback errora
            print(e)
            return None
###############################################################################
    def upload_json_agregiranih(self, x):
        """
        Za zadani json string x, predaj zahtjev za dodavanjem u REST servis.
        U slucaju uspjesnog zahtjeva vrati True.
        U slucaju neuspjesnog zahtjeva vrati False.
        """
        url = self._base + self._resursi['siroviPodaci']
        payload = {"id":"putJson", "name":"PUT"}
        try:
            r = requests.put(url, params = payload, data = x, timeout = 9.1)
            if r.ok:
                return True
            else:
                print('Neuspjeh prilikom uploada na REST', r.status_code, r.reason)
        except requests.exceptions.RequestException as e:
            #U slucaju ako se requests slomi, traceback errora
            print(e)
            return False
###############################################################################
###############################################################################
if __name__ == '__main__':
    baza = "http://172.20.1.166:9090/SKZ-war/webresources/"
    resursi = {"siroviPodaci":"dhz.skz.rs.sirovipodaci", 
                "programMjerenja":"dhz.skz.aqdb.entity.programmjerenja"}

    wz = WebZahtjev(baza, resursi)        
    r = wz.get_sve_programe_mjerenja()

    #primjer poziva funkcije
    r2 = wz.get_sirovi(162,'2014-12-15') #15 dan 12 mjeseca 2014 godine    