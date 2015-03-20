# -*- coding: utf-8 -*-
"""
Created on Mon Feb  2 11:22:25 2015

@author: User

Klasa (canvas) za prikaz ZERO ili SPAN vrijednosti.
"""
from PyQt4 import QtCore

import pomocne_funkcije #import pomocnih funkcija
import opceniti_canvas #import opcenitog (abstract) canvasa
###############################################################################
###############################################################################
class ZeroSpanGraf(opceniti_canvas.MPLCanvas):
    """
    Klasa za prikaz Zero vrijednosti
    """
    def __init__(self, *args, tip = None, lok = None, **kwargs):
        opceniti_canvas.MPLCanvas.__init__(self, *args, **kwargs)

        self.data = None

        self.statusGlavniGraf = False
        self.statusHighlight = False
        #kooridinate zadnjeg highlighta
        self.lastHighlight = (None, None)


        #tip odredjuje da li je ovo zero ili span graf
        self.tipGrafa = tip
        #lokacija odredjuje da li je graf na vrhu ili dnu ('top', 'bottom')
        self.lokacija = lok

        """
        SETTER POZICIJE GRAFA
        - pomicanje canvasa
        - pomicanje kooridinatnih osi
        - odredjivanje na kojoj osi se crtaju tickovi
        """
        if self.lokacija == 'top':
            #prebaci lokaciju tickova
            self.axes.xaxis.set_ticks_position('top')
            self.axes.figure.subplots_adjust(bottom = 0.02)
            self.axes.figure.subplots_adjust(right = 0.98)
        else:
            self.axes.xaxis.set_ticks_position('bottom')
            self.axes.figure.subplots_adjust(top = 0.98)
            self.axes.figure.subplots_adjust(right = 0.98)
###############################################################################
    def crtaj(self, ulaz):
        """
        ulaz je arg. lista
        ulaz[0] = frejm
        ulaz[1] = grafSettingsDTO
        ulaz[2] = raspon x osi (xmin, xmax)
        """
        self.axes.clear()

        self.statusGlavniGraf = False
        self.statusHighlight = False

        #kooridinate zadnjeg highlighta
        self.lastHighlight = (None, None)

        self.updateaj_labele_na_panelu('normal', ['','','','',''])

        self.data = ulaz[0]
        self.dto = ulaz[1]
        self.raspon = ulaz[2]

        #prvi ulazni datum
        beginpoint = self.raspon[0]
        #zadnji ulazni datum
        endpoint = self.raspon[1]

        #priprema podataka za crtanje
        x = list(self.data.index) #svi indeksi
        y = list(self.data['vrijednost']) #sve vrijednosti
        wu = list(self.data['maxDozvoljeno']) #warning up
        wl = list(self.data['minDozvoljeno']) #warning low
        #pronalazak samo ok tocaka
        frejm = self.data.copy()
        okTocke = frejm[frejm['vrijednost'] <= frejm['maxDozvoljeno']]
        okTocke = okTocke[okTocke['vrijednost'] >= okTocke['minDozvoljeno']]
        xok = list(okTocke.index)
        yok = list(okTocke['vrijednost'])
        #pronalazak losih tocaka
        frejm = self.data.copy()
        badTocke = frejm[frejm['vrijednost'] > frejm['maxDozvoljeno']]
        badTocke = badTocke[badTocke['vrijednost'] < badTocke['minDozvoljeno']]
        xbad = list(badTocke.index)
        ybad = list(badTocke['vrijednost'])

        if self.tipGrafa == 'span' and len(x) > 0:
            #midline
            self.axes.plot(x,
                           y,
                           linestyle = self.dto.spanMidline.lineStyle,
                           linewidth = self.dto.spanMidline.lineWidth,
                           color = self.dto.spanMidline.color,
                           zorder = self.dto.spanMidline.zorder,
                           label = self.dto.spanMidline.label,
                           picker = 5)
            #ok values
            if len(xok) > 0:
                self.crtaj_scatter_zs(xok, yok, self.dto.spanVOK)
            #bad values
            if len(xbad) > 0:
                self.crtaj_scatter_zs(xbad, ybad, self.dto.spanVBAD)
            #warning lines?
            if self.dto.spanWarning1.crtaj:
                self.crtaj_line_zs(x, wu, self.dto.spanWarning1)
                self.crtaj_line_zs(x, wl, self.dto.spanWarning2)
            #fill
            self.draw()
            ledge, hedge = self.axes.get_ylim() #y granice canvasa za fill
            if self.dto.spanFill1.crtaj:
                self.crtaj_fill_zs(x, wl, wu, self.dto.spanFill1)
                self.crtaj_fill_zs(x, wu, hedge, self.dto.spanFill2)
                self.crtaj_fill_zs(x, ledge, wl, self.dto.spanFill2)
            self.statusGlavniGraf = True
        elif self.tipGrafa == 'zero' and len(x) > 0:
            #midline
            self.axes.plot(x,
                           y,
                           linestyle = self.dto.zeroMidline.lineStyle,
                           linewidth = self.dto.zeroMidline.lineWidth,
                           color = self.dto.zeroMidline.color,
                           zorder = self.dto.zeroMidline.zorder,
                           label = self.dto.zeroMidline.label,
                           picker = 5)
            #ok values
            if len(xok) > 0:
                self.crtaj_scatter_zs(xok, yok, self.dto.zeroVOK)
            #bad values
            if len(xbad) > 0:
                self.crtaj_scatter_zs(xbad, ybad, self.dto.zeroVBAD)
            #warning lines?
            if self.dto.zeroWarning1.crtaj:
                self.crtaj_line_zs(x, wu, self.dto.zeroWarning1)
                self.crtaj_line_zs(x, wl, self.dto.zeroWarning2)
            #fill
            self.draw()
            ledge, hedge = self.axes.get_ylim() #y granice canvasa za fill
            if self.dto.zeroFill1.crtaj:
                self.crtaj_fill_zs(x, wl, wu, self.dto.zeroFill1)
                self.crtaj_fill_zs(x, wu, hedge, self.dto.zeroFill2)
                self.crtaj_fill_zs(x, ledge, wl, self.dto.zeroFill2)
            self.statusGlavniGraf = True

        #Axes labeli
        self.axes.set_xlabel('Vrijeme')
        self.axes.set_ylabel(self.tipGrafa.upper())
        #limit grafa
        self.axes.set_xlim((beginpoint, endpoint))
        self.setup_limits('zero')
        self.setup_ticks(self.data.index)

        self.draw()
#        #TODO! not implemented mozda i nije potrebno
#        self.setup_legend()
#        self.toggle_ticks()
#        self.toggle_grid()
#        self.toggle_legend()
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
                                        markersize = 1.5*self.dto.zeroVOK.markerSize,
                                        color = 'yellow',
                                        alpha = 0.5,
                                        zorder = 10)
        self.lastHighlight = (x, y)
        self.statusHighlight = True
###############################################################################
    def setup_ticks(self, x):
        """
        pozicija major tickova za zero/span graf. tickovi su na danima, format
        MM.DD
        """
        tickLoc, tickLab = pomocne_funkcije.sredi_xtickove_zerospan(x)
        self.axes.set_xticks(tickLoc)
        self.axes.set_xticklabels(tickLab)
###############################################################################
    def crtaj_scatter_zs(self, x, y, dto):
        """
        scatter type plot za zero/span graf
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
###############################################################################
    def crtaj_line_zs(self, x, y, dto):
        """
        line plot za zero/span graf
        x, y su liste kooridinata, dto je objekt koji sadrzi izgled
        """
        self.axes.plot(x,
                       y,
                       linestyle = dto.lineStyle,
                       linewidth = dto.lineWidth,
                       color = dto.color,
                       zorder = dto.zorder,
                       label = dto.label)
###############################################################################
    def crtaj_fill_zs(self, x, y1, y2, dto):
        """fill plot za zero/span graf"""
        self.axes.fill_between(x,
                               y1,
                               y2,
                               color = dto.color,
                               zorder = dto.zorder,
                               label = dto.label)
###############################################################################
    def on_pick_point(self, event):
        """
        pick callback, ali funkcionira samo ako se pickaju tocke na grafu
        """
        #definiraj x i y preko izabrane tocke
        x = self.data.index[event.ind[0]]
        y = self.data.loc[x, 'vrijednost']
        minD = self.data.loc[x, 'minDozvoljeno']
        maxD = self.data.loc[x, 'maxDozvoljeno']
        if y >= minD and y<= maxD:
            status = 'Dobar'
        else:
            status = 'Ne valja'

        if event.mouseevent.button == 1 or event.mouseevent.button == 2:
            #left click or middle click
            #update labels
            argList = [str(x), str(y), str(minD), str(maxD), str(status)]
            #highlight tocku
            self.highlight_pick((x, y))
            #emit update vrijednosti
            self.updateaj_labele_na_panelu('pick', argList)
###############################################################################
    def pick_nearest(self, argList):
        """
        Nakon sto netko na komplementarnom grafu izabere index, pronadji najblizi
        te ga highlitaj i updateaj labele na panelu
        """
        if self.statusGlavniGraf:
            ind = pomocne_funkcije.pronadji_najblizi_time_indeks(self.data.index, argList[0])
            x = self.data.index[ind]
            y = self.data.loc[x, 'vrijednost']
            minD = self.data.loc[x, 'minDozvoljeno']
            maxD = self.data.loc[x, 'maxDozvoljeno']
            if y >= minD and y<= maxD:
                status = 'Dobar'
            else:
                status = 'Ne valja'

            newArgList = [str(x), str(y), str(minD), str(maxD), str(status)]
            self.highlight_pick((x, y))
            self.updateaj_labele_na_panelu('normal', newArgList)
###############################################################################
    def updateaj_labele_na_panelu(self, tip, argList):
        if self.tipGrafa == 'zero':
            if tip =='pick':
                self.emit(QtCore.SIGNAL('zero_point_pick_update(PyQt_PyObject)'),argList)
                self.emit(QtCore.SIGNAL('zero_point_update(PyQt_PyObject)'),argList)
            else:
                self.emit(QtCore.SIGNAL('zero_point_update(PyQt_PyObject)'),argList)
        elif self.tipGrafa == 'span':
            if tip == 'pick':
                self.emit(QtCore.SIGNAL('span_point_pick_update(PyQt_PyObject)'),argList)
                self.emit(QtCore.SIGNAL('span_point_update(PyQt_PyObject)'),argList)
            else:
                self.emit(QtCore.SIGNAL('span_point_update(PyQt_PyObject)'),argList)
###############################################################################
    def clear_me(self):
        """
        clear grafa i replace sa porukom da nema dostupnih podataka
        """
        self.axes.clear()
        self.statusGlavniGraf = False
        self.statusHighlight = False
        self.lastHighlight = (None, None)
        self.axes.text(0.5,
                       0.5,
                       'Nemoguce pristupiti podacima',
                       horizontalalignment='center',
                       verticalalignment='center',
                       fontsize = 8,
                       transform = self.axes.transAxes)
        self.draw()
###############################################################################
    def rect_zoom(self, eclick, erelease):
        #TODO! reconnect and reimplement
        """
        REIMPLEMENTED!

        metoda odradjuje zoom na isti nacin kao i metoda definirana u super klasi
        samo uz jednu iznimku. emitira signal koji resizea x komponetu drugog tipa
        grafa.

        tj. zoom na zero grafu skalira x os span grafa i obrnuto.
        """
        #rubovi zoom prozora
        x = sorted([eclick.xdata, erelease.xdata])
        y = sorted([eclick.ydata, erelease.ydata])
        #reset granica osi
        for ax in self.fig.axes:
            ax.set_xlim(x)
            ax.set_ylim(y)
        #draw
        self.draw()

        if self.tipGrafa == 'zero':
            self.emit(QtCore.SIGNAL('zero_sync_x_zoom(PyQt_PyObject)'), x)
        elif self.tipGrafa == 'span':
            self.emit(QtCore.SIGNAL('span_sync_x_zoom(PyQt_PyObject)'), x)
###############################################################################
    def sync_x_zoom(self, x):
        """
        postavi novi raspon x osi.
        """
        for ax in self.fig.axes:
            ax.set_xlim(x)
        self.draw()
###############################################################################
###############################################################################
