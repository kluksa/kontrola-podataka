# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 08:20:44 2014

@author: User

Klasa za satni panel.
Wrapper koji sadrzi:
    1. Label sa informacijom o glavnom kanalu
    2. satni canvas (canvas za prikaz satno agregiranih podataka)
    3. matplotlib toolbar koji dodaje nekoliko opcija za rad sa grafom
"""
from PyQt4 import QtGui, uic #import djela Qt frejmworka
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar #import mpl toolbara

import satniCanvas

base3, form3 = uic.loadUiType('panel_za_canvas.ui')
class SatniPanel(base3, form3):
    """
    Klasa za "prikaz" satnog grafa
    - naslov glavnog kanala je izdvojen u labelu pri vrhu panela
    - ispod naslova se nalazi prostor za canvas (sam canvas se nalazi u drugoj klasi)
    - ispod canvasa nalazi se mplToolbar povezan sa canvasom
    """
    def __init__(self, parent = None, defaulti = None, infoFrejmovi = None):
        super(base3, self).__init__(parent)
        self.setupUi(self)

        #sredi title panela
        self.setWindowTitle('Satno agregirani podaci')

        #defaultini izbor za grafove
        self.__defaulti = defaulti #dictionary sa "opisom" grafova
        self.__infoFrejmovi = infoFrejmovi #[stanica, tMin, tMax, [lista kanala]]
        #inicijalizacija ostalih grafickih elemenata
        self.widget1 = QtGui.QWidget()
        self.widget2 = QtGui.QWidget()
        #inicijalizacija canvasa
        self.canvas = satniCanvas.Graf(parent = self.widget1)
        #inicijalizacija Navigation bara
        self.mplToolbar = NavigationToolbar(self.canvas, self.widget2)
        #dodavanje canvasa i toolbara u verticalLayout na panelu        
        self.graphLayout.addWidget(self.canvas)
        self.graphLayout.addWidget(self.mplToolbar)
        
        self.initial_setup()
###############################################################################
    def get_defaulti(self):
        """
        Metoda vraca dictionary sa informacijama o izgledu grafova, sto i kako 
        se crta. Export postavki.
        
        primjer izgleda self.__defaulti:
        self.__defaulti = {
            'glavniKanal':{
                'midline':{'kanal':'1-SO2-ppb', 'line':'-', 'rgb':(0,0,0), 'alpha':1.0, 'zorder':100, 'label':None},
                'validanOK':{'kanal':'1-SO2-ppb', 'marker':'d', 'rgb':(0,255,0), 'alpha':1.0, 'zorder':100, 'label':None}, 
                'validanNOK':{'kanal':'1-SO2-ppb', 'marker':'d', 'rgb':(255,0,0), 'alpha':1.0, 'zorder':100, 'label':None}, 
                'nevalidanOK':{'kanal':'1-SO2-ppb', 'marker':'o', 'rgb':(0,255,0), 'alpha':1.0, 'zorder':100, 'label':None}, 
                'nevalidanNOK':{'kanal':'1-SO2-ppb', 'marker':'o', 'rgb':(255,0,0), 'alpha':1.0, 'zorder':100, 'label':None},
                'fillsatni':{'kanal':'1-SO2-ppb', 'crtaj':True, 'data1':'q05', 'data2':'q95', 'rgb':(0,0,255), 'alpha':0.5, 'zorder':1}, 
                'ekstremimin':{'kanal':'1-SO2-ppb', 'crtaj':False, 'marker':'+', 'rgb':(90,50,10), 'alpha':1.0, 'zorder':100, 'label':'min'}, 
                'ekstremimax':{'kanal':'1-SO2-ppb', 'crtaj':False, 'marker':'+', 'rgb':(90,50,10), 'alpha':1.0, 'zorder':100, 'label':'max'}
                            },
            'pomocniKanali':{
                'graf1':{'kanal':'1-SO2-ppb', 'marker':'x', 'line':'--', 'rgb':(100,50,0), 'alpha':0.9, 'zorder':2, 'label':'graf1'}, 
                'graf2':{'kanal':'11-NO2-ppb', 'marker':'d', 'line':'-', 'rgb':(0,100,50), 'alpha':0.5, 'zorder':3, 'label':'graf2'}, 
                'graf3':{'kanal':'12-NO-ppb', 'marker':'p', 'line':':', 'rgb':(50,0,100), 'alpha':0.7, 'zorder':4, 'label':'graf3'}
                            }, 
            'ostalo':{
                'opcijeminutni':{'cursor':False, 'span':False, 'ticks':True, 'grid':False, 'legend':False}, 
                'opcijesatni':{'cursor':False, 'span':False, 'ticks':True, 'grid':False, 'legend':False}
                    }
                        }
        """
        return self.__defaulti
###############################################################################
    def zamjeni_defaulte(self, defaulti):
        """
        Kratka funkcija koja sluzi za elegantnu zamjenu postavki grafova.
        Import postavki.
        """
        self.__defaulti = defaulti
        self.initial_setup()
###############################################################################
    def zamjeni_frejmove(self, info):
        """
        Metoda postavlja infromaciju o dostupnim frejmovima.
        info je lista koja sadrzi [stanica, tmin, tmax, [lista kanala]].
        Ta informacija omogucuje canvasu da prilikom crtanja zna poslati
        smisleni zahtjev kontroloru da dohvati podatke
        """
        self.__infoFrejmovi = info
        self.initial_setup()
###############################################################################
    def initial_setup(self):
        """
        Metoda zaduzena za "refresh" cijelog panela
        """
        #postavi label da prikazuje koji je trenutni glavni kanal
        if self.__defaulti != None:
            glavniKanal = self.__defaulti['glavniKanal']['validanOK']['kanal']
        opis = 'Glavni kanal : '+str(glavniKanal)
        self.label.setText(opis)
        
        #naredi crtanje grafa canvasu ako su ulazni paremetri razliciti od None
        if self.__defaulti != None and self.__infoFrejmovi != None:
            self.canvas.crtaj(self.__defaulti, self.__infoFrejmovi)
###############################################################################
###############################################################################