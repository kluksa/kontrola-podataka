# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 12:27:25 2015

@author: DHMZ-Milic
"""
#TODO! integracija i testing ovog canvasa u applikaciju

import datetime
import matplotlib
import functools
import pandas as pd
from PyQt4 import QtGui, QtCore #import djela Qt frejmworka
from enum import Enum
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas #import specificnog canvasa za Qt
from matplotlib.figure import Figure #import figure
from matplotlib.widgets import RectangleSelector, SpanSelector, Cursor

import app.general.pomocne_funkcije as pomocne_funkcije
################################################################################
################################################################################
class SatniEnum(Enum):
    """konstante za satni graf"""
    tip = 'SATNI'
    midline = 'avg'
    minimum = 'min'
    maksimum = 'max'
################################################################################
################################################################################
class MinutniEnum(Enum):
    """konstante za minutni graf"""
    tip = 'MINUTNI'
    midline = 'koncentracija'
################################################################################
################################################################################
class ZeroEnum(Enum):
    """konstante za zero graf"""
    tip = 'ZERO'
    midline = 'vrijednost'
    warningLow = 'minDozvoljeno'
    warningHigh = 'maxDozvoljeno'
################################################################################
################################################################################
class SpanEnum(Enum):
    """konstante za span graf"""
    tip = 'SPAN'
    midline = 'vrijednost'
    warningLow = 'minDozvoljeno'
    warningHigh = 'maxDozvoljeno'
################################################################################
################################################################################
class GrafEnum(Enum):
    """nested enum svih tipova grafova, cilj je inicijalizrati canvas sa jedom
    od vrijednosti kao tip. (npr. tip = GrafEnum.satni.value)"""
    satni = SatniEnum
    minutni = MinutniEnum
    zero = ZeroEnum
    span = SpanEnum
################################################################################
################################################################################
class Kanvas(FigureCanvas):
    """
    Canvas za prikaz i interakciju sa grafovima
    """
    def __init__(self, konfig, appKonfig, tip, parent = None, width = 6, height = 5, dpi=100):
        """osnovna definicija figure, axes i canvasa"""
        self.fig = Figure(figsize = (width, height), dpi = dpi)
        self.axes = self.fig.add_subplot(111)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(
            self,
            QtGui.QSizePolicy.Expanding,
            QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        """podrska za kontekstni meni"""
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        """bitni memberi"""
        self.tip_grafa = tip #Enum objekt sa tipom grafa npr. GrafEnum.satni.value
        self.dto = konfig #konfig dto objekt
        self.appDto = appKonfig #app konfig objekt
        self.data = {} #prazan dict koji ce sadrzavati frejmove sa podacima
        self.gKanal = None #kanal id glavnog kanala
        self.tKontejner = None #kanal id za temperaturu kontejnera za zadani glavni kanal
        self.pocetnoVrijeme = None #min zadano vrijeme za prikaz
        self.zavrsnoVrijeme = None #max zadano vrijeme za prikaz
        self.xlim_original = self.axes.get_xlim() #definicija raspona x osi grafa (zoom)
        self.ylim_original = self.axes.get_ylim() #definicija raspona y osi grafa (zoom)
        self.statusGlavniGraf = False #status glavnog grafa (da li je glavni kanal nacrtan)
        self.statusAnnotation = False #status prikaza annotationa
        self.lastAnnotation = None #kooridinate zadnjeg annotationa
        self.statusHighlight = False #status prikaza oznacene izabrane tocke
        self.lastHighlight = (None, None) #kooridinate zadnjeg highlighta
        self.legenda = None #placeholder za legendu

        #dynamic size za highlight (1.5 puta veci od markera)
        if self.tip_grafa is SpanEnum:
            self.highlightSize = 1.5 * self.dto.spanVOK.markerSize
        elif self.tip_grafa is ZeroEnum:
            self.highlightSize = 1.5 * self.dto.zeroVOK.markerSize
        elif self.tip_grafa is SatniEnum:
            self.highlightSize = 1.5 * self.dto.satniVOK.markerSize
        else:
            self.highlightSize = 15

        #Axes labeli
        self.axes.set_xlabel('Vrijeme')
        self.axes.set_ylabel(self.tip_grafa.tip.value)

        if self.tip_grafa is SpanEnum:
            #prebaci lokaciju tickova
            self.axes.xaxis.set_ticks_position('top')
            self.axes.figure.subplots_adjust(bottom = 0.02)
            self.axes.figure.subplots_adjust(right = 0.98)
        elif self.tip_grafa is ZeroEnum:
            self.axes.xaxis.set_ticks_position('bottom')
            self.axes.figure.subplots_adjust(top = 0.98)
            self.axes.figure.subplots_adjust(right = 0.98)

        self.initialize_interaction()
################################################################################
    def crtaj(self, ulaz):
        """
        Glavna metoda za crtanje na canvas. Eksplicitne naredbe za crtanje.

        Crtanje ide kroz nekoliko koraka:
        1. reinicijalizacija membera ovisno o ulaznim podacima
        2. priprema i dohvacanje podataka za crtanje
        3. crtanje glavnog kanala
        4. crtanje pomocnih kanala
        5. crtanje temperature kontejnera
        6. provjera za crtanje highlighta (markera trenutno izabrane tocke)
        7. setup granica, tickova, grida, interakcije....

        ulaz je dict podataka
        ulaz['kanalId'] --> int ,programMjerenjaId glavnog kanala [int]
        ulaz['pocetnoVrijeme'] --> pocetno vrijeme [pandas timestamp]
        ulaz['zavrsnoVrijeme'] --> zavrsno vrijeme [pandas timestamp]
        ulaz['tempKontejner'] --> temperatura kontejnera id (ili None) [int]
        """
        ###priprema za crtanje... reset i inicijalizacija membera###
        self.axes.clear()
        self.data = {}
        self.statusGlavniGraf = False
        self.statusAnnotation = False
        self.pocetnoVrijeme = ulaz['pocetnoVrijeme']
        self.zavrsnoVrijeme = ulaz['zavrsnoVrijeme']
        self.gKanal = ulaz['kanalId']
        self.tKontejner = ulaz['tempKontejner']

        #redo Axes labels
        self.axes.set_xlabel('Vrijeme')
        self.axes.set_ylabel(self.tip_grafa.tip.value)

        ###emit zahtjev za podacima glavnog kanala, return se vraca u member self.data
        arg = {'kanal':self.gKanal,
               'od':self.pocetnoVrijeme,
               'do':self.zavrsnoVrijeme}
        self.emit_request_za_podacima(arg)

        #Provjera za postojanjem podataka glavnog kanala.
        if self.gKanal in self.data.keys():
            """temperatura kontejnera i pomocni grafovi se koriste samo kod
            satnog i minutnog grafa"""
            if self.tip_grafa is SatniEnum or self.tip_grafa is MinutniEnum:
                #ucitaj temperaturu kontejnera ako postoji
                if self.tKontejner is not None:
                    arg = {'kanal':self.tKontejner,
                           'od':self.pocetnoVrijeme,
                           'do':self.zavrsnoVrijeme}
                    self.emit_request_za_podacima(arg)
                #kreni ucitavati pomocne kanale po potrebi
                for programKey in self.dto.dictPomocnih.keys():
                    if programKey not in self.data.keys():
                        arg = {'kanal':programKey,
                               'od':self.pocetnoVrijeme,
                               'do':self.zavrsnoVrijeme}
                        self.emit_request_za_podacima(arg)
            #naredba za crtanje glavnog grafa
            self.crtaj_glavni_kanal()
            #set dostupnih pomocnih kanala za crtanje
            pomocni = set(self.data.keys()) - set([self.gKanal, self.tKontejner])
            self.crtaj_pomocne(pomocni)

            ###micanje tocaka od rubova, tickovi, legenda...
            self.setup_limits()
            self.setup_ticks()
            self.setup_legend()

            #toggle minor tickova, i grida
            if self.tip_grafa is SatniEnum:
                self.toggle_ticks(self.appDto.satniTicks)
                self.toggle_grid(self.appDto.satniGrid)
                self.toggle_legend(self.appDto.satniLegend)
            elif self.tip_grafa is MinutniEnum:
                self.toggle_ticks(self.appDto.minutniTicks)
                self.toggle_grid(self.appDto.minutniGrid)
                self.toggle_legend(self.appDto.minutniLegend)
            elif self.tip_grafa is ZeroEnum or self.tip_grafa is SpanEnum:
                self.toggle_legend(self.appDto.zsLegend)
            #crtanje temperature kontejnera
            self.crtaj_oznake_temperature(15,30)
            #highlight prijasnje tocke
            if self.statusHighlight:
                hx, hy = self.lastHighlight
                if hx in self.data[self.gKanal].index:
                    #pronadji novu y vrijednosti indeksa
                    hy = self.data[self.gKanal].loc[hx, self.tip_grafa.midline.value]
                    self.make_highlight(hx, hy, self.highlightSize)
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
################################################################################
    def crtaj_glavni_kanal(self):
        """
        Metoda za crtanje komponenti glavnog kanala na canvas (midline, ekstremi, fill...)
        """
        if self.tip_grafa is SatniEnum:
            #midline
            frejm = self.data[self.gKanal]
            x = list(frejm.index)
            y = list(frejm[self.tip_grafa.midline.value])
            self.crtaj_line(x, y, self.dto.satniMidline)
            #fill izmedju komponenti
            if self.dto.satniFill.crtaj:
                self.crtaj_fill(x,
                                list(frejm[self.dto.satniFill.komponenta1]),
                                list(frejm[self.dto.satniFill.komponenta2]),
                                self.dto.satniFill)
            #ekstremi min i max
            if self.dto.satniEksMin.crtaj:
                self.crtaj_scatter_value(self.tip_grafa.minimum.value, self.dto.satniEksMin, None)
                self.crtaj_scatter_value(self.tip_grafa.maksimum.value, self.dto.satniEksMax, None)
            #plot tocaka ovisno o flagu i validaciji
            self.crtaj_scatter_value(self.tip_grafa.midline.value, self.dto.satniVOK, 1000)
            self.crtaj_scatter_value(self.tip_grafa.midline.value, self.dto.satniVBAD, -1000)
            self.crtaj_scatter_value(self.tip_grafa.midline.value, self.dto.satniNVOK, 1)
            self.crtaj_scatter_value(self.tip_grafa.midline.value, self.dto.satniNVBAD, -1)
            self.statusGlavniGraf = True
        elif self.tip_grafa is MinutniEnum:
            #midline plot
            frejm = self.data[self.gKanal]
            x = list(frejm.index)
            y = list(frejm[self.tip_grafa.midline.value])
            self.crtaj_line(x, y, self.dto.minutniMidline)
            #plot tocaka ovisno o flagu i validaciji
            self.crtaj_scatter_value(self.tip_grafa.midline.value, self.dto.minutniVOK, 1000)
            self.crtaj_scatter_value(self.tip_grafa.midline.value, self.dto.minutniVBAD, -1000)
            self.crtaj_scatter_value(self.tip_grafa.midline.value, self.dto.minutniNVOK, 1)
            self.crtaj_scatter_value(self.tip_grafa.midline.value, self.dto.minutniNVBAD, -1)
            self.statusGlavniGraf = True
        elif self.tip_grafa is ZeroEnum:
            #priprema podataka za crtanje
            tocke = self.pripremi_zero_span_podatke_za_crtanje()
            #midline (plot je drugacije definiran zbog pickera)
            self.axes.plot(tocke['x'],
                           tocke['y'],
                           linestyle = self.dto.zeroMidline.lineStyle,
                           linewidth = self.dto.zeroMidline.lineWidth,
                           color = self.dto.zeroMidline.color,
                           zorder = self.dto.zeroMidline.zorder,
                           label = self.dto.zeroMidline.label,
                           picker = 5)
            #ok values
            if len(tocke['xok']) > 0:
                self.crtaj_scatter(tocke['xok'], tocke['yok'], self.dto.zeroVOK)
            #bad values
            if len(tocke['xbad']) > 0:
                self.crtaj_scatter(tocke['xbad'], tocke['ybad'], self.dto.zeroVBAD)
            #warning lines?
            if self.dto.zeroWarning1.crtaj:
                self.crtaj_line(tocke['x'], tocke['warningUp'], self.dto.zeroWarning1)
                self.crtaj_line(tocke['x'], tocke['warningLow'], self.dto.zeroWarning2)
            #fill
            ledge, hedge = self.axes.get_ylim() #y granice canvasa za fill
            if self.dto.zeroFill1.crtaj:
                self.crtaj_fill(tocke['x'], tocke['warningLow'], tocke['warningUp'], self.dto.zeroFill1)
                self.crtaj_fill(tocke['x'], tocke['warningUp'], hedge, self.dto.zeroFill2)
                self.crtaj_fill(tocke['x'], ledge, tocke['warningLow'], self.dto.zeroFill2)
            self.statusGlavniGraf = True
        elif self.tip_grafa is SpanEnum:
            #priprema podataka za crtanje
            tocke = self.pripremi_zero_span_podatke_za_crtanje()
            #midline (plot je drugacije definiran zbog pickera)
            self.axes.plot(tocke['x'],
                           tocke['y'],
                           linestyle = self.dto.spanMidline.lineStyle,
                           linewidth = self.dto.spanMidline.lineWidth,
                           color = self.dto.spanMidline.color,
                           zorder = self.dto.spanMidline.zorder,
                           label = self.dto.spanMidline.label,
                           picker = 5)
            #ok values
            if len(tocke['xok']) > 0:
                self.crtaj_scatter(tocke['xok'], tocke['yok'], self.dto.spanVOK)
            #bad values
            if len(tocke['xbad']) > 0:
                self.crtaj_scatter(tocke['xbad'], tocke['ybad'], self.dto.spanVBAD)
            #warning lines?
            if self.dto.zeroWarning1.crtaj:
                self.crtaj_line(tocke['x'], tocke['warningUp'], self.dto.spanWarning1)
                self.crtaj_line(tocke['x'], tocke['warningLow'], self.dto.spanWarning2)
            #fill
            ledge, hedge = self.axes.get_ylim() #y granice canvasa za fill
            if self.dto.zeroFill1.crtaj:
                self.crtaj_fill(tocke['x'], tocke['warningLow'], tocke['warningUp'], self.dto.spanFill1)
                self.crtaj_fill(tocke['x'], tocke['warningUp'], hedge, self.dto.spanFill2)
                self.crtaj_fill(tocke['x'], ledge, tocke['warningLow'], self.dto.spanFill2)
            self.statusGlavniGraf = True
################################################################################
    def crtaj_pomocne(self, popis):
        """
        Metoda za crtanje pomocnih grafova. Ulazni parametar popis je set id
        oznaka programa mjerenja. Ulazni parametar tip, definira tip grafa
        (satni ili minutni)
        """
        for key in popis:
            frejm = self.data[key]
            x = list(frejm.index)
            y = list(frejm[self.tip_grafa.midline.value])
            self.axes.plot(x,
                           y,
                           marker=self.dto.dictPomocnih[key].markerStyle,
                           markersize=self.dto.dictPomocnih[key].markerSize,
                           linestyle=self.dto.dictPomocnih[key].lineStyle,
                           linewidth=self.dto.dictPomocnih[key].lineWidth,
                           color=self.dto.dictPomocnih[key].color,
                           zorder=self.dto.dictPomocnih[key].zorder,
                           label=self.dto.dictPomocnih[key].label)
################################################################################
    def crtaj_oznake_temperature(self, tempMin, tempMax):
        """
        Crtanje oznaka za temperaturu kontejnera ako su izvan zadanih granica
        """
        if self.tip_grafa is SatniEnum or self.tip_grafa is MinutniEnum:
            if self.tKontejner in self.data.keys():
                frejm = self.data[self.tKontejner]
                frejm = frejm[frejm['flag'] > 0]
                if len(frejm):
                    overlimit = frejm[frejm[self.tip_grafa.midline.value] > tempMax]
                    underlimit = frejm[frejm[self.tip_grafa.midline.value] < tempMin]
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
################################################################################
    def setup_ticks(self):
        """
        Postavljanje pozicije i formata tickova x osi.
        """
        if self.tip_grafa is SatniEnum:
            tickovi = pomocne_funkcije.pronadji_tickove_satni(self.pocetnoVrijeme, self.zavrsnoVrijeme)
        elif self.tip_grafa is MinutniEnum:
            tickovi = pomocne_funkcije.pronadji_tickove_minutni(self.pocetnoVrijeme, self.zavrsnoVrijeme)
        elif self.tip_grafa is ZeroEnum or self.tip_grafa is SpanEnum:
            tickovi = pomocne_funkcije.pronadji_tickove_zero_span(self.pocetnoVrijeme, self.zavrsnoVrijeme)

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
            label.set_rotation(30)
            label.set_fontsize(8)
################################################################################
    def crtaj_scatter(self, x, y, dto):
        """
        pomocna funkcija za crtanje scatter grafova
        x, y, su liste kooridinata, dto je objekt koji sadrzi izgled
        """
        self.axes.plot(x,
                       y,
                       marker = dto.markerStyle,
                       markersize = dto.markerSize,
                       linestyle = 'None',
                       color = dto.color,
                       zorder = dto.zorder,
                       label = dto.label)
################################################################################
    def crtaj_line(self, x, y, dto):
        """
        pomocna funkcija za crtanje line grafova
        x, y su liste kooridinata, dto je objekt koji sadrzi izgled
        """
        self.axes.plot(x,
                       y,
                       linestyle = dto.lineStyle,
                       linewidth = dto.lineWidth,
                       color = dto.color,
                       zorder = dto.zorder,
                       label = dto.label)
################################################################################
    def crtaj_fill(self, x, y1, y2, dto):
        """
        pomocna funkcija za crtanje fill grafova
        x definira x os, y1 i y2 su granice izmedju kojih se sjenca,
        dto je konfig objekt sa opisom boje itd."""
        self.axes.fill_between(x,
                               y1,
                               y2,
                               color = dto.color,
                               zorder = dto.zorder,
                               label = dto.label)
################################################################################
    def pripremi_zero_span_podatke_za_crtanje(self):
        """Pripremanje podataka za crtanje zero/span. Funkcija vraca dictionary
        sa podacima koji se dalje koriste za crtanje"""
        #priprema podataka za crtanje
        frejm = self.data[self.gKanal]
        x = list(frejm.index) #svi indeksi
        y = list(frejm[self.tip_grafa.midline.value]) #sve vrijednosti
        warningUp = list(frejm[self.tip_grafa.warningHigh.value]) #warning up
        warningLow = list(frejm[self.tip_grafa.warningLow.value]) #warning low
        #pronalazak samo ok tocaka
        tempfrejm = self.data[self.gKanal].copy()
        okTocke = tempfrejm[tempfrejm[self.tip_grafa.midline.value] <= tempfrejm[self.tip_grafa.warningHigh.value]]
        okTocke = okTocke[okTocke[self.tip_grafa.midline.value] >= okTocke[self.tip_grafa.warningLow.value]]
        xok = list(okTocke.index)
        yok = list(okTocke[self.tip_grafa.midline.value])
        #pronalazak losih tocaka
        tempfrejm = self.data[self.gKanal].copy()
        badOver = tempfrejm[tempfrejm[self.tip_grafa.midline.value] > tempfrejm[self.tip_grafa.warningHigh.value]]
        tempfrejm = self.data[self.gKanal].copy()
        badUnder = tempfrejm[tempfrejm[self.tip_grafa.midline.value] < tempfrejm[self.tip_grafa.warningLow.value]]
        badTocke = badUnder.append(badOver)
        badTocke.sort()
        badTocke.drop_duplicates(subset='vrijeme',
                                 take_last=True,
                                 inplace=True) # za svaki slucaj ako dodamo 2 ista indeksa
        xbad = list(badTocke.index)
        ybad = list(badTocke[self.tip_grafa.midline.value])

        return {'x':x,
                'y':y,
                'warningUp':warningUp,
                'warningLow':warningLow,
                'xok':xok,
                'yok':yok,
                'xbad':xbad,
                'ybad':ybad}
################################################################################
    def crtaj_scatter_value(self, komponenta, dto, flag):
        """
        Pomocna funkcija za crtanje scatter tipa grafa (samo tocke).
        -komponenta je opisni string ()
        -dto je grafDTO objekt
        -flag je int vrijednost flaga za razlikovanje validacije ili None (za sve
        tocke neovisno o flagu)

        P.S.
        Funkcija ne poziva draw() metodu canvasa. Tu metodu bi trebala pozvati glavna
        funkcija za crtanje.
        """
        frejm = self.data[self.gKanal]
        if flag != None:
            frejm = frejm[frejm['flag'] == flag]
        x = list(frejm.index)
        #crtaj samo ako ima podataka
        if len(x) > 0:
            if komponenta == 'min':
                y = list(frejm['min'])
            elif komponenta == 'max':
                y = list(frejm['max'])
            elif komponenta == 'koncentracija':
                y = list(frejm['koncentracija'])
            elif komponenta == 'avg':
                y = list(frejm['avg'])
            else:
                return
            #naredba za plot
            self.crtaj_scatter(x, y, dto)
            self.statusGlavniGraf = True
################################################################################
    def initialize_interaction(self):
        """Setup inicijalnih postavki interakcije sa grafom.
        (zoom, cursor, span selector, pick)
        """
        #caller id za pick callbackove
        self.cid1 = None
        self.cid2 = None
        #definicija izgleda mpl widget elemenata - zoom
        self.zoomBoxInfo = dict(facecolor = 'yellow',
                                edgecolor = 'black',
                                alpha = 0.5,
                                fill = True)
        #definicija izgleda mpl widget elemenata - span selector
        self.spanBoxInfo = dict(alpha = 0.3, facecolor = 'yellow')
        #zoom implement, inicijalizacija rectangle selectora za zoom
        self.zoomSelector = RectangleSelector(self.axes,
                                              self.rect_zoom,
                                              drawtype = 'box',
                                              rectprops = self.zoomBoxInfo)
        self.zoomSelector.set_active(False)
        #cursor implement, inicijalizacija pomocnih lijija cursora
        self.cursorAssist = Cursor(self.axes, useblit = True, color = 'tomato', linewidth = 1)
        self.cursorAssist.visible = False
        #span selector, inicijalizacija span selectora (izbor vise tocaka po x osi)
        self.spanSelector = SpanSelector(self.axes,
                                         self.span_select,
                                         direction = 'horizontal',
                                         useblit = True,
                                         rectprops = self.spanBoxInfo)
        self.spanSelector.visible = False
################################################################################
    def rect_zoom(self, eclick, erelease):
        """
        Callback funkcija za rectangle zoom canvasa. Funkcija lovi click i release
        evente (rubovi kvadrata) te povecava izabrani dio slike preko cijelog
        canvasa.
        """
        x = sorted([eclick.xdata, erelease.xdata])
        y = sorted([eclick.ydata, erelease.ydata])
        #set nove granice osi za sve axese
        for ax in self.fig.axes:
            ax.set_xlim(x)
            ax.set_ylim(y)
        #redraw
        self.draw()

        #sinhronizacija zooma x osi zero i span grafa.
        if self.tip_grafa is ZeroEnum or self.tip_grafa is SpanEnum:
            self.emit(QtCore.SIGNAL('sync_x_zoom(PyQt_PyObject)'), x)
################################################################################
    def on_pick(self, event):
        """
        Resolve pick eventa za satni i minutni graf.
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
            if self.tip_grafa is SatniEnum:
                xpoint = pomocne_funkcije.zaokruzi_vrijeme(xpoint, 3600)
            elif self.tip_grafa is MinutniEnum:
                xpoint = pomocne_funkcije.zaokruzi_vrijeme(xpoint, 60)
            else:
                raise AttributeError('Krivi tip grafa')
            #aktualna konverzija iz datetime.datetime objekta u pandas.tislib.Timestamp
            xpoint = pd.to_datetime(xpoint)
            #bitno je da zaokruzeno vrijeme nije izvan granica frejma (izbjegavnjanje index errora)
            if xpoint >= self.zavrsnoVrijeme:
                xpoint = self.zavrsnoVrijeme
            if xpoint <= self.pocetnoVrijeme:
                xpoint = self.pocetnoVrijeme
            #highlight selected point - kooridinate ako nedostaju podaci
            if xpoint in list(self.data[self.gKanal].index):
                ypoint = self.data[self.gKanal].loc[xpoint, self.tip_grafa.midline.value]
            else:
                miny = self.data[self.gKanal][self.tip_grafa.midline.value].min()
                maxy = self.data[self.gKanal][self.tip_grafa.midline.value].max()
                ypoint = (miny + maxy)/2
            """
            Ponasanje ovisno o pritisnutom gumbu na misu.
            """
            if event.button == 1:
                if self.tip_grafa is SatniEnum:
                    #left click, naredi crtanje minutnog i highlight tocku
                    self.emit(QtCore.SIGNAL('crtaj_minutni_graf(PyQt_PyObject)'), xpoint) #crtanje minutnog
                    self.highlight_pick((xpoint, ypoint), self.highlightSize) #highlight odabir, size pointa
            elif event.button == 2:
                tekst = self.setup_annotation_text(xpoint)
                offset = self.setup_annotation_offset(event)
                datacords = (xpoint, ypoint)
                self.annotate_pick(datacords, offset, tekst)
            elif event.button == 3:
                loc = QtGui.QCursor.pos() #lokacija klika
                self.show_context_menu(loc, xpoint, xpoint) #interval koji treba promjeniti
################################################################################
    def on_pick_point(self, event):
        """
        Callback za pick na ZERO ili SPAN grafu.
        """
        #definiraj x i y preko izabrane tocke
        x = self.data[self.gKanal].index[event.ind[0]]
        y = self.data[self.gKanal].loc[x, self.tip_grafa.midline.value]
        minD = self.data[self.gKanal].loc[x, self.tip_grafa.warningLow.value]
        maxD = self.data[self.gKanal].loc[x, self.tip_grafa.warningHigh.value]
        # ako postoje vise istih indeksa, uzmi zadnji
        if type(y) is pd.core.series.Series:
            y = y[-1]
            minD = minD[-1]
            maxD = maxD[-1]
        if y >= minD and y<= maxD:
            status = 'Dobar'
        else:
            status = 'Ne valja'

        if event.mouseevent.button == 1 or event.mouseevent.button == 2:
            #left click or middle click
            #update labels
            argList = {'xtocka': str(x),
                       'ytocka': str(y),
                       'minDozvoljenoOdstupanje': str(minD),
                       'maxDozvoljenoOdstupanje': str(maxD),
                       'status': str(status)}
            #highlight tocku
            self.highlight_pick((x, y), self.highlightSize)
            #emit update vrijednosti
            self.updateaj_labele_na_panelu('pick', argList)
################################################################################
    def pick_nearest(self, argList):
        """
        Nakon sto netko na komplementarnom grafu izabere index, pronadji najblizi
        te ga highlitaj i updateaj labele na panelu

        argList je dict

        argList = {'xtocka': str(x),
                   'ytocka': str(y),
                   'minDozvoljenoOdstupanje': str(minD),
                   'maxDozvoljenoOdstupanje': str(maxD),
                   'status': str(status)}
        """
        if self.statusGlavniGraf:
            ind = pomocne_funkcije.pronadji_najblizi_time_indeks(self.data[self.gKanal].index, argList['xtocka'])
            x = self.data[self.gKanal].index[ind]
            y = self.data[self.gKanal].loc[x, self.tip_grafa.midline.value]
            minD = self.data[self.gKanal].loc[x, self.tip_grafa.warningLow.value]
            maxD = self.data[self.gKanal].loc[x, self.tip_grafa.warningHigh.value]
            # ako postoje vise istih indeksa, uzmi zadnji
            if type(y) is pd.core.series.Series:
                y = y[-1]
                minD = minD[-1]
                maxD = maxD[-1]
            if y >= minD and y<= maxD:
                status = 'Dobar'
            else:
                status = 'Ne valja'

            #newArgList = [str(x), str(y), str(minD), str(maxD), str(status)]
            newArgList = {'xtocka': str(x),
                          'ytocka': str(y),
                          'minDozvoljenoOdstupanje': str(minD),
                          'maxDozvoljenoOdstupanje': str(maxD),
                          'status': str(status)}

            self.highlight_pick((x, y), self.highlightSize)
            self.updateaj_labele_na_panelu('normal', newArgList)
################################################################################
    def updateaj_labele_na_panelu(self, tip, argList):
        """
        update labela na zero span panelu (istovremeno i trigger za pick najblize
        tocke na drugom canvasu, npr. click na zero canvasu triggera span canvas...)
        """
        if self.tip_grafa is ZeroEnum:
            if tip =='pick':
                self.emit(QtCore.SIGNAL('pick_nearest(PyQt_PyObject)'),argList)
                self.emit(QtCore.SIGNAL('prikazi_info_zero(PyQt_PyObject)'),argList)
            else:
                self.emit(QtCore.SIGNAL('prikazi_info_zero(PyQt_PyObject)'),argList)
        elif self.tip_grafa is SpanEnum:
            if tip == 'pick':
                self.emit(QtCore.SIGNAL('pick_nearest(PyQt_PyObject)'),argList)
                self.emit(QtCore.SIGNAL('prikazi_info_span(PyQt_PyObject)'),argList)
            else:
                self.emit(QtCore.SIGNAL('prikazi_info_span(PyQt_PyObject)'),argList)
################################################################################
    def setup_annotation_offset(self, event):
        """
        Funkcija postavlja annotation offset ovisno o polozaju klika na canvas.
        """
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
        return (clickedx, clickedy)
################################################################################
    def setup_annotation_text(self, xpoint):
        """
        Definiranje teksta za prikaz annotationa (sto ce biti unutar annotationa).
        Ulazni parametar je tocka za koju radimo annotation. Funkcija vraca string
        teksta annotationa.
        """
        if xpoint in list(self.data[self.gKanal].index):
            if self.tip_grafa is SatniEnum:
                yavg = self.data[self.gKanal].loc[xpoint, u'avg']
                ymin = self.data[self.gKanal].loc[xpoint, u'min']
                ymax = self.data[self.gKanal].loc[xpoint, u'max']
                ystatus = self.data[self.gKanal].loc[xpoint, u'status']
                ycount = self.data[self.gKanal].loc[xpoint, u'count']
                tekst = 'Vrijeme: '+str(xpoint)+'\nAverage: '+str(yavg)+'\nMin:'+str(ymin)+'\nMax:'+str(ymax)+'\nStatus:'+str(ystatus)+'\nCount:'+str(ycount)
            elif self.tip_grafa is MinutniEnum:
                ykonc = self.data[self.gKanal].loc[xpoint, u'koncentracija']
                ystat = self.data[self.gKanal].loc[xpoint, u'status']
                yflag = self.data[self.gKanal].loc[xpoint, u'flag']
                tekst = 'Vrijeme: '+str(xpoint)+'\nKoncentracija: '+str(ykonc)+'\nStatus:'+str(ystat)+'\nFlag:'+str(yflag)
        else:
            tekst = 'Vrijeme: '+str(xpoint)+'\nNema podataka'
        return tekst
################################################################################
    def span_select(self, xmin, xmax):
        """
        Metoda je povezana sa span selektorom (ako je inicijaliziran).
        Metoda je zaduzena da prikaze kontekstni dijalog za promjenu flaga
        na mjestu gdje "releasamo" ljevi klik za satni i minutni graf.

        t1 i t2 su timestampovi, ali ih treba adaptirati iz matplotlib vremena u
        "zaokruzene" pandas timestampove. (na minutnom grafu se zaokruzuje na najblizu
        minutu, dok na satnom na najblizi sat)
        """
        if self.statusGlavniGraf: #glavni graf mora biti nacrtan
            #konverzija ulaznih vrijednosti u pandas timestampove
            t1 = matplotlib.dates.num2date(xmin)
            t2 = matplotlib.dates.num2date(xmax)
            t1 = datetime.datetime(t1.year, t1.month, t1.day, t1.hour, t1.minute, t1.second)
            t2 = datetime.datetime(t2.year, t2.month, t2.day, t2.hour, t2.minute, t2.second)
            #vremena se zaokruzuju
            if self.tip_grafa is SatniEnum:
                t1 = pomocne_funkcije.zaokruzi_vrijeme(t1, 3600)
                t2 = pomocne_funkcije.zaokruzi_vrijeme(t2, 3600)
            elif self.tip_grafa is MinutniEnum:
                t1 = pomocne_funkcije.zaokruzi_vrijeme(t1, 60)
                t2 = pomocne_funkcije.zaokruzi_vrijeme(t2, 60)
            t1 = pd.to_datetime(t1)
            t2 = pd.to_datetime(t2)

            #osiguranje da se ne preskoce granice glavnog kanala (izbjegavanje index errora)
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
################################################################################
    def show_context_menu(self, pos, tmin, tmax):
        """
        Metoda iscrtava kontekstualni meni sa opcijama za promjenom flaga
        na minutnom i satnom grafu.
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
        action1.triggered.connect(functools.partial(self.promjena_flaga, flag = 1000))
        action2.triggered.connect(functools.partial(self.promjena_flaga, flag = -1000))
        #prikazi menu na definiranoj tocki grafa
        menu.popup(pos)
################################################################################
    def promjena_flaga(self, flag = None):
        """
        Metoda sluzi za promjenu flaga
        ovisno o keyword argumentu tip.
        """
        #dohvati rubove intervala (spremljeni su u membere prilikom poziva dijaloga)
        tmin = self.__lastTimeMin
        tmax = self.__lastTimeMax
        if self.tip_grafa is SatniEnum:
            #pomak slicea da uhvati sve ciljane minutne podatke
            tmin = tmin - datetime.timedelta(minutes = 59)
            tmin = pd.to_datetime(tmin)
        if flag != None:
            arg = {'od': tmin,
                   'do': tmax,
                   'noviFlag': flag,
                   'kanal': self.gKanal}
            #generalni emit za promjenu flaga
            self.emit(QtCore.SIGNAL('promjeni_flag(PyQt_PyObject)'), arg)
################################################################################
    def connect_pick_evente(self):
        """mpl connection ovisno o tipu canvasa. Pick tocke ili pick bilo gdje
        na grafu."""
        if self.tip_grafa is SatniEnum or self.tip_grafa is MinutniEnum:
            self.cid1 = self.mpl_connect('button_press_event', self.on_pick)
        elif self.tip_grafa is ZeroEnum or self.tip_grafa is SpanEnum:
            self.cid2 = self.mpl_connect('pick_event', self.on_pick_point)
        else:
            raise AttributeError('Pogresni tip grafa')
################################################################################
    def disconnect_pick_evente(self):
        """Opceniti disconnect pick eventa. Pick eventi se trebaju odspojiti prilikom
        zoom akcije i prilikom izbora vise tocaka uz pomoc span selektora (izbjegavanje
        konfliktnih signala)."""
        if self.cid1 != None:
            self.mpl_disconnect(self.cid1)
            self.cid1 = None
        if self.cid2 != None:
            self.mpl_disconnect(self.cid2)
            self.cid2 = None
################################################################################
    def set_interaction_mode(self, zoom, cursor, span):
        """
        Toggle nacina interakcije, ovisno o zeljenom nacinu interakcije sa canvasom.
        zoom --> boolean
        cursor --> boolean
        span --> boolean
        """
        #set up pick callbacks ovisno o tipu grafa
        self.disconnect_pick_evente()
        self.connect_pick_evente()
        if zoom:
            #zoom on, all else off
            self.zoomSelector.set_active(True)
            self.cursorAssist.visible = False
            self.spanSelector.visible = False
            self.disconnect_pick_evente()
        else:
            #zoom off
            self.zoomSelector.set_active(False)
            if cursor:
                self.cursorAssist.visible = True
            else:
                self.cursorAssist.visible = False
            if span:
                self.spanSelector.visible = True
                self.disconnect_pick_evente()
            else:
                self.spanSelector.visible = False
################################################################################
    def full_zoom_out(self):
        """
        Reset granica x i y osi da pokrivaju isti raspon kao i originalna slika.
        Full zoom out.

        vrijednosti su spremljene u memberima u obliku tuple
        self.xlim_original --> (xmin, xmax)
        self.ylim_original --> (ymin, ymax)
        """
        self.axes.set_xlim(self.xlim_original)
        self.axes.set_ylim(self.ylim_original)
        #nacrtaj promjenu
        self.draw()
################################################################################
    def setup_limits(self):
        """
        Prosirivanje granica grafa da ticke nisu na rubu.
        Pomak ovisi o tipu grafa (1 sat, 5 minuta ili 1 dan)
        Konacne granice se spremaju u member xlim_original i ylim_original
        radi implementacije zoom out metode.
        """
        #dohvati trenutne granice x osi
        xmin, xmax = self.axes.get_xlim()
        xmin = pomocne_funkcije.mpl_time_to_pandas_datetime(xmin)
        xmax = pomocne_funkcije.mpl_time_to_pandas_datetime(xmax)

        #odmakni x granice za specificni interval ovisno o tipu
        if self.tip_grafa is SatniEnum:
            tmin, tmax = pomocne_funkcije.prosiri_granice_grafa(xmin, xmax, 60)
        elif self.tip_grafa is MinutniEnum:
            tmin, tmax = pomocne_funkcije.prosiri_granice_grafa(xmin, xmax, 5)
        elif self.tip_grafa is ZeroEnum or self.tip_grafa is SpanEnum:
            tmin, tmax = pomocne_funkcije.prosiri_granice_grafa(xmin, xmax, 1440)
        else:
            tmin, tmax = xmin, xmax
        #set granice za max zoom out
        self.xlim_original = (tmin, tmax)
        self.ylim_original = self.axes.get_ylim()
        #set granice grafa
        self.axes.set_xlim(self.xlim_original)
        self.axes.set_ylim(self.ylim_original)
################################################################################
    def toggle_ticks(self, x):
        """
        Toggle minor tickova on i off ovisno o ulaznoj vrijednosti x (boolean).
        """
        if x and self.statusGlavniGraf:
            self.axes.minorticks_on()
        else:
            self.axes.minorticks_off()
        self.draw()
################################################################################
    def toggle_grid(self, x):
        """
        Toggle grida on i off, ovisno o ulaznoj vrijednosti x (boolean)
        """
        if x and self.statusGlavniGraf:
            self.axes.grid(True)
        else:
            self.axes.grid(False)
        self.draw()
################################################################################
    def toggle_legend(self, x):
        """
        Toggle legende on i off, ovisno o ulaznoj vrijednosti x (boolean)
        """
        if self.legenda is not None:
            if x and self.statusGlavniGraf:
                self.legenda.set_visible(True)
            else:
                self.legenda.set_visible(False)
        self.draw()
################################################################################
    def setup_legend(self):
        """
        Setup legende na canvas. Lokacija, stil, alpha...
        """
        self.legenda = self.axes.legend(loc = 1,
                                        fontsize = 8,
                                        fancybox = True)
        self.legenda.get_frame().set_alpha(0.8)
################################################################################
    def emit_request_za_podacima(self, arg):
        """
        Slanje zahtjeva za podacima. Kontroler vraca trazene podatke u member
        self.data. Opis zahtjeva (sto se tocno trazi) zadan je preko ulaznog argumenta
        arg (specificni dictionary podataka, ovisno o tipu grafa).
        """
        if self.tip_grafa is SatniEnum:
            self.emit(QtCore.SIGNAL('dohvati_agregirani_frejm(PyQt_PyObject)'), arg)
        elif self.tip_grafa is MinutniEnum:
            self.emit(QtCore.SIGNAL('dohvati_minutni_frejm(PyQt_PyObject)'), arg)
        elif self.tip_grafa is ZeroEnum:
            self.emit(QtCore.SIGNAL('request_zero_frejm(PyQt_PyObject)'), arg)
        elif self.tip_grafa is SpanEnum:
            self.emit(QtCore.SIGNAL('request_span_frejm(PyQt_PyObject)'), arg)
        else:
            raise AttributeError('Pogresni tip grafa')
################################################################################
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
################################################################################
    def make_annotation(self, point, offs, tekst):
        """Annotation instance object, pozicija na grafu"""
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
################################################################################
    def highlight_pick(self, tpl, size):
        """
        crta highlight tocku na grafu sa koridinatama tpl = (x, y), velicine size
        """
        x, y = tpl
        if self.statusHighlight:
            if not tpl == self.lastHighlight:
                self.axes.lines.remove(self.highlight[0])
                self.make_highlight(x, y, size)
        else:
            self.make_highlight(x, y, size)

        self.draw()
################################################################################
    def make_highlight(self, x, y, size):
        """
        napravi instancu highlight tocke na kooridinati x, y.
        Velicina markera je definirana sa ulaznim parametrom size
        """
        self.highlight = self.axes.plot(x,
                                        y,
                                        marker = 'o',
                                        markersize = int(size),
                                        color = 'yellow',
                                        alpha = 0.5,
                                        zorder = 10)
        self.lastHighlight = (x, y)
        self.statusHighlight = True
################################################################################
    def clear_graf(self):
        """
        clear grafa
        """
        self.data = {} #spremnik za frejmove (ucitane)
        self.statusGlavniGraf = False
        self.statusAnnotation = False
        self.statusHighlight = False
        self.lastHighlight = (None, None)
        self.lastAnnotation = None

        self.axes.clear()

        #redo Axes labels
        self.axes.set_xlabel('Vrijeme')
        self.axes.set_ylabel(self.tip_grafa.tip.value)

        self.draw()
################################################################################
    def sync_x_zoom(self, x):
        """
        Postavi novi raspon x osi. Metoda sluzi za sinhronizaciju zooma po x osi
        za zero i span graf
        """
        for ax in self.fig.axes:
            ax.set_xlim(x)
        self.draw()
################################################################################
    def clear_zero_span(self):
        """
        clear grafa i replace sa porukom da nema dostupnih podataka
        """
        self.clear_graf()
        self.axes.text(0.5,
                       0.5,
                       'Nije moguce pristupiti podacima',
                       horizontalalignment='center',
                       verticalalignment='center',
                       fontsize = 8,
                       transform = self.axes.transAxes)
        self.draw()
################################################################################
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
################################################################################
    def set_agregirani_kanal(self, ulaz):
        """
        BITNA METODA! - mehanizam s kojim se ucitavaju frejmovi za crtanje.
        -metoda crtaj trazi od kontrolera podatke
        -ovo je predvidjeni slot gdje kontroler vraca trazene podatke
        - ulaz je mapa koja sadrzi kanalId i agregirani frejm

        metoda postavlja agregirani frejm u self.data
        ulaz['kanal'] -> int, 'ime' kanala
        ulaz['agregirani'] -> pandas dataframe, agregirani podaci
        """
        self.data[ulaz['kanal']] = ulaz['agregirani']
################################################################################
    def set_zero_span_frejm(self, ulaz):
        """
        BITNA METODA! - mehanizam s kojim se ucitavaju frejmovi za crtanje.
        -metoda crtaj trazi od kontrolera podatke
        -ovo je predvidjeni slot gdje kontroler vraca trazene podatke
        - ulaz je mapa koja sadrzi kanalId i zero/span graf

        metoda postavlja zero (ili span) frejm u self.data
        ulaz['kanal'] -> int, 'ime' kanala
        ulaz['zsFrejm'] -> pandas dataframe, zero span podaci
        """
        self.data[ulaz['kanal']] = ulaz['zsFrejm']
################################################################################
################################################################################