# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 13:14:26 2014

@author: User

Klasa (canvas) za prikaz minutnih vrijednosti.
"""

from PyQt4 import QtGui, QtCore
import datetime
import matplotlib
import functools
from matplotlib.widgets import SpanSelector, Cursor

import pandas as pd
import numpy as np

import pomocneFunkcije #import pomocnih funkcija
import opcenitiCanvas #import opcenitog (abstract) canvasa

###############################################################################
###############################################################################
class Graf(opcenitiCanvas.MPLCanvas):
    """
    Definira detalje crtanja minutnog grafa i pripadne evente
    
    - pamti se samo nekoliko "priavte" membera (stanje grafa, trenutne postavke...)
    
    Bitne metode:
    1. crtaj(self, lista) : glavna naredba za crtanje
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
        
        #podrska za kontekstni meni za promjenu flaga
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)      

        self.data = {} #spremnik za frejmove (ucitane)
        self.infoMapa = {} #spremnik sa info podacima o kanalima

        self.__statusGlavniGraf = False #da li je nacrtan glavni graf
        self.__statusSpanSelector = False #da li je span selector aktivan
        #annotation
        self.__zadnjiAnnotationx = None
        self.__testAnnotation = False

        #TODO! zoom implementacija
        #definicija raspona granica grafa za zoom
        self.defaultRasponX = self.axes.get_xlim()
        self.defaultRasponY = self.axes.get_ylim()

        #rastegni canvas udesno
        self.axes.figure.subplots_adjust(right = 0.98)

        self.veze()        
###############################################################################
    def veze(self):
        """interne veze izmedju elemenata"""
        #veza izmedju klika misa na canvasu i funkcije koja ju odradjuje
        self.mpl_connect('button_press_event', self.on_pick)
        #TODO! zoom implementacija
        self.mpl_connect('scroll_event', self.scroll_zoom)
###############################################################################
    def set_minutni_kanal(self, lista):
        """
        BITNA METODA! - mehanizam s kojim se ucitavaju frejmovi za crtanje.
        -metoda crtaj trazi od kontrolera podatke
        -ovo je predvidjeni slot gdje kontroler vraca trazene podatke
        
        metoda postavlja frejm minutnih podataka u self.__data
        lista -> [kanal, frejm, dict]
        kanal -> int, ime kanala
        frejm -> pandas dataframe, minutni podaci
        dict -> dict sa opisom kanala, sadrzi naziv, formulu, mjernu jedinicu, postaju
        """
        self.data[lista[0]] = lista[1]
        self.infoMapa[lista[0]] = lista[2]
###############################################################################
    def crtaj(self, lista):
        """Eksplicitne naredbe za crtanje zadane sa popisom grafova i vremenskim
        intervalom.
        
        ulaz je lista
        lista[0] - nested dict grafova za crtanje sa postavkama
        lista[1] - donja granica vremenskog intervala
        lista[2] - gornja granica vremenskog intervala
        """
        #TODO!
        #nije testirano do kraja, potencijali problemi sa praznim frejmovima ili
        #nedostatkom frejma

        #promjeni cursor u wait cursor
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

        #clear data, svaki poziv ove metode uvjetuje ponovno povlacenje podataka
        #iz modela. Cilj je dohvatiti zadnje azurne podatke.
        self.data = {}
        
        #informacije za crtanje, vremenski span i informacije o grafovima
        self.popisGrafova = lista[0]
        self.minVrijeme = lista[1]
        self.maxVrijeme = lista[2]

        #y granice pomocnih kanala, defaulti
        self.dGranica = 0
        self.gGranica = 1        

        #clear graf
        self.axes.clear()
        #prebaci privatne membere koji prate stanje
        self.__statusGlavniGraf = False #trenutno glavni graf nije nacrtan
        self.__testAnnotation = False #clear ce maknuti i annotatione sa grafa
        
        #definiraj x granice canvasa, prosiri lagano interval da tocke nisu na rubu
        self.xmin, self.xmax = pomocneFunkcije.prosiri_granice_grafa(
            self.minVrijeme, 
            self.maxVrijeme, 
            5)

        self.axes.set_xlim(self.xmin, self.xmax)
        
        #sredi tick labele i tick positioning
        self.xMtickLoc, self.xMTickLab, self.xTickLoc = pomocneFunkcije.pronadji_tickove_minutni(self.xmin, self.xmax)
        self.axes.set_xticks(self.xMtickLoc)
        self.axes.set_xticklabels(self.xMTickLab)
        
        #format x kooridinate
        xLabels = self.axes.get_xticklabels()
        for label in xLabels:
            #lagana rotacija i promjena fonta
            label.set_rotation(30)
            label.set_fontsize(8)

        #test opcenitih postavki priije crtanja:
        #CURSOR
        if self.popisGrafova['ostalo']['opcijeminutni']['cursor'] == True:
            self.cursor = Cursor(self.axes, useblit = True, color = 'tomato', linewidth = 1)
        else:
            self.cursor = None
        #MINOR TICKS
        if self.popisGrafova['ostalo']['opcijeminutni']['ticks'] == True:
            self.axes.set_xticks(self.xTickLoc, minor = True)
            #self.axes.minorticks_on()
        else:
            self.axes.minorticks_off()
        #GRID
        if self.popisGrafova['ostalo']['opcijeminutni']['grid'] == True:
            self.axes.grid(True, which = 'major', linewidth = 0.5, linestyle = '-')
            self.axes.grid(True, which = 'minor', linewidth = 0.5)
        else:
            self.axes.grid(False)
        #SPAN SELECTOR
        if self.popisGrafova['ostalo']['opcijeminutni']['span'] == True:
            self.__statusSpanSelector = True
            self.spanSelector = SpanSelector(self.axes, 
                                             self.minutni_span_flag, 
                                             direction = 'horizontal', 
                                             useblit = True, 
                                             rectprops = dict(alpha = 0.3, facecolor = 'yellow'))
        else:
            self.spanSelector = None
            self.__statusSpanSelector = False

        #pronadji sve kanale predvidjene za crtanje te ucitaj podatke u self.data
        kanali = []
        #glavni kanal je jednak za sve u self.__opcije['glavniKanal'], uzmi bilo koji graf
        kanali.append(self.popisGrafova['glavniKanal']['validanOK']['kanal'])
        #kreni pretrazivati za kanale po pomocnim kanalima
        for graf in list(self.popisGrafova['pomocniKanali'].keys()):
            kanal = self.popisGrafova['pomocniKanali'][graf]['kanal']
            if kanal not in kanali:
                #izbjegni ponovno upisivanje istog kanala
                kanali.append(kanal)
        #lista kanali sada sadrzi sve kanale koji se trebaju crtati
        #kreni ucitavati podatke u self.data
        for kanal in kanali:
            #zatrazi ciljani frejm od kontrolera
            self.emit(QtCore.SIGNAL('dohvati_minutni_frejm_kanal(PyQt_PyObject)'), [kanal, self.minVrijeme, self.maxVrijeme])
        
        #podaci su u self.data, ispod su specificne naredbe za crtanje
        """
        glavniKanal sastoji se od 8 razlicitih grafova, ali samo treba
        nacrtati 5. Ekstremi i fill ne postoje kao opcija. Crta se samo
        koncentracija. detaljnije:
        
        1. midline 
            -> line plot kroz koncentracije
            -> samo radi lakseg pracenja vremenskog sljeda podataka
        
        2. validanOK
            -> scatter plot koji prikazuje validirane podatke koji imaju dobar flag
            
        3. validanNOK
            -> scatter plot koji prikazuje validirane podatke koji imaju los flag
            
        4. nevalidanOK
            -> scatter plot koji prikazuje podatke koji su validirani i imaju dobar flag
            
        5. nevalidanNOK
            -> scatter plot koji prikazuje podatke koji nisu validirani i imaju los flag
        """
        #redefiniramo kanali, zanima nas sto je stvarno ucitano
        kanali = list(self.data.keys())
        #plot naredbe, detaljno cu komentirati prvu, ostale su na slican nacin:        

        #1. midline
        #provjeri da li je trazeni kanal medju ucitanimaself.functools.partial(toggle, tip = 'bleh') (nije nuzno istinito)
        kanal = self.popisGrafova['glavniKanal']['midline']['kanal']
        #provjeri da li je trazeni kanal medju ucitanima (nije nuzno istinito)
        if kanal in kanali:
            #dohvati frejm
            frejm = self.data[kanal]
            #izbaci sve nan koncentracije
            #frejm = frejm[np.isnan(frejm[u'koncentracija'] != True)]
            #za x vrijednosti postavi indekse frejma, pandas timestampove
            x = list(frejm.index)
            #za y vrijednosti postavi specificni kanal, 'avg', srednje vrijednosti
            y = list(frejm[u'koncentracija'])
            """
            y granice glavnog kanala, ekstremi
            """
            najmanji = min(y)
            najveci = max(y)
            if najmanji < self.dGranica:
                self.dGranica = najmanji
            if najveci > self.gGranica:
                self.gGranica = najveci

            #naredba za plot
            self.axes.plot(x, 
                           y, 
                           linewidth = self.popisGrafova['glavniKanal']['midline']['linewidth'], 
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
            #frejm = frejm[np.isnan(frejm[u'koncentracija'] != True)] #izbaci sve nan koncentracije
            frejm = frejm[frejm[u'flag'] == 1000] #samo dobri flagovi, validirani
            x = list(frejm.index)
            y = list(frejm[u'koncentracija'])
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
            frejm= self.data[kanal]
            #frejm = frejm[np.isnan(frejm[u'koncentracija'] != True)] #izbaci sve nan koncentracije
            frejm = frejm[frejm[u'flag'] == -1000] #samo losi flagovi, validirani
            x = list(frejm.index)
            y = list(frejm[u'koncentracija'])
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
            #frejm = frejm[np.isnan(frejm[u'koncentracija'] != True)] #izbaci sve nan koncentracije
            frejm = frejm[frejm[u'flag'] >= 0] #samo dobri flagovi
            frejm = frejm[frejm[u'flag'] != 1000] #uzmi sve nevalidirane
            x = list(frejm.index)
            y = list(frejm[u'koncentracija'])
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
            #frejm = frejm[np.isnan(frejm[u'koncentracija'] != True)] #izbaci sve nan koncentracije
            frejm = frejm[frejm[u'flag'] < 0] #samo losi flagovi
            frejm = frejm[frejm[u'flag'] != -1000] #uzmi sve nevalidirane
            x = list(frejm.index)
            y = list(frejm[u'koncentracija'])
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
        #kraj crtanja glavnog kanala
        
        #crtanje pomocnih kanala:
        for graf in list(self.popisGrafova['pomocniKanali'].keys()):
            kanal = self.popisGrafova['pomocniKanali'][graf]['kanal']
            if kanal in kanali:
                frejm = self.data[kanal]
                #frejm = frejm[np.isnan(frejm[u'koncentracija'] != True)] #izbaci sve nan koncentracije
                x = list(frejm.index)
                y = list(frejm[u'koncentracija']) #samo crtamo srednje vrijednosti
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

                              
        if self.__statusGlavniGraf:
            trenutniGlavniKanal = self.popisGrafova['glavniKanal']['validanOK']['kanal']
            #rubovi indeksa glavnog kanala, treba za pick i span granice
            self.__tmin = self.data[trenutniGlavniKanal].index.min()
            self.__tmax = self.data[trenutniGlavniKanal].index.max()

        """
        provjera da li je glavni graf uspjesno nacrtan prije odredjivanja
        vertikalnog raspona i legende
        """
        if self.__statusGlavniGraf:            
            #odredjivanje vertikalnog raspona grafa
            miny = self.data[trenutniGlavniKanal][u'koncentracija'].min()
            maxy = self.data[trenutniGlavniKanal][u'koncentracija'].max()
    
            if miny < self.dGranica:
                self.dGranica = miny
            if maxy > self.gGranica:
                self.gGranica = maxy
            
            self.axes.set_ylim(self.dGranica - 1, self.gGranica + 1)
    
            #prikaz legende na zahtjev
            if self.popisGrafova['ostalo']['opcijeminutni']['legend'] == True:
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

        #TODO! zapamti max granice grafa za full zoom out!
        self.xlim_original = (self.xmin, self.xmax)
        self.ylim_original = self.axes.get_ylim()
        
        #promjeni cursor u normalan cursor
        QtGui.QApplication.restoreOverrideCursor()
###############################################################################
    def minutni_span_flag(self, tmin, tmax):
        """
        Metoda je povezana sa span selektorom (ako je inicijaliziran).
        Metoda je zaduzena da prikaze kontekstni dijalog za promjenu flaga
        na mjestu gdje "releasamo" ljevi klik.
        
        tmin i tmax su timestampovi, ali ih treba adaptirati
        """
        if self.MODEPICK:
            if self.__statusGlavniGraf: #glavni graf mora biti nacrtan
                #konverzija ulaznih vrijednosti u pandas timestampove
                tmin = matplotlib.dates.num2date(tmin)
                tmax = matplotlib.dates.num2date(tmax)
                tmin = datetime.datetime(tmin.year, tmin.month, tmin.day, tmin.hour, tmin.minute, tmin.second)
                tmax = datetime.datetime(tmax.year, tmax.month, tmax.day, tmax.hour, tmax.minute, tmax.second)
                #vremena se zaokruzuju na najblizu minutu (60 sekundi)
                tmin = pomocneFunkcije.zaokruzi_vrijeme(tmin, 60)
                tmax = pomocneFunkcije.zaokruzi_vrijeme(tmax, 60)
                tmin = pd.to_datetime(tmin)
                tmax = pd.to_datetime(tmax)
        
                #osiguranje da se ne preskoce granice glavnog kanala
                if tmin < self.__tmin:
                    tmin = self.__tmin
                if tmin > self.__tmax:
                    tmin = self.__tmax
                if tmax < self.__tmin:
                    tmax = self.__tmin
                if tmax > self.__tmax:
                    tmax = self.__tmax
                
                #tocke ne smiju biti iste (izbjegavamo paljenje dijaloga na ljevi klik)
                if tmin != tmax:
                    #pozovi dijalog za promjenu flaga
                    loc = QtGui.QCursor.pos()
                    self.show_menu(loc, tmin, tmax)
###############################################################################
    def show_menu(self, pos, tmin, tmax):
        """
        Metoda iscrtava kontekstualni meni tjekom desnog klika (ili
        prilikom selektiranja sa spanom) na poziciji pos.
        """
        #zapamti rubna vremena intervala, trebati ce za druge metode
        self.__lastTimeMin = tmin
        self.__lastTimeMax = tmax
        #definiraj menu i postavi akcije u njega
        menu = QtGui.QMenu(self)
        menu.setTitle('Promjeni flag')
        action1 = QtGui.QAction("Flag: dobar", menu)
        action2 = QtGui.QAction("Flag: los", menu)
        menu.addAction(action1)
        menu.addAction(action2)
        #povezi akcije menua sa metodama
        action1.triggered.connect(functools.partial(self.promjena_flaga, tip = 1000))
        action2.triggered.connect(functools.partial(self.promjena_flaga, tip = -1000))
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
        #dohvati glavni kanal
        glavniKanal = self.popisGrafova['glavniKanal']['validanOK']['kanal']
        #pakiranje zahtjeva u listu [tmin, tmax, flag, kanal] ovisno o tipu
        if tip != None:
            arg = [tmin, tmax, tip, glavniKanal]
            #generalni emit za promjenu flaga
            self.emit(QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), arg)
################################################################################    
    def on_pick(self, event):
        """
        Metoda odradjuje interakciju sa canvasom. Preuzima event (mouseclick), 
        te ovisno o infomaciji sadrzanom u eventu mjenja flag, stavlja annotation.
        
        -glavni graf mora biti nacrtan
        -event mora biti unutar axesa (prostora za crtanje)
        -desni klik pokrece context manager za promjenu flaga
        -middle mouse klik pokazuje tj. brise annotation
        """
        if self.MODEPICK:
            #picker za podatke, annotations etc...
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
                xpoint = pomocneFunkcije.zaokruzi_vrijeme(xpoint, 60)
                #aktualna konverzija iz datetime.datetime objekta u pandas.tislib.Timestamp
                xpoint = pd.to_datetime(xpoint)
                #bitno je da zaokruzeno vrijeme nije izvan granica frejma (izbjegavnjanje index errora)
                if xpoint >= self.__tmax:
                    xpoint = self.__tmax
                if xpoint <= self.__tmin:
                    xpoint = self.__tmin
    
                #glavni kanal
                gkanal = self.popisGrafova['glavniKanal']['validanOK']['kanal']
    
                if xpoint in list(self.data[gkanal].index):
                    ypoint = self.data[gkanal].loc[xpoint, u'koncentracija']
                    if np.isnan(ypoint): #potencijalo za taj index konc = np.NaN
                        miny = self.data[gkanal][u'koncentracija'].min()
                        maxy = self.data[gkanal][u'koncentracija'].max()
                        ypoint = (miny + maxy)/2                    
                else:
                    miny = self.data[gkanal][u'koncentracija'].min()
                    maxy = self.data[gkanal][u'koncentracija'].max()
                    ypoint = (miny + maxy)/2
    
                if event.button == 2:
                    #annotations
                    #dohvati tekst annotationa
                    if xpoint in list(self.data[gkanal].index):
                        konc = self.data[gkanal].loc[xpoint, u'koncentracija']
                        status = self.data[gkanal].loc[xpoint, u'status']
                        flag = self.data[gkanal].loc[xpoint, u'flag']
                        tekst = 'Vrijeme: '+str(xpoint)+'\nKonc.: '+str(konc)+'\nStatus: '+str(status)+'\nFlag: '+str(flag)
                    else:
                        tekst = 'Vrijeme: '+str(xpoint)+'\nNema podatka'
    
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
    def clear_minutni(self):
        """
        clear minutnog grafa, reset na defaultne postavke
        """
        #podrska za kontekstni meni za promjenu flaga
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)      

        self.data = {} #spremnik za frejmove (ucitane)
        self.__statusGlavniGraf = False #da li je nacrtan glavni graf
        self.__statusSpanSelector = False #da li je span selector aktivan
        #annotation
        self.__zadnjiAnnotationx = None
        self.__testAnnotation = False
        
        self.axes.clear()
        self.draw()
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