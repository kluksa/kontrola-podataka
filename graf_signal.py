# -*- coding: utf-8 -*-
"""
Created on Tue Apr 29 08:32:47 2014

@author: velimir

Izdvajanje grafova u pojedine klase. Dodana je mini aplikacija za funkcionalno testiranje
"""

#import statements
import sys
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import datetime
from datetime import timedelta
from PyQt4 import QtGui,QtCore
import pandas as pd
from matplotlib.widgets import SpanSelector
#import numpy as np

#pomocni...samo za lokalni test
import citac
from agregator import Agregator


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
    
    def brisi_graf(self):
        self.axes.clear()
        self.draw()
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
class HoverAnotation(object):
    #TODO!
    #dovrsi
    """
    cilj: kad se misem priblizimo nekoj od zadanih tocaka, da se za nju prikaze
    annotation
    """
    def __init__(self, ax, x, y, tolerance = 3, formatter = str, offsets = (-20, 20)):
        self.offsets = offsets
        self.formatter = formatter
        self.tolerance = tolerance
        self.ax = ax
        self.dot = ax.scatter(x[0], y[0], s=130, color='yellow', alpha=0.7)
        self.annotation = self.setup_annotation()
        self.ax.connect('motion_notify_event', self)
        
    def setup_annotation(self):
        """
        setup za annotation
        """
        annotation = self.ax.annotate(
            '', 
            xy=(0, 0), 
            ha = 'right',
            xytext = self.offsets, 
            textcoords = 'offset points', 
            va = 'bottom', 
            bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.75), 
            arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0'))
        return annotation
        
    def __call__(self, event):
        """
        event je pomak cursora unutar grafa
        cilj: oznaciti tocku blizu koje je mis, napisati njen annotation
        """
        ax = self.ax
        if event.inaxes == ax:
            x, y = event.xdata, event.ydata
        else:
            return
            
        annotation = self.annotation
        x, y = self.snap(x,y)
        annotation.xy = x, y
        annotation.set_text(self.formatter(x, y))
        self.dot.set_offsets((x, y))
        event.canvas.draw()
        
    def snap(self, x, y):
        """
        funkcija treba vratiti kooridinate x,y blize tocke cursoru
        """
        pass

###############################################################################
###############################################################################
class GrafSatniSrednjaci(MPLCanvas):
    """
    subklasa MPLCanvas, definira detalje crtanja satnog grafa
    """
    def __init__(self, *args, **kwargs):
        MPLCanvas.__init__(self, *args, **kwargs)
        self.donjaGranica = None
        self.gornjaGranica = None
        self.data = None
        self.veze()
###############################################################################        
    def veze(self):
        self.cidpick = self.mpl_connect('pick_event', self.onpick)
###############################################################################        
    def onpick(self, event):
        """
        akcije prilikom eventa, odabira na grafu
        """
        xpoint = event.mouseevent.xdata
        xpoint = matplotlib.dates.num2date(xpoint) #datetime.datetime
        #problem.. rounding offset aware i offset naive datetimes..workaround
        god = xpoint.year
        mon = xpoint.month
        day = xpoint.day
        h = xpoint.hour
        m = xpoint.minute
        s = xpoint.second
        xpoint = datetime.datetime(god, mon, day, h, m, s)
        xpoint = zaokruzi_vrijeme(xpoint, 3600)   #round na najblizi sat
                
        if event.mouseevent.button == 1:
            #left click
            xtime = pd.to_datetime(xpoint)
            arg = xtime
            print('ljevi klik, arg: ', arg) #samo test izlaznog podatka
            self.emit(QtCore.SIGNAL('gui_crtaj_minutni_graf(PyQt_PyObject)'), 
                      arg)
        
        if event.mouseevent.button == 3:
            #right click
            tmax = xpoint
            tmin = xpoint - timedelta(minutes = 59)
            tmax = pd.to_datetime(tmax)
            tmin = pd.to_datetime(tmin)
            opis = 'Odabrano vrijeme: \nOD: '+str(tmin)+'\nDO: '+str(tmax)
            flag = FlagDijalog(message = opis)
            if flag.odgovor == 'valja':
                arg = [tmin, tmax, 1]
                print('good flag change: ', arg)
                self.emit(QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), arg)
            elif flag.odgovor=='nevalja':
                arg = [tmin, tmax, -1]
                print('bad flag change: ', arg)
                self.emit(QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), arg)
            else:
                pass
###############################################################################            
    def crtaj(self, data):
        """
        priprema podataka i eksplicitne naredbe za crtanje
        """
        if len(data) != 0:
            self.data = data
            self.axes.clear()
            
            #x granice podataka - timestamp
            self.donjaGranica = data[u'avg'].index.min()
            self.gornjaGranica = data[u'avg'].index.max()
            
            #naslov grafa
            title = 'Agregirani podaci od: '+str(self.donjaGranica)+' do: '+str(self.gornjaGranica)
            self.axes.set_title(title, fontsize=4)
            
            #priprema vrijednosti za crtanje
            #agregirani podatci sa dobrim flagovima
            data = self.data.copy()
            data1 = data[data[u'flag'] >= 0]
            #agregirani podatci sa losim flagovima
            data = self.data.copy()
            data2 = data[data[u'flag'] < 0]
            
            if len(data1) != 0:
                vrijeme1 = list(data1[u'avg'].index)
                avg1 = list(data1[u'avg'])                
                self.axes.scatter(vrijeme1, avg1,
                          marker='o',
                          color='green', 
                          zorder = 3, 
                          picker = 2)                          
                          
            if len(data2) != 0:
                vrijeme2 = list(data2[u'avg'].index)
                avg2 = list(data2[u'avg'])               
                self.axes.scatter(vrijeme2, avg2,
                          marker='o',
                          color='red', 
                          zorder = 3, 
                          picker = 2)
                          
            #ostali dijelovi grafa
            vrijeme = list(data[u'avg'].index)
            minValue = list(data[u'min'])
            maxValue = list(data[u'max'])
            q05 = list(data[u'q05'])
            q95 = list(data[u'q95'])
            median = list(data[u'median'])
            
            self.axes.scatter(vrijeme, minValue,
                              marker = '+', 
                              color = 'black', 
                              lw = 0.5, 
                              zorder = 2)
            
            self.axes.scatter(vrijeme, maxValue,
                              marker = '+', 
                              color = 'black', 
                              lw = 0.5, 
                              zorder = 2)

            self.axes.plot(vrijeme, median,  
                       color='black', 
                       lw = 1.2, 
                       alpha = 0.5, 
                       zorder = 2)
                       
            self.axes.fill_between(vrijeme, 
                               q05, 
                               q95, 
                               facecolor = 'blue', 
                               alpha = 0.3, 
                               zorder = 1)


                                          
            #granice crtanog podrucja
            #x-os
            minxlim = vrijeme[0] - timedelta(hours = 1)
            minxlim = pd.to_datetime(minxlim)
            maxxlim = vrijeme[len(vrijeme)-1] + timedelta(hours = 1)
            maxxlim = pd.to_datetime(maxxlim)
            self.axes.set_xlim(minxlim, maxxlim)
            
            #y-os
            raspon = minValue + maxValue
            raspon.sort()
            minylim = raspon[0] #najmanja crijednost
            maxylim = raspon[len(raspon)-1] #najveca vrijednost
            pad = (minylim + maxylim)/5 #padding da nisu na rubu
            minylim = minylim - pad
            maxylim = maxylim + pad
            self.axes.set_ylim(minylim, maxylim)
            
            #format x kooridinate
            xLabels = self.axes.get_xticklabels()
            for label in xLabels:
                label.set_rotation(20)
                label.set_fontsize(4)
            
            #format y kooridinate
            yLabels=self.axes.get_yticklabels()
            for label in yLabels:
                label.set_fontsize(4)
                
            self.fig.tight_layout()
            self.draw()
            
        else:
            self.axes.clear()
            #napisi poruku na grafu da nema podataka
            self.axes.text(0.5, 0.5, 
                           'Nema izmjerenih podataka.', 
                           horizontalalignment = 'center', 
                           verticalalignment ='center', 
                           size = 'medium')
            self.fig.tight_layout()
            self.draw()

###############################################################################
###############################################################################
class GrafMinutniPodaci(MPLCanvas):
    """
    Klasa, canvas za crtanje minutnih podataka
    """
    def __init__(self, *args, **kwargs):
        MPLCanvas.__init__(self, *args, **kwargs)
        self.donjaGranica = None
        self.gornjaGranica = None
        self.data = None
        self.dataTest = False
        
        self.veze()
###############################################################################        
    def veze(self):
        """avg1 = list(data1[u'avg'])                
                self.axes.scatter(vrijeme1, avg1,
                          marker='d',
                          color='green', 
                          zorder = 3, 
                          picker = 2)   
        event connect, span selector...
        """
        self.cidpick = self.mpl_connect('pick_event', self.onpick)
        self.span = SpanSelector(self.axes, 
                                 self.minutni_span_flag, 
                                 'horizontal', 
                                 useblit = True, 
                                 rectprops = dict(alpha = 0.3,
                                                  facecolor = 'yellow')
                                )
###############################################################################    
    def onpick(self, event):
        """
        pick event, desni klik za promjenu flaga
        """
        xpoint = event.mouseevent.xdata
        xpoint = matplotlib.dates.num2date(xpoint) #datetime.datetime
        #problem.. rounding offset aware i offset naive datetimes..workaround
        god = xpoint.year
        mon = xpoint.month
        day = xpoint.day
        h = xpoint.hour
        m = xpoint.minute
        s = xpoint.second
        xpoint = datetime.datetime(god, mon, day, h, m, s)
        xpoint = zaokruzi_vrijeme(xpoint, 60)   #round na najblizu minutu
                
        if event.mouseevent.button == 3:
            #right click
            t = pd.to_datetime(xpoint)
            opis = 'Odabrano vrijeme: '+str(t)
            flag = FlagDijalog(message = opis)
            if flag.odgovor == 'valja':
                arg = [t, t, 1]
                print('good flag change: ', arg)
                self.emit(QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), arg)
            elif flag.odgovor=='nevalja':
                arg = [t, t, -1]
                print('bad flag change: ', arg)
                self.emit(QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), arg)
            else:
                pass
###############################################################################
    def minutni_span_flag(self, xmin, xmax):
        """
        span selector za promjenu flaga na nizu podataka
        """
        if self.dataTest == False:
            #ako nema nacrtanih podataka, zanemari span
            return
        xmin = matplotlib.dates.num2date(xmin)
        xmax = matplotlib.dates.num2date(xmax)
        xmin = datetime.datetime(xmin.year, xmin.month, xmin.day, xmin.hour, xmin.minute, xmin.second)
        xmax = datetime.datetime(xmax.year, xmax.month, xmax.day, xmax.hour, xmax.minute, xmax.second)
        xmin = zaokruzi_vrijeme(xmin, 60)
        if xmin < self.donjaGranica:
            xmin = self.donjaGranica
        if xmin > self.gornjaGranica:
            xmin = self.gornjaGranica
        xmax = zaokruzi_vrijeme(xmax, 60)
        if xmax < self.donjaGranica:
            xmax = self.donjaGranica
        if xmax > self.gornjaGranica:
            xmax = self.gornjaGranica
        
        xmin = pd.to_datetime(xmin)
        xmax = pd.to_datetime(xmax)
        
        opis = 'Odabrano vrijeme: \nOD: '+str(xmin)+'\nDO: '+ str(xmax)
        flag = FlagDijalog(message = opis)
        if flag.odgovor == 'valja':
            arg = [xmin, xmax, 1]
            print('good flag change: ', arg)
            self.emit(QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), arg)
        elif flag.odgovor=='nevalja':
            arg = [xmin, xmax, -1]
            print('bad flag change: ', arg)
            self.emit(QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), arg)
        else:
            pass
###############################################################################
    def crtaj(self, data):
        """
        crtanje minutnih podataka
        """
        if len(data) != 0:
            self.dataTest = True
            self.data = data
            self.axes.clear()
            
            self.donjaGranica = data.index.min()
            self.gornjaGranica = data.index.max()
            
            title='Minutni podaci od: '+str(self.donjaGranica)+' do: '+str(self.gornjaGranica)
            self.axes.set_title(title,fontsize=4)
            
            #svi
            vrijeme = list(data.index)
            konc = list(data[u'koncentracija'])
            
            #flag veci od nule
            df1 = data[data[u'flag'] >= 0]
            vrijeme1 = list(df1.index)
            konc1 = list(df1[u'koncentracija'])
            
            #flag manji od nule
            df2 = data[data[u'flag'] < 0]
            vrijeme2 = list(df2.index)
            konc2 = list(df2.index)
            
            #plot crne linije
            self.axes.plot(vrijeme, konc,
                           color = 'black', 
                           zorder = 1)
            
            #scatter plot podataka, vrijednost flaga pozitivna
            self.axes.scatter(vrijeme1, konc1,
                              marker = 'o', 
                              color = 'green', 
                              zorder = 2, 
                              picker = 2)
            
            #scatter plot podataka, vrijednost flaga negativna
            self.axes.scatter(vrijeme2, konc2,
                      marker = 'o', 
                      color = 'red', 
                      zorder = 2, 
                      picker = 2)
                      
            #granice crtanog podrucja
            #x-os
            minxlim = self.donjaGranica - timedelta(minutes=5)
            maxxlim = self.gornjaGranica + timedelta(minutes=5)
            minxlim = pd.to_datetime(minxlim)
            maxxlim = pd.to_datetime(maxxlim)
            self.axes.set_xlim(minxlim, maxxlim)
            
            #y-os
            raspon = konc
            raspon.sort()
            minylim = raspon[0] #najmanja crijednost
            maxylim = raspon[len(raspon)-1] #najveca vrijednost
            pad = (minylim + maxylim)/5 #padding da nisu na rubu
            minylim = minylim - pad
            maxylim = maxylim + pad
            self.axes.set_ylim(minylim, maxylim)
            
            #format x kooridinate
            xLabels = self.axes.get_xticklabels()
            for label in xLabels:
                label.set_rotation(20)
                label.set_fontsize(4)
            
            #format y kooridinate
            yLabels=self.axes.get_yticklabels()
            for label in yLabels:
                label.set_fontsize(4)
                
            self.fig.tight_layout()
            self.draw()
        else:
            self.axes.clear()
            self.dataTest = False
            #napisi poruku na grafu da nema podataka
            self.axes.text(0.5, 0.5, 
                           'Nema izmjerenih podataka.', 
                           horizontalalignment = 'center', 
                           verticalalignment ='center', 
                           size = 'medium')
            self.fig.tight_layout()
            self.draw()
###############################################################################
################################################################################
#class GrafMinutniPodaci(MPLCanvas):
#    """
#    Graf za crtanje minutnih podataka.
#    Ulaz:
#        data je lista pandas datafrejmova, satni slice koncetracije
#        [0] cijeli -> cijeli dataframe (sluzi za plot linije)
#        [1] pozitivanFlag ->dio dataframe gdje je flag >=0 (za scatter plot)
#        [2] negativanFlag ->dio dataframe gdje je flag <0 (za scatter plot)
#    SIGNALI:
#    flagTockaMinutni(PyQt_PyObject)
#        -izbor jedne tocke kojoj treba promjeniti flag - desni klik
#        -emitira listu - [vrijeme(timestamp),novi flag, string 'flagTockaMinutni']
#    flagSpanMinutni(PyQt_PyObject)
#        -izbor spana, lijevi klik & drag. na klik granice su identicne
#        -emitira listu - [vrijeme min, vrijeme max, novi flag, string 'flagSpanMinutni']
#        -min i max granice su isti broj na jedan ljevi klik...problem?
#    """
#    def __init__(self,*args,**kwargs):
#        MPLCanvas.__init__(self,*args,**kwargs)
#        self.donjaGranica=None
#        self.gornjaGranica=None
#        self.veze()
#    
#    def veze(self):
#        #desni klik za izbor jedne točke
#        self.cidpick=self.mpl_connect('pick_event',self.onpick)
#        #span selector
#        self.span=SpanSelector(self.axes,
#                               self.minutni_span_flag,
#                               'horizontal',
#                               useblit=True,
#                               rectprops=dict(alpha=0.5,facecolor='tomato')
#                               )
#    
#    def minutni_span_flag(self,xmin,xmax):
#        #test da li je graf nacrtan
#        if ((self.donjaGranica!=None) and (self.gornjaGranica!=None)):
#            xmin=round(xmin)
#            xmax=round(xmax)
#            puniSatMin=False
#            puniSatMax=False
#        
#            if xmin==60:
#                puniSatMin=True
#                xmin='00'
#            else:
#                xmin=str(xmin)
#            
#            if xmax==60:
#                puniSatMax=True
#                xmax='00'
#            else:
#                xmax=str(xmax)
#        
#            #sastavi timestamp
#            godina=str(self.donjaGranica.year)
#            mjesec=str(self.donjaGranica.month)
#            dan=str(self.donjaGranica.day)
#            sat=str(self.donjaGranica.hour)
#            timeMin=godina+'-'+mjesec+'-'+dan+' '+sat+':'+xmin+':'+'00'
#            timeMax=godina+'-'+mjesec+'-'+dan+' '+sat+':'+xmax+':'+'00'
#            minOznaka=pd.to_datetime(timeMin)
#            maxOznaka=pd.to_datetime(timeMax)
#        
#            if puniSatMin:
#                minOznaka=minOznaka+timedelta(hours=1)
#            
#            if puniSatMax:
#                maxOznaka=maxOznaka+timedelta(hours=1)
#            
#            opis='Odabrani interval od '+str(minOznaka)+' do '+str(maxOznaka)
#            flag=FlagDijalog(message=opis)
#            if flag.odgovor=='valja':
#                #provjeri da li je min i max ista tocka
#                if minOznaka==maxOznaka:
#                    #arg=[minOznaka,1]
#                    arg=[minOznaka, 1, 'flagSpanMinutni']
#                    self.emit(QtCore.SIGNAL('flagSpanMinutni(PyQt_PyObject)'),arg)
#                else:
#                    #arg=[minOznaka,maxOznaka,1]
#                    arg = [minOznaka, maxOznaka, 1, 'flagSpanMinutni']
#                    self.emit(QtCore.SIGNAL('flagSpanMinutni(PyQt_PyObject)'),arg)
#            elif flag.odgovor=='nevalja':
#                #provjeri da li je min i max ista tocka
#                if minOznaka==maxOznaka:
#                    #arg=[minOznaka,-1]
#                    arg=[minOznaka, -1, 'flagSpanMinutni']
#                    self.emit(QtCore.SIGNAL('flagSpanMinutni(PyQt_PyObject)'),arg)
#                else:
#                    #arg=[minOznaka,maxOznaka,-1]
#                    arg=[minOznaka,maxOznaka, -1, 'flagSpanMinutni']
#                    self.emit(QtCore.SIGNAL('flagSpanMinutni(PyQt_PyObject)'),arg)
#            else:
#                pass
#            
#            
#        else:
#            message='Unable to select data, draw some first'
#            self.emit(QtCore.SIGNAL('set_status_bar(PyQt_PyObject)'),message)
#        
#    def onpick(self,event):
#        """
#        Picker na minutnom grafu
#        """
#        #start annotation part
#        self.tooltipTekst='time: %s\nkoncentracija: %0.2f\nflag: %0.2f\nstatus: %0.2f'
#        self.annX=0
#        self.annY=0
#        self.annotation=self.axes.annotate(
#            self.tooltipTekst,
#            xy=(self.annX,self.annY),
#            xytext=(0.1,0.6),
#            textcoords='axes fraction',
#            ha='left',
#            va='bottom',
#            fontsize=5,
#            bbox=dict(boxstyle='square',fc='cyan',alpha=0.7,zorder=10),
#            arrowprops=dict(arrowstyle='->',connectionstyle='arc3,rad=0',alpha=0.6,zorder=10)
#            )
#        self.annotation.set_visible(False)
#        #kraj annotation part
#        
#        puniSat=False
#        #overlap pickera?
#        izbor=event.mouseevent.xdata
#        if type(izbor)==list:
#            izbor=izbor[0]
#            
#        izbor=round(izbor)
#        if izbor==60:
#            puniSat=True
#            izbor='00'
#        else:
#            izbor=str(izbor)
#        #sastavi timestamp
#        godina=str(self.donjaGranica.year)
#        mjesec=str(self.donjaGranica.month)
#        dan=str(self.donjaGranica.day)
#        sat=str(self.donjaGranica.hour)
#        time=godina+'-'+mjesec+'-'+dan+' '+sat+':'+izbor+':'+'00'
#        timeOznaka=pd.to_datetime(time)
#        if puniSat:
#            timeOznaka=timeOznaka+timedelta(hours=1)
#        
#        #desni klik - promjena flaga jedne tocke
#        if event.mouseevent.button==3:
#            opis='Odabrano vrijeme: '+str(timeOznaka)
#            flag=FlagDijalog(message=opis)
#            if flag.odgovor=='valja':
#                #arg=[timeOznaka,1]
#                arg=[timeOznaka, 1, 'flagTockaMinutni']
#                self.emit(QtCore.SIGNAL('flagTockaMinutni(PyQt_PyObject)'),arg)
#            elif flag.odgovor=='nevalja':
#                #arg=[timeOznaka,-1]
#                arg=[timeOznaka, -1, 'flagTockaMinutni']
#                self.emit(QtCore.SIGNAL('flagTockaMinutni(PyQt_PyObject)'),arg)
#            else:
#                pass
#                
#        #middle klik misem, annotation tocke
#        if event.mouseevent.button==2:
#            if self.zadnjiAnnotation==timeOznaka:
#                self.annotation.remove()
#                self.zadnjiAnnotation=None
#                self.draw()
#            else:
#                self.annX=event.mouseevent.xdata
#                self.annY=event.mouseevent.ydata
#                self.annotation.xy=self.annX,self.annY
#                #tekst annotationa
#                izbor=str(timeOznaka)
#                koncentracija=self.dataframe.loc[izbor,u'koncentracija']
#                status=self.dataframe.loc[izbor,u'status']
#                flag=self.dataframe.loc[izbor,u'flag']
#                self.annotation.set_text(self.tooltipTekst % (izbor,koncentracija,flag,status))
#                self.annotation.set_visible(True)
#                self.zadnjiAnnotation=timeOznaka
#                self.draw()
#                self.annotation.remove()
#
#    def crtaj(self,data):
#        """
#        x os plota će biti minute timestampa od 1 do 60
#        """
#        self.zadnjiAnnotation=None
#        self.dataframe=data[0]
#        #zapamti podatke o timestampu za datum i sat
#        self.donjaGranica=data[0].index.min()
#        self.gornjaGranica=data[0].index.max()
#        #priprema za crtanje
#        self.axes.clear()
#        title='Minutni podaci od: '+str(self.donjaGranica)+' do: '+str(self.gornjaGranica)
#        self.axes.set_title(title,fontsize=4)
#        linija=data[0].loc[:,u'koncentracija']
#        tockeOk=data[1].loc[:,u'koncentracija']
#        tockeNo=data[2].loc[:,u'koncentracija']
#        xMinute=[]
#        xFlagOk=[]
#        xFlagNo=[]
#        
#        if len(linija)!=0:
#            for i in linija.index:
#                if i.minute!=0:
#                    xMinute.append(i.minute)
#                else:
#                    xMinute.append(60)
#        
#        if len(tockeOk)!=0:
#            for i in tockeOk.index:
#                if i.minute!=0:
#                    xFlagOk.append(i.minute)
#                else:
#                    xFlagOk.append(60)
#        
#        if len(tockeNo)!=0:
#            for i in tockeNo.index:
#                if i.minute!=0:
#                    xFlagNo.append(i.minute)
#                else:
#                    xFlagNo.append(60)
#        
#        if len(xMinute)==len(linija.values):
#            self.axes.plot(xMinute,linija.values,
#                           color='black')
#        
#        if len(xFlagOk)==len(tockeOk.values):
#            self.axes.scatter(xFlagOk,tockeOk.values,
#                              color='green',
#                              marker='o',
#                              picker=2,
#                              alpha=0.4)
#        
#        if len(xFlagNo)==len(tockeNo.values):
#            self.axes.scatter(xFlagNo,tockeNo.values,
#                              color='red',
#                              marker='o',
#                              picker=2,
#                              alpha=0.4)
#        
#        xLabels=self.axes.get_xticklabels()
#        for label in xLabels:
#            label.set_fontsize(4)
#            
#        yLabels=self.axes.get_yticklabels()
#        for label in yLabels:
#            label.set_fontsize(4)
#        #pokusaj automatskog proavnavanja
#        self.axes.set_xlim(1,60)
#        self.fig.tight_layout()
#        self.draw()
################################################################################
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
       
        
        """
        Testni podaci, dictionary pandas datafrejmova koji je rezultat agregatora.
        """
        
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
        agregirani = agregator.agregiraj_kanal(frejm)
        minutedata = frejm.loc['2014-06-04 15:01:00':'2014-06-04 16:00:00',:]
        
        #naredba za plot
#        canvasSatni.crtaj(agregirani)
#        canvasMinutni.crtaj(minutedata)
        
        canvasSatni.crtaj(pd.DataFrame())
        canvasMinutni.crtaj(pd.DataFrame())

            
if __name__=='__main__':
    aplikacija=QtGui.QApplication(sys.argv)
    app=ApplicationMain()
    app.show()
    sys.exit(aplikacija.exec_())