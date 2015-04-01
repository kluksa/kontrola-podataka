# -*- coding: utf-8 -*-
"""
Created on Thu Jan 22 09:52:37 2015

@author: User
"""

from PyQt4 import QtCore, QtGui
import datetime #python datetime objekt, potreban za timedelta isl.
import pandas as pd
#import os #pristup direktorijima, provjere postojanja filea....
import json #json parser
import logging

import pomocne_funkcije #pomocne funkcije i klase (npr. AppExcept exception...)
import networking_funkcije #web zahtjev, interface prema REST servisu
import dokument_model #interni model za zapisivanje podataka u dict pandas datafrejmova
import data_reader #REST reader/writer
import agregator #agregator
import model_drva #pomocne klase za definiranje tree modela programa mjerenja
import dodaj_ref_zs #dijalog za dodavanje referentnih zero i span vrijednosti
###############################################################################
###############################################################################
class Kontroler(QtCore.QObject):
    """
    Kontrolni dio aplikacije.
    Tu se nalazi glavna logika programa i povezivanje dijela akcija iz gui
    djela sa modelom.
    """
    def __init__(self, parent = None, gui = None):
        logging.debug('inicijalizacija kontrolora, start')
        QtCore.QObject.__init__(self, parent)
        ###inicijalizacija dokumenta###
        self.dokument = dokument_model.DataModel()
        ###incijalizacija satnog agregatora podataka###
        self.satniAgregator = agregator.Agregator()
        #gui element - instanca displaya
        self.gui = gui
        ###definiranje pomocnih membera###
        self.aktivniTab = self.gui.tabWidget.currentIndex() #koji je tab trenutno aktivan? bitno za crtanje
        self.pickedDate = None #zadnje izabrani datum, string 'yyyy-mm-dd'
        self.gKanal = None #trenutno aktivni glavni kanal, integer
        self.sat = None #zadnje izabrani sat na satnom grafu, bitno za crtanje minutnog
        self.tmin = None #donji rub vremenskog slajsa izabranog dana
        self.tmax = None #dornji rub vremenskog slajsa izabranog dana
        self.modelProgramaMjerenja = None #tree model programa mjerenja
        self.mapaMjerenjeIdToOpis = None #dict podataka o kanalu, kljuc je ID mjerenja
        self.appAuth = ("", "") #korisnicko ime i lozinka za REST servis
        self.setGlavnihKanala = set() #set glavnih kanala, prati koji su glavni kanali bili aktivni
        self.kalendarStatus = {} #dict koji prati za svaki kanalId da li su podaci ucitani i/ili spremljeni
        self.brojDana = 30 #max broj dana za zero span graf
        self.drawStatus = [False, False] #status grafa prema panelu [koncPanel, zsPanel]. True ako je graf nacrtan.

        ###povezivanje akcija sa funkcijama###
        self.setup_veze()
        logging.debug('inicijalizacija kontrolora, end')
###############################################################################
    def setup_veze(self):
        """
        Povezivanje emitiranih signala iz raznih dijelova aplikacije sa
        funkcijama koje definiraju tok programa.
        """
        ###ERROR MSG###
        #rest_izbornik
        self.connect(self.gui.restIzbornik,
                     QtCore.SIGNAL('error_message(PyQt_PyObject)'),
                     self.prikazi_error_msg)

        ###LOG IN REQUEST###
        self.connect(self.gui,
                     QtCore.SIGNAL('request_log_in(PyQt_PyObject)'),
                     self.user_log_in)

        ###LOG OUT REQUEST###
        self.connect(self.gui,
                     QtCore.SIGNAL('request_log_out'),
                     self.user_log_out)

        ###PROMJENA TABA U DISPLAYU###
        self.connect(self.gui,
                     QtCore.SIGNAL('tab_promjenjen(PyQt_PyObject)'),
                     self.promjena_aktivnog_taba)

        ###RECONNECT REQUEST###
        self.connect(self.gui,
                     QtCore.SIGNAL('request_reconnect'),
                     self.reconnect_to_REST)

        ###UPDATE BOJE NA KALENDARU REST IZBORNIKA###
        self.connect(self,
                     QtCore.SIGNAL('update_boje_kalendara(PyQt_PyObject)'),
                     self.gui.restIzbornik.calendarWidget.refresh_dates)

        ###GUMBI ZA PREBACIVANJE DANA NAPRIJED/NAZAD###
        #panel sa koncentracijama
        self.connect(self.gui.koncPanel,
                     QtCore.SIGNAL('prebaci_dan(PyQt_PyObject)'),
                     self.promjeni_datum)

        #naredba rest izborniku da napravi pomak dana
        self.connect(self,
                     QtCore.SIGNAL('dan_naprjed'),
                     self.gui.restIzbornik.sljedeci_dan)

        self.connect(self,
                     QtCore.SIGNAL('dan_nazad'),
                     self.gui.restIzbornik.prethodni_dan)

        ###UPDATE LABELA NA PANELIMA###
        #panel sa koncentracijama
        self.connect(self,
                     QtCore.SIGNAL('update_graf_label(PyQt_PyObject)'),
                     self.gui.koncPanel.change_glavniLabel)
        #panel sa zero/span podacima
        self.connect(self,
                     QtCore.SIGNAL('update_graf_label(PyQt_PyObject)'),
                     self.gui.zsPanel.change_glavniLabel)
        #panel sa koncentracijama, satni label
        self.connect(self,
                     QtCore.SIGNAL('update_sat_label(PyQt_PyObject)'),
                     self.gui.koncPanel.change_satLabel)

        ###PRIPREMA PODATAKA ZA CRTANJE (koncentracije)###
        self.connect(self.gui.restIzbornik,
                     QtCore.SIGNAL('gui_izbornik_citaj(PyQt_PyObject)'),
                     self.priredi_podatke)

        ###PROMJENA BROJA DANA U ZERO/SPAN PANELU###
        self.connect(self.gui.zsPanel,
                     QtCore.SIGNAL('request_zs_broj_dana_change(PyQt_PyObject)'),
                     self.update_zs_broj_dana)

        ###CRTANJE SATNOG GRAFA I INTERAKCIJA###
        #zahtjev satnog canvasa za agregiranim podacima
        self.connect(self.gui.koncPanel.satniGraf,
                     QtCore.SIGNAL('request_agregirani_frejm(PyQt_PyObject)'),
                     self.dohvati_agregirani_frejm)
        #slanje agregiranog frejma nazad satnom canvasu
        self.connect(self,
                     QtCore.SIGNAL('vrati_agregirani_frejm(PyQt_PyObject)'),
                     self.gui.koncPanel.satniGraf.set_agregirani_kanal)
        #zahtjev kontorlora za pocetkom crtanja satnog grafa
        self.connect(self,
                     QtCore.SIGNAL('nacrtaj_satni_graf(PyQt_PyObject)'),
                     self.gui.koncPanel.satniGraf.crtaj)
        #pick vremena sa satnog grafa - crtanje minutnog grafa za taj interval
        self.connect(self.gui.koncPanel.satniGraf,
                     QtCore.SIGNAL('gui_crtaj_minutni_graf(PyQt_PyObject)'),
                     self.crtaj_minutni_graf)
        #promjena flaga na satnom grafu
        self.connect(self.gui.koncPanel.satniGraf,
                     QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'),
                     self.promjeni_flag)

        ###POVRATNA INFORMACIJA DOKUMENTA DA JE DOSLO DO PROMJENE FLAGA###
        self.connect(self.dokument,
                     QtCore.SIGNAL('model_flag_changed'),
                     self.crtaj_satni_graf)

        ###CRTANJE MINUTNOG GRAFA I INTERAKCIJA###
        #zahtjev minutnoog canvasa za minutnim podacima
        self.connect(self.gui.koncPanel.minutniGraf,
                     QtCore.SIGNAL('request_minutni_frejm(PyQt_PyObject)'),
                     self.dohvati_minutni_frejm)
        #slanje minutnog frejma nazad minutnom canvasu
        self.connect(self,
                     QtCore.SIGNAL('vrati_minutni_frejm(PyQt_PyObject)'),
                     self.gui.koncPanel.minutniGraf.set_minutni_kanal)
        #zahtjev kontorlora za pocetkom crtanja minutnog grafa
        self.connect(self,
                     QtCore.SIGNAL('nacrtaj_minutni_graf(PyQt_PyObject)'),
                     self.gui.koncPanel.minutniGraf.crtaj)
        #clear minutnog grafa
        self.connect(self,
                     QtCore.SIGNAL('clear_minutni_graf'),
                     self.gui.koncPanel.minutniGraf.clear_minutni)
        #promjena flaga na minutnog grafu
        self.connect(self.gui.koncPanel.minutniGraf,
                     QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'),
                     self.promjeni_flag)

        ###CRTANJE ZERO/SPAN GRAFA I INTERAKCIJA###
        #clear zero/span grafova
        self.connect(self,
                     QtCore.SIGNAL('clearZeroSpan'),
                     self.gui.zsPanel.zeroGraf.clear_me)
        self.connect(self,
                     QtCore.SIGNAL('clearZeroSpan'),
                     self.gui.zsPanel.spanGraf.clear_me)
        #crtanje zero
        self.connect(self,
                     QtCore.SIGNAL('crtaj_zero(PyQt_PyObject)'),
                     self.gui.zsPanel.zeroGraf.crtaj)
        #crtanje span
        self.connect(self,
                     QtCore.SIGNAL('crtaj_span(PyQt_PyObject)'),
                     self.gui.zsPanel.spanGraf.crtaj)
        #setter podataka za tocku na zero grafu
        self.connect(self.gui.zsPanel.zeroGraf,
                     QtCore.SIGNAL('zero_point_update(PyQt_PyObject)'),
                     self.gui.zsPanel.prikazi_info_zero)
        #pick tocke na zero grafu - nadji najblizu tocku na span grafu
        self.connect(self.gui.zsPanel.zeroGraf,
                     QtCore.SIGNAL('zero_point_pick_update(PyQt_PyObject)'),
                     self.gui.zsPanel.spanGraf.pick_nearest)
        #setter podataka za tocku na span grafu
        self.connect(self.gui.zsPanel.spanGraf,
                     QtCore.SIGNAL('span_point_update(PyQt_PyObject)'),
                     self.gui.zsPanel.prikazi_info_span)
        #pick tocke na span grafu - nadji najblizu tocku na zero grafu
        self.connect(self.gui.zsPanel.spanGraf,
                     QtCore.SIGNAL('span_point_pick_update(PyQt_PyObject)'),
                     self.gui.zsPanel.zeroGraf.pick_nearest)

        #sync zooma po x osi za zero i span graf
        self.connect(self.gui.zsPanel.zeroGraf,
                     QtCore.SIGNAL('zero_sync_x_zoom(PyQt_PyObject)'),
                     self.gui.zsPanel.spanGraf.sync_x_zoom)
        self.connect(self.gui.zsPanel.spanGraf,
                     QtCore.SIGNAL('span_sync_x_zoom(PyQt_PyObject)'),
                     self.gui.zsPanel.zeroGraf.sync_x_zoom)

        ###DODAVANJE NOVE ZERO ILI SPAN REFERENTNE VRIJEDNOSTI###
        self.connect(self.gui.zsPanel,
                     QtCore.SIGNAL('dodaj_novi_zs_ref'),
                     self.dodaj_novu_referentnu_vrijednost)

        ###UPLOAD SATNO AGREGIRANIH NA REST SERVIS###
        self.connect(self.gui.restIzbornik,
                     QtCore.SIGNAL('request_upload_agregirane'),
                     self.upload_satno_agregirane)
        ###UPLOAD MINUTNIH PODATAKA NA REST SERVIS###
        self.connect(self.gui.restIzbornik,
                     QtCore.SIGNAL('request_upload_minutne'),
                     self.upload_minutne_na_REST)

        ###PROMJENA IZGLEDA GRAFA###
        self.connect(self.gui,
                     QtCore.SIGNAL('izgled_grafa_promjenjen'),
                     self.apply_promjena_izgleda_grafova)
###############################################################################
    def dohvati_minutni_frejm(self, lista):
        """
        Bitna metoda za crtanje minutnih podataka
        ulaz je lista sa 3 elementa
        lista[0] - id glavnog kanala mjerenja (int)
        lista[1] - tmin (pandas timestamp)
        lista[2] - tmax (pandas timestamp)
        """
        try:
            frejm = self.dokument.get_frame(key = lista[0], tmin = lista[1], tmax = lista[2])
        except pomocne_funkcije.AppExcept:
            logging.error('App exception.', exc_info = True)
            frejm = None
        #test za ispravnost vracenog frejma
        if isinstance(frejm, pd.core.frame.DataFrame):
            arg = [lista[0], frejm]
            self.emit(QtCore.SIGNAL('vrati_minutni_frejm(PyQt_PyObject)'), arg)
###############################################################################
    def dohvati_agregirani_frejm(self, lista):
        """
        Bitna metoda za crtanje satno agregiranih podataka.
        ulaz je lista sa 3 elementa
        lista[0] - id glavnog kanala (int)
        lista[1] - tmin, (pandas timestamp)
        lista[2] - tmax, (pandas timestamp)
        """
        try:
            frejm = self.dokument.get_frame(key = lista[0], tmin = lista[1], tmax = lista[2])
        except pomocne_funkcije.AppExcept:
            logging.error('App exception.', exc_info = True)
            frejm = None
        #test za ispravnost vracenog frejma
        if isinstance(frejm, pd.core.frame.DataFrame):
            #agregiraj frejm
            agregiraniFrejm = self.satniAgregator.agregiraj_kanal(frejm)
            #agregator ce vratiti None ako mu se prosljedi prazan frejm
            if isinstance(agregiraniFrejm, pd.core.frame.DataFrame):
                #vrati listu [kanal, agregiraniFrejm] nazad satnom grafu
                arg = [lista[0], agregiraniFrejm]
                self.emit(QtCore.SIGNAL('vrati_agregirani_frejm(PyQt_PyObject)'), arg)
###############################################################################
    def user_log_in(self, x):
        """
        - postavi podatke u self.appAuth
        - reinitialize connection objekt i sve objekte koji ovise o njemu.
        """
        self.appAuth = x
        #spoji se na rest
        self.reconnect_to_REST()
###############################################################################
    def user_log_out(self):
        """
        - clear self.appAuth
        - reinitialize connection objekt i sve objekte koji ovise o njemu.
        """
        self.appAuth = ("", "")
        self.reconnect_to_REST()
###############################################################################
    def initialize_web_and_rest_interface(self):
        """
        Inicijalizacija web zahtjeva i REST reader/writer objekata koji ovise o
        njemu.
        """
        #dohvati podatke o rest servisu
        baseurl = str(self.gui.appSettings.RESTBaseUrl)
        resursi = {'siroviPodaci':str(self.gui.appSettings.RESTSiroviPodaci),
                   'programMjerenja':str(self.gui.appSettings.RESTProgramMjerenja),
                   'zerospan':str(self.gui.appSettings.RESTZeroSpan),
                   'satniPodaci':str(self.gui.appSettings.RESTSatniPodaci)}
        #inicijalizacija webZahtjeva
        self.webZahtjev = networking_funkcije.WebZahtjev(baseurl, resursi, self.appAuth)
        #inicijalizacija REST readera
        self.restReader = data_reader.RESTReader(model = self.dokument, source = self.webZahtjev)
        #inicijalizacija REST writera agregiranih podataka
        self.restWriter = data_reader.RESTWriterAgregiranih(source = self.webZahtjev)
###############################################################################
    def konstruiraj_tree_model(self):
        """
        Povuci sa REST servisa sve programe mjerenja
        Pokusaj sastaviti model, tree strukturu programa mjerenja
        """
        try:
            #dohvati dictionary programa mjerenja sa rest servisa
            mapa = self.webZahtjev.get_programe_mjerenja()
            #spremi mapu u privatni member
            self.mapaMjerenjeIdToOpis = mapa
            #root objekt
            tree = model_drva.TreeItem(['stanice', None, None], parent = None)
            #za svaku individualnu stanicu napravi TreeItem objekt, reference objekta spremi u dict
            stanice = {}
            for i in sorted(list(mapa.keys())):
                stanica = mapa[i]['postajaNaziv']
                if stanica not in stanice:
                    stanice[stanica] = model_drva.TreeItem([stanica, None, None], parent = tree)
            #za svako individualnu komponentu napravi TreeItem sa odgovarajucim parentom (stanica)
            for i in mapa.keys():
                stanica = mapa[i]['postajaNaziv'] #parent = stanice[stanica]
                komponenta = mapa[i]['komponentaNaziv']
                #mjernaJedinica = mapa[i]['komponentaMjernaJedinica']
                usporedno = mapa[i]['usporednoMjerenje']
                #data = [komponenta, mjernaJedinica, i]
                data = [komponenta, usporedno, i]
                model_drva.TreeItem(data, parent = stanice[stanica]) #kreacija TreeItem objekta

            self.modelProgramaMjerenja = model_drva.ModelDrva(tree) #napravi model

        except pomocne_funkcije.AppExcept as err:
            #log error sa stack traceom exceptiona
            logging.error('App exception', exc_info = True)
            self.prikazi_error_msg(err)
###############################################################################
    def reconnect_to_REST(self):
        """
        inicijalizacija objekata vezanih za interakciju sa REST servisom
        -webZahtjev()
        -dataReader()
        -dataWriter()
        """
        #promjeni cursor u wait cursor
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        #inicijalizacija objekata
        self.initialize_web_and_rest_interface()

        #konstruiraj tree model programa mjerenja
        self.konstruiraj_tree_model()

        #postavi tree model u ciljani tree view widget na display
        if self.modelProgramaMjerenja != None:
            self.gui.restIzbornik.treeView.setModel(self.modelProgramaMjerenja)
            self.gui.restIzbornik.model = self.modelProgramaMjerenja
            logging.info('Tree model programa mjerenja uspjesno postavljen')
        else:
            logging.info('Tree model programa mjerenja nije uspjesno postavljen')

        #vrati izgled cursora nazad na normalni
        QtGui.QApplication.restoreOverrideCursor()
###############################################################################
    def prikazi_error_msg(self, poruka):
        """
        Prikaz informacijskog dijaloga nakon neke greske
        """
        #vrati izgled cursora nazad na normalni nakon exceptiona
        QtGui.QApplication.restoreOverrideCursor()
        #prikazi information dialog sa pogreskom
        #QtGui.QMessageBox.information(self.gui, 'Pogreska prilikom rada', str(poruka))
###############################################################################
    def priredi_podatke(self, lista):
        """
        Funkcija analizira zahtjev preuzet u obliku liste [programMjerenjaId, datum]
        te radi 4 bitne stvari:

        1. provjerava da li je zahtjev pomaknuo "fokus" sa prikazanih podataka
            - preciznije, usporedjuje membere self.gKanal, self.pickedDate
              sa nadolazecim zahtjevom
        2. Ucitava podatke sa REST servisa u dokument (priprema lokalnu kopiju za rad)
            - rest citac 'pamti' da li je vec obradio isti zahtjev pa se ucitava
              samo ako je potrebno
            - rest citac namjerno nece zapamtiti trenutni dan
        3. Postavlja odredjene membere potrebne za daljnji rad
            - self.gKanal --> trenutni glavni kanal za crtanje (programMjerenjaId)
            - self.tmin --> donji vremenski rub datuma (datum 00:01:00)
            - self.tmax --> gornji vremenski rub datuma (datum +1 dan 00:00:00)
            - self.pickedDate --> trenutno izabrani dan
        4. Pokrece proces crtanja

        """
        #reset status crtanja
        self.drawStatus = [False, False]
        print('priredi podatke {0}'.format(lista))
        self.gKanal = int(lista[0]) #informacija o glavnom kanalu
        datum = lista[1] #datum je string formata YYYY-MM-DD
        self.pickedDate = datum #postavi izabrani datum
        #pretvaranje datuma u 2 timestampa od 00:01:00 do 00:00:00 iduceg dana
        tsdatum = pd.to_datetime(datum)
        self.tmax = tsdatum + datetime.timedelta(days = 1)
        self.tmin = tsdatum + datetime.timedelta(minutes = 1)
        #za svaki slucaj, pobrinimo se da su varijable pandas.tslib.Timestamp
        self.tmax = pd.to_datetime(self.tmax)
        self.tmin = pd.to_datetime(self.tmin)
        sviBitniKanali = []
        sviBitniKanali.append(self.gKanal)
        #dodaj kanal sa temperaturom kontejnera ako postoji za tu stanicu
        #TODO!
        self.tKontejnerId = self.get_kanal_temp_kontenjera()
        if self.tKontejnerId is not None:
            sviBitniKanali.append(self.tKontejnerId)

        #prati koji su sve glavni kanali izabrani!!!
        self.setGlavnihKanala = self.setGlavnihKanala.union([self.gKanal])
        #pronadji sve ostale kanale potrebne za crtanje
        for key in self.gui.grafSettings.dictPomocnih:
            sviBitniKanali.append(key)
        #lista svih koji se nisu uspjeli ucitati
        notUcitani = []
        #pokusaj ucitati sve bitne kanale (glavni + pomocni kanali
        for kanal in sviBitniKanali:
            try:
                #citanje pojedinog kanala (ukljucujuci i pomocne)
                self.restReader.read(key = kanal, date = datum)
                #update kalendarStatus
                self.update_kalendarStatus(kanal, datum, 'ucitani')
            except pomocne_funkcije.AppExcept as e1:
                logging.info('Kanal nije ucitan u dokument, kanal = {0}'.format(str(kanal)), exc_info = True)
                #dodaj listu [kanal, datum] u listu notUcitani
                notUcitani.append([kanal, datum, e1])
        #update boju na kalendaru ovisno o ucitanim podacima
        self.promjena_boje_kalendara()
        if len(notUcitani) > 0:
            #neki se nisu ucitali u dokument, informiraj koirsnika
            msg = 'Sljedeci kanali nisu ucitani:\n'
            for i in notUcitani:
                msg = msg + str(notUcitani[i][0])+','
            #prokazi informacijski dijalog ?
            self.prikazi_error_msg(msg)

        #update lebele na panelima (povratna informacija koji je kanal aktivan i za koje vrijeme)
        argList = [self.mapaMjerenjeIdToOpis[self.gKanal], self.pickedDate]
        self.emit(QtCore.SIGNAL('update_graf_label(PyQt_PyObject)'), argList)
        #pokreni crtanje, ali ovisno o tabu koji je aktivan
        self.promjena_aktivnog_taba(self.aktivniTab)
###############################################################################
    def crtaj_satni_graf(self):
        """
        Funkcija koja emitira signal sa naredbom za crtanje samo ako je prethodno
        zadan datum, tj. donja i gornja granica intervala i glavni kanal.
        """
        if (self.tmin != None and self.tmax != None and self.gKanal != None):
            self.emit(QtCore.SIGNAL('nacrtaj_satni_graf(PyQt_PyObject)'), {'kanalId' : self.gKanal, 'pocetnoVrijeme': self.tmin, 'zavrsnoVrijeme' : self.tmax, 'tempKontejner'  : self.tKontejnerId})
            #promjena labela u panelima sa grafovima, opis
            try:
                opisKanala = self.mapaMjerenjeIdToOpis[self.gKanal]
                argList = [opisKanala, str(self.tmin), str(self.tmax)]
                self.emit(QtCore.SIGNAL('update_graf_label(PyQt_PyObject)'), argList)
                """
                opis naredbi koje sljede:
                Zanima nas da li je netko vec odabrao satni interval za minutni graf.
                Zanima nas da li je satni interval unutar izabranog datuma.
                Bitno je jer u slucaju promjene datuma minutni graf ce ostati
                prikazivati zadnji satni interval. Da ne bi doslo do zabune (potencijalno
                dva grafa mogu prikazivati razlicite kanale i/ili datume), moramo
                "clearati" graf ili narediti ponovno crtanje minutnog grafa.
                """
                if self.sat != None:
                    if (self.sat >= self.tmin and self.sat <= self.tmax):
                        self.crtaj_minutni_graf(self.sat)
                    else:
                        #clear minutni graf ako se datum pomakne
                        self.emit(QtCore.SIGNAL('clear_minutni_graf'))
                        #clear izabrani label sata
                        self.emit(QtCore.SIGNAL('update_sat_label(PyQt_PyObject)'), '')
            except (TypeError, LookupError) as err:
                print(err)
                self.prikazi_error_msg(err)
###############################################################################
    def crtaj_zero_span(self):
        """
        Crtanje zero span podataka.
        1. dohvati podatke sa REST servisa,
        2. update label
        3. naredi crtanje istih
        """
        self.emit(QtCore.SIGNAL('clearZeroSpan'))
        try:
            if not self.gKanal:
                raise pomocne_funkcije.AppExcept('Glavni kanal nije izabran, abort')
            #dokvati listu [zeroFrejm, spanFrejm]
            frejmovi = self.webZahtjev.get_zero_span(self.gKanal, self.pickedDate, self.brojDana)

            #sync max raspona x osi (vremena)
            raspon = pomocne_funkcije.sync_zero_span_x_os(frejmovi)

            if frejmovi != None:
                outputZero = [frejmovi[0], self.gui.grafSettings, raspon]
                outputSpan = [frejmovi[1], self.gui.grafSettings, raspon]
                #emitiraj signal za crtanjem
                self.emit(QtCore.SIGNAL('crtaj_zero(PyQt_PyObject)'), outputZero)
                self.emit(QtCore.SIGNAL('crtaj_span(PyQt_PyObject)'), outputSpan)
            else:
                #nema podataka
                raise pomocne_funkcije.AppExcept('Nema raspolozivih podataka')

        except pomocne_funkcije.AppExcept as err:
            logging.error('Problem kod ucitavanje zero/span sa REST servisa.', exc_info = True)
            opis = 'Problem kod ucitavanja Zero/Span podataka sa REST servisa.' + str(err)
            self.prikazi_error_msg(opis)
        except AttributeError as err2:
            logging.error('web interface nije incijaliziran, Potrebno se ulogirati.', exc_info = True)
            opis = 'Problem kod ucitavanja Zero/Span podataka sa REST servisa.'+ str(err2)
            self.prikazi_error_msg(opis)
###############################################################################
    def crtaj_minutni_graf(self, izabrani_sat):
        """
        Ova funkcija se brine za pravilni odgovor na ljevi klik tocke na satno
         agregiranom grafu. Za zadani sat, odredjuje rubove intervala te salje
        dobro zadani zahtjev za crtanjem minutnom canvasu.
        """
        self.sat = izabrani_sat
        if self.sat <= self.tmax and self.sat >=self.tmin:
            highLim = self.sat
            lowLim = highLim - datetime.timedelta(minutes = 59)
            lowLim = pd.to_datetime(lowLim)
            #update labela izabranog sata
            self.emit(QtCore.SIGNAL('update_sat_label(PyQt_PyObject)'), self.sat)
            self.emit(QtCore.SIGNAL('nacrtaj_minutni_graf(PyQt_PyObject)'),[self.gKanal, lowLim, highLim, self.gui.grafSettings, self.gui.appSettings, self.tKontejnerId])
###############################################################################
    def dodaj_novu_referentnu_vrijednost(self):
        """
        Poziv dijaloga za dodavanje nove referentne vrijednosti za zero ili
        span. Upload na REST servis.
        """
        if self.mapaMjerenjeIdToOpis != None and self.gKanal != None:
            #dict sa opisnim parametrima za kanal
            postaja  = self.mapaMjerenjeIdToOpis[self.gKanal]['postajaNaziv']
            komponenta = self.mapaMjerenjeIdToOpis[self.gKanal]['komponentaNaziv']
            formula = self.mapaMjerenjeIdToOpis[self.gKanal]['komponentaFormula']
            opis = '{0}, {1}( {2} )'.format(postaja, komponenta, formula)

            dijalog = dodaj_ref_zs.DijalogDodajRefZS(parent = None, opisKanal = opis, idKanal = self.gKanal)
            if dijalog.exec_():
                podaci = dijalog.vrati_postavke()
                try:
                    #test da li je sve u redu?
                    assert isinstance(podaci['vrijednost'], float), 'Neuspjeh. Podaci nisu spremljeni na REST servis.\nReferentna vrijednost je krivo zadana.'
                    #napravi json string za upload (dozvoljeno odstupanje je placeholder)
                    #int od vremena... output je double zboj milisekundi
                    jS = {"vrijeme":int(podaci['vrijeme']),
                          "vrijednost":podaci['vrijednost'],
                          "vrsta":podaci['vrsta'],
                          "maxDozvoljeno":0.0,
                          "minDozvoljeno":0.0}

                    #dict to json dump
                    jS = json.dumps(jS)
                    #potvrda za unos!
                    odgovor = QtGui.QMessageBox.question(self.gui,
                                                         "Potvrdi upload na REST servis",
                                                         "Potvrdite spremanje podataka na REST servis",
                                                         QtGui.QMessageBox.Yes|QtGui.QMessageBox.No)

                    if odgovor == QtGui.QMessageBox.Yes:
                        #put json na rest!
                        self.webZahtjev.upload_ref_vrijednost_zs(jS, self.gKanal)
                        #confirmation da je uspjelo
                        QtGui.QMessageBox.information(self.gui, "Potvrda unosa na REST", "Podaci sa novom referentnom vrijednosti uspjesno su spremljeni na REST servis")
                        logging.info('Uspjesno dodana nova referentna vrijednost zero/span. json = {0}'.format(jS))
                except AssertionError as err:
                    logging.error('Pogreska kod zadavanja referentne vrijednosti za zero ili span (nije float)', exc_info = True)
                    self.prikazi_error_msg(str(err))
                except pomocne_funkcije.AppExcept as err2:
                    logging.error('Pogreska kod uploada referentne vrijednosti zero/span na servis.', exc_info = True)
                    self.prikazi_error_msg(str(err2))
        else:
            logging.info('pokusaj dodavanje ref vrijednosti bez ucitanih kanala mjerenja ili bez izabranog kanala')
            self.prikazi_error_msg('Neuspjeh. Programi mjerenja nisu ucitani ili kanal nije izabran')
###############################################################################
    def upload_minutne_na_REST(self):
        """
        Dohvati trenutno aktivni kanal i vrijeme adaptiraj i upload na REST
        """
        if self.gKanal != None and self.pickedDate != None:
            try:
                #promjeni cursor u wait cursor
                QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                #dohvati frame iz dokumenta
                frejm = self.dokument.get_frame(key = self.gKanal, tmin = self.tmin, tmax = self.tmax)
                assert type(frejm) == pd.core.frame.DataFrame, 'Kontroler.upload_minutne_to_REST:Assert fail, frame pogresnog tipa'
                if len(frejm):
                    testValidacije = frejm['flag'].map(self.test_stupnja_validacije)
                    lenSvih = len(testValidacije)
                    lenDobrih = len(testValidacije[testValidacije == True])
                    if lenSvih == lenDobrih:
                        msg = msg = 'Spremi minutne podatke od ' + str(self.gKanal) + ':' + str(self.tmin.date()) + ' na REST web servis?'
                    else:
                        msg = 'Neki podaci nisu validirani.\nNije moguce spremiti minutne podatke na REST servis.'
                        #raise assertion error (izbaciti ce dijalog sa informacijom da nije moguce spremiti podatke)
                        raise AssertionError(msg)

                    #privremeno vrati izgled cursora nazad na normalni
                    QtGui.QApplication.restoreOverrideCursor()
                    #prompt izbora za spremanje filea, question
                    odgovor = QtGui.QMessageBox.question(self.gui,
                                                         "Potvrdi upload na REST servis",
                                                         msg,
                                                         QtGui.QMessageBox.Yes|QtGui.QMessageBox.No)
                    if odgovor == QtGui.QMessageBox.Yes:
                        #ponovno prebaci na wait cursor
                        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                        #napravi prazan dataframe indeksiran na isti nacin kao agregirani
                        output = pd.DataFrame(index = frejm.index)
                        #dodaj trazene stupce u output frejm

                        output['vrijeme'] = frejm.index
                        output['vrijednost'] = frejm['koncentracija']
                        output['id'] = frejm['id']
                        output['valjan'] = frejm['flag'].map(pomocne_funkcije.int_to_boolean)
                        #konverzija output frejma u json string
                        jstring = output.to_json(orient = 'records')
                        #upload uz pomoc rest writera
                        self.restWriter.upload_minutne(jso = jstring)
                        #update status kalendara
                        self.update_kalendarStatus(self.gKanal, self.pickedDate, 'spremljeni')
                        self.promjena_boje_kalendara()
                #vrati izgled cursora nazad na normalni
                QtGui.QApplication.restoreOverrideCursor()
            except AssertionError as e1:
                logging.error('Nema podataka ili svi nisu validirani.', exc_info = True)
                self.prikazi_error_msg(e1)
            except pomocne_funkcije.AppExcept as e2:
                logging.error('Error prilikom uploada na rest servis', exc_info = True)
                self.prikazi_error_msg(e2)
            finally:
                #vrati izgled cursora nazad na normalni
                QtGui.QApplication.restoreOverrideCursor()
###############################################################################
    def upload_satno_agregirane(self):
        """
        Dohvati trenutno aktivni kanal i vrijeme, agregiraj i upload na rest
        """
        if self.gKanal != None and self.pickedDate != None:
            try:
                #promjeni cursor u wait cursor
                QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

                #dohvati frame iz dokumenta
                frejm = self.dokument.get_frame(key = self.gKanal, tmin = self.tmin, tmax = self.tmax)

                assert type(frejm) == pd.core.frame.DataFrame, 'Kontroler.upload_agregirane_to_REST:Assert fail, frame pogresnog tipa'
                if len(frejm):
                    #agregiraj podatke
                    agregirani = self.satniAgregator.agregiraj_kanal(frejm)

                    #provjeri stupanj validacije agregiranog frejma
                    testValidacije = agregirani[u'flag'].map(self.test_stupnja_validacije)
                    lenSvih = len(testValidacije)
                    lenDobrih = len(testValidacije[testValidacije == True])

                    if lenSvih == lenDobrih:
                        msg = msg = 'Spremi agregirane podatke od ' + str(self.gKanal) + ':' + str(self.tmin.date()) + ' na REST web servis?'
                    else:
                        msg = 'Neki podaci nisu validirani.\nNije moguce spremiti agregirane podatke na REST servis.'
                        #raise assertion error (izbaciti ce dijalog sa informacijom da nije moguce spremiti podatke)
                        raise AssertionError(msg)

                    #privremeno vrati izgled cursora nazad na normalni
                    QtGui.QApplication.restoreOverrideCursor()
                    #prompt izbora za spremanje filea, question
                    odgovor = QtGui.QMessageBox.question(self.gui,
                                                         "Potvrdi upload na REST servis",
                                                         msg,
                                                         QtGui.QMessageBox.Yes|QtGui.QMessageBox.No)
                    if odgovor == QtGui.QMessageBox.Yes:
                        #ponovno prebaci na wait cursor
                        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                        #napravi prazan dataframe indeksiran na isti nacin kao agregirani
                        output = pd.DataFrame(index = agregirani.index)
                        #dodaj trazene stupce u output frejm
                        output['programMjerenjaId'] = int(self.gKanal)
                        output['vrijeme'] = agregirani.index
                        output['vrijednost'] = agregirani['avg']
                        output['status'] = agregirani['status']
                        output['obuhvat'] = agregirani['count'].map(self.agregirani_count_to_postotak)
                        #konverzija output frejma u json string
                        jstring = output.to_json(orient = 'records')
                        #upload uz pomoc rest writera
                        self.restWriter.upload_agregirane(jso = jstring)
                        #update status kalendara
                        self.update_kalendarStatus(self.gKanal, self.pickedDate, 'spremljeni')
                        self.promjena_boje_kalendara()

                #vrati izgled cursora nazad na normalni
                QtGui.QApplication.restoreOverrideCursor()
            except AssertionError as e1:
                logging.error('Nema podataka ili svi nisu validirani.', exc_info = True)
                self.prikazi_error_msg(e1)
            except pomocne_funkcije.AppExcept as e2:
                logging.error('Error prilikom uploada na rest servis', exc_info = True)
                self.prikazi_error_msg(e2)
            finally:
                #vrati izgled cursora nazad na normalni
                QtGui.QApplication.restoreOverrideCursor()
###############################################################################
    def test_stupnja_validacije(self, x):
        """
        Pomocna funkcija, provjerava da li je vrijednost 1000 ili -1000.
        """
        if abs(x) == 1000:
            return True
        else:
            return False
###############################################################################
    def agregirani_count_to_postotak(self, x):
        """
        Pomocna funkcija za racunanje obuhvata agregiranih podataka
        """
        return int(x*100/60)
###############################################################################
    def update_kalendarStatus(self, progMjer, datum, tip):
        """
        dodavanje datuma na popis ucitanih i ili validiranih ovisno o tipu
        i programu mjerenja.

        progMjer --> program mjerenja id, integer
        datum --> string reprezentacija datuma  'yyyy-MM-dd' formata
        tip --> 'ucitani' ili 'spremljeni'
        """
        datum = QtCore.QDate.fromString(datum, 'yyyy-MM-dd')
        if progMjer in self.kalendarStatus:
            if tip == 'spremljeni':
                if datum not in self.kalendarStatus[progMjer]['ok']:
                    self.kalendarStatus[progMjer]['ok'].append(datum)
            else:
                if datum not in self.kalendarStatus[progMjer]['bad']:
                    self.kalendarStatus[progMjer]['bad'].append(datum)
        else:
            self.kalendarStatus[progMjer] = {'ok':[], 'bad':[datum]}
###############################################################################
    def promjena_boje_kalendara(self):
        """
        Funkcija emitira signal sa podacima o boji za glavni kanal (self.gKanal)
        """
        self.emit(QtCore.SIGNAL('update_boje_kalendara(PyQt_PyObject)'), self.kalendarStatus[self.gKanal])
###############################################################################
    def promjeni_datum(self, x):
        """
        Odgovor na zahtjev za pomicanjem datuma za 1 dan (gumbi sljedeci/prethodni)
        Emitiraj signal da izbornik promjeni datum ovisno o x. Ako je x == 1
        prebaci 1 dan naprijed, ako je x == -1 prebaci jedan dan nazad
        """
        if x == 1:
            self.emit(QtCore.SIGNAL('dan_naprjed'))
        else:
            self.emit(QtCore.SIGNAL('dan_nazad'))
###############################################################################
    def update_zs_broj_dana(self, x):
        """
        Preuzimanje zahtjeva za promjenom broja dana na zero span grafu.
        Ponovno crtanje grafa.
        """
        self.brojDana = int(x)
        self.crtaj_zero_span()
###############################################################################
    def promjena_aktivnog_taba(self, x):
        """
        Promjena aktivnog taba u displayu
        - promjeni member self.aktivniTab
        - kreni crtati grafove za ciljani tab ako prije nisu nacrtani
        """
        self.aktivniTab = x
        if x == 0 and not self.drawStatus[0]:
            self.crtaj_satni_graf()
            self.drawStatus[0] = True
        elif x == 1 and not self.drawStatus[1]:
            self.crtaj_zero_span()
            self.drawStatus[0] = False
###############################################################################
    def apply_promjena_izgleda_grafova(self):
        """
        funkcija se pokrece nakon izlaska iz dijaloga za promjenu grafova.
        Naredba da se ponovno nacrtaju svi grafovi
        """
        self.crtaj_satni_graf()
        self.crtaj_zero_span()
###############################################################################
    def promjeni_flag(self, lista):
        """
        Odgovor kontrolora na zahtjev za promjenom flaga. Kontrolor naredjuje
        dokumentu da napravi odgovarajucu izmjenu.
        Ulazni parametar je lista koja sadrzi [tmin, tmax, novi flag, kanal].
        tocan vremenski interval (rubovi su ukljuceni), novu vrijednost flaga,
        te program mjerenja (kanal) na koji se promjena odnosi.

        P.S. dokument ima vlastiti signal da javi kada je doslo do promjene

        QtCore.SIGNAL('model_flag_changed')
        """
        self.dokument.change_flag(key = lista[3], tmin = lista[0], tmax = lista[1], flag = lista[2])
###############################################################################
    def exit_check(self):
        """
        Funkcija sluzi za provjeru spremljenog rada prije izlaska iz aplikacije.

        provjerava za svaki ucitani glavni kanal, datume ucitanih i datume
        uspjesno spremljenih na REST.

        Funkcija vraca boolean ovisno o jednakosti skupova datuma.

        poziva ga glavniprozor.py - u overloadanoj metodi za izlaz iz aplikacije
        """
        out = True
        for kanal in self.setGlavnihKanala:
            if set(self.kalendarStatus[kanal]['ok']) == set(self.kalendarStatus[kanal]['bad']):
                out = out and True
            else:
                out = out and False
        #return rezultat (upozori da neki podaci NISU spremljeni na REST)
        return out
###############################################################################
    def get_kanal_temp_kontenjera(self):
        """
        iz dicta programa mjerenja i glavnog kanala dohvati programMjerenjaId
        odgovarajuceg mjerenja Temperature kontejnera za tu stanicu (ako
        postoji, ako ne vrati None)
        """
        stanica = self.mapaMjerenjeIdToOpis[self.gKanal]['postajaId']
        for key in self.mapaMjerenjeIdToOpis:
            if self.mapaMjerenjeIdToOpis[key]['postajaId'] is stanica:
                if self.mapaMjerenjeIdToOpis[key]['komponentaNaziv'] == 'Temperatura kontejnera':
                    if key is not self.gKanal:
                        return key
###############################################################################
###############################################################################