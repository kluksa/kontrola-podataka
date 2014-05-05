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
    """
    def __init__(self,parent=None,width=6,height=5,dpi=100):
        fig=Figure(figsize=(width,height),dpi=dpi)
        self.axes=fig.add_subplot(111)
        FigureCanvas.__init__(self,fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(
            self,
            QtGui.QSizePolicy.Expanding,
            QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
    def crtaj(self):
        #metoda za crtanje, specifična klasa za pojedini graf je overloada
        pass 
###############################################################################    
class GrafSatniSrednjaci(MPLCanvas):
    """
    subklasa MPLCanvas, ona definira detalje crtanja isl.
    SIGNAL:
    QtCore.SIGNAL('odabirSatni(PyQt_PyObject)') -->slider selector
    
    """      
    def __init__(self,*args,**kwargs):
        MPLCanvas.__init__(self,*args,**kwargs)
        self.donjaGranica=None
        self.gornjaGranica=None
    
    def veze(self):
        self.cidpick=self.mpl_connect('pick_event',self.onpick)
    
    def onpick(self,event):
        """
        Pick average, plavi dijamanti - emitira signal sa izborom
        -satni interval je od npr 00:01:00 do 01:00:00, dakle trebamo
        emitirati odabir i tocku 59 minuta ranije.
        """
        linija=event.artist
        #sve x kooridinate
        xTocke=linija.get_xdata()
        #event index  
        tocka=event.ind
        xmax=xTocke[tocka]
        xmax=pd.to_datetime(xmax)
        xmin=xmax-timedelta(minutes=59)
        xmin=pd.to_datetime(xmin)
        
        if event.mouseevent.button==1:
            #left click -> iscrtava minutne podatke
            arg=[xmin,xmax]
            self.emit(QtCore.SIGNAL('crtajMinutni(PyQt_PyObject)'),arg)
        
        if event.mouseevent.button==3:
            #right click -> otvara izbornik za promjenu flaga satnih podataka
            opis='Odabrani interval od '+str(xmin)+' do '+str(xmax)
            tekst='Odaberi int vrijednost flaga:'
            flag,ok=QtGui.QInputDialog.getDouble(self,opis,tekst)
            if ok:
                arg=[xmin,xmax,flag]
                self.emit(QtCore.SIGNAL('flagSatni(PyQt_PyObject)'),arg)
            else:
                print('bez promjene - ovaj else se može brisati')
            
            
    def crtaj(self,data):
        """
        data je dictionary pandas datafrejmova koji izbacuje agregator
        """
        #x granice podataka - timestamp
        self.donjaGranica=data['avg'].index.min()
        self.gornjaGranica=data['avg'].index.max()
        #clear axes i crtaj
        
        self.axes.clear()
        title='Agregirani satni podaci\nod: '+str(self.donjaGranica)+' do: '+str(self.gornjaGranica)
        self.axes.set_title(title,fontsize=6)
        
        vrijeme=data['avg'].index
        
        self.axes.plot(vrijeme,data['avg'].values,
                       marker='d',
                       color='blue',
                       lw=1.5,
                       alpha=0.6,
                       label='average',
                       picker=3)
        self.axes.scatter(vrijeme,data['min'].values,
                          marker='+',
                          color='black',
                          lw=0.3,
                          label='min/max')
        self.axes.scatter(vrijeme,data['max'].values,
                          marker='+',
                          color='black',
                          lw=0.3)
        self.axes.plot(vrijeme,data['med'].values,
                       marker='x',
                       color='black',
                       lw=0.3,
                       label='median')
        self.axes.fill_between(vrijeme,data['q05'].values,data['q95'].values,
                               facecolor='green',
                               alpha=0.4)
        xLabels=self.axes.get_xticklabels()
        for label in xLabels:
            label.set_rotation(30)
            label.set_fontsize(6)
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
        
        canvasSatni=GrafSatniSrednjaci(self.mainWidget,width=6,height=5,dpi=150)
        canvasSatni.veze()
        
        mainLayout=QtGui.QVBoxLayout(self.mainWidget)
        mainLayout.addWidget(canvasSatni)
        self.setCentralWidget(self.mainWidget)
       
        #naredbe za spajanje siglala iz klasa
       
        #connect to test signal
        self.connect(canvasSatni,QtCore.SIGNAL('flagSatni(PyQt_PyObject)'),self.test_print)
        self.connect(canvasSatni,QtCore.SIGNAL('crtajMinutni(PyQt_PyObject)'),self.test_print)
        
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
                
        #naredba za plot
        canvasSatni.crtaj(data)
    
    def test_print(self,x):
        #samo test za provjeru emitiranog signala
        print(x)
        
if __name__=='__main__':
    aplikacija=QtGui.QApplication(sys.argv)
    app=ApplicationMain()
    app.show()
    sys.exit(aplikacija.exec_())
