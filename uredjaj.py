# -*- coding: utf-8 -*-
"""
Created on Sat Mar  8 21:09:15 2014

@author: kraljevic

Velimir
1.lagana izmjena WlApi.status_agregator
"""
from datetime import datetime

class Uredjaj(object):
    def validan(self, status):
        raise NotImplementedError("Please Implement this method")
    def status_agregator(self, statusLista) :
        raise NotImplementedError("Please Implement this method")
    def validnost(self, status):
        return [(self.validan(s)) for s in status]
        #return [(self.valid(s)) for s in status]
        
class WlApi(Uredjaj):
    def status_agregator(self, statusLista):
        status=0
        for s in statusLista:
            """
            kludge fix.
            1. Binary OR radi samo na tipu integer, zato int() (pandas df
                sprema podatke kao np.float64 ili nešto slično)
            2. Na tekst ne bi trebao naletiti, ali np.nan je problem
                forsiram da np.nan tretira kao nulu, ali ako postoji
                neki bolji status kod koji pokriva taj slučaj, lako se
                zamjeni. ValueError se javi ako int(s) ne primi dobar argument
            """
            try:
                status |= int(s)
            except ValueError:
                status|=int(0)
        return s

        
class M100E(WlApi):
    pocetak=datetime(1014,2,1)
    kraj=datetime(3014,2,24,16,0)

    def validan(self, status):
        if status == 0:
            return 22
        elif status == 1:
            return 23
        elif status == 2:
            return 24
        else:
            return -22
            
            

class M100C(WlApi):
    pocetak=datetime(1014,2,24,16,1)
    kraj=datetime(3014,2,26,16,0)

    def validan(self, status):
        if status == 0:
            return 102
        else:
            return -102
       
