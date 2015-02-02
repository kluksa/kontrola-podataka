# -*- coding: utf-8 -*-
"""
Created on Thu Jan 22 09:52:37 2015

@author: User
"""

from PyQt4 import QtCore, QtGui
import datetime #python datetime objekt, potreban za timedelta isl.
import pickle #serializer podataka, koristim za spremanje/ucitavanje postavki
import pandas as pd #pandas modul, za provjeru tipa nekih argumenata
import copy #modul za deep copy nested struktura (primarno za kopije self.graf_defaults)
import configparser #parser za configuration file (built in)
import os #pristup direktorijima, provjere postojanja filea....

import pomocneFunkcije #pomocne funkcije i klase (npr. AppExcept exception...)
import networking_funkcije #web zahtjev, interface prema REST servisu
import dokument_model #interni model za zapisivanje podataka u dict pandas datafrejmova
import datareader #REST reader/writer
import agregator #agregator
import modeldrva #pomocne klase za definiranje tree modela programa mjerenja
import dijalog1 #modul sa dijalozima za promjenu i dodavanje grafova
###############################################################################
###############################################################################
class Kontroler(QtCore.QObject):
    """
    Kontrolni dio aplikacije.
    Tu se nalazi glavna logika programa i povezivanje dijela akcija iz gui
    djela sa modelom.
    
    Opis toka akcija:
    1.report exceptiona:
        -Svaki uhvaceni Exception treba emitirati signal. Kontroler osluskuje
        za signale sa "potpisom" QtCore.SIGNAL('error_message(PyQt_PyObject)')
        -Kontroler zatim prikazuje informacijski dijalog
        
    """
    def __init__(self, parent = None, gui = None):
        QtCore.QObject.__init__(self, parent)
        """inicijalizacija dokumenta"""
        self.dokument = dokument_model.DataModel()

        """incijalizacija agregatora podataka"""
        self.satniAgreg = agregator.Agregator()
        
        #TODO! try block ? possible read/parse fail
        #base exception for configparser: configparser.Error
        config = configparser.ConfigParser()
        config.read("config.ini")
        
        REST_info = dict(config['REST_info'])
        
        """url settings za REST web zahtjev"""
        #defaults        
        self.baza = "http://172.20.1.166:9090/SKZ-war/webresources/"
        self.resursi = {"siroviPodaci":"dhz.skz.rs.sirovipodaci", 
                        "programMjerenja":"dhz.skz.aqdb.entity.programmjerenja",
                        "zerospan":"dhz.skz.rs.zerospan"}

        #TODO! sredi "ljepsi nacin" ucitavanja config filea / neki dijalog za promjenu vrijednosti
        self.baza = REST_info["base_url"]
        self.resursi["siroviPodaci"] = REST_info["sirovipodaci"]
        self.resursi["programMjerenja"] = REST_info["programmjerenja"]
        self.resursi["zerospan"] = REST_info["zerospan"]


        """ostali memberi"""
        self.pickedDate = None #zadnje izabrani dan
        self.gKanal = None #trenutno aktivni glavni kanal
        self.tmin = None #donji rub vremenskog slajsa dana (datum-00:01:00)
        self.tmax = None #gornji rub vremenskog slajsa dana (datum+1 dan-00:00:00)
        self.sat = None #zadnje izabrani sat na satnom grafu (timestamp)
        self.modelProgramaMjerenja = None #tree model programa mjerenja
        self.mapa_mjerenjeId_to_opis = None #mapa, program mjerenja:dict parametara
        self.reloadAttempt = 0 #member koji prati broj pokusaja sklapanja tree modela programa mjerenja
        
        """inicijalizacija web sucelja (REST reader, REST writer, webZahtjev)"""
        self.initialize_web_and_rest_interface(self.baza, self.resursi)

        """ocekuje se da se prosljedi instanca valjanog GUI elementa"""
        self.gui = gui
        
        """defaultne vrijednosti za crtanje grafova (kanal je program mjerenja)"""
        self.graf_defaults = {
                'glavniKanal':{
                    'midline':{'kanal':None, 'line':'-', 'linewidth':1.0, 'rgb':(0,0,0), 'alpha':1.0, 'zorder':100, 'label':'average'},
                    'validanOK':{'kanal':None, 'marker':'d', 'rgb':(0,255,0), 'alpha':1.0, 'zorder':100, 'label':'validiran, dobar', 'markersize':12}, 
                    'validanNOK':{'kanal':None, 'marker':'d', 'rgb':(255,0,0), 'alpha':1.0, 'zorder':100, 'label':'validiran, los', 'markersize':12}, 
                    'nevalidanOK':{'kanal':None, 'marker':'o', 'rgb':(0,255,0), 'alpha':1.0, 'zorder':100, 'label':'nije validiran, dobar', 'markersize':12}, 
                    'nevalidanNOK':{'kanal':None, 'marker':'o', 'rgb':(255,0,0), 'alpha':1.0, 'zorder':100, 'label':'nije validiran, los', 'markersize':12},
                    'fillsatni':{'kanal':None, 'crtaj':True, 'data1':'q05', 'data2':'q95', 'rgb':(0,0,255), 'alpha':0.5, 'zorder':1}, 
                    'ekstremimin':{'kanal':None, 'crtaj':True, 'marker':'+', 'rgb':(90,50,10), 'alpha':1.0, 'zorder':100, 'label':'min', 'markersize':12}, 
                    'ekstremimax':{'kanal':None, 'crtaj':True, 'marker':'+', 'rgb':(90,50,10), 'alpha':1.0, 'zorder':100, 'label':'max', 'markersize':12}
                                },
                'pomocniKanali':{}, 
                'ostalo':{
                    'opcijeminutni':{'cursor':False, 'span':True, 'ticks':True, 'grid':False, 'legend':False}, 
                    'opcijesatni':{'cursor':False, 'span':False, 'ticks':True, 'grid':False, 'legend':False}
                        }
                            }
        
        """povezivanje signala i funkcija (definicija toka)"""
        self.poveznice()
        
        """
        Dovrsavanje inicijalizacije aplikacije
        Pokusaj sljedece redom:
        1. update_gui_action_state
            - provjeri zadani graf_defaults
            - sastavi mapu opcija (cursor, span...)
            - prosljedi informaciju glavnom elementu GUI-a da tocno postavi
              stanje checkable akcija
        2. update_gui_tree_view
            - Spoji se na REST servis i probaj dohvatiti sve programe mjerenja
            - napravi "tree model" svih programa mjerenja
            - prosljedi "pointer" na model REST izborniku (koontorlni dio gui-a).
              tj. dovrsi inicijalizaciju rest izbornika
        """
        #1
        self.update_gui_action_state()
        #2
        self.reloadAttempt += 1
        self.konstruiraj_tree_model()
        if self.modelProgramaMjerenja != None:
            #postavi model u ciljani tree view gui-a
            self.gui.restIzbornik.treeView.setModel(self.modelProgramaMjerenja)
            #postavi model u member restIzbornika
            self.gui.restIzbornik.model = self.modelProgramaMjerenja
        
        """load default preset - pozicija widgeta"""
        self.load_preset_mehanika(config['PRESET']['file_loc'])
###############################################################################
    def initialize_web_and_rest_interface(self, baza, resursi):
        """
        Inicijalizacija web zahtjeva i REST reader/writer objekata koji ovise o
        njemu.
        """
        #inicijalizacija webZahtjeva
        self.webZahtjev = networking_funkcije.WebZahtjev(self.baza, self.resursi)
        #inicijalizacija REST readera
        self.restReader = datareader.RESTReader(model = self.dokument, source = self.webZahtjev)
        #inicijalizacija REST writera agregiranih podataka
        self.restWriter = datareader.RESTWriterAgregiranih(source = self.webZahtjev)
###############################################################################
    def update_gui_action_state(self):
        """
        Prepakiraj defaultne postavke ('ostalo') satnog i minutnog grafa
        u mapu i pozovi set_action_state metodu gui-a
        """
        mapa = {}
        mapa['satnigrid'] = self.graf_defaults['ostalo']['opcijesatni']['grid']
        mapa['satnicursor'] = self.graf_defaults['ostalo']['opcijesatni']['cursor']
        mapa['satnispan'] = self.graf_defaults['ostalo']['opcijesatni']['span']
        mapa['satniticks'] = self.graf_defaults['ostalo']['opcijesatni']['ticks']
        mapa['satnilegend'] = self.graf_defaults['ostalo']['opcijesatni']['legend']
        mapa['minutnigrid'] = self.graf_defaults['ostalo']['opcijeminutni']['grid']
        mapa['minutnicursor'] = self.graf_defaults['ostalo']['opcijeminutni']['cursor']
        mapa['minutnispan'] = self.graf_defaults['ostalo']['opcijeminutni']['span']
        mapa['minutniticks'] = self.graf_defaults['ostalo']['opcijeminutni']['ticks']
        mapa['minutnilegend'] = self.graf_defaults['ostalo']['opcijeminutni']['legend']
        #naredi gui-u update stanja checkable akcija
        self.gui.set_action_state(mapa)       
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
            self.mapa_mjerenjeId_to_opis = mapa
            #root objekt
            tree = modeldrva.TreeItem(['stanice', None, None], parent = None)
            #za svaku individualnu stanicu napravi TreeItem objekt, reference objekta spremi u dict
            stanice = {}
            for i in sorted(list(mapa.keys())):
                stanica = mapa[i]['postajaNaziv']
                if stanica not in stanice:
                    stanice[stanica] = modeldrva.TreeItem([stanica, None, None], parent = tree)
            #za svako individualnu komponentu napravi TreeItem sa odgovarajucim parentom (stanica)
            for i in mapa.keys():
                stanica = mapa[i]['postajaNaziv'] #parent = stanice[stanica]
                komponenta = mapa[i]['komponentaNaziv']
                #mjernaJedinica = mapa[i]['komponentaMjernaJedinica']
                usporedno = mapa[i]['usporednoMjerenje']
                #data = [komponenta, mjernaJedinica, i]
                data = [komponenta, usporedno, i]
                modeldrva.TreeItem(data, parent = stanice[stanica]) #kreacija TreeItem objekta
            
            self.modelProgramaMjerenja = modeldrva.ModelDrva(tree) #napravi model
            
        except pomocneFunkcije.AppExcept as err:
            if self.reloadAttempt > 1:
                self.prikazi_error_msg(err)
            else:
                print('Error:\nTree model programa mjerenja nije inicijaliziran')
###############################################################################
    def reconnect_to_REST(self):
        """
        Ponovno spajanje na REST servis (refresh)
        
        -Formiranje novog web zahtjeva, REST readera i Rest writera
        (dokument ostaje isti)
        -update stanja checkable akcija prema defaultima
        -update tree modela programa mjerenja
        """
        #promjeni cursor u wait cursor
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

        self.initialize_web_and_rest_interface(self.baza, self.resursi)
        self.update_gui_action_state()
        self.reloadAttempt += 1
        self.konstruiraj_tree_model()
        if self.modelProgramaMjerenja != None:
            #postavi model u ciljani tree view gui-a
            self.gui.restIzbornik.treeView.setModel(self.modelProgramaMjerenja)
        
        #vrati izgled cursora nazad na normalni
        QtGui.QApplication.restoreOverrideCursor()
###############################################################################
    def poveznice(self):
        """
        Povezivanje emitiranih signala iz raznih dijelova aplikacije sa
        funkcijama koje definiraju tok programa.
        """
        ###prihvat Exception vezanih signala###
        self.connect(self.restReader, 
                     QtCore.SIGNAL('error_message(PyQt_PyObject)'), 
                     self.prikazi_error_msg)

        self.connect(self.restWriter, 
                     QtCore.SIGNAL('error_message(PyQt_PyObject)'), 
                     self.prikazi_error_msg)

        self.connect(self.webZahtjev, 
                     QtCore.SIGNAL('error_message(PyQt_PyObject)'), 
                     self.prikazi_error_msg)
        
        ###gui zahtjev za reinicijalizacijom membera vezanih za REST servis###
        #npr. nakon sto dobijemo povratnu informaciju o 404 http erroru
        self.connect(self.gui, 
                     QtCore.SIGNAL('gui_reinitialize_REST'), 
                     self.reconnect_to_REST)
                     
        ###gui zahtjev, izabrani datum i program mjerenja sa izbornika, priprema crtanja grafova###
        self.connect(self.gui.restIzbornik, 
                     QtCore.SIGNAL('gui_izbornik_citaj(PyQt_PyObject)'), 
                     self.priredi_podatke)
                     
        ###gui zahtjev, pokreni zero/span crtanje i dohvacanje podataka###
        self.connect(self.gui.restIzbornik, 
                     QtCore.SIGNAL('gui_izbornik_citaj(PyQt_PyObject)'), 
                     self.nacrtaj_zero_span)

        ###zaprimanje zahtjeva od panela za prebacivanjem dana naprijed ili nazad###
        self.connect(self.gui.panel, 
                     QtCore.SIGNAL('prebaci_dan(PyQt_PyObject)'), 
                     self.promjeni_datum)
        
        ###slanje zahtjeva za prebacivanje dan naprijed rest izborniku###
        self.connect(self, 
                     QtCore.SIGNAL('dan_naprjed'), 
                     self.gui.restIzbornik.sljedeci_dan)
        
        ###slanje zahtjeva za prebacivanje dan unazad rest izborniku###
        self.connect(self, 
                     QtCore.SIGNAL('dan_nazad'), 
                     self.gui.restIzbornik.prethodni_dan)

        ###izbornik, promjena opcija grafova i dodavanje pomocnih grafova###
        self.connect(self.gui.restIzbornik, 
                     QtCore.SIGNAL('promjeni_postavke_grafova'), 
                     self.prikazi_glavni_graf_dijalog)
        
        ###naredba za crtanje satnog grafa###
        self.connect(self, 
                     QtCore.SIGNAL('nacrtaj_satni_graf(PyQt_PyObject)'), 
                     self.gui.panel.satniGraf.crtaj)
                
        ###update labela u panelu za grafove###
        self.connect(self, 
                     QtCore.SIGNAL('update_graf_label(PyQt_PyObject)'), 
                     self.gui.panel.change_label)

        ###naredba za crtanje minutnog grafa###
        self.connect(self, 
                     QtCore.SIGNAL('nacrtaj_minutni_graf(PyQt_PyObject)'), 
                     self.gui.panel.minutniGraf.crtaj)
        
        ###clear minutnog grafa###
        self.connect(self, 
                     QtCore.SIGNAL('clear_minutni_graf'), 
                     self.gui.panel.minutniGraf.clear_minutni)

        ###promjena flaga###
        #naredba sa satnog grafa
        self.connect(self.gui.panel.satniGraf,
                     QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), 
                     self.promjeni_flag)
                     
        #naredba sa minutnog grafa
        self.connect(self.gui.panel.minutniGraf,
                     QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), 
                     self.promjeni_flag)
                     
        #signal dokumenta da je doslo do promjene u flagu - naredi ponovno crtanje
        self.connect(self.dokument, 
                     QtCore.SIGNAL('model_flag_changed'), 
                     self.naredi_crtanje_satnog)
                     
        
        ###spajanje zahtjeva za frejmovima od canvasa, te odgovor kontolora na zahtjev###
        ###SATNI###
        self.connect(self.gui.panel.satniGraf,
                     QtCore.SIGNAL('dohvati_agregirani_frejm_kanal(PyQt_PyObject)'), 
                     self.vrati_agregirani_frejm)
                     
        self.connect(self, 
                     QtCore.SIGNAL('emitiraj_agregirani(PyQt_PyObject)'), 
                     self.gui.panel.satniGraf.set_agregirani_kanal)
                     
        self.connect(self.gui.panel.satniGraf, 
                     QtCore.SIGNAL('gui_crtaj_minutni_graf(PyQt_PyObject)'), 
                     self.naredi_crtanje_minutnog)
                     
        ###MINUTNI###
        self.connect(self.gui.panel.minutniGraf,
                     QtCore.SIGNAL('dohvati_minutni_frejm_kanal(PyQt_PyObject)'), 
                     self.vrati_minutni_frejm)
                     
        self.connect(self, 
                     QtCore.SIGNAL('emitiraj_minutni_slajs(PyQt_PyObject)'), 
                     self.gui.panel.minutniGraf.set_minutni_kanal)

        ####povezivanje raznih kontrola sa displaya vezano za izgled grafova####
        #satni, grid
        self.connect(self.gui, 
                     QtCore.SIGNAL('update_satni_grid(PyQt_PyObject)'), 
                     self.update_satni_grid)

        #satni, cursor
        self.connect(self.gui, 
                     QtCore.SIGNAL('update_satni_cursor(PyQt_PyObject)'), 
                     self.update_satni_cursor)

        #satni, span
        self.connect(self.gui, 
                     QtCore.SIGNAL('update_satni_span(PyQt_PyObject)'), 
                     self.update_satni_span)

        #satni, minor ticks
        self.connect(self.gui, 
                     QtCore.SIGNAL('update_satni_ticks(PyQt_PyObject)'), 
                     self.update_satni_ticks)
                     
        #satni, legenda
        self.connect(self.gui, 
                     QtCore.SIGNAL('update_satni_legenda(PyQt_PyObject)'), 
                     self.update_satni_legenda)
        
        #minutni, grid
        self.connect(self.gui, 
                     QtCore.SIGNAL('update_minutni_grid(PyQt_PyObject)'), 
                     self.update_minutni_grid)

        #minutni, cursor
        self.connect(self.gui, 
                     QtCore.SIGNAL('update_minutni_cursor(PyQt_PyObject)'), 
                     self.update_minutni_cursor)

        #minutni, span
        self.connect(self.gui, 
                     QtCore.SIGNAL('update_minutni_span(PyQt_PyObject)'), 
                     self.update_minutni_span)

        #minutni, minor ticks
        self.connect(self.gui, 
                     QtCore.SIGNAL('update_minutni_ticks(PyQt_PyObject)'), 
                     self.update_minutni_ticks)

        #minutni, legenda
        self.connect(self.gui, 
                     QtCore.SIGNAL('update_minutni_legenda(PyQt_PyObject)'), 
                     self.update_minutni_legenda)
        
        ###crtanje minutnog grafa, ###
        self.connect(self, 
                     QtCore.SIGNAL('promjena_flaga_minutni(PyQt_PyObject)'), 
                     self.gui.panel.minutniGraf.crtaj)

        ###save preset###
        self.connect(self.gui, 
                     QtCore.SIGNAL('request_save_preset'),
                     self.save_preset)
                     
        ###load preset###
        self.connect(self.gui, 
                     QtCore.SIGNAL('request_load_preset'),
                     self.load_preset)

        ###set/update novog glavnog kanala u rest izbornik (prilikoom load preseta)###
        self.connect(self, 
                     QtCore.SIGNAL('set_glavni_kanal_izbornik(PyQt_PyObject)'), 
                     self.gui.restIzbornik.postavi_novi_glavni_kanal)
                     
        ###crtaj zero naredba zeroCanvas###
        self.connect(self, 
                     QtCore.SIGNAL('crtaj_zero(PyQt_PyObject)'), 
                     self.gui.zspanel.zeroGraf.crtaj)
                     
        ###crtaj span naredba spanCanvas###
        self.connect(self, 
                     QtCore.SIGNAL('crtaj_span(PyQt_PyObject)'), 
                     self.gui.zspanel.spanGraf.crtaj)
        


###############################################################################
    def prikazi_error_msg(self, poruka):
        """
        Prikaz informacijskog dijaloga nakon neke greske
        """
        #vrati izgled cursora nazad na normalni nakon exceptiona
        QtGui.QApplication.restoreOverrideCursor()
        #prikazi information dialog sa pogreskom
        QtGui.QMessageBox.information(self.gui, 'Pogreska prilikom rada', str(poruka))
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
    def agregirani_count_to_postotak(self, x):
        """
        Pomocna funkcija za racunanje obuhvata agregiranih podataka
        """
        return int(x*100/60)
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
    def priredi_podatke(self, lista):
        """
        Funkcija analizira zahtjev preuzet u obliku liste [programMjerenjaId, datum]
        te radi 4 bitne stvari:
        
        1. provjerava da li je zahtjev pomaknuo "fokus" sa prikazanih podataka
           i po potrebi pita sa save/upload podataka na REST prije nego sto se
           zamjene
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
        4. Pokrece proces crtanja satnog grafa (agregiranog)
        """
        print('priredi podatke {0}'.format(lista))

        #1. Promjena glavnog kanala i/ili datuma. Pitaj za save podataka?
        if (self.gKanal != lista[0] or self.pickedDate != lista[1]):
            #provjeri da li su memberi None prije prompta sa upload na REST
            if self.gKanal != None and self.pickedDate != None:
                #pozovi na spremanje
                self.upload_agregirane_to_REST()
                
        #3. postavi nove vrijednosti preuzete iz zahtjeva kao membere
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
        
        #2. ucitavanje svih kanala od interesa za crtanje u dokument
        sviBitniKanali = []
        sviBitniKanali.append(self.gKanal)
        #postavi novi glavni kanal svugdje gdje je to bitno u graf_defaults
        for graf in self.graf_defaults['glavniKanal']:
            self.graf_defaults['glavniKanal'][graf]['kanal'] = self.gKanal
        #pronadji sve ostale kanale potrebne za crtanje
        for graf in self.graf_defaults['pomocniKanali']:
            sviBitniKanali.append(self.graf_defaults['pomocniKanali'][graf]['kanal'])
        #lista svih koji se nisu uspjeli ucitati
        notUcitani = []
        #pokusaj ucitati sve bitne kanale (glavni + pomocni kanali definirani u self.graf_defaults)
        for kanal in sviBitniKanali:
            try:
                self.restReader.read(key = kanal, date = datum)
            except pomocneFunkcije.AppExcept as e1:
                #dodaj listu [kanal, datum] u listu notUcitani
                notUcitani.append([kanal, datum, e1])
        if len(notUcitani) > 0:
            #neki se nisu ucitali u dokument, informiraj koirsnika
            msg = 'Sljedeci kanali nisu ucitani:\n'
            for i in notUcitani:
                msg = msg + str(notUcitani[i][0])+','
            #prokazi informacijski dijalog
            self.prikazi_error_msg(msg)
        
        #4.emit signala sa naredbom za crtanje grafova
        self.naredi_crtanje_satnog()
###############################################################################
    def upload_agregirane_to_REST(self):
        """
        funkcija uzima slice glavnog kanala, agregira ga, i uploada na rest servis.
        Prompt za potvrdu spremanja podataka?
        """
        try:
            #promjeni cursor u wait cursor
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

            #dohvati frame iz dokumenta
            frejm = self.dokument.get_frame(key = self.gKanal, tmin = self.tmin, tmax = self.tmax)
            
            assert type(frejm) == pd.core.frame.DataFrame, 'Kontroler.upload_agregirane_to_REST:Assert fail, frame pogresnog tipa'
            if len(frejm) > 0:
                #agregiraj podatke
                agregirani = self.satniAgreg.agregiraj_kanal(frejm)
                
                #provjeri stupanj validacije agregiranog frejma
                testValidacije = agregirani[u'flag'].map(self.test_stupnja_validacije)
                lenSvih = len(testValidacije)
                lenDobrih = len(testValidacije[testValidacije == True])
                if lenSvih == lenDobrih:
                    msg = msg = 'Spremi agregirane podatke od ' + str(self.gKanal) + ':' + str(self.tmin.date()) + '\nna REST web servis?'
                else:
                    msg = 'Spremi agregirane podatke od ' + str(self.gKanal) + ':' + str(self.tmin.date()) + '\nna REST web servis?'
                    warn = '\nOPREZ!\nNeki podaci nisu validirani. Prilikom spremanja svi podaci smatraju se validiranima.'
                    msg = msg+warn
                
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
                    self.restWriter.upload(jso = jstring)
            
            #vrati izgled cursora nazad na normalni
            QtGui.QApplication.restoreOverrideCursor()
        except AssertionError as e1:
            self.prikazi_error_msg(e1)
        except pomocneFunkcije.AppExcept as e2:
            self.prikazi_error_msg(e2)
        finally:
            #vrati izgled cursora nazad na normalni
            QtGui.QApplication.restoreOverrideCursor()
###############################################################################
    def prikazi_glavni_graf_dijalog(self):
        """            
        Metoda poziva modalni dijalog za izbor postavki grafa.
        Ako se prihvati izbor, promjene se defaultne vrijednosti te se 
        informacija o promjeni propagira dalje.
        """
        #napravi kopiju trenutnih postavki
        postavke = copy.deepcopy(self.graf_defaults)
        #inicijaliziraj i prikazi dijalog.
        dijalogDetalji = dijalog1.OpcijeGrafova(
            defaulti = postavke, 
            opiskanala = self.mapa_mjerenjeId_to_opis, 
            stablo = self.modelProgramaMjerenja)
            
        if dijalogDetalji.exec_(): #ako je OK vraca 1, isto kao i True
            postavke = dijalogDetalji.dohvati_postavke()
            #kopiraj nove postavke i postavi ih u graf_defaults
            self.graf_defaults = copy.deepcopy(postavke)
            """
            moramo pokrenuti pripremu podataka jer pomocni kanali nisu nuzno ucitani.
            Priprema podataka poziva crtanje satnog grafa, a naredba za crtanje
            satnog grafa ukljucuje crtanje minutnog (ili clear)
            """
            #provjeri da li je izabran neki datum
            if self.tmin != None:
                targ = (self.tmin - datetime.timedelta(minutes = 1)) # timestamp
                targ = str(targ.date())
                self.priredi_podatke([self.gKanal, targ])
###############################################################################
    def naredi_crtanje_satnog(self):
        """
        Funkcija koja emitira signal sa naredbom za crtanje samo ako je prethodno
        zadan datum, tj. donja i gornja granica intervala.
        """
        if (self.tmin != None and self.tmax != None):
            self.emit(QtCore.SIGNAL('nacrtaj_satni_graf(PyQt_PyObject)'), [self.graf_defaults, self.tmin, self.tmax])
            #promjena labela u panelima sa grafovima, opis
            try:
                opisKanala = self.mapa_mjerenjeId_to_opis[self.gKanal]
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
                        self.naredi_crtanje_minutnog(self.sat)
                    else:
                        #clear minutni graf ako se datum pomakne
                        self.emit(QtCore.SIGNAL('clear_minutni_graf'))
            except (TypeError, LookupError) as err:
                print(err)
                self.prikazi_error_msg(err)
###############################################################################
    def naredi_crtanje_minutnog(self, izabrani_sat):
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
            self.emit(QtCore.SIGNAL('nacrtaj_minutni_graf(PyQt_PyObject)'),[self.graf_defaults, lowLim, highLim])
###############################################################################
    def promjeni_flag(self, lista):
        """
        Odgovor kontrolora na zahtjev za promjenom flaga. Kontrolor naredjuje
        dokumentu da napravi odgovarajucu izmjenu.
        Ulazni parametar je lista koja sadrzi [tmin, tmax, novi flag, kanal].
        tocan vremenski interval (rubovi su ukljuceni), novu vrijednost flaga, 
        te program mjerenja (kanal) na koji se promjena odnosi.
        
        P.S. dokument ima vlastiti signal da javi kada je doslo do promjene
        """
        self.dokument.change_flag(key = lista[3], tmin = lista[0], tmax = lista[1], flag = lista[2])
###############################################################################
    def vrati_agregirani_frejm(self, kanal):
        """
        Ova metoda prihvaca zahtjev za frejmom specificnog kanala. Kontroler
        prati koji je datum izabran te je zaduzen da vrati nazad agregirani 
        slajs frejma iz dokumenta koji odgovara kanalu i vremenskim rubovima 
        datuma. Nakon sto dohvati podatke, emitira signal sa agregiranim 
        slajsom frejma i kanalom (upakiranim u listu).
        """
        #TODO! ako ne dohvati frame iz dokumenta, vrati None
        try:
            frejm = self.dokument.get_frame(key = kanal, tmin = self.tmin, tmax = self.tmax)
        except pomocneFunkcije.AppExcept as err:
            #dohvacanje frejma je propalo
            tekst = 'Trazena komponenta nije ucitana u model.\n' + str(repr(err))
            #TODO! potencijalno iritantni popup - silent ignore?
            self.prikazi_error_msg(tekst)
            frejm = None
        #provjeri da li je frame stvarno dataframe prije agregacije (i da nije None)
        if isinstance(frejm,pd.core.frame.DataFrame):
            #agregiraj
            agregiraniFrejm = self.satniAgreg.agregiraj_kanal(frejm)
            #agregator ce vratiti None ako mu se prosljedi prazan frejm
            if isinstance(agregiraniFrejm, pd.core.frame.DataFrame):
                #prosljedi kanalid, agregirani frejm i opis kanala (mapu) satnomCanvasu
                opisKanala = self.mapa_mjerenjeId_to_opis[kanal]
                arg = [kanal, agregiraniFrejm, opisKanala]
                #emitiraj signal
                self.emit(QtCore.SIGNAL('emitiraj_agregirani(PyQt_PyObject)'), arg)
###############################################################################
    def vrati_minutni_frejm(self, lista):
        """
        zaprima zahtjev za frejm [kanal, tmin, tmax], dohvaca trazeni slajs od 
        dokumenta, reemitira trazeni slice.
        """
        frejm = self.dokument.get_frame(key = lista[0], tmin = lista[1], tmax = lista[2])
        if isinstance(frejm, pd.core.frame.DataFrame):
            #dodaj opis slajsa kanala, (mjerna jedinica, naziv, formula...)
            opisKanala = self.mapa_mjerenjeId_to_opis[lista[0]]
            arg = [lista[0], frejm, opisKanala]
            self.emit(QtCore.SIGNAL('emitiraj_minutni_slajs(PyQt_PyObject)'), arg)
###############################################################################
    def update_satni_grid(self, x):
        self.graf_defaults['ostalo']['opcijesatni']['grid'] = x
        self.naredi_crtanje_satnog()
###############################################################################        
    def update_satni_cursor(self, x):
        self.graf_defaults['ostalo']['opcijesatni']['cursor'] = x
        self.naredi_crtanje_satnog()
###############################################################################        
    def update_satni_span(self, x):
        self.graf_defaults['ostalo']['opcijesatni']['span'] = x
        self.naredi_crtanje_satnog()
###############################################################################        
    def update_satni_ticks(self, x):
        self.graf_defaults['ostalo']['opcijesatni']['ticks'] = x
        self.naredi_crtanje_satnog()
###############################################################################        
    def update_satni_legenda(self, x):
        self.graf_defaults['ostalo']['opcijesatni']['legend'] = x
        self.naredi_crtanje_satnog()
###############################################################################    
    def update_minutni_grid(self, x):
        self.graf_defaults['ostalo']['opcijeminutni']['grid'] = x
        #malo konfuzno, promjena flaga minutnog povlaci crtanje minutnog grafa
        self.promjena_flaga_minutni()
###############################################################################        
    def update_minutni_cursor(self, x):
        self.graf_defaults['ostalo']['opcijeminutni']['cursor'] = x
        self.promjena_flaga_minutni()
###############################################################################        
    def update_minutni_span(self, x):
        self.graf_defaults['ostalo']['opcijeminutni']['span'] = x
        self.promjena_flaga_minutni()
###############################################################################        
    def update_minutni_ticks(self, x):
        self.graf_defaults['ostalo']['opcijeminutni']['ticks'] = x
        self.promjena_flaga_minutni()
###############################################################################        
    def update_minutni_legenda(self, x):
        self.graf_defaults['ostalo']['opcijeminutni']['legend'] = x
        self.promjena_flaga_minutni()
###############################################################################
    def promjena_flaga_minutni(self):
        """
        Adapter, model emitira signal ako je doslo do promjene flaga, ali taj
        signal ne nosi informaciju o trenutno izabranom satu. Funkcija poziva
        na ponovno crtanje minutnog grafa sa ispravnim argumentom.
        
        P.S. zbog nacina rada, ovu funkciju mozemo iskoristiti i kada dolazi
        do promjene postavki minutnog grafa. npr. promjena prikaza minor tickova.
        """
        if self.sat != None:
            self.naredi_crtanje_minutnog(self.sat)
###############################################################################
    def save_preset(self):
        """
        Funkcija omogucava spremanje postavki aplikacije u binary file.
        Sprema se geometrija prozora, postavke grafova iz self.graf_defaults, 
        stanje checkboxeva toolbarova isl.
        """
        #zapamti bine komponente
        preset = self.gui.saveState()
        geometrija = self.gui.geometry()
        ostalo = copy.deepcopy(self.graf_defaults)
        #poslozi ih u dictionary
        mapa = {'preset':preset, 'geometrija':geometrija, 'ostalo':ostalo}
        try:
            #dohvati filename i stvori novi file uz pomoc getSaveFileName dijaloga
            fileName = QtGui.QFileDialog.getSaveFileName(parent = self.gui, 
                                                     caption = 'Spremi postavke', 
                                                     filter = "Dat files (*.dat);;All files(*.*)")

            if fileName:
                with open(fileName, 'wb') as fwrite:
                    pickle.dump(mapa, fwrite)
                    print('save preset ok')
                    
        except Exception as err:
            #opceniti fail akcije, javi error
            tekst = 'Save postavki aplikacije nije uspjesno izveden.\n\n'+str(err)
            self.prikazi_error_msg(tekst)
###############################################################################
    def load_preset_mehanika(self, fileName):
        """
        Funkcija odradjuje ucitavanje postavki ako je zadan file.
        Mehanika iza postavljana preseta.
        """
        mapa = None
        
        if fileName:
            with open(fileName, 'rb') as fread:
                mapa = pickle.load(fread)

        try:
            tekst = 'Pogreska prilikom ucitavanja postavki.\nFile je corrupted ili je zadan pogresni file.'
            assert isinstance(mapa, dict), tekst #provjera da je mapa tipa dict
            assert ('geometrija' in mapa.keys()), tekst #provjera za trazeni kljuc u dictu
            assert ('preset' in mapa.keys()), tekst #provjera za trazeni kljuc u dictu
            assert ('ostalo' in mapa.keys()), tekst #provjera za trazeni kljuc u dictu
            assert isinstance(mapa['geometrija'],QtCore.QRect), tekst #provjera tipa trazenog objekta
            assert isinstance(mapa['preset'],QtCore.QByteArray), tekst #provjera tipa trazenog objekta
            assert isinstance(mapa['ostalo'],dict), tekst #provjera tipa trazenog objekta
            #provjera da li je mapa programa mjerenja zadana, potrebna je radi smislenog zadavanja kanala za crtanje
            if self.mapa_mjerenjeId_to_opis == None:
                raise AssertionError('Mapa programa mjerenja nije zadana.\nPokusajte se ponovno spojiti na REST servis.')
            
            #svi dostupni kljucevi programaMjerenjaId
            presetGlavniKanal = self.graf_defaults['glavniKanal']['validanOK']['kanal']
            set1 = set(self.mapa_mjerenjeId_to_opis)
            #set kljuceva spremljenih u mapa['ostalo']
            set2 = []
            #dodaj glavni kanal
            set2.append(mapa['ostalo']['glavniKanal']['validanOK']['kanal'])
            #dodaj pomocne kanale
            for graf in mapa['ostalo']['pomocniKanali']:
                set2.append(mapa['ostalo']['pomocniKanali'][graf]['kanal'])
            #convert listu u set
            set2 = set(set2)
            #None moze biti u setu 2, makni ga sa popisa
            if None in set2:
                set2.remove(None)
            #porvjera da li je set2 subset seta1, tj. da li su svi kljucevi u ucitanim
            #defaultnim grafovima dostupni REST readeru (ako nisu javi error)
            assert set2.issubset(set1), 'Neki ucitani programi mjerenja nisu dobro definirani (nisu dostupni REST servisu)'

            #postavi geometriju
            self.gui.setGeometry(mapa['geometrija'])
            #postavi state displaya
            self.gui.restoreState(mapa['preset'])
            #postavi defaultne grafove
            self.graf_defaults = copy.deepcopy(mapa['ostalo'])
            
            #sinhroniziraj checkable akcije sa ucitanim stanjem
            self.update_gui_action_state()
            #TODO!
            #promjeni glavni kanal u rest izborniku (QTreeView) da odgovara novom glavnom kanalu
            presetGlavniKanal = self.graf_defaults['glavniKanal']['validanOK']['kanal']
            if presetGlavniKanal != None:
                print('postavi kanal...emitiraj novu postavku gui/restizborniku')
                self.emit(QtCore.SIGNAL('set_glavni_kanal_izbornik(PyQt_PyObject)'),presetGlavniKanal)
        
        except AssertionError as err:
            opis = 'Load postavki aplikacije nije uspjesno izveden.\n\n' + str(err)
            self.prikazi_error_msg(opis)				
###############################################################################
    def load_preset(self):
        """
        Funkcija omogucava ucitavanje postavke aplikacije iz binarnog filea.
        File treba biti prethodno spremljen uz pomoc self.save_preset().
        """
        #dohvati fileName uz pomoc getOpenFileName dijaloga
        fileName = QtGui.QFileDialog.getOpenFileName(parent = self.gui, 
                                                     caption = 'Ucitaj postavke',
                                                     filter = "Dat files (*.dat);;All files(*.*)")
        try:
            #provjera da li file postoji
            assert os.path.isfile(fileName), 'File ne postoji'
            self.load_preset_mehanika(fileName)
        except AssertionError as err:
            opis = 'Za load preset nije zadan ispravan file.\n'+str(err)
            self.prikazi_error_msg(opis)
###############################################################################
    def nacrtaj_zero_span(self, lista):
        """
        Crtanje zero span podataka.
        1. dohvati podatke sa REST servisa, 
        2. naredi crtanje istih
        """
        progMjer = int(lista[0])
        datum = str(lista[1])
        try:
            #dokvati listu [zeroFrejm, spanFrejm]
            frejmovi = self.webZahtjev.get_zero_span(progMjer, datum)
            #emitiraj signal za crtanjem
            self.emit(QtCore.SIGNAL('crtaj_zero(PyQt_PyObject)'), frejmovi[0])
            self.emit(QtCore.SIGNAL('crtaj_span(PyQt_PyObject)'), frejmovi[1])
            
        except pomocneFunkcije.AppExcept as err:
            opis = 'Problem kod ucitavanja Zero/Span podataka sa REST servisa.' + str(err)
            self.prikazi_error_msg(opis)
            
###############################################################################