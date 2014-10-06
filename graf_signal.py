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

def format1(x,y):
    return 'izlaz: \nx:'+str(x)+'\ny:'+str(y)

###############################################################################
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
        xpoint = datetime.datetime(xpoint.year, 
                                   xpoint.month, 
                                   xpoint.day, 
                                   xpoint.hour, 
                                   xpoint.minute, 
                                   xpoint.second)
        xpoint = zaokruzi_vrijeme(xpoint, 3600)   #round na najblizi sat
                
        if event.mouseevent.button == 1:
            #left click
            xtime = pd.to_datetime(xpoint)
            arg = xtime
            print('ljevi klik, arg: ', arg) #samo test izlaznog podatka
            self.emit(QtCore.SIGNAL('gui_crtaj_minutni_graf(PyQt_PyObject)'), 
                      arg)
        
        #TODO!
        #annotations
        if event.mouseevent.button == 2:
            x = pd.to_datetime(xpoint)
            print('najblizi x: ', x)
            print(event.mouseevent)
            
            
        
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
        
        self.zadnjiAnnotation = None
        self.testAnnotation = False
        
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
        xpoint = datetime.datetime(xpoint.year, 
                                   xpoint.month, 
                                   xpoint.day, 
                                   xpoint.hour, 
                                   xpoint.minute, 
                                   xpoint.second)
        xpoint = zaokruzi_vrijeme(xpoint, 60)   #round na najblizu minutu
        xpoint = pd.to_datetime(xpoint)
        
        if xpoint >= self.data.index.max():
            xpoint = self.data.index.max()
        if xpoint <= self.data.index.min():
            xpoint = self.data.index.min()
        
        #annotations
        if event.mouseevent.button == 2:
            #odabrana tocka
            xtime = xpoint
            if xtime != self.zadnjiAnnotation:
                if self.testAnnotation == True:
                    self.annotation.remove()
                    self.draw()
                    
                self.zadnjiAnnotation = xtime
                self.testAnnotation = True
                yconc = self.data.loc[xtime, u'koncentracija']
                ystat = self.data.loc[xtime, u'status']
                yflag = self.data.loc[xtime, u'flag']
            
                tekst = 'Vrijeme: '+str(xtime.time())+'\nKonc.: '+str(yconc)+'\nStatus: '+str(ystat)+'\nFlag: '+str(yflag)
            
                #grubo odredjena sredina grafa za ofset anotationa
                size = self.frameSize()
                x, y = size.width(), size.height()
                x = x//2
                y= y//2
                #grube koorininate kliknute tocke 
                clickedx = event.mouseevent.x
                clickedy = event.mouseevent.y
            
                if clickedx >= x:
                    clickedx = -60
                    if clickedy >= y:
                        clickedy = -30
                    else:
                        clickedy = 30
                else:
                    clickedx = 30
                    if clickedy >= y:
                        clickedy = -30
                    else:
                        clickedy = 30
                self.annotation = self.axes.annotate(
                    tekst, 
                    xy = (xtime, yconc), 
                    xytext = (clickedx, clickedy), 
                    textcoords = 'offset points', 
                    ha = 'left', 
                    va = 'center', 
                    fontsize = 5, 
                    bbox = dict(boxstyle = 'square', fc = 'cyan', alpha = 0.7, zorder = 4), 
                    arrowprops = dict(arrowstyle = '->', alpha = 0.7, zorder = 4))
                self.draw()
            else:
                self.annotation.remove()
                self.zadnjiAnnotation = None
                self.testAnnotation = False
                self.draw()
                
        if event.mouseevent.button == 3:
            #right click
            t = xpoint
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
            konc2 = list(df2[u'koncentracija'])
            
            #plot crne linije
            self.axes.plot(vrijeme, konc,
                           color = 'black', 
                           zorder = 1)
            
            #scatter plot podataka, vrijednost flaga pozitivna
            if len(df1 > 0):
                self.axes.scatter(vrijeme1, konc1,
                                  marker = 'o', 
                                  color = 'green', 
                                  zorder = 2, 
                                  picker = 2)
                
            #scatter plot podataka, vrijednost flaga negativna
            if len(df2 > 0):
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
            yLabels = self.axes.get_yticklabels()
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
        
        self.canvasSatni=GrafSatniSrednjaci(self.widget1,width=6,height=5,dpi=150)
        self.canvasMinutni=GrafMinutniPodaci(self.widget2,width=6,height=5,dpi=150)
        
        mainLayout=QtGui.QVBoxLayout(self.mainWidget)
        mainLayout.addWidget(self.canvasSatni)
        mainLayout.addWidget(self.canvasMinutni)
        
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
        #dio sa negativnim flagovima...
        minutedata.loc['2014-06-04 15:01:00':'2014-06-04 15:30:00',u'flag'] = -1
        
        #naredba za plot
        self.agregirani = agregirani
        self.minutni = minutedata
        
        self.canvasSatni.crtaj(agregirani)
        self.canvasMinutni.crtaj(minutedata)
        
        self.connect(self.canvasMinutni, 
                     QtCore.SIGNAL('gui_promjena_flaga(PyQt_PyObject)'), 
                     self.flag_update)
        
    def flag_update(self, data):
        tmin = data[0]
        tmax = data[1]
        nflag = data[2]
        #BROKEN... RADI NA MINUTNOM--- 
        self.minutni.loc[tmin:tmax,u'flag'] = nflag
        self.canvasMinutni.crtaj(self.minutni)
        
        
            
if __name__=='__main__':
    aplikacija=QtGui.QApplication(sys.argv)
    app=ApplicationMain()
    app.show()
    sys.exit(aplikacija.exec_())