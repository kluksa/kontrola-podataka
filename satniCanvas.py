# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 08:38:40 2014

@author: User

Klasa (canvas) za prikaz satno agregiranih vrijednosti.
"""
from PyQt4 import QtGui, QtCore

import matplotlib
from matplotlib.widgets import SpanSelector, Cursor

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
    
    1. crtaj(self, mapaGrafova, infoFrejmovi) : glavna naredba za crtanje.
        - mapaGrafova -> mapa (dict) sa opcijama grafova (dict sa 
        informacijom o glavnom kanalu, pomocnim kanalima, opcijama).
        Tu je sadrzana informacija kako graf treba izgledati te sto ce biti nacrtano.
        
        -infoFrejmovi -> izvor podataka, lista. [stanica, tMin, tMax, [lista kanala]]
        Tu je sadrzana informacija s kojom se moze pristupiti podacima.
        
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
        
        self.__opcije = None #dict opcija grafa
        self.__data = {} #spremnik za frejmove (ucitane)
        self.__info = None #info o dostupnim frejmovima
        self.__statusGlavniGraf = False #da li je nacrtan glavni graf
        self.__statusSpanSelector = False #da li je span selector aktivan
        #highlight
        self.__zadnjiHighlightx = None #xpoint zadnjeg highlighta
        self.__zadnjiHighlighty = None #ypoint zadnjeg highlighta
        self.__testHighlight = False #test da li je highligt nacrtan
        #annotation
        self.__zadnjiAnnotationx = None
        self.__testAnnotation = False
        
        self.veze()
###############################################################################
    def veze(self):
        """interne veze izmedju elemenata"""
        #veza izmedju klika misa na canvasu i funkcije koja ju odradjuje
        self.mpl_connect('button_press_event', self.on_pick)
###############################################################################        
    def set_agregirani_kanal(self, lista):
        """
        BITNA METODA! - mehanizam s kojim se ucitavaju frejmovi za crtanje.
        -metoda crtaj trazi od kontrolera podatke
        -ovo je predvidjeni slot gdje kontroler vraca trazene podatke
        
        metoda postavlja agregirani frejm u self.__data
        lista -> [kanal, frejm]
        kanal -> string, ime kanala
        frejm -> pandas dataframe, agregirani podaci
        """
        self.__data[lista[0]] = lista[1]        
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
    def crtaj(self, mapaGrafova, infoFrejmovi):
        """Eksplicitne naredbe za crtanje
        
        ulaz:
        mapaGrafova -> defaultni dict sa opcijama grafova
        infoFrejmovi -> izvor podataka [stanica, tMin, tMax, [lista kanala]]
        """
        #promjeni cursor u wait cursor
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        #spremi ulazne parametre u privatne membere
        self.__opcije = mapaGrafova
        self.__info = infoFrejmovi
        #clear data, svaki poziv ove metode uvjetuje ponovno povlacenje podataka
        #iz modela. Cilj je dohvatiti zadnje azurne podatke.
        self.__data = {}
        
        #clear graf
        self.axes.clear()
        #prebaci privatne membere koji prate stanje
        self.__statusGlavniGraf = False #trenutno glavni graf nije nacrtan
        self.__testAnnotation = False #clear ce maknuti i annotatione sa grafa
        
        #podesi granice x osi da su malo sire od podataka da tocke nisu na rubu
        if self.__info != None:
            #definiraj granice canvasa, prisiri interval podataka za 60 minuta
            self.xmin, self.xmax = pomocneFunkcije.prosiri_granice_grafa(
                self.__info[1], 
                self.__info[2], 
                60)
            #naredba za postavljanje horizontalne granice canvasa
            self.axes.set_xlim(self.xmin, self.xmax)
        
        #format x kooridinate
        xLabels = self.axes.get_xticklabels()
        for label in xLabels:
            #cilj je lagano zaokrenuti labele da nisu jedan preko drugog
            label.set_rotation(20)
            label.set_fontsize(8)

        #test opcenitih postavki priije crtanja:
        #CURSOR
        if self.__opcije['ostalo']['opcijesatni']['cursor'] == True:
            self.cursor = Cursor(self.axes, useblit = True, color = 'tomato', linewidth = 1)
        else:
            self.cursor = None
        #GRID
        if self.__opcije['ostalo']['opcijesatni']['grid'] == True:
            self.axes.grid(True)
        else:
            self.axes.grid(False)
        #MINOR TICKS
        if self.__opcije['ostalo']['opcijesatni']['ticks'] == True:
            self.axes.minorticks_on()
        else:
            self.axes.minorticks_off()
        #SPAN SELECTOR
        if self.__opcije['ostalo']['opcijesatni']['span'] == True:
            self.__statusSpanSelector = True
            self.spanSelector = SpanSelector(self.axes, 
                                             self.satni_span_flag, 
                                             direction = 'horizontal', 
                                             useblit = True, 
                                             rectprops = dict(alpha = 0.3, facecolor = 'yellow'))
        else:
            self.spanSelector = None
            self.__statusSpanSelector = False
        
        
        #pronadji sve kanale predvidjene za crtanje te ucitaj podatke u self.__data
        kanali = []
        #glavni kanal je jednak za sve u self.__opcije['glavniKanal'], uzmi bilo koji graf
        kanali.append(self.__opcije['glavniKanal']['validanOK']['kanal'])
        #kreni pretrazivati za kanale po self.__info['pomocnimKanali']
        for graf in list(self.__opcije['pomocniKanali'].keys()):
            kanal = self.__opcije['pomocniKanali'][graf]['kanal']
            if kanal not in kanali:
                #izbjegni ponovno upisivanje istog kanala
                kanali.append(kanal)
        #lista kanali sada sadrzi sve kanale koji se trebaju crtati
        #kreni ucitavati podatke u self.__data
        for kanal in kanali:
            if kanal in self.__info[3]: #ako je kanal dostupan dokumentu
                #pripremi zahtjev za dohvacanje podataka [stanica, tmin, tmax, kanal]
                msg = [self.__info[0], self.__info[1], self.__info[2], kanal]
                #zatrazi ciljani frejm od kontrolera
                self.emit(QtCore.SIGNAL('dohvati_agregirani_frejm_kanal(PyQt_PyObject)'), msg)
        
        #podaci su u self.__data, ispod su specificne naredbe za crtanje
        
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
        kanali = list(self.__data.keys())
        #plot naredbe, detaljno cu komentirati prvu, ostale su na slican nacin:
        
        #1. midline
        #provjeri da li je trazeni kanal medju ucitanima (nije nuzno istinito)
        kanal = self.__opcije['glavniKanal']['midline']['kanal']
        #provjeri da li je trazeni kanal medju ucitanima (nije nuzno istinito)
        if kanal in kanali:
            #dohvati frejm
            data = self.__data[kanal]
            #za x vrijednosti postavi indekse frejma, pandas timestampove
            x = list(data.index)
            #za y vrijednosti postavi specificni kanal, 'avg', srednje vrijednosti
            y = list(data[u'avg'])
            #naredba za plot
            self.axes.plot(x, 
                           y, 
                           linestyle = self.__opcije['glavniKanal']['midline']['line'],
                           color = pomocneFunkcije.normalize_rgb(self.__opcije['glavniKanal']['midline']['rgb']), 
                           alpha = self.__opcije['glavniKanal']['midline']['alpha'],
                           zorder = self.__opcije['glavniKanal']['midline']['zorder'],
                           label = self.__opcije['glavniKanal']['midline']['label'])
            #zapamti da je glavni graf nacrtan
            self.__statusGlavniGraf = True
            
        #2. validanOK
        kanal = self.__opcije['glavniKanal']['validanOK']['kanal']
        if kanal in kanali:
            data = self.__data[kanal]
            data = data[data[u'flag'] == 1000] #samo dobri flagovi, validirani
            x = list(data.index)
            y = list(data[u'avg'])
            self.axes.scatter(x, 
                              y, 
                              marker = self.__opcije['glavniKanal']['validanOK']['marker'], 
                              color = pomocneFunkcije.normalize_rgb(self.__opcije['glavniKanal']['validanOK']['rgb']), 
                              alpha = self.__opcije['glavniKanal']['validanOK']['alpha'], 
                              zorder = self.__opcije['glavniKanal']['validanOK']['zorder'], 
                              label = self.__opcije['glavniKanal']['validanOK']['label'])
            self.__statusGlavniGraf = True

        #3. validanNOK
        kanal = self.__opcije['glavniKanal']['validanNOK']['kanal']
        if kanal in kanali:
            data = self.__data[kanal]
            data = data[data[u'flag'] == -1000] #samo losi flagovi, validirani
            x = list(data.index)
            y = list(data[u'avg'])
            self.axes.scatter(x, 
                              y, 
                              marker = self.__opcije['glavniKanal']['validanNOK']['marker'], 
                              color = pomocneFunkcije.normalize_rgb(self.__opcije['glavniKanal']['validanNOK']['rgb']), 
                              alpha = self.__opcije['glavniKanal']['validanNOK']['alpha'], 
                              zorder = self.__opcije['glavniKanal']['validanNOK']['zorder'], 
                              label = self.__opcije['glavniKanal']['validanNOK']['label'])
            self.__statusGlavniGraf = True

        #4. nevalidanOK
        kanal = self.__opcije['glavniKanal']['nevalidanOK']['kanal']
        if kanal in kanali:
            data = self.__data[kanal]
            data = data[data[u'flag'] == 1] #samo dobri flagovi, nevalidirani
            x = list(data.index)
            y = list(data[u'avg'])
            self.axes.scatter(x, 
                              y, 
                              marker = self.__opcije['glavniKanal']['nevalidanOK']['marker'], 
                              color = pomocneFunkcije.normalize_rgb(self.__opcije['glavniKanal']['nevalidanOK']['rgb']), 
                              alpha = self.__opcije['glavniKanal']['nevalidanOK']['alpha'], 
                              zorder = self.__opcije['glavniKanal']['nevalidanOK']['zorder'], 
                              label = self.__opcije['glavniKanal']['nevalidanOK']['label'])
            self.__statusGlavniGraf = True
        
        #5 nevalidanNOK
        kanal = self.__opcije['glavniKanal']['nevalidanNOK']['kanal']
        if kanal in kanali:
            data = self.__data[kanal]
            data = data[data[u'flag'] == -1] #samo losi flagovi, nevalidirani
            x = list(data.index)
            y = list(data[u'avg'])
            self.axes.scatter(x, 
                              y, 
                              marker = self.__opcije['glavniKanal']['nevalidanNOK']['marker'], 
                              color = pomocneFunkcije.normalize_rgb(self.__opcije['glavniKanal']['nevalidanNOK']['rgb']), 
                              alpha = self.__opcije['glavniKanal']['nevalidanNOK']['alpha'], 
                              zorder = self.__opcije['glavniKanal']['nevalidanNOK']['zorder'], 
                              label = self.__opcije['glavniKanal']['nevalidanNOK']['label'])
            self.__statusGlavniGraf = True
            
        #6. fillsatni
        kanal = self.__opcije['glavniKanal']['fillsatni']['kanal']
        if self.__opcije['glavniKanal']['fillsatni']['crtaj'] == True:
            if kanal in kanali:
                data = self.__data[kanal]
                x = list(data.index)
                y1 = list(data[self.__opcije['glavniKanal']['fillsatni']['data1']])
                y2 = list(data[self.__opcije['glavniKanal']['fillsatni']['data2']])
                self.axes.fill_between(x, 
                                       y1, 
                                       y2, 
                                       facecolor = pomocneFunkcije.normalize_rgb(self.__opcije['glavniKanal']['fillsatni']['rgb']), 
                                       alpha = self.__opcije['glavniKanal']['fillsatni']['alpha'], 
                                       zorder = self.__opcije['glavniKanal']['fillsatni']['zorder'])
                self.__statusGlavniGraf = True
        
        #7. ekstremimin
        kanal = self.__opcije['glavniKanal']['ekstremimin']['kanal']
        if self.__opcije['glavniKanal']['ekstremimin']['crtaj'] == True:
            if kanal in kanali:
                data = self.__data[kanal]
                x = list(data.index)
                y = list(data[u'min'])
                self.axes.scatter(x, 
                                  y, 
                                  marker = self.__opcije['glavniKanal']['ekstremimin']['marker'], 
                                  color = pomocneFunkcije.normalize_rgb(self.__opcije['glavniKanal']['ekstremimin']['rgb']), 
                                  alpha = self.__opcije['glavniKanal']['ekstremimin']['alpha'], 
                                  zorder = self.__opcije['glavniKanal']['ekstremimin']['zorder'], 
                                  label = self.__opcije['glavniKanal']['ekstremimin']['label'])
                self.__statusGlavniGraf = True

        #8. ekstremimax
        kanal = self.__opcije['glavniKanal']['ekstremimax']['kanal']
        if self.__opcije['glavniKanal']['ekstremimax']['crtaj'] == True:
            if kanal in kanali:
                data = self.__data[kanal]
                x = list(data.index)
                y = list(data[u'max'])
                self.axes.scatter(x, 
                                  y, 
                                  marker = self.__opcije['glavniKanal']['ekstremimax']['marker'], 
                                  color = pomocneFunkcije.normalize_rgb(self.__opcije['glavniKanal']['ekstremimax']['rgb']), 
                                  alpha = self.__opcije['glavniKanal']['ekstremimax']['alpha'], 
                                  zorder = self.__opcije['glavniKanal']['ekstremimax']['zorder'], 
                                  label = self.__opcije['glavniKanal']['ekstremimax']['label'])
                self.__statusGlavniGraf = True
        #kraj crtanja glavnog kanala
        
        #crtanje pomocnih kanala:
        for graf in list(self.__opcije['pomocniKanali'].keys()):
            kanal = self.__opcije['pomocniKanali'][graf]['kanal']
            if kanal in kanali:
                data = self.__data[kanal]
                x = list(data.index)
                y = list(data[u'avg']) #samo crtamo srednje vrijednosti
                self.axes.plot(x, 
                               y, 
                               marker = self.__opcije['pomocniKanali'][graf]['marker'], 
                               linestyle = self.__opcije['pomocniKanali'][graf]['line'],
                               color = pomocneFunkcije.normalize_rgb(self.__opcije['pomocniKanali'][graf]['rgb']), 
                               alpha = self.__opcije['pomocniKanali'][graf]['alpha'],
                               zorder = self.__opcije['pomocniKanali'][graf]['zorder'],
                               label = self.__opcije['pomocniKanali'][graf]['label'])
                              
        #highlight dot
        if self.__statusGlavniGraf:
            self.__testHighlight = False
            trenutniGlavniKanal = self.__opcije['glavniKanal']['validanOK']['kanal']
            
            #rubovi indeksa glavnog kanala, treba za pick i span granice
            self.__tmin = self.__data[trenutniGlavniKanal].index.min()
            self.__tmax = self.__data[trenutniGlavniKanal].index.max()
            
            #odredjivanje x, y granica highlight trocke
            if self.__zadnjiHighlightx in list(self.__data[trenutniGlavniKanal].index):
                ypoint = self.__data[trenutniGlavniKanal].loc[self.__zadnjiHighlightx, u'avg']
            else:
                miny = self.__data[trenutniGlavniKanal][u'min'].min()
                maxy = self.__data[trenutniGlavniKanal][u'max'].max()
                ypoint = (miny + maxy)/2
            
            #nacrtaj highlight
            self.highlight_dot(self.__zadnjiHighlightx, ypoint)
        
        #TODO! pikaz legende
        #prikaz legende na zahtjev
        if self.__opcije['ostalo']['opcijesatni']['legend'] == True:
            self.leg = self.axes.legend(loc = 1, fontsize =8, fancybox  = True)
            self.leg.get_frame().set_alpha(0.9)                    

        
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
            trenutniGlavniKanal = self.__opcije['glavniKanal']['validanOK']['kanal']
            
            #highlight selected point - kooridinate ako nedostaju podaci
            if xpoint in list(self.__data[trenutniGlavniKanal].index):
                ypoint = self.__data[trenutniGlavniKanal].loc[xpoint, u'avg']
            else:
                miny = self.__data[trenutniGlavniKanal][u'min'].min()
                maxy = self.__data[trenutniGlavniKanal][u'max'].max()
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
                if xpoint in list(self.__data[trenutniGlavniKanal].index):
                    yavg = self.__data[trenutniGlavniKanal].loc[xpoint, u'avg']
                    ymin = self.__data[trenutniGlavniKanal].loc[xpoint, u'min']
                    ymax = self.__data[trenutniGlavniKanal].loc[xpoint, u'max']
                    ystatus = self.__data[trenutniGlavniKanal].loc[xpoint, u'status']
                    ycount = self.__data[trenutniGlavniKanal].loc[xpoint, u'count']
                
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
        action1 = QtGui.QAction("Flag: Dobar", menu) #pozitivan flag
        action2 = QtGui.QAction("Flag: Los", menu) #negativan flag
        menu.addAction(action1)
        menu.addAction(action2)
        #povezi akcije menua sa metodama
        action1.triggered.connect(self.dijalog_promjena_flaga_OK)
        action2.triggered.connect(self.dijalog_promjena_flaga_NOK)
        #prikazi menu na definiranoj tocki grafa
        menu.popup(pos)
###############################################################################    
    def dijalog_promjena_flaga_OK(self):
        """
        Metoda sluzi za promjenu flaga na pozitivnu vrijednost i 
        tretira se da su svi unutar intervala validirani.
        
        flag postavlja na 1000 na svim minutnim podatcima unutar intervala, 
        ukljucujuci rubove.
        """
        #dohvati rubove intervala (spremljeni su u membere prilikom poziva dijaloga)
        tmin = self.__lastTimeMin
        tmax = self.__lastTimeMax
        #pomak slicea da uhvati sve ciljane minutne podatke
        tmin = tmin - timedelta(minutes = 59)
        tmin = pd.to_datetime(tmin)
        #dohvati glavni kanal
        glavniKanal = self.__opcije['glavniKanal']['validanOK']['kanal']
        #pakiranje zahtjeva u listu [min, max, flag, kanal, stanica]
        arg = [tmin, tmax, 1000, glavniKanal, self.__info[0]]
        #sredi generalni emit za promjenu flaga
        self.emit(QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), arg)
###############################################################################        
    def dijalog_promjena_flaga_NOK(self):
        """
        Metoda sluzi za promjenu flaga na negativnu vrijednost i 
        tretira se da su svi unutar intervala validirani.
        
        flag postavlja na -1000 na svim minutnim podatcima unutar intervala, 
        ukljucujuci rubove.
        """
        #dohvati rubove intervala (spremljeni su u membere prilikom poziva dijaloga)
        tmin = self.__lastTimeMin
        tmax = self.__lastTimeMax
        #pomak slicea da uhvati sve ciljane minutne podatke
        tmin = tmin - timedelta(minutes = 59)
        tmin = pd.to_datetime(tmin)
        #dohvati glavni kanal
        glavniKanal = self.__opcije['glavniKanal']['validanOK']['kanal']
        #pakiranje zahtjeva u listu [min, max, flag, kanal, stanica]
        arg = [tmin, tmax, -1000, glavniKanal, self.__info[0]]
        #sredi generalni emit za promjenu flaga
        self.emit(QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), arg)
###############################################################################
    def promjenjen_flag(self, lista):
        #TODO! mozda je lista visak
        """
        Metoda sluzi kao slot preko kojega kontroler daje do znanja canvasu
        da su podaci promjenjeni (flag). Zahtjev za ponovnim crtanjem (refresh)
        grafa.
        """
        self.__info = lista
        self.crtaj(self.__opcije, self.__info)
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
###############################################################################