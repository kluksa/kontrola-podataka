# -*- coding: utf-8 -*-
"""
Created on Tue Apr 29 08:32:47 2014

@author: velimir

Izdvajanje grafova u pojedine klase. Dodana je mini aplikacija za funkcionalno testiranje
"""

#import statements
import sys
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt4 import QtGui,QtCore
import pandas as pd
import numpy as np
from datetime import timedelta

###############################################################################
class MPLCanvas(FigureCanvas):
    """
    matplotlib canvas class, generalni
    -overloadaj metodu crtaj sa specificnim naredbama
    """
    def __init__(self,parent=None,width=6,height=5,dpi=100):
        self.fig=Figure(figsize=(width,height),dpi=dpi)
        self.axes=self.fig.add_subplot(111)
        FigureCanvas.__init__(self,self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(
            self,
            QtGui.QSizePolicy.Expanding,
            QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
    def crtaj(self):
        pass
    
    def brisi_graf(self):
        self.axes.clear()
###############################################################################    
class GrafSatniSrednjaci(MPLCanvas):
    """
    subklasa MPLCanvas, ona definira detalje crtanja isl.
    SIGNALI:
    odabirSatni(PyQt_PyObject)
        -odabir jednog satnog agregata
        -emitira listu. [vrijeme(timestamp)]
    flagSatni(PyQt_PyObject)
        -promjena flaga jednog satnog agregata
        -emitira listu. [vrijeme(timestamp), novi flag]
    """      
    def __init__(self,*args,**kwargs):
        MPLCanvas.__init__(self,*args,**kwargs)
        self.donjaGranica=None
        self.gornjaGranica=None
        self.veze()
    
    def veze(self):
        self.cidpick=self.mpl_connect('pick_event',self.onpick)
    
    def onpick(self,event):
        """
        Pick average, plavi dijamanti - emitira signal sa izborom
        """
        linija=event.artist
        xTocke=linija.get_xdata()
        tocka=event.ind
        xtocka=xTocke[tocka]
        xtocka=pd.to_datetime(xtocka)
        #kod resizanja grafa - mogući problem je preklapanje pickera
        #kludge fix za sada - odabrati manji i smanjiti radijus pickera
        xtocka=xtocka[0]
                
        if event.mouseevent.button==1:
            #left click
            arg=[xtocka]
            self.emit(QtCore.SIGNAL('odabirSatni(PyQt_PyObject)'),arg)
        
        if event.mouseevent.button==3:
            #right click
            opis='Odabrano vrijeme: '+str(xtocka)
            tekst='Odaberi novu vrijednost flaga:'
            flag,ok=QtGui.QInputDialog.getDouble(self,opis,tekst)
            if ok:
                arg=[xtocka,flag]
                self.emit(QtCore.SIGNAL('flagSatni(PyQt_PyObject)'),arg)
            
            
    def crtaj(self,data):
        """
        data je dictionary pandas datafrejmova koji izbacuje agregator
        """
        #x granice podataka - timestamp
        self.donjaGranica=data['avg'].index.min()
        self.gornjaGranica=data['avg'].index.max()
        #clear axes i crtaj
        
        self.axes.clear()
        title='Agregirani satni podaci od: '+str(self.donjaGranica)+' do: '+str(self.gornjaGranica)
        self.axes.set_title(title,fontsize=4)
        
        vrijeme=data['avg'].index
        
        self.axes.plot(vrijeme,data['avg'].values,
                       marker='d',
                       color='blue',
                       lw=1.5,
                       alpha=0.5,
                       picker=2)
        self.axes.scatter(vrijeme,data['min'].values,
                          marker='+',
                          color='black',
                          lw=0.3)
        self.axes.scatter(vrijeme,data['max'].values,
                          marker='+',
                          color='black',
                          lw=0.3)
        self.axes.scatter(vrijeme,data['med'].values,
                       marker='_',
                       color='black',
                       lw=1)
        self.axes.fill_between(vrijeme,data['q05'].values,data['q95'].values,
                               facecolor='green',
                               alpha=0.4)
        
        xLabels=self.axes.get_xticklabels()
        for label in xLabels:
            label.set_rotation(20)
            label.set_fontsize(4)
            
        yLabels=self.axes.get_yticklabels()
        for label in yLabels:
            label.set_fontsize(4)
            
        #pokusaj automatskog poravnavanja grafa, labela isl.
        self.axes.set_xlim(vrijeme.min(),vrijeme.max())
        self.fig.tight_layout()
        self.draw()
###############################################################################        
class GrafMinutniPodaci(MPLCanvas):
    """
    Graf za crtanje minutnih podataka.
    Ulaz:
    data je lista pandas datafrejmova, satni slice koncetracije
       0 cijeli -> cijeli dataframe (sluzi za plot linije)
       1 pozitivanFlag ->dio dataframe gdje je flag >=0 (za scatter plot)
       2 negativanFlag ->dio dataframe gdje je flag <0 (za scatter plot)
    """
    def __init__(self,*args,**kwargs):
        MPLCanvas.__init__(self,*args,**kwargs)
        
    def crtaj(self,data):
        """
        x os plota će biti minute timestampa od 1 do 60
        """

        #priprema za crtanje
        self.axes.clear()
        linija=data[0]
        tockeOk=data[1]
        tockeNo=data[2]
        xMinute=[]
        xFlagOk=[]
        xFlagNo=[]
        
        for i in linija.index:
            if i.minute!=0:
                xMinute.append(i.minute)
            else:
                xMinute.append(60)
        
        for i in tockeOk.index:
            if i.minute!=0:
                xFlagOk.append(i.minute)
            else:
                xFlagOk.append(60)
        
        for i in tockeNo.index:
            if i.minute!=0:
                xFlagNo.append(i.minute)
            else:
                xFlagNo.append(60)
        
        if len(xMinute)!=0:
            self.axes.plot(xMinute,linija.values,
                           color='black',
                           alpha=0.8)
                       
        if len(xFlagOk)!=0:
            self.axes.scatter(xFlagOk,tockeOk.values,
                              color='green',
                              marker='o')
        
        if len(xFlagNo)!=0:
            self.axes.scatter(xFlagNo,tockeNo.values,
                              color='red',
                              marker='o')
                              
        #pokusaj automatskog proavnavanja
        self.axes.set_xlim(1,60)
        self.fig.tight_layout()
        self.draw()
###############################################################################        
class ApplicationMain(QtGui.QMainWindow):
    """
    Testna aplikacija za provjeru ispravnosti MPL klasa za Qt
    """
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("Testna aplikacija")
        self.mainWidget=QtGui.QWidget(self)
        self.widget1=QtGui.QWidget()
        self.widget2=QtGui.QWidget()
        
        canvasSatni=GrafSatniSrednjaci(self.widget1,width=6,height=5,dpi=150)
        canvasMinutni=GrafMinutniPodaci(self.widget2,width=6,height=5,dpi=150)        
        
        mainLayout=QtGui.QVBoxLayout(self.mainWidget)
        mainLayout.addWidget(canvasSatni)
        mainLayout.addWidget(canvasMinutni)
        self.setCentralWidget(self.mainWidget)
       
        #connect to test signal
        self.connect(canvasSatni,QtCore.SIGNAL('flagSatni(PyQt_PyObject)'),self.test_print)
        self.connect(canvasSatni,QtCore.SIGNAL('odabirSatni(PyQt_PyObject)'),self.test_print)
        
        """
        Testni podaci, dictionary pandas datafrejmova koji je rezultat agregatora.
        Koristim istu strukturu podataka ali random vrijednosti
        """
        vrijeme=pd.date_range('2014-03-15 12:00:00',periods=36,freq='H')
        avg=10+np.random.rand(len(vrijeme))
        min=6+np.random.rand(len(vrijeme))
        max=14+np.random.rand(len(vrijeme))
        median=10+np.random.rand(len(vrijeme))
        q05=12+np.random.rand(len(vrijeme))
        q95=8+np.random.rand(len(vrijeme))
        ts1=pd.Series(avg,vrijeme)
        ts2=pd.Series(min,vrijeme)
        ts3=pd.Series(max,vrijeme)
        ts4=pd.Series(median,vrijeme)
        ts5=pd.Series(q05,vrijeme)
        ts6=pd.Series(q95,vrijeme)
        data={'avg':ts1,'min':ts2,'max':ts3,'med':ts4,'q05':ts5,'q95':ts6}
        
        #test podatci za minutni graf
        time=pd.date_range('2014-05-15 12:01:00',periods=60,freq='Min')
        konc=10+np.random.rand(len(time))
        flag=np.random.rand(len(time))
        flag[20:30]=-1
        status=np.random.rand(len(time))
        dic={u'koncentracija':konc,u'flag':flag,u'status':status}
        
        #slapanje datafrejmova za graf
        df=pd.DataFrame(dic,index=time)
        dfKonc=df.loc[:,u'koncentracija']
        dfOk=df[df.loc[:,u'flag']>=0]
        dfOk=dfOk.loc[:,u'koncentracija']
        dfNo=df[df.loc[:,u'flag']<0]
        dfNo=dfNo.loc[:,u'koncentracija']
        mData=[dfKonc,dfOk,dfNo]
        
        #naredba za plot
        canvasSatni.crtaj(data)
        canvasMinutni.crtaj(mData)
    
    def test_print(self,x):
        #samo test za provjeru emitiranog signala
        print(x)
        
if __name__=='__main__':
    aplikacija=QtGui.QApplication(sys.argv)
    app=ApplicationMain()
    app.show()
    sys.exit(aplikacija.exec_())
