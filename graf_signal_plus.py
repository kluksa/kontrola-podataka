# -*- coding: utf-8 -*-
"""
Created on Tue Oct  7 11:21:29 2014

@author: User
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Apr 29 08:32:47 2014

@author: velimir

Izdvajanje grafova u pojedine klase. Dodana je mini aplikacija za funkcionalno testiranje
"""

#import statements
import sys
import copy
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import datetime
from datetime import timedelta
from PyQt4 import QtGui,QtCore, uic
import pandas as pd
from matplotlib.widgets import SpanSelector, Cursor
import numpy as np

#pomocni...samo za lokalni test
#import citac
#from agregator import Agregator

###############################################################################
#TODO!
#fix so this works puno toga promjenjeno
def crtaj_graf(canvas = None, 
               xlist = [], 
               ylist1 = [], 
               ylist2 = [], 
               tip = None, 
               linestyle = '-', 
               linewidth = 1.0, 
               marker = None, 
               color = 'black', 
               alpha = 1.0, 
               z = 1):
    """
    Generalna funkcija za crtanje grafova.
        
    Ulazni parametri su zadani preko keyword argumenata da kasnije ne dodje do
    zabune.
    
    Izlaz, crtanje na datom canvasu
    """
    
    if tip == 'plot' and len(xlist) == len(ylist1):
        #lineplot
        if len(xlist) != 0:
            canvas.axes.plot(xlist, 
                             ylist1, 
                             marker = marker, 
                             linestyle = linestyle, 
                             linewidth = linewidth, 
                             color = color, 
                             alpha = alpha, 
                             zorder = z)
            #naredba canvasu za crtanje
            canvas.draw()
        else:
            pass
        
    elif tip == 'scatter' and len(xlist) == len(ylist1):
        #scatter plot
        if len(xlist) != 0:
            canvas.axes.scatter(xlist, 
                                ylist1, 
                                marker = marker, 
                                color = color, 
                                alpha = alpha, 
                                zorder = z)
            #naredba za crtanje
            canvas.draw()
        else:
            pass
        
    elif tip == 'fill' and len(xlist) == len(ylist1) == len(ylist2):
        #fill between 2 y lines
        if len(xlist) != 0:
            canvas.axes.fill_between(xlist, 
                                     ylist1, 
                                     ylist2, 
                                     facecolor = color, 
                                     alpha = alpha, 
                                     zorder = z)
            #naredba canvasu za crtanje
            canvas.draw()
        else:
            pass
###############################################################################
def zaokruzi_vrijeme(dt_objekt, nSekundi):
    """
    Funkcija zaokruzuje na najblize vrijeme zadano sa nSekundi
    dt_objekt -> ulaz je datetime.datetime objekt
    nSekundi -> broj sekundi na koje se zaokruzuje, npr.
        60 - minuta
        3600 - sat
    
    izlaz je datetime.datetime objekt ili None (po defaultu)
    """
    if dt_objekt == None:
        return
    else:
        tmin = datetime.datetime.min
        delta = (dt_objekt - tmin).seconds
        zaokruzeno = ((delta + (nSekundi / 2)) // nSekundi) * nSekundi
        izlaz = dt_objekt + timedelta(0, zaokruzeno-delta, -dt_objekt.microsecond)
        return izlaz
###############################################################################
###############################################################################
class MPLCanvas(FigureCanvas):
    """
    matplotlib canvas class, generalni
    -overloadaj metodu crtaj sa specificnim naredbama
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
###############################################################################
###############################################################################
class FlagDijalog(QtGui.QDialog):
    """
    Custom dijalog za promjenu flaga
    """
    def __init__(self, parent = None, message = None):
        QtGui.QDialog.__init__(self)

        self.odgovor = None        
        msgBox = QtGui.QMessageBox()
        msgBox.setWindowTitle('Dijalog za promjenu valjanosti podataka')
        msgBox.setText(message)
        msgBox.addButton(QtGui.QPushButton('Valjan'), QtGui.QMessageBox.YesRole)
        msgBox.addButton(QtGui.QPushButton('Nevaljan'), QtGui.QMessageBox.NoRole)
        msgBox.addButton(QtGui.QPushButton('Odustani'), QtGui.QMessageBox.RejectRole)
        ret = msgBox.exec_()
        
        #odgovor se dohvati preko member varijable
        #0==YesRole
        if ret == 0:
            self.odgovor='valja'
        #1==NoRole
        elif ret == 1:
            self.odgovor='nevalja'
        else:
        #2==RejectRole
            self.odgovor='bez promjene'
###############################################################################
###############################################################################
base, form = uic.loadUiType('glavnikanaldetalji.ui')
class GlavniKanalDetalji(base, form):
    """
    Klasa za "prikaz" izbora opcija za crtanje glavnog kanala.
    
    Dict koji se mora prosljediti... postavke svih mogucih grafova
    
    validanOK = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'marker':'p', 'color':(0,255,0), 'alpha':1, 'zorder':20}
    validanNOK = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'marker':'p', 'color':(0,255,0), 'alpha':1, 'zorder':20}
    nevalidanOK = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'marker':'o', 'color':(255,0,0), 'alpha':1, 'zorder':20}
    nevalidanNOK = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'marker':'o', 'color':(255,0,0), 'alpha':1, 'zorder':20}
    glavnikanal1 = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'stupac1':'min', 'marker':'+', 'line':'None', 'color':(0,0,0), 'alpha':0.9, 'zorder':8}
    glavnikanal2 = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'stupac1':'max', 'marker':'+', 'line':'None', 'color':(0,0,0), 'alpha':0.9, 'zorder':9}
    glavnikanal3 = {'crtaj':True, 'tip':'plot', 'kanal':None, 'stupac1':'median', 'marker':'None', 'line':'-', 'color':(45,86,90), 'alpha':0.9, 'zorder':10}
    glavnikanal4 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'--', 'color':(73,189,191), 'alpha':0.9, 'zorder':11}
    glavnikanalfill = {'crtaj':True, 'tip':'fill', 'kanal':None, 'stupac1':'q05', 'stupac2':'q95', 'marker':'None', 'line':'--', 'color':(31,117,229), 'alpha':0.4, 'zorder':7}
    pomocnikanal1 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(186,113,123), 'alpha':0.9, 'zorder':1}
    pomocnikanal2 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(213,164,255), 'alpha':0.9, 'zorder':2}
    pomocnikanal3 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(111,118,255), 'alpha':0.9, 'zorder':3}
    pomocnikanal4 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(149,255,147), 'alpha':0.9, 'zorder':4}
    pomocnikanal5 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(214,255,137), 'alpha':0.9, 'zorder':5}
    pomocnikanal6 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(255,64,47), 'alpha':0.9, 'zorder':6}
    opcenito = {'grid':False, 'cursor':False, 'span':False, 'minorTicks':True}        
    mapa2 = {'validanOK':validanOK, 
             'validanNOK':validanNOK, 
             'nevalidanOK':nevalidanOK, 
             'nevalidanNOK':nevalidanNOK, 
             'glavnikanal1':glavnikanal1, 
             'glavnikanal2':glavnikanal2, 
             'glavnikanal3':glavnikanal3, 
             'glavnikanal4':glavnikanal4, 
             'glavnikanalfill':glavnikanalfill, 
             'pomocnikanal1':pomocnikanal1, 
             'pomocnikanal2':pomocnikanal2, 
             'pomocnikanal3':pomocnikanal3, 
             'pomocnikanal4':pomocnikanal4, 
             'pomocnikanal5':pomocnikanal5, 
             'pomocnikanal6':pomocnikanal6, 
             'opcenito':opcenito}
    """
    def __init__(self, parent = None, defaulti = None):
        super(base, self).__init__(parent)
        self.setupUi(self)
        
        #sve opcije su sadrzane u dictu defaulti
        self.__defaulti = defaulti
        
        self.__sviMarkeri = ['None', 'o', 'v', '^', '<', '>', 's', 'p', '*', 'h', '+', 'x', 'd', '_', '|']
        self.__sveLinije = ['None', '-', '--', '-.', ':']
        self.__sviPodaci = ['min', 'max', 'count', 'status', 'median', 'avg', 'q05', 'q95', 'std']
        self.__sviTipovi = ['scatter', 'plot']
        
        self.setup_glavni()
        self.setup_glavnikanal1()
        self.setup_glavnikanal2()
        self.setup_glavnikanal3()
        self.setup_glavnikanal4()
        self.setup_glavnikanalfill()
        
        self.enable_graf1()
        self.enable_graf2()
        self.enable_graf3()
        self.enable_graf4()
        self.enable_fill()
                
        self.poveznice()
        
    def poveznice(self):
        """
        Povezivanje kontrolnih elemenata sa funkcijama koje mjenjaju stanja
        """
        #qcheckboxes
        self.kanal1Check.stateChanged.connect(self.enable_graf1)
        self.kanal2Check.stateChanged.connect(self.enable_graf2)
        self.kanal3Check.stateChanged.connect(self.enable_graf3)
        self.kanal4Check.stateChanged.connect(self.enable_graf4)
        self.fillCheck.stateChanged.connect(self.enable_fill)
        #qcomboboxes        
        self.markerOK.currentIndexChanged.connect(self.change_markerOK)
        self.markerNOK.currentIndexChanged.connect(self.change_markerNOK)
        self.kanal1Komponenta.currentIndexChanged.connect(self.change_kanal1Komponenta)
        self.kanal2Komponenta.currentIndexChanged.connect(self.change_kanal2Komponenta)
        self.kanal3Komponenta.currentIndexChanged.connect(self.change_kanal3Komponenta)
        self.kanal4Komponenta.currentIndexChanged.connect(self.change_kanal4Komponenta)
        self.fillKomponenta1.currentIndexChanged.connect(self.change_fillKomponenta1)
        self.fillKomponenta2.currentIndexChanged.connect(self.change_fillKomponenta2)
        self.kanal1Tip.currentIndexChanged.connect(self.change_kanal1Tip)
        self.kanal2Tip.currentIndexChanged.connect(self.change_kanal2Tip)
        self.kanal3Tip.currentIndexChanged.connect(self.change_kanal3Tip)
        self.kanal4Tip.currentIndexChanged.connect(self.change_kanal4Tip)
        self.kanal1Marker.currentIndexChanged.connect(self.change_kanal1Marker)
        self.kanal2Marker.currentIndexChanged.connect(self.change_kanal2Marker)
        self.kanal3Marker.currentIndexChanged.connect(self.change_kanal3Marker)
        self.kanal4Marker.currentIndexChanged.connect(self.change_kanal4Marker)
        self.kanal1Linija.currentIndexChanged.connect(self.change_kanal1Linija)
        self.kanal2Linija.currentIndexChanged.connect(self.change_kanal2Linija)
        self.kanal3Linija.currentIndexChanged.connect(self.change_kanal3Linija)
        self.kanal4Linija.currentIndexChanged.connect(self.change_kanal4Linija)
        #qpushbuttons
        self.colorOK.clicked.connect(self.change_colorOK)
        self.colorNOK.clicked.connect(self.change_colorNOK)
        self.kanal1Boja.clicked.connect(self.change_kanal1Boja)
        self.kanal2Boja.clicked.connect(self.change_kanal2Boja)
        self.kanal3Boja.clicked.connect(self.change_kanal3Boja)
        self.kanal4Boja.clicked.connect(self.change_kanal4Boja)
        self.fillBoja.clicked.connect(self.change_fillBoja)
        
    def setup_glavni(self):
        """glavni scatter plot agregiranih srednjaka"""
        #clear
        self.markerOK.clear()
        self.markerNOK.clear()
        self.markerOK.addItems(self.__sviMarkeri[1:]) #izbaci 'None'
        self.markerNOK.addItems(self.__sviMarkeri[1:]) #izbaci 'None'
        ind = self.markerOK.findText(self.__defaulti['validanOK']['marker'])
        self.markerOK.setCurrentIndex(ind)
        #marker prije validacije
        ind = self.markerNOK.findText(self.__defaulti['nevalidanOK']['marker'])
        self.markerNOK.setCurrentIndex(ind)
        defaultBoja = self.__defaulti['validanOK']['color']
        defaultAlpha = self.__defaulti['validanOK']['alpha']
        boja = self.default_color_to_qcolor(defaultBoja, defaultAlpha)
        stil = self.color_to_style_string('QPushButton#colorOK', boja)
        self.colorOK.setStyleSheet(stil)
        defaultBoja = self.__defaulti['validanNOK']['color']
        defaultAlpha = self.__defaulti['validanNOK']['alpha']
        boja = self.default_color_to_qcolor(defaultBoja, defaultAlpha)
        stil = self.color_to_style_string('QPushButton#colorNOK', boja)
        self.colorNOK.setStyleSheet(stil)
        
    def setup_glavnikanal1(self):
        """glavni pomocni graf 1"""
        self.kanal1Marker.clear()
        self.kanal1Marker.addItems(self.__sviMarkeri)
        ind = self.kanal1Marker.findText(self.__defaulti['glavnikanal1']['marker'])
        self.kanal1Marker.setCurrentIndex(ind)
        self.kanal1Komponenta.clear()
        self.kanal1Komponenta.addItems(self.__sviPodaci)
        ind = self.kanal1Komponenta.findText(self.__defaulti['glavnikanal1']['stupac1'])
        self.kanal1Komponenta.setCurrentIndex(ind)
        self.kanal1Linija.clear()
        self.kanal1Linija.addItems(self.__sveLinije)
        ind = self.kanal1Linija.findText(self.__defaulti['glavnikanal1']['line'])
        self.kanal1Linija.setCurrentIndex(ind)
        self.kanal1Tip.clear()
        self.kanal1Tip.addItems(self.__sviTipovi)
        ind = self.kanal1Tip.findText(self.__defaulti['glavnikanal1']['tip'])
        self.kanal1Tip.setCurrentIndex(ind)        
        defaultBoja = self.__defaulti['glavnikanal1']['color']
        defaultAlpha = self.__defaulti['glavnikanal1']['alpha']
        boja = self.default_color_to_qcolor(defaultBoja, defaultAlpha)
        stil = self.color_to_style_string('QPushButton#kanal1Boja', boja)
        self.kanal1Boja.setStyleSheet(stil)
        self.kanal1Check.setChecked(self.__defaulti['glavnikanal1']['crtaj'])

    def setup_glavnikanal2(self):
        """glavni pomocni graf 2"""
        self.kanal2Marker.clear()
        self.kanal2Marker.addItems(self.__sviMarkeri)
        ind = self.kanal2Marker.findText(self.__defaulti['glavnikanal2']['marker'])
        self.kanal2Marker.setCurrentIndex(ind)
        self.kanal2Komponenta.clear()
        self.kanal2Komponenta.addItems(self.__sviPodaci)
        ind = self.kanal2Komponenta.findText(self.__defaulti['glavnikanal2']['stupac1'])
        self.kanal2Komponenta.setCurrentIndex(ind)
        self.kanal2Linija.clear()
        self.kanal2Linija.addItems(self.__sveLinije)
        ind = self.kanal2Linija.findText(self.__defaulti['glavnikanal2']['line'])
        self.kanal2Linija.setCurrentIndex(ind)
        self.kanal2Tip.clear()
        self.kanal2Tip.addItems(self.__sviTipovi)
        ind = self.kanal2Tip.findText(self.__defaulti['glavnikanal2']['tip'])
        self.kanal2Tip.setCurrentIndex(ind)
        defaultBoja = self.__defaulti['glavnikanal2']['color']
        defaultAlpha = self.__defaulti['glavnikanal2']['alpha']
        boja = self.default_color_to_qcolor(defaultBoja, defaultAlpha)
        stil = self.color_to_style_string('QPushButton#kanal2Boja', boja)
        self.kanal2Boja.setStyleSheet(stil)
        self.kanal2Check.setChecked(self.__defaulti['glavnikanal2']['crtaj'])

    def setup_glavnikanal3(self):
        """glavni pomocni graf 3"""
        self.kanal3Marker.clear()
        self.kanal3Marker.addItems(self.__sviMarkeri)
        ind = self.kanal3Marker.findText(self.__defaulti['glavnikanal3']['marker'])
        self.kanal3Marker.setCurrentIndex(ind)
        self.kanal3Komponenta.clear()
        self.kanal3Komponenta.addItems(self.__sviPodaci)
        ind = self.kanal3Komponenta.findText(self.__defaulti['glavnikanal3']['stupac1'])
        self.kanal3Komponenta.setCurrentIndex(ind)
        self.kanal3Linija.clear()
        self.kanal3Linija.addItems(self.__sveLinije)
        ind = self.kanal3Linija.findText(self.__defaulti['glavnikanal3']['line'])
        self.kanal3Linija.setCurrentIndex(ind)
        self.kanal3Tip.clear()
        self.kanal3Tip.addItems(self.__sviTipovi)
        ind = self.kanal3Tip.findText(self.__defaulti['glavnikanal3']['tip'])
        self.kanal3Tip.setCurrentIndex(ind)
        defaultBoja = self.__defaulti['glavnikanal3']['color']
        defaultAlpha = self.__defaulti['glavnikanal3']['alpha']
        boja = self.default_color_to_qcolor(defaultBoja, defaultAlpha)
        stil = self.color_to_style_string('QPushButton#kanal3Boja', boja)
        self.kanal3Boja.setStyleSheet(stil)
        self.kanal3Check.setChecked(self.__defaulti['glavnikanal3']['crtaj'])

    def setup_glavnikanal4(self):
        """glavni pomocni graf 4"""
        self.kanal4Marker.clear()
        self.kanal4Marker.addItems(self.__sviMarkeri)
        ind = self.kanal4Marker.findText(self.__defaulti['glavnikanal4']['marker'])
        self.kanal4Marker.setCurrentIndex(ind)
        self.kanal4Komponenta.clear()
        self.kanal4Komponenta.addItems(self.__sviPodaci)
        ind = self.kanal4Komponenta.findText(self.__defaulti['glavnikanal4']['stupac1'])
        self.kanal4Komponenta.setCurrentIndex(ind)
        self.kanal4Linija.clear()
        self.kanal4Linija.addItems(self.__sveLinije)
        ind = self.kanal4Linija.findText(self.__defaulti['glavnikanal4']['line'])
        self.kanal4Linija.setCurrentIndex(ind)
        self.kanal4Tip.clear()
        self.kanal4Tip.addItems(self.__sviTipovi)
        ind = self.kanal4Tip.findText(self.__defaulti['glavnikanal4']['tip'])
        self.kanal4Tip.setCurrentIndex(ind)
        defaultBoja = self.__defaulti['glavnikanal4']['color']
        defaultAlpha = self.__defaulti['glavnikanal4']['alpha']
        boja = self.default_color_to_qcolor(defaultBoja, defaultAlpha)
        stil = self.color_to_style_string('QPushButton#kanal4Boja', boja)
        self.kanal4Boja.setStyleSheet(stil)
        self.kanal4Check.setChecked(self.__defaulti['glavnikanal4']['crtaj'])
       
    def setup_glavnikanalfill(self):
        """fill_between graf"""
        self.fillKomponenta1.clear()
        self.fillKomponenta2.clear()
        self.fillKomponenta1.addItems(self.__sviPodaci)
        self.fillKomponenta2.addItems(self.__sviPodaci)
        ind = self.fillKomponenta1.findText(self.__defaulti['glavnikanalfill']['stupac1'])
        self.fillKomponenta1.setCurrentIndex(ind)
        ind = self.fillKomponenta2.findText(self.__defaulti['glavnikanalfill']['stupac2'])
        self.fillKomponenta2.setCurrentIndex(ind)
        defaultBoja = self.__defaulti['glavnikanalfill']['color']
        defaultAlpha = self.__defaulti['glavnikanalfill']['alpha']
        boja = self.default_color_to_qcolor(defaultBoja, defaultAlpha)
        stil = self.color_to_style_string('QPushButton#fillBoja', boja)
        self.fillBoja.setStyleSheet(stil)
        self.fillCheck.setChecked(self.__defaulti['glavnikanalfill']['crtaj'])
    
    def enable_graf1(self):
        """toggle checkbox, enables or disables related controls"""
        if self.kanal1Check.isChecked() == True:
            self.kanal1Komponenta.setEnabled(True)
            self.kanal1Marker.setEnabled(True)
            self.kanal1Linija.setEnabled(True)
            self.kanal1Boja.setEnabled(True)
            self.kanal1Tip.setEnabled(True)
        else:
            self.kanal1Komponenta.setEnabled(False)
            self.kanal1Marker.setEnabled(False)
            self.kanal1Linija.setEnabled(False)
            self.kanal1Boja.setEnabled(False)
            self.kanal1Tip.setEnabled(False)
            
    def enable_graf2(self):
        """toggle checkbox, enables or disables related controls"""
        if self.kanal2Check.isChecked() == True:
            self.kanal2Komponenta.setEnabled(True)
            self.kanal2Marker.setEnabled(True)
            self.kanal2Linija.setEnabled(True)
            self.kanal2Boja.setEnabled(True)
            self.kanal2Tip.setEnabled(True)
        else:
            self.kanal2Komponenta.setEnabled(False)
            self.kanal2Marker.setEnabled(False)
            self.kanal2Linija.setEnabled(False)
            self.kanal2Boja.setEnabled(False)
            self.kanal2Tip.setEnabled(False)

    def enable_graf3(self):
        """toggle checkbox, enables or disables related controls"""
        if self.kanal3Check.isChecked() == True:
            self.kanal3Komponenta.setEnabled(True)
            self.kanal3Marker.setEnabled(True)
            self.kanal3Linija.setEnabled(True)
            self.kanal3Boja.setEnabled(True)
            self.kanal3Tip.setEnabled(True)
        else:
            self.kanal3Komponenta.setEnabled(False)
            self.kanal3Marker.setEnabled(False)
            self.kanal3Linija.setEnabled(False)
            self.kanal3Boja.setEnabled(False)
            self.kanal3Tip.setEnabled(False)

    def enable_graf4(self):
        """toggle checkbox, enables or disables related controls"""
        if self.kanal4Check.isChecked() == True:
            self.kanal4Komponenta.setEnabled(True)
            self.kanal4Marker.setEnabled(True)
            self.kanal4Linija.setEnabled(True)
            self.kanal4Boja.setEnabled(True)
            self.kanal4Tip.setEnabled(True)
        else:
            self.kanal4Komponenta.setEnabled(False)
            self.kanal4Marker.setEnabled(False)
            self.kanal4Linija.setEnabled(False)
            self.kanal4Boja.setEnabled(False)
            self.kanal4Tip.setEnabled(False)

    def enable_fill(self):
        """toggle checkbox, enables or disables related controls"""
        if self.fillCheck.isChecked() == True:
            self.fillKomponenta1.setEnabled(True)
            self.fillKomponenta2.setEnabled(True)
            self.fillBoja.setEnabled(True)
        else:
            self.fillKomponenta1.setEnabled(False)
            self.fillKomponenta2.setEnabled(False)
            self.fillBoja.setEnabled(False)
    
    def change_markerOK(self):
        newValue = self.markerOK.currentText()
        self.__defaulti['validanOK']['marker'] = str(newValue)
        self.__defaulti['validanNOK']['marker'] = str(newValue)

    def change_markerNOK(self):
        newValue = self.markerNOK.currentText()
        self.__defaulti['nevalidanOK']['marker'] = str(newValue)
        self.__defaulti['nevalidanNOK']['marker'] = str(newValue)
    
    def change_colorOK(self):
        defaultBoja = self.__defaulti['validanOK']['color']
        defaultAlpha = self.__defaulti['validanOK']['alpha']
        boja = self.default_color_to_qcolor(defaultBoja, defaultAlpha)
        #dijalog
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test za validnu boju
            color = QtGui.QColor.fromRgba(color)
            rgb, a = self.qcolor_to_default_color(color)
            #update dict
            self.__defaulti['validanOK']['color'] = rgb
            self.__defaulti['validanOK']['alpha'] = a
            self.__defaulti['nevalidanOK']['color'] = rgb
            self.__defaulti['nevalidanOK']['alpha'] = a
            #set new color
            stil = self.color_to_style_string('QPushButton#colorOK', color)
            self.colorOK.setStyleSheet(stil)
   
    def change_colorNOK(self):
        defaultBoja = self.__defaulti['validanNOK']['color']
        defaultAlpha = self.__defaulti['validanNOK']['alpha']
        boja = self.default_color_to_qcolor(defaultBoja, defaultAlpha)
        #dijalog
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test za validnu boju
            color = QtGui.QColor.fromRgba(color)
            rgb, a = self.qcolor_to_default_color(color)
            #update dict
            self.__defaulti['validanNOK']['color'] = rgb
            self.__defaulti['validanNOK']['alpha'] = a
            self.__defaulti['nevalidanNOK']['color'] = rgb
            self.__defaulti['nevalidanNOK']['alpha'] = a
            #set new color
            stil = self.color_to_style_string('QPushButton#colorNOK', color)
            self.colorNOK.setStyleSheet(stil)
    
    def change_kanal1Komponenta(self):
        newValue = self.kanal1Komponenta.currentText()
        self.__defaulti['glavnikanal1']['stupac1'] = str(newValue)

    def change_kanal2Komponenta(self):
        newValue = self.kanal2Komponenta.currentText()
        self.__defaulti['glavnikanal2']['stupac1'] = str(newValue)
    
    def change_kanal3Komponenta(self):
        newValue = self.kanal3Komponenta.currentText()
        self.__defaulti['glavnikanal3']['stupac1'] = str(newValue)
    
    def change_kanal4Komponenta(self):
        newValue = self.kanal4Komponenta.currentText()
        self.__defaulti['glavnikanal4']['stupac1'] = str(newValue)
    
    def change_fillKomponenta1(self):
        newValue = self.fillKomponenta1.currentText()
        self.__defaulti['glavnikanalfill']['stupac1'] = str(newValue)
    
    def change_fillKomponenta2(self):
        newValue = self.fillKomponenta2.currentText()
        self.__defaulti['glavnikanalfill']['stupac2'] = str(newValue)
    
    def change_kanal1Marker(self):
        newValue = self.kanal1Marker.currentText()
        self.__defaulti['glavnikanal1']['marker'] = str(newValue)
    
    def change_kanal2Marker(self):
        newValue = self.kanal2Marker.currentText()
        self.__defaulti['glavnikanal2']['marker'] = str(newValue)
    
    def change_kanal3Marker(self):
        newValue = self.kanal3Marker.currentText()
        self.__defaulti['glavnikanal3']['marker'] = str(newValue)
    
    def change_kanal4Marker(self):
        newValue = self.kanal4Marker.currentText()
        self.__defaulti['glavnikanal4']['marker'] = str(newValue)
    
    def change_kanal1Linija(self):
        newValue = self.kanal1Linija.currentText()
        self.__defaulti['glavnikanal1']['line'] = str(newValue)
    
    def change_kanal2Linija(self):
        newValue = self.kanal2Linija.currentText()
        self.__defaulti['glavnikanal2']['line'] = str(newValue)
    
    def change_kanal3Linija(self):
        newValue = self.kanal3Linija.currentText()
        self.__defaulti['glavnikanal3']['line'] = str(newValue)
    
    def change_kanal4Linija(self):
        newValue = self.kanal4Linija.currentText()
        self.__defaulti['glavnikanal4']['line'] = str(newValue)
    
    def change_kanal1Tip(self):
        newValue = self.kanal1Tip.currentText()
        self.__defaulti['glavnikanal1']['tip'] = str(newValue)

    def change_kanal2Tip(self):
        newValue = self.kanal2Tip.currentText()
        self.__defaulti['glavnikanal2']['tip'] = str(newValue)
    
    def change_kanal3Tip(self):
        newValue = self.kanal3Tip.currentText()
        self.__defaulti['glavnikanal3']['tip'] = str(newValue)
    
    def change_kanal4Tip(self):
        newValue = self.kanal4Tip.currentText()
        self.__defaulti['glavnikanal4']['tip'] = str(newValue)
    
    def change_kanal1Boja(self):
        defaultBoja = self.__defaulti['glavnikanal1']['color']
        defaultAlpha = self.__defaulti['glavnikanal1']['alpha']
        boja = self.default_color_to_qcolor(defaultBoja, defaultAlpha)
        #dijalog
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test za validnu boju
            color = QtGui.QColor.fromRgba(color)
            rgb, a = self.qcolor_to_default_color(color)
            #update dict
            self.__defaulti['glavnikanal1']['color'] = rgb
            self.__defaulti['glavnikanal1']['alpha'] = a
            #set new color
            stil = self.color_to_style_string('QPushButton#kanal1Boja', color)
            self.kanal1Boja.setStyleSheet(stil)
    
    def change_kanal2Boja(self):
        defaultBoja = self.__defaulti['glavnikanal2']['color']
        defaultAlpha = self.__defaulti['glavnikanal2']['alpha']
        boja = self.default_color_to_qcolor(defaultBoja, defaultAlpha)
        #dijalog
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test za validnu boju
            color = QtGui.QColor.fromRgba(color)
            rgb, a = self.qcolor_to_default_color(color)
            #update dict
            self.__defaulti['glavnikanal2']['color'] = rgb
            self.__defaulti['glavnikanal2']['alpha'] = a
            #set new color
            stil = self.color_to_style_string('QPushButton#kanal2Boja', color)
            self.kanal2Boja.setStyleSheet(stil)
    
    def change_kanal3Boja(self):
        defaultBoja = self.__defaulti['glavnikanal3']['color']
        defaultAlpha = self.__defaulti['glavnikanal3']['alpha']
        boja = self.default_color_to_qcolor(defaultBoja, defaultAlpha)
        #dijalog
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test za validnu boju
            color = QtGui.QColor.fromRgba(color)
            rgb, a = self.qcolor_to_default_color(color)
            #update dict
            self.__defaulti['glavnikanal3']['color'] = rgb
            self.__defaulti['glavnikanal3']['alpha'] = a
            #set new color
            stil = self.color_to_style_string('QPushButton#kanal3Boja', color)
            self.kanal3Boja.setStyleSheet(stil)
    
    def change_kanal4Boja(self):
        defaultBoja = self.__defaulti['glavnikanal4']['color']
        defaultAlpha = self.__defaulti['glavnikanal4']['alpha']
        boja = self.default_color_to_qcolor(defaultBoja, defaultAlpha)
        #dijalog
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test za validnu boju
            color = QtGui.QColor.fromRgba(color)
            rgb, a = self.qcolor_to_default_color(color)
            #update dict
            self.__defaulti['glavnikanal4']['color'] = rgb
            self.__defaulti['glavnikanal4']['alpha'] = a
            #set new color
            stil = self.color_to_style_string('QPushButton#kanal4Boja', color)
            self.kanal4Boja.setStyleSheet(stil)
    
    def change_fillBoja(self):
        defaultBoja = self.__defaulti['glavnikanalfill']['color']
        defaultAlpha = self.__defaulti['glavnikanalfill']['alpha']
        boja = self.default_color_to_qcolor(defaultBoja, defaultAlpha)
        #dijalog
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test za validnu boju
            color = QtGui.QColor.fromRgba(color)
            rgb, a = self.qcolor_to_default_color(color)
            #update dict
            self.__defaulti['glavnikanalfill']['color'] = rgb
            self.__defaulti['glavnikanalfill']['alpha'] = a
            #set new color
            stil = self.color_to_style_string('QPushButton#fillBoja', color)
            self.fillBoja.setStyleSheet(stil)

    def default_color_to_qcolor(self, rgb, a):
        """
        helper funkcija za transformaciju boje u QColor
        input:
            rgb -> (r, g, b) tuple
            a -> float izmedju [0:1]
        output:
            QtGui.QColor objekt
        """
        boja = QtGui.QColor()
        #unpack tuple of rgb color
        r, g, b = rgb
        boja.setRed(r)
        boja.setGreen(g)
        boja.setBlue(b)
        #alpha je izmedju 0-1, input treba biti int 0-255
        a = int(a*255)
        boja.setAlpha(a)
        return boja
        
    def qcolor_to_default_color(self, color):
        """
        helper funkcija za transformacije qcolor u defaultnu boju
        input:
            color ->QtGui.QColor
        output:
            (r,g,b) tuple, i alpha
        """
        r = color.red()
        g = color.green()
        b = color.blue()
        a = color.alpha()/255
        return (r,g,b), a
        
    def color_to_style_string(self, target, color):
        """
        helper funkcija za izradu styleSheet stringa
        input:
            target -> string, target of background color change
                npr. 'QLabel#label1'
            color -> QtGui.QColor
        output:
            string - styleSheet 'css' style background for target element
        """
        r = color.red()
        g = color.green()
        b = color.blue()
        a = int(100*color.alpha()/255)
        stil = target + " {background: rgba(" +"{0},{1},{2},{3}%)".format(r,g,b,a)+"}"
        return stil
        
    def vrati_dict(self):
        """funkcija vraca izmjenjeni defaultni dictionary svih grafova"""
        return self.__defaulti
###############################################################################
###############################################################################
base1, form1 = uic.loadUiType('pomocnigrafdetalji.ui')
class PomocniGrafDetalji(base1, form1):
    """
    Opcenita klasa za izbor detalja grafa

    incijalizacija sa:
        defaulti : dict, popis svih predvidjenih grafova
        graf : string, kljuc mape pojedinog grafa
    """
    def __init__(self, parent = None, defaulti = None, graf = None):
        super(base1, self).__init__(parent)
        self.setupUi(self)
        
        #defaultni izbor za grafove
        self.__defaulti = defaulti #defaultni dict svih grafova
        self.__graf = graf #string kljuca specificnog grafa
        
        self.__sviMarkeri = ['None', 'o', 'v', '^', '<', '>', 's', 'p', '*', 'h', '+', 'x', 'd', '_', '|']
        self.__sveLinije = ['None', '-', '--', '-.', ':']
        self.__sviPodaci = ['min', 'max', 'count', 'status', 'median', 'avg', 'q05', 'q95', 'std']
        self.__sviTipovi = ['scatter', 'plot']
        
        self.popuni_izbornike()
        self.veze()
        
    def veze(self):
        """poveznice izmedju kontrolih elemenata i funkcija koje mjenjaju stanje
        objekta"""
        self.komponenta.currentIndexChanged.connect(self.change_komponenta)
        self.tip.currentIndexChanged.connect(self.change_tip)
        self.marker.currentIndexChanged.connect(self.change_marker)
        self.linija.currentIndexChanged.connect(self.change_linija)
        self.boja.clicked.connect(self.change_boja)
    
    def change_komponenta(self):
        newValue = self.komponenta.currentText()
        self.__defaulti[self.__graf]['stupac1'] = newValue
    
    def change_tip(self):
        newValue = self.tip.currentText()
        self.__defaulti[self.__graf]['tip'] = newValue
    
    def change_marker(self):
        newValue = self.marker.currentText()
        self.__defaulti[self.__graf]['marker'] = newValue
    
    def change_linija(self):
        newValue = self.linija.currentText()
        self.__defaulti[self.__graf]['line'] = newValue
    
    def change_boja(self):
        rgb = self.__defaulti[self.__graf]['color']
        a = self.__defaulti[self.__graf]['alpha']
        boja = self.default_color_to_qcolor(rgb, a)
        #dijalog
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test za validnu boju
            color = QtGui.QColor.fromRgba(color)
            rgb, a = self.qcolor_to_default_color(color)
            #update dict
            self.__defaulti[self.__graf]['color'] = rgb
            self.__defaulti[self.__graf]['alpha'] = a
            #set new color
            stil = self.color_to_style_string('QPushButton#boja', color)
            self.boja.setStyleSheet(stil)
    
    def popuni_izbornike(self):
        """inicijalizacija izbornika sa defaultinim postavkama"""
        naziv = 'Detalji pomocnog grafa, kanal: ' + str(self.__defaulti[self.__graf]['kanal'])
        self.setWindowTitle(naziv)
        self.komponenta.clear()
        self.komponenta.addItems(self.__sviPodaci)
        ind = self.komponenta.findText(self.__defaulti[self.__graf]['stupac1'])
        self.komponenta.setCurrentIndex(ind)
        self.tip.clear()
        self.tip.addItems(self.__sviTipovi)
        ind = self.tip.findText(self.__defaulti[self.__graf]['tip'])
        self.tip.setCurrentIndex(ind)
        self.marker.clear()
        self.marker.addItems(self.__sviMarkeri)
        ind = self.marker.findText(self.__defaulti[self.__graf]['marker'])
        self.marker.setCurrentIndex(ind)
        self.linija.clear()
        self.linija.addItems(self.__sveLinije)
        ind = self.linija.findText(self.__defaulti[self.__graf]['line'])
        self.linija.setCurrentIndex(ind)
        
        rgb = self.__defaulti[self.__graf]['color']
        a = self.__defaulti[self.__graf]['alpha']
        color = self.default_color_to_qcolor(rgb, a)
        stil = self.color_to_style_string('QPushButton#boja', color)
        self.boja.setStyleSheet(stil)

    def default_color_to_qcolor(self, rgb, a):
        """
        helper funkcija za transformaciju boje u QColor
        input:
            rgb -> (r, g, b) tuple
            a -> float izmedju [0:1]
        output:
            QtGui.QColor objekt
        """
        boja = QtGui.QColor()
        #unpack tuple of rgb color
        r, g, b = rgb
        boja.setRed(r)
        boja.setGreen(g)
        boja.setBlue(b)
        #alpha je izmedju 0-1, input treba biti int 0-255
        a = int(a*255)
        boja.setAlpha(a)
        return boja
        
    def qcolor_to_default_color(self, color):
        """
        helper funkcija za transformacije qcolor u defaultnu boju
        input:
            color ->QtGui.QColor
        output:
            (r,g,b) tuple, i alpha
        """
        r = color.red()
        g = color.green()
        b = color.blue()
        a = color.alpha()/255
        return (r,g,b), a
        
    def color_to_style_string(self, target, color):
        """
        helper funkcija za izradu styleSheet stringa
        input:
            target -> string, target of background color change
                npr. 'QLabel#label1'
            color -> QtGui.QColor
        output:
            string - styleSheet 'css' style background for target element
        """
        r = color.red()
        g = color.green()
        b = color.blue()
        a = int(100*color.alpha()/255)
        stil = target + " {background: rgba(" +"{0},{1},{2},{3}%)".format(r,g,b,a)+"}"
        return stil
        
    def vrati_dict(self):
        """funkcija vraca izmjenjeni defaultni dictionary svih grafova"""
        return self.__defaulti
###############################################################################
###############################################################################

base2, form2 = uic.loadUiType('satnigraf.ui')
class SatniGraf(base2, form2):
    """
    Klasa za "prikaz" satnog grafa
    Sadrzi kontrole i canvas za graf (canvas je u drugoj klasi)
    """
    def __init__(self, parent = None, defaulti = None):
        super(base2, self).__init__(parent)
        self.setupUi(self)
        
        #defaultini izbor za grafove
        self.__defaulti = defaulti
        #inicijalizacija ostalih grafickih elemenata
        self.widget1 = QtGui.QWidget()
        self.widget2 = QtGui.QWidget()
        #inicijalizacija canvasa na mjesto self.grafWidget
        self.canvasSatni = GrafSatniSrednjaci(parent = self.widget1)
        #inicijalizacija Navigation bara
        self.mplToolbar = NavigationToolbar(self.canvasSatni, self.widget2)
        self.graphLayout.addWidget(self.canvasSatni)
        self.graphLayout.addWidget(self.mplToolbar)
        
        self.veze()
        self.initial_setup()        
        
        
        #opis slicea : slice od: do:
        self.labelSlice.setText('opis slicea- programski handle')
        
        
        #razne kontrole za rad sa grafom
        #grid handle        
        self.canvasSatni.axes.grid()

        #cursor handle
        self.cursor = Cursor(self.canvasSatni.axes, useblit=True, color='tomato', linewidth=1 )

        #minor ticks handle
        self.canvasSatni.axes.minorticks_on()

    def initial_setup(self):
        """inicijalne postavke izbornika (stanje comboboxeva, checkboxeva...)"""
        #TODO!
        #inicijalno upisivanje.....
        
        #checkboxes
        self.glavniGrafCheck.setChecked(True)
        self.enable_glavni_kanal()
        self.pGraf1Check.setChecked(self.__defaulti['pomocnikanal1']['crtaj'])
        self.enable_pomocni_kanal1()
        self.pGraf2Check.setChecked(self.__defaulti['pomocnikanal2']['crtaj'])
        self.enable_pomocni_kanal2()
        self.pGraf3Check.setChecked(self.__defaulti['pomocnikanal3']['crtaj'])
        self.enable_pomocni_kanal3()
        self.pGraf4Check.setChecked(self.__defaulti['pomocnikanal4']['crtaj'])
        self.enable_pomocni_kanal4()
        self.pGraf5Check.setChecked(self.__defaulti['pomocnikanal5']['crtaj'])
        self.enable_pomocni_kanal5()
        self.pGraf6Check.setChecked(self.__defaulti['pomocnikanal6']['crtaj'])
        self.enable_pomocni_kanal6()
        self.gridCheck.setChecked(self.__defaulti['opcenito']['grid'])
        self.enable_grid()
        self.cursorCheck.setChecked(self.__defaulti['opcenito']['cursor'])
        self.enable_cursor()
        self.spanSelectorCheck.setChecked(self.__defaulti['opcenito']['span'])
        self.enable_spanSelector()
        self.minorTickCheck.setChecked(self.__defaulti['opcenito']['minorTicks'])
        self.enable_minorTick()
        
        #button colors
        self.change_boja_pGraf1Detalji()
        self.change_boja_pGraf2Detalji()
        self.change_boja_pGraf3Detalji()
        self.change_boja_pGraf4Detalji()
        self.change_boja_pGraf5Detalji()
        self.change_boja_pGraf6Detalji()
        
        #initial combobox values... popis kanala, treba prosljediti dokument
        #dict svih agregiranih...tada se mogu populirati comboboxevi



    def veze(self):
        """poveznice izmedju kontrolnih elemenata i funkcija koje mjenjaju stanja"""
        #TODO!
        #BITNO... SVE FUNKCIJE KOJE MJENJAJU NEKE POSTAVKE GRAFA MORAJU POZIVATI
        #PONOVNO CRTANJE!!!!!!!!!
        #dijalozi
        self.glavniGrafDetalji.clicked.connect(self.dijalog_glavniGrafDetalji)
        self.pGraf1Detalji.clicked.connect(self.dijalog_pGraf1Detalji)
        self.pGraf2Detalji.clicked.connect(self.dijalog_pGraf2Detalji)
        self.pGraf3Detalji.clicked.connect(self.dijalog_pGraf3Detalji)
        self.pGraf4Detalji.clicked.connect(self.dijalog_pGraf4Detalji)
        self.pGraf5Detalji.clicked.connect(self.dijalog_pGraf5Detalji)
        self.pGraf6Detalji.clicked.connect(self.dijalog_pGraf6Detalji)
        #comboboxes
        self.glavniGrafIzbor.currentIndexChanged.connect(self.update_glavni_kanal)
        self.pGraf1Izbor.currentIndexChanged.connect(self.update_pomocni_kanal1)
        self.pGraf2Izbor.currentIndexChanged.connect(self.update_pomocni_kanal2)
        self.pGraf3Izbor.currentIndexChanged.connect(self.update_pomocni_kanal3)
        self.pGraf4Izbor.currentIndexChanged.connect(self.update_pomocni_kanal4)
        self.pGraf5Izbor.currentIndexChanged.connect(self.update_pomocni_kanal5)
        self.pGraf6Izbor.currentIndexChanged.connect(self.update_pomocni_kanal6)
        #checkboxes
        self.glavniGrafCheck.stateChanged.connect(self.enable_glavni_kanal)
        self.pGraf1Check.stateChanged.connect(self.enable_pomocni_kanal1)
        self.pGraf2Check.stateChanged.connect(self.enable_pomocni_kanal2)
        self.pGraf3Check.stateChanged.connect(self.enable_pomocni_kanal3)
        self.pGraf4Check.stateChanged.connect(self.enable_pomocni_kanal4)
        self.pGraf5Check.stateChanged.connect(self.enable_pomocni_kanal5)
        self.pGraf6Check.stateChanged.connect(self.enable_pomocni_kanal6)
        self.gridCheck.stateChanged.connect(self.enable_grid)
        self.cursorCheck.stateChanged.connect(self.enable_cursor)
        self.spanSelectorCheck.stateChanged.connect(self.enable_spanSelector)
        self.minorTickCheck.stateChanged.connect(self.enable_minorTick)
        
    def enable_grid(self):
        if self.gridCheck.isChecked() == True:
            self.__defaulti['opcenito']['grid'] = True
        else:
            self.__defaulti['opcenito']['grid'] = False
    
    def enable_cursor(self):
        if self.cursorCheck.isChecked() == True:
            self.__defaulti['opcenito']['cursor'] = True
        else:
            self.__defaulti['opcenito']['cursor'] = False
    
    def enable_spanSelector(self):
        if self.spanSelectorCheck.isChecked() == True:
            self.__defaulti['opcenito']['span'] = True
        else:
            self.__defaulti['opcenito']['span'] = False
    
    def enable_minorTick(self):
        if self.minorTickCheck.isChecked() == True:
            self.__defaulti['opcenito']['minorTicks'] = True
        else:
            self.__defaulti['opcenito']['minorTicks'] = False
    
    def enable_glavni_kanal(self):
        if self.glavniGrafCheck.isChecked() == True:
            self.glavniGrafIzbor.setEnabled(True)
            self.glavniGrafDetalji.setEnabled(True)
        else:
            self.glavniGrafIzbor.setEnabled(False)
            self.glavniGrafDetalji.setEnabled(False)

    def enable_pomocni_kanal1(self):
        if self.pGraf1Check.isChecked() == True:
            self.pGraf1Izbor.setEnabled(True)
            self.pGraf1Detalji.setEnabled(True)
        else:
            self.pGraf1Izbor.setEnabled(False)
            self.pGraf1Detalji.setEnabled(False)
            
    def enable_pomocni_kanal2(self):
        if self.pGraf2Check.isChecked() == True:
            self.pGraf2Izbor.setEnabled(True)
            self.pGraf2Detalji.setEnabled(True)
        else:
            self.pGraf2Izbor.setEnabled(False)
            self.pGraf2Detalji.setEnabled(False)
    
    def enable_pomocni_kanal3(self):
        if self.pGraf3Check.isChecked() == True:
            self.pGraf3Izbor.setEnabled(True)
            self.pGraf3Detalji.setEnabled(True)
        else:
            self.pGraf3Izbor.setEnabled(False)
            self.pGraf3Detalji.setEnabled(False)

    def enable_pomocni_kanal4(self):
        if self.pGraf4Check.isChecked() == True:
            self.pGraf4Izbor.setEnabled(True)
            self.pGraf4Detalji.setEnabled(True)
        else:
            self.pGraf4Izbor.setEnabled(False)
            self.pGraf4Detalji.setEnabled(False)

    def enable_pomocni_kanal5(self):
        if self.pGraf5Check.isChecked() == True:
            self.pGraf5Izbor.setEnabled(True)
            self.pGraf5Detalji.setEnabled(True)
        else:
            self.pGraf5Izbor.setEnabled(False)
            self.pGraf5Detalji.setEnabled(False)

    def enable_pomocni_kanal6(self):
        if self.pGraf6Check.isChecked() == True:
            self.pGraf6Izbor.setEnabled(True)
            self.pGraf6Detalji.setEnabled(True)
        else:
            self.pGraf6Izbor.setEnabled(False)
            self.pGraf6Detalji.setEnabled(False)

    def update_glavni_kanal(self):
        newValue = self.glavniGrafIzbor.currentText()
        self.__defaulti['validanOK']['kanal'] = newValue
        self.__defaulti['validanNOK']['kanal'] = newValue
        self.__defaulti['nevalidanOK']['kanal'] = newValue
        self.__defaulti['nevalidanNOK']['kanal'] = newValue
        self.__defaulti['glavnikanal1']['kanal'] = newValue
        self.__defaulti['glavnikanal2']['kanal'] = newValue
        self.__defaulti['glavnikanal3']['kanal'] = newValue
        self.__defaulti['glavnikanal4']['kanal'] = newValue
        self.__defaulti['glavnikanalfill']['kanal'] = newValue
    
    def update_pomocni_kanal1(self):
        newValue = self.pGraf1Izbor.currentText()
        self.__defaulti['pomocnikanal1']['kanal'] = newValue
    
    def update_pomocni_kanal2(self):
        newValue = self.pGraf2Izbor.currentText()
        self.__defaulti['pomocnikanal2']['kanal'] = newValue
    
    def update_pomocni_kanal3(self):
        newValue = self.pGraf3Izbor.currentText()
        self.__defaulti['pomocnikanal3']['kanal'] = newValue
    
    def update_pomocni_kanal4(self):
        newValue = self.pGraf4Izbor.currentText()
        self.__defaulti['pomocnikanal4']['kanal'] = newValue
    
    def update_pomocni_kanal5(self):
        newValue = self.pGraf5Izbor.currentText()
        self.__defaulti['pomocnikanal5']['kanal'] = newValue
    
    def update_pomocni_kanal6(self):
        newValue = self.pGraf6Izbor.currentText()
        self.__defaulti['pomocnikanal6']['kanal'] = newValue
        
    def change_boja_pGraf1Detalji(self):
        rgb = self.__defaulti['pomocnikanal1']['color']
        a = self.__defaulti['pomocnikanal1']['alpha']
        boja = self.default_color_to_qcolor(rgb, a)
        stil = self.color_to_style_string('QPushButton#pGraf1Detalji', boja)
        self.pGraf1Detalji.setStyleSheet(stil)
        
    def change_boja_pGraf2Detalji(self):
        rgb = self.__defaulti['pomocnikanal2']['color']
        a = self.__defaulti['pomocnikanal2']['alpha']
        boja = self.default_color_to_qcolor(rgb, a)
        stil = self.color_to_style_string('QPushButton#pGraf2Detalji', boja)
        self.pGraf2Detalji.setStyleSheet(stil)

    def change_boja_pGraf3Detalji(self):
        rgb = self.__defaulti['pomocnikanal3']['color']
        a = self.__defaulti['pomocnikanal3']['alpha']
        boja = self.default_color_to_qcolor(rgb, a)
        stil = self.color_to_style_string('QPushButton#pGraf3Detalji', boja)
        self.pGraf3Detalji.setStyleSheet(stil)

    def change_boja_pGraf4Detalji(self):
        rgb = self.__defaulti['pomocnikanal4']['color']
        a = self.__defaulti['pomocnikanal4']['alpha']
        boja = self.default_color_to_qcolor(rgb, a)
        stil = self.color_to_style_string('QPushButton#pGraf4Detalji', boja)
        self.pGraf4Detalji.setStyleSheet(stil)

    def change_boja_pGraf5Detalji(self):
        rgb = self.__defaulti['pomocnikanal5']['color']
        a = self.__defaulti['pomocnikanal5']['alpha']
        boja = self.default_color_to_qcolor(rgb, a)
        stil = self.color_to_style_string('QPushButton#pGraf5Detalji', boja)
        self.pGraf5Detalji.setStyleSheet(stil)

    def change_boja_pGraf6Detalji(self):
        rgb = self.__defaulti['pomocnikanal6']['color']
        a = self.__defaulti['pomocnikanal6']['alpha']
        boja = self.default_color_to_qcolor(rgb, a)
        stil = self.color_to_style_string('QPushButton#pGraf6Detalji', boja)
        self.pGraf6Detalji.setStyleSheet(stil)

    def dijalog_glavniGrafDetalji(self):
        """dijalog za promjenu izgleda glavnog grafa"""
        #deep copy dicta za dijalog
        grafinfo = copy.deepcopy(self.__defaulti)
        #inicijalizacija dijaloga
        glavnigrafdijalog = GlavniKanalDetalji(defaulti = grafinfo)
        if glavnigrafdijalog.exec_(): #ako OK, returns 1 , isto kao i True
            grafinfo = glavnigrafdijalog.vrati_dict()
            self.__defaulti = copy.deepcopy(grafinfo)
        
    def dijalog_pGraf1Detalji(self):
        """dijalog za promjenu izgleda pomocnog grafa 1"""
        #deep copy dicta za dijalog
        grafinfo = copy.deepcopy(self.__defaulti)
        #inicijalizacija dijaloga
        pomocnigrafdijalog = PomocniGrafDetalji(defaulti = grafinfo, graf = 'pomocnikanal1')
        if pomocnigrafdijalog.exec_():
            grafinfo = pomocnigrafdijalog.vrati_dict()
            self.__defaulti = copy.deepcopy(grafinfo)
            self.change_boja_pGraf1Detalji()
            
    def dijalog_pGraf2Detalji(self):
        """dijalog za promjenu izgleda pomocnog grafa 2"""
        #deep copy dicta za dijalog
        grafinfo = copy.deepcopy(self.__defaulti)
        #inicijalizacija dijaloga
        pomocnigrafdijalog = PomocniGrafDetalji(defaulti = grafinfo, graf = 'pomocnikanal2')
        if pomocnigrafdijalog.exec_():
            grafinfo = pomocnigrafdijalog.vrati_dict()
            self.__defaulti = copy.deepcopy(grafinfo)
            self.change_boja_pGraf2Detalji()

    def dijalog_pGraf3Detalji(self):
        """dijalog za promjenu izgleda pomocnog grafa 3"""
        #deep copy dicta za dijalog
        grafinfo = copy.deepcopy(self.__defaulti)
        #inicijalizacija dijaloga
        pomocnigrafdijalog = PomocniGrafDetalji(defaulti = grafinfo, graf = 'pomocnikanal3')
        if pomocnigrafdijalog.exec_():
            grafinfo = pomocnigrafdijalog.vrati_dict()
            self.__defaulti = copy.deepcopy(grafinfo)
            self.change_boja_pGraf3Detalji()

    def dijalog_pGraf4Detalji(self):
        """dijalog za promjenu izgleda pomocnog grafa 4"""
        #deep copy dicta za dijalog
        grafinfo = copy.deepcopy(self.__defaulti)
        #inicijalizacija dijaloga
        pomocnigrafdijalog = PomocniGrafDetalji(defaulti = grafinfo, graf = 'pomocnikanal4')
        if pomocnigrafdijalog.exec_():
            grafinfo = pomocnigrafdijalog.vrati_dict()
            self.__defaulti = copy.deepcopy(grafinfo)
            self.change_boja_pGraf4Detalji()

    def dijalog_pGraf5Detalji(self):
        """dijalog za promjenu izgleda pomocnog grafa 5"""
        #deep copy dicta za dijalog
        grafinfo = copy.deepcopy(self.__defaulti)
        #inicijalizacija dijaloga
        pomocnigrafdijalog = PomocniGrafDetalji(defaulti = grafinfo, graf = 'pomocnikanal5')
        if pomocnigrafdijalog.exec_():
            grafinfo = pomocnigrafdijalog.vrati_dict()
            self.__defaulti = copy.deepcopy(grafinfo)
            self.change_boja_pGraf5Detalji()

    def dijalog_pGraf6Detalji(self):
        """dijalog za promjenu izgleda pomocnog grafa 6"""
        #deep copy dicta za dijalog
        grafinfo = copy.deepcopy(self.__defaulti)
        #inicijalizacija dijaloga
        pomocnigrafdijalog = PomocniGrafDetalji(defaulti = grafinfo, graf = 'pomocnikanal6')
        if pomocnigrafdijalog.exec_():
            grafinfo = pomocnigrafdijalog.vrati_dict()
            self.__defaulti = copy.deepcopy(grafinfo)
            self.change_boja_pGraf6Detalji()
            
    def default_color_to_qcolor(self, rgb, a):
        """
        helper funkcija za transformaciju boje u QColor
        input:
            rgb -> (r, g, b) tuple
            a -> float izmedju [0:1]
        output:
            QtGui.QColor objekt
        """
        boja = QtGui.QColor()
        #unpack tuple of rgb color
        r, g, b = rgb
        boja.setRed(r)
        boja.setGreen(g)
        boja.setBlue(b)
        #alpha je izmedju 0-1, input treba biti int 0-255
        a = int(a*255)
        boja.setAlpha(a)
        return boja
        
    def qcolor_to_default_color(self, color):
        """
        helper funkcija za transformacije qcolor u defaultnu boju
        input:
            color ->QtGui.QColor
        output:
            (r,g,b) tuple, i alpha
        """
        r = color.red()
        g = color.green()
        b = color.blue()
        a = color.alpha()/255
        return (r,g,b), a
        
    def color_to_style_string(self, target, color):
        """
        helper funkcija za izradu styleSheet stringa
        input:
            target -> string, target of background color change
                npr. 'QLabel#label1'
            color -> QtGui.QColor
        output:
            string - styleSheet 'css' style background for target element
        """
        r = color.red()
        g = color.green()
        b = color.blue()
        a = int(100*color.alpha()/255)
        stil = target + " {background: rgba(" +"{0},{1},{2},{3}%)".format(r,g,b,a)+"}"
        return stil
###############################################################################
###############################################################################

class GrafSatniSrednjaci(MPLCanvas):
    """
    Definira detalje crtanja satno agregiranog grafa i pripadne evente
    """
    def __init__(self, *args, **kwargs):
        """konstruktor"""
        MPLCanvas.__init__(self, *args, **kwargs)

        self.data = None #frejmovi
        
        self.veze()
    
    def veze(self):
        """povezivanje mpl_eventa"""
        self.mpl_connect('button_press_event', self.on_pick)

    def on_pick(self, event):
        """definiranje ponasanja pick eventa na canvasu"""
        pass
    
    def crtaj(self, lista):
        """Eksplicitne naredbe za crtanje"""
        for graf in lista:
            pass
    
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
            
if __name__=='__main__':
    #NOVA konstrukcija ulaznog dicta svih mogucih grafova 
    validanOK = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'marker':'p', 'color':(0,255,0), 'alpha':1, 'zorder':20}
    validanNOK = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'marker':'p', 'color':(255,0,0), 'alpha':1, 'zorder':20}
    nevalidanOK = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'marker':'o', 'color':(0,255,0), 'alpha':1, 'zorder':20}
    nevalidanNOK = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'marker':'o', 'color':(255,0,0), 'alpha':1, 'zorder':20}
    glavnikanal1 = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'stupac1':'min', 'marker':'+', 'line':'None', 'color':(0,0,0), 'alpha':0.9, 'zorder':8}
    glavnikanal2 = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'stupac1':'max', 'marker':'+', 'line':'None', 'color':(0,0,0), 'alpha':0.9, 'zorder':9}
    glavnikanal3 = {'crtaj':True, 'tip':'plot', 'kanal':None, 'stupac1':'median', 'marker':'None', 'line':'-', 'color':(45,86,90), 'alpha':0.9, 'zorder':10}
    glavnikanal4 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'--', 'color':(73,189,191), 'alpha':0.9, 'zorder':11}
    glavnikanalfill = {'crtaj':True, 'tip':'fill', 'kanal':None, 'stupac1':'q05', 'stupac2':'q95', 'marker':'None', 'line':'--', 'color':(31,117,229), 'alpha':0.4, 'zorder':7}
    pomocnikanal1 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(186,113,123), 'alpha':0.9, 'zorder':1}
    pomocnikanal2 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(213,164,255), 'alpha':0.9, 'zorder':2}
    pomocnikanal3 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(111,118,255), 'alpha':0.9, 'zorder':3}
    pomocnikanal4 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(149,255,147), 'alpha':0.9, 'zorder':4}
    pomocnikanal5 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(214,255,137), 'alpha':0.9, 'zorder':5}
    pomocnikanal6 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(255,64,47), 'alpha':0.9, 'zorder':6}
    opcenito = {'grid':False, 'cursor':False, 'span':False, 'minorTicks':True}        
    mapa2 = {'validanOK':validanOK, 
             'validanNOK':validanNOK, 
             'nevalidanOK':nevalidanOK, 
             'nevalidanNOK':nevalidanNOK, 
             'glavnikanal1':glavnikanal1, 
             'glavnikanal2':glavnikanal2, 
             'glavnikanal3':glavnikanal3, 
             'glavnikanal4':glavnikanal4, 
             'glavnikanalfill':glavnikanalfill, 
             'pomocnikanal1':pomocnikanal1, 
             'pomocnikanal2':pomocnikanal2, 
             'pomocnikanal3':pomocnikanal3, 
             'pomocnikanal4':pomocnikanal4, 
             'pomocnikanal5':pomocnikanal5, 
             'pomocnikanal6':pomocnikanal6, 
             'opcenito':opcenito}
             
    aplikacija = QtGui.QApplication(sys.argv)
    app = SatniGraf(parent = None, defaulti = mapa2)
    app.show()
    sys.exit(aplikacija.exec_())