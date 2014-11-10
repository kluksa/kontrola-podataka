# -*- coding: utf-8 -*-
"""
Created on Fri May  9 13:19:45 2014

@author: velimir

"""

from PyQt4 import QtGui,QtCore
#import pandas as pd
#from datetime import timedelta


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
                     
        #setter kanala za gui
        self.connect(self, 
                     QtCore.SIGNAL('kontrola_set_kanali(PyQt_PyObject)'), 
                     gui.webLoggerIzbornik.postavi_kanale)
                     
        #nakon izabranog datuma tj. promjene datuma kontroler je zaduzen
        #da informira i panele o izboru, paneli imaju specificnu metodu za to
        #slotovi zamjeni_frejmove povlace ponovno crtanje
        self.connect(self, 
                     QtCore.SIGNAL('kontrola_datum_promjenjen(PyQt_PyObject)'), 
                     gui.panel.zamjeni_frejmove)                    
        
        #spajanje projmene defaulta od webloggera sa slotom u displayu - load_defaults
        self.connect(gui.webLoggerIzbornik, 
                     QtCore.SIGNAL('wl_promjena_defaulta(PyQt_PyObject)'), 
                     gui.load_defaults)
        
        #signal da su defaulti u gui promjenjeni
        self.connect(gui, 
                     QtCore.SIGNAL('promjena_defaulta(PyQt_PyObject)'), 
                     self.promjena_defaulta)
                     
        #kontroler -> razni elementi guia, update defaultnih postavki grafova
        #slotovi zamjeni_defaulte povlace ponovno crtanje grafa
        self.connect(self, 
                     QtCore.SIGNAL('update_defaulti(PyQt_PyObject)'), 
                     gui.panel.zamjeni_defaulte)

        self.connect(self, 
                     QtCore.SIGNAL('update_defaulti(PyQt_PyObject)'), 
                     gui.panel.zamjeni_defaulte)
                     
        #spajanje zahtjeva za dohvacanjem satno agregiranog slicea (crtanje grafa)
        self.connect(gui.panel.satniGraf,
                     QtCore.SIGNAL('dohvati_agregirani_frejm_kanal(PyQt_PyObject)'), 
                     self.dohvati_agregirani_slajs)
        #dohvaceni frejm sa kanalom se prosljedjuje canvasu
        self.connect(self, 
                     QtCore.SIGNAL('set_agregirani_frejm(PyQt_PyObject)'), 
                     gui.panel.satniGraf.set_agregirani_kanal)
                     
        #ljevi klik na satnom grafu... zoom na minutni slice                     
        self.connect(gui.panel.satniGraf, 
                     QtCore.SIGNAL('gui_crtaj_minutni_graf(PyQt_PyObject)'), 
                     gui.panel.minutniGraf.fokusiraj_interval)
        
        #spajanje zahtjeva za dohvacanjem minutnog slicea (crtanje grafa)
        self.connect(gui.panel.minutniGraf,
                     QtCore.SIGNAL('dohvati_minutni_frejm_kanal(PyQt_PyObject)'), 
                     self.dohvati_minutni_slajs)
                     
        self.connect(self, 
                     QtCore.SIGNAL('set_minutni_frejm(PyQt_PyObject)'), 
                     gui.panel.minutniGraf.set_minutni_kanal)

        #promjena flaga na satnom grafu
        self.connect(gui.panel.satniGraf, 
                     QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), 
                     self.promjeni_flag)
                     
        #promjena flaga na minutnom grafu
        self.connect(gui.panel.minutniGraf, 
                     QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), 
                     self.promjeni_flag)

###############################################################################
    def set_citac(self, citac):
        """
        Postavljanje citaca u dokument
        
        Gui ocekuje odgovor koje su stanice dostupne citacu
        """
        self.__citac = citac
        #poziv metode dokumenta da postavi citac
        self.__dokument.set_citac(self.__citac)
        #upit za dostupne podatke do kojih dokument moze doci
        self.__dostupni = self.__dokument.dohvati_dostupne_podatke()
        #update izbornik stanica u gui-u
        stanice = sorted(list(self.__dostupni.keys()))
        if stanice != []:
            self.emit(QtCore.SIGNAL('kontrola_set_stanice(PyQt_PyObject)'), stanice)
###############################################################################
    def postavi_datume(self, stanica):
        """
        Metoda preuzima zahtjev za datumima (za danu stanicu).
        Signalizira gui-u koji su datumi dostupni za stanicu.
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
        ucitavanje podataka....
        nakon ucitavanja sastavlja listu koja sluzi kao vodic do dostupnih podataka
        [stainca, tmin, tmax, [lista dobrih kanala]] (u panelima je to self.__info)
        
        Ova metoda se primarno pokrece kada se promjeni datum u izborniku.
        Osim sto se treba updateati izbor za glavni kanal, moramo siglalizirati panelima
        da im se promjenio izvor podataka.
        """
        #promjeni cursor u wait cursor
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        
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
        self.emit(QtCore.SIGNAL('kontrola_set_kanali(PyQt_PyObject)'), self.__okFrejmovi)
        #emiti koji mjenjaju izvor podataka u panelima za grafove
        self.emit(QtCore.SIGNAL('kontrola_datum_promjenjen(PyQt_PyObject)'), self.__okFrejmovi)
        
        #vrati izgled cursora nazad na normalni
        QtGui.QApplication.restoreOverrideCursor()
###############################################################################
    def promjena_defaulta(self, defaulti):
        """
        Metoda zaprima promjenjeni dict u kojem se nalaze informacije sto i kako
        se treba crtati. Posao ove metode je tu informaciju prosljediti panelima
        (i drugim klasama koje prate stanje) da bi znali sto prikazati na grafu.
        
        """
        #reemit podataka
        self.emit(QtCore.SIGNAL('update_defaulti(PyQt_PyObject)'), defaulti)
###############################################################################
    def dohvati_agregirani_slajs(self, lista):
        """
        zahtjev od doumenta da vrati trazeni agregirani slajs podataka
        lista = [stanica, tmin, tmax, kanal]
        """
        frejm = self.__dokument.dohvati_agregirani_frejm(lista[0], 
                                                         lista[1], 
                                                         lista[2], 
                                                         lista[3])
        kanal = lista[3]
        self.emit(QtCore.SIGNAL('set_agregirani_frejm(PyQt_PyObject)'), [kanal, frejm])
###############################################################################
    def dohvati_minutni_slajs(self, lista):
        """
        zahtjev od doumenta da vrati trazeni slajs podataka
        lista = [stanica, tmin, tmax, kanal]
        """
        frejm = self.__dokument.dohvati_minutni_frejm(lista[0], 
                                                      lista[1], 
                                                      lista[2], 
                                                      lista[3])
        kanal = lista[3]
        self.emit(QtCore.SIGNAL('set_minutni_frejm(PyQt_PyObject)'), [kanal, frejm])
###############################################################################
    def promjeni_flag(self, lista):
        """
        zahtjev za promjenom flaga, lista tocne podatke sto se mora mjenjati
        lista:
        [0] -> min vremenski index, ukljucujuci
        [1] -> max vremenski index, ukljucujuci
        [2] -> vrijednost flaga , 1000 ako je tocka OK, -1000 ako nije
        podatak se smatra validiranim ako mu je abs(flag) == 1000
        [3] -> kanal, string
        [4] -> stanica, string
        """
        #promjeni cursor u wait cursor
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        
        #reci dokumentu da prebaci flag na trazenom mjestu
        self.__dokument.promjeni_flag(lista)
        
        #XXX!
        #mali workaround, treba javiti panelima da ponovno potegnu nove podatke
        #umjesto izmisljana tople vode, iskoritimo postojeci signal
        
        #dohvati informacije o "valjanim" frejmovima
        self.__okFrejmovi = self.__dokument.dohvati_info_podataka(self.__trenutnaStanica, 
                                                                  self.__tMin, 
                                                                  self.__tMax)

        self.emit(QtCore.SIGNAL('kontrola_datum_promjenjen(PyQt_PyObject)'), self.__okFrejmovi)
        
        #vrati izgled cursora nazad na normalni
        QtGui.QApplication.restoreOverrideCursor()
###############################################################################
