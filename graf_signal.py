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
from matplotlib.widgets import SpanSelector

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
    ulaz je jedan pandas dataframe a ne dictiorary...treba prepraviti klasu!!!
    SIGNALI:
    odabirSatni(PyQt_PyObject)
        -odabir jednog satnog agregata, lijevi klik
        -emitira listu. [vrijeme(timestamp)]
    flagSatni(PyQt_PyObject)
        -promjena flaga jednog satnog agregata, desni klik
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
        #start annotation part
        self.tooltipTekst='time: %s\naverage: %0.2f\nmedian: %0.2f\nq05: %0.2f\nq95: %0.2f\nmin: %0.2f\nmax: %0.2f\ncount: %0.2f\nstatus: %0.2f'
        self.annX=0
        self.annY=0
        self.annotation=self.axes.annotate(
            self.tooltipTekst,
            xy=(self.annX,self.annY),
            xytext=(0.1,0.6),
            textcoords='axes fraction',
            ha='left',
            va='bottom',
            fontsize=5,
            bbox=dict(boxstyle='square',fc='cyan',alpha=0.7,zorder=10),
            arrowprops=dict(arrowstyle='->',connectionstyle='arc3,rad=0',alpha=0.6,zorder=10)
            )
        self.annotation.set_visible(False)
        #kraj annotation part
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
            
        if event.mouseevent.button==2:
            #annotations sa middle mouse gumbom
            #set pozicije na koju pointa strelica
            if self.zadnjiAnnotation==xtocka:
                self.annotation.remove()
                self.zadnjiAnnotation=None
                self.draw()
            else:
                self.annX=event.mouseevent.xdata
                self.annY=event.mouseevent.ydata
                self.annotation.xy=self.annX,self.annY
                #tekst annotationa
                avg=self.data['avg'].loc[xtocka]
                med=self.data['med'].loc[xtocka]
                q95=self.data['q95'].loc[xtocka]
                q05=self.data['q05'].loc[xtocka]
                min=self.data['min'].loc[xtocka]
                max=self.data['max'].loc[xtocka]
                count=self.data['count'].loc[xtocka]
                status=self.data['status'].loc[xtocka]
                self.annotation.set_text(self.tooltipTekst % (xtocka,avg,med,q05,q95,min,max,count,status))
                self.annotation.set_visible(True)
                self.zadnjiAnnotation=xtocka
                self.draw()
                self.annotation.remove()
        
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
        data je pandas dataframe koji izbacuje agregator-ima posebni stupac
        'flagstat'. Taj stupac je True ako su svi flagovi tocaka
        s podatcima negativni (False ako ima pozitivnih flagova).
        -kako smisleno prikazati podatke???
        """
        self.data=data
        self.zadnjiAnnotation=None
        #x granice podataka - timestamp
        self.donjaGranica=data['avg'].index.min()
        self.gornjaGranica=data['avg'].index.max()
        #clear axes i crtaj
        
        self.axes.clear()
        title='Agregirani satni podaci od: '+str(self.donjaGranica)+' do: '+str(self.gornjaGranica)
        self.axes.set_title(title,fontsize=4)
        
        #ukupni raspon podataka
        vrijeme=data['avg'].index
        
        """
        Svi koji imaju flagstat stupac False
        tj. normalni slucaj, kada svi minutni podatci u sliceu nemaju negativan flag
        """
        self.data1=data[data['flagstat']==False]
        vrijeme1=self.data1['avg'].index
        self.axes.plot(vrijeme1,self.data1['avg'].values,
                       marker='d',
                       color='blue',
                       lw=1.5,
                       alpha=0.7,
                       picker=2,
                       zorder=3)
        self.axes.scatter(vrijeme1,self.data1['min'].values,
                          marker='+',
                          color='black',
                          lw=0.3,
                          alpha=0.6,
                          zorder=2)
        self.axes.scatter(vrijeme1,self.data1['max'].values,
                          marker='+',
                          color='black',
                          lw=0.3,
                          alpha=0.6,
                          zorder=2)
        self.axes.scatter(vrijeme1,self.data1['med'].values,
                       marker='_',
                       color='black',
                       lw=1.5,
                       alpha=0.6,
                       zorder=2)
        self.axes.fill_between(vrijeme1,
                               self.data1['q05'].values,
                               self.data1['q95'].values,
                               facecolor='green',
                               alpha=0.4,
                               zorder=1)
        
        """
        Svi koji imaju flagstat stupac True
        tj - svi minutni podatci u sliceu imaju flag manji od 0
        """
        self.data2=data[data['flagstat']==True]
        vrijeme2=self.data2['avg'].index
        self.axes.plot(vrijeme2,self.data2['avg'].values,
                       marker='d',
                       color='red',
                       lw=1.5,
                       alpha=0.7,
                       picker=2,
                       zorder=3)
        self.axes.scatter(vrijeme2,self.data2['min'].values,
                          marker='+',
                          color='black',
                          lw=0.3,
                          alpha=0.6,
                          zorder=2)
        self.axes.scatter(vrijeme2,self.data2['max'].values,
                          marker='+',
                          color='black',
                          lw=0.3,
                          alpha=0.6,
                          zorder=2)
        self.axes.scatter(vrijeme2,self.data2['med'].values,
                       marker='_',
                       color='black',
                       lw=1.5,
                       alpha=0.6,
                       zorder=2)
        self.axes.fill_between(vrijeme2,
                               self.data2['q05'].values,
                               self.data2['q95'].values,
                               facecolor='tomato',
                               alpha=0.4,
                               zorder=1)
        
        
        
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
        [0] cijeli -> cijeli dataframe (sluzi za plot linije)
        [1] pozitivanFlag ->dio dataframe gdje je flag >=0 (za scatter plot)
        [2] negativanFlag ->dio dataframe gdje je flag <0 (za scatter plot)
    SIGNALI:
    flagTockaMinutni(PyQt_PyObject)
        -izbor jedne tocke kojoj treba promjeniti flag - desni klik
        -emitira listu - [vrijeme(timestamp),novi flag]
    flagSpanMinutni(PyQt_PyObject)
        -izbor spana, lijevi klik & drag. na klik granice su identicne
        -emitira listu - [vrijeme min, vrijeme max, novi flag]
        -min i max granice su isti broj na jedan ljevi klik...problem?
    """
    def __init__(self,*args,**kwargs):
        MPLCanvas.__init__(self,*args,**kwargs)
        self.donjaGranica=None
        self.gornjaGranica=None
        self.veze()
    
    def veze(self):
        #desni klik za izbor jedne točke
        self.cidpick=self.mpl_connect('pick_event',self.onpick)
        #span selector
        self.span=SpanSelector(self.axes,
                               self.minutni_span_flag,
                               'horizontal',
                               useblit=True,
                               rectprops=dict(alpha=0.5,facecolor='tomato')
                               )
    
    def minutni_span_flag(self,xmin,xmax):
        #test da li je graf nacrtan
        if ((self.donjaGranica!=None) and (self.gornjaGranica!=None)):
            xmin=round(xmin)
            xmax=round(xmax)
            puniSatMin=False
            puniSatMax=False
        
            if xmin==60:
                puniSatMin=True
                xmin='00'
            else:
                xmin=str(xmin)
            
            if xmax==60:
                puniSatMax=True
                xmax='00'
            else:
                xmax=str(xmax)
        
            #sastavi timestamp
            godina=str(self.donjaGranica.year)
            mjesec=str(self.donjaGranica.month)
            dan=str(self.donjaGranica.day)
            sat=str(self.donjaGranica.hour)
            timeMin=godina+'-'+mjesec+'-'+dan+' '+sat+':'+xmin+':'+'00'
            timeMax=godina+'-'+mjesec+'-'+dan+' '+sat+':'+xmax+':'+'00'
            minOznaka=pd.to_datetime(timeMin)
            maxOznaka=pd.to_datetime(timeMax)
        
            if puniSatMin:
                minOznaka=minOznaka+timedelta(hours=1)
            
            if puniSatMax:
                maxOznaka=maxOznaka+timedelta(hours=1)
            
            opis='Odabrani interval od '+str(minOznaka)+' do '+str(maxOznaka)
            tekst='Odaberi novu vrijednost flaga:'
            flag,ok=QtGui.QInputDialog.getDouble(self,opis,tekst)
            if ok:
                #provjeri da li je min i max ista tocka..
                if minOznaka==maxOznaka:
                    arg=[minOznaka,flag]
                    self.emit(QtCore.SIGNAL('flagSpanMinutni(PyQt_PyObject)'),arg)
                else:
                    arg=[minOznaka,maxOznaka,flag]
                    self.emit(QtCore.SIGNAL('flagSpanMinutni(PyQt_PyObject)'),arg)
        else:
            message='Unable to select data, draw some first'
            self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),message)
        
    def onpick(self,event):
        """
        Picker na minutnom grafu
        """
        #start annotation part
        self.tooltipTekst='time: %s\nkoncentracija: %0.2f\nflag: %0.2f\nstatus: %0.2f'
        self.annX=0
        self.annY=0
        self.annotation=self.axes.annotate(
            self.tooltipTekst,
            xy=(self.annX,self.annY),
            xytext=(0.1,0.6),
            textcoords='axes fraction',
            ha='left',
            va='bottom',
            fontsize=5,
            bbox=dict(boxstyle='square',fc='cyan',alpha=0.7,zorder=10),
            arrowprops=dict(arrowstyle='->',connectionstyle='arc3,rad=0',alpha=0.6,zorder=10)
            )
        self.annotation.set_visible(False)
        #kraj annotation part
        
        puniSat=False
        #overlap pickera?
        izbor=event.mouseevent.xdata
        if type(izbor)==list:
            izbor=izbor[0]
            
        izbor=round(izbor)
        if izbor==60:
            puniSat=True
            izbor='00'
        else:
            izbor=str(izbor)
        #sastavi timestamp
        godina=str(self.donjaGranica.year)
        mjesec=str(self.donjaGranica.month)
        dan=str(self.donjaGranica.day)
        sat=str(self.donjaGranica.hour)
        time=godina+'-'+mjesec+'-'+dan+' '+sat+':'+izbor+':'+'00'
        timeOznaka=pd.to_datetime(time)
        if puniSat:
            timeOznaka=timeOznaka+timedelta(hours=1)
        
        #desni klik - promjena flaga jedne tocke
        if event.mouseevent.button==3:
            opis='Odabrano vrijeme: '+str(timeOznaka)
            tekst='Odaberi novu vrijednost flaga:'
            flag,ok=QtGui.QInputDialog.getDouble(self,opis,tekst)
            if ok:
                arg=[timeOznaka,flag]
                self.emit(QtCore.SIGNAL('flagTockaMinutni(PyQt_PyObject)'),arg)
                
        #middle klik misem, annotation tocke
        if event.mouseevent.button==2:
            if self.zadnjiAnnotation==timeOznaka:
                self.annotation.remove()
                self.zadnjiAnnotation=None
                self.draw()
            else:
                self.annX=event.mouseevent.xdata
                self.annY=event.mouseevent.ydata
                self.annotation.xy=self.annX,self.annY
                #tekst annotationa
                izbor=str(timeOznaka)
                koncentracija=self.dataframe.loc[izbor,u'koncentracija']
                status=self.dataframe.loc[izbor,u'status']
                flag=self.dataframe.loc[izbor,u'flag']
                self.annotation.set_text(self.tooltipTekst % (izbor,koncentracija,flag,status))
                self.annotation.set_visible(True)
                self.zadnjiAnnotation=timeOznaka
                self.draw()
                self.annotation.remove()

    def crtaj(self,data):
        """
        x os plota će biti minute timestampa od 1 do 60
        """
        self.zadnjiAnnotation=None
        self.dataframe=data[0]
        #zapamti podatke o timestampu za datum i sat
        self.donjaGranica=data[0].index.min()
        self.gornjaGranica=data[0].index.max()
        #priprema za crtanje
        self.axes.clear()
        title='Minutni podaci od: '+str(self.donjaGranica)+' do: '+str(self.gornjaGranica)
        self.axes.set_title(title,fontsize=4)
        linija=data[0].loc[:,u'koncentracija']
        tockeOk=data[1].loc[:,u'koncentracija']
        tockeNo=data[2].loc[:,u'koncentracija']
        xMinute=[]
        xFlagOk=[]
        xFlagNo=[]
        
        if len(linija)!=0:
            for i in linija.index:
                if i.minute!=0:
                    xMinute.append(i.minute)
                else:
                    xMinute.append(60)
        
        if len(tockeOk)!=0:
            for i in tockeOk.index:
                if i.minute!=0:
                    xFlagOk.append(i.minute)
                else:
                    xFlagOk.append(60)
        
        if len(tockeNo)!=0:
            for i in tockeNo.index:
                if i.minute!=0:
                    xFlagNo.append(i.minute)
                else:
                    xFlagNo.append(60)
        
        if len(xMinute)==len(linija.values):
            self.axes.plot(xMinute,linija.values,
                           color='black')
        
        if len(xFlagOk)==len(tockeOk.values):
            self.axes.scatter(xFlagOk,tockeOk.values,
                              color='green',
                              marker='o',
                              picker=2,
                              alpha=0.4)
        
        if len(xFlagNo)==len(tockeNo.values):
            self.axes.scatter(xFlagNo,tockeNo.values,
                              color='red',
                              marker='o',
                              picker=2,
                              alpha=0.4)
        
        xLabels=self.axes.get_xticklabels()
        for label in xLabels:
            label.set_fontsize(4)
            
        yLabels=self.axes.get_yticklabels()
        for label in yLabels:
            label.set_fontsize(4)
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
        self.connect(canvasMinutni,QtCore.SIGNAL('flagTockaMinutni(PyQt_PyObject)'),self.test_print)
        self.connect(canvasMinutni,QtCore.SIGNAL('flagSpanMinutni(PyQt_PyObject)'),self.test_print)
        
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
        status=np.random.rand(len(vrijeme))
        std=np.random.rand(len(vrijeme))
        count=np.random.rand(len(vrijeme))
        #testni data frame za satni graf
        data=pd.DataFrame(
            {'avg':avg,
            'min':min,
            'max':max,
            'med':median,
            'q05':q05,
            'q95':q95,
            'status':status,
            'std':std,
            'count':count},
            index=vrijeme)
        
        #test podatci za minutni graf
        time=pd.date_range('2014-05-15 12:01:00',periods=60,freq='Min')
        konc=10+np.random.rand(len(time))
        flag=np.random.rand(len(time))
        flag[20:30]=-1
        status=np.random.rand(len(time))
        dic={u'koncentracija':konc,u'flag':flag,u'status':status}
        
        #slapanje datafrejmova za graf
        df=pd.DataFrame(dic,index=time)
        dfKonc=df
        dfOk=df[df.loc[:,u'flag']>=0]
        dfNo=df[df.loc[:,u'flag']<0]
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