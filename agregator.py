# -*- coding: utf-8 -*-
"""
Agregator dio
"""

import pandas as pd
from datetime import timedelta, datetime
import matplotlib.pyplot as plt

import citac
import auto_validacija
import uredjaj


class Agregator(object):
    
    uredjaji=[]

    def __init__(self, uredjaji):
        self.uredjaj = uredjaji
        
    def dodajUredjaj(self, uredjaj):
        self.uredjaji.append(uredjaj)
        
            
    def setDataFrame(self, df):
        self.__df = df
        self.pocetak = df.index.min()+pd.DateOffset(hours=1) 
        self.kraj = df.index.max()
        self.sviSati=pd.date_range(self.pocetak, self.kraj, freq='H')
    
    def agreg(self, kraj):
        #modifikacija get slice kopira direktno, bez flag testa
        dds=self.getSlajs(kraj)
        
        #test da li su svi not nan flagovi negativni
        ddNan=dds[pd.isnull(dds[u'koncentracija'])==False]
        ddFlag=ddNan[ddNan[u'flag']<0]
        if len(ddNan)==len(ddFlag):
            #svi not nan flagovi su negativni
            allFlagStatus=True
        else:
            allFlagStatus=False
        
        ddd=dds[dds[u'flag']>=0]
        avg=ddd.mean().iloc[0]
        std=ddd.std().iloc[0]
        max=ddd.max().iloc[0]
        min=ddd.min().iloc[0]
        med=ddd.quantile(0.5).iloc[0]
        q95=ddd.quantile(0.05).iloc[0]
        q05=ddd.quantile(0.95).iloc[0]
        count=ddd.count().iloc[0]
            
        status=0
        for i in ddd[u'status']:
            try:
                status|=int(i)
            except ValueError:
                status|=int(0)
        
        #prikazi druge podatke ako su svi flagovi manji od nule jer ddd je prazan
        if allFlagStatus:
            #prikazi agregat cijelog slajsa?
            avg=dds.mean().iloc[0]
            std=dds.std().iloc[0]
            max=dds.max().iloc[0]
            min=dds.min().iloc[0]
            med=dds.quantile(0.5).iloc[0]
            q95=dds.quantile(0.05).iloc[0]
            q05=dds.quantile(0.95).iloc[0]
            count=dds.count().iloc[0]
            
            status=0
            for i in dds[u'status']:
                try:
                    status|=int(i)
                except ValueError:
                    status|=int(0)

        data = {'avg':avg,'std':std,'min':min,'max':max,'med':med,'q95':q95,
                'q05':q05,'count':count,'status':status,'flagstat':allFlagStatus}
        return kraj, data
    
    def getSlajs(self, kraj):
        pocetak= kraj-timedelta(minutes=59)
# koristimo iskljucivo flagove, a ne statuse. Flagove odredjuje AutoValidacija
        #return self.__df[pocetak:kraj][self.__df['flag']>0]
        return self.__df[pocetak:kraj]
    
    def agregirajNiz(self):
        niz = []
        for sat in self.sviSati:
        	vrijeme, vrijednost = self.agreg(sat)
        	niz.append(vrijednost)
        return pd.DataFrame(niz, self.sviSati)
        
    def nizNiz(self):
        niz = []
        for sat in self.sviSati:
            fr = self.getSlajs(sat).iloc[:,0]
            niz.append(fr)
        return niz
    

if __name__ == "__main__":
    data = citac.WlReader().citaj('./data/pj.csv')
    u1 = uredjaj.M100E()
    u2 = uredjaj.M100C()
    u1.pocetak=datetime(2000,1,1)
    u2.pocetak=datetime(2014,2,24,0,10)
    u1.kraj=datetime(2014,2,24,0,10)
    u2.kraj=datetime(2015,1,1)
    
    a = auto_validacija.AutoValidacija()
    a.dodaj_uredjaj(u2)
    a.dodaj_uredjaj(u1)
    a.validiraj(data['1-SO2-ppb'])
    
    ag = Agregator([u1,u2])
    ag.setDataFrame(data['1-SO2-ppb'])
    agregirani = ag.agregirajNiz()
    nizNizova = ag.nizNiz()

    plt.boxplot(nizNizova)
    plt.plot(agregirani['avg'])
    plt.plot(agregirani['q05'])
    plt.plot(agregirani['q95'])
    plt.show()