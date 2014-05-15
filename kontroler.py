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
        self.lastLoadedFile=None
        self.trenutnaListaKanala=None
        self.trenutnaListaSati=None
        self.lastKanal=None
        self.lastSat=None
        """
        Connections
        """
        #status bar updates (jedino direktno spajanje modela i gui)
        self.connect(self,
                     QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),
                     gui.set_status_bar)

        self.connect(gui,
                     QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),
                     gui.set_status_bar)

        self.connect(model,
                     QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),
                     gui.set_status_bar)
        
        #read csv procedure
        self.connect(gui,
                     QtCore.SIGNAL('gui_request_read_csv(PyQt_PyObject)'),
                     self.med_read_csv)

        self.connect(self,
                     QtCore.SIGNAL('med_request_read_csv(PyQt_PyObject)'),
                     model.citaj_csv)

        self.connect(model,
                     QtCore.SIGNAL('doc_get_kljucevi(PyQt_PyObject)'),
                     self.set_trenutnaListaKanala)

        self.connect(self,
                     QtCore.SIGNAL('med_update_kanali(PyQt_PyObject)'),
                     gui.set_kanali)

        
        #crtaj satni procedure
        self.connect(gui,
                     QtCore.SIGNAL('gui_request_crtaj_satni(PyQt_PyObject)'),
                     self.med_request_crtaj_satni)
        
        self.connect(self,
                     QtCore.SIGNAL('med_request_draw_satni(PyQt_PyObject)'),
                     model.doc_pripremi_satne_podatke)
                     
        self.connect(model,
                     QtCore.SIGNAL('doc_draw_satni(PyQt_PyObject)'),
                     self.med_naredi_crtaj_satni)

        self.connect(self,
                     QtCore.SIGNAL('med_draw_satni(PyQt_PyObject)'),
                     gui.canvasSatni.crtaj)
                     
        self.connect(model,
                     QtCore.SIGNAL('doc_sati(PyQt_PyObject)'),
                     self.set_trenutnaListaSati)
                     
        self.connect(self,
                     QtCore.SIGNAL('med_update_sati(PyQt_PyObject)'),
                     gui.set_sati)
        
        #crtaj minutni procedure
        #gumb
        self.connect(gui,
                     QtCore.SIGNAL('gui_request_crtaj_minutni(PyQt_PyObject)'),
                     self.med_request_crtaj_minutni)
                     
        self.connect(self,
                     QtCore.SIGNAL('med_ewquest_draw_minutni(PyQt_PyObject)'),
                     model.doc_pripremi_minutne_podatke)
        
        self.connect(model,
                     QtCore.SIGNAL('doc_minutni_podatci(PyQt_PyObject)'),
                     self.med_naredi_crtaj_minutni)
        
        self.connect(self,
                     QtCore.SIGNAL('med_draw_minutni(PyQt_PyObject)'),
                     gui.canvasMinutni.crtaj)
                     
        self.connect(model,
                     QtCore.SIGNAL('doc_trenutni_sat(PyQt_PyObject)'),
                     self.set_lastSat)
                     
        self.connect(self,
                     QtCore.SIGNAL('med_update_sat(PyQt_PyObject)'),
                     gui.set_sat)
        
        #crtaj minutni procedure
        #event na satnom canvasu ljevi klik - dalje se veze na connecte gumba
        self.connect(gui.canvasSatni,
                     QtCore.SIGNAL('odabirSatni(PyQt_PyObject)'),
                     self.med_request_crtaj_minutni)
        
        
        #change flag minutni procedure
        self.connect(gui.canvasMinutni,
                     QtCore.SIGNAL('flagTockaMinutni(PyQt_PyObject)'),
                     self.med_request_flag_minutni)
        
        self.connect(self,
                     QtCore.SIGNAL('med_request_flag_minutni(PyQt_PyObject)'),
                     model.promjeni_flag_minutni)
                     
        self.connect(model,
                     QtCore.SIGNAL('reagregiranje_gotovo(PyQt_PyObject)'),
                     self.crtaj_grafove)
                     
        self.connect(gui.canvasMinutni,
                     QtCore.SIGNAL('flagSpanMinutni(PyQt_PyObject)'),
                     self.med_request_flag_minutni_span)
                     
        self.connect(self,
                     QtCore.SIGNAL('med_request_flag_minutni_span(PyQt_PyObject)'),
                     model.promjeni_flag_minutni_span)
                     
        self.connect(gui.canvasSatni,
                     QtCore.SIGNAL('flagSatni(PyQt_PyObject)'),
                     self.med_request_flag_satni)
                     
        
        
###############################################################################

    def med_read_csv(self,filepath):
        self.lastLoadedFile=filepath
        message='Loading and preparing file '+filepath
        self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),message)
        self.emit(QtCore.SIGNAL('med_request_read_csv(PyQt_PyObject)'),filepath)
    
    
    def med_request_crtaj_satni(self,kanal):
        self.lastKanal=kanal
        message='Drawing aggregated data for '+kanal
        self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),message)
        self.emit(QtCore.SIGNAL('med_request_draw_satni(PyQt_PyObject)'),
                  kanal)
        
    def med_naredi_crtaj_satni(self,dataframe):
        self.emit(QtCore.SIGNAL('med_draw_satni(PyQt_PyObject)'),dataframe)
        
    def med_request_crtaj_minutni(self,sat):
        """
        Na ovu metodu se spaja i gumb (sat je string) i event lijevi klik misa
        na grafu (sat je lista timestampova). U slucaju da je klik misem,
        prilagodimo podatke da vraća string prvog indeksa (adapter).
        """
        if type(sat)==list:
            sat=str(sat[0])
        
        self.lastSat=sat
        self.emit(QtCore.SIGNAL('med_ewquest_draw_minutni(PyQt_PyObject)'),
                  sat)
                  
    def med_naredi_crtaj_minutni(self,data):
        self.emit(QtCore.SIGNAL('med_draw_minutni(PyQt_PyObject)'),data)
        
    def med_request_flag_satni(self,lista):
        """
        Zahtjev od gui za promjenu flaga, lista=[sat,novi flag]
        -desni klik misa na satnom grafu
        
        Ovaj zahtjev je povezan s promjenom minutnog flaga, tj. promjena je
        na minutnom intervalu [sat-59min:sat] - adapter
        """
        sat=lista[0]
        flag=lista[1]
        #ovo je u biti slucaj sa spanom, samo moramo zadati donju granicu
        sat=pd.to_datetime(sat)
        satMin=sat-timedelta(minutes=59)
        #castanje nazad u string
        satMax=str(sat)
        satMin=str(satMin)
        data=[satMin,satMax,flag]
        
        #poziv na mjenjanje flaga spanu
        self.med_request_flag_minutni_span(data)
    
    def med_request_flag_minutni(self,lista):
        """
        Zahtjev od gui za promjenu flaga, lista=[sat,flag]
        -desni klik misa na minutnom grafu
        
        Promjena flaga za jedan minutni podatak
        """
        dic={'time':lista[0],
             'flag':lista[1],
             'kanal':self.lastKanal,
             'sat':self.lastSat}
        self.emit(QtCore.SIGNAL('med_request_flag_minutni(PyQt_PyObject)'),
                  dic)
        message='Reaggregating'
        self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),message)
        
    def med_request_flag_minutni_span(self,lista):
        """
        Zahtjev od gui za promjenu flaga, lista=[min,max,flag]
        -lijevi klik misa (moze i click and drag)
        
        Promjena flaga na vise minutnih podataka u rasponu
        """
        down=lista[0]
        up=lista[1]
        flag=lista[2]
        if down==up:
            #slucaj kada su granice raspona iste, reducira se na desni klik
            self.med_request_flag_minutni(self,[down,flag])
        
        dic={'min':down,
             'max':up,
             'flag':flag,
             'kanal':self.lastKanal,
             'sat':self.lastSat}
        
        self.emit(QtCore.SIGNAL('med_request_flag_minutni_span(PyQt_PyObject)'),
                  dic)
            
    
    def crtaj_grafove(self,lista):
        """
        Ova fuckija služi za ponovo crtanje oba grafa nakon reagregiranja
        """
        self.lastKanal=lista[0]
        self.lastSat=lista[1]
        #naredbe za crtanje
        self.med_request_crtaj_satni(self.lastKanal)
        self.med_request_crtaj_minutni(self.lastSat)
    
###############################################################################
    def set_lastLoadedFile(self,filepath):
        self.lastLoadedFile=filepath
        
    def set_trenutnaListaKanala(self,kanali):
        self.trenutnaListaKanala=kanali
        self.emit(QtCore.SIGNAL('med_update_kanali(PyQt_PyObject)'),kanali)
        
    def set_trenutnaListaSati(self,sati):
        self.trenutnaListaSati=sati
        self.emit(QtCore.SIGNAL('med_update_sati(PyQt_PyObject)'),sati)
        
    def set_lastKanal(self,kanal):
        self.lastKanal=kanal
        self.emit(QtCore.SIGNAL('med_update_kanal(PyQt_PyObject)'),kanal)
        
    def set_lastSat(self,sat):
        self.lastSat=sat
        self.emit(QtCore.SIGNAL('med_update_sat(PyQt_PyObject)'),sat)
        
        

