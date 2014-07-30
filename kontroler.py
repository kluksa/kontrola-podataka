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

class Mediator(QtGui.QWidget):
    """
    Pokusaj implementacije Mediator patterna
    
    Inicijalizacija mediatora:
        -kao argumente mu treba prosljediti gui instancu i instancu modela
    """
    def __init__(self,parent=None,gui=None,model=None):
        QtGui.QWidget.__init__(self,parent)
        """
        Nekoliko membera
        """
#        self.lastLoadedFile=None
#        self.trenutnaListaKanala=None
#        self.trenutnaListaSati=None
#        self.lastKanal=None
#        self.lastSat=None

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
    
    
    
###############################################################################
    def med_request_crtaj_minutni(self,sat):
        """
        Graf moze vratiti listu timestampova ako je graf sitan ili ako je 
        puno tocaka. Ova funkcija je "adapter"
        """
        if type(sat)==list:
            sat=str(sat[0])
            
        sat=str(sat)
        #self.lastSat=sat
        self.emit(QtCore.SIGNAL('med_request_draw_minutni(PyQt_PyObject)'), sat)    
###############################################################################
    def printtest(self, x):
        print(x)
        #status bar updates (jedino direktno spajanje modela i gui)
#        self.connect(self,
#                     QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),
#                     gui.set_status_bar)
#
#        self.connect(gui,
#                     QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),
#                     gui.set_status_bar)
#
#        self.connect(model,
#                     QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),
#                     gui.set_status_bar)
#        
#        #read csv procedure
#        self.connect(gui.izborMapeSadrzaj,
#                     QtCore.SIGNAL('open_weblogger_file(PyQt_PyObject)'),
#                     self.med_read_csv)
#
#        self.connect(self,
#                     QtCore.SIGNAL('med_request_read_csv(PyQt_PyObject)'),
#                     model.citaj_csv)
#
#        self.connect(model,
#                     QtCore.SIGNAL('doc_get_kljucevi(PyQt_PyObject)'),
#                     self.set_trenutnaListaKanala)
#
#        self.connect(self,
#                     QtCore.SIGNAL('med_update_kanali(PyQt_PyObject)'),
#                     gui.izborMapeSadrzaj.set_mjerenja)

#TODO!
#connectioni se lome jer prilikom inicijalizacije weblogger_izbornik ne postoji :)
#1. treba inicijalizirati dock widget srediti prikazivanje uz neku opciju tipa hide/show
#2. kreni povezivati funkcionalnost korak po korak
#-open one file
#-open multiple files
#-crtanje satnih podataka
#-crtanje minutnih podataka
#-promjena na satnim podatcima
#-promjena na minutnim podatcima (single click/span)
#P.S. kod ispod je komentiran da ne smeta prilikom pokretanja aplikacije

#        #read csv (lista)
#        
#        #self.connect(gui.izborMapeSadrzaj,
#        #             QtCore.SIGNAL('read_lista(PyQt_PyObject)'),
#        #             self.med_read_lista_csv)
#        
#        self.connect(gui,
#                     QtCore.SIGNAL('read-lista(PyQt_PyObject)'),
#                     self.med_read_lista_csv)
#                     
#        self.connect(self,
#                     QtCore.SIGNAL('med_request_read_list_csv(PyQt_PyObject)'),
#                     model.citaj_lista_csv)
#                     
#        
#        #crtaj satni procedure
#        self.connect(gui,
#                     QtCore.SIGNAL('gui_request_crtaj_satni(PyQt_PyObject)'),
#                     self.med_request_crtaj_satni)
#        
#        self.connect(self,
#                     QtCore.SIGNAL('med_request_draw_satni(PyQt_PyObject)'),
#                     model.doc_pripremi_satne_podatke)
#                     
#        self.connect(model,
#                     QtCore.SIGNAL('doc_draw_satni(PyQt_PyObject)'),
#                     self.med_naredi_crtaj_satni)
#
#        self.connect(self,
#                     QtCore.SIGNAL('med_draw_satni(PyQt_PyObject)'),
#                     gui.canvasSatni.crtaj)
#        
#                     
#        #crtaj minutni procedure
#        self.connect(self,
#                     QtCore.SIGNAL('med_request_draw_minutni(PyQt_PyObject)'),
#                     model.doc_pripremi_minutne_podatke)
#        
#        self.connect(model,
#                     QtCore.SIGNAL('doc_minutni_podatci(PyQt_PyObject)'),
#                     self.med_naredi_crtaj_minutni)
#        
#        self.connect(self,
#                     QtCore.SIGNAL('med_draw_minutni(PyQt_PyObject)'),
#                     gui.canvasMinutni.crtaj)
#                     
#                     
#        #crtaj minutni procedure
#        #event na satnom canvasu ljevi klik - dalje se veze na connecte gumba
#        self.connect(gui.canvasSatni,
#                     QtCore.SIGNAL('odabirSatni(PyQt_PyObject)'),
#                     self.med_request_crtaj_minutni)
#        
#        
#        #change flag minutni procedure
#        self.connect(gui.canvasMinutni,
#                     QtCore.SIGNAL('flagTockaMinutni(PyQt_PyObject)'),
#                     self.med_request_flag_minutni)
#        
#        self.connect(self,
#                     QtCore.SIGNAL('med_request_flag_minutni(PyQt_PyObject)'),
#                     model.promjeni_flag_minutni)
#                     
#        self.connect(model,
#                     QtCore.SIGNAL('reagregiranje_gotovo(PyQt_PyObject)'),
#                     self.crtaj_grafove)
#                     
#        self.connect(gui.canvasMinutni,
#                     QtCore.SIGNAL('flagSpanMinutni(PyQt_PyObject)'),
#                     self.med_request_flag_minutni_span)
#                     
#        self.connect(self,
#                     QtCore.SIGNAL('med_request_flag_minutni_span(PyQt_PyObject)'),
#                     model.promjeni_flag_minutni_span)
#                     
#        self.connect(gui.canvasSatni,
#                     QtCore.SIGNAL('flagSatni(PyQt_PyObject)'),
#                     self.med_request_flag_satni)
#                  
#        #save csv procedura
#        self.connect(gui,
#                     QtCore.SIGNAL('gui_request_save_csv(PyQt_PyObject)'),
#                     self.med_request_save_csv)
#        
#        self.connect(self,
#                     QtCore.SIGNAL('med_request_save_csv(PyQt_PyObject)'),
#                     model.save_trenutni_frejmovi)
#                     
#        #load csv procedura
#        self.connect(gui,
#                     QtCore.SIGNAL('gui_request_load_csv(PyQt_PyObject)'),
#                     self.med_request_load_csv)
#                     
#        self.connect(self,
#                     QtCore.SIGNAL('med_request_load_csv(PyQt_PyObject)'),
#                     model.load_frejmovi_iz_csv)             
#        
#        #clear grafova
#        self.connect(model,
#                     QtCore.SIGNAL('grafovi_clear()'),
#                     self.clear_graphics)
#                     
#        self.connect(self,
#                     QtCore.SIGNAL('graphics_clear()'),
#                     gui.canvasSatni.brisi_graf)
#        
#        self.connect(self,
#                     QtCore.SIGNAL('graphics_clear()'),
#                     gui.canvasMinutni.brisi_graf)
#        
################################################################################
#
#    def med_read_csv(self,filepath):
#        self.lastLoadedFile=filepath
#        message='Loading and preparing file '+filepath
#        self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),message)
#        self.emit(QtCore.SIGNAL('med_request_read_csv(PyQt_PyObject)'),filepath)
#        
#    def med_read_lista_csv(self,lista):
#        self.lastLoadedFile=lista[-1]
#        message='Ucitavanje vise datoteka, molim pricekajte'
#        self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),message)
#        self.emit(QtCore.SIGNAL('med_request_read_list_csv(PyQt_PyObject)'),lista)
#        
#    def med_request_crtaj_satni(self,kanal):
#        self.lastKanal=kanal
#        message='Drawing aggregated data for '+kanal
#        self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),message)
#        self.emit(QtCore.SIGNAL('med_request_draw_satni(PyQt_PyObject)'),
#                  kanal)
#        
#    def med_naredi_crtaj_satni(self,dataframe):
#        self.emit(QtCore.SIGNAL('med_draw_satni(PyQt_PyObject)'),dataframe)
#        
#    def med_request_crtaj_minutni(self,sat):
#        """
#        Na ovu metodu se spaja i gumb (sat je string) i event lijevi klik misa
#        na grafu (sat je lista timestampova). U slucaju da je klik misem,
#        prilagodimo podatke da vraća string prvog indeksa (adapter).
#        """
#        if type(sat)==list:
#            sat=str(sat[0])
#            
#        sat=str(sat)
#        self.lastSat=sat
#        self.emit(QtCore.SIGNAL('med_request_draw_minutni(PyQt_PyObject)'),
#                  sat)
#                  
#    def med_naredi_crtaj_minutni(self,data):
#        self.emit(QtCore.SIGNAL('med_draw_minutni(PyQt_PyObject)'),data)
#        
#    def med_request_flag_satni(self,lista):
#        """
#        Zahtjev od gui za promjenu flaga, lista=[timestamp,novi flag]
#        -desni klik misa na satnom grafu
#        
#        Ovaj zahtjev je povezan s promjenom minutnog flaga, tj. promjena je
#        na minutnom intervalu [sat-59min:sat] - adapter
#        """
#        satMax=lista[0]
#        #type(sat)=='pandas.tslib.Timestamp'
#        flag=lista[1]
#        #ovo je u biti slucaj sa spanom, samo moramo zadati donju granicu
#        #sat=pd.to_datetime(sat)
#        satMin=satMax-timedelta(minutes=59)
#        
#        data=[satMin,satMax,flag]
#        self.lastSat=str(satMax)
#        
#        #poziv na mjenjanje flaga spanu
#        self.med_request_flag_minutni_span(data)
#    
#    def med_request_flag_minutni(self,lista):
#        """
#        Zahtjev od gui za promjenu flaga, lista=[timestamp,flag]
#        -desni klik misa na minutnom grafu
#        
#        Promjena flaga za jedan minutni podatak
#        """
#        dic={'time':lista[0],
#             'flag':lista[1],
#             'kanal':self.lastKanal,
#             'sat':self.lastSat}
#        self.emit(QtCore.SIGNAL('med_request_flag_minutni(PyQt_PyObject)'),
#                  dic)
#        message='Reaggregating'
#        self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),message)
#        
#    def med_request_flag_minutni_span(self,lista):
#        """
#        Zahtjev od gui za promjenu flaga, lista=[min,max,flag]
#        -lijevi klik misa (moze i click and drag)
#        
#        Promjena flaga na vise minutnih podataka u rasponu
#        """
#        if len(lista)==2:
#            #slucaj kada su granice raspona iste, reducira se na desni klik
#            down=lista[0]            
#            flag=lista[1]
#            data=[down,flag]
#            self.med_request_flag_minutni(data)
#        else:
#            #slucaj kada su granice raspona razlicite
#            down=lista[0]
#            up=lista[1]
#            flag=lista[2]
#        
#            dic={'min':down,
#                 'max':up,
#                 'flag':flag,
#                 'kanal':self.lastKanal,
#                 'sat':self.lastSat}
#        
#            self.emit(QtCore.SIGNAL('med_request_flag_minutni_span(PyQt_PyObject)'),
#                  dic)
#            
#    
#    def crtaj_grafove(self,lista):
#        """
#        Ova fuckija služi za ponovo crtanje oba grafa nakon reagregiranja
#        """
#        self.lastKanal=lista[0]
#        self.lastSat=lista[1]
#        #naredbe za crtanje
#        self.med_request_crtaj_satni(self.lastKanal)
#        self.med_request_crtaj_minutni(self.lastSat)
#        
#    def med_request_save_csv(self,filepath):
#        """
#        Prosljedi filename csv filea do dokumenta za save
#        """
#        self.emit(QtCore.SIGNAL('med_request_save_csv(PyQt_PyObject)'),filepath)
#    
#    def med_request_load_csv(self,filepath):
#        """
#        Prosljedi filename csv filea do dokumenta za load
#        """
#        self.lastLoadedFile=filepath
#        self.emit(QtCore.SIGNAL('med_request_load_csv(PyQt_PyObject)'),filepath)
#    
#    def clear_graphics(self):
#        """
#        Naredba za clear oba grafa
#        """
#        self.emit(QtCore.SIGNAL('graphics_clear()'))
################################################################################
#    def set_lastLoadedFile(self,filepath):
#        self.lastLoadedFile=filepath
#        
#    def set_trenutnaListaKanala(self,kanali):
#        self.trenutnaListaKanala=kanali
#        self.emit(QtCore.SIGNAL('med_update_kanali(PyQt_PyObject)'),kanali)
#        
#    def set_lastKanal(self,kanal):
#        self.lastKanal=kanal
#        self.emit(QtCore.SIGNAL('med_update_kanal(PyQt_PyObject)'),kanal)
#        
