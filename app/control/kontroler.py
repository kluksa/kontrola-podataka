# -*- coding: utf-8 -*-
"""
Created on Thu Jan 22 09:52:37 2015

@author: User
"""
from PyQt4 import QtCore, QtGui
import datetime  # python datetime objekt, potreban za timedelta isl.
import pandas as pd
# import os #pristup direktorijima, provjere postojanja filea....
import json  # json parser
import logging

import app.general.pomocne_funkcije as pomocne_funkcije  # pomocne funkcije i klase (npr. AppExcept exception...)
import app.general.networking_funkcije as networking_funkcije  # web zahtjev, interface prema REST servisu
import app.model.dokument_model as dokument_model  # interni model za zapisivanje podataka u dict pandas datafrejmova
import app.model.data_reader as data_reader  # REST reader/writer
import app.general.agregator as agregator  # agregator
import app.model.model_drva as model_drva  # pomocne klase za definiranje tree modela programa mjerenja
import app.view.dodaj_ref_zs as dodaj_ref_zs  # dijalog za dodavanje referentnih zero i span vrijednosti
###############################################################################
###############################################################################
class Kontroler(QtCore.QObject):
    """
    Kontrolni dio aplikacije.
    Tu se nalazi glavna logika programa i povezivanje dijela akcija iz gui
    djela sa modelom.
    """

    def __init__(self, parent=None, gui=None):
        logging.debug('inicijalizacija kontrolora, start')
        QtCore.QObject.__init__(self, parent)
        ###incijalizacija satnog agregatora podataka###
        self.satniAgregator = agregator.Agregator()
        ###inicijalizacija dokumenta###
        self.dokument = dokument_model.DataModel()
        # postavljanje agregatora u model
        self.dokument.set_agregator(self.satniAgregator)
        # gui element - instanca displaya
        self.gui = gui
        ###definiranje pomocnih membera###
        self.aktivniTab = self.gui.tabWidget.currentIndex()  #koji je tab trenutno aktivan? bitno za crtanje
        self.pickedDate = None  #zadnje izabrani datum, string 'yyyy-mm-dd'
        self.gKanal = None  #trenutno aktivni glavni kanal, integer
        self.sat = None  #zadnje izabrani sat na satnom grafu, bitno za crtanje minutnog
        self.pocetnoVrijeme = None  #donji rub vremenskog slajsa izabranog dana
        self.zavrsnoVrijeme = None  #gornji rub vremenskog slajsa izabranog dana
        self.modelProgramaMjerenja = None  #tree model programa mjerenja
        self.mapaMjerenjeIdToOpis = None  #dict podataka o kanalu, kljuc je ID mjerenja
        self.appAuth = ("", "")  #korisnicko ime i lozinka za REST servis
        self.setGlavnihKanala = set()  #set glavnih kanala, prati koji su glavni kanali bili aktivni
        self.kalendarStatus = {}  #dict koji prati za svaki kanalId da li su podaci ucitani i/ili spremljeni
        self.brojDana = 30  #max broj dana za zero span graf
        self.drawStatus = [False, False]  #status grafa prema panelu [koncPanel, zsPanel]. True ako je graf nacrtan.
        self.zeroFrejm = None  #member sa trenutnim Zero frejmom
        self.spanFrejm = None  #member sa trenutnim Span frejmom
        self.sviBitniKanali = []  #lista potrebnih programMjerenjaId (kanala) za crtanje. Refresh za svaki izbor kanala i datuma.
        self.frejmovi = {}  #mapa aktualnih frejmova (programMjerenjaId:slajs)
        self.agregiraniFrejmovi = {}  #mapa aktualnih agregiranih frejmova (programMjerenjaId:slajs)
        self.brojDanaSatni = 1 #member prati koliko dana se prikazuje za satno agregirani graf
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
        # rest_izbornik
        self.connect(self.gui.restIzbornik,
                     QtCore.SIGNAL('prikazi_error_msg(PyQt_PyObject)'),
                     self.prikazi_error_msg)

        ###LOG IN REQUEST###
        self.connect(self.gui,
                     QtCore.SIGNAL('user_log_in(PyQt_PyObject)'),
                     self.user_log_in)

        ###LOG OUT REQUEST###
        self.connect(self.gui,
                     QtCore.SIGNAL('user_log_out'),
                     self.user_log_out)

        ###PROMJENA TABA U DISPLAYU###
        self.connect(self.gui,
                     QtCore.SIGNAL('promjena_aktivnog_taba(PyQt_PyObject)'),
                     self.promjena_aktivnog_taba)

        ###RECONNECT REQUEST###
        self.connect(self.gui,
                     QtCore.SIGNAL('reconnect_to_REST'),
                     self.reconnect_to_REST)

        ###GUMBI ZA PREBACIVANJE DANA NAPRIJED/NAZAD###
        # panel sa koncentracijama
        self.connect(self.gui.koncPanel,
                     QtCore.SIGNAL('promjeni_datum(PyQt_PyObject)'),
                     self.promjeni_datum)

        ###PRIPREMA PODATAKA ZA CRTANJE (koncentracije)###
        self.connect(self.gui.restIzbornik,
                     QtCore.SIGNAL('priredi_podatke(PyQt_PyObject)'),
                     self.priredi_podatke)
        self.connect(self.gui.restIzbornik,
                     QtCore.SIGNAL('priredi_podatke(PyQt_PyObject)'),
                     self.gui.visednevniPanel.set_gKanal)

        ###PROMJENA BROJA DANA U ZERO/SPAN PANELU###
        self.connect(self.gui.zsPanel,
                     QtCore.SIGNAL('update_zs_broj_dana(PyQt_PyObject)'),
                     self.update_zs_broj_dana)

        ###CRTANJE SATNOG GRAFA I INTERAKCIJA###
        #pick vremena sa satnog grafa - crtanje minutnog grafa za taj interval
        self.connect(self.gui.koncPanel.satniGraf,
                     QtCore.SIGNAL('crtaj_minutni_graf(PyQt_PyObject)'),
                     self.crtaj_minutni_graf)
        #promjena flaga na satnom grafu
        self.connect(self.gui.koncPanel.satniGraf,
                     QtCore.SIGNAL('promjeni_flag(PyQt_PyObject)'),
                     self.promjeni_flag)

        ###POVRATNA INFORMACIJA DOKUMENTA DA JE DOSLO DO PROMJENE FLAGA###
        self.connect(self.dokument,
                     QtCore.SIGNAL('model_flag_changed'),
                     self.crtaj_satni_graf)
        ###CRTANJE MINUTNOG GRAFA I INTERAKCIJA###
        #promjena flaga na minutnog grafu
        self.connect(self.gui.koncPanel.minutniGraf,
                     QtCore.SIGNAL('promjeni_flag(PyQt_PyObject)'),
                     self.promjeni_flag)

        ###CRTANJE ZERO/SPAN GRAFA I INTERAKCIJA###
        #setter podataka za tocku na zero grafu
        self.connect(self.gui.zsPanel.zeroGraf,
                     QtCore.SIGNAL('prikazi_info_zero(PyQt_PyObject)'),
                     self.gui.zsPanel.prikazi_info_zero)
        #pick tocke na zero grafu - nadji najblizu tocku na span grafu
        self.connect(self.gui.zsPanel.zeroGraf,
                     QtCore.SIGNAL('pick_nearest(PyQt_PyObject)'),
                     self.gui.zsPanel.spanGraf.pick_nearest)
        #setter podataka za tocku na span grafu
        self.connect(self.gui.zsPanel.spanGraf,
                     QtCore.SIGNAL('prikazi_info_span(PyQt_PyObject)'),
                     self.gui.zsPanel.prikazi_info_span)
        #pick tocke na span grafu - nadji najblizu tocku na zero grafu
        self.connect(self.gui.zsPanel.spanGraf,
                     QtCore.SIGNAL('pick_nearest(PyQt_PyObject)'),
                     self.gui.zsPanel.zeroGraf.pick_nearest)

        ###CRTANJE SATNO AGREGIRANIH PODATAKA SA RESTA###
        self.connect(self.gui.visednevniPanel,
                     QtCore.SIGNAL('nacrtaj_rest_satne(PyQt_PyObject)'),
                     self.nacrtaj_rest_satne)

        ###DODAVANJE NOVE ZERO ILI SPAN REFERENTNE VRIJEDNOSTI###
        self.connect(self.gui.zsPanel,
                     QtCore.SIGNAL('dodaj_novu_referentnu_vrijednost'),
                     self.dodaj_novu_referentnu_vrijednost)
        ###PROMJENA IZGLEDA GRAFA###
        self.connect(self.gui,
                     QtCore.SIGNAL('apply_promjena_izgleda_grafova'),
                     self.apply_promjena_izgleda_grafova)
        ###GUMB NA KONCENTRACIJSKOM PANELU ZA PONISTAVANJE IZMJENA###
        self.connect(self.gui.koncPanel,
                     QtCore.SIGNAL('ponisti_izmjene'),
                     self.ponisti_izmjene)
        ###GUMB NA KONCENTRACIJSKOM PANELU ZA SPREMANJE NA REST###
        self.connect(self.gui.koncPanel,
                     QtCore.SIGNAL('upload_minutne_na_REST'),
                     self.upload_minutne_na_REST)
        ###update labela na koncentracijskom panelu###
        self.connect(self.gui.koncPanel.satniGraf,
                     QtCore.SIGNAL('set_labele_satne_tocke(PyQt_PyObject)'),
                     self.gui.koncPanel.set_labele_satne_tocke)
        self.connect(self.gui.koncPanel.minutniGraf,
                     QtCore.SIGNAL('set_labele_minutne_tocke(PyQt_PyObject)'),
                     self.gui.koncPanel.set_labele_minutne_tocke)
        ###update labela za satnu rest tocku###
        self.connect(self.gui.visednevniPanel.satniRest,
                     QtCore.SIGNAL('set_labele_rest_satne_tocke(PyQt_PyObject)'),
                     self.gui.visednevniPanel.prikazi_info_satni_rest)
        ###promjena max broja dana za satni graf...
        self.connect(self.gui.koncPanel,
                     QtCore.SIGNAL('promjeni_max_broj_dana_satnog(PyQt_PyObject)'),
                     self.promjeni_max_broj_dana_satnog)
    ###############################################################################
    def promjeni_max_broj_dana_satnog(self, x):
        """
        promjena raspona max broja dana za satno agregirani graf. ulazni parametar
        x je broj dana, integer u rasponu [1-5].
        """
        self.brojDanaSatni = int(x)
        #ako su izabrani glank i datum, ponovno nacrtaj graf
        if self.gKanal != None and self.pickedDate != None:
            self.priredi_podatke({'programMjerenjaId':self.gKanal, 'datumString':self.pickedDate})
    ###############################################################################
    def napravi_listu_dana(self, datum, brojDana):
        """
        Funkcija uzima datum string formata 'YYYY-MM-DD' i integer broja dana.
        Izlaz fukcije je lista QDate objekata (datum i N prethodnih dana)
        """
        date = datetime.datetime.strptime(datum, '%Y-%m-%d')
        popis = [date-datetime.timedelta(days=i) for i in range(brojDana)]
        izlaz = [QtCore.QDate(i) for i in popis]
        return izlaz
    ###############################################################################
    def user_log_in(self, x):
        """
        - postavi podatke u self.appAuth
        - reinitialize connection objekt i sve objekte koji ovise o njemu.
        """
        self.appAuth = x
        # spoji se na rest
        self.reconnect_to_REST()
    ###############################################################################
    def user_log_out(self):
        """
        - clear self.appAuth
        - reinitialize connection objekt i sve objekte koji ovise o njemu.
        - mankuti tree view
        - clear grafove
        """
        self.appAuth = ("", "")
        #reset webZahtjev, dokumnet....
        self.initialize_web_and_rest_interface(False)

        #reset tree view model... prikazi nista.
        tree = model_drva.TreeItem(['stanice', None, None, None], parent=None)
        self.modelProgramaMjerenja = model_drva.ModelDrva(tree)
        #set model to views
        self.gui.restIzbornik.treeView.setModel(self.modelProgramaMjerenja)
        self.gui.restIzbornik.model = self.modelProgramaMjerenja
        #clear glavni kanal i datum, clear sve grafove
        self.gKanal = None
        self.pickedDate = None
        self.gui.koncPanel.satniGraf.clear_graf()
        self.gui.koncPanel.minutniGraf.clear_graf()
        self.gui.zsPanel.zeroGraf.clear_graf()
        self.gui.zsPanel.spanGraf.clear_graf()
        self.gui.visednevniPanel.satniRest.clear_graf()
    ###############################################################################
    def initialize_web_and_rest_interface(self, tip):
        """
        Inicijalizacija web zahtjeva i REST reader/writer objekata koji ovise o
        njemu.
        Takodjer dohvati i mapu status codea  i postavi je u minutni i satni kanvas
        Tip je boolean vrijednost... True za log in, False za log out
        """
        # dohvati podatke o rest servisu
        baseurl = str(self.gui.konfiguracija.REST.RESTBaseUrl)
        resursi = {'siroviPodaci': str(self.gui.konfiguracija.REST.RESTSiroviPodaci),
                   'programMjerenja': str(self.gui.konfiguracija.REST.RESTProgramMjerenja),
                   'zerospan': str(self.gui.konfiguracija.REST.RESTZeroSpan),
                   'satniPodaci': str(self.gui.konfiguracija.REST.RESTSatniPodaci),
                   'statusMap': str(self.gui.konfiguracija.REST.RESTStatusMap)}
        # inicijalizacija webZahtjeva
        self.webZahtjev = networking_funkcije.WebZahtjev(baseurl, resursi, self.appAuth)
        #inicijalizacija REST readera
        self.restReader = data_reader.RESTReader(source=self.webZahtjev)
        #postavljanje readera u model
        self.dokument.set_reader(self.restReader)
        #inicijalizacija REST writera agregiranih podataka
        self.restWriter = data_reader.RESTWriter(source=self.webZahtjev)
        #postavljanje writera u model
        self.dokument.set_writer(self.restWriter)
        if tip:
            try:
                statusMapa = self.webZahtjev.get_statusMap()
                self.dokument.set_statusMap(statusMapa)
                self.gui.koncPanel.satniGraf.set_statusMap(statusMapa)
                self.gui.koncPanel.minutniGraf.set_statusMap(statusMapa)
                self.gui.visednevniPanel.satniRest.set_statusMap(statusMapa)
            except pomocne_funkcije.AppExcept as err:
                logging.error('App exception', exc_info=True)
                msg = 'Pristup mapi sa statusima nije moguc.\n' + str(err)
                self.prikazi_error_msg(msg)
                self.gui.action_log_in.setEnabled(True)
                self.gui.action_log_out.setEnabled(False)
    ###############################################################################
    def nadji_default_pomocne_za_kanal(self, kanal):
        """
        za zadani kanal, ako je formula kanala unutar nekog od setova,
        vrati sve druge kanale na istoj postaji koji takodjer pripadaju istom
        setu.

        npr. ako je izabrani kanal Desinic NO, funkcija vraca id mjerenja za
        NO2 i NOx sa Desinica (ako postoje)
        """
        setovi = [('NOx','NO','NO2'), ('PM10','PM1','PM2.5')]
        output = set()
        postaja = self.mapaMjerenjeIdToOpis[kanal]['postajaId']
        formula = self.mapaMjerenjeIdToOpis[kanal]['komponentaFormula']
        ciljaniSet = None
        for kombinacija in setovi:
            if formula in kombinacija:
                ciljaniSet = kombinacija
                break
        if ciljaniSet == None:
            return output
        for programMjerenja in self.mapaMjerenjeIdToOpis:
            if self.mapaMjerenjeIdToOpis[programMjerenja]['postajaId'] == postaja and programMjerenja != kanal:
                if self.mapaMjerenjeIdToOpis[programMjerenja]['komponentaFormula'] in ciljaniSet:
                    output.add(programMjerenja)
        return output


    ###############################################################################
    def konstruiraj_tree_model(self):
        """
        Povuci sa REST servisa sve programe mjerenja
        Pokusaj sastaviti model, tree strukturu programa mjerenja
        """
        try:
            # dohvati dictionary programa mjerenja sa rest servisa
            mapa = self.webZahtjev.get_programe_mjerenja()
            # spremi mapu u privatni member
            self.mapaMjerenjeIdToOpis = mapa
            self.gui.konfiguracija.reset_pomocne(self.mapaMjerenjeIdToOpis)
            #dodaj pomocne grafove 'random boje' ovisno da li su u NOX ili PM grupi
            for kanal in self.mapaMjerenjeIdToOpis:
                pomocni = self.nadji_default_pomocne_za_kanal(kanal)
                for i in pomocni:
                    naziv = self.mapaMjerenjeIdToOpis[i]['komponentaFormula']
                    self.gui.konfiguracija.dodaj_random_pomocni(kanal, i, naziv)


            #root objekt
            tree = model_drva.TreeItem(['stanice', None, None, None], parent=None)
            #za svaku individualnu stanicu napravi TreeItem objekt, reference objekta spremi u dict
            stanice = []
            for i in sorted(list(mapa.keys())):
                stanica = mapa[i]['postajaNaziv']
                if stanica not in stanice:
                    stanice.append(stanica)
            stanice = sorted(stanice)
            postaje = [model_drva.TreeItem([name, None, None, None], parent=tree) for name in stanice]
            strPostaje = [str(i) for i in postaje]
            for i in mapa:
                stanica = mapa[i]['postajaNaziv']  #parent = stanice[stanica]
                komponenta = mapa[i]['komponentaNaziv']
                mjernaJedinica = mapa[i]['komponentaMjernaJedinica']
                formula = mapa[i]['komponentaFormula']
                opis = " ".join([formula, '[', mjernaJedinica, ']'])
                usporedno = mapa[i]['usporednoMjerenje']
                #data = [komponenta, mjernaJedinica, i]
                data = [komponenta, usporedno, i, opis]
                redniBrojPostaje = strPostaje.index(stanica)
                model_drva.TreeItem(data, parent=postaje[redniBrojPostaje])  #kreacija TreeItem objekta

            self.modelProgramaMjerenja = model_drva.ModelDrva(tree)  #napravi model
        except pomocne_funkcije.AppExcept:
            # log error sa stack traceom exceptiona
            logging.error('App exception', exc_info=True)
            self.mapaMjerenjeIdToOpis = None
        ###############################################################################

    def reconnect_to_REST(self):
        """
        inicijalizacija objekata vezanih za interakciju sa REST servisom
        -webZahtjev()
        -dataReader()
        -dataWriter()
        """
        # promjeni cursor u wait cursor
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        # inicijalizacija objekata
        self.initialize_web_and_rest_interface(True)
        #konstruiraj tree model programa mjerenja
        self.konstruiraj_tree_model()
        #postavi tree model u ciljani tree view widget na display
        if self.modelProgramaMjerenja is not None:
            self.gui.restIzbornik.treeView.setModel(self.modelProgramaMjerenja)
            self.gui.restIzbornik.model = self.modelProgramaMjerenja
            logging.info('Tree model programa mjerenja uspjesno postavljen')
            self.gui.action_log_in.setEnabled(False)
            self.gui.action_log_out.setEnabled(True)
        else:
            logging.info('Tree model programa mjerenja nije uspjesno postavljen')
            self.gui.action_log_in.setEnabled(True)
            self.gui.action_log_out.setEnabled(False)
            msg = 'Krivi login user ili password.\n Spajanje sa REST servisom nije moguce'
            self.prikazi_error_msg(msg)

        #vrati izgled cursora nazad na normalni
        QtGui.QApplication.restoreOverrideCursor()

    ###############################################################################
    def prikazi_error_msg(self, poruka):
        """
        Prikaz informacijskog dijaloga nakon neke greske
        """
        # vrati izgled cursora nazad na normalni nakon exceptiona
        QtGui.QApplication.restoreOverrideCursor()
        # prikazi information dialog sa pogreskom
        QtGui.QMessageBox.information(self.gui, 'Pogreska prilikom rada', str(poruka))

    ###############################################################################
    def pripremi_membere_prije_ucitavanja_zahtjeva(self, mapa):
        """
        Funkcija analizira zahtjev preuzet u obliku mape
        {'programMjerenjaId':int, 'datumString':'YYYY-MM-DD'}
        i reinicijalizira odredjene membere kontorlora.
        """
        # reset status crtanja
        self.drawStatus = [False, False]
        self.gKanal = int(mapa['programMjerenjaId'])  # informacija o glavnom kanalu
        datum = mapa['datumString']  # datum je string formata YYYY-MM-DD
        self.pickedDate = datum  # postavi izabrani datum
        # pretvaranje datuma u 2 timestampa od 00:01:00 do 00:00:00 iduceg dana
        tsdatum = pd.to_datetime(datum)
        self.zavrsnoVrijeme = tsdatum + datetime.timedelta(days=1)
        self.pocetnoVrijeme = tsdatum + datetime.timedelta(minutes=1) - datetime.timedelta(days=self.brojDanaSatni-1) #offset dana unazad
        #za svaki slucaj, pobrinimo se da su varijable pandas.tslib.Timestamp
        self.zavrsnoVrijeme = pd.to_datetime(self.zavrsnoVrijeme)
        self.pocetnoVrijeme = pd.to_datetime(self.pocetnoVrijeme)
    ###############################################################################
    def ucitaj_podatke_ako_nisu_prije_ucitani(self):
        """
        Metoda usporedjuje argumente zahtjeva sa 'cacheom' vec odradjenih zahtjeva.
        Ako zahtjev nije prije odradjen, ucitava se u dokument.
        """
        self.sviBitniKanali = []  # varijabla sa listom svih programMjerenjaId koje treba ucitati
        self.sviBitniKanali.append(self.gKanal)  # dodaj glavni kanal na popis
        # pronadji sve ostale kanale potrebne za crtanje
        for key in self.gui.konfiguracija.dictPomocnih[self.gKanal]:
            self.sviBitniKanali.append(key)
        #kreni ucitavati po potrebi
        for kanal in self.sviBitniKanali:
            try:
                #citanje pojedinog kanala (ukljucujuci i pomocne)
                self.dokument.citaj(key=kanal, date=self.pickedDate, ndana=self.brojDanaSatni)
                #update kalendarStatus
                self.update_kalendarStatus(kanal, self.pickedDate, 'ucitani')
                #dodaj glavni kanal u setGlavnihKanala
                self.setGlavnihKanala = self.setGlavnihKanala.union([self.gKanal])
                self.modelProgramaMjerenja.set_usedMjerenja(self.kalendarStatus)
            except pomocne_funkcije.AppExcept:
                logging.info('Kanal nije ucitan u dokument, kanal = {0}'.format(str(kanal)), exc_info=True)
        #update boju na kalendaru ovisno o ucitanim podacima
        self.promjena_boje_kalendara()

    ###############################################################################
    def priredi_podatke(self, mapa):
        """
        Funkcija analizira zahtjev preuzet u obliku mape
        {'programMjerenjaId':int, 'datumString':'YYYY-MM-DD'}

        metoda priprema kontolor za crtanje, priprema podatke, updatea labele na
        panelima i pokrece proces crtanja.
        """
        # ovo potencijalno traje... wait cursor
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        # reinicijalizacija membera (self.gKanal, self.pocetnoVrijeme....)
        self.pripremi_membere_prije_ucitavanja_zahtjeva(mapa)
        #ucitavanje podataka ako prije nisu ucitani (ako nisu u cacheu zahtjeva)
        self.ucitaj_podatke_ako_nisu_prije_ucitani()
        #restore wait cursora
        QtGui.QApplication.restoreOverrideCursor()

        argMap = {'opis': self.mapaMjerenjeIdToOpis[self.gKanal],
                  'datum': self.pickedDate,
                  'mjerenjeId': self.gKanal}
        self.gui.koncPanel.change_glavniLabel(argMap)
        self.gui.zsPanel.change_glavniLabel(argMap)
        self.gui.visednevniPanel.change_glavniLabel(argMap)

        self.emit(QtCore.SIGNAL('change_glavniLabel(PyQt_PyObject)'), argMap)
        #pokreni crtanje, ali ovisno o tabu koji je aktivan
        self.promjena_aktivnog_taba(self.aktivniTab)
    ###############################################################################
    def ponisti_izmjene(self):
        """
        Funkcija ponovno ucitava podatke sa REST servisa i poziva na ponovno crtanje
        trenutno aktivnog kanala za trenutno izabrani datum.
        """
        if self.gKanal is not None and self.pickedDate is not None:
            mapa = {'programMjerenjaId': self.gKanal,
                    'datumString': self.pickedDate}
            # pokreni postupak kao da je kombinacija datuma i kanala prvi puta izabrana
            self.priredi_podatke(mapa)
        ###############################################################################

    def crtaj_satni_graf(self):
        """
        Funkcija koja emitira signal sa naredbom za crtanje samo ako je prethodno
        zadan datum, tj. donja i gornja granica intervala i glavni kanal.
        """
        if self.pocetnoVrijeme != None and self.zavrsnoVrijeme != None and self.gKanal != None:
            arg = {'kanalId': self.gKanal,
                   'pocetnoVrijeme': self.pocetnoVrijeme,
                   'zavrsnoVrijeme': self.zavrsnoVrijeme}
            # relevantni agregirani frejmovi za satni graf
            self.agregiraniFrejmovi = self.dokument.dohvati_agregirane_frejmove(
                lista=self.sviBitniKanali,
                tmin=self.pocetnoVrijeme,
                tmax=self.zavrsnoVrijeme)
            # naredba za crtanje satnog grafa
            self.gui.koncPanel.satniGraf.crtaj(self.agregiraniFrejmovi, arg)
            #promjena labela u panelima sa grafovima, opis
            try:
                """
                opis naredbi koje sljede:
                Zanima nas da li je netko vec odabrao satni interval za minutni graf.
                Zanima nas da li je satni interval unutar izabranog datuma.
                Bitno je jer u slucaju promjene datuma minutni graf ce ostati
                prikazivati zadnji satni interval. Da ne bi doslo do zabune (potencijalno
                dva grafa mogu prikazivati razlicite kanale i/ili datume), moramo
                "clearati" graf ili narediti ponovno crtanje minutnog grafa.
                """
                if self.sat is not None:
                    if self.sat >= self.pocetnoVrijeme and self.sat <= self.zavrsnoVrijeme:
                        #nacrtaj minutni graf
                        self.crtaj_minutni_graf(self.sat)
                    else:
                        #clear minutni graf ako se datum pomakne
                        self.gui.koncPanel.minutniGraf.clear_graf()
                        #clear izabrani label sata (prosljedi prazan string)
                        self.gui.koncPanel.change_satLabel('')
            except (TypeError, LookupError) as err:
                logging.error('App exception', exc_info=True)
                self.prikazi_error_msg(err)
            ###############################################################################

    def dohvati_zero_span(self):
        """
        Za ulazni json string, convert i vrati zero i span frejm.
        Moguci exceptioni su:
        ArrtibuteError --> self.webZahtjev mozda nije inicijaliziran i ne postoji
        pomocne_funkcije.AppExcept --> fail prilikom ucitavanja json stringa sa REST
        AssertionError --> los format ulaznog frejma
        ValueError, TypeError --> krivi argumenti za json parser ili los json
        """
        jsonText = self.webZahtjev.get_zero_span(self.gKanal, self.pickedDate, self.brojDana)
        try:
            frejm = pd.read_json(jsonText, orient='records', convert_dates=['vrijeme'])
        except ValueError:
            logging.error('App exception', exc_info=True)
            msg = """
                Error je kod dohvacanja zero/span podataka sa resta.
                Moguce nije valjani json.
                Kanal: {0}
                Datum: {1}
                JSON:{2}""".format(str(self.gKanal), str(self.pickedDate), str(jsonText))
            logging.error(msg)
            #vrati dva prazna datafrejma, nista se nece crtati dalje
            return pd.DataFrame(), pd.DataFrame()

        # test za strukturu frejma
        assert 'vrsta' in frejm.columns
        assert 'vrijeme' in frejm.columns
        assert 'vrijednost' in frejm.columns

        zeroFrejm = frejm[frejm['vrsta'] == "Z"]
        spanFrejm = frejm[frejm['vrsta'] == "S"]
        zeroFrejm = zeroFrejm.set_index(zeroFrejm['vrijeme'])
        spanFrejm = spanFrejm.set_index(spanFrejm['vrijeme'])

        # kontrola za besmislene vrijednosti (tipa -999)
        zeroFrejm = zeroFrejm[zeroFrejm['vrijednost'] > -998.0]
        spanFrejm = spanFrejm[spanFrejm['vrijednost'] > -998.0]

        return zeroFrejm, spanFrejm

    ###############################################################################
    def crtaj_zero_span(self):
        """
        Crtanje zero span podataka.

        -Clear podataka
        -Dohvati podatke sa REST servisa
        -Nacrtaj ako ima podataka
        """
        # clear grafove
        self.gui.zsPanel.zeroGraf.clear_zero_span()
        self.gui.zsPanel.zeroGraf.clear_zero_span()

        # provjeri da li je izabran glavni kanal i datum.
        if self.gKanal is not None and self.pickedDate is not None:
            try:
                #promjeni cursor u wait cursor
                QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                #dohvati frejmove
                self.zeroFrejm, self.spanFrejm = self.dohvati_zero_span()
                #nastavi dalje samo ako oba frejma nisu prazna
                if len(self.zeroFrejm) > 0 or len(self.spanFrejm) > 0:
                    #fix duplicate rows (if any)
                    self.zeroFrejm.drop_duplicates(subset='vrijeme',
                                                   take_last=True,
                                                   inplace=True)
                    self.zeroFrejm.sort()
                    self.spanFrejm.drop_duplicates(subset='vrijeme',
                                                   take_last=True,
                                                   inplace=True)
                    self.spanFrejm.sort()
                    #redefinicija argumenata
                    tmax = datetime.datetime.strptime(self.pickedDate, '%Y-%m-%d')
                    tmin = tmax - datetime.timedelta(days=self.brojDana)
                    arg = {'kanalId': self.gKanal,
                           'pocetnoVrijeme': tmin,
                           'zavrsnoVrijeme': tmax}
                    #naredi crtanje
                    self.gui.zsPanel.zeroGraf.crtaj(self.zeroFrejm, arg)
                    self.gui.zsPanel.spanGraf.crtaj(self.spanFrejm, arg)
            except pomocne_funkcije.AppExcept as err1:
                #sluzi da hvata lose requestove
                logging.error('Problem kod ucitavanje zero/span sa REST servisa.', exc_info=True)
                opis = 'Problem kod ucitavanja Zero/Span podataka sa REST servisa.' + str(err1)
                self.prikazi_error_msg(opis)
            except AttributeError:
                #moguci fail ako se funkcija pozove prije inicijalizacije REST interfacea.
                logging.error('web interface nije incijaliziran, Potrebno se ulogirati.', exc_info=True)
            except (TypeError, ValueError, AssertionError):
                #mofuci fail za lose formatirani json string
                logging.error('greska kod parsanja json stringa za zero i span.', exc_info=True)
            finally:
                QtGui.QApplication.restoreOverrideCursor()
            ###############################################################################

    def crtaj_minutni_graf(self, izabrani_sat):
        """
        Funkcija crta minutni graf za izabrani sat.
        Ova funkcija se brine za pravilni odgovor na ljevi klik tocke na satno
        agregiranom grafu. Za zadani sat, odredjuje rubove intervala te
        poziva crtanje minutnog grafa.
        """
        self.sat = izabrani_sat
        if self.zavrsnoVrijeme >= self.sat >= self.pocetnoVrijeme:
            highLim = self.sat
            lowLim = highLim - datetime.timedelta(minutes=59)
            lowLim = pd.to_datetime(lowLim)
            # update labela izabranog sata
            self.gui.koncPanel.change_satLabel(self.sat)
            arg = {'kanalId': self.gKanal,
                   'pocetnoVrijeme': lowLim,
                   'zavrsnoVrijeme': highLim}
            # naredba za dohvacanje podataka
            self.frejmovi = self.dokument.dohvati_minutne_frejmove(
                lista=self.sviBitniKanali,
                tmin=lowLim,
                tmax=highLim)
            #naredba za crtanje
            self.gui.koncPanel.minutniGraf.crtaj(self.frejmovi, arg)
        ###############################################################################

    def dodaj_novu_referentnu_vrijednost(self):
        """
        Poziv dijaloga za dodavanje nove referentne vrijednosti za zero ili
        span. Upload na REST servis.
        """
        if self.mapaMjerenjeIdToOpis is not None and self.gKanal is not None:
            # dict sa opisnim parametrima za kanal
            postaja = self.mapaMjerenjeIdToOpis[self.gKanal]['postajaNaziv']
            komponenta = self.mapaMjerenjeIdToOpis[self.gKanal]['komponentaNaziv']
            formula = self.mapaMjerenjeIdToOpis[self.gKanal]['komponentaFormula']
            opis = '{0}, {1}( {2} )'.format(postaja, komponenta, formula)

            dijalog = dodaj_ref_zs.DijalogDodajRefZS(parent=None, opisKanal=opis, idKanal=self.gKanal)
            if dijalog.exec_():
                podaci = dijalog.vrati_postavke()
                try:
                    # test da li je sve u redu?
                    assert isinstance(podaci['vrijednost'],
                                      float), 'Neuspjeh. Podaci nisu spremljeni na REST servis.\nReferentna vrijednost je krivo zadana.'
                    #napravi json string za upload (dozvoljeno odstupanje je placeholder)
                    #int od vremena... output je double zboj milisekundi
                    jS = {"vrijeme": int(podaci['vrijeme']),
                          "vrijednost": podaci['vrijednost'],
                          "vrsta": podaci['vrsta'],
                          "maxDozvoljeno": 0.0,
                          "minDozvoljeno": 0.0}

                    #dict to json dump
                    jS = json.dumps(jS)
                    #potvrda za unos!
                    odgovor = QtGui.QMessageBox.question(self.gui,
                                                         "Potvrdi upload na REST servis",
                                                         "Potvrdite spremanje podataka na REST servis",
                                                         QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)

                    if odgovor == QtGui.QMessageBox.Yes:
                        #put json na rest!
                        self.webZahtjev.upload_ref_vrijednost_zs(jS, self.gKanal)
                        #confirmation da je uspjelo
                        QtGui.QMessageBox.information(self.gui, "Potvrda unosa na REST",
                                                      "Podaci sa novom referentnom vrijednosti uspjesno su spremljeni na REST servis")
                        logging.info('Uspjesno dodana nova referentna vrijednost zero/span. json = {0}'.format(jS))
                except AssertionError as err:
                    logging.error('Pogreska kod zadavanja referentne vrijednosti za zero ili span (nije float)',
                                  exc_info=True)
                    self.prikazi_error_msg(str(err))
                except pomocne_funkcije.AppExcept as err2:
                    logging.error('Pogreska kod uploada referentne vrijednosti zero/span na servis.', exc_info=True)
                    self.prikazi_error_msg(str(err2))
        else:
            logging.info('pokusaj dodavanje ref vrijednosti bez ucitanih kanala mjerenja ili bez izabranog kanala')
            self.prikazi_error_msg('Neuspjeh. Programi mjerenja nisu ucitani ili kanal nije izabran')
        ###############################################################################
    def upload_minutne_na_REST(self):
        """
        Za trenutno aktivni kanal i datum, spremi slajs minutnog frejma na
        REST servis.
        Pitaj za potvrdu odluke sa spremanje podataka, prije nego krene upload.
        """
        if self.gKanal is not None and self.pickedDate is not None:
            # prompt izbora za spremanje filea, question
            msg = " ".join(['Spremi minutne podatke od',
                            str(self.gKanal),
                            ':',
                            self.pickedDate,
                            'na REST web servis?'])
            odgovor = QtGui.QMessageBox.question(self.gui,
                                                 "Potvrdi upload na REST servis",
                                                 msg,
                                                 QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if odgovor == QtGui.QMessageBox.Yes:
                try:
                    # promjeni cursor u wait cursor
                    QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                    #reci dokumentu da spremi minutne podatke na rest
                    datumi = self.napravi_listu_dana(self.pickedDate, self.brojDanaSatni)
                    #convert from qdate to string representation
                    datumi = [i.toString('yyyy-MM-dd') for i in datumi]
                    for datum in datumi:
                        self.dokument.persist_minutne_podatke(key=self.gKanal, date=datum)
                    #update status kalendara
                    self.update_kalendarStatus(self.gKanal, self.pickedDate, 'spremljeni')
                    self.promjena_boje_kalendara()
                    #report success
                    msg = " ".join(['Minutni podaci za',
                                    str(self.gKanal),
                                    'su spremljeni na REST servis.'])
                    self.prikazi_error_msg(msg)
                except (Exception, pomocne_funkcije.AppExcept):
                    logging.error('Error prilikom uploada na rest servis', exc_info=True)
                    msg = 'Podaci nisu spremljeni na REST servis. Doslo je do pogreske prilikom rada.'
                    # report fail
                    self.prikazi_error_msg(msg)
                finally:
                    # vrati izgled cursora nazad na normalni
                    QtGui.QApplication.restoreOverrideCursor()
                    #ponovno ucitaj podatake sa RESTA za isti datum i glavni kanal kao i one koje si spremio
                    self.ponisti_izmjene()
        else:
            msg = 'Nije moguce spremiti minutne podatke na REST jer nije izabran glavni kanal i datum.'
            self.prikazi_error_msg(msg)
        ###############################################################################

    def update_kalendarStatus(self, progMjer, datum, tip):
        """
        dodavanje datuma na popis ucitanih i ili validiranih ovisno o tipu
        i programu mjerenja.

        progMjer --> program mjerenja id, integer
        datum --> string reprezentacija datuma  'yyyy-MM-dd' formata
        tip --> 'ucitani' ili 'spremljeni'
        """
        #datum = QtCore.QDate.fromString(datum, 'yyyy-MM-dd')
        danas = datetime.datetime.now().strftime('%Y-%m-%d')
        datumi = self.napravi_listu_dana(datum, self.brojDanaSatni)
        for datum in datumi:
            if datum != danas:
                if progMjer in self.kalendarStatus:
                    if tip == 'spremljeni':
                        if datum not in self.kalendarStatus[progMjer]['ok']:
                            self.kalendarStatus[progMjer]['ok'].append(datum)
                    else:
                        if datum not in self.kalendarStatus[progMjer]['bad']:
                            self.kalendarStatus[progMjer]['bad'].append(datum)
                        if self.dokument.provjeri_validiranost_dana(self.gKanal, datum):
                            self.kalendarStatus[progMjer]['ok'].append(datum)
                else:
                    self.kalendarStatus[progMjer] = {'ok': [], 'bad': [datum]}
        ###############################################################################

    def promjena_boje_kalendara(self):
        """
        Funkcija mjenja boju kalendara ovisno o podacima za glavni kanal.
        self.kalendarStatus je mapa koja za svaki kanal prati koji su datumi
        ucitani, a koji su spremljeni na REST servis.

        P.S. izdvojeno van kao funkcija samo radi citljivosti.
        """
        if self.gKanal in self.kalendarStatus:
            self.gui.restIzbornik.calendarWidget.refresh_dates(self.kalendarStatus[self.gKanal])
        ###############################################################################

    def promjeni_datum(self, x):
        """
        Odgovor na zahtjev za pomicanjem datuma za 1 dan (gumbi sljedeci/prethodni)
        Emitiraj signal da izbornik promjeni datum ovisno o x. Ako je x == 1
        prebaci 1 dan naprijed, ako je x == -1 prebaci jedan dan nazad
        """
        if x == 1:
            self.gui.restIzbornik.sljedeci_dan()
        else:
            self.gui.restIzbornik.prethodni_dan()
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
        if x is 0 and not self.drawStatus[0]:
            self.crtaj_satni_graf()
            self.drawStatus[0] = True
        elif x is 1 and not self.drawStatus[1]:
            self.crtaj_zero_span()
            self.drawStatus[1] = True
        ###############################################################################

    def apply_promjena_izgleda_grafova(self):
        """
        funkcija se pokrece nakon izlaska iz dijaloga za promjenu grafova.
        Naredba da se ponovno nacrtaju svi grafovi.
        """
        self.drawStatus = [False, False] # promjena izgleda grafa, tretiraj kao da nisu nacrtani
        if self.gKanal != None:
            mapa = {'programMjerenjaId':self.gKanal, 'datumString':self.pickedDate}
            self.priredi_podatke(mapa)
    ###############################################################################
    def promjeni_flag(self, ulaz):
        """
        Odgovor kontrolora na zahtjev za promjenom flaga. Kontrolor naredjuje
        dokumentu da napravi odgovarajucu izmjenu.

        Ulazni parametar je mapa:
        ulaz['od'] -->pocetno vrijeme, pandas timestamp
        ulaz['do'] -->zavrsno vrijeme, pandas timestamp
        ulaz['noviFlag'] -->novi flag
        ulaz['kanal'] -->kanal koji se mijenja

        P.S. dokument ima vlastiti signal da javi kada je doslo do promjene

        QtCore.SIGNAL('model_flag_changed')
        """
        self.dokument.change_flag(key=ulaz['kanal'], tmin=ulaz['od'], tmax=ulaz['do'], flag=ulaz['noviFlag'])

    ###############################################################################
    def sync_zero_span_x_os(self, frejm1, frejm2):
        """
        Metoda sluzi za definiciju raspona x osi za zero i span graf
        ulaz su 2 datafrejma
        izlaz je vremenski raspon x osi
        """
        min1 = min(frejm1.index)
        min2 = min(frejm2.index)
        max1 = max(frejm1.index)
        max2 = max(frejm2.index)

        return [min(min1, min2), max(max1, max2)]
    ###############################################################################
    def nacrtaj_rest_satne(self, mapa):
        """
        Metoda je zaduzena da preuzme podatke sa REST servisa, pripremi ih
        za crtanje i pokrene crtanje direktnom naredbom zaduzenom kanvasu

        ulazna mapa ima sljedeca polja
        ['datumOd','datumDo', 'kanal', 'valjani','validacija']

        P.S. ista mapa se mora prosljediti webZahtjevu da povuce podatke sa RESTA
        """
        try:
            jsonText = self.webZahtjev.get_satne_podatke(mapa)
            df = pd.read_json(jsonText, orient='records', convert_dates=['vrijeme'])
            frames, metaData = self.adapt_rest_satni_frejm(df)
            #TODO! naredba za crtanje....
            self.gui.visednevniPanel.satniRest.crtaj(frames, metaData)
        except ValueError:
            logging.error('App exception', exc_info=True)
            msg = """
                Error je kod dohvacanja satnih podataka sa resta.
                Moguce nije valjani json.
                Kanal: {0}
                Datum: {1}
                JSON:{2}""".format(str(self.gKanal), str(self.pickedDate), str(jsonText))
            logging.error(msg)
            #vrati dva prazna datafrejma, nista se nece crtati dalje
            return pd.DataFrame(), pd.DataFrame()
        except pomocne_funkcije.AppExcept as err:
            # log error sa stack traceom exceptiona
            logging.error('App exception', exc_info=True)
            self.prikazi_error_msg(err)
    ###############################################################################
    def adapt_rest_satni_frejm(self, frejm):
        """
        metoda prilagodjava ulazni dataframe i sve potrebno za crtanje.
        frejm i mapu sa meta_podacima
        """
        frejm = frejm.set_index(frejm['vrijeme'])
        pocetno = frejm.index.min()
        zavrsno = frejm.index.max()
        kanal = frejm.loc[pocetno, 'programMjerenjaId']
        frejm.rename(columns={'valjan':'flag','vrijednost':'avg'}, inplace = True)
        frejm['flag'] = frejm['flag'].map(self.adapt_valjan)

        frejmovi = {kanal:frejm}
        metaMap = {'kanalId': kanal,
                   'pocetnoVrijeme': pocetno,
                   'zavrsnoVrijeme': zavrsno}

        return frejmovi, metaMap

    def adapt_valjan(self, x):
        """hellper converter iz booleana u flag"""
        if x:
            return 1
        else:
            return -1
        ###############################################################################
        ###############################################################################