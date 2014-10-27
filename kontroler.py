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
    
    Uspjesno se inicijalizira tek kada mu se prosljedi instanca gui-a i instanca
    dokumenta. Mora znati koje elemente povezuje.
    
    job list:
    1. na zahtjev gui-a postaviti citac u dokument
    2. smisleno popunjavanje gui izbornika sa naredbama
    3. dohvatiti tj. zatraziti od dokumenta podatke
    4. update podataka po potrebi u dokumentu
    5. pamtiti stanje zahtjeva
    """
    def __init__(self, parent = None, gui = None, dokument = None):
        """Konstruktor klase"""
        QtGui.QWidget.__init__(self, parent)
        
        if gui == None and dokument == None:
            raise IOError('Pogresno inicijalizirani kontroler')
        
        #atributi
        self.__dokument = dokument #instanca dokumenta
        self.__citac = None #instanca citaca
        self.__dostupni = None #svi dostupni podatci do kojih se moze doci
        self.__trenutnaStanica = None #trenutno aktivna stanica
        self.__tMin = None #trenutno aktivna donja granica vremenskog slicea
        self.__tMax = None #trenutno aktivna gornja granica vremenskog slicea
        self.__satni = None #zadnje dohvaceni slice frejma agregiranih
        self.__minutni = None #zadnje dohvaceni slice frejma minutnih
        self.__trenutniSat = None #sat za koji je nacrtan minutni graf

        #TODO!
        #veze sa gui-em nisu podesene kako treba, provjeri objekte koji salju i
        #primaju signale npr. gui.weblogger_izbornik
        #popravi na kraju
        #TODO!
        #sredi promjenu kursora tjekom ucitavanja isl...kao dekorator?

        #gui - set citac
        self.connect(gui.webLoggerIzbornik, 
                     QtCore.SIGNAL('gui_set_citac(PyQt_PyObject)'),
                     self.set_citac)
        
        #setter stanica za gui
        self.connect(self, 
                     QtCore.SIGNAL('kontrola_set_stanice(PyQt_PyObject)'), 
                     gui.webLoggerIzbornik.set_stanice)
        
        #gui - izbor stanice
        self.connect(gui.webLoggerIzbornik,
                     QtCore.SIGNAL('gui_izbor_stanice(PyQt_PyObject)'),
                     self.postavi_datume)

        #setter datuma za gui
        self.connect(self, 
                     QtCore.SIGNAL('kontrola_dostupni_datumi(PyQt_PyObject)'),
                     gui.webLoggerIzbornik.set_datumi)
        
        #gui - odabir datuma (direktno ili preko navigacijskih gumbi)
        self.connect(gui.webLoggerIzbornik,
                     QtCore.SIGNAL('gui_vremenski_raspon(PyQt_PyObject)'), 
                     self.priredi_vremenski_raspon)
                     
#        #kontroler - canvasi , postavljanje frejmova
#        self.connect(self, 
#                     QtCore.SIGNAL('kontrola_set_satni(PyQt_PyObject)'), 
#                     gui.satniCanvas.zamjeni_frejmove)
#                     
#        self.connect(self, 
#                     QtCore.SIGNAL('kontrola_set_minutni(PyQt_PyObject)'), 
#                     gui.minutniCanvas.zamjeni_frejmove)
#        
#        #spajanje ljevog klika na satnom grafu sa fokusiranjem minutnog grafa
#        self.connect(gui.satniCanvas.canvasSatni, 
#                     QtCore.SIGNAL('gui_crtaj_minutni_graf(PyQt_PyObject)'), 
#                     gui.minutniCanvas.canvasMinutni.fokusiraj_interval)        
#                     
#        #gui - izbor na satnom grafu, naredba za crtanje minutnih podataka
#        self.connect(gui.satniCanvas,
#                     QtCore.SIGNAL('gui_crtaj_minutni_graf(PyQt_PyObject)'),
#                     self.crtaj_minutni)
#                     
#        #naredba gui dijelu za crtanje satnih podataka
#        self.connect(self, 
#                     QtCore.SIGNAL('kontrola_crtaj_satni_frejm(PyQt_PyObject)'), 
#                     gui.satniCanvas.crtaj)
#                     
#        #naredba gui dijelu za crtanje minutnih podataka
#        self.connect(self, 
#                     QtCore.SIGNAL('kontrola_crtaj_minutni_frejm(PyQt_PyObject)'), 
#                     gui.minutniCanvas.crtaj)
#                     
#        #gui - promjena flaga na satnom grafu
#        self.connect(gui.satniCanvas, 
#                     QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), 
#                     self.promjena_flaga)
#
#        #gui - promjena flaga na minutnom grafu
#        self.connect(gui.minutniCanvas, 
#                     QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), 
#                     self.promjena_flaga)
###############################################################################
    def set_citac(self, citac):
        """Postavljanje citaca u dokument"""
        self.__citac = citac
        #poziv metode dokumenta da postavi citac
        self.__dokument.set_citac(self.__citac)
        #upit za dostupne podatke do kojih dokument moze doci
        self.__dostupni = self.__dokument.dohvati_dostupne_podatke()
        #update izbornik stanica u gui-u
        stanice = sorted(list(self.__dostupni.keys()))
        if stanice != []:
            self.emit(QtCore.SIGNAL('kontrola_set_stanice(PyQt_PyObject)'), stanice)
        else:
            #TODO!
            #neki info da nema dostupnih stanica, popup il nesto u tom stilu
            pass
###############################################################################
    def postavi_datume(self, stanica):
        """
        Metoda signalizira gui-u koji su datumi dostupni za stanicu
        """
        def string_to_date(x):
            return QtCore.QDate.fromString(x, 'yyyy-MM-dd')
            
        temp = []
        datumi = []
        #zapamti izbor stanice
        self.__trenutnaStanica = stanica
        
        for i in map(str, self.__dostupni[stanica]):
            temp.append(i)
        
        for i in map(string_to_date, temp):
            datumi.append(i)
        #emit list to gui
        self.emit(QtCore.SIGNAL('kontrola_dostupni_datumi(PyQt_PyObject)'), datumi)
###############################################################################
    def priredi_vremenski_raspon(self, data):
        """
        Funkcija naredjuje dokumentu da pripremi trazene podatke
        """
        #TODO!
        #trebam doci do svih frejmova za tu kombinaciju stanice i vremena
        
        #zapamti izbor
        self.__trenutnaStanica = data[0]
        self.__tMin = data[1]
        self.__tMax = data[2]
        #naredba dokumentu da pripremi podatke (ucitava po potrebi)
        self.__dokument.pripremi_podatke(self.__trenutnaStanica,
                                         self.__tMin, 
                                         self.__tMax)
                
        self.__minutni, self.__satni = self.__dokument.dohvati_podatke(
            self.__trenutnaStanica, 
            self.__tMin, 
            self.__tMax)
#        
#        self.emit(QtCore.SIGNAL('kontrola_set_satni(PyQt_PyObject)'), self.__satni)
#        self.emit(QtCore.SIGNAL('kontrola_set_minutni(PyQt_PyObject)'), self.__minutni)
        
###############################################################################
#    def crtaj_satni(self, kanal):
#        """
#        Funkcija trazi od dokumenta slice satno agregiranih podataka zadanih
#        ulaznim parametrima.
#        
#        stanica, kanal, min i max vrijeme slicea (ukljucujuci granice)
#        """
#        self.__trenutniKanal = kanal
#        #dohvati trazene sliceove minutnih i agregiranih podataka
#        self.__minutni, self.__satni = self.__dokument.dohvati_podatke(
#            self.__trenutnaStanica, 
#            self.__trenutniKanal, 
#            self.__tMin, 
#            self.__tMax)
#            
#        #emit crtanje satnog grafa
#        self.emit(QtCore.SIGNAL('kontrola_crtaj_satni_frejm(PyQt_PyObject)'), self.__satni)
#        #ako je bio nacrtani minutni graf, emit i za njegovo crtanje
#        if self.__trenutniSat != None:
#            self.crtaj_minutni(self.__trenutniSat)
#        
################################################################################
#    def crtaj_minutni(self, sat):
#        """
#        Funkcija crta minutni niz podataka
#        sat -> pandas datetime timestamp. Mora odgovarati indeksu u datafrejmu
#        """
#        self.__trenutniSat = sat #kraj intervala
#        start = sat - timedelta(minutes=59)
#        start = pd.to_datetime(start)
#        #dohvati trazeni dio minutnog frejma
#        frejm = self.__minutni.copy()
#        frejm = frejm[frejm.index >= start]
#        frejm = frejm[frejm.index <= self.__trenutniSat]
#        
#        self.emit(QtCore.SIGNAL('kontrola_crtaj_minutni_frejm(PyQt_PyObject)'), frejm)
###############################################################################
#    def promjena_flaga(self, data):
#        """
#        naredba za promjenu flagova na grafu
#        data -> lista podataka -> [start, end, novi flag]
#        flag se mjenja na minutnim podatcima, updatea se dokument, 
#        ponovi se zahtjev za crtanjem.
#        """
#        start = data[0] #pandas timestamp
#        end = data[1] #pandas timestamp
#        noviFlag = data[2] #int? mozda float, da se razlikuju od automatskih??
#        
#        #start i end potencijalo ne postoje kao indeksi, workaround
#        #dohvati slice
#        frejm = self.__minutni.copy()
#        frejm = frejm[frejm.index >= start]
#        frejm = frejm[frejm.index <= end]
#        #postavi flag
#        frejm['flag'] = noviFlag
#        print(frejm)
#        #TODO!
#        #update flaga u dokumentu
#        self.__dokument.update_frejm(
#            self.__trenutnaStanica, 
#            self.__trenutniKanal, 
#            frejm)
#        #povlacenje novih podataka iz dokumenta
#        self.__minutni, self.__satni = self.__dokument.dohvati_podatke(
#                self.__trenutnaStanica, 
#                self.__trenutniKanal, 
#                self.__tMin, 
#                self.__tMax)
#        #zahtjevi za crtanjem, pozovi crtanje satnog, sa zadnjim kanalom
#        #crtanje satnog ce povuci crtanje minutnog ako je prethodno bio nacrtan
#        self.crtaj_satni(self.__trenutniKanal)

###############################################################################
###############################################################################