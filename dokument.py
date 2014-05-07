'''
Created on Apr 21, 2014

@author: kraljevic
'''
import pandas as pd
import numpy as np

import citac
import uredjaj
import agregator
import auto_validacija

class Dokument(object):
    '''
    classdocs
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
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
        
    def citaj_csv(self,path):
        """
        Ucitava podatke iz csv filea
        sprema sve kljuceve u member listu
        popunjava dict s uredjajima
        """
        self.frejmovi=citac.WlReader.citaj(path)
        self.kljucSviFrejmovi=list(self.frejmovi)
        self.set_uredjaji(self.kljucSviFrejmovi)
        
        
    def set_uredjaji(self,kljucevi):
        """
        Popunjavanje dicta s komponenta:uredjaj.
        
        Manji problem je, nemam blage veze koji je uredjaj za koju komponentu
        i mislim da fali hrpa uredjaja u modulu uredjaj.py
        
        Direktno matchanje stringova zamjeniti regexom??
        """
        for kljuc in kljucevi:
            if kljuc=='S02':
                #nesto u ovom stilu...
                self.dictUredjaja[kljuc]=uredjaj.M100C()
            elif kljuc=='neki drugi':
                pass
            else:
                #neka generalna metoda???
                pass

    def set_agregirani_sve(self,frejmovi):
        #agregiranje i autovalidacija cijelog dicta frejmova
        for kljuc in list(frejmovi):
            ag=agregator.Agregator(self.dictUredjaja[kljuc])
                        
            validator=auto_validacija.AutoValidacija()
            validator.dodaj_uredjaj(self.dictUredjaja[kljuc])
            validator.validiraj(self.frejmovi[kljuc])
            
            ag.setDataFrame(self.frejmovi[kljuc])
            self.agregirani[kljuc]=ag.agregirajNiz()
    
    def set_agregirani_odabir(self,frejmovi,kljuc):
        """
        Agregiranje jedne komponente bez autovalidacije.
        Autovalidacija bi pregazila custom flagove.
        Nema smisla reagregirati sve ako je promjena samo na jednoj komponenti
        """
        ag=agregator.Agregator(self.dictUredjaja[kljuc])
        ag.setDataFrame(self.frejmovi[kljuc])
        self.agregirani[kljuc]=ag.agregirajNiz()


"""      
    def set_podaci(self,frejmovi):
        # autovalidacija i agregiranje
        for i in list(frejmovi):
            # agregator mora biti unutar petlje ili ga treba inicijalizirati za 
            # svaku komponentu unutar petlje jer nacelno nije isti validator za 
            # svaku komponentu.
            # Ako je unutar petlje onda ne treba biti member varijable, a ako postoji
            # dobar razlog da bude member (a postoji zbog ragregacije) onda mora biti 
            # mapa (komponenta, agregator)
            ag = agregator.Agregator(listaUredjaja)  # izbaciti izvan petlje?
            autoValidator.validiraj(self.data[i])                
            ag.setDataFrame(self.data[i])
            self.agregirani[i] = ag.agregirajNiz()
            self.nizNizova[i] = ag.nizNiz()         
"""            