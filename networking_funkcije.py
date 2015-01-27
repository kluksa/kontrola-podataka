# -*- coding: utf-8 -*-
"""
Created on Wed Jan 21 10:58:46 2015

@author: User
"""

import requests
import xml.etree.ElementTree as ET
from PyQt4 import QtCore
import pomocneFunkcije

###############################################################################
###############################################################################
class WebZahtjev(QtCore.QObject):
    """
    Klasa zaduzena za komunikaciju sa REST servisom
    """
###############################################################################
    def __init__(self, base, resursi):
        """inicijalizacija sa baznim url-om i dictom resursa"""
        QtCore.QObject.__init__(self)
        self._base = base
        self._resursi = resursi
###############################################################################
    def parse_xml(self, x):
        """
        Pomocna funkcija za internu upotrebu, NE POZIVAJ IZVAN MODULA.
        Parsira xml sa programima mjerenja preuzetih sa rest servisa, 
        input: string
        output: dictionary sa bitnim podacima
        """
        rezultat = {}
        root = ET.fromstring(x)
        for programMjerenja in root:
            i = int(programMjerenja.find('id').text)
            postajaId = int(programMjerenja.find('.postajaId/id').text)
            postajaNaziv = programMjerenja.find('.postajaId/nazivPostaje').text
            komponentaId = programMjerenja.find('.komponentaId/id').text
            komponentaNaziv = programMjerenja.find('.komponentaId/naziv').text
            komponentaMjernaJedinica = programMjerenja.find('.komponentaId/mjerneJediniceId/oznaka').text
            komponentaFormula = programMjerenja.find('.komponentaId/formula').text
            usporednoMjerenje = programMjerenja.find('usporednoMjerenje').text
            #dodavanje mjerenja u dictionary
            rezultat[i] = {
                'postajaId':postajaId, 
                'postajaNaziv':postajaNaziv, 
                'komponentaId':komponentaId, 
                'komponentaNaziv':komponentaNaziv, 
                'komponentaMjernaJedinica':komponentaMjernaJedinica, 
                'komponentaFormula':komponentaFormula, 
                'usporednoMjerenje':usporednoMjerenje}
        #vrati trazeni dictionary
        return rezultat
###############################################################################
    def get_programe_mjerenja(self):
        """
        Metoda salje zahtjev za svim programima mjerenja prema REST servisu.
        Uz pomoc funkcije parse_xml, prepakirava dobivene podatke u mapu
        'zanimljivih' podataka
        """
        #pointaj url prema trazenom podatku iz wadl filea
        url = self._base + self._resursi['programMjerenja']
        #pripremi zahtjev metode
        payload = {"id":"findAll", "name":"GET"}
        try:
            #odradi request###############################################################################
            r = requests.get(url, params = payload, timeout = 9.1)
            #assert dobar response (status code 200) i xml content-type
            assert r.ok == True, 'Bad request, response code:{0}'.format(r.status_code)
            assert r.headers['Content-Type'] == 'application/xml', 'Bad response, not xml'
            #xml parsing
            rezultat = self.parse_xml(r.text)
            return rezultat
        except AssertionError as e1:
            tekst = 'WebZahtjev.get_programe_mjerenja:Assert fail.\n{0}'.format(e1)
            raise pomocneFunkcije.AppExcept(tekst) from e1
        except requests.exceptions.RequestException as e2:
            tekst = 'WebZahtjev.get_programe_mjerenja:Request fail (http error, timeout...).\n{0}'.format(e2)
            raise pomocneFunkcije.AppExcept(tekst) from e2
        except Exception as e3:
            tekst = 'WebZahtjev.get_programe_mjerenja:Opceniti fail.\n{0}'.format(e3)
            raise pomocneFunkcije.AppExcept(tekst) from e3
###############################################################################
    def get_sirovi(self, programMjerenja, datum):
        """
        Novi REST servis, za zadani program mjerenja (int) i datum (string, 
        u formatu YYYY-MM-DD) dohvati sirove podatke
        """
        #point url na trazeni dio REST servisa
        url = self._base + self._resursi['siroviPodaci']+'/'+str(programMjerenja)+'/'+datum
        #pripremi zahtjev###############################################################################
        payload = {"id":"getJson", "name":"GET"}
        try:
            r = requests.get(url, params = payload, timeout = 9.1)
            #assert dobar response (status code 200), json content-type
            assert r.ok == True, 'Bad request, response code:{0}'.format(r.status_code)
            assert r.headers['Content-Type'] == 'application/json', 'Bad response, not json'
            #assert da je duljina json stringa dovoljna (ako nema podataka, dobivam nazad prazan string)
            assert len(r.text) > 3, 'Bad response, empty json string'
            return r.text
        except AssertionError as e1:
            tekst = 'WebZahtjev.get_sirovi:Assert fail.\n{0}'.format(e1)
            raise pomocneFunkcije.AppExcept(tekst) from e1
        except requests.exceptions.RequestException as e2:
            tekst = 'WebZahtjev.get_sirovi:Request fail (http error, timeout...).\n{0}'.format(e2)
            raise pomocneFunkcije.AppExcept(tekst) from e2
        except Exception as e3:
            tekst = 'WebZahtjev.get_sirovi:Opceniti fail.\n{0}'.format(e3)
            raise pomocneFunkcije.AppExcept(tekst) from e3
###############################################################################
    def upload_json_agregiranih(self, x):
        """
        Za zadani json string x, predaj zahtjev za spremanje u REST servis.
        """
        #point url na REST  servis
        url = self._base + self._resursi['siroviPodaci']
        #pripiremi zahtjev
        payload = {"id":"putJson", "name":"PUT"}
        headers = {'Content-type': 'application/json'}
        try:
            assert x != None, 'Ulazni parametar je None, json string nije zadan.'
            assert len(x) > 0, 'Ulazni json string je prazan'
            r = requests.put(url, params = payload, data = x, headers = headers, timeout = 9.1)
            assert r.ok == True, 'Bad request, response code:{0}'.format(r.status_code)
        except AssertionError as e1:
            tekst = 'WebZahtjev.upload_json_agregiranih:Assert fail.\n{0}'.format(e1)
            raise pomocneFunkcije.AppExcept(tekst) from e1
        except requests.exceptions.RequestException as e2:
            tekst = 'WebZahtjev.upload_json_agregiranih:Request fail (http error, timeout...).\n{0}'.format(e2)
            raise pomocneFunkcije.AppExcept(tekst) from e2
###############################################################################
###############################################################################
if __name__ == '__main__':
    #definiranje baze i resursa
    baza = "http://172.20.1.166:9090/SKZ-war/webresources/"
    resursi = {"siroviPodaci":"dhz.skz.rs.sirovipodaci", 
                "programMjerenja":"dhz.skz.aqdb.entity.programmjerenja"}
    #inicijalizacija WebZahtjev objekta
    wz = WebZahtjev(baza, resursi)
    """
    u principu, pozovi metodu unutar try bloka, ako se nesto slomi, 
    exception ce se re-raisati kao Exception sa opisom gdje i sto je puklo.
    """
    try:
        r = wz.get_programe_mjerenja()
        print(r)
#        r1 = wz.get_sirovi(145, '2015-01-14')
#        print(r1)
#        r2 = wz.upload_json_agregiranih('')
    except Exception as e:
        print(e) #vraca tekst exceptiona
        print(repr(e))