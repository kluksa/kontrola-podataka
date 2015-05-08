# -*- coding: utf-8 -*-
"""
Created on Wed Jan 21 10:58:46 2015

@author: User
"""
from requests.auth import HTTPBasicAuth
import requests
import logging
import xml.etree.ElementTree as ET
from PyQt4 import QtCore
import json

import app.general.pomocne_funkcije as pomocne_funkcije
###############################################################################
###############################################################################
class WebZahtjev(QtCore.QObject):
    """
    Klasa zaduzena za komunikaciju sa REST servisom

    INSTANCIRAN:
    - u modulu kontroler.py prilikom inicijalizacije objekta Kontroler
    - referenca na taj objekt se prosljedjuje svima koji komuniciraju sa REST-om

    drugi modluli koji ga koriste:
    -datareader.RESTReader (source)
    -datareader.RESTWriter (source)
    """
###############################################################################
    def __init__(self, base, resursi, auth):
        """inicijalizacija sa baznim url-om i dictom resursa i tupleom
        (user, password)"""
        QtCore.QObject.__init__(self)
        self._base = base
        self._resursi = resursi
        self.user, self.pswd = auth

        #, auth = HTTPBasicAuth(self.user, self.pswd)
        #, auth = (self.user, self.pswd)
###############################################################################
    def get_satne_podatke(self, mapa):
        """
        Metoda dohvaca satno agregirane podatke sa REST servisa.
        ulazni parametar je mapa podataka

        {
            'datumOd': string, format mora biti "YYYY-MM-DDThh:mm:ss"
            'datumDo': string, format mora biti "YYYY-MM-DDThh:mm:ss"
            'kanal': int, id programa mjerenja
            'valjani': boolean, Da li se prikazuju samo valjani
            'validacija': int, nivo validacije
        }

        metoda vraca json string
        """
        url = self._base + self._resursi['satniPodaci']+'/'
        res = "/".join([str(mapa['kanal']),str(mapa['datumOd']),str(mapa['datumDo'])])
        url = url+res
        payload = {"samo_valjani":mapa['valjani'],
                   "nivo_validacije":mapa['validacija']}
        try:
            r = requests.get(url,
                             timeout=39.1,
                             auth = HTTPBasicAuth(self.user, self.pswd),
                             params=payload)
            assert r.ok == True, 'Bad request, response code={0}, url={1}'.format(r.status_code, r.url)
            assert r.headers['Content-Type'] == 'application/json', 'Bad response, not json'
            return r.text
        except AssertionError as e1:
            tekst = 'WebZahtjev.get_satne_podatke:Assert fail.\n{0}'.format(e1)
            raise pomocne_funkcije.AppExcept(tekst) from e1
        except requests.exceptions.RequestException as e2:
            tekst = 'WebZahtjev.get_satne_podatke:Request fail (http error, timeout...).\n{0}'.format(e2)
            raise pomocne_funkcije.AppExcept(tekst) from e2
        except Exception as e3:
            tekst = 'WebZahtjev.get_satne_podatke:Opceniti fail.\n{0}'.format(e3)
            raise pomocne_funkcije.AppExcept(tekst) from e3
###############################################################################
    def get_statusMap(self):
        """
        Metoda dohvaca podatke o statusima sa REST servisa
        vraca dictionary:
        {broj bita [int] : opisni string [str]}
        """
        url = self._base + self._resursi['statusMap']
        try:
            r = requests.get(url, timeout = 39.1, auth = HTTPBasicAuth(self.user, self.pswd))
            #assert dobar response (status code 200) i xml content-type
            assert r.ok == True, 'Bad request, response code={0}, url={1}'.format(r.status_code, r.url)
            assert r.headers['Content-Type'] == 'application/json', 'Bad response, not json'
            jsonStr = r.text
            #parse and asemble statusMap
            x = json.loads(jsonStr)
            rezultat = {}
            for i in range(len(x)):
                rezultat[x[i]['i']] = x[i]['s']
            return rezultat
        except AssertionError as e1:
            tekst = 'WebZahtjev.get_statusMap:Assert fail.\n{0}'.format(e1)
            raise pomocne_funkcije.AppExcept(tekst) from e1
        except requests.exceptions.RequestException as e2:
            tekst = 'WebZahtjev.get_statusMap:Request fail (http error, timeout...).\n{0}'.format(e2)
            raise pomocne_funkcije.AppExcept(tekst) from e2
        except Exception as e3:
            tekst = 'WebZahtjev.get_statusMap:Opceniti fail.\n{0}'.format(e3)
            raise pomocne_funkcije.AppExcept(tekst) from e3
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
            r = requests.get(url, params = payload, timeout = 39.1, auth = HTTPBasicAuth(self.user, self.pswd))
            #r = requests.get(url, params = payload, timeout = 9.1, auth = HTTPDigestAuth(self.user, self.pswd))
            #assert dobar response (status code 200) i xml content-type
            assert r.ok == True, 'Bad request, response code={0}, url={1}'.format(r.status_code, r.url)
            assert r.headers['Content-Type'] == 'application/xml', 'Bad response, not xml'
            #xml parsing
            rezultat = self.parse_xml(r.text)
            return rezultat
        except AssertionError as e1:
            tekst = 'WebZahtjev.get_programe_mjerenja:Assert fail.\n{0}'.format(e1)
            raise pomocne_funkcije.AppExcept(tekst) from e1
        except requests.exceptions.RequestException as e2:
            tekst = 'WebZahtjev.get_programe_mjerenja:Request fail (http error, timeout...).\n{0}'.format(e2)
            raise pomocne_funkcije.AppExcept(tekst) from e2
        except Exception as e3:
            tekst = 'WebZahtjev.get_programe_mjerenja:Opceniti fail.\n{0}'.format(e3)
            raise pomocne_funkcije.AppExcept(tekst) from e3
###############################################################################
    def get_sirovi(self, programMjerenja, datum):
        """
        Novi REST servis, za zadani program mjerenja (int) i datum (string,
        u formatu YYYY-MM-DD) dohvati sirove podatke
        """
        #point url na trazeni dio REST servisa
        url = self._base + self._resursi['siroviPodaci']+'/'+str(programMjerenja)+'/'+datum
        #pripremi zahtjev
        payload = {"id":"getPodaci", "name":"GET"}
        try:
            r = requests.get(url, params = payload, timeout = 39.1, auth = HTTPBasicAuth(self.user, self.pswd))
            #assert dobar response (status code 200), json content-type
            assert r.ok == True, 'Bad request, response code={0}, url={1}'.format(r.status_code, r.url)
            assert r.headers['Content-Type'] == 'application/json', 'Bad response, not json'
            return r.text
        except AssertionError as e1:
            tekst = 'WebZahtjev.get_sirovi:Assert fail.\n{0}'.format(e1)
            raise pomocne_funkcije.AppExcept(tekst) from e1
        except requests.exceptions.RequestException as e2:
            tekst = 'WebZahtjev.get_sirovi:Request fail (http error, timeout...).\n{0}'.format(e2)
            raise pomocne_funkcije.AppExcept(tekst) from e2
        except Exception as e3:
            tekst = 'WebZahtjev.get_sirovi:Opceniti fail.\n{0}'.format(e3)
            raise pomocne_funkcije.AppExcept(tekst) from e3
###############################################################################
    def upload_json_minutnih(self, program=None, jstring=None, date=None):
        """
        Za zadani json string minutnih podataka, predaj zahtjev za spremanje u REST servis.
        Dodatni parametar je program mjerenja id
        """
        #point url na REST  servis
        url = self._base + self._resursi['siroviPodaci']+ '/'+str(program)+'/'+str(date)
        #pripiremi zahtjev
        payload = {"id":"putPodaci", "name":"PUT"}
        headers = {'Content-type': 'application/json'}
        try:
            assert jstring is not None, 'Ulazni parametar je None, json string nije zadan.'
            assert len(jstring) > 0, 'Ulazni json string je prazan'
            r = requests.put(url,
                             params=payload,
                             data=jstring,
                             headers=headers,
                             timeout=39.1,
                             auth = HTTPBasicAuth(self.user, self.pswd))
            assert r.ok == True, 'Bad request, response code={0}, url={1}, json={2}'.format(r.status_code, r.url, jstring)
        except AssertionError as e1:
            tekst = 'WebZahtjev.upload_json_minutnih:Assert fail.\n{0}'.format(e1)
            raise pomocne_funkcije.AppExcept(tekst) from e1
        except requests.exceptions.RequestException as e2:
            tekst = 'WebZahtjev.upload_json_minutnih:Request fail (http error, timeout...).\n{0}'.format(e2)
            raise pomocne_funkcije.AppExcept(tekst) from e2

###############################################################################
    def get_zero_span(self, programMjerenja, datum, kolicina):
        """
        Dohvati zero-span vrijednosti
        program mjerenja je tipa int, datum je string

        path -- "program/datum"
        """
        try:
            #point url na trazeni dio REST servisa
            url = self._base + self._resursi['zerospan']+'/'+str(programMjerenja)+'/'+datum
            #pripremi zahtjev
            payload = {"id":"getZeroSpanLista", "name":"GET", "broj_dana":int(kolicina)}
            #request
            r = requests.get(url, params = payload, timeout = 39.1, auth = HTTPBasicAuth(self.user, self.pswd))
            assert r.ok == True, 'Bad request/response code={0}, url={1}'.format(r.status_code, r.url)
            assert r.headers['Content-Type'] == 'application/json', 'Bad response, not json'
            return r.text
        except requests.exceptions.RequestException as e1:
            tekst = 'WebZahtjev.get_zero_span:Request fail (http error, timeout...).\n{0}'.format(e1)
            raise pomocne_funkcije.AppExcept(tekst) from e1
        except AssertionError as e2:
            tekst = 'WebZahtjev.get_zero_span:Assert fail. Bad response.\n{0}'.format(e2)
            raise pomocne_funkcije.AppExcept(tekst) from e2
        except Exception as e3:
            tekst = 'WebZahtjev.get_zero_span:exception. {0}'.format(e3)
            raise pomocne_funkcije.AppExcept(tekst) from e3
###############################################################################
    def upload_ref_vrijednost_zs(self, jS, kanal):
        """
        funkcija za upload nove vrijednosti referentne tocke zero ili span
        na REST servis.

        kanal je int vrijednost trenutno programMjerenjaId
        jS je json string sa podacima o novoj referentnoj vrijednosti
        """
        #point url na REST  servis
        url = self._base + self._resursi['zerospan']+'/'+str(kanal)
        #pripiremi zahtjev
        payload = {"id":"putZeroSpanReferentnuVrijednost", "name":"PUT"}
        headers = {'Content-type': 'application/json'}
        try:
            assert jS is not None, 'Ulazni parametar je None, json string nije zadan.'
            assert len(jS) > 0, 'Ulazni json string je prazan'
            r = requests.put(url, params = payload, data = jS, headers = headers, timeout = 9.1, auth = HTTPBasicAuth(self.user, self.pswd))
            assert r.ok == True, 'Bad request, response code={0}, url={1}, json={2}'.format(r.status_code, r.url, jS)
        except AssertionError as e1:
            tekst = 'WebZahtjev.upload_ref_vrijednost_zs:Assert fail.\n{0}'.format(e1)
            logging.error('assert fail (bad response, los request..)', exc_info = True)
        except requests.exceptions.RequestException as e2:
            tekst = 'WebZahtjev.upload_ref_vrijednost_zs:Request fail (http error, timeout...).\n{0}'.format(e2)
            raise pomocne_funkcije.AppExcept(tekst) from e2
###############################################################################
###############################################################################