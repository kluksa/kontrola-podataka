# -*- coding: utf-8 -*-
"""
Created on Thu Dec 18 14:32:49 2014

@author: User
"""

from PyQt4 import QtCore, QtGui
import pandas as pd
from datetime import timedelta
import copy
import pickle

import datamodel
import datareader
import agregator
import networking_funkcije
import dijalog1
###############################################################################
###############################################################################
class Kontroler(QtCore.QObject):
    """
    Poveznica izmedju Gui kontrola i logike programa, poveznica sa modelom.
    """
    def __init__(self, parent = None, gui = None):
        QtCore.QObject.__init__(self, parent)
        """inicijalizacija relevantnih objekata i membera"""
        
        #url settings za REST web zahtjev i njegova incijalizacija
        self.baza = "http://172.20.1.166:9090/SKZ-war/webresources/"
        self.resursi = {"siroviPodaci":"dhz.skz.rs.sirovipodaci", 
                        "programMjerenja":"dhz.skz.aqdb.entity.programmjerenja"}
        self.webZahtjev = networking_funkcije.WebZahtjev(self.baza, self.resursi)

        #inicijalizacija dokumenta
        self.dokument = datamodel.DataModel()

        #konstrukcija pomocnih dictova, adapteri za upis u dokument i izbornike
        self.programToKomponenta, self.komponentaToProgram = self.make_transformation_dicts(self.webZahtjev)

        #inicijalizacija citaca
        self.csvReader = datareader.FileReader(model = self.dokument, mapa = self.komponentaToProgram)
        self.restReader = datareader.RESTReader(model = self.dokument, source = self.webZahtjev)
        self.restWriter = datareader.RESTWriterAgregiranih(source = self.webZahtjev)

        #ocekuje se da se prosljedi instanca valjanog GUI elementa 
        self.gui = gui
        
        #defaultne vrijednosti za crtanje grafova (kanal je program mjerenja)
        self.graf_defaults = {
                'glavniKanal':{
                    'midline':{'kanal':None, 'line':'-', 'rgb':(0,0,0), 'alpha':1.0, 'zorder':100, 'label':'average'},
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
        #rubovi vremenskog intervala za izbor datuma (zadnje izabran datum)
        self.gKanal = None
        self.tmin = None
        self.tmax = None
        self.sat = None
        #incijalizacija agregatora
        self.satniAgreg = agregator.Agregator()
        #povezivanje signala i funkcija
        self.poveznice()
###############################################################################
    def poveznice(self):
        """
        Funkcija koja postavlja logicke veze izmedju dijelova programa.
        """
        ###save/load preset akcije###
        self.connect(self.gui, 
                     QtCore.SIGNAL('request_save_preset'),
                     self.save_preset)
                     
        self.connect(self.gui, 
                     QtCore.SIGNAL('request_load_preset'),
                     self.load_preset)
                     
        self.connect(self, 
                     QtCore.SIGNAL('update_action_state(PyQt_PyObject)'), 
                     self.gui.reset_action_state)
                     
        self.connect(self, 
                     QtCore.SIGNAL('prebaci_glavni_kanal(PyQt_PyObject)'), 
                     self.gui.webLoggerIzbornik.postavi_novi_glavni_kanal)

        
        ####izbor programa mjerenja i datuma####
        self.connect(self.gui.webLoggerIzbornik,
                     QtCore.SIGNAL('gui_izbornik_citaj(PyQt_PyObject)'), 
                     self.priredi_podatke)
                     
        ###update labela u panelu za grafove###
        self.connect(self, 
                     QtCore.SIGNAL('update_graf_label(PyQt_PyObject)'), 
                     self.gui.panel.change_label)
        
        ###clear minutnog grafa###
        self.connect(self, 
                     QtCore.SIGNAL('clear_minutni_graf'), 
                     self.gui.panel.minutniGraf.clear_minutni)
                     
        ###prebacivanje dana naprijed / nazad###
        self.connect(self.gui.panel, 
                     QtCore.SIGNAL('prebaci_dan(PyQt_PyObject)'), 
                     self.promjeni_datum)
                     
        self.connect(self, 
                     QtCore.SIGNAL('dan_naprjed'), 
                     self.gui.webLoggerIzbornik.sljedeci_dan)
                     
        self.connect(self, 
                     QtCore.SIGNAL('dan_nazad'), 
                     self.gui.webLoggerIzbornik.prethodni_dan)


                     
        ###spajanje signala za crtanje sa specificnim canvasima###
        self.connect(self, 
                     QtCore.SIGNAL('nacrtaj_satni_graf(PyQt_PyObject)'), 
                     self.gui.panel.satniGraf.crtaj)
        
        self.connect(self, 
                     QtCore.SIGNAL('nacrtaj_minutni_graf(PyQt_PyObject)'), 
                     self.gui.panel.minutniGraf.crtaj)
                     
        self.connect(self, 
                     QtCore.SIGNAL('promjena_flaga_minutni(PyQt_PyObject)'), 
                     self.gui.panel.minutniGraf.crtaj)

        
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






        ###promjena flaga###
        self.connect(self.gui.panel.satniGraf,
                     QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), 
                     self.promjeni_flag)

        self.connect(self.gui.panel.minutniGraf,
                     QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), 
                     self.promjeni_flag)
                     
        self.connect(self.dokument, 
                     QtCore.SIGNAL('model_flag_changed'), 
                     self.naredi_crtanje_satnog)
        #crtanje satnog ukljucuje crtanje minutnog ako je prethodno izabrani sat unutar datuma
        self.connect(self.dokument, 
                     QtCore.SIGNAL('model_flag_changed'), 
                     self.naredi_crtanje_satnog)




        ###READ FROM FILE###
        self.connect(self.gui, 
                     QtCore.SIGNAL('KEEP_OUT(PyQt_PyObject)'),
                     self.read_from_csv_file)
        
        
        ####povezivanje raznih kontrola sa displaya vezano za izgled grafova####
        self.connect(self.gui.webLoggerIzbornik,
                     QtCore.SIGNAL('promjeni_postavke_grafova'), 
                     self.prikazi_glavni_graf_dijalog)
                     
        ###SATNI###
        self.connect(self.gui, 
                     QtCore.SIGNAL('update_satni_grid(PyQt_PyObject)'), 
                     self.update_satni_grid)

        self.connect(self.gui, 
                     QtCore.SIGNAL('update_satni_cursor(PyQt_PyObject)'), 
                     self.update_satni_cursor)

        self.connect(self.gui, 
                     QtCore.SIGNAL('update_satni_span(PyQt_PyObject)'), 
                     self.update_satni_span)

        self.connect(self.gui, 
                     QtCore.SIGNAL('update_satni_ticks(PyQt_PyObject)'), 
                     self.update_satni_ticks)

        self.connect(self.gui, 
                     QtCore.SIGNAL('update_satni_legenda(PyQt_PyObject)'), 
                     self.update_satni_legenda)
        ###MINUTNI###
        self.connect(self.gui, 
                     QtCore.SIGNAL('update_minutni_grid(PyQt_PyObject)'), 
                     self.update_minutni_grid)

        self.connect(self.gui, 
                     QtCore.SIGNAL('update_minutni_cursor(PyQt_PyObject)'), 
                     self.update_minutni_cursor)

        self.connect(self.gui, 
                     QtCore.SIGNAL('update_minutni_span(PyQt_PyObject)'), 
                     self.update_minutni_span)

        self.connect(self.gui, 
                     QtCore.SIGNAL('update_minutni_ticks(PyQt_PyObject)'), 
                     self.update_minutni_ticks)

        self.connect(self.gui, 
                     QtCore.SIGNAL('update_minutni_legenda(PyQt_PyObject)'), 
                     self.update_minutni_legenda)





    
###############################################################################
    #funkcije za update defaultnih vrijednosti za crtanje (grid, ticks....)
    ###SATNI###
    def update_satni_grid(self, x):
        self.graf_defaults['ostalo']['opcijesatni']['grid'] = x
        print('satni grid', x)
        self.naredi_crtanje_satnog()
###############################################################################        
    def update_satni_cursor(self, x):
        self.graf_defaults['ostalo']['opcijesatni']['cursor'] = x
        print('satni cursor', x)
        self.naredi_crtanje_satnog()
###############################################################################        
    def update_satni_span(self, x):
        self.graf_defaults['ostalo']['opcijesatni']['span'] = x
        print('satni span', x)
        self.naredi_crtanje_satnog()
###############################################################################        
    def update_satni_ticks(self, x):
        self.graf_defaults['ostalo']['opcijesatni']['ticks'] = x
        print('satni ticks', x)
        self.naredi_crtanje_satnog()
###############################################################################        
    def update_satni_legenda(self, x):
        self.graf_defaults['ostalo']['opcijesatni']['legend'] = x
        print('satni legenda', x)
        self.naredi_crtanje_satnog()
###############################################################################    
    ###MINUTNI###
    def update_minutni_grid(self, x):
        self.graf_defaults['ostalo']['opcijeminutni']['grid'] = x
        print('minutni grid', x)
        #malo konfuzno, promjena flaga minutnog povlaci crtanje minutnog grafa
        self.promjena_flaga_minutni()
###############################################################################        
    def update_minutni_cursor(self, x):
        self.graf_defaults['ostalo']['opcijeminutni']['cursor'] = x
        print('minutni cursor', x)
        self.promjena_flaga_minutni()
###############################################################################        
    def update_minutni_span(self, x):
        self.graf_defaults['ostalo']['opcijeminutni']['span'] = x
        print('minutni span', x)
        self.promjena_flaga_minutni()
###############################################################################        
    def update_minutni_ticks(self, x):
        self.graf_defaults['ostalo']['opcijeminutni']['ticks'] = x
        print('minutni ticks', x)
        self.promjena_flaga_minutni()
###############################################################################        
    def update_minutni_legenda(self, x):
        self.graf_defaults['ostalo']['opcijeminutni']['legend'] = x
        print('minutni legenda', x)
        self.promjena_flaga_minutni()
###############################################################################
    def naredi_crtanje_satnog(self):
        """
        Funkcija koja emitira signal sa naredbom za crtanje samo ako je prethodno
        zadan datum, tj. donja i gornja granica intervala.
        """
        if (self.tmin != None and self.tmax != None):
            self.emit(QtCore.SIGNAL('nacrtaj_satni_graf(PyQt_PyObject)'), [self.graf_defaults, self.tmin, self.tmax])
            #promjena labela u panelima sa grafovima, opis
            kanalText = str(self.programToKomponenta[self.gKanal])
            argList = [kanalText, str(self.tmin), str(self.tmax)]
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
###############################################################################
    def priredi_podatke(self, lista):
        """
        Funkcija prihvaca listu [program_mjerenja_id, datum] i radi sljedece:
        
        -postavlja program_mjerenja_id kao glavni kanal
        -uz pomoc REST citaca pokusava ucitati sve sirove podatke u dokument
        (prolazi i kroz sve pomocne kanale iz self.graf_defaults)
        -prilikom zavrsetka emitira signal sa listom [self.graf_defaults, tmin, tmax]
        koji ce se naknadno koristiti kao signal za crtanje grafova
        """
        #TODO! Promjena datuma i/ili kanala! Pitaj za save podataka?
        self.upload_agregirane_to_REST()
        
        self.gKanal = lista[0]
        datum = lista[1] #datum je string formata YYYY-MM-DD
        
        #pretvaranje datuma u 2 timestampa od 00:01:00 do 00:00:00 iduceg dana
        tsdatum = pd.to_datetime(datum)
        self.tmax = tsdatum + timedelta(days = 1)
        self.tmin = tsdatum + timedelta(minutes = 1)
        #za svaki slucaj, pobrinimo se da su varijable pandas.tslib.Timestamp
        self.tmax = pd.to_datetime(self.tmax)
        self.tmin = pd.to_datetime(self.tmin)

        sviBitniKanali = []
        sviBitniKanali.append(self.gKanal)
        #postavi novi glavni kanal svugdje gdje je to bitno
        for graf in self.graf_defaults['glavniKanal']:
            self.graf_defaults['glavniKanal'][graf]['kanal'] = self.gKanal
        #pronadji sve ostale kanale potrebne za crtanje
        for graf in self.graf_defaults['pomocniKanali']:
            sviBitniKanali.append(self.graf_defaults['pomocniKanali'][graf]['kanal'])
        #pokusaj ucitati sve kanale
        ucitani = []
        for kanal in sviBitniKanali:
            t = self.restReader.read(key = kanal, date = datum)
            #lista uspjeha citanja, elementi su tuple (kanal, datum, True/False)
            ucitani.append((kanal, datum, t))
        #emit signala sa naredbom za crtanje grafova
        self.naredi_crtanje_satnog()
###############################################################################        
    def read_from_csv_file(self):
        """
        BITNO!
        Pomocna funkcija za ucitavanje csv fileova u dokument.
        Moguce je ucitati vise csv fileova istovremeno.
        Koristi samo ako znas sve posljedice!!!!!
        
        objesnjenje:
        -Oba citaca "pisu" po istom dokumentu
        -Oba citaca (REST i CSV) interno prate sto su ucitali (neka vrsta cachea)
        te je nemoguce dva puta ucitati isti zahtjev sa bilo kojim citacem.
        -za isti datum i program mjerenja drugi citac moze "trajno pregaziti" 
        vec ucitane vrijednosti koje ne mozemo vratiti zbog cache mehanizma citaca
        """
        #instanca dijaloga, parent je instanca gui
        x = QtGui.QFileDialog(parent = self.gui)
        #lista izabranih fileova
        popisFileova = x.getOpenFileNames(caption='Open files', 
                                          filter='CSV Weblogger (*.csv)')
        
        #ucitavanje fileova u dokument
        self.csvReader.read_path_list(pathList = popisFileova)
###############################################################################            
    def make_transformation_dicts(self, webzahtjev):
        """
        Funkcija stvara 2 dictionarija za pomoc prilikom citanja fileova i 
        popunjavanja nekih izbornika.
        
        Primjer.
        stanica, komponenta --> programMjerenja???
        programMjerenja --> stanica, komponenta ???
        
        Bitno za konverziju FileReadera, POSTAJA MORA BITI LOWERCASE!!!
        radi nekonzistentnog pisanja podataka u fileovima i u bazi
        """
        basemap = webzahtjev.get_sve_programe_mjerenja()
        mapa1 = {}
        mapa2 = {}       
        for key in basemap.keys():
            programMjerenja = int(key)
            formula = basemap[key]['komponentaFormula']
            mjernajedinica = basemap[key]['komponentaMjernaJedinica']
            postajaNaziv = basemap[key]['postajaNaziv'].lower()
            
            mapa1[programMjerenja] = formula+'-'+mjernajedinica
            
            mapa2[postajaNaziv] = {}
        for key in basemap.keys():
            programMjerenja = int(key)
            postajaNaziv = basemap[key]['postajaNaziv'].lower()
            
            mapa2[postajaNaziv][mapa1[programMjerenja]] = programMjerenja
        return mapa1, mapa2
###############################################################################
    def vrati_agregirani_frejm(self, kanal):
        """
        Ova metoda prihvaca zahtjev za frejmom specificnog kanala. Kontroler
        prati koji je datum izabran te je zaduzen da vrati nazad agregirani 
        slajs frejma iz dokumenta koji odgovara kanalu i vremenskim rubovima 
        datuma. Nakon sto dohvati podatke, emitira signal sa agregiranim 
        slajsom frejma i kanalom (upakiranim u listu).
        """
        frejm = self.dokument.get_frame(key = kanal, tmin = self.tmin, tmax = self.tmax)
        #provjeri da li je frame stvarno dataframe prije agregacije (i da nije None)
        if type(frejm) == pd.core.frame.DataFrame:
            #agregiraj
            agregiraniFrejm = self.satniAgreg.agregiraj_kanal(frejm)
            #agregator ce vratiti None ako mu se prosljedi prazan frejm
            if type(agregiraniFrejm) == pd.core.frame.DataFrame:
                arg = [kanal, agregiraniFrejm]
                #emitiraj signal
                self.emit(QtCore.SIGNAL('emitiraj_agregirani(PyQt_PyObject)'), arg)
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
    def naredi_crtanje_minutnog(self, izabrani_sat):
        """
        Ova funkcija se brine za pravilni odgovor na ljevi klik tocke na satno
         agregiranom grafu. Za zadani sat, odredjuje rubove intervala te salje
        dobro zadani zahtjev za crtanjem minutnom canvasu.
        """
        self.sat = izabrani_sat
        if self.sat <= self.tmax and self.sat >=self.tmin:
            highLim = self.sat
            lowLim = highLim - timedelta(minutes = 59)
            lowLim = pd.to_datetime(lowLim)
            self.emit(QtCore.SIGNAL('nacrtaj_minutni_graf(PyQt_PyObject)'),[self.graf_defaults, lowLim, highLim])       
###############################################################################
    def promjena_flaga_minutni(self):
        """
        Adapter, model emitira signal ako je doslo do promjene flaga, ali taj
        signal ne nosi informaciju o trenutno izabranom satu. Funkcija poziva
        na ponovno crtanje minutnog grafa sa ispravnim argumentom.
        """
        if self.sat != None:
            self.naredi_crtanje_minutnog(self.sat)
###############################################################################
    def vrati_minutni_frejm(self, lista):
        """
        zaprima zahtjev za frejm [kanal, tmin, tmax], dohvaca trazeni slajs od 
        dokumenta, reemitira trazeni slice.
        """
        frejm = self.dokument.get_frame(key = lista[0], tmin = lista[1], tmax = lista[2])
        if type(frejm) == pd.core.frame.DataFrame:
            arg = [lista[0], frejm]
            self.emit(QtCore.SIGNAL('emitiraj_minutni_slajs(PyQt_PyObject)'), arg)
###############################################################################
    def prikazi_glavni_graf_dijalog(self):
        """            
        Metoda poziva modalni dijalog za izbor postavki grafa.
        Ako se prihvati izbor, promjene se defaultne vrijednosti te se 
        informacija o promjeni propagira dalje.
        """
        #definicija pomocnih mapa za konverziju programa mjerenja u kanal i nazad
        self.kanali = {}
        self.programiMjerenja = {}
        for keystanica in self.komponentaToProgram:
            for keykomponenta in self.komponentaToProgram[keystanica]:
                programMjerenja = self.komponentaToProgram[keystanica][keykomponenta]
                self.kanali[keystanica+'::'+keykomponenta] = programMjerenja
                self.programiMjerenja[programMjerenja] = keystanica+'::'+keykomponenta
                
        postavke = copy.deepcopy(self.graf_defaults)
        dijalogDetalji = dijalog1.IzborStoSeCrta(mapaKanali = self.kanali, rMapaKanali = self.programiMjerenja, defaulti = self.graf_defaults)
        if dijalogDetalji.exec_(): #ako je OK vraca 1, isto kao i True
            postavke = dijalogDetalji.dohvati_postavke()
            self.graf_defaults = copy.deepcopy(postavke)
            #moramo pokrenuti pripremu podataka, pomocni kanali nisu nuzno ucitani
            #priprema podataka nakon sto zavrsi poziva crtanje satnog grafa
            #satni graf po potrebi poziva crtanje minutnog grafa (ili ga cleara)
            targ = str((self.tmin - timedelta(minutes = 1))) # timestamp u string formatu
            self.priredi_podatke([self.gKanal, targ])
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
        #dohvati filename gdje ih spremamo
        fileName = QtGui.QFileDialog.getSaveFileName(parent = self.gui, 
                                                     caption = 'Spremi postavke', 
                                                     filter = "Dat files (*.dat);;All files(*.*)")
        if fileName:
            with open(fileName, 'wb') as fwrite:
                pickle.dump(mapa, fwrite)
                print('Postavke su spremljene')
###############################################################################
    def load_preset(self):
        """
        Funkcija omogucava ucitavanje postavke aplikacije iz binarnog filea.
        File treba biti prethodno spremljen uz pomoc self.save_preset().
        """
        print('load preset starts')
        mapa = None
        #implicitni fail prilikom ucitavanja
        test = False
        #dohvati fileName
        fileName = QtGui.QFileDialog.getOpenFileName(parent = self.gui, 
                                                     caption = 'Ucitaj postavke',
                                                     filter = "Dat files (*.dat);;All files(*.*)")
        if fileName:
            with open(fileName, 'rb') as fread:
                mapa = pickle.load(fread)
                #provjere da li je file ispravan
                if type(mapa) == dict:
                    print('mapa je dict')
                    kljucevi = list(mapa.keys())
                    if ('geometrija' in kljucevi) and ('preset' in kljucevi) and ('ostalo' in kljucevi):
                        t1 = type(mapa['geometrija']) == QtCore.QRect
                        t2 = type(mapa['preset']) == QtCore.QByteArray
                        t3 = type(mapa['ostalo']) == dict
                        test = t1 and t2 and t3
        
                if test:
                    #napravi set kljuceva od svih dostupnih rest readeru
                    set1 = set(list(self.programToKomponenta.keys()))
                    #napravi set kljuceva svih podataka u mapa['ostalo']
                    set2 = []
                    set2.append(mapa['ostalo']['glavniKanal']['validanOK']['kanal'])
                    for graf in mapa['ostalo']['pomocniKanali']:
                        set2.append(mapa['ostalo']['pomocniKanali'][graf]['kanal'])
                    set2 = set(set2)
                    #None moze biti u setu2... makni ga
                    if None in set2:
                        set2.remove(None)
                    #provjera da li je set2 subset seta1 tj. da li su svi kljucevi u
                    #novim defaultnim opcijama grafova dostupni REST readeru
                    if set2.issubset(set1):
                        #postavi geometriju
                        self.gui.setGeometry(mapa['geometrija'])
                        #postavi state displaya
                        self.gui.restoreState(mapa['preset'])
                        #postavi defaultne grafove
                        self.graf_defaults = copy.deepcopy(mapa['ostalo'])
                        #sinhroniziraj checkable akcije sa ucitanim stanjem
                        self.refresh_toolbar_akcije()
                        #pomakni programski promjeni izabrani kanal u webloggeru (TreeNode.py)
                        presetGlavniKanal = self.graf_defaults['glavniKanal']['validanOK']['kanal']
                        if presetGlavniKanal != None:
                            self.emit(QtCore.SIGNAL('prebaci_glavni_kanal(PyQt_PyObject)'), int(presetGlavniKanal))
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
    def refresh_toolbar_akcije(self):
        """
        Funkcija informira display o stanju checkable akcija (Satni grid, ...). 
        Primarno sluzi za pravilan prikaz displaya prilikom ucitavanja postavki 
        nakon sto pozovemo funkciju self.load_preset
        
        Emitirati cemo skraceni dict postavki koje treba podesiti:
        """
        checkableActionList = {}
        checkableActionList['satnigrid'] = self.graf_defaults['ostalo']['opcijesatni']['grid']
        checkableActionList['satnispan'] = self.graf_defaults['ostalo']['opcijesatni']['span']
        checkableActionList['satniticks'] = self.graf_defaults['ostalo']['opcijesatni']['ticks']
        checkableActionList['satnicursor'] = self.graf_defaults['ostalo']['opcijesatni']['cursor']
        checkableActionList['satnilegend'] = self.graf_defaults['ostalo']['opcijesatni']['legend']
        checkableActionList['minutnigrid'] = self.graf_defaults['ostalo']['opcijeminutni']['grid']
        checkableActionList['minutnispan'] = self.graf_defaults['ostalo']['opcijeminutni']['span']
        checkableActionList['minutniticks'] = self.graf_defaults['ostalo']['opcijeminutni']['ticks']
        checkableActionList['minutnicursor'] = self.graf_defaults['ostalo']['opcijeminutni']['cursor']
        checkableActionList['minutnilegend'] = self.graf_defaults['ostalo']['opcijeminutni']['legend']
        
        #emit updateani dict stanja displayu
        self.emit(QtCore.SIGNAL('update_action_state(PyQt_PyObject)'), checkableActionList)
###############################################################################
    def upload_agregirane_to_REST(self):
        """
        funkcija uzima slice glavnog kanala, agregira ga, i uploada na rest servis.
        Prompt za potvrdu spremanja podataka?
        
        konceptualni problemi:
        1. sto tocno spremiti na REST?
            - trenutno, agregirane vrijednosti glavnoga kanala za zadani dan
            (tj. trenutno nacrtani graf)
            
        2. gdje tocno pozvati funkciju i kada?
            -prilikom prebacivanja dana u kalendaru
            -prilikom prebacivanja glavnog kanala
            
        3. upozoriti ako nisu svi podaci validirani?
            -provjera je implementirana i radi, ali samo printa rezultat provjere.
            -trenutno svi podaci se smartraju validiranima

        DODATNO:
        izlazni json ce biti poput liste, gdje je svaki element jedan redak
        pandas datafrejma
        
        Treba:
        -srediti "pamcenje" sto smo spremili da se ne ponavljamo (lista ili nesto slicno)
        -srediti bolji opis glavnog kanala u poruci ili ga izbaciti van?
        """
        #TODO! implementacije uploada na rest servis
        frejm = self.dokument.get_frame(key = self.gKanal, tmin = self.tmin, tmax = self.tmax)
        if type(frejm) == pd.core.frame.DataFrame:
            if len(frejm) > 0:
                #agregiraj
                agregirani = self.satniAgreg.agregiraj_kanal(frejm)

                #provjeri da li je cijeli agregirani frejm validiran
                testValidacije = agregirani[u'flag'].map(self.test_stupnja_validacije)
                lenSvih = len(testValidacije)
                lenDobrih = len(testValidacije[testValidacije == True])
                print(lenSvih, lenDobrih)
                if lenSvih == lenDobrih:
                    msg = 'Spremi agregirane podatke od ' + str(self.gKanal) + ':' + str(self.tmin.date()) + '\nna REST web servis?'
                    print('svi su validirani')
                else:
                    msg = 'Spremi agregirane podatke od ' + str(self.gKanal) + ':' + str(self.tmin.date()) + '\nna REST web servis?'
                    warn = '\nOPREZ!\nNeki podaci nisu validirani. Prilikom spremanja svi podaci smatraju se validiranima.'
                    msg = msg+warn
                    print('neki nisu validirani')
                
                #prompt izbora spremanja filea
                odgovor = QtGui.QMessageBox.question(self.gui,
                                                     "Potvrdi spremanje na REST web servis", 
                                                     msg, 
                                                     QtGui.QMessageBox.Yes|QtGui.QMessageBox.No)
                                            
                if odgovor == QtGui.QMessageBox.Yes:
                    #upload potvrdjen, nastavi dalje
                    #napravi novi prazan frame indeksiran na isti nacin kao i agregirani
                    output = pd.DataFrame(index = agregirani.index)
                    #dodaj trazene stupce u output frejm
                    output['programMjerenjaId'] = int(self.gKanal)
                    output['vrijeme'] = agregirani.index.map(self.timestamp_to_ispravan_json_format)
                    output['vrijednost'] = agregirani['avg']
                    output['status'] = agregirani['status']
                    output['obuhvat'] = agregirani['count'].map(self.agregirani_count_to_postotak)
                    #konverzija output frejma u json string
                    jstring = output.to_json(orient = 'records')
                    print(jstring)
                    #upload uz pomoc self.restWriter, NOT IMPLEMENTED
                    self.restWriter.upload(jso = jstring)
            else:
                print('model je vratio prazan frejm')
        else:
            print('model je vratio None, krivi ulazni parametri')
###############################################################################
    def agregirani_count_to_postotak(self, x):
        """
        Pomocna funkcija za racunanje obuhvata agregiranih podataka
        """
        return int(x*100/60)
###############################################################################
    def timestamp_to_ispravan_json_format(self, x):
        """
        Pomocna funkcija za pretvorbu timestampa u tocno definirani string.
        'YYYY-MM-DDTHH:mm'
        """
        #convert to string 'YYYY-MM-DD HH:mm:ss'
        datum = str(x)
        #adaptiraj
        out = datum[:10]+'T'+datum[11:]
        out = out[:-3]
        return out
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
###############################################################################