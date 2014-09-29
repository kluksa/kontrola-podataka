# -*- coding: utf-8 -*-
"""
Created on Fri May  9 13:19:45 2014

@author: velimir

Problemi:
status:
-Kontroler dobro incijalizira i model i view, link na test output funkciju radi ok
-Iz nekog razloga, model.citaj_csv ne radi
"""

from PyQt4 import QtGui,QtCore
import pandas as pd
from datetime import timedelta


class Kontrola(QtGui.QWidget):
    """Instanca kontrolera aplikacije
    
    Kontrolira tjek izvodjenja operacija izmedju GUI-a i Dokumenta.
    Pohranjuje trenutno aktivne podatke radi brzeg dohvacanja.
    
    Uspjesno se inicijalizira tek kada mu se prosljedi instanca gui-a i instanca
    dokumenta. Mora znati koje elemente povezuje.
    """
    def __init__(self, parent = None, gui = None, model = None):
        """Konstruktor klase"""
        QtGui.QWidget.__init__(self, parent)
        #TODO!
        #provjeri inicijalizaciju konstruktora
        self.__gui = gui
        self.__model = model
        self.__citac = None
        #memberi koji prate trenutno stanje tj.sto se trenutno prikazuje
        self.__trenutnaStanica = None
        self.__trenutniKanal = None
        self.__trenutniMinutniSlice = None
        self.__trenutniAgregiraniSlice = None
        self.__tMin = None
        self.__tMax = None
        
        """Povezivanje GUI --> Kontrola"""
        #TODO!
        #1. IZBOR CITACA (ili promjena)
        self.connect(self.__gui,
                     QtCore.SIGNAL('set_citac(PyQt_PyObject)'),
                     self.set_citac)
        #2. IZBOR STANICE 
        #3. IZBOR DATUMA (dozvoliti neki opceniti izbor raspona, min max ?)
        #4. IZBOR KANALA
        #5. INTERAKCIJA SA GRAFOM AGREGIRANIH PODATAKA
        #6. INTERAKCIJA SA GRAFOM MINUTNIH PODATAKA
        """Povezivanje Kontrola --> Dokument"""
        #TODO!
        #1. ZAHTJEV ZA POSTAVLJANJEM NOVOG CITACA
        #2. ZAHTJEV ZA MAPOM RASPOLOZIVIH PODATAKA
        #3. ZAHTJEV ZA POPISOM KANALA ZA STANICU I DATUM
        #4. ZAHTJEV ZA FREJMOVIMA (stanica, vrijeme, kanal)
        #5. ZAHTJEV ZA SPREMANJEM PODATAKA
        
        """Povezivanja Dokument --> Kontrola"""
        #TODO!
        #1. ODGOVOR NA POSTAVLJANJE CITACA
        #2. ODGOVOR, RASPOLOZIVI PODACI
        #3. ODGOVOR, RASPOLOZIVI KANALI ZA STANICU I DATUM
        #4. ODGOVOR, FREJMOVI
        
        """Povezivanje Kontrola --> GUI"""
        #TODO!
        #1. REFRESH LISTE STANICA
        #2. REFRESH LISTE DATUMA (update kalendara)
        #3. REFRESH LISTE KANALA
        #4. REFRESH GRAFOVA (clear, davanje novih naredbi za crtanjem)
        #5. INFORMATIVNE PORUKE (exceptions, warnings)
        #6. PROMJENA IZGLEDA KURSORA TJEKOM RADA

    def set_citac(self, citac):
        """
        Preuzima izabrani objekt citaca, prosljedjuje ga dokumentu
        
        Dokument je sadrzan u memberu self.__model
        """
        self.__citac = citac
        self.__model.set_citac(citac)
###############################################################################
###############################################################################
                     

class Mediator(QtGui.QWidget):
    """
    Pokusaj implementacije Mediator patterna
    
    Inicijalizacija mediatora:
        -kao argumente mu treba prosljediti gui instancu i instancu modela
    """
    def __init__(self,parent=None,gui=None,model=None):
        QtGui.QWidget.__init__(self,parent)

        """
        Connections
        """
###############################################################################
        """
        Status bar updates.
        
        -dodaj nove connectione po potrebi
        -budi konzistentan sa imenom emitiranog signala
        -mjenjaj samo odakle signal dolazi
        """
        self.connect(gui.webLoggerIzbornik,
                     QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),
                     gui.set_status_bar)
        
        self.connect(model,
                     QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),
                     gui.set_status_bar)
                     
        self.connect(self, 
                     QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),
                     gui.set_status_bar)
###############################################################################
        """
        Ulaz za frejmove.
        
        -dodaj nove connectione po potrebi
        -budi konzistentan sa imenom emitiranog signala
        -mjenjaj samo odakle signal dolazi
        """
        self.connect(gui.webLoggerIzbornik,
                     QtCore.SIGNAL('ucitani_frejmovi(PyQt_PyObject)'),
                     model.set_frejmovi)

###############################################################################
        """
        Ulaz za promjenu mjerenja (kanala)
        -dodaj nove connectione po potrebi
        -budi konzistentan sa imenom emitiranog signala
        -mjenjaj samo odakle signal dolazi
        """
        self.connect(gui.webLoggerIzbornik,
                     QtCore.SIGNAL('promjena_mjerenja(PyQt_PyObject)'), 
                     model.set_aktivni_frejm)
###############################################################################
        """
        Clear gui canvasa (grafova)
        """
        self.connect(model,
                     QtCore.SIGNAL('brisi_satni_graf()'), 
                     gui.canvasSatni.brisi_graf)
        
        self.connect(model,
                     QtCore.SIGNAL('brisi_minutni_graf()'), 
                     gui.canvasMinutni.brisi_graf)

        self.connect(model,
                     QtCore.SIGNAL('brisi_grafove()'), 
                     gui.canvasSatni.brisi_graf)
                     
        self.connect(model,
                     QtCore.SIGNAL('brisi_grafove()'), 
                     gui.canvasMinutni.brisi_graf)
###############################################################################
        """
        Crtanje grafova i gui kontrole vezane za grafove
        """
        #signali iz dokumenta prema gui-u vezani za crtanje
        #crtanje satnog grafa
        self.connect(model, 
                     QtCore.SIGNAL('crtaj_satni(PyQt_PyObject)'), 
                     gui.canvasSatni.crtaj)
        
        #crtanje minutnog grafa
        self.connect(model, 
                     QtCore.SIGNAL('crtaj_minutni(PyQt_PyObject)'), 
                     gui.canvasMinutni.crtaj)

                     
        #lijevi klik na satnom grafu (izbor sata)
        #1. dohvati signal sa grafa, prosljedi ga adapteru
        self.connect(gui.canvasSatni,
                     QtCore.SIGNAL('odabirSatni(PyQt_PyObject)'), 
                     self.med_request_crtaj_minutni)

        #2. prosljedi signal iz adaptera dokumentu
        self.connect(self, 
                     QtCore.SIGNAL('med_request_draw_minutni(PyQt_PyObject)'), 
                     model.crtaj_minutni_graf)
        

        #desni klik na satnom grafu (promjena flaga)
        #1. dohvati signal sa grafa
        self.connect(gui.canvasSatni, 
                     QtCore.SIGNAL('flagSatni(PyQt_PyObject)'), 
                     self.med_request_flag_change)
                     
        #2. prosljedi signal iz adaptera dokumentu
        self.connect(self, 
                     QtCore.SIGNAL('med_promjena_flaga_satni(PyQt_PyObject)'),
                     model.promjeni_flag)
                                      

        #desni klik na minutnom grafu(promjena flaga)
        #1. dohvati signal sa grafa
        self.connect(gui.canvasMinutni, 
                     QtCore.SIGNAL('flagTockaMinutni(PyQt_PyObject)'), 
                     self.med_request_flag_change)
                     
        #2. prosljedi signal iz adaptera dokumentu
        self.connect(self, 
                     QtCore.SIGNAL('med_promjena_flaga_min(PyQt_PyObject)'), 
                     model.promjeni_flag)
                     

        #span selection na minutnom grafu(promjena flaga)
        #1. dohvati signal sa grafa
        self.connect(gui.canvasMinutni, 
                     QtCore.SIGNAL('flagSpanMinutni(PyQt_PyObject)'), 
                     self.med_request_flag_change)
                     
        #2. prosljedi signal iz adaptera dokumentu
        self.connect(self, 
                     QtCore.SIGNAL('med_promjena_flaga_min_span2(PyQt_PyObject)'), 
                     model.promjeni_flag)
                     
        #3. prosljedi signal iz adaptera dokumentu
        self.connect(self, 
                     QtCore.SIGNAL('med_promjena_flaga_min_span1(PyQt_PyObject)'),  
                     model.promjeni_flag)

###############################################################################
    def med_request_crtaj_minutni(self,sat):
        """
        Vezan za lijevi klik na tocku u satnom grafu
        Graf moze vratiti listu timestampova ako je graf sitan ili ako je 
        puno tocaka. Ova funkcija je "adapter"
        """
        if type(sat) == list:
            sat=str(sat[0])
            
        sat=str(sat)
        #self.lastSat=sat
        self.emit(QtCore.SIGNAL('med_request_draw_minutni(PyQt_PyObject)'), sat)    
###############################################################################
    def med_request_flag_change(self, lista):
        """
        Vezan za desni klik na tocku u satnom grafu
        Ova funkcija je "adapter"
        ulaz --> [max vrijeme, novi flag, "potpis signala"]
        ulaz --> [min vrijeme, max vrijeme, novi flag, "potpis signala"]
        izlaz --> [min vrijeme, max vrijeme, novi flag]
        """
        if len(lista) == 3:
            if lista[2] == 'flagSatni':
                #slucaj desnog klika na tocku u satnom grafu
                satMax = pd.to_datetime(lista[0])
                satMin = satMax - timedelta(minutes=59)
                satMin = pd.to_datetime(satMin)
                data = [satMin, satMax, lista[1]]
                self.emit(QtCore.SIGNAL('med_promjena_flaga_satni(PyQt_PyObject)'), data)
            if lista[2] == 'flagSpanMinutni':
                #slucaj ljevog klika na minutnom grafu (tocka je ista)
                satMax = pd.to_datetime(lista[0])
                satMin = satMax
                data = [satMin, satMax, lista[1]]
                self.emit(QtCore.SIGNAL('med_promjena_flaga_min_span1(PyQt_PyObject)'), data)
            if lista[2] == 'flagTockaMinutni':
                #slucaj desnog klika na tocku u minutnom grafu
                data = [lista[0], lista[0], lista[1]]                
                self.emit(QtCore.SIGNAL('med_promjena_flaga_min(PyQt_PyObject)'), data)
        elif len(lista) == 4:
            if lista[3] == 'flagSpanMinutni':
                #slucaj sa spanom kada je pokriven interval
                lista.pop()
                data = lista
                self.emit(QtCore.SIGNAL('med_promjena_flaga_min_span2(PyQt_PyObject)'), data)
        else:
            message = 'Greska prilikom promjene flaga.'
            self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'), message)
###############################################################################
###############################################################################
