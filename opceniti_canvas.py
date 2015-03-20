# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 08:04:32 2014

@author: User

Klasa definira opceniti matplotlib canvas za Qt framework.
Klasa je namjenjena da se subklasa u 2 canvasa. Agregirani (satni), te minutni canvas.
"""

from PyQt4 import QtGui #import djela Qt frejmworka
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas #import specificnog canvasa za Qt
from matplotlib.figure import Figure #import figure
from matplotlib.widgets import RectangleSelector, SpanSelector, Cursor

import pomocne_funkcije

###############################################################################
###############################################################################
class MPLCanvas(FigureCanvas):
    """
    Opcenita klasa za matplotlib canvas

    Bitne metode za overloadajne:
    -crtaj --> defiinra sto se crta
    -on_pick --> definira pick event
    -on_pick_point --> definira pick pickable pointa
    -span_select --> definira span selektor

    """
    def __init__(self, parent = None, width = 6, height = 5, dpi=100):
        self.fig = Figure(figsize = (width, height), dpi = dpi)
        self.axes = self.fig.add_subplot(111)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(
            self,
            QtGui.QSizePolicy.Expanding,
            QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        #originalne granice grafa, pregazi trenutnim vrijednositma naokn sto ih nacrtas
        self.xlim_original = (0.0, 1.0)
        self.ylim_original = (0.0, 1.0)

        #definicija izgleda mpl widget elemenata
        self.zoomBoxInfo = dict(facecolor = 'yellow',
                                edgecolor = 'black',
                                alpha = 0.5,
                                fill = True)

        self.spanBoxInfo = dict(alpha = 0.3, facecolor = 'yellow')

        #caller id za callbackove
        self.cid1 = None
        self.cid2 = None

        #boolean, informacija da li je nacrtan graf
        self.statusGlavniGraf = False

        #placeholder za legendu
        self.legenda = None

        #zoom implement
        self.zoomSelector = RectangleSelector(self.axes,
                                              self.rect_zoom,
                                              drawtype = 'box',
                                              rectprops = self.zoomBoxInfo)
        self.zoomSelector.set_active(False)

        #cursor implement
        self.cursorAssist = Cursor(self.axes, useblit = True, color = 'tomato', linewidth = 1)
        self.cursorAssist.visible = False

        #span selector
        self.spanSelector = SpanSelector(self.axes,
                                         self.span_select,
                                         direction = 'horizontal',
                                         useblit = True,
                                         rectprops = self.spanBoxInfo)
        self.spanSelector.visible = False

###############################################################################
    def crtaj(self):
        """overload specific method"""
        print('crtaj method, overload za specificni graf')
###############################################################################
    def rect_zoom(self, eclick, erelease):
        """
        Callback funkcija za rectangle zoom canvasa.
        """
        x = sorted([eclick.xdata, erelease.xdata])
        y = sorted([eclick.ydata, erelease.ydata])
        #set nove granice osi za sve axese
        for ax in self.fig.axes:
            ax.set_xlim(x)
            ax.set_ylim(y)
        #redraw
        self.draw()
###############################################################################
    def on_pick(self, event):
        print('on_pick method, overload for specific graph')
###############################################################################
    def on_pick_point(self, event):
        print('on_pick_point method, overload for specific graph')
###############################################################################
    def span_select(self, xmin, xmax):
        print('span select metoda, overload for specific graph')
###############################################################################
    def connect_pick_evente(self, tip):
        """mpl connection ovisno o tipu canvasa"""
        if tip == 'SATNI' or tip == 'MINUTNI':
            self.cid1 = self.mpl_connect('button_press_event', self.on_pick)
        elif tip == 'ZERO' or tip == 'SPAN':
            self.cid2 = self.mpl_connect('pick_event', self.on_pick_point)
###############################################################################
    def disconnect_pick_evente(self):
        """opceniti disconnect pick eventa"""
        if self.cid1 != None:
            self.mpl_disconnect(self.cid1)
            self.cid1 = None
        if self.cid2 != None:
            self.mpl_disconnect(self.cid2)
            self.cid2 = None
###############################################################################
    def set_interaction_mode(self, zoom, cursor, span, tip):
        """
        toggle nacina interakcije
        zoom --> boolean
        cursor --> boolean
        span --> boolean
        tip --> string, opis tipa grafa (SATNI, ZERO, SPAN ...)
        """
        #set up pick callbacks ovisno o tipu grafa
        self.disconnect_pick_evente()
        self.connect_pick_evente(tip)
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
###############################################################################
    def full_zoom_out(self):
        """
        Reset granica x i y osi da pokrivaju isti raspon kao i originalna slika

        vrijednosti su spremljene u memberima u obliku tuple
        self.xlim_original --> (xmin, xmax)
        self.ylim_original --> (ymin, ymax)
        """
        self.axes.set_xlim(self.xlim_original)
        self.axes.set_ylim(self.ylim_original)
        #nacrtaj promjenu
        self.draw()
###############################################################################
    def setup_limits(self, tip):
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
        if tip == 'SATNI':
            tmin, tmax = pomocne_funkcije.prosiri_granice_grafa(xmin, xmax, 60)
        elif tip == 'MINUTNI':
            tmin, tmax = pomocne_funkcije.prosiri_granice_grafa(xmin, xmax, 5)
        elif tip == 'ZERO' or tip == 'SPAN':
            tmin, tmax = pomocne_funkcije.prosiri_granice_grafa(xmin, xmax, 1440)
        else:
            tmin, tmax = xmin, xmax
        #set granice za max zoom out
        self.xlim_original = (tmin, tmax)
        self.ylim_original = self.axes.get_ylim()
        #set granice grafa
        self.axes.set_xlim(self.xlim_original)
        self.axes.set_ylim(self.ylim_original)
        self.draw()
###############################################################################
    def toggle_ticks(self, x):
        """
        toggle minor tickova on i off ovisno o ulaznoj vrijednosti x (boolean)
        """
        if x and self.statusGlavniGraf:
            self.axes.minorticks_on()
        else:
            self.axes.minorticks_off()
        self.draw()
###############################################################################
    def toggle_grid(self, x):
        """
        toggle grida on i off, ovisno o ulaznoj vrijednosti x (boolean)
        """
        if x and self.statusGlavniGraf:
            self.axes.grid(True)
        else:
            self.axes.grid(False)
        self.draw()
###############################################################################
    def toggle_legend(self, x):
        """
        toggle legende on i off, ovisno o ulaznoj vrijednosti x (boolean)
        """
        if x and self.statusGlavniGraf:
            self.legenda.set_visible(True)
        else:
            self.legenda.set_visible(False)
        self.draw()
###############################################################################
    def setup_legend(self):
        self.legenda = self.axes.legend(loc = 1,
                                        fontsize = 8,
                                        fancybox = True)
        self.legenda.get_frame().set_alpha(0.8)
###############################################################################
###############################################################################
