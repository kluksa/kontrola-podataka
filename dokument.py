'''
Created on Apr 21, 2014

@author: kraljevic
'''
import pandas as pd
import numpy as np

from PyQt4 import QtGui,QtCore
from datetime import timedelta

import citac
import uredjaj
import agregator
import auto_validacija

class Dokument(QtGui.QWidget):
    '''
    classdocs
    -sublkasa QWidgeta zbog emit metode
    '''


    def __init__(self,parent=None):
        '''
        Constructor
        '''
        QtGui.QWidget.__init__(self,parent)
        #bitni memberi - varijable
        #svi dict bi trebali korisiti isti kljuc - komponentu (npr. SO2-ppb)
        #1. dict datafrejmova koji sadrze sve podatke
        self.frejmovi={}
        #2. dict satno agregiranih podataka
        self.agregirani={}
        #3. kljuc - trenutno aktivna komponenta (npr. SO2-ppb)
        self.aktivniFrame=None
        #4. trenutno odabrani satno agregirani podatak (sa satnog grafa)
        self.odabraniSatniPodatak=None
        #5. odabrani minutni podatak (sa minutnog grafa)
        self.odabraniMinutniPodatak=None
        #6. status satnog grafa? - da li je nacrtan
        self.grafStatusSatni=False
        #7. status minutnog grafa - da li je nacrtan
        self.grafStatusMinutni=False
        #8. popis svih ključeva mape frejmovi
        self.kljucSviFrejmovi=[]
        #9. dict uredjaja za agregator?
        self.dictUredjaja={}
        
        '''
        self.nizNizova = {}
        
        Gornji member u biti ne treba. Podatci za grafove su u drugom formatu
        -satni graf -> self.agregirani['self.aktivniFrame']
        -minutni graf -> self.frejmovi['self.aktivniFrame'].loc[min:max,u'koncentracija']
        '''
###############################################################################        
    def citaj_csv(self,path):
        """
        Ucitava podatke iz csv filea
        sprema sve kljuceve u member listu
        popunjava dict s uredjajima
        inicijalna agregacija sa autovalidacijom
        """
        reader=citac.WlReader()
        self.frejmovi=reader.citaj(path)
        self.kljucSviFrejmovi=list(self.frejmovi)
        self.set_uredjaji(self.kljucSviFrejmovi)
        self.agregiraj_sve(self.kljucSviFrejmovi)
        
        #emitiraj nove podatke o kljucu
        self.emit(QtCore.SIGNAL('update_kljuc(PyQt_PyObject)'),self.kljucSviFrejmovi)
###############################################################################
    def set_uredjaji(self,kljucevi):
        """
        Popunjavanje dicta s komponenta:uredjaj. Za sada su svi uredjaji M100C
        
        Manji problem je, nemam blage veze koji je uredjaj za koju komponentu
        i mislim da fali hrpa uredjaja u modulu uredjaj.py
        
        Direktno matchanje stringova zamjeniti regexom??
        """
        for kljuc in kljucevi:
            if kljuc=='S02':
                #nesto u ovom stilu...
                self.dictUredjaja[kljuc]=uredjaj.M100E()
            elif kljuc=='neki drugi':
                #drugi kljuc
                self.dictUredjaja[kljuc]=uredjaj.M100C()
            else:
                #neka generalna metoda???
                self.dictUredjaja[kljuc]=uredjaj.M100C()
###############################################################################
    def agregiraj_sve(self,frejmovi):
        """
        Agregiranje svih komponenata sa autovalidacijom.
        Ovu metodu je bitno pozvati nakon ucitavanja novih podataka barem jednom
        """
        for kljuc in list(frejmovi):
            ag=agregator.Agregator(self.dictUredjaja[kljuc])
            
            validator=auto_validacija.AutoValidacija()
            validator.dodaj_uredjaj(self.dictUredjaja[kljuc])
            validator.validiraj(self.frejmovi[kljuc])
            
            ag.setDataFrame(self.frejmovi[kljuc])
            self.agregirani[kljuc]=ag.agregirajNiz()
###############################################################################    
    def agregiraj_odabir(self,frejmovi,kljuc):
        """
        Agregiranje jedne komponente bez autovalidacije.
        Autovalidacija bi pregazila custom flagove.
        Nema smisla reagregirati sve ako je promjena samo na jednoj komponenti
        """
        ag=agregator.Agregator(self.dictUredjaja[kljuc])
        ag.setDataFrame(self.frejmovi[kljuc])
        self.agregirani[kljuc]=ag.agregirajNiz()
###############################################################################        
    def set_kanal(self,kanal):
        """
        Set aktivni frame, emitiraj signal za crtanje satnih podataka
        """
        self.aktivniFrame=kanal
        listaSatnih=[]
        for i in list(range(len(self.agregirani[self.aktivniFrame].index))):
            listaSatnih.append(str(self.agregirani[self.aktivniFrame].index[i]))
        
        self.emit(QtCore.SIGNAL('popis_satnih(PyQt_PyObject)'),listaSatnih)
        
        """
        #test, print datafrejma... graf izgleda cudno
        x=self.agregirani[self.aktivniFrame]
        print('average:')
        print(x['avg'])
        print('minutni podatci:')
        print(self.frejmovi[self.aktivniFrame].iloc[0:20,:])
        #dataframe satnih agregata ima hrpu nan vrijednosti...problem s autovalidacijom???
        """
        
        self.emit(
            QtCore.SIGNAL('crtaj_satni(PyQt_PyObject)'),
            self.agregirani[self.aktivniFrame])
###############################################################################
    def priprema_crtanja_minutni(self,vrijeme):
        """
        Nađi vremenske granice podataka,
        prosljedi listu datafrejmova za crtanje emitom
        """
        #klik s grafa vraca listu timestampova, value comboboxa je string
        if type(vrijeme)==list:
            vrijeme=vrijeme[0]
        if type(vrijeme)==str:
            vrijeme=pd.to_datetime(vrijeme)
        
        self.odabraniSatniPodatak=vrijeme
        #emit update comboboxa
        self.emit(QtCore.SIGNAL('set_satni_combobox(PyQt_PyObject)'),
                  str(vrijeme))
                  
        maxTime=vrijeme
        minTime=maxTime-timedelta(minutes=59)
        maxTime=str(maxTime)
        minTime=str(minTime)
        
        svi=self.frejmovi[self.aktivniFrame].loc[minTime:maxTime,:]
        sviOk=svi[svi.loc[:,u'flag']>=0]
        sviNotOk=svi[svi.loc[:,u'flag']<0]
        
        #treba nam samo podatak o koncentraciji
        svi=svi.loc[:,u'koncentracija']
        sviOk=sviOk.loc[:,u'koncentracija']
        sviNotOk=sviNotOk.loc[:,u'koncentracija']
        
        lista=[svi,sviOk,sviNotOk]
        self.emit(QtCore.SIGNAL('crtaj_minutni(PyQt_PyObject)'),lista)

###############################################################################
    def set_odabrani_sat(self,vrijeme):
        self.odabraniSatniPodatak=vrijeme
        self.emit(QtCore.SIGNAL('set_satni_combobox(PyQt_PyObject)'),
                  str(vrijeme))
        
        #kreni crtati graf
        self.priprema_crtanja_minutni(self.odabraniSatniPodatak)