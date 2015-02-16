# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 08:38:40 2014

@author: User

Klasa (canvas) za prikaz satno agregiranih vrijednosti.
"""
from PyQt4 import QtGui, QtCore

import matplotlib
from matplotlib.widgets import SpanSelector, Cursor

import functools #pomoc kod refactoringa koda

import pandas as pd

import datetime
from datetime import timedelta

import pomocneFunkcije #import pomocnih funkcija
import opcenitiCanvas #import opcenitog (abstract) canvasa
###############################################################################
###############################################################################
class Graf(opcenitiCanvas.MPLCanvas):
    """
    Definira detalje crtanja satno agregiranog grafa i pripadne evente
    
    - pamti se samo nekoliko "priavte" membera (stanje grafa, trenutne postavke...)
    
    Bitne metode:
    
    1.crtaj(self, lista)
        - glavna metoda za crtanje grafa
        - lista = [nested dict opcija i kanala, tmin, tmax]
            
    2. on_pick(self, event): odradjuje interakciju sa grafom
        -event je mouseclick.
        -lijevi klik misem prosljedjuje naredbu za crtanje minutnog grafa
        -desni klik misem poteze promjenu flaga
        -middle klik misem iscrtava annotation na grafu
    """
    def __init__(self, *args, **kwargs):
        """konstruktor"""
        opcenitiCanvas.MPLCanvas.__init__(self, *args, **kwargs)
        
        #podrska za kontekstni meni za promjenu flaga (desni klik misem na canvas)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        
        self.data = {} #privremeni spremnik za frejmove (ucitane)

        self.__statusGlavniGraf = False #da li je nacrtan glavni graf
        self.__statusSpanSelector = False #da li je span selector aktivan
        #highlight
        self.__zadnjiHighlightx = None #xpoint zadnjeg highlighta
        self.__zadnjiHighlighty = None #ypoint zadnjeg highlighta
        self.__testHighlight = False #test da li je highligt nacrtan
        #annotation
        self.__zadnjiAnnotationx = None
        self.__testAnnotation = False
        
        #TODO! zoom implementacija
        #definicija raspona granica grafa za zoom
        self.defaultRasponX = self.axes.get_xlim()
        self.defaultRasponY = self.axes.get_ylim()

        
        self.veze()
###############################################################################
    def veze(self):
        """interne veze izmedju elemenata"""
        #veza izmedju klika misa na canvasu i funkcije koja ju odradjuje
        self.mpl_connect('button_press_event', self.on_pick)
        #TODO! zoom implementacija
        self.mpl_connect('scroll_event', self.scroll_zoom)
###############################################################################        
    def set_agregirani_kanal(self, lista):
        """
        BITNA METODA! - mehanizam s kojim se ucitavaju frejmovi za crtanje.
        -metoda crtaj trazi od kontrolera podatke
        -ovo je predvidjeni slot gdje kontroler vraca trazene podatke
        
        metoda postavlja agregirani frejm u self.data
        lista -> [kanal, frejm]
        kanal -> int, ime kanala
        frejm -> pandas dataframe, agregirani podaci
        """
        self.data[lista[0]] = lista[1] 
###############################################################################            
    def highlight_dot(self, x, y):
        """
        Crta zuti dot kao vizualni marker za odabranu tocku (zadnji lijevi
        klik na grafu).
        zorder je postavljen da se crta iznad svega
        """
        if not self.__testHighlight and self.__statusGlavniGraf:
            self.hdot = self.axes.scatter(x, 
                                          y, 
                                          s = 100, 
                                          color = 'yellow', 
                                          alpha = 0.5, 
                                          zorder = 101)
            self.__zadnjiHighlightx = x
            self.__zadnjiHighlighty = y
            self.__testHighlight = True
            self.draw()
###############################################################################
    def crtaj(self, lista):
        """Eksplicitne naredbe za crtanje
        
        ulaz --> lista [dict grafova i opcija, tmin, tmax]
        """
        #promjeni cursor u wait cursor
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.popisGrafova = lista[0]
        self.minVrijeme = lista[1]
        self.maxVrijeme = lista[2]
        
        #clear data, svaki poziv ove metode uvjetuje ponovno povlacenje podataka
        #iz modela. Cilj je dohvatiti zadnje azurne podatke.
        self.data = {}
        
        #y granice pomocnih kanala, defaulti
        self.dGranica = 0
        self.gGranica = 1        
        
        #clear graf
        self.axes.clear()
        #prebaci privatne membere koji prate stanje
        self.__statusGlavniGraf = False #trenutno glavni graf nije nacrtan
        self.__testAnnotation = False #clear ce maknuti i annotatione sa grafa
        
        #podesi granice x osi da su malo sire od podataka da tocke nisu na rubu
        #definiraj granice canvasa, prisiri interval podataka za 60 minuta
        self.xmin, self.xmax = pomocneFunkcije.prosiri_granice_grafa(
            self.minVrijeme, 
            self.maxVrijeme, 
            60)
        #naredba za postavljanje horizontalne granice canvasa
        self.axes.set_xlim(self.xmin, self.xmax)
        
        #definiraj raspon tickova i format x labela
        self.xTickLoc, self.xTickLab = pomocneFunkcije.pronadji_tickove_satni(self.xmin, self.xmax)
        #postavi tickove
        self.axes.set_xticks(self.xTickLoc)
        self.axes.set_xticklabels(self.xTickLab)
        
        #format x kooridinate
        xLabels = self.axes.get_xticklabels()
        for label in xLabels:
            #cilj je lagano zaokrenuti labele da nisu jedan preko drugog
            label.set_rotation(30)
            label.set_fontsize(8)
            

        #test opcenitih postavki priije crtanja:
        #CURSOR
        if self.popisGrafova['ostalo']['opcijesatni']['cursor'] == True:
            self.cursor = Cursor(self.axes, useblit = True, color = 'tomato', linewidth = 1)
        else:
            self.cursor = None
        #MINOR TICKS
        if self.popisGrafova['ostalo']['opcijesatni']['ticks'] == True:
            self.axes.minorticks_on()
        else:
            self.axes.minorticks_off()
        #GRID
        if self.popisGrafova['ostalo']['opcijesatni']['grid'] == True:
            #modificiraj stil grida
            self.axes.grid(True, which = 'major')
        else:
            self.axes.grid(False)
        #SPAN SELECTOR
        if self.popisGrafova['ostalo']['opcijesatni']['span'] == True:
            self.__statusSpanSelector = True
            self.spanSelector = SpanSelector(self.axes, 
                                             self.satni_span_flag, 
                                             direction = 'horizontal', 
                                             useblit = True, 
                                             rectprops = dict(alpha = 0.3, facecolor = 'yellow'))
        else:
            self.spanSelector = None
            self.__statusSpanSelector = False
        
        
        #pronadji sve kanale predvidjene za crtanje te ucitaj podatke u self.data
        kanali = []
        #glavni kanal je jednak za sve u self.popisGrafova['glavniKanal'], uzmi bilo koji graf
        kanali.append(self.popisGrafova['glavniKanal']['validanOK']['kanal'])
        #kreni pretrazivati za kanale po self.popisGrafova['pomocnimKanali']
        for graf in list(self.popisGrafova['pomocniKanali'].keys()):
            kanal = self.popisGrafova['pomocniKanali'][graf]['kanal']
            if kanal not in kanali:
                #izbjegni ponovno upisivanje istog kanala
                kanali.append(kanal)
        #lista kanali sada sadrzi sve kanale koji se trebaju crtati

        #kreni ucitavati podatke u self.data
        for kanal in kanali:
            #zatrazi ciljani frejm od kontrolera
            self.emit(QtCore.SIGNAL('dohvati_agregirani_frejm_kanal(PyQt_PyObject)'), kanal)
        
        #podaci (ciljani frejmovi) su u self.data, ispod su specificne naredbe za crtanje
        """
        glavniKanal sastoji se od 8 razlicitih grafova, detaljnije:
        1. midline 
            -> line plot kroz srednje vrijednosti
            -> samo radi lakseg pracenja vremenskog sljeda podataka
        
        2. validanOK
            -> scatter plot koji prikazuje validirane podatke koji imaju dobar flag
            
        3. validanNOK
            -> scatter plot koji prikazuje validirane podatke koji imaju los flag
            
        4. nevalidanOK
            -> scatter plot koji prikazuje podatke koji su validirani i imaju dobar flag
            
        5. nevalidanNOK
            -> scatter plot koji prikazuje podatke koji nisu validirani i imaju los flag
            
        6. fillsatni
            -> fill_between plot
            -> osjencano podrucje izmedju 2 seta podataka
            -> po defaultu to su 5 i 95 percentil (q05, q95)
        
        7. ekstremimin
            -> scatter plot minimalnih vrijednosti podataka
        
        8. ekstremimax
            -> scatter plot maksimalnih vrijednosti podataka
        """
        #redefinicija kanala, zanima nas sto je stvarno ucitano
        kanali = list(self.data.keys())
        #glavni kanal
        trenutniGlavniKanal = self.popisGrafova['glavniKanal']['validanOK']['kanal']
        #plot naredbe, detaljno cu komentirati prvu, ostale su na slican nacin:
        
        #1. midline
        #provjeri da li je trazeni kanal medju ucitanima (nije nuzno istinito)
        kanal = self.popisGrafova['glavniKanal']['midline']['kanal']
        #provjeri da li je trazeni kanal medju ucitanima (nije nuzno istinito)
        if kanal in kanali:
            #dohvati frejm
            frejm = self.data[kanal]
            #za x vrijednosti postavi indekse frejma, pandas timestampove
            x = list(frejm.index)
            #za y vrijednosti postavi specificni kanal, 'avg', srednje vrijednosti
            y = list(frejm[u'avg'])
            #naredba za plot
            self.axes.plot(x, 
                           y, 
                           linestyle = self.popisGrafova['glavniKanal']['midline']['line'],
                           color = pomocneFunkcije.normalize_rgb(self.popisGrafova['glavniKanal']['midline']['rgb']), 
                           alpha = self.popisGrafova['glavniKanal']['midline']['alpha'],
                           zorder = self.popisGrafova['glavniKanal']['midline']['zorder'],
                           label = self.popisGrafova['glavniKanal']['midline']['label'])
            #zapamti da je glavni graf nacrtan
            self.__statusGlavniGraf = True
            
        #2. validanOK
        kanal = self.popisGrafova['glavniKanal']['validanOK']['kanal']
        if kanal in kanali:
            frejm = self.data[kanal]
            frejm = frejm[frejm[u'flag'] == 1000] #samo dobri flagovi, validirani
            x = list(frejm.index)
            y = list(frejm[u'avg'])
            #"gimnastika" za boju ruba markera
            boja = pomocneFunkcije.normalize_rgb(self.popisGrafova['glavniKanal']['validanOK']['rgb'])
            a = self.popisGrafova['glavniKanal']['validanOK']['alpha']
            #convert rgb to hexcode, then convert hexcode to valid rgba
            hexcolor = matplotlib.colors.rgb2hex(boja)
            edgeBoja = matplotlib.colors.colorConverter.to_rgba(hexcolor, alpha = a)
            self.axes.scatter(x, 
                              y, 
                              marker = self.popisGrafova['glavniKanal']['validanOK']['marker'], 
                              color = edgeBoja, 
                              alpha = a, 
                              zorder = self.popisGrafova['glavniKanal']['validanOK']['zorder'], 
                              label = self.popisGrafova['glavniKanal']['validanOK']['label'], 
                              s = self.popisGrafova['glavniKanal']['validanOK']['markersize'])
            self.__statusGlavniGraf = True

        #3. validanNOK
        kanal = self.popisGrafova['glavniKanal']['validanNOK']['kanal']
        if kanal in kanali:
            frejm = self.data[kanal]
            frejm = frejm[frejm[u'flag'] == -1000] #samo losi flagovi, validirani
            x = list(frejm.index)
            y = list(frejm[u'avg'])
            #"gimnastika" za boju ruba markera
            boja = pomocneFunkcije.normalize_rgb(self.popisGrafova['glavniKanal']['validanNOK']['rgb'])
            a = self.popisGrafova['glavniKanal']['validanNOK']['alpha']
            #convert rgb to hexcode, then convert hexcode to valid rgba
            hexcolor = matplotlib.colors.rgb2hex(boja)
            edgeBoja = matplotlib.colors.colorConverter.to_rgba(hexcolor, alpha = a)
            self.axes.scatter(x, 
                              y, 
                              marker = self.popisGrafova['glavniKanal']['validanNOK']['marker'], 
                              color = edgeBoja, 
                              alpha = a, 
                              zorder = self.popisGrafova['glavniKanal']['validanNOK']['zorder'], 
                              label = self.popisGrafova['glavniKanal']['validanNOK']['label'], 
                              s = self.popisGrafova['glavniKanal']['validanNOK']['markersize'])
            self.__statusGlavniGraf = True

        #4. nevalidanOK
        kanal = self.popisGrafova['glavniKanal']['nevalidanOK']['kanal']
        if kanal in kanali:
            frejm = self.data[kanal]
            frejm = frejm[frejm[u'flag'] == 1] #samo dobri flagovi, nevalidirani
            x = list(frejm.index)
            y = list(frejm[u'avg'])
            #"gimnastika" za boju ruba markera
            boja = pomocneFunkcije.normalize_rgb(self.popisGrafova['glavniKanal']['nevalidanOK']['rgb'])
            a = self.popisGrafova['glavniKanal']['nevalidanOK']['alpha']
            #convert rgb to hexcode, then convert hexcode to valid rgba
            hexcolor = matplotlib.colors.rgb2hex(boja)
            edgeBoja = matplotlib.colors.colorConverter.to_rgba(hexcolor, alpha = a)
            self.axes.scatter(x, 
                              y, 
                              marker = self.popisGrafova['glavniKanal']['nevalidanOK']['marker'], 
                              color = edgeBoja,  
                              alpha = a, 
                              zorder = self.popisGrafova['glavniKanal']['nevalidanOK']['zorder'], 
                              label = self.popisGrafova['glavniKanal']['nevalidanOK']['label'], 
                              s = self.popisGrafova['glavniKanal']['nevalidanOK']['markersize'])
            self.__statusGlavniGraf = True
        
        #5 nevalidanNOK
        kanal = self.popisGrafova['glavniKanal']['nevalidanNOK']['kanal']
        if kanal in kanali:
            frejm = self.data[kanal]
            frejm = frejm[frejm[u'flag'] == -1] #samo losi flagovi, nevalidirani
            x = list(frejm.index)
            y = list(frejm[u'avg'])
            #"gimnastika" za boju ruba markera
            boja = pomocneFunkcije.normalize_rgb(self.popisGrafova['glavniKanal']['nevalidanNOK']['rgb'])
            a = self.popisGrafova['glavniKanal']['nevalidanNOK']['alpha']
            #convert rgb to hexcode, then convert hexcode to valid rgba
            hexcolor = matplotlib.colors.rgb2hex(boja)
            edgeBoja = matplotlib.colors.colorConverter.to_rgba(hexcolor, alpha = a)
            self.axes.scatter(x, 
                              y, 
                              marker = self.popisGrafova['glavniKanal']['nevalidanNOK']['marker'], 
                              color = edgeBoja, 
                              alpha = a, 
                              zorder = self.popisGrafova['glavniKanal']['nevalidanNOK']['zorder'], 
                              label = self.popisGrafova['glavniKanal']['nevalidanNOK']['label'], 
                              s = self.popisGrafova['glavniKanal']['nevalidanNOK']['markersize'])
            self.__statusGlavniGraf = True
            
        #6. fillsatni
        kanal = self.popisGrafova['glavniKanal']['fillsatni']['kanal']
        if self.popisGrafova['glavniKanal']['fillsatni']['crtaj'] == True:
            if kanal in kanali:
                frejm = self.data[kanal]
                x = list(frejm.index)
                y1 = list(frejm[self.popisGrafova['glavniKanal']['fillsatni']['data1']])
                y2 = list(frejm[self.popisGrafova['glavniKanal']['fillsatni']['data2']])
                self.axes.fill_between(x, 
                                       y1, 
                                       y2, 
                                       facecolor = pomocneFunkcije.normalize_rgb(self.popisGrafova['glavniKanal']['fillsatni']['rgb']), 
                                       alpha = self.popisGrafova['glavniKanal']['fillsatni']['alpha'], 
                                       zorder = self.popisGrafova['glavniKanal']['fillsatni']['zorder'])
                self.__statusGlavniGraf = True
        
        #7. ekstremimin
        kanal = self.popisGrafova['glavniKanal']['ekstremimin']['kanal']
        if self.popisGrafova['glavniKanal']['ekstremimin']['crtaj'] == True:
            if kanal in kanali:
                frejm = self.data[kanal]
                x = list(frejm.index)
                y = list(frejm[u'min'])
                #"gimnastika" za boju ruba markera
                boja = pomocneFunkcije.normalize_rgb(self.popisGrafova['glavniKanal']['ekstremimin']['rgb'])
                a = self.popisGrafova['glavniKanal']['ekstremimin']['alpha']
                #convert rgb to hexcode, then convert hexcode to valid rgba
                hexcolor = matplotlib.colors.rgb2hex(boja)
                edgeBoja = matplotlib.colors.colorConverter.to_rgba(hexcolor, alpha = a)
                self.axes.scatter(x, 
                                  y, 
                                  marker = self.popisGrafova['glavniKanal']['ekstremimin']['marker'], 
                                  color = boja, 
                                  alpha = a, 
                                  zorder = self.popisGrafova['glavniKanal']['ekstremimin']['zorder'], 
                                  label = self.popisGrafova['glavniKanal']['ekstremimin']['label'], 
                                  s = self.popisGrafova['glavniKanal']['ekstremimin']['markersize'])
                self.__statusGlavniGraf = True

        #8. ekstremimax
        kanal = self.popisGrafova['glavniKanal']['ekstremimax']['kanal']
        if self.popisGrafova['glavniKanal']['ekstremimax']['crtaj'] == True:
            if kanal in kanali:
                frejm = self.data[kanal]
                x = list(frejm.index)
                y = list(frejm[u'max'])
                #"gimnastika" za boju ruba markera
                boja = pomocneFunkcije.normalize_rgb(self.popisGrafova['glavniKanal']['ekstremimax']['rgb'])
                a = self.popisGrafova['glavniKanal']['ekstremimax']['alpha']
                #convert rgb to hexcode, then convert hexcode to valid rgba
                hexcolor = matplotlib.colors.rgb2hex(boja)
                edgeBoja = matplotlib.colors.colorConverter.to_rgba(hexcolor, alpha = a)
                self.axes.scatter(x, 
                                  y, 
                                  marker = self.popisGrafova['glavniKanal']['ekstremimax']['marker'], 
                                  color = edgeBoja, 
                                  alpha = a, 
                                  zorder = self.popisGrafova['glavniKanal']['ekstremimax']['zorder'], 
                                  label = self.popisGrafova['glavniKanal']['ekstremimax']['label'], 
                                  s = self.popisGrafova['glavniKanal']['ekstremimax']['markersize'])
                self.__statusGlavniGraf = True
        #kraj crtanja glavnog kanala
        
        #crtanje pomocnih kanala:
        for graf in list(self.popisGrafova['pomocniKanali'].keys()):
            kanal = self.popisGrafova['pomocniKanali'][graf]['kanal']
            if kanal in kanali:
                frejm = self.data[kanal]
                x = list(frejm.index)
                y = list(frejm[u'avg']) #samo crtamo srednje vrijednosti
                """
                y granice pomocnih kanala, ekstremi
                """
                najmanji = min(y)
                najveci = max(y)
                if najmanji < self.dGranica:
                    self.dGranica = najmanji
                if najveci > self.gGranica:
                    self.gGranica = najveci
                
                #"gimnastika" za boju ruba markera
                boja = pomocneFunkcije.normalize_rgb(self.popisGrafova['pomocniKanali'][graf]['rgb'])
                a = self.popisGrafova['pomocniKanali'][graf]['alpha']
                #convert rgb to hexcode, then convert hexcode to valid rgba
                hexcolor = matplotlib.colors.rgb2hex(boja)
                edgeBoja = matplotlib.colors.colorConverter.to_rgba(hexcolor, alpha = a)

                self.axes.plot(x, 
                               y, 
                               marker = self.popisGrafova['pomocniKanali'][graf]['marker'], 
                               linestyle = self.popisGrafova['pomocniKanali'][graf]['line'],
                               color = edgeBoja, 
                               alpha = a,
                               zorder = self.popisGrafova['pomocniKanali'][graf]['zorder'],
                               label = self.popisGrafova['pomocniKanali'][graf]['label'], 
                               markersize = self.popisGrafova['pomocniKanali'][graf]['markersize'], 
                               linewidth = self.popisGrafova['pomocniKanali'][graf]['linewidth'])
                              
        #highlight dot
        if self.__statusGlavniGraf:
            self.__testHighlight = False
            trenutniGlavniKanal = self.popisGrafova['glavniKanal']['validanOK']['kanal']
            
            #rubovi indeksa glavnog kanala, treba za pick i span granice
            self.__tmin = self.data[trenutniGlavniKanal].index.min()
            self.__tmax = self.data[trenutniGlavniKanal].index.max()
            
            #odredjivanje x, y granica highlight trocke
            if self.__zadnjiHighlightx in list(self.data[trenutniGlavniKanal].index):
                ypoint = self.data[trenutniGlavniKanal].loc[self.__zadnjiHighlightx, u'avg']
            else:
                miny = self.data[trenutniGlavniKanal][u'min'].min()
                maxy = self.data[trenutniGlavniKanal][u'max'].max()
                ypoint = (miny + maxy)/2
            
            #nacrtaj highlight
            self.highlight_dot(self.__zadnjiHighlightx, ypoint)
        """
        provjera da li je glavni graf uspjesno nacrtan prije odredjivanja
        vertikalnog raspona i legende
        """
        if self.__statusGlavniGraf:
            #odredjivanje vertikalnog raspona grafa
            #glavni kanal
            miny = self.data[trenutniGlavniKanal][u'min'].min()
            maxy = self.data[trenutniGlavniKanal][u'max'].max()
            if miny < self.dGranica:
                self.dGranica = miny
            if maxy > self.gGranica:
                self.gGranica = maxy
                
            self.axes.set_ylim(self.dGranica - 1, self.gGranica + 1)
            
            #prikaz legende na zahtjev
            if self.popisGrafova['ostalo']['opcijesatni']['legend'] == True:
                self.leg = self.axes.legend(loc = 1, fontsize =8, fancybox  = True)
                self.leg.get_frame().set_alpha(0.9)
        else:
            self.axes.clear()
            self.axes.text(0.5, 
                           0.5, 
                           'Nemoguce pristupiti podacima', 
                           horizontalalignment='center', 
                           verticalalignment='center', 
                           fontsize = 8, 
                           transform = self.axes.transAxes)
        
        #TODO! zoom implementacija
        #redefiniraj granice okvira za zoom opciju
        self.defaultRasponX = self.axes.get_xlim()
        self.defaultRasponY = self.axes.get_ylim()
        
        #naredba za crtanje na canvas
        self.draw()
        
        #promjeni cursor u normalan cursor
        QtGui.QApplication.restoreOverrideCursor()
################################################################################
    def on_pick(self, event):
        """
        Metoda odradjuje interakciju sa canvasom. Preuzima event (mouseclick), 
        te ovisno o infomaciji sadrzanom u eventu mjenja flag, stavlja annotation
        ili salje zahtjev za crtanje minutnog grafa i highlighta tocku na grafu.

        -glavni graf mora biti nacrtan
        -event mora biti unutar axesa (prostora za crtanje)
        """
        if self.__statusGlavniGraf and event.inaxes == self.axes:
            #nuzna konverzija x tocke eventa u pandas timestamp
            xpoint = matplotlib.dates.num2date(event.xdata) #datetime.datetime
            #problem.. rounding offset aware i offset naive datetimes..workaround
            xpoint = datetime.datetime(xpoint.year, 
                                       xpoint.month, 
                                       xpoint.day, 
                                       xpoint.hour, 
                                       xpoint.minute, 
                                       xpoint.second)
            #zaokruzi na najblizi puni sat (bitno za podudaranje indeksa u frejmu)
            xpoint = pomocneFunkcije.zaokruzi_vrijeme(xpoint, 3600)
            #aktualna konverzija iz datetime.datetime objekta u pandas.tislib.Timestamp
            xpoint = pd.to_datetime(xpoint)
            #bitno je da zaokruzeno vrijeme nije izvan granica frejma (izbjegavnjanje index errora)
            if xpoint >= self.__tmax:
                xpoint = self.__tmax
            if xpoint <= self.__tmin:
                xpoint = self.__tmin

            #glavni kanal, za sve grafove u 'glavniKanal' kanali su isti, uzmi bilo koji
            trenutniGlavniKanal = self.popisGrafova['glavniKanal']['validanOK']['kanal']
            
            #highlight selected point - kooridinate ako nedostaju podaci
            if xpoint in list(self.data[trenutniGlavniKanal].index):
                ypoint = self.data[trenutniGlavniKanal].loc[xpoint, u'avg']
            else:
                miny = self.data[trenutniGlavniKanal][u'min'].min()
                maxy = self.data[trenutniGlavniKanal][u'max'].max()
                ypoint = (miny + maxy)/2
            
            if event.button == 1:
                #left click
                #test da li je span aktivan
                if self.__statusSpanSelector == False:
                    #signal to draw minute data
                    self.emit(QtCore.SIGNAL('gui_crtaj_minutni_graf(PyQt_PyObject)'), xpoint)
                
                    #highlight choice
                    if self.__testHighlight == False:
                        self.highlight_dot(xpoint, ypoint)
                    else:
                        if self.__zadnjiHighlightx != xpoint:
                            self.hdot.remove()
                            self.__testHighlight = False
                            self.highlight_dot(xpoint, ypoint)

            if event.button == 2:
                #annotations
                #dohvati tekst annotationa
                if xpoint in list(self.data[trenutniGlavniKanal].index):
                    yavg = self.data[trenutniGlavniKanal].loc[xpoint, u'avg']
                    ymin = self.data[trenutniGlavniKanal].loc[xpoint, u'min']
                    ymax = self.data[trenutniGlavniKanal].loc[xpoint, u'max']
                    ystatus = self.data[trenutniGlavniKanal].loc[xpoint, u'status']
                    ycount = self.data[trenutniGlavniKanal].loc[xpoint, u'count']
                
                    tekst = 'Vrijeme: '+str(xpoint)+'\nAverage: '+str(yavg)+'\nMin:'+str(ymin)+'\nMax:'+str(ymax)+'\nStatus:'+str(ystatus)+'\nCount:'+str(ycount)
                else:
                    tekst = 'Vrijeme: '+str(xpoint)+'\nNema podataka'
                
                #annotation offset
                size = self.frameSize()
                x, y = size.width(), size.height()
                x = x//2
                y= y//2
                clickedx = event.x
                clickedy = event.y
            
                if clickedx >= x:
                    clickedx = -80
                    if clickedy >= y:
                        clickedy = -30
                    else:
                        clickedy = 30
                else:
                    clickedx = 30
                    if clickedy >= y:
                        clickedy = -30
                    else:
                        clickedy = 30
                
                if self.__testAnnotation == False:
                    #napravi annotation
                    self.__zadnjiAnnotationx = xpoint
                    self.__testAnnotation = True
                    #sami annotation, zorder 102, garancija da je iznad svega
                    self.annotation = self.axes.annotate(
                        tekst, 
                        xy = (xpoint, ypoint), 
                        xytext = (clickedx, clickedy), 
                        textcoords = 'offset points', 
                        ha = 'left', 
                        va = 'center', 
                        fontsize = 7, 
                        zorder = 102, 
                        bbox = dict(boxstyle = 'square', fc = 'cyan', alpha = 0.7), 
                        arrowprops = dict(arrowstyle = '->'))
                    self.draw()
                    
                else:
                    if xpoint == self.__zadnjiAnnotationx:
                        self.annotation.remove()
                        self.__zadnjiAnnotationx = None
                        self.__testAnnotation = False
                        self.draw()
                    else:
                        self.annotation.remove()
                        self.__zadnjiAnnotationx = xpoint
                        self.__testAnnotation = True
                        self.annotation = self.axes.annotate(
                            tekst, 
                            xy = (xpoint, ypoint), 
                            xytext = (clickedx, clickedy), 
                            textcoords = 'offset points', 
                            ha = 'left', 
                            va = 'center', 
                            fontsize = 7, 
                            zorder = 102, 
                            bbox = dict(boxstyle = 'square', fc = 'cyan', alpha = 0.7), 
                            arrowprops = dict(arrowstyle = '->'))
                        self.draw()
            
            if event.button == 3:
                #flag change
                #poziva context menu sa informacijom o lokaciji i satu
                loc = QtGui.QCursor.pos() #lokacija klika
                self.show_menu(loc, xpoint, xpoint) #interval koji treba promjeniti
###############################################################################
    def show_menu(self, pos, tmin, tmax):
        """
        Metoda iscrtava kontekstualni meni tjekom desnog klika (ili
        prilikom selektiranja sa spanom)
        """
        #zapamti rubna vremena intervala, trebati ce za druge metode
        self.__lastTimeMin = tmin
        self.__lastTimeMax = tmax
        #definiraj menu i postavi akcije u njega
        menu = QtGui.QMenu(self)
        menu.setTitle('Promjeni flag')
        action1 = QtGui.QAction("Validiran podatak, flag: dobar", menu)
        action2 = QtGui.QAction("Validiran podatak, flag: los", menu)
        action3 = QtGui.QAction("Sirov podatak, flag: dobar", menu)
        action4 = QtGui.QAction("Sirov podatak, flag: los", menu)
        menu.addAction(action1)
        menu.addAction(action2)
        menu.addAction(action3)
        menu.addAction(action4)
        #povezi akcije menua sa metodama
        action1.triggered.connect(functools.partial(self.promjena_flaga, tip = 1000))
        action2.triggered.connect(functools.partial(self.promjena_flaga, tip = -1000))
        action3.triggered.connect(functools.partial(self.promjena_flaga, tip = 1))
        action4.triggered.connect(functools.partial(self.promjena_flaga, tip = -1))
        
        #prikazi menu na definiranoj tocki grafa
        menu.popup(pos)
###############################################################################    
    def promjena_flaga(self, tip = None):
        """
        Metoda sluzi za promjenu flaga ili stanja validiranosti podataka
        ovisno o keyword argumentu tip.
        """
        #dohvati rubove intervala (spremljeni su u membere prilikom poziva dijaloga)
        tmin = self.__lastTimeMin
        tmax = self.__lastTimeMax
        #pomak slicea da uhvati sve ciljane minutne podatke
        tmin = tmin - timedelta(minutes = 59)
        tmin = pd.to_datetime(tmin)
        #dohvati glavni kanal
        glavniKanal = self.popisGrafova['glavniKanal']['validanOK']['kanal']
        #pakiranje zahtjeva u listu [tmin, tmax, flag, kanal] ovisno o tipu
        if tip != None:
            arg = [tmin, tmax, tip, glavniKanal]
            #generalni emit za promjenu flaga
            self.emit(QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), arg)
###############################################################################
    def satni_span_flag(self, tmin, tmax):
        """
        Metoda je povezana sa span selektorom (ako je inicijaliziran).
        Metoda je zaduzena da prikaze kontekstni dijalog za promjenu flaga
        na mjestu gdje "releasamo" ljevi klik.
        
        tmin i tmax su timestampovi, ali ih treba adaptirati
        """
        if self.__statusGlavniGraf: #glavni graf mora biti nacrtan
            #konverzija ulaznih vrijednosti u pandas timestampove
            tmin = matplotlib.dates.num2date(tmin)
            tmax = matplotlib.dates.num2date(tmax)
            tmin = datetime.datetime(tmin.year, tmin.month, tmin.day, tmin.hour, tmin.minute, tmin.second)
            tmax = datetime.datetime(tmax.year, tmax.month, tmax.day, tmax.hour, tmax.minute, tmax.second)
            #vremena se zaokruzuju na najblizi sat
            tmin = pomocneFunkcije.zaokruzi_vrijeme(tmin, 3600)
            tmax = pomocneFunkcije.zaokruzi_vrijeme(tmax, 3600)
            tmin = pd.to_datetime(tmin)
            tmax = pd.to_datetime(tmax)
    
            #osiguranje da se ne preskoce granice glavnog kanala (izbjegavanje index errora)
            if tmin < self.__tmin:
                tmin = self.__tmin
            if tmin > self.__tmax:
                tmin = self.__tmax
            if tmax < self.__tmin:
                tmax = self.__tmin
            if tmax > self.__tmax:
                tmax = self.__tmax
                        
            #tocke ne smiju biti iste (izbjegavamo paljenje dijaloga na ljevi klik)
            #zoom, pan opcije na toolbaru moraju biti "off"
            if tmin != tmax:
                #pozovi dijalog za promjenu flaga
                loc = QtGui.QCursor.pos()
                self.show_menu(loc, tmin, tmax)
###############################################################################
    #TODO! zoom implementacija
    def scroll_zoom(self, event):
        """
        Implementacija zooma uz pomoc scroll gumba.
        
        scroll up   --> zoom in
        scroll down --> zoom out
        
        Zoom je centriran okolo pozicije misa kada se scrolla. ta tocka ce uvijek
        ostati tamo gdje je i bila, samo ce se skala pomaknuti za predefinirani
        faktor povecanja.
        
        BITNO JE NAPOMENUTI! zoom samo redefinira granice koje se prikazuju
        """
        #zanemari ako je cursor izvan canvasa
        if event.inaxes:
            #nadji trenutni raspon x i y osi
            xRaspon = self.axes.get_xlim()
            yRaspon = self.axes.get_ylim()
            #nadji tocku iznad koje je aktiviran scroll_event
            trenutniX = event.xdata
            trenutniY = event.ydata
            #definiraj povecanje zooma, gradacija zooma
            faktorPovecanja = 1.5
            #odredi novu skalu (raspon) ovisno o smjeru scrolla
            if event.button == 'down':
                #zoom out
                skala = faktorPovecanja
            elif event.button == 'up':
                #zoom in
                skala = 1.0 / faktorPovecanja
            else:
                """
                potencijalni visak, ali za svaki slucaj da event.button ne bude
                'up' ili 'down' vec nesto trece.
                """
                #tj. nemoj niti povecati niti smanjiti raspon x i y osi
                skala = 1
            
            if self.__statusGlavniGraf:
                #nova duljina / raspon skale xmax-xmin
                lenNoviX = (xRaspon[1] - xRaspon[0]) * skala
                lenNoviY = (yRaspon[1] - yRaspon[0]) * skala
            
                #relativni polozaj tocke od koje radimo zoom
                relPosX = (xRaspon[1] - trenutniX) / (xRaspon[1] - xRaspon[0])
                relPosY = (yRaspon[1] - trenutniY) / (yRaspon[1] - yRaspon[0])
                
                #racunanje novih x granica grafa
                xmin = trenutniX - lenNoviX * (1 - relPosX)
                xmax = trenutniX + lenNoviX * relPosX
            
                #racunanje novih y granica grafa
                ymin = trenutniY - lenNoviY * (1 - relPosY)
                ymax = trenutniY + lenNoviY * relPosY
            
                #onemoguci zoom out izvan granica originalnog grafa
                if self.defaultRasponX[0] > xmin:
                    xmin = self.defaultRasponX[0]
                if self.defaultRasponX[1] < xmax:
                    xmax = self.defaultRasponX[1]
                if self.defaultRasponY[0] > ymin:
                    ymin = self.defaultRasponY[0]
                if self.defaultRasponY[1] < ymax:
                    ymax = self.defaultRasponY[1]
            
                #postavi nove granice
                self.axes.set_xlim([xmin, xmax])
                self.axes.set_ylim([ymin, ymax])
                
                #prikazi promjenu
                self.draw()
###############################################################################
###############################################################################