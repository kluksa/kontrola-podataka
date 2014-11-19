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

class WebZahtjev():
    """
    Ova klasa sluzi za komunikaciju sa restful web servisom.
    """
    def __init__(self, base, resursi):
        """
        inicijalizacija sa baznim url-om i dictom resursa
        """
        self._base = base
        self._resursi = resursi
        
    def get_broj_postaja(self):
        """
        Funkcija vraca broj postaja
        """
        #url resursa
        url = self._base + self._resursi['postaja'] + "/count"
        #get request web servisu
        r = requests.get(url, timeout = 9.1)
        if r.ok:
            return r.text
        else:
            print('get_broj_postaja ', r.status_code, r.reason)

    def get_postaja_id(self, id):
        """
        Dohvati samo jednu postaju preko njenog id, vraca body zahtjeva, 
        xml string
        """
        #url resursa
        url = self._base + self._resursi['postaja'] + '/' + str(id)
        r = requests.get(url, timeout = 9.1)
        if r.ok:
            return r.text

        else:
            print('get_postaja_id ', r.status_code, r.reason)
        
            
    def get_sve_postaje(self):
        """
        Funkcija vraca nested dict sa informacijom o svim postajama
        {'ime postaje': {xml tag elementa: vrijednost elementa}}
        """
        #url resursa
        url = self._base + self._resursi['postaja']
        #payload za poziv metode
        payload = {"id":"findAll", "name":"GET"}
        #get request web servisu
        r = requests.get(url, params = payload, timeout = 9.1)
        if r.ok:
            if r.headers['Content-Type'] == 'application/xml':
                drvo = ET.fromstring(r.text) #xml parser, stvaranje tree objekta
                output = {} #plan je napraviti nested dict {nazivPostaje:{xml tag : vrijednost}}
                for postaja in drvo:
                    ind = postaja.find('nazivPostaje').text
                    output[ind] = {}
                    for element in postaja:
                        output[ind][element.tag] = element.text

                return output
            else:
                print('get_sve_postaje Content-Type nije application/xml')

        else:
            print('get_sve_postaje ', r.status_code, r.reason)
    
if __name__ == '__main__':
    #niicijalna definicija baze i resursa definiranih u wadl
    baza = "http://172.20.1.166:9090/TestWeb/webresources/"
    resursi = {
        "postaja":"dhz.skz.aqdb.entity.postaja", 
        "korisnik":"dhz.skz.aqdb.entity.korisnik", 
        "programMjerenja":"dhz.skz.aqdb.entity.programmjerenja",
        "komponente":"dhz.skz.aqdb.entity.komponenta"}
    
    
    wz = WebZahtjev(baza, resursi)
    r = wz.get_sve_postaje()
    #pretty print izlaza za test
    for key in r.keys():
        print('postaja: ', key)
        for element in r[key].keys():
            print('    ', element, ' : ', r[key][element])



        
    
    
    
    
    

