# -*- coding: utf-8 -*-
"""
Created on Mon Nov 10 08:50:02 2014

@author: User

Panel za grafove.
Wrapper koji sadrzi:
    1. label sa informacijom o glavnom kanalu te vremenskom slajsu.
    2. gumbe za navigaciju (prethodni i sljedeci dan)
    3. satni canvas (canvas za prikaz satno agregiranih podataka)
    4. minutni canvas (canvas za prikaz minutnih podataka)
"""

from PyQt4 import uic #import djela Qt frejmworka
import satniCanvas
import minutniCanvas

base3, form3 = uic.loadUiType('panel_za_canvase.ui')
class GrafPanel(base3, form3):
    """
    Klasa za prikaz grafova
    Sadrzaj ovog panela je sljedeci (kako se prikazuje odozgo prema dolje):
    
    1. self.verticalLayoutSatni
        -placeholder definiran u QtDesigneru (layout)
        -sluzi da se u njega stavi satni canvas
        
    2. self.horizontalLayout
        -horiznotalni layout koji sadrzi 3 elementa
        2.1. self.pushButtonPrethodni
            -QPushButton koji sluzi za prebacivanje dana na prethodni dan
        2.2. self.label
            -QLabel koji sluzi za prikaz naziva glavnog kanala i vremenkog intervala
        2.3. self.pushButtonSljedeci
            -QPushButton koji slizi za prebacivanje dana na sljedeci dan
    
    3. self.verticalLayoutMinutni
        -placeholder definiran u QtDesigneru (QWidget)
        -sluzi da se u njega stavi minutni canvas
        
    dodatno definirani memberi
    self.__defaulti
        -dictionary sa opisom kako grafovi trebaju izgledati i koji se grafovi trebaju crtati
        
    self.__info
        -lista koja sluzi kao "pointer" na izvor podataka
        -[stanica, tMin, tMax, [lista dostupnih kanala]]
        
    self.satniGraf
        -instanca satnog canvasa
        
    self.minutniGraf
        -instanca minutnog canvasa
    """
    def __init__(self, parent = None, defaulti = None, infoFrejmovi = None):
        super(base3, self).__init__(parent)
        self.setupUi(self)

        #sredi title panela
        self.setWindowTitle('Graf satno agregiranih podataka i minutnih podataka')

        #defaultini izbor za grafove
        self.__defaulti = defaulti #dictionary sa "opisom" grafova
        self.__infoFrejmovi = infoFrejmovi #[stanica, tMin, tMax, [lista kanala]]
       
        #inicijalizacija canvasa
        self.satniGraf = satniCanvas.Graf(parent = None)
        self.minutniGraf = minutniCanvas.Graf(parent = None)
        
        #dodavanje canvasa u layout panela
        self.verticalLayoutSatni.addWidget(self.satniGraf)
        self.verticalLayoutMinutni.addWidget(self.minutniGraf)

        self.initial_setup()
###############################################################################
    def initial_setup(self):
        """
        Metoda zaduzena za "refresh" cijelog panela
        Naredba za crtanje grafova se mora zadati sa 2 varijable
        (self.__defaulti i self.__infoFrejmovi). Usljed promjene
        stanja jedne od te dvije varijable, treba ponovo nacrtati graf.
        To je posao ove metode i poziva se svaki puta kada se postavi novi
        self.__defaulti ili self.__infoFrejmovi.
        """
        #placeholderi za stringove rubove vremenskog niza
        tmin = ''
        tmax = ''
        #postavi label da prikazuje koji je trenutni glavni kanal
        if self.__defaulti != None:
            glavniKanal = self.__defaulti['glavniKanal']['validanOK']['kanal']
            
        if self.__infoFrejmovi != None:
            tmin = self.__infoFrejmovi[1]
            tmax = self.__infoFrejmovi[2]
            
        opis = 'Glavni kanal: '+str(glavniKanal)+' od: '+str(tmin)+' do:'+str(tmax)
        self.label.setText(opis)
        
        #naredi crtanje grafa canvasu ako su ulazni paremetri razliciti od None
        if self.__defaulti != None and self.__infoFrejmovi != None:
            self.satniGraf.crtaj(self.__defaulti, self.__infoFrejmovi)
            self.minutniGraf.crtaj(self.__defaulti, self.__infoFrejmovi)
            
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
    def get_defaulti(self):
        """
        Metoda vraca dictionary sa informacijama o izgledu grafova, sto i kako 
        se crta.
        
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