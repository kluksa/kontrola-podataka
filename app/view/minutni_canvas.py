# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 13:14:26 2014

@author: User

Klasa (canvas) za prikaz minutnih vrijednosti.
"""

import functools
import datetime

from PyQt4 import QtGui, QtCore
import matplotlib
import pandas as pd

import app.general.pomocne_funkcije as pomocne_funkcije
import app.view.opceniti_canvas as opceniti_canvas
###############################################################################
###############################################################################
class MinutniKanvas(opceniti_canvas.OpcenitiKanvas):
    """
    Definira detalje crtanja minutnog grafa i pripadne evente
    """
    def __init__(self, konfig, appKonfig, *args, **kwargs):
        """konstruktor"""
        opceniti_canvas.OpcenitiKanvas.__init__(self, *args, **kwargs)

        #podrska za kontekstni meni za promjenu flaga
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.data = {} #spremnik za frejmove (ucitane)

        #da li je nacrtan glavni graf
        self.statusGlavniGraf = False
        self.statusAnnotation = False

        #kooridinate zadnjeg highlighta
        self.lastAnnotation = None

        #definicija raspona granica grafa za zoom
        self.xlim_original = self.axes.get_xlim()
        self.ylim_original = self.axes.get_ylim()

        #rastegni canvas udesno
        self.axes.figure.subplots_adjust(right = 0.98)

        self.dto = konfig
        self.appDto = appKonfig
###############################################################################
    def crtaj_pomocne(self, popis):
        for key in popis:
            frejm = self.data[key]
            x = list(frejm.index)
            y = list(frejm[u'koncentracija'])
            self.axes.plot(x,
                           y,
                           marker=self.dto.dictPomocnih[key].markerStyle,
                           markersize=self.dto.dictPomocnih[key].markerSize,
                           linestyle=self.dto.dictPomocnih[key].lineStyle,
                           linewidth=self.dto.dictPomocnih[key].lineWidth,
                           color=self.dto.dictPomocnih[key].color,
                           zorder=self.dto.dictPomocnih[key].zorder,
                           label=self.dto.dictPomocnih[key].label)

    def crtaj_glavni_graf(self):
        # midline plot
        frejm = self.data[self.gKanal]
        x = list(frejm.index)
        y = list(frejm[u'koncentracija'])
        self.axes.plot(x,
                       y,
                       linestyle=self.dto.minutniMidline.lineStyle,
                       linewidth=self.dto.minutniMidline.lineWidth,
                       color=self.dto.minutniMidline.color,
                       zorder=self.dto.minutniMidline.zorder,
                       label=self.dto.minutniMidline.label)
        #plot tocaka ovisno o flagu i validaciji
        self.crtaj_scatter_konc(self.dto.minutniVOK, 1000)
        self.crtaj_scatter_konc(self.dto.minutniVBAD, -1000)
        self.crtaj_scatter_konc(self.dto.minutniNVOK, 1)
        self.crtaj_scatter_konc(self.dto.minutniNVBAD, -1)

    def crtaj_oznake_temperature(self):
        frejm = self.data[self.tKontejner]
        frejm = frejm[frejm['flag'] > 0]
        overlimit = frejm[frejm['koncentracija'] > 30]
        underlimit = frejm[frejm['koncentracija'] < 15]
        frejm = overlimit.append(underlimit)
        x = list(frejm.index)
        brojLosih = len(x)
        if brojLosih:
            y1, y2 = self.ylim_original
            c = y2 - 0.05 * abs(y2 - y1)  # odmak od gornjeg ruba za 5% max raspona
            y = [c for i in range(brojLosih)]
            self.axes.plot(x,
                           y,
                           marker='*',
                           color='Red',
                           linestyle='None',
                           alpha=0.4)

    def crtaj(self, ulaz):
        """Eksplicitne naredbe za crtanje zadane sa popisom grafova i vremenskim
        intervalom.

        ulaz je mapa
        ulaz['kanalId'] - glavni kanal id
        ulaz['pocetnoVrijeme'] - min vrijeme
        ulaz['zavrsnoVrijeme'] - max vrijeme
        ulaz['tempKontejner'] - temp. kontejnera id
        """
        #promjeni cursor u wait cursor
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

        #clear data, svaki poziv ove metode uvjetuje ponovno povlacenje podataka
        #iz modela. Cilj je dohvatiti zadnje azurne podatke.
        self.axes.clear()
        self.data = {}
        self.statusGlavniGraf = False
        self.statusAnnotation = False
        self.pocetnoVrijeme = ulaz['pocetnoVrijeme']
        self.zavrsnoVrijeme = ulaz['zavrsnoVrijeme']
        ###step 1. probaj dohvatiti glavni kanal za crtanje###
        self.gKanal = ulaz['kanalId']
        self.tKontejner = ulaz['tempKontejner']
        #emit zahtjev za podacima, return se vraca u member self.data
        arg = {'kanal': self.gKanal,
               'od': self.pocetnoVrijeme,
               'do': self.zavrsnoVrijeme}
        self.emit(QtCore.SIGNAL('request_minutni_frejm(PyQt_PyObject)'), arg)

        if self.gKanal in self.data.keys():
            #TODO! ucitaj temperaturu kontejnera ako postoji
            if self.tKontejner is not None:
                arg = {'kanal': self.tKontejner,
                       'od': self.pocetnoVrijeme,
                       'do': self.zavrsnoVrijeme}
                self.emit(QtCore.SIGNAL('request_minutni_frejm(PyQt_PyObject)'), arg)
            #kreni ucitavati ostale ako ih ima!
            for programKey in self.dto.dictPomocnih.keys():
                if programKey not in self.data.keys():
                    arg = {'kanal': programKey,
                           'od': self.pocetnoVrijeme,
                           'do': self.zavrsnoVrijeme}
                    self.emit(QtCore.SIGNAL('request_minutni_frejm(PyQt_PyObject)'), arg)

            self.crtaj_glavni_graf()

            key_set = set(self.data.keys()) - set([self.gKanal, self.tKontejner])
            popis =  {key: self.data[key] for key in key_set}

            self.crtaj_pomocne(popis)
            #set limits and ticks
            self.setup_limits('MINUTNI') #metda definirana u opceniti_canvas.py
            self.setup_ticks(pomocne_funkcije.pronadji_tickove_minutni(self.pocetnoVrijeme, self.zavrsnoVrijeme))
            self.setup_legend() #metda definirana u opceniti_canvas.py

            #toggle minor tickova, i grida
            self.toggle_ticks(self.appDto.minutniTicks) #metda definirana u opceniti_canvas.py
            self.toggle_grid(self.appDto.minutniGrid) #metda definirana u opceniti_canvas.py
            self.toggle_legend(self.appDto.minutniLegend) #metda definirana u opceniti_canvas.py


            #TODO! crtanje upozorenja ako je temeratura kontejnera izvan granica
            if self.tKontejner in self.data:
                self.crtaj_oznake_temperature()
        else:
            self.axes.clear()
            self.axes.text(0.5,
                           0.5,
                           'Nije moguce pristupiti podacima za trazeni kanal i sat.',
                           horizontalalignment='center',
                           verticalalignment='center',
                           fontsize = 8,
                           transform = self.axes.transAxes)
        self.draw()
        #promjeni cursor u normalan cursor
        QtGui.QApplication.restoreOverrideCursor()
###############################################################################
    def setup_ticks(self, tickovi):
        """
        postavljanje pozicije i formata tickova x osi.
        major ticks - svaki puni sat
        minor ticks - svakih 15 minuta (ali bez vrijednosti punog sata)
        """

        self.majorTickLoc = tickovi['majorTickovi']
        self.majorTickLab = tickovi['majorLabeli']
        self.minorTickLoc = tickovi['minorTickovi']
        self.minorTickLab = tickovi['minorLabeli']

        self.axes.set_xticks(self.majorTickLoc, minor = False)
        self.axes.set_xticklabels(self.majorTickLab, minor = False)
        self.axes.set_xticks(self.minorTickLoc, minor = True)
        self.axes.set_xticklabels(self.minorTickLab, minor = True)

        allXLabels = self.axes.get_xticklabels(which = 'both') #dohvati sve labele
        for label in allXLabels:
            label.set_rotation(45)
            label.set_fontsize(8)

###############################################################################
    def span_select(self, t1, t2):
        """
        Metoda je povezana sa span selektorom (ako je inicijaliziran).
        Metoda je zaduzena da prikaze kontekstni dijalog za promjenu flaga
        na mjestu gdje "releasamo" ljevi klik.

        t1 i t2 su timestampovi, ali ih treba adaptirati
        """
        sekunde = 60
        if self.statusGlavniGraf: #glavni graf mora biti nacrtan
            #konverzija ulaznih vrijednosti u pandas timestampove
            t1 = matplotlib.dates.num2date(t1)
            t2 = matplotlib.dates.num2date(t2)
            t1 = datetime.datetime(t1.year, t1.month, t1.day, t1.hour, t1.minute, t1.second)
            t2 = datetime.datetime(t2.year, t2.month, t2.day, t2.hour, t2.minute, t2.second)
            #vremena se zaokruzuju na najblizu minutu (60 sekundi)
            t1 = pomocne_funkcije.zaokruzi_vrijeme(t1, sekunde)
            t2 = pomocne_funkcije.zaokruzi_vrijeme(t2, sekunde)
            t1 = pd.to_datetime(t1)
            t2 = pd.to_datetime(t2)

            #osiguranje da se ne preskoce granice glavnog kanala
            if t1 < self.pocetnoVrijeme:
                t1 = self.pocetnoVrijeme
            if t1 > self.zavrsnoVrijeme:
                t1 = self.zavrsnoVrijeme
            if t2 < self.pocetnoVrijeme:
                t2 = self.pocetnoVrijeme
            if t2 > self.zavrsnoVrijeme:
                t2 = self.zavrsnoVrijeme

            #tocke ne smiju biti iste (izbjegavamo paljenje dijaloga na ljevi klik)
            if t1 != t2:
                #pozovi dijalog za promjenu flaga
                loc = QtGui.QCursor.pos()
                self.show_context_menu(loc, t1, t2)
###############################################################################
    def show_context_menu(self, pos, tmin, tmax):
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
        #pakiranje zahtjeva u listu [tmin, tmax, flag, kanal] ovisno o tipu
        if tip != None:
            #arg = [tmin, tmax, tip, self.gKanal]
            arg = {'od': tmin,
                   'do': tmax,
                   'noviFlag': tip,
                   'kanal': self.gKanal}

            #generalni emit za promjenu flaga
            self.emit(QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), arg)
###############################################################################
    def crtaj_scatter_konc(self, dto, flag):
        """
        pomocna funkcija za crtanje scatter tipa grafa (samo tocke)
        komponenta je opisni string
        dto je grafDTO objekt
        flag je int vrijednost flaga za razlikovanje validacije ILI None
        """
        frejm = self.data[self.gKanal]
        if flag != None:
            frejm = frejm[frejm[u'flag'] == flag]
        x = list(frejm.index)
        #crtaj samo ako ima podataka
        if len(x) > 0:
            y = list(frejm[u'koncentracija'])
            #naredba za plot
            self.axes.plot(x,
                           y,
                           marker = dto.markerStyle,
                           markersize = dto.markerSize,
                           linestyle = 'None',
                           color = dto.color,
                           zorder = dto.zorder,
                           label = dto.label)
            self.statusGlavniGraf = True
###############################################################################
    def on_pick(self, event):
        """
        pick event na satnom grafu
        """
        if self.statusGlavniGraf and event.inaxes == self.axes:
            xpoint = matplotlib.dates.num2date(event.xdata) #datetime.datetime
            #problem.. rounding offset aware i offset naive datetimes..workaround
            xpoint = datetime.datetime(xpoint.year,
                                       xpoint.month,
                                       xpoint.day,
                                       xpoint.hour,
                                       xpoint.minute,
                                       xpoint.second)
            #zaokruzi na najblizi puni sat (bitno za podudaranje indeksa u frejmu)
            xpoint = pomocne_funkcije.zaokruzi_vrijeme(xpoint, 60)
            #aktualna konverzija iz datetime.datetime objekta u pandas.tislib.Timestamp
            xpoint = pd.to_datetime(xpoint)
            #bitno je da zaokruzeno vrijeme nije izvan granica frejma (izbjegavnjanje index errora)
            if xpoint >= self.zavrsnoVrijeme:
                xpoint = self.zavrsnoVrijeme
            if xpoint <= self.pocetnoVrijeme:
                xpoint = self.pocetnoVrijeme

            #highlight selected point - kooridinate ako nedostaju podaci
            if xpoint in list(self.data[self.gKanal].index):
                ypoint = self.data[self.gKanal].loc[xpoint, u'koncentracija']
            else:
                miny = self.data[self.gKanal][u'koncentracija'].min()
                maxy = self.data[self.gKanal][u'koncentracija'].max()
                ypoint = (miny + maxy)/2

            #tipovi akcija ovisno o pritisnutom gumbu
            if event.button == 2:
                if xpoint in list(self.data[self.gKanal].index):
                    ykonc = self.data[self.gKanal].loc[xpoint, u'koncentracija']
                    ystat = self.data[self.gKanal].loc[xpoint, u'status']
                    yflag = self.data[self.gKanal].loc[xpoint, u'flag']
                    tekst = 'Vrijeme: '+str(xpoint)+'\nKoncentracija: '+str(ykonc)+'\nStatus:'+str(ystat)+'\nFlag:'+str(yflag)
                else:
                    tekst = 'Vrijeme: '+str(xpoint)+'\nNema podataka za izabrani sat'

                #annotation offset
                size = self.frameSize()
                x, y = size.width(), size.height()
                x = x//2
                y = y//2
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

                datacords = (xpoint, ypoint)
                offset = (clickedx, clickedy)
                self.annotate_pick(datacords, offset, tekst)

            elif event.button == 3:
                #flag change
                #poziva context menu sa informacijom o lokaciji i satu
                loc = QtGui.QCursor.pos() #lokacija klika
                self.show_context_menu(loc, xpoint, xpoint) #interval koji treba promjeniti
###############################################################################
    def annotate_pick(self, point, offs, tekst):
        """
        Mangage annotation za tocku point, na offsetu offs, sa tekstom tekst
        point - (x, y) tuple
        offs - (xoff, yoff) tuple
        tekst - string
        """
        if self.statusAnnotation:
            self.annotation.remove()
            self.statusAnnotation = False
            if point[0] != self.lastAnnotation:
                self.make_annotation(point, offs, tekst)
        else:
            self.make_annotation(point, offs, tekst)
        self.draw()
###############################################################################
    def make_annotation(self, point, offs, tekst):
        """Napravi annotation instancu"""
        self.annotation = self.axes.annotate(
                    tekst,
                    xy = point,
                    xytext = offs,
                    textcoords = 'offset points',
                    ha = 'left',
                    va = 'center',
                    fontsize = 7,
                    zorder = 102,
                    bbox = dict(boxstyle = 'square', fc = 'cyan', alpha = 0.7),
                    arrowprops = dict(arrowstyle = '->'))
        self.lastAnnotation = point[0]
        self.statusAnnotation = True
###############################################################################
    def clear_minutni(self):
        """
        clear minutnog grafa
        """
        #podrska za kontekstni meni za promjenu flaga
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.data = {} #spremnik za frejmove (ucitane)

        self.statusGlavniGraf = False
        self.statusAnnotation = False

        #kooridinate zadnjeg highlighta
        self.lastAnnotation = None

        self.axes.clear()
        self.draw()
###############################################################################
    def set_minutni_kanal(self, argMap):
        """
        BITNA METODA! - mehanizam s kojim se ucitavaju frejmovi za crtanje.
        -metoda crtaj trazi od kontrolera podatke
        -ovo je predvidjeni slot gdje kontroler vraca trazene podatke
        -ulaz je mapa

        metoda postavlja frejm minutnih podataka u self.__data
        argMap['kanal'] -> int, ime kanala
        argMap['dataFrejm'] -> pandas dataframe, minutni podaci
        """
        self.data[argMap['kanal']] = argMap['dataFrejm']
###############################################################################

###############################################################################
