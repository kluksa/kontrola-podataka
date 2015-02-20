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
from matplotlib.widgets import RectangleSelector

###############################################################################
###############################################################################
class MPLCanvas(FigureCanvas):
    """
    Opcenita klasa za matplotlib canvas
    
    -overloadaj metodu crtaj sa specificnim naredbama za pojedini graf
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
        
        #zoom & pick mode boolean konstante
        self.MODEZOOM = False
        self.MODEPICK = True
        
        #instance of rectangle selector
        self.rectSelector = None
###############################################################################
    def crtaj(self):
        pass
###############################################################################
    def zoom_or_pick(self, lista):
        """
        Svaki canvas mora pratiti da li je trenutno aktivan zoom ili pick mode.
        
        ulazni parametar je lista 2 boolean vrijednosti [zoom, pick]
        
        ovisno o stanju tih varijabli definirati ce trenutni tip interakcije
        """
        self.MODEZOOM = lista[0]
        self.MODEPICK = lista[1]
        if self.MODEZOOM:
            self.rectSelector = RectangleSelector(self.axes, 
                                                  self.rect_zoom, 
                                                  drawtype = 'box')
        else:
            self.rectSelector = None
###############################################################################
    def rect_zoom(self, eclick, erelease):
        """
        Callback funkcija za rectangle zoom canvasa.
        """
        x = sorted([eclick.xdata, erelease.xdata])
        y = sorted([eclick.ydata, erelease.ydata])
        #set nove granice osi
        self.axes.set_xlim(x)
        self.axes.set_ylim(y)
        #redraw
        self.draw()
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