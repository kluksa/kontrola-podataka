# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 08:38:40 2014

@author: User

Klasa (canvas) za prikaz satno agregiranih vrijednosti.
"""
from PyQt4 import QtGui, QtCore

import functools
import matplotlib
import pandas as pd
import datetime
from datetime import timedelta

import pomocne_funkcije
import opceniti_canvas
###############################################################################
###############################################################################
class Graf(opceniti_canvas.MPLCanvas):
    """
    Definira detalje crtanja satno agregiranog grafa i pripadne evente
    """
    def __init__(self, *args, **kwargs):
        """konstruktor"""
        opceniti_canvas.MPLCanvas.__init__(self, *args, **kwargs)
        #podrska za kontekstni meni za promjenu flaga (desni klik misem na canvas)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.data = {} #privremeni spremnik za frejmove (ucitane)

        #da li je nacrtan glavni graf
        self.statusGlavniGraf = False
        self.statusHighlight = False
        self.statusAnnotation = False

        #kooridinate zadnjeg highlighta
        self.lastHighlight = (None, None)
        self.lastAnnotation = None

        #definicija raspona granica grafa za zoom
        self.xlim_original = self.axes.get_xlim()
        self.ylim_original = self.axes.get_ylim()

        #rastegni canvas udesno
        self.axes.figure.subplots_adjust(right = 0.98)
###############################################################################
    def crtaj(self, lista):
        """
        Eksplicitne naredbe za crtanje

        lista[0] --> int ,programMjerenjaId glavnog kanala
        lista[1] --> tmin
        lista[2] --> tmax
        lista[3] --> grafSettingsDTO
        lista[4] --> appSettingsDTO
        """
        #promjeni cursor u wait cursor
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        ###priprema... reset nekih membera u pocetno stanje###
        self.axes.clear()
        self.data = {}
        self.statusGlavniGraf = False
        self.statusAnnotation = False
        self.tmin = lista[1]
        self.tmax = lista[2]
        self.dto = lista[3]
        self.appDto = lista[4]
        self.tKontejner = lista[5]
        ###step 1. probaj dohvatiti glavni kanal za crtanje###
        self.gKanal = lista[0]
        #emit zahtjev za podacima, return se vraca u member self.data
        self.emit(QtCore.SIGNAL('request_agregirani_frejm(PyQt_PyObject)'), lista[:3])
        if self.gKanal in self.data.keys():
            #TODO! ucitaj temperaturu kontejnera ako postoji
            if self.tKontejner is not None:
                arg = [self.tKontejner, self.tmin, self.tmax]
                self.emit(QtCore.SIGNAL('request_agregirani_frejm(PyQt_PyObject)'), arg)
            #kreni ucitavati ostale ako ih ima!
            for programKey in self.dto.dictPomocnih.keys():
                if programKey not in self.data.keys():
                    arg = [programKey, self.tmin, self.tmax]
                    self.emit(QtCore.SIGNAL('request_agregirani_frejm(PyQt_PyObject)'), arg)

            #ostali bi sada svi trebali biti u self.data
            ###step2. crtanje grafova koji su uspjesno ucitani u self.data###
            #midline
            frejm = self.data[self.gKanal]
            x = list(frejm.index)
            y = list(frejm[u'avg'])
            self.axes.plot(x,
                           y,
                           linestyle = self.dto.satniMidline.lineStyle,
                           linewidth = self.dto.satniMidline.lineWidth,
                           color = self.dto.satniMidline.color,
                           zorder = self.dto.satniMidline.zorder,
                           label = self.dto.satniMidline.label)

            #fill izmedju komponenti
            if self.dto.satniFill.crtaj:
                y1 = list(frejm[self.dto.satniFill.komponenta1])
                y2 = list(frejm[self.dto.satniFill.komponenta2])
                self.axes.fill_between(x,
                                       y1,
                                       y2,
                                       facecolor = self.dto.satniFill.color,
                                       zorder = self.dto.satniFill.zorder,
                                       label = self.dto.satniFill.label)

            #ekstremi min i max
            if self.dto.satniEksMin.crtaj:
                self.crtaj_scatter_konc('min', self.dto.satniEksMin, None)
                self.crtaj_scatter_konc('max', self.dto.satniEksMax, None)
            #validan i ok flag
            self.crtaj_scatter_konc('avg', self.dto.satniVOK, 1000)
            #validan i los flag
            self.crtaj_scatter_konc('avg', self.dto.satniVBAD, -1000)
            #sirov podatak i ok flag
            self.crtaj_scatter_konc('avg', self.dto.satniNVOK, 1)
            #sirov podatak i los flag
            self.crtaj_scatter_konc('avg', self.dto.satniNVBAD, -1)

            #crtanje pomocnih grafova
            popis = list(self.data.keys())
            popis.remove(self.gKanal)
            #TODO! makni temperaturu kontenjera sa popisa
            if self.tKontejner:
                popis.remove(self.tKontejner)
            for key in popis:
                frejm = self.data[key]
                x = list(frejm.index)
                y = list(frejm[u'avg'])
                self.axes.plot(x,
                               y,
                               marker = self.dto.dictPomocnih[key].markerStyle,
                               markersize = self.dto.dictPomocnih[key].markerSize,
                               linestyle = self.dto.dictPomocnih[key].lineStyle,
                               linewidth = self.dto.dictPomocnih[key].lineWidth,
                               color = self.dto.dictPomocnih[key].color,
                               zorder = self.dto.dictPomocnih[key].zorder,
                               label = self.dto.dictPomocnih[key].label)

            #set limits and ticks
            self.setup_limits('SATNI') #metda definirana u opceniti_canvas.py
            self.setup_ticks()
            self.setup_legend() #metda definirana u opceniti_canvas.py

            #toggle minor tickova, i grida
            self.toggle_ticks(self.appDto.satniTicks) #metda definirana u opceniti_canvas.py
            self.toggle_grid(self.appDto.satniGrid) #metda definirana u opceniti_canvas.py
            self.toggle_legend(self.appDto.satniLegend) #metda definirana u opceniti_canvas.py

            #TODO! crtanje upozorenja ako je temeratura kontejnera izvan granica
            if self.tKontejner is not None:
                frejm = self.data[self.tKontejner]
                frejm = frejm[frejm['flag'] > 0]
                overlimit = frejm[frejm['avg'] > 30]
                underlimit = frejm[frejm['avg'] < 15]
                frejm = overlimit.append(underlimit)
                x = list(frejm.index)
                brojLosih = len(x)
                if brojLosih:
                    y1, y2 = self.ylim_original
                    c = y2 - 0.05*abs(y2-y1) #odmak od gornjeg ruba za 5% max raspona
                    y = [c for i in range(brojLosih)]
                    self.axes.plot(x,
                                   y,
                                   marker = '*',
                                   color = 'Red',
                                   linestyle = 'None',
                                   alpha = 0.4)


            #highlight prijasnje tocke #TODO!
            if self.statusHighlight:
                hx, hy = self.lastHighlight
                if hx in self.data[self.gKanal].index:
                    # pronadji novu y vrijednosti indeksa
                    hy = self.data[self.gKanal].loc[hx, 'avg']
                    self.make_highlight(hx, hy)
                else:
                    self.statusHighlight = False
                    self.lastHighlight = (None, None)

            self.draw()
            #promjeni cursor u normalan cursor
            QtGui.QApplication.restoreOverrideCursor()

        else:
            self.axes.clear()
            self.axes.text(0.5,
                           0.5,
                           'Nije moguce pristupiti podacima za trazeni kanal.',
                           horizontalalignment='center',
                           verticalalignment='center',
                           fontsize = 8,
                           transform = self.axes.transAxes)
            self.draw()
            #promjeni cursor u normalan cursor
            QtGui.QApplication.restoreOverrideCursor()
###############################################################################
    def setup_ticks(self):
        """
        postavljanje pozicije i formata tickova x osi.
        major ticks - svaki puni sat
        minor ticks - svakih 15 minuta (ali bez vrijednosti punog sata)
        """
        tickovi = pomocne_funkcije.pronadji_tickove_satni(self.tmin, self.tmax)
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
    def crtaj_scatter_konc(self, komponenta, dto, flag):
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
            if komponenta == 'min':
                y = list(frejm[u'min'])
            elif komponenta == 'max':
                y = list(frejm[u'max'])
            else:
                y = list(frejm[u'avg'])
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
    def highlight_pick(self, tpl):
        """
        crta highlight tocku na grafu sa koridinatama tpl = (x, y)
        """
        x, y = tpl
        if self.statusHighlight:
            if not tpl == self.lastHighlight:
                self.axes.lines.remove(self.highlight[0])
                self.make_highlight(x, y)
        else:
            self.make_highlight(x, y)

        self.draw()
###############################################################################
    def make_highlight(self, x, y):
        """
        napravi instancu highlight tocke na kooridinati x, y
        """
        self.highlight = self.axes.plot(x,
                                        y,
                                        marker = 'o',
                                        markersize = 1.5*self.dto.satniVOK.markerSize,
                                        color = 'yellow',
                                        alpha = 0.5,
                                        zorder = 10)
        self.lastHighlight = (x, y)
        self.statusHighlight = True
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
            xpoint = pomocne_funkcije.zaokruzi_vrijeme(xpoint, 3600)
            #aktualna konverzija iz datetime.datetime objekta u pandas.tislib.Timestamp
            xpoint = pd.to_datetime(xpoint)
            #bitno je da zaokruzeno vrijeme nije izvan granica frejma (izbjegavnjanje index errora)
            if xpoint >= self.tmax:
                xpoint = self.tmax
            if xpoint <= self.tmin:
                xpoint = self.tmin

            #highlight selected point - kooridinate ako nedostaju podaci
            if xpoint in list(self.data[self.gKanal].index):
                ypoint = self.data[self.gKanal].loc[xpoint, u'avg']
            else:
                miny = self.data[self.gKanal][u'min'].min()
                maxy = self.data[self.gKanal][u'max'].max()
                ypoint = (miny + maxy)/2

            if event.button == 1:
                #left click, naredi crtanje minutnog i highlight tocku
                self.emit(QtCore.SIGNAL('gui_crtaj_minutni_graf(PyQt_PyObject)'), xpoint)
                #highlight selected point
                self.highlight_pick((xpoint, ypoint))

            elif event.button == 2:
                if xpoint in list(self.data[self.gKanal].index):
                    yavg = self.data[self.gKanal].loc[xpoint, u'avg']
                    ymin = self.data[self.gKanal].loc[xpoint, u'min']
                    ymax = self.data[self.gKanal].loc[xpoint, u'max']
                    ystatus = self.data[self.gKanal].loc[xpoint, u'status']
                    ycount = self.data[self.gKanal].loc[xpoint, u'count']

                    tekst = 'Vrijeme: '+str(xpoint)+'\nAverage: '+str(yavg)+'\nMin:'+str(ymin)+'\nMax:'+str(ymax)+'\nStatus:'+str(ystatus)+'\nCount:'+str(ycount)
                else:
                    tekst = 'Vrijeme: '+str(xpoint)+'\nNema podataka'

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
    def span_select(self, t1, t2):
        """
        Metoda je povezana sa span selektorom (ako je inicijaliziran).
        Metoda je zaduzena da prikaze kontekstni dijalog za promjenu flaga
        na mjestu gdje "releasamo" ljevi klik.

        t1 i t2 su timestampovi, ali ih treba adaptirati
        """
        if self.statusGlavniGraf: #glavni graf mora biti nacrtan
            #konverzija ulaznih vrijednosti u pandas timestampove
            t1 = matplotlib.dates.num2date(t1)
            t2 = matplotlib.dates.num2date(t2)
            t1 = datetime.datetime(t1.year, t1.month, t1.day, t1.hour, t1.minute, t1.second)
            t2 = datetime.datetime(t2.year, t2.month, t2.day, t2.hour, t2.minute, t2.second)
            #vremena se zaokruzuju na najblizi sat
            t1 = pomocne_funkcije.zaokruzi_vrijeme(t1, 3600)
            t2 = pomocne_funkcije.zaokruzi_vrijeme(t2, 3600)
            t1 = pd.to_datetime(t1)
            t2 = pd.to_datetime(t2)

            #osiguranje da se ne preskoce granice glavnog kanala (izbjegavanje index errora)
            if t1 < self.tmin:
                t1 = self.tmin
            if t1 > self.tmax:
                t1 = self.tmax
            if t2 < self.tmin:
                t2 = self.tmin
            if t2 > self.tmax:
                t2 = self.tmax
            print(t1, t2)
            #tocke ne smiju biti iste (izbjegavamo paljenje dijaloga na ljevi klik)
            if t1 != t2:
                #pozovi dijalog za promjenu flaga
                loc = QtGui.QCursor.pos()
                self.show_context_menu(loc, t1, t2)
###############################################################################
    def set_agregirani_kanal(self, arglist):
        """
        BITNA METODA! - mehanizam s kojim se ucitavaju frejmovi za crtanje.
        -metoda crtaj trazi od kontrolera podatke
        -ovo je predvidjeni slot gdje kontroler vraca trazene podatke

        metoda postavlja agregirani frejm u self.data
        lista -> [kanal, frejm]
        kanal -> int, ime kanala
        frejm -> pandas dataframe, agregirani podaci
        """
        self.data[arglist[0]] = arglist[1]
###############################################################################
    def show_context_menu(self, pos, tmin, tmax):
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
        Metoda sluzi za promjenu flaga
        ovisno o keyword argumentu tip.
        """
        #dohvati rubove intervala (spremljeni su u membere prilikom poziva dijaloga)
        tmin = self.__lastTimeMin
        tmax = self.__lastTimeMax
        #pomak slicea da uhvati sve ciljane minutne podatke
        tmin = tmin - timedelta(minutes = 59)
        tmin = pd.to_datetime(tmin)
        #pakiranje zahtjeva u listu [tmin, tmax, flag, glavni kanal] ovisno o tipu
        if tip != None:
            arg = [tmin, tmax, tip, self.gKanal]
            #generalni emit za promjenu flaga
            self.emit(QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), arg)
###############################################################################
###############################################################################