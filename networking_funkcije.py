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


        
if __name__ == '__main__':
    #niicijalna definicija baze i resursa definiranih u wadl
    baza = "http://172.20.1.166:9090/WebApplication1/webresources/"
    resursi = {"programMjerenja":"test.entity.programmjerenja"}
    
    wz = WebZahtjev(baza, resursi)        
    r = wz.get_sve_programe_mjerenja()    
    
#    #response to xml
#    with open('C:/Documents and Settings/User/Desktop/programmjerenja.xml','w',encoding='utf-8') as fajl:
#        fajl.write(r.text)