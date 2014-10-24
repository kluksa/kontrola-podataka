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
import citac
from agregator import Agregator

###############################################################################
def default_color_to_qcolor(rgb, a):
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
    
def qcolor_to_default_color(color):
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
    
def color_to_style_string(target, color):
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
    
    Dict defaulti je specifican. Mora prosljediti konsturktoru. 
    Sadrzi postavke svih mogucih grafova (boja, da li se crtaju...)
    """
    def __init__(self, parent = None, defaulti = None):
        super(base, self).__init__(parent)
        self.setupUi(self)
        
        #sve opcije su sadrzane u dictu defaulti
        self.__defaulti = defaulti
        
        self.__sviMarkeri = ['None', 'o', 'v', '^', '<', '>', 's', 'p', '*', 'h', '+', 'x', 'd', '_', '|']
        self.__sveLinije = ['None', '-', '--', '-.', ':']
        self.__sviPodaci = ['min', 'max', 'median', 'avg', 'q05', 'q95']
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
        boja = default_color_to_qcolor(defaultBoja, defaultAlpha)
        stil = color_to_style_string('QPushButton#colorOK', boja)
        self.colorOK.setStyleSheet(stil)
        defaultBoja = self.__defaulti['validanNOK']['color']
        defaultAlpha = self.__defaulti['validanNOK']['alpha']
        boja = default_color_to_qcolor(defaultBoja, defaultAlpha)
        stil = color_to_style_string('QPushButton#colorNOK', boja)
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
        boja = default_color_to_qcolor(defaultBoja, defaultAlpha)
        stil = color_to_style_string('QPushButton#kanal1Boja', boja)
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
        boja = default_color_to_qcolor(defaultBoja, defaultAlpha)
        stil = color_to_style_string('QPushButton#kanal2Boja', boja)
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
        boja = default_color_to_qcolor(defaultBoja, defaultAlpha)
        stil = color_to_style_string('QPushButton#kanal3Boja', boja)
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
        boja = default_color_to_qcolor(defaultBoja, defaultAlpha)
        stil = color_to_style_string('QPushButton#kanal4Boja', boja)
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
        boja = default_color_to_qcolor(defaultBoja, defaultAlpha)
        stil = color_to_style_string('QPushButton#fillBoja', boja)
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
            self.__defaulti['glavnikanal1']['crtaj'] = True
        else:
            self.kanal1Komponenta.setEnabled(False)
            self.kanal1Marker.setEnabled(False)
            self.kanal1Linija.setEnabled(False)
            self.kanal1Boja.setEnabled(False)
            self.kanal1Tip.setEnabled(False)
            self.__defaulti['glavnikanal1']['crtaj'] = False
            
    def enable_graf2(self):
        """toggle checkbox, enables or disables related controls"""
        if self.kanal2Check.isChecked() == True:
            self.kanal2Komponenta.setEnabled(True)
            self.kanal2Marker.setEnabled(True)
            self.kanal2Linija.setEnabled(True)
            self.kanal2Boja.setEnabled(True)
            self.kanal2Tip.setEnabled(True)
            self.__defaulti['glavnikanal2']['crtaj'] = True
        else:
            self.kanal2Komponenta.setEnabled(False)
            self.kanal2Marker.setEnabled(False)
            self.kanal2Linija.setEnabled(False)
            self.kanal2Boja.setEnabled(False)
            self.kanal2Tip.setEnabled(False)
            self.__defaulti['glavnikanal2']['crtaj'] = False

    def enable_graf3(self):
        """toggle checkbox, enables or disables related controls"""
        if self.kanal3Check.isChecked() == True:
            self.kanal3Komponenta.setEnabled(True)
            self.kanal3Marker.setEnabled(True)
            self.kanal3Linija.setEnabled(True)
            self.kanal3Boja.setEnabled(True)
            self.kanal3Tip.setEnabled(True)
            self.__defaulti['glavnikanal3']['crtaj'] = True
        else:
            self.kanal3Komponenta.setEnabled(False)
            self.kanal3Marker.setEnabled(False)
            self.kanal3Linija.setEnabled(False)
            self.kanal3Boja.setEnabled(False)
            self.kanal3Tip.setEnabled(False)
            self.__defaulti['glavnikanal3']['crtaj'] = False

    def enable_graf4(self):
        """toggle checkbox, enables or disables related controls"""
        if self.kanal4Check.isChecked() == True:
            self.kanal4Komponenta.setEnabled(True)
            self.kanal4Marker.setEnabled(True)
            self.kanal4Linija.setEnabled(True)
            self.kanal4Boja.setEnabled(True)
            self.kanal4Tip.setEnabled(True)
            self.__defaulti['glavnikanal4']['crtaj'] = True
        else:
            self.kanal4Komponenta.setEnabled(False)
            self.kanal4Marker.setEnabled(False)
            self.kanal4Linija.setEnabled(False)
            self.kanal4Boja.setEnabled(False)
            self.kanal4Tip.setEnabled(False)
            self.__defaulti['glavnikanal4']['crtaj'] = False

    def enable_fill(self):
        """toggle checkbox, enables or disables related controls"""
        if self.fillCheck.isChecked() == True:
            self.fillKomponenta1.setEnabled(True)
            self.fillKomponenta2.setEnabled(True)
            self.fillBoja.setEnabled(True)
            self.__defaulti['glavnikanalfill']['crtaj'] = True
        else:
            self.fillKomponenta1.setEnabled(False)
            self.fillKomponenta2.setEnabled(False)
            self.fillBoja.setEnabled(False)
            self.__defaulti['glavnikanalfill']['crtaj'] = False
    
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
        boja = default_color_to_qcolor(defaultBoja, defaultAlpha)
        #dijalog
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test za validnu boju
            color = QtGui.QColor.fromRgba(color)
            rgb, a = qcolor_to_default_color(color)
            #update dict
            self.__defaulti['validanOK']['color'] = rgb
            self.__defaulti['validanOK']['alpha'] = a
            self.__defaulti['nevalidanOK']['color'] = rgb
            self.__defaulti['nevalidanOK']['alpha'] = a
            #set new color
            stil = color_to_style_string('QPushButton#colorOK', color)
            self.colorOK.setStyleSheet(stil)
   
    def change_colorNOK(self):
        defaultBoja = self.__defaulti['validanNOK']['color']
        defaultAlpha = self.__defaulti['validanNOK']['alpha']
        boja = default_color_to_qcolor(defaultBoja, defaultAlpha)
        #dijalog
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test za validnu boju
            color = QtGui.QColor.fromRgba(color)
            rgb, a = qcolor_to_default_color(color)
            #update dict
            self.__defaulti['validanNOK']['color'] = rgb
            self.__defaulti['validanNOK']['alpha'] = a
            self.__defaulti['nevalidanNOK']['color'] = rgb
            self.__defaulti['nevalidanNOK']['alpha'] = a
            #set new color
            stil = color_to_style_string('QPushButton#colorNOK', color)
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
        boja = default_color_to_qcolor(defaultBoja, defaultAlpha)
        #dijalog
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test za validnu boju
            color = QtGui.QColor.fromRgba(color)
            rgb, a = qcolor_to_default_color(color)
            #update dict
            self.__defaulti['glavnikanal1']['color'] = rgb
            self.__defaulti['glavnikanal1']['alpha'] = a
            #set new color
            stil = color_to_style_string('QPushButton#kanal1Boja', color)
            self.kanal1Boja.setStyleSheet(stil)
    
    def change_kanal2Boja(self):
        defaultBoja = self.__defaulti['glavnikanal2']['color']
        defaultAlpha = self.__defaulti['glavnikanal2']['alpha']
        boja = default_color_to_qcolor(defaultBoja, defaultAlpha)
        #dijalog
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test za validnu boju
            color = QtGui.QColor.fromRgba(color)
            rgb, a = qcolor_to_default_color(color)
            #update dict
            self.__defaulti['glavnikanal2']['color'] = rgb
            self.__defaulti['glavnikanal2']['alpha'] = a
            #set new color
            stil = color_to_style_string('QPushButton#kanal2Boja', color)
            self.kanal2Boja.setStyleSheet(stil)
    
    def change_kanal3Boja(self):
        defaultBoja = self.__defaulti['glavnikanal3']['color']
        defaultAlpha = self.__defaulti['glavnikanal3']['alpha']
        boja = default_color_to_qcolor(defaultBoja, defaultAlpha)
        #dijalog
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test za validnu boju
            color = QtGui.QColor.fromRgba(color)
            rgb, a = qcolor_to_default_color(color)
            #update dict
            self.__defaulti['glavnikanal3']['color'] = rgb
            self.__defaulti['glavnikanal3']['alpha'] = a
            #set new color
            stil = color_to_style_string('QPushButton#kanal3Boja', color)
            self.kanal3Boja.setStyleSheet(stil)
    
    def change_kanal4Boja(self):
        defaultBoja = self.__defaulti['glavnikanal4']['color']
        defaultAlpha = self.__defaulti['glavnikanal4']['alpha']
        boja = default_color_to_qcolor(defaultBoja, defaultAlpha)
        #dijalog
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test za validnu boju
            color = QtGui.QColor.fromRgba(color)
            rgb, a = qcolor_to_default_color(color)
            #update dict
            self.__defaulti['glavnikanal4']['color'] = rgb
            self.__defaulti['glavnikanal4']['alpha'] = a
            #set new color
            stil = color_to_style_string('QPushButton#kanal4Boja', color)
            self.kanal4Boja.setStyleSheet(stil)
    
    def change_fillBoja(self):
        defaultBoja = self.__defaulti['glavnikanalfill']['color']
        defaultAlpha = self.__defaulti['glavnikanalfill']['alpha']
        boja = default_color_to_qcolor(defaultBoja, defaultAlpha)
        #dijalog
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test za validnu boju
            color = QtGui.QColor.fromRgba(color)
            rgb, a = qcolor_to_default_color(color)
            #update dict
            self.__defaulti['glavnikanalfill']['color'] = rgb
            self.__defaulti['glavnikanalfill']['alpha'] = a
            #set new color
            stil = color_to_style_string('QPushButton#fillBoja', color)
            self.fillBoja.setStyleSheet(stil)
        
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
        self.__sviPodaci = ['min', 'max', 'median', 'avg', 'q05', 'q95']
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
        boja = default_color_to_qcolor(rgb, a)
        #dijalog
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test za validnu boju
            color = QtGui.QColor.fromRgba(color)
            rgb, a = qcolor_to_default_color(color)
            #update dict
            self.__defaulti[self.__graf]['color'] = rgb
            self.__defaulti[self.__graf]['alpha'] = a
            #set new color
            stil = color_to_style_string('QPushButton#boja', color)
            self.boja.setStyleSheet(stil)
    
    def popuni_izbornike(self):
        """inicijalizacija izbornika sa defaultinim postavkama"""
        naziv = 'Detalji pomocnog grafa, kanal: ' + str(self.__defaulti[self.__graf]['kanal'])
        self.groupBox.setTitle(str(self.__defaulti[self.__graf]['kanal']))
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
        color = default_color_to_qcolor(rgb, a)
        stil = color_to_style_string('QPushButton#boja', color)
        self.boja.setStyleSheet(stil)

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
    def __init__(self, parent = None, defaulti = None, frejmovi = None):
        super(base2, self).__init__(parent)
        self.setupUi(self)
        
        #defaultini izbor za grafove
        self.__defaulti = defaulti
        self.__agregiraniFrejmovi = frejmovi
        #inicijalizacija ostalih grafickih elemenata
        self.widget1 = QtGui.QWidget()
        self.widget2 = QtGui.QWidget()
        #inicijalizacija canvasa na mjesto self.grafWidget
        self.canvasSatni = GrafSatniSrednjaci(parent = self.widget1)
        #inicijalizacija Navigation bara
        self.mplToolbar = NavigationToolbar(self.canvasSatni, self.widget2)
        self.graphLayout.addWidget(self.canvasSatni)
        self.graphLayout.addWidget(self.mplToolbar)
        #toggle gumb za sakrivanje izbora grafa...
        self.toggleDetalji.toggled.connect(self.groupBox.setVisible)
        self.toggleDetalji.toggled.connect(self.groupBox_2.setVisible)
                
        self.veze()
        self.initial_setup()
        #opis slicea : slice od: do:
        self.labelSlice.setText('Prikazano vrijeme:')
        
    def zamjeni_frejmove(self, frejmovi):
        self.__agregiraniFrejmovi = frejmovi
        self.initial_setup()
        
    def initial_setup(self):
        """inicijalne postavke izbornika (stanje comboboxeva, checkboxeva...)"""
        self.tmin = None
        self.tmax = None
        
        self.canvasSatni.__statusGlavniGraf = False
        self.canvasSatni.__testAnnotation = False
        self.canvasSatni.__zadnjiHighlightx = None
        self.canvasSatni.__zadnjiHighlighty = None
        self.canvasSatni.__zadnjiAnnotationx = None        

        
        if self.__agregiraniFrejmovi != None:
            self.tmin, self.tmax = self.plot_time_span()
            naslov = 'Prikazano vrijeme od: '+str(self.tmin)+' do: '+str(self.tmax)
            self.labelSlice.setText(naslov)
        
        #checkboxes
        self.glavniGrafCheck.setChecked(self.__defaulti['validanOK']['crtaj'])
        self.pGraf1Check.setChecked(self.__defaulti['pomocnikanal1']['crtaj'])
        self.pGraf2Check.setChecked(self.__defaulti['pomocnikanal2']['crtaj'])
        self.pGraf3Check.setChecked(self.__defaulti['pomocnikanal3']['crtaj'])
        self.pGraf4Check.setChecked(self.__defaulti['pomocnikanal4']['crtaj'])
        self.pGraf5Check.setChecked(self.__defaulti['pomocnikanal5']['crtaj'])
        self.pGraf6Check.setChecked(self.__defaulti['pomocnikanal6']['crtaj'])
        
        #button colors
        self.change_boja_pGraf1Detalji()
        self.change_boja_pGraf2Detalji()
        self.change_boja_pGraf3Detalji()
        self.change_boja_pGraf4Detalji()
        self.change_boja_pGraf5Detalji()
        self.change_boja_pGraf6Detalji()
               
        if self.__agregiraniFrejmovi != None:
            #popis svih dostupnih kanala
            kanali = sorted(list(self.__agregiraniFrejmovi.keys()))
            zadnjiKanal = self.__defaulti['validanOK']['kanal']
            self.glavniGrafIzbor.blockSignals(True)            
            self.glavniGrafIzbor.clear()
            self.glavniGrafIzbor.addItems(kanali)
            if zadnjiKanal != None:
                ind = self.glavniGrafIzbor.findText(zadnjiKanal)
                self.glavniGrafIzbor.setCurrentIndex(ind)
            self.glavniGrafIzbor.blockSignals(False)
            noviKanal = self.glavniGrafIzbor.currentText()
            self.__defaulti['validanOK']['kanal'] = noviKanal
            self.__defaulti['validanNOK']['kanal'] = noviKanal
            self.__defaulti['nevalidanOK']['kanal'] = noviKanal
            self.__defaulti['nevalidanNOK']['kanal'] = noviKanal
            self.__defaulti['glavnikanal1']['kanal'] = noviKanal
            self.__defaulti['glavnikanal2']['kanal'] = noviKanal
            self.__defaulti['glavnikanal3']['kanal'] = noviKanal
            self.__defaulti['glavnikanal4']['kanal'] = noviKanal
            self.__defaulti['glavnikanalfill']['kanal'] = noviKanal

            zadnjiKanal = self.__defaulti['pomocnikanal1']['kanal']
            self.pGraf1Izbor.blockSignals(True)
            self.pGraf1Izbor.clear()
            self.pGraf1Izbor.addItems(kanali)
            if zadnjiKanal != None:
                ind = self.pGraf1Izbor.findText(zadnjiKanal)
                self.pGraf1Izbor.setCurrentIndex(ind)
            self.pGraf1Izbor.blockSignals(False)
            noviKanal = self.pGraf1Izbor.currentText()
            self.__defaulti['pomocnikanal1']['kanal'] = noviKanal
                
            zadnjiKanal = self.__defaulti['pomocnikanal2']['kanal']
            self.pGraf2Izbor.blockSignals(True)
            self.pGraf2Izbor.clear()
            self.pGraf2Izbor.addItems(kanali)
            if zadnjiKanal != None:
                ind = self.pGraf2Izbor.findText(zadnjiKanal)
                self.pGraf2Izbor.setCurrentIndex(ind)
            self.pGraf2Izbor.blockSignals(False)
            noviKanal = self.pGraf2Izbor.currentText()
            self.__defaulti['pomocnikanal2']['kanal'] = noviKanal

            zadnjiKanal = self.__defaulti['pomocnikanal3']['kanal']
            self.pGraf3Izbor.blockSignals(True)
            self.pGraf3Izbor.clear()
            self.pGraf3Izbor.addItems(kanali)
            if zadnjiKanal != None:
                ind = self.pGraf3Izbor.findText(zadnjiKanal)
                self.pGraf3Izbor.setCurrentIndex(ind)
            self.pGraf3Izbor.blockSignals(False)
            noviKanal = self.pGraf3Izbor.currentText()
            self.__defaulti['pomocnikanal3']['kanal'] = noviKanal
            
            zadnjiKanal = self.__defaulti['pomocnikanal4']['kanal']
            self.pGraf4Izbor.blockSignals(True)
            self.pGraf4Izbor.clear()
            self.pGraf4Izbor.addItems(kanali)
            if zadnjiKanal != None:
                ind = self.pGraf4Izbor.findText(zadnjiKanal)
                self.pGraf4Izbor.setCurrentIndex(ind)
            self.pGraf4Izbor.blockSignals(False)
            noviKanal = self.pGraf4Izbor.currentText()
            self.__defaulti['pomocnikanal4']['kanal'] = noviKanal
            
            zadnjiKanal = self.__defaulti['pomocnikanal5']['kanal']
            self.pGraf5Izbor.blockSignals(True)
            self.pGraf5Izbor.clear()
            self.pGraf5Izbor.addItems(kanali)
            if zadnjiKanal != None:
                ind = self.pGraf5Izbor.findText(zadnjiKanal)
                self.pGraf5Izbor.setCurrentIndex(ind)
            self.pGraf5Izbor.blockSignals(False)
            noviKanal = self.pGraf5Izbor.currentText()
            self.__defaulti['pomocnikanal5']['kanal'] = noviKanal
            
            zadnjiKanal = self.__defaulti['pomocnikanal6']['kanal']
            self.pGraf6Izbor.blockSignals(True)
            self.pGraf6Izbor.clear()
            self.pGraf6Izbor.addItems(kanali)
            if zadnjiKanal != None:
                ind = self.pGraf6Izbor.findText(zadnjiKanal)
                self.pGraf6Izbor.setCurrentIndex(ind)
            self.pGraf6Izbor.blockSignals(False)
            noviKanal = self.pGraf6Izbor.currentText()
            self.__defaulti['pomocnikanal6']['kanal'] = noviKanal
            #naredba za crtanje je zadnja kod inicijalizacije
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)            
            
    def veze(self):
        """poveznice izmedju kontrolnih elemenata i funkcija koje mjenjaju stanja"""
        #BITNO... SVE FUNKCIJE KOJE MJENJAJU NEKE POSTAVKE GRAFA MORAJU POZIVATI
        #PONOVNO CRTANJE!
        #naredba za crtanje (ulazni podaci su dict opisa grafa, dict frejmova)
        #self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
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
        
    def enable_grid(self, x):
        if x:
            self.__defaulti['opcenito']['grid'] = True
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
        else:
            self.__defaulti['opcenito']['grid'] = False
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
    
    def enable_cursor(self, x):
        if x:
            self.__defaulti['opcenito']['cursor'] = True
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
        else:
            self.__defaulti['opcenito']['cursor'] = False
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
    
    def enable_spanSelector(self, x):
        if x:
            self.__defaulti['opcenito']['span'] = True
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
        else:
            self.__defaulti['opcenito']['span'] = False
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
    
    def enable_minorTick(self, x):
        if x:
            self.__defaulti['opcenito']['minorTicks'] = True
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
        else:
            self.__defaulti['opcenito']['minorTicks'] = False
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
    
    def enable_glavni_kanal(self):
        if self.glavniGrafCheck.isChecked() == True:
            self.glavniGrafIzbor.setEnabled(True)
            self.glavniGrafDetalji.setEnabled(True)
            self.__defaulti['validanOK']['crtaj'] = True
            self.__defaulti['validanNOK']['crtaj'] = True
            self.__defaulti['nevalidanOK']['crtaj'] = True
            self.__defaulti['nevalidanNOK']['crtaj'] = True
            self.__defaulti['glavnikanal1']['crtaj'] = True
            self.__defaulti['glavnikanal2']['crtaj'] = True
            self.__defaulti['glavnikanal3']['crtaj'] = True
            self.__defaulti['glavnikanal4']['crtaj'] = True
            self.__defaulti['glavnikanalfill']['crtaj'] = True
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
        else:
            self.glavniGrafIzbor.setEnabled(False)
            self.glavniGrafDetalji.setEnabled(False)
            self.__defaulti['validanOK']['crtaj'] = False
            self.__defaulti['validanNOK']['crtaj'] = False
            self.__defaulti['nevalidanOK']['crtaj'] = False
            self.__defaulti['nevalidanNOK']['crtaj'] = False
            self.__defaulti['glavnikanal1']['crtaj'] = False
            self.__defaulti['glavnikanal2']['crtaj'] = False
            self.__defaulti['glavnikanal3']['crtaj'] = False
            self.__defaulti['glavnikanal4']['crtaj'] = False
            self.__defaulti['glavnikanalfill']['crtaj'] = False
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)

    def enable_pomocni_kanal1(self):
        if self.pGraf1Check.isChecked() == True:
            self.pGraf1Izbor.setEnabled(True)
            self.pGraf1Detalji.setEnabled(True)
            self.__defaulti['pomocnikanal1']['crtaj'] = True
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
        else:
            self.pGraf1Izbor.setEnabled(False)
            self.pGraf1Detalji.setEnabled(False)
            self.__defaulti['pomocnikanal1']['crtaj'] = False
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
            
    def enable_pomocni_kanal2(self):
        if self.pGraf2Check.isChecked() == True:
            self.pGraf2Izbor.setEnabled(True)
            self.pGraf2Detalji.setEnabled(True)
            self.__defaulti['pomocnikanal2']['crtaj'] = True
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
        else:
            self.pGraf2Izbor.setEnabled(False)
            self.pGraf2Detalji.setEnabled(False)
            self.__defaulti['pomocnikanal2']['crtaj'] = False
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
    
    def enable_pomocni_kanal3(self):
        if self.pGraf3Check.isChecked() == True:
            self.pGraf3Izbor.setEnabled(True)
            self.pGraf3Detalji.setEnabled(True)
            self.__defaulti['pomocnikanal3']['crtaj'] = True
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
        else:
            self.pGraf3Izbor.setEnabled(False)
            self.pGraf3Detalji.setEnabled(False)
            self.__defaulti['pomocnikanal3']['crtaj'] = False
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)

    def enable_pomocni_kanal4(self):
        if self.pGraf4Check.isChecked() == True:
            self.pGraf4Izbor.setEnabled(True)
            self.pGraf4Detalji.setEnabled(True)
            self.__defaulti['pomocnikanal4']['crtaj'] = True
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
        else:
            self.pGraf4Izbor.setEnabled(False)
            self.pGraf4Detalji.setEnabled(False)
            self.__defaulti['pomocnikanal4']['crtaj'] = False
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)

    def enable_pomocni_kanal5(self):
        if self.pGraf5Check.isChecked() == True:
            self.pGraf5Izbor.setEnabled(True)
            self.pGraf5Detalji.setEnabled(True)
            self.__defaulti['pomocnikanal5']['crtaj'] = True
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
        else:
            self.pGraf5Izbor.setEnabled(False)
            self.pGraf5Detalji.setEnabled(False)
            self.__defaulti['pomocnikanal5']['crtaj'] = False
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)

    def enable_pomocni_kanal6(self):
        if self.pGraf6Check.isChecked() == True:
            self.pGraf6Izbor.setEnabled(True)
            self.pGraf6Detalji.setEnabled(True)
            self.__defaulti['pomocnikanal6']['crtaj'] = True
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
        else:
            self.pGraf6Izbor.setEnabled(False)
            self.pGraf6Detalji.setEnabled(False)
            self.__defaulti['pomocnikanal6']['crtaj'] = False
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)

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
        self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
    
    def update_pomocni_kanal1(self):
        newValue = self.pGraf1Izbor.currentText()
        self.__defaulti['pomocnikanal1']['kanal'] = newValue
        self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
    
    def update_pomocni_kanal2(self):
        newValue = self.pGraf2Izbor.currentText()
        self.__defaulti['pomocnikanal2']['kanal'] = newValue
        self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
    
    def update_pomocni_kanal3(self):
        newValue = self.pGraf3Izbor.currentText()
        self.__defaulti['pomocnikanal3']['kanal'] = newValue
        self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
    
    def update_pomocni_kanal4(self):
        newValue = self.pGraf4Izbor.currentText()
        self.__defaulti['pomocnikanal4']['kanal'] = newValue
        self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
    
    def update_pomocni_kanal5(self):
        newValue = self.pGraf5Izbor.currentText()
        self.__defaulti['pomocnikanal5']['kanal'] = newValue
        self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
    
    def update_pomocni_kanal6(self):
        newValue = self.pGraf6Izbor.currentText()
        self.__defaulti['pomocnikanal6']['kanal'] = newValue
        self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
        
    def change_boja_pGraf1Detalji(self):
        rgb = self.__defaulti['pomocnikanal1']['color']
        a = self.__defaulti['pomocnikanal1']['alpha']
        boja = default_color_to_qcolor(rgb, a)
        stil = color_to_style_string('QPushButton#pGraf1Detalji', boja)
        self.pGraf1Detalji.setStyleSheet(stil)
        
    def change_boja_pGraf2Detalji(self):
        rgb = self.__defaulti['pomocnikanal2']['color']
        a = self.__defaulti['pomocnikanal2']['alpha']
        boja = default_color_to_qcolor(rgb, a)
        stil = color_to_style_string('QPushButton#pGraf2Detalji', boja)
        self.pGraf2Detalji.setStyleSheet(stil)

    def change_boja_pGraf3Detalji(self):
        rgb = self.__defaulti['pomocnikanal3']['color']
        a = self.__defaulti['pomocnikanal3']['alpha']
        boja = default_color_to_qcolor(rgb, a)
        stil = color_to_style_string('QPushButton#pGraf3Detalji', boja)
        self.pGraf3Detalji.setStyleSheet(stil)

    def change_boja_pGraf4Detalji(self):
        rgb = self.__defaulti['pomocnikanal4']['color']
        a = self.__defaulti['pomocnikanal4']['alpha']
        boja = default_color_to_qcolor(rgb, a)
        stil = color_to_style_string('QPushButton#pGraf4Detalji', boja)
        self.pGraf4Detalji.setStyleSheet(stil)

    def change_boja_pGraf5Detalji(self):
        rgb = self.__defaulti['pomocnikanal5']['color']
        a = self.__defaulti['pomocnikanal5']['alpha']
        boja = default_color_to_qcolor(rgb, a)
        stil = color_to_style_string('QPushButton#pGraf5Detalji', boja)
        self.pGraf5Detalji.setStyleSheet(stil)

    def change_boja_pGraf6Detalji(self):
        rgb = self.__defaulti['pomocnikanal6']['color']
        a = self.__defaulti['pomocnikanal6']['alpha']
        boja = default_color_to_qcolor(rgb, a)
        stil = color_to_style_string('QPushButton#pGraf6Detalji', boja)
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
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
        
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
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
            
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
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)

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
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)

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
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)

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
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)

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
            self.canvasSatni.crtaj(self.__defaulti, self.__agregiraniFrejmovi)
            
    def plot_time_span(self):
        """Vraca granice plota, min i max prikazano vrijeme"""
        duljina = 0
        najveci = None
        for frejm in self.__agregiraniFrejmovi:
            l = len(self.__agregiraniFrejmovi[frejm])
            if l > duljina:
                najveci = frejm
                duljina = l
        
        xmin = self.__agregiraniFrejmovi[najveci].index.min()
        xmax = self.__agregiraniFrejmovi[najveci].index.max()
        xmin = pd.to_datetime(xmin.date())
        xmax = pd.to_datetime(xmax.date())
        xmin = xmin - timedelta(hours = 1)
        xmin = pd.to_datetime(xmin)
        xmax = xmax + timedelta(hours = 1)
        xmax = pd.to_datetime(xmax)
        return xmin, xmax
###############################################################################
###############################################################################
class GrafSatniSrednjaci(MPLCanvas):
    """
    Definira detalje crtanja satno agregiranog grafa i pripadne evente
    """
    def __init__(self, *args, **kwargs):
        """konstruktor"""
        MPLCanvas.__init__(self, *args, **kwargs)
        
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.__defaulti = None
        self.__data = None
        self.__statusGlavniGraf = False #da li je nacrtan glavni graf
        self.__statusSpanSelector = False #da li je span selector aktivan
        #min i max, vremenski raspon glavnog kanala
        self.__tmin, self.__tmax = self.xlimit_glavnog_kanala()
        #highlight
        self.__zadnjiHighlightx = None #xpoint zadnjeg highlighta
        self.__zadnjiHighlighty = None #ypoint zadnjeg highlighta
        self.__testHighlight = False #test da li je highligt nacrtan
        #annotation
        self.__zadnjiAnnotationx = None
        self.__testAnnotation = False
        
        self.veze()

    def show_menu(self, pos, tmin, tmax):
        self.__lastTimeMin = tmin
        self.__lastTimeMax = tmax
        menu = QtGui.QMenu(self)
        menu.setTitle('Promjeni flag')
        action1 = QtGui.QAction("Flag: Dobar", menu) #pozitivan flag
        action2 = QtGui.QAction("Flag: Los", menu) #negativan flag
        menu.addAction(action1)
        menu.addAction(action2)
        action1.triggered.connect(self.dijalog_promjena_flaga_OK)
        action2.triggered.connect(self.dijalog_promjena_flaga_NOK)
        menu.popup(pos)
    
    def dijalog_promjena_flaga_OK(self):
        tmin = self.__lastTimeMin
        tmax = self.__lastTimeMax
        #pomak slicea da uhvati sve ciljane minutne podatke
        tmin = tmin - timedelta(minutes = 59)
        tmin = pd.to_datetime(tmin)
        arg = [tmin, tmax, 1000]
        #sredi generalni emit za promjenu flaga
        self.emit(QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), arg)
        
    def dijalog_promjena_flaga_NOK(self):
        tmin = self.__lastTimeMin
        tmax = self.__lastTimeMax
        #pomak slicea da uhvati sve ciljane minutne podatke
        tmin = tmin - timedelta(minutes = 59)
        tmin = pd.to_datetime(tmin)
        arg = [tmin, tmax, -1000]
        #sredi generalni emit za promjenu flaga
        self.emit(QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), arg)
        
    def veze(self):
        """povezivanje mpl_eventa"""
        self.mpl_connect('button_press_event', self.on_pick)

    def on_pick(self, event):
        """definiranje ponasanja pick eventa na canvasu"""

        #XXX!
        """
        UPOZORENJE!!!
        
        Ovaj dio koda rijesava konflikte prilikom zoom/pan akcija na
        toolbaru. Postoje dva problema:
        
        1.
        ._active nije namjenjen da ga se dohvati metodom i mogu ga 
        nenajavljeno promjeniti u nekoj drugoj verziji matplotliba
        
        2. 
        parent mora imati member mplToolar tipa NavigationToolbar2QT, 
        koji mora biti povezan sa ovim canvasom.
        
        Radi na Matplotlib 1.3.1
        
        ._active == None ako su Pan i Zoom opcije iskljucene
        ._active == 'PAN' ako je pan/zoom opcija ukljucena
        ._active == 'ZOOM' ako je zoom rect opcija ukljucena
        """
        #od parenta dohvati toolbar, tj. njegovo stanje
        stanje = self.parent().mplToolbar._active
                
        if self.__statusGlavniGraf and event.inaxes == self.axes and stanje == None:
            xpoint = matplotlib.dates.num2date(event.xdata) #datetime.datetime
            #problem.. rounding offset aware i offset naive datetimes..workaround
            xpoint = datetime.datetime(xpoint.year, 
                                       xpoint.month, 
                                       xpoint.day, 
                                       xpoint.hour, 
                                       xpoint.minute, 
                                       xpoint.second)
            xpoint = zaokruzi_vrijeme(xpoint, 3600)
            xpoint = pd.to_datetime(xpoint)
            #pobrini se da xpoint ne prelazi granice zadanih podataka glavnog kanala
            if xpoint >= self.__tmax:
                xpoint = self.__tmax
            if xpoint <= self.__tmin:
                xpoint = self.__tmin

            #highlight selected point - kooridinate ako nedostaju podaci
            trenutniGlavniKanal = self.__defaulti['validanOK']['kanal']
            
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
                    #sami annotation
                    self.annotation = self.axes.annotate(
                        tekst, 
                        xy = (xpoint, ypoint), 
                        xytext = (clickedx, clickedy), 
                        textcoords = 'offset points', 
                        ha = 'left', 
                        va = 'center', 
                        fontsize = 7, 
                        zorder = 22, 
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
                            zorder = 22, 
                            bbox = dict(boxstyle = 'square', fc = 'cyan', alpha = 0.7), 
                            arrowprops = dict(arrowstyle = '->'))
                        self.draw()
            
            if event.button == 3:
                #flag change
                
                #test da li je span aktivan
                if self.__statusSpanSelector == False:
                    #poziva context menu sa informacijom o lokaciji i satu
                    loc = QtGui.QCursor.pos()
                    self.show_menu(loc, xpoint, xpoint)
    
    def satni_span_flag(self, tmin, tmax):
        """satni span selector"""
        if self.__statusGlavniGraf: #glavni graf mora biti nacrtan
            tmin = matplotlib.dates.num2date(tmin)
            tmax = matplotlib.dates.num2date(tmax)
            tmin = datetime.datetime(tmin.year, tmin.month, tmin.day, tmin.hour, tmin.minute, tmin.second)
            tmax = datetime.datetime(tmax.year, tmax.month, tmax.day, tmax.hour, tmax.minute, tmax.second)
            tmin = zaokruzi_vrijeme(tmin, 3600)
            tmax = zaokruzi_vrijeme(tmax, 3600)
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
                
            if tmin != tmax: #tocke ne smiju biti iste
                #pozovi dijalog za promjenu flaga
                loc = QtGui.QCursor.pos()
                self.show_menu(loc, tmin, tmax)
    
    def normalize_rgb(self, rgbTuple):
        """konverter za plotanje, mpl kao color ima sequence vrijednosti 
        izmedju [0-1]"""
        r, g, b = rgbTuple
        return (r/255, g/255, b/255)

    def xlimit_glavnog_kanala(self):
        """FUnkcija vraca tmin i tmax, vremenski raspon glavnog kanala"""
        if self.__defaulti != None and self.__data != None:
            glavniKanal = self.__defaulti['validanOK']['kanal']
            tmin = self.__data[glavniKanal].index.min()
            tmax = self.__data[glavniKanal].index.max()
            return tmin, tmax
        else:
            return None, None
        
        
    def xlimit_grafa(self):
        """
        Funkcija vraca 2 vrijednosti za sirinu grafa.
        
        1.nalazi najdulji frejm (najvise podataka)
        2.nalazi rubne indexe tog frejma
        3.odmice ih za 1 sat (od vrijednosti datuma)
        """
        if self.__data != None:
            duljina = 0
            najveci = None
            for frejm in self.__data:
                l = len(self.__data[frejm])
                if l > duljina:
                    najveci = frejm
                    duljina = l
                    
            xmin = self.__data[najveci].index.min()
            xmax = self.__data[najveci].index.max()
            xmin = pd.to_datetime(xmin.date())
            xmax = pd.to_datetime(xmax.date())
            xmin = xmin - timedelta(hours = 1)
            xmin = pd.to_datetime(xmin)
            xmax = xmax + timedelta(hours = 1)
            xmax = pd.to_datetime(xmax)
            return xmin, xmax
        else:
            return 0, 1

            
    def highlight_dot(self, x, y):
        """Highligt zuti dot kao vizualni marker za odabranu tocku"""
        if not self.__testHighlight and self.__statusGlavniGraf:
            self.hdot = self.axes.scatter(x, 
                                          y, 
                                          s = 100, 
                                          color = 'yellow', 
                                          alpha = 0.5, 
                                          zorder = 21)
            self.__zadnjiHighlightx = x
            self.__zadnjiHighlighty = y
            self.__testHighlight = True
            self.draw()

    
    def crtaj(self, mapaGrafova, satniFrejmovi):
        """Eksplicitne naredbe za crtanje
        
        ulaz:
        mapaGrafova -> defaultni dict sa opcijama grafova
        satniFrejmovi -> izvor podataka za crtanje
        """
        
        self.__defaulti = mapaGrafova
        self.__data = satniFrejmovi
        self.axes.clear()
        self.__statusGlavniGraf = False
        self.__testAnnotation = False
        
        self.xmin, self.xmax = self.xlimit_grafa()
        self.__tmin, self.__tmax = self.xlimit_glavnog_kanala()
        self.axes.set_xlim(self.xmin, self.xmax)
        
        #format x kooridinate
        xLabels = self.axes.get_xticklabels()
        for label in xLabels:
            label.set_rotation(20)
            label.set_fontsize(8)

        #test opcenitih postavki priije crtanja : cursor, grid...
        if self.__defaulti['opcenito']['cursor'] == True:
            self.cursor = Cursor(self.axes, useblit = True, color = 'tomato', linewidth = 1)
        else:
            self.cursor = None

        if self.__defaulti['opcenito']['grid'] == True:
            self.axes.grid(True)
        else:
            self.axes.grid(False)
            
        if self.__defaulti['opcenito']['minorTicks'] == True:
            self.axes.minorticks_on()
        else:
            self.axes.minorticks_off()
        
        if self.__defaulti['opcenito']['span'] == True:
            self.__statusSpanSelector = True
            self.spanSelector = SpanSelector(self.axes, 
                                             self.satni_span_flag, 
                                             direction = 'horizontal', 
                                             useblit = True, 
                                             rectprops = dict(alpha = 0.3, facecolor = 'yellow'))
        else:
            self.spanSelector = None
            self.__statusSpanSelector = False
        
        plotlista = ['validanOK', 'validanNOK', 'nevalidanOK', 
                     'nevalidanNOK', 'glavnikanal1', 'glavnikanal2', 
                     'glavnikanal3', 'glavnikanal4', 'glavnikanalfill', 
                     'pomocnikanal1', 'pomocnikanal2', 'pomocnikanal3', 
                     'pomocnikanal4', 'pomocnikanal5', 'pomocnikanal6']
                
        specials = ['validanOK', 'validanNOK', 'nevalidanOK', 'nevalidanNOK']
        for graf in plotlista:
            #kreni graf po graf, provjeri da li je predvidjen za crtanje i crtaj
            kanal = self.__defaulti[graf]['kanal']
            test1 = (kanal != None)
            if self.__data == None:
                test2 = False
            else:
                test2 = (kanal in list(self.__data.keys()))
            test3 = (self.__defaulti[graf]['crtaj'] == True)
            #kanal mora postojati i mora biti u podatcima da bi se nacrtao
            if test1 and test2 and test3:
                if graf in specials:
                    #slucaj sa glavnim scatter tockama
                    #priprema podataka je specificna
                    if graf == 'validanOK':
                        #samo svi podaci gdje je flag = 1000
                        data = self.__data[kanal]
                        data = data[data[u'flag'] == 1000]
                        x = list(data.index)
                        y = list(data[u'avg'])
                        assert(len(x) == len(y))
                        self.axes.scatter(x, 
                                          y, 
                                          marker = self.__defaulti['validanOK']['marker'], 
                                          color = self.normalize_rgb(self.__defaulti['validanOK']['color']), 
                                          alpha = self.__defaulti['validanOK']['alpha'], 
                                          zorder = self.__defaulti['validanOK']['zorder'])
                        self.__statusGlavniGraf = True

                    elif graf == 'validanNOK':
                        #samo svi podaci gdje je flag = -1000
                        data = self.__data[kanal]
                        data = data[data[u'flag'] == -1000]
                        x = list(data.index)
                        y = list(data[u'avg'])
                        assert(len(x) == len(y))
                        self.axes.scatter(x, 
                                          y, 
                                          marker = self.__defaulti['validanNOK']['marker'], 
                                          color = self.normalize_rgb(self.__defaulti['validanNOK']['color']), 
                                          alpha = self.__defaulti['validanNOK']['alpha'],
                                          zorder = self.__defaulti['validanNOK']['zorder'])
                        self.__statusGlavniGraf = True
                        
                    elif graf == 'nevalidanOK':
                        #samo svi podaci gdje je flag = 1
                        data = self.__data[kanal]
                        data = data[data[u'flag'] == 1]
                        x = list(data.index)
                        y = list(data[u'avg'])
                        assert(len(x) == len(y))
                        self.axes.scatter(x, 
                                          y, 
                                          marker = self.__defaulti['nevalidanOK']['marker'], 
                                          color = self.normalize_rgb(self.__defaulti['nevalidanOK']['color']), 
                                          alpha = self.__defaulti['nevalidanOK']['alpha'], 
                                          zorder = self.__defaulti['nevalidanOK']['zorder'])
                        self.__statusGlavniGraf = True
                        
                    elif graf == 'nevalidanNOK':
                        #samo svi podaci gdje je flag = -1
                        data = self.__data[kanal]
                        data = data[data[u'flag'] == -1]
                        x = list(data.index)
                        y = list(data[u'avg'])
                        assert(len(x) == len(y))
                        self.axes.scatter(x, 
                                          y, 
                                          marker = self.__defaulti['nevalidanNOK']['marker'], 
                                          color = self.normalize_rgb(self.__defaulti['nevalidanNOK']['color']), 
                                          alpha = self.__defaulti['nevalidanNOK']['alpha'], 
                                          zorder = self.__defaulti['nevalidanNOK']['zorder'])
                        self.__statusGlavniGraf = True
                        
                else:
                    #normalan slucaj (plotamo cijeli niz)
                    data = self.__data[kanal]
                    #izbaci iz popisa sve koje imaju np.NaN vrijednost za avg?
                    data = data[np.isnan(data[u'avg']) != True]
                    
                    x = list(data.index)
                    y = list(data[self.__defaulti[graf]['stupac1']])
                    assert(len(x) == len(y))
                    #scatter
                    if self.__defaulti[graf]['tip'] == 'scatter':
                        self.axes.scatter(x,
                                          y,
                                          marker = self.__defaulti[graf]['marker'], 
                                          color = self.normalize_rgb(self.__defaulti[graf]['color']), 
                                          alpha = self.__defaulti[graf]['alpha'], 
                                          zorder = self.__defaulti[graf]['zorder'])
                    #plot
                    elif self.__defaulti[graf]['tip'] == 'plot':
                        self.axes.plot(x, 
                                       y, 
                                       marker = self.__defaulti[graf]['marker'], 
                                       linestyle = self.__defaulti[graf]['line'], 
                                       color = self.normalize_rgb(self.__defaulti[graf]['color']), 
                                       alpha = self.__defaulti[graf]['alpha'], 
                                       zorder = self.__defaulti[graf]['zorder'])
                    #fill_between
                    elif self.__defaulti[graf]['tip'] == 'fill':
                        y2 = data[self.__defaulti[graf]['stupac2']]
                        assert(len(y2) == len(y))
                        self.axes.fill_between(x, 
                                               y, 
                                               y2, 
                                               facecolor = self.normalize_rgb(self.__defaulti[graf]['color']), 
                                               alpha = self.__defaulti[graf]['alpha'], 
                                               zorder = self.__defaulti[graf]['zorder'])
                                               
        #highlight dot
        if self.__statusGlavniGraf:
            self.__testHighlight = False
            self.highlight_dot(self.__zadnjiHighlightx, self.__zadnjiHighlighty)
        
        self.draw()
        
        
###############################################################################
###############################################################################
class GrafMinutni(MPLCanvas):
    #TODO!
    #minutni canvas, crtanje isl
    #NOT IMPLEMENTED
    """Canvas minutnog grafa"""
    def __init__(self, *args, **kwargs):
        """konstruktor"""
        MPLCanvas.__init__(self, *args, **kwargs)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.__defaulti = None
        self.__frejmovi = None
        self.__sat = None
        
        self.__annotationx = None
        self.__annotationTest = False
        self.__statusSpanSelector = False
        self.__statusGlavniGraf = False
        
    def veze(self):
        self.mpl_connect('button_press_event', self.on_pick)

    def plot_time_span(self, vrijeme):
        """
        Za zadano vrijeme (pd.timestamp) vraca rubne vrijednosti indeksa 
        minutnog slicea.
        """
        tmax =  vrijeme
        tmin = vrijeme - timedelta(minutes = 59)
        tmin = pd.to_datetime(tmin)
        return tmin, tmax
    
    def refokusiraj(self, sat):
        #TODO!
        #probaj umjesto ponovnog iscrtavanja grafa refokusirati sa xlim veliki graf
        pass
    
    def crtaj(self, defaulti, frejmovi, sat):
        """ideja, nacrtati sve podatke, ali inicijalno ograniciti sliku
        na raspon satnog podatka"""
        self.__defaulti = defaulti
        self.__frejmovi = frejmovi
        self.__sat = sat
        
        self.axes.clear()
        self.__statusGlavniGraf = False
        self.__annotationTest = False
                                
        specials = ['m_validanOK', 'm_validanNOK', 
                    'm_nevalidanOK', 'm_nevalidanNOK']
        pomocni = ['m_pomocnikanal1', 'm_pomocnikanal2', 
                   'm_pomocnikanal3', 'm_pomocnikanal4', 
                   'm_pomocnikanal5', 'm_pomocnikanal6', 
                   'm_glavnikanal']
        plotlista = specials + pomocni
        
        for graf in plotlista:
            kanal = self.__defaulti[graf]['kanal']
            test1 = (kanal != None)
            if self.__frejmovi == None:
                test2 = False
            else:
                test2 = (kanal in list(self.__frejmovi.keys()))
            test3 = (self.__defaulti[graf]['crtaj'] == True)
            
            if (test1 and test2 and test3):
                if graf in specials:
                    #crtaj specificne scatter plotove
                    if graf == 'm_validanOK':
                        data = self.__frejmovi[kanal]
                        data = data[data[u'flag'] == 1000]
                        x = list(data.index)
                        y = list(data[u'koncentracija'])
                        assert(len(x) == len(y))
                        self.axes.scatter(x, 
                                          y, 
                                          marker = self.__defaulti['m_validanOK']['marker'], 
                                          color = self.normalize_rgb(self.__defaulti['m_validanOK']['color']), 
                                          alpha = self.__defaulti['m_validanOK']['alpha'], 
                                          zorder = self.__defaulti['m_validanOK']['zorder'])
                        
                    if graf == 'm_validanNOK':
                        data = self.__frejmovi[kanal]
                        data = data[data[u'flag'] == -1000]
                        x = list(data.index)
                        y = list(data[u'koncentracija'])
                        assert(len(x) == len(y))
                        self.axes.scatter(x, 
                                          y, 
                                          marker = self.__defaulti['m_validanNOK']['marker'], 
                                          color = self.normalize_rgb(self.__defaulti['m_validanNOK']['color']), 
                                          alpha = self.__defaulti['m_validanNOK']['alpha'], 
                                          zorder = self.__defaulti['m_validanNOK']['zorder'])

                    if graf == 'm_nevalidanOK':
                        data = self.__frejmovi[kanal]
                        data = data[data[u'flag'] >= 0]
                        data = data[data[u'flag'] != 1000 ]
                        x = list(data.index)
                        y = list(data[u'koncentracija'])
                        assert(len(x) == len(y))
                        self.axes.scatter(x, 
                                          y, 
                                          marker = self.__defaulti['m_nevalidanOK']['marker'], 
                                          color = self.normalize_rgb(self.__defaulti['m_nevalidanOK']['color']), 
                                          alpha = self.__defaulti['m_nevalidanOK']['alpha'], 
                                          zorder = self.__defaulti['m_nevalidanOK']['zorder'])

                    if graf == 'm_nevalidanNOK':
                        data = self.__frejmovi[kanal]
                        data = data[data[u'flag'] < 0 ]
                        data = data[data[u'flag'] != -1000 ]
                        x = list(data.index)
                        y = list(data[u'koncentracija'])
                        assert(len(x) == len(y))
                        self.axes.scatter(x, 
                                          y, 
                                          marker = self.__defaulti['m_nevalidanNOK']['marker'], 
                                          color = self.normalize_rgb(self.__defaulti['m_nevalidanNOK']['color']), 
                                          alpha = self.__defaulti['m_nevalidanNOK']['alpha'], 
                                          zorder = self.__defaulti['m_nevalidanNOK']['zorder'])
                
                else:
                    #crtaj line plotove
                    data = self.__frejmovi[kanal]
                    x = list(data.index)
                    y = list(data[u'koncentracija'])
                    assert(len(x) == len(y))
                    self.axes.plot(x,
                                   y, 
                                   marker = self.__defaulti[graf]['marker'], 
                                   color = self.normalize_rgb(self.__defaulti[graf]['color']), 
                                   alpha = self.__defaulti[graf]['alpha'],
                                   linestyle = self.__defaulti[graf]['line'], 
                                   zorder = self.__defaulti[graf]['zorder'])

        #XXX! samo za testiranje
        self.__sat = pd.to_datetime('2014-06-04 15:00:00')
        if self.__sat != None:
            self.xmin, self.xmax = self.plot_time_span(self.__sat)
            self.axes.set_xlim(self.xmin, self.xmax)
        
        #format x kooridinate
        xLabels = self.axes.get_xticklabels()
        for label in xLabels:
            label.set_rotation(20)
            label.set_fontsize(8)
        #finalna naredba za prikaz
        self.draw()

    def normalize_rgb(self, rgbTuple):
        """konverter za plotanje, mpl kao color ima sequence vrijednosti 
        izmedju [0-1]"""
        r, g, b = rgbTuple
        return (r/255, g/255, b/255)

    def on_pick(self, event):
        """definiranje ponasanja pick eventa na canvasu"""

        #XXX!
        """
        UPOZORENJE!!!
        
        Ovaj dio koda rijesava konflikte prilikom zoom/pan akcija na
        toolbaru. Postoje dva problema:
        
        1.
        ._active nije namjenjen da ga se dohvati metodom i mogu ga 
        nenajavljeno promjeniti u nekoj drugoj verziji matplotliba
        
        2. 
        parent mora imati member mplToolar tipa NavigationToolbar2QT, 
        koji mora biti povezan sa ovim canvasom.
        
        Radi na Matplotlib 1.3.1
        
        ._active == None ako su Pan i Zoom opcije iskljucene
        ._active == 'PAN' ako je pan/zoom opcija ukljucena
        ._active == 'ZOOM' ako je zoom rect opcija ukljucena
        """
        #od parenta dohvati toolbar, tj. njegovo stanje
        stanje = self.parent().mplToolbar._active


###############################################################################
###############################################################################
base3, form3 = uic.loadUiType('minutnigraf.ui')
class MinutniGraf(base3, form3):
    """Klasa za minutni graf sa dijelom kontrola"""
    def __init__(self, parent = None, defaulti = None, frejmovi = None, sat = None):
        super(base3, self).__init__(parent)
        self.setupUi(self)
        
        #defaultini izbor za grafove
        self.__defaulti = defaulti
        self.__minutniFrejmovi = frejmovi
        self.__sat = sat #timestamp indeksa satno agregiranog podatka

        #inicijalizacija ostalih grafickih elemenata
        self.widget1 = QtGui.QWidget()
        self.widget2 = QtGui.QWidget()
        #inicijalizacija canvasa na mjesto self.grafWidget
        self.canvasMinutni = GrafMinutni(parent = self.widget1)
        #inicijalizacija Navigation bara
        self.mplToolbar = NavigationToolbar(self.canvasMinutni, self.widget2)
        self.canvasLayout.addWidget(self.canvasMinutni)
        self.canvasLayout.addWidget(self.mplToolbar)
        
        #toggle gumb za skrivanje izbora grafa...
        self.toggleDetalji.toggled.connect(self.groupBox.setVisible)
        self.toggleDetalji.toggled.connect(self.groupBox_2.setVisible)
        
        #inicijalni tekst
        self.sliceLabel.setText('Prikazano vrijeme: ')
        
        self.veze()
        self.initial_setup(self.__sat)

    def zamjeni_frejmove(self, defaulti, frejmovi):
        self.__defaulti = defaulti
        self.__minutniFrejmovi = frejmovi
        self.initial_setup(None)
    
    def veze(self):
        #spajanje widgeta sa kontrolnim funkcijama
        #izbor boje i stila grafa
        self.glavniDetalji.clicked.connect(self.glavniDetalji_dijalog)
        self.pomocni1Detalji.clicked.connect(self.pomocni1Detalji_dijalog)
        self.pomocni2Detalji.clicked.connect(self.pomocni2Detalji_dijalog)
        self.pomocni3Detalji.clicked.connect(self.pomocni3Detalji_dijalog)
        self.pomocni4Detalji.clicked.connect(self.pomocni4Detalji_dijalog)
        self.pomocni5Detalji.clicked.connect(self.pomocni5Detalji_dijalog)
        self.pomocni6Detalji.clicked.connect(self.pomocni6Detalji_dijalog)
        #comboboxes - izbor kanala za crtanje
        self.pomocni1Combo.currentIndexChanged.connect(self.update_pomocni1Combo)
        self.pomocni2Combo.currentIndexChanged.connect(self.update_pomocni2Combo)
        self.pomocni3Combo.currentIndexChanged.connect(self.update_pomocni3Combo)
        self.pomocni4Combo.currentIndexChanged.connect(self.update_pomocni4Combo)
        self.pomocni5Combo.currentIndexChanged.connect(self.update_pomocni5Combo)
        self.pomocni6Combo.currentIndexChanged.connect(self.update_pomocni6Combo)
        #checkboxes - izbor da li se grafovi crtaju
        self.glavniCheck.stateChanged.connect(self.enable_glavniCheck)
        self.pomocni1Check.stateChanged.connect(self.enable_pomocni1Check)
        self.pomocni2Check.stateChanged.connect(self.enable_pomocni2Check)
        self.pomocni3Check.stateChanged.connect(self.enable_pomocni3Check)
        self.pomocni4Check.stateChanged.connect(self.enable_pomocni4Check)
        self.pomocni5Check.stateChanged.connect(self.enable_pomocni5Check)
        self.pomocni6Check.stateChanged.connect(self.enable_pomocni6Check)

    def enable_grid(self, x):
        if x:
            self.__defaulti['m_opcenito']['grid'] = True
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)
        else:
            self.__defaulti['m_opcenito']['grid'] = False
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)
    
    def enable_cursor(self, x):
        if x:
            self.__defaulti['m_opcenito']['cursor'] = True
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)
        else:
            self.__defaulti['m_opcenito']['cursor'] = False
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)
    
    def enable_spanSelector(self, x):
        if x:
            self.__defaulti['m_opcenito']['span'] = True
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)
        else:
            self.__defaulti['m_opcenito']['span'] = False
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)
    
    def enable_minorTicks(self, x):
        if x:
            self.__defaulti['m_opcenito']['minorTicks'] = True
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)
        else:
            self.__defaulti['m_opcenito']['minorTicks'] = False
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)

    def enable_glavniCheck(self):
        if self.glavniCheck.isChecked() == True:
            self.glavniDetalji.setEnabled(True)
            self.__defaulti['m_validanOK']['crtaj'] = True
            self.__defaulti['m_validanNOK']['crtaj'] = True
            self.__defaulti['m_nevalidanOK']['crtaj'] = True
            self.__defaulti['m_nevalidanNOK']['crtaj'] = True
            self.__defaulti['m_glavnikanal']['crtaj'] = True
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)
        else:
            self.glavniDetalji.setEnabled(False)
            self.__defaulti['m_validanOK']['crtaj'] = False
            self.__defaulti['m_validanNOK']['crtaj'] = False
            self.__defaulti['m_nevalidanOK']['crtaj'] = False
            self.__defaulti['m_nevalidanNOK']['crtaj'] = False
            self.__defaulti['m_glavnikanal']['crtaj'] = False
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)
    
    def enable_pomocni1Check(self):
        if self.pomocni1Check.isChecked() == True:
            self.pomocni1Combo.setEnabled(True)
            self.pomocni1Detalji.setEnabled(True)
            self.__defaulti['m_pomocnikanal1']['crtaj'] = True
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)
        else:
            self.pomocni1Combo.setEnabled(False)
            self.pomocni1Detalji.setEnabled(False)
            self.__defaulti['m_pomocnikanal1']['crtaj'] = False
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)

    def enable_pomocni2Check(self):
        if self.pomocni2Check.isChecked() == True:
            self.pomocni2Combo.setEnabled(True)
            self.pomocni2Detalji.setEnabled(True)
            self.__defaulti['m_pomocnikanal2']['crtaj'] = True
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)
        else:
            self.pomocni2Combo.setEnabled(False)
            self.pomocni2Detalji.setEnabled(False)
            self.__defaulti['m_pomocnikanal2']['crtaj'] = False
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)

    def enable_pomocni3Check(self):
        if self.pomocni3Check.isChecked() == True:
            self.pomocni3Combo.setEnabled(True)
            self.pomocni3Detalji.setEnabled(True)
            self.__defaulti['m_pomocnikanal3']['crtaj'] = True
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)
        else:
            self.pomocni3Combo.setEnabled(False)
            self.pomocni3Detalji.setEnabled(False)
            self.__defaulti['m_pomocnikanal3']['crtaj'] = False
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)

    def enable_pomocni4Check(self):
        if self.pomocni4Check.isChecked() == True:
            self.pomocni4Combo.setEnabled(True)
            self.pomocni4Detalji.setEnabled(True)
            self.__defaulti['m_pomocnikanal4']['crtaj'] = True
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)
        else:
            self.pomocni4Combo.setEnabled(False)
            self.pomocni4Detalji.setEnabled(False)
            self.__defaulti['m_pomocnikanal4']['crtaj'] = False
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)

    def enable_pomocni5Check(self):
        if self.pomocni5Check.isChecked() == True:
            self.pomocni5Combo.setEnabled(True)
            self.pomocni5Detalji.setEnabled(True)
            self.__defaulti['m_pomocnikanal5']['crtaj'] = True
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)
        else:
            self.pomocni5Combo.setEnabled(False)
            self.pomocni5Detalji.setEnabled(False)
            self.__defaulti['m_pomocnikanal5']['crtaj'] = False
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)

    def enable_pomocni6Check(self):
        if self.pomocni6Check.isChecked() == True:
            self.pomocni6Combo.setEnabled(True)
            self.pomocni6Detalji.setEnabled(True)
            self.__defaulti['m_pomocnikanal6']['crtaj'] = True
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)
        else:
            self.pomocni6Combo.setEnabled(False)
            self.pomocni6Detalji.setEnabled(False)
            self.__defaulti['m_pomocnikanal6']['crtaj'] = False
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)

    def update_pomocni1Combo(self):
        newValue = self.pomocni1Combo.currentText()
        self.__defaulti['m_pomocnikanal1']['kanal'] = newValue
        self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)

    def update_pomocni2Combo(self):
        newValue = self.pomocni2Combo.currentText()
        self.__defaulti['m_pomocnikanal2']['kanal'] = newValue
        self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)

    def update_pomocni3Combo(self):
        newValue = self.pomocni3Combo.currentText()
        self.__defaulti['m_pomocnikanal3']['kanal'] = newValue
        self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)

    def update_pomocni4Combo(self):
        newValue = self.pomocni4Combo.currentText()
        self.__defaulti['m_pomocnikanal4']['kanal'] = newValue
        self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)

    def update_pomocni5Combo(self):
        newValue = self.pomocni5Combo.currentText()
        self.__defaulti['m_pomocnikanal5']['kanal'] = newValue
        self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)

    def update_pomocni6Combo(self):
        newValue = self.pomocni6Combo.currentText()
        self.__defaulti['m_pomocnikanal6']['kanal'] = newValue
        self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)
        
    def initial_setup(self, izbor):
        self.__sat = izbor

        self.canvasMinutni.__statusGlavniGraf = False
        self.canvasMinutni.__testAnnotation = False
        self.canvasMinutni.__zadnjiHighlightx = None
        self.canvasMinutni.__zadnjiHighlighty = None
        self.canvasMinutni.__zadnjiAnnotationx = None
               
        if self.__minutniFrejmovi != None:
            if self.__sat != None:
                datum = str(self.__sat.date())
                naslov = 'Prikazano vrijeme za '+datum
                self.labelSlice.setText(naslov)
            
        #checkboxes
        self.glavniCheck.setChecked(self.__defaulti['m_validanOK']['crtaj'])
        self.pomocni1Check.setChecked(self.__defaulti['m_pomocnikanal1']['crtaj'])
        self.pomocni2Check.setChecked(self.__defaulti['m_pomocnikanal2']['crtaj'])
        self.pomocni3Check.setChecked(self.__defaulti['m_pomocnikanal3']['crtaj'])
        self.pomocni4Check.setChecked(self.__defaulti['m_pomocnikanal4']['crtaj'])
        self.pomocni5Check.setChecked(self.__defaulti['m_pomocnikanal5']['crtaj'])
        self.pomocni6Check.setChecked(self.__defaulti['m_pomocnikanal6']['crtaj'])

        #color buttons
        self.change_boja_pomocni1Detalji()
        self.change_boja_pomocni2Detalji()
        self.change_boja_pomocni3Detalji()
        self.change_boja_pomocni4Detalji()
        self.change_boja_pomocni5Detalji()
        self.change_boja_pomocni6Detalji()
        
        #comboboxes i label glavnog grafa
        if self.__minutniFrejmovi != None:
            kanali = sorted(list(self.__minutniFrejmovi.keys()))
            
            #glavni kanal mora odgovarati glavnom kanalu satnog grafa
            #direktno se prepisuje (zato je label a ne combobox)
            glavniKanal = self.__defaulti['validanOK']['kanal']
            if glavniKanal == None:
                self.glavniKanalLabel.setText('Glavni kanal')
            else:
                self.glavniKanalLabel.setText(glavniKanal)
        
            zadnjiKanal = self.__defaulti['m_pomocnikanal1']['kanal']
            self.pomocni1Combo.blockSignals(True)
            self.pomocni1Combo.clear()
            self.pomocni1Combo.addItems(kanali)
            if zadnjiKanal != None:
                ind = self.pomocni1Combo.findText(zadnjiKanal)
                self.pomocni1Combo.setCurrentIndex(ind)
            self.pomocni1Combo.blockSignals(False)
            noviKanal = self.pomocni1Combo.currentText()
            self.__defaulti['m_pomocnikanal1']['kanal'] = noviKanal

            zadnjiKanal = self.__defaulti['m_pomocnikanal2']['kanal']
            self.pomocni2Combo.blockSignals(True)
            self.pomocni2Combo.clear()
            self.pomocni2Combo.addItems(kanali)
            if zadnjiKanal != None:
                ind = self.pomocni2Combo.findText(zadnjiKanal)
                self.pomocni2Combo.setCurrentIndex(ind)
            self.pomocni2Combo.blockSignals(False)
            noviKanal = self.pomocni2Combo.currentText()
            self.__defaulti['m_pomocnikanal2']['kanal'] = noviKanal

            zadnjiKanal = self.__defaulti['m_pomocnikanal3']['kanal']
            self.pomocni3Combo.blockSignals(True)
            self.pomocni3Combo.clear()
            self.pomocni3Combo.addItems(kanali)
            if zadnjiKanal != None:
                ind = self.pomocni3Combo.findText(zadnjiKanal)
                self.pomocni3Combo.setCurrentIndex(ind)
            self.pomocni3Combo.blockSignals(False)
            noviKanal = self.pomocni3Combo.currentText()
            self.__defaulti['m_pomocnikanal3']['kanal'] = noviKanal

            zadnjiKanal = self.__defaulti['m_pomocnikanal4']['kanal']
            self.pomocni4Combo.blockSignals(True)
            self.pomocni4Combo.clear()
            self.pomocni4Combo.addItems(kanali)
            if zadnjiKanal != None:
                ind = self.pomocni4Combo.findText(zadnjiKanal)
                self.pomocni4Combo.setCurrentIndex(ind)
            self.pomocni4Combo.blockSignals(False)
            noviKanal = self.pomocni4Combo.currentText()
            self.__defaulti['m_pomocnikanal4']['kanal'] = noviKanal

            zadnjiKanal = self.__defaulti['m_pomocnikanal5']['kanal']
            self.pomocni5Combo.blockSignals(True)
            self.pomocni5Combo.clear()
            self.pomocni5Combo.addItems(kanali)
            if zadnjiKanal != None:
                ind = self.pomocni5Combo.findText(zadnjiKanal)
                self.pomocni5Combo.setCurrentIndex(ind)
            self.pomocni5Combo.blockSignals(False)
            noviKanal = self.pomocni5Combo.currentText()
            self.__defaulti['m_pomocnikanal5']['kanal'] = noviKanal

            zadnjiKanal = self.__defaulti['m_pomocnikanal6']['kanal']
            self.pomocni6Combo.blockSignals(True)
            self.pomocni6Combo.clear()
            self.pomocni6Combo.addItems(kanali)
            if zadnjiKanal != None:
                ind = self.pomocni6Combo.findText(zadnjiKanal)
                self.pomocni6Combo.setCurrentIndex(ind)
            self.pomocni6Combo.blockSignals(False)
            noviKanal = self.pomocni6Combo.currentText()
            self.__defaulti['m_pomocnikanal6']['kanal'] = noviKanal
            
            #naredba za crtanje je zadnja kod inicijalizacije
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)
    
    def glavniDetalji_dijalog(self):
        #deep copy dicta za dijalog
        grafinfo = copy.deepcopy(self.__defaulti)
        #inicijalizacija dijaloga
        glavnigrafdijalog = GlavniKanalDetaljiM(defaulti = grafinfo)
        if glavnigrafdijalog.exec_():
            grafinfo = glavnigrafdijalog.vrati_dict()
            self.__defaulti = copy.deepcopy(grafinfo)
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)
    
    def pomocni1Detalji_dijalog(self):
        """dijalog za promjenu izgleda pomocnog minutnog grafa 1"""
        #deep copy dicta za dijalog
        grafinfo = copy.deepcopy(self.__defaulti)
        #inicijalizacija dijaloga
        pomocnigrafdijalog = PomocniGrafDetaljiM(defaulti = grafinfo, graf = 'm_pomocnikanal1')
        if pomocnigrafdijalog.exec_():
            grafinfo = pomocnigrafdijalog.vrati_dict()
            self.__defaulti = copy.deepcopy(grafinfo)
            self.change_boja_pomocni1Detalji()
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)

    def pomocni2Detalji_dijalog(self):
        """dijalog za promjenu izgleda pomocnog minutnog grafa 2"""
        #deep copy dicta za dijalog
        grafinfo = copy.deepcopy(self.__defaulti)
        #inicijalizacija dijaloga
        pomocnigrafdijalog = PomocniGrafDetaljiM(defaulti = grafinfo, graf = 'm_pomocnikanal2')
        if pomocnigrafdijalog.exec_():
            grafinfo = pomocnigrafdijalog.vrati_dict()
            self.__defaulti = copy.deepcopy(grafinfo)
            self.change_boja_pomocni2Detalji()
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)

    def pomocni3Detalji_dijalog(self):
        """dijalog za promjenu izgleda pomocnog minutnog grafa 3"""
        #deep copy dicta za dijalog
        grafinfo = copy.deepcopy(self.__defaulti)
        #inicijalizacija dijaloga
        pomocnigrafdijalog = PomocniGrafDetaljiM(defaulti = grafinfo, graf = 'm_pomocnikanal3')
        if pomocnigrafdijalog.exec_():
            grafinfo = pomocnigrafdijalog.vrati_dict()
            self.__defaulti = copy.deepcopy(grafinfo)
            self.change_boja_pomocni3Detalji()
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)

    def pomocni4Detalji_dijalog(self):
        """dijalog za promjenu izgleda pomocnog minutnog grafa 4"""
        #deep copy dicta za dijalog
        grafinfo = copy.deepcopy(self.__defaulti)
        #inicijalizacija dijaloga
        pomocnigrafdijalog = PomocniGrafDetaljiM(defaulti = grafinfo, graf = 'm_pomocnikanal4')
        if pomocnigrafdijalog.exec_():
            grafinfo = pomocnigrafdijalog.vrati_dict()
            self.__defaulti = copy.deepcopy(grafinfo)
            self.change_boja_pomocni4Detalji()
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)

    def pomocni5Detalji_dijalog(self):
        """dijalog za promjenu izgleda pomocnog minutnog grafa 5"""
        #deep copy dicta za dijalog
        grafinfo = copy.deepcopy(self.__defaulti)
        #inicijalizacija dijaloga
        pomocnigrafdijalog = PomocniGrafDetaljiM(defaulti = grafinfo, graf = 'm_pomocnikanal5')
        if pomocnigrafdijalog.exec_():
            grafinfo = pomocnigrafdijalog.vrati_dict()
            self.__defaulti = copy.deepcopy(grafinfo)
            self.change_boja_pomocni5Detalji()
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)

    def pomocni6Detalji_dijalog(self):
        """dijalog za promjenu izgleda pomocnog minutnog grafa 6"""
        #deep copy dicta za dijalog
        grafinfo = copy.deepcopy(self.__defaulti)
        #inicijalizacija dijaloga
        pomocnigrafdijalog = PomocniGrafDetaljiM(defaulti = grafinfo, graf = 'm_pomocnikanal6')
        if pomocnigrafdijalog.exec_():
            grafinfo = pomocnigrafdijalog.vrati_dict()
            self.__defaulti = copy.deepcopy(grafinfo)
            self.change_boja_pomocni6Detalji()
            self.canvasMinutni.crtaj(self.__defaulti, self.__minutniFrejmovi, self.__sat)

    def change_boja_pomocni1Detalji(self):
        """set boje gumba iz defaulta"""
        rgb = self.__defaulti['m_pomocnikanal1']['color']
        a = self.__defaulti['m_pomocnikanal1']['alpha']
        boja = default_color_to_qcolor(rgb, a)
        stil = color_to_style_string('QPushButton#pomocni1Detalji', boja)
        self.pomocni1Detalji.setStyleSheet(stil)

    def change_boja_pomocni2Detalji(self):
        """set boje gumba iz defaulta"""
        rgb = self.__defaulti['m_pomocnikanal2']['color']
        a = self.__defaulti['m_pomocnikanal2']['alpha']
        boja = default_color_to_qcolor(rgb, a)
        stil = color_to_style_string('QPushButton#pomocni2Detalji', boja)
        self.pomocni2Detalji.setStyleSheet(stil)

    def change_boja_pomocni3Detalji(self):
        """set boje gumba iz defaulta"""
        rgb = self.__defaulti['m_pomocnikanal3']['color']
        a = self.__defaulti['m_pomocnikanal3']['alpha']
        boja = default_color_to_qcolor(rgb, a)
        stil = color_to_style_string('QPushButton#pomocni3Detalji', boja)
        self.pomocni3Detalji.setStyleSheet(stil)

    def change_boja_pomocni4Detalji(self):
        """set boje gumba iz defaulta"""
        rgb = self.__defaulti['m_pomocnikanal4']['color']
        a = self.__defaulti['m_pomocnikanal4']['alpha']
        boja = default_color_to_qcolor(rgb, a)
        stil = color_to_style_string('QPushButton#pomocni4Detalji', boja)
        self.pomocni4Detalji.setStyleSheet(stil)

    def change_boja_pomocni5Detalji(self):
        """set boje gumba iz defaulta"""
        rgb = self.__defaulti['m_pomocnikanal5']['color']
        a = self.__defaulti['m_pomocnikanal5']['alpha']
        boja = default_color_to_qcolor(rgb, a)
        stil = color_to_style_string('QPushButton#pomocni5Detalji', boja)
        self.pomocni5Detalji.setStyleSheet(stil)

    def change_boja_pomocni6Detalji(self):
        """set boje gumba iz defaulta"""
        rgb = self.__defaulti['m_pomocnikanal6']['color']
        a = self.__defaulti['m_pomocnikanal6']['alpha']
        boja = default_color_to_qcolor(rgb, a)
        stil = color_to_style_string('QPushButton#pomocni6Detalji', boja)
        self.pomocni6Detalji.setStyleSheet(stil)

###############################################################################
###############################################################################
base4, form4 = uic.loadUiType('m_pomocnigrafdetalji.ui')
class PomocniGrafDetaljiM(base4, form4):
    """
    Opcenita klasa za izbor detalja grafa

    incijalizacija sa:
        defaulti : dict, popis svih predvidjenih grafova
        graf : string, kljuc mape pojedinog grafa
    """
    def __init__(self, parent = None, defaulti = None, graf = None):
        super(base4, self).__init__(parent)
        self.setupUi(self)
        
        #defaultni izbor za grafove
        self.__defaulti = defaulti #defaultni dict svih grafova
        self.__graf = graf #string kljuca specificnog grafa
        
        self.__sviMarkeri = ['None', 'o', 'v', '^', '<', '>', 's', 'p', '*', 'h', '+', 'x', 'd', '_', '|']
        self.__sveLinije = ['None', '-', '--', '-.', ':']
        self.__sviTipovi = ['scatter', 'plot']
        
        self.popuni_izbornike()
        self.veze()
        
    def veze(self):
        self.tip.currentIndexChanged.connect(self.change_tip)
        self.marker.currentIndexChanged.connect(self.change_marker)
        self.linija.currentIndexChanged.connect(self.change_linija)
        self.boja.clicked.connect(self.change_boja)
    
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
        boja = default_color_to_qcolor(rgb, a)
        #dijalog
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test za validnu boju
            color = QtGui.QColor.fromRgba(color)
            rgb, a = qcolor_to_default_color(color)
            #update dict
            self.__defaulti[self.__graf]['color'] = rgb
            self.__defaulti[self.__graf]['alpha'] = a
            #set new color
            stil = color_to_style_string('QPushButton#boja', color)
            self.boja.setStyleSheet(stil)

    def popuni_izbornike(self):
        """inicijalizacija izbornika sa defaultinim postavkama"""
        naziv = 'Detalji pomocnog minutnog grafa, kanal: ' + str(self.__defaulti[self.__graf]['kanal'])
        self.groupBox.setTitle(str(self.__defaulti[self.__graf]['kanal']))
        self.setWindowTitle(naziv)
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
        color = default_color_to_qcolor(rgb, a)
        stil = color_to_style_string('QPushButton#boja', color)
        self.boja.setStyleSheet(stil)

    def vrati_dict(self):
        """funkcija vraca izmjenjeni defaultni dictionary svih grafova"""
        return self.__defaulti
###############################################################################
###############################################################################
base5, form5 = uic.loadUiType('m_glavnikanaldetalji.ui')
class GlavniKanalDetaljiM(base5, form5):
    """
    Klasa za "prikaz" izbora opcija za crtanje glavnog kanala minutnog grafa.
    
    Dict defaulti je specifican. Mora prosljediti konsturktoru. 
    Sadrzi postavke svih mogucih grafova (boja, da li se crtaju...)
    """
    def __init__(self, parent = None, defaulti = None):
        super(base5, self).__init__(parent)
        self.setupUi(self)
        
        #sve opcije su sadrzane u dictu defaulti
        self.__defaulti = defaulti
        
        self.__sviMarkeri = ['o', 'v', '^', '<', '>', 's', 'p', '*', 'h', '+', 'x', 'd', '_', '|']
        self.__sveLinije = ['-', '--', '-.', ':']
        
        self.popuni_izbornike()
        self.veze()
        
    def veze(self):
        self.markerOK.currentIndexChanged.connect(self.update_markerOK)
        self.markerNOK.currentIndexChanged.connect(self.update_markerNOK)
        self.stilLinije.currentIndexChanged.connect(self.update_stilLinije)
        self.colorOK.clicked.connect(self.promjena_boje_colorOK)
        self.colorNOK.clicked.connect(self.promjena_boje_colorNOK)
        self.bojaLinije.clicked.connect(self.promjena_boje_bojaLinije)
    
    def update_markerOK(self):
        newValue = self.markerOK.currentText()
        self.__defaulti['m_validanOK']['marker'] = newValue
        self.__defaulti['m_validanNOK']['marker'] = newValue
    
    def update_markerNOK(self):
        newValue = self.markerNOK.currentText()
        self.__defaulti['m_nevalidanOK']['marker'] = newValue
        self.__defaulti['m_nevalidanNOK']['marker'] = newValue
    
    def update_stilLinije(self):
        newValue = self.stilLinije.currentText()
        self.__defaulti['m_glavnikanal']['line'] = newValue
    
    def promjena_boje_colorOK(self):
        rgb = self.__defaulti['m_validanOK']['color']
        a = self.__defaulti['m_validanOK']['alpha']
        boja = default_color_to_qcolor(rgb, a)
        #dijalog
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test za validnu boju
            color = QtGui.QColor.fromRgba(color)
            rgb, a = qcolor_to_default_color(color)
            #update dict
            self.__defaulti['m_validanOK']['color'] = rgb
            self.__defaulti['m_validanOK']['alpha'] = a
            self.__defaulti['m_nevalidanOK']['color'] = rgb
            self.__defaulti['m_nevalidanOK']['alpha'] = a
            #set new color
            stil = color_to_style_string('QPushButton#colorOK', color)
            self.colorOK.setStyleSheet(stil)

    def promjena_boje_colorNOK(self):
        rgb = self.__defaulti['m_validanNOK']['color']
        a = self.__defaulti['m_validanNOK']['alpha']
        boja = default_color_to_qcolor(rgb, a)
        #dijalog
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test za validnu boju
            color = QtGui.QColor.fromRgba(color)
            rgb, a = qcolor_to_default_color(color)
            #update dict
            self.__defaulti['m_validanNOK']['color'] = rgb
            self.__defaulti['m_validanNOK']['alpha'] = a
            self.__defaulti['m_nevalidanNOK']['color'] = rgb
            self.__defaulti['m_nevalidanNOK']['alpha'] = a
            #set new color
            stil = color_to_style_string('QPushButton#colorNOK', color)
            self.colorNOK.setStyleSheet(stil)

    def promjena_boje_bojaLinije(self):
        rgb = self.__defaulti['m_glavnikanal']['color']
        a = self.__defaulti['m_glavnikanal']['alpha']
        boja = default_color_to_qcolor(rgb, a)
        #dijalog
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test za validnu boju
            color = QtGui.QColor.fromRgba(color)
            rgb, a = qcolor_to_default_color(color)
            #update dict
            self.__defaulti['m_glavnikanal']['color'] = rgb
            self.__defaulti['m_glavnikanal']['alpha'] = a
            #set new color
            stil = color_to_style_string('QPushButton#bojaLinije', color)
            self.bojaLinije.setStyleSheet(stil)
    
    def popuni_izbornike(self):
        #comboboxes
        self.markerOK.clear()
        self.markerOK.addItems(self.__sviMarkeri)
        ind = self.markerOK.findText(self.__defaulti['m_validanOK']['marker'])
        self.markerOK.setCurrentIndex(ind)
        
        self.markerNOK.clear()
        self.markerNOK.addItems(self.__sviMarkeri)
        ind = self.markerNOK.findText(self.__defaulti['m_nevalidanOK']['marker'])
        self.markerNOK.setCurrentIndex(ind)
        
        self.stilLinije.clear()
        self.stilLinije.addItems(self.__sveLinije)
        ind = self.stilLinije.findText(self.__defaulti['m_glavnikanal']['line'])
        self.stilLinije.setCurrentIndex(ind)
        #buttons
        rgb = self.__defaulti['m_validanOK']['color']
        a = self.__defaulti['m_validanOK']['alpha']
        color = default_color_to_qcolor(rgb, a)
        stil = color_to_style_string('QPushButton#colorOK', color)
        self.colorOK.setStyleSheet(stil)
        
        rgb = self.__defaulti['m_validanNOK']['color']
        a = self.__defaulti['m_validanNOK']['alpha']
        color = default_color_to_qcolor(rgb, a)
        stil = color_to_style_string('QPushButton#colorNOK', color)
        self.colorNOK.setStyleSheet(stil)
        
        rgb = self.__defaulti['m_glavnikanal']['color']
        a = self.__defaulti['m_glavnikanal']['alpha']
        color = default_color_to_qcolor(rgb, a)
        stil = color_to_style_string('QPushButton#bojaLinije', color)
        self.bojaLinije.setStyleSheet(stil)        

    def vrati_dict(self):
        """funkcija vraca izmjenjeni defaultni dictionary svih grafova"""
        return self.__defaulti        
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
            
if __name__=='__main__':
    
    """
    Kasnije, provjeri sto se jos da optimizirati
    """
    #NOVA konstrukcija ulaznog dicta svih mogucih grafova
    validanOK = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'marker':'p', 'color':(0,255,0), 'alpha':1, 'zorder':20}
    validanNOK = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'marker':'p', 'color':(255,0,0), 'alpha':1, 'zorder':20}
    nevalidanOK = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'marker':'o', 'color':(0,255,0), 'alpha':1, 'zorder':20}
    nevalidanNOK = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'marker':'o', 'color':(255,0,0), 'alpha':1, 'zorder':20}
    glavnikanal1 = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'stupac1':'min', 'marker':'+', 'line':'None', 'color':(0,0,0), 'alpha':0.9, 'zorder':8}
    glavnikanal2 = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'stupac1':'max', 'marker':'+', 'line':'None', 'color':(0,0,0), 'alpha':0.9, 'zorder':9}
    glavnikanal3 = {'crtaj':True, 'tip':'plot', 'kanal':None, 'stupac1':'median', 'marker':'None', 'line':'-', 'color':(45,86,90), 'alpha':0.9, 'zorder':10}
    glavnikanal4 = {'crtaj':True, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'--', 'color':(73,189,191), 'alpha':0.9, 'zorder':11}
    glavnikanalfill = {'crtaj':True, 'tip':'fill', 'kanal':None, 'stupac1':'q05', 'stupac2':'q95', 'marker':'None', 'line':'--', 'color':(31,117,229), 'alpha':0.4, 'zorder':7}
    pomocnikanal1 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(186,113,123), 'alpha':0.9, 'zorder':1}
    pomocnikanal2 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(213,164,255), 'alpha':0.9, 'zorder':2}
    pomocnikanal3 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(111,118,255), 'alpha':0.9, 'zorder':3}
    pomocnikanal4 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(149,255,147), 'alpha':0.9, 'zorder':4}
    pomocnikanal5 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(214,255,137), 'alpha':0.9, 'zorder':5}
    pomocnikanal6 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(255,64,47), 'alpha':0.9, 'zorder':6}
    opcenito = {'grid':False, 'cursor':False, 'span':False, 'minorTicks':True}
    m_validanOK = {'crtaj':True, 'tip':'scatter', 'kanal':'1-SO2-ppb', 'marker':'d', 'color':(0,255,0), 'alpha':1, 'zorder':20}
    m_validanNOK = {'crtaj':True, 'tip':'scatter', 'kanal':'1-SO2-ppb', 'marker':'d', 'color':(255,0,0), 'alpha':1, 'zorder':20}
    m_nevalidanOK = {'crtaj':True, 'tip':'scatter', 'kanal':'1-SO2-ppb', 'marker':'o', 'color':(0,255,0), 'alpha':1, 'zorder':20}
    m_nevalidanNOK = {'crtaj':True, 'tip':'scatter', 'kanal':'1-SO2-ppb', 'marker':'o', 'color':(255,0,0), 'alpha':1, 'zorder':20}
    m_glavnikanal = {'crtaj':True, 'tip':'plot', 'kanal':'1-SO2-ppb', 'stupac1':'koncentracija', 'marker':'None', 'line':'-', 'color':(45,86,90), 'alpha':0.9, 'zorder':10}
    m_pomocnikanal1 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'koncentracija', 'marker':'None', 'line':'-', 'color':(186,113,123), 'alpha':0.9, 'zorder':1}
    m_pomocnikanal2 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'koncentracija', 'marker':'None', 'line':'-', 'color':(213,164,255), 'alpha':0.9, 'zorder':2}
    m_pomocnikanal3 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'koncentracija', 'marker':'None', 'line':'-', 'color':(111,118,255), 'alpha':0.9, 'zorder':3}
    m_pomocnikanal4 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'koncentracija', 'marker':'None', 'line':'-', 'color':(149,255,147), 'alpha':0.9, 'zorder':4}
    m_pomocnikanal5 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'koncentracija', 'marker':'None', 'line':'-', 'color':(214,255,137), 'alpha':0.9, 'zorder':5}
    m_pomocnikanal6 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'koncentracija', 'marker':'None', 'line':'-', 'color':(255,64,47), 'alpha':0.9, 'zorder':6}
    m_opcenito = {'grid':False, 'cursor':False, 'span':True, 'minorTicks':True}
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
             'opcenito':opcenito, 
             'm_validanOK':m_validanOK, 
             'm_validanNOK':m_validanNOK, 
             'm_nevalidanOK':m_nevalidanOK, 
             'm_nevalidanNOK':m_nevalidanNOK, 
             'm_glavnikanal':m_glavnikanal, 
             'm_pomocnikanal1':m_pomocnikanal1, 
             'm_pomocnikanal2':m_pomocnikanal2, 
             'm_pomocnikanal3':m_pomocnikanal3, 
             'm_pomocnikanal4':m_pomocnikanal4, 
             'm_pomocnikanal5':m_pomocnikanal5, 
             'm_pomocnikanal6':m_pomocnikanal6, 
             'm_opcenito':m_opcenito}
    
    reader = citac.WlReader('./data/')
    reader.dohvati_sve_dostupne()
    stanica = 'plitvicka jezera'
    datum = '20140604'
    datum = pd.to_datetime(datum)
    datum = datum.date()
    frejmovi = reader.citaj(stanica, datum)
    #jedan frejm
    frejm = frejmovi['1-SO2-ppb']
    #frejm = frejmovi['49-O3-ug/m3']
    
    #Inicijaliziraj agregator
    agregator = Agregator()
    #agregiraj frejm
    agregirani = agregator.agregiraj(frejmovi)
    
    aplikacija = QtGui.QApplication(sys.argv)
    app = MinutniGraf(parent = None, defaulti = mapa2, frejmovi = frejmovi, sat = None)
    #app = SatniGraf(parent = None, defaulti = mapa2, frejmovi = None)
    app.show()
    #dodaj frejmove
    #app.zamjeni_frejmove(agregirani)
    
    sys.exit(aplikacija.exec_())