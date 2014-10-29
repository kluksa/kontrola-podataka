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
                     
        #kontroler - canvasi , postavljanje frejmova
        self.connect(self, 
                     QtCore.SIGNAL('kontrola_set_satni(PyQt_PyObject)'), 
                     gui.satniCanvas.zamjeni_frejmove)
        
        #spajanje zahtjeva za dohvacanjem satno agregiranog slicea (crtanje grafa)
        self.connect(gui.satniCanvas.canvasSatni,
                     QtCore.SIGNAL('dohvati_agregirani_frejm_kanal(PyQt_PyObject)'), 
                     self.dohvati_agregirani_slajs)
                     
        self.connect(self, 
                     QtCore.SIGNAL('set_agregirani_frejm(PyQt_PyObject)'), 
                     gui.satniCanvas.canvasSatni.set_agregirani_kanal)
                     
        #ljevi klik na satnom grafu... zoom na minutni slice                     
        self.connect(gui.satniCanvas.canvasSatni, 
                     QtCore.SIGNAL('gui_crtaj_minutni_graf(PyQt_PyObject)'), 
                     gui.minutniCanvas.canvasMinutni.fokusiraj_interval)
        


                     
#        self.connect(self, 
#                     QtCore.SIGNAL('kontrola_set_minutni(PyQt_PyObject)'), 
#                     gui.minutniCanvas.zamjeni_frejmove)
#                     
#        #promjena glavnog kanala na satnom grafu uvjetuje promjenu na minutnom                     
#        self.connect(gui.satniCanvas, 
#                     QtCore.SIGNAL('glavni_satni_kanal(PyQt_PyObject)'), 
#                     gui.minutniCanvas.postavi_glavni_kanal)
#                             
#
#        #promjena flaga na satnom grafu
#        self.connect(gui.satniCanvas.canvasSatni, 
#                     QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), 
#                     self.printaj)
#                     
#        #promjena flaga na minutnom grafu
#        self.connect(gui.minutniCanvas.canvasMinutni, 
#                     QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), 
#                     self.printaj)
                     
        
        
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
        
        #dohvati informacije o "valjanim" frejmovima
        self.__okFrejmovi = self.__dokument.dohvati_info_podataka(self.__trenutnaStanica, 
                                                                  self.__tMin, 
                                                                  self.__tMax)
        #emit koji postavlja izbor frejmova u gui
        self.emit(QtCore.SIGNAL('kontrola_set_satni(PyQt_PyObject)'), self.__okFrejmovi)
        self.emit(QtCore.SIGNAL('kontrola_set_minutni(PyQt_PyObject)'), self.__okFrejmovi)
        
###############################################################################
    def dohvati_agregirani_slajs(self, lista):
        """
        zahtjev od doumenta da vrati trazeni slajs podataka
        lista = [stanica, tmin, tmax, kanal]
        """
        frejm = self.__dokument.dohvati_agregirani_frejm(lista[0], 
                                                         lista[1], 
                                                         lista[2], 
                                                         lista[3])
        kanal = lista[3]
        self.emit(QtCore.SIGNAL('set_agregirani_frejm(PyQt_PyObject)'), [kanal, frejm])
###############################################################################
    def printaj(self, x):
        print(x)