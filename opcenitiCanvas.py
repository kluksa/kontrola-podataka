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
        
    def crtaj(self):
        pass
