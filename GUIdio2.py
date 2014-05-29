# -*- coding: utf-8 -*-
"""
Created on Wed Apr 16 10:17:49 2014

@author: velimir
"""

# import main libraries
import sys
import pandas as pd
import numpy as np

# from import statements
from PyQt4 import QtGui, QtCore
from matplotlib.backends.backend_qt4agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import \
    NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
from datetime import datetime, timedelta
from matplotlib.widgets import SpanSelector

# import from personal modules
import agregator
import auto_validacija
import citac
import uredjaj
import grafovi

class GlavniProzor(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle('Validacija podataka, pokusaj 3')
        self.resize(700, 400)
        self.sizePolicy = QtGui.QSizePolicy(
                QtGui.QSizePolicy.Expanding,
                QtGui.QSizePolicy.Expanding)
        self.setMinimumSize(QtCore.QSize(300, 300))
        self.setMouseTracking(True)
        
        self.create_status_bar()        
        self.create_menu()
        tBar = self.create_tool_bar()
        self.addToolBar(tBar)
        
        # defintion of some members
        self.trenutniKanal = None
        self.spanToggleStatus = False
        self.aktivniNizNizova = None
        self.zadnjiSatniSlice = None  # pamti koji je zadnji minutni graf crtan
        
        
                                
        """define main widget as container for graphics tables etc...
        set layout
        """
        self.mainWidget = QtGui.QWidget()
        """
        Layout i definicija canvas za grafove ->graphLayout
        """
        self.satniSrednjaci = QtGui.QWidget()
        self.satniSrednjaci.setSizePolicy(QtGui.QSizePolicy.Expanding,
                                    QtGui.QSizePolicy.Expanding)                
        self.satniSrednjaci.setWindowTitle('Satno agregirani podaci')
        self.fig1 = Figure()
        self.canvas1 = FigureCanvas(self.fig1)
        self.canvas1.setParent(self.satniSrednjaci)
        self.axes1 = self.fig1.add_subplot(111)
        self.mplToolbar1 = NavigationToolbar(self.canvas1, self.satniSrednjaci)
         
        self.satniPodaci = QtGui.QWidget()
        self.satniPodaci.setSizePolicy(QtGui.QSizePolicy.Expanding,
                                    QtGui.QSizePolicy.Expanding)       
        self.satniPodaci.setWindowTitle('Podaci u odabranom intervalu')
        self.fig2 = Figure()
        self.canvas2 = FigureCanvas(self.fig2)
        self.canvas2.setParent(self.satniPodaci)
        self.axes2 = self.fig2.add_subplot(111)
        self.mplToolbar2 = NavigationToolbar(self.canvas2, self.satniPodaci)
        
        # span selector toggle
        if self.spanToggleStatus == True:
            self.toggle_span()
        else:
            self.canvas1.mpl_connect('pick_event', self.onpick)
                
        
        self.combo1 = QtGui.QComboBox()
        self.connect(self.combo1,
                     QtCore.SIGNAL('currentIndexChanged(int)'),
                     self.update_trenutni_kanal)
        
        self.grafovi = grafovi.Grafovi(parent=self)
        graphLayout = QtGui.QVBoxLayout()
#         g1 = QtGui.QVBoxLayout()
#         g1.addWidget(self.satniSrednjaci)
#         g1.addWidget(self.mplToolbar1)               
#         g2 = QtGui.QVBoxLayout()
#         g2.addWidget(self.satniPodaci)
#        g2.addWidget(self.mplToolbar2)
        graphLayout.addWidget(self.combo1)
#        graphLayout.addLayout(g1)
#        graphLayout.addLayout(g2)
        graphLayout.addWidget(self.grafovi)
        
        
        """
        glavni layout
        """
        final = QtGui.QVBoxLayout(self.mainWidget)
        final.addLayout(graphLayout)
        
        self.setCentralWidget(self.mainWidget)
    ###########################################################################
    def update_trenutni_kanal(self):
        self.trenutniKanal = self.combo1.currentText()
        self.aktivniNizNizova = self.nizNizova[str(self.trenutniKanal)]
        # clear both graphs, draw new        
        self.axes2.clear()
        self.canvas2.draw()
        self.draw_request_satni()
        
    ###########################################################################
    def create_action(self,
                      text,
                      slot=None,
                      shortcut=None,
                      icon=None,
                      tooltip=None,
                      checkable=False,
                      signal="triggered()"
                      ):
        """
        Creates a PyQt4 action, and customizes it (shortcut, signal-slot...)
        """
        action = QtGui.QAction(text, self)
        
        if icon is not None:
            action.setIcon(QtGui.QIcon(icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tooltip is not None:
            action.setToolTip(tooltip)
            action.setStatusTip(tooltip)
        if slot is not None:
            self.connect(action, QtCore.SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action
    ###########################################################################
    def add_actions_to(self, target, actions):
        """
        Short function to add actions to target menu. It can add multiple
        actions, and add separators between them if argument is None.
        """
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)
    ###########################################################################
    def create_status_bar(self):
        self.statusBar().showMessage('Ready for work')
    ###########################################################################
    def create_menu(self):
        """
        By using create_action i add_actions_to methods, create a menu
        """
        self.fileMenu = self.menuBar().addMenu("&File")
        self.graphMenu = self.menuBar().addMenu("&Graph")
        
        self.action_exit = self.create_action('&Exit',
                                            slot=self.close,
                                            shortcut='Ctrl+Q',
                                            tooltip='Exit the application')
        self.action_load = self.create_action('&Load',
                                            slot=self.read_csv,
                                            shortcut='Alt+L',
                                            tooltip='Load file')
        self.action_toggle_selector = self.create_action('&Toggle span selector',
                                                       slot=self.toggle_span,
                                                       tooltip='turn on/off span selector')
                                            
        fileMenuList = [self.action_load,
                      None,
                      self.action_exit]
        graphMenuList = [self.action_toggle_selector]
        
        self.add_actions_to(self.fileMenu, fileMenuList)
        self.add_actions_to(self.graphMenu, graphMenuList)
    ###########################################################################
    def pass_function(self):
        """
        some crap to connect to to test if connection works, also placeholder
        """
        print('something something something else')
    ###########################################################################
    def create_tool_bar(self):
        """
        By using create_action i add_actions_to methods, create a tool bar
        """
        toolBar = self.addToolBar('Main toolbar')
        
        toolBarList = [self.action_load,
                     None,
                     self.action_toggle_selector,
                     None,
                     self.action_exit]
             
        self.add_actions_to(toolBar, toolBarList)
        return toolBar    
    ###########################################################################
    # redefine close to ask for confirmation
    def closeEvent(self, event):
        reply = QtGui.QMessageBox.question(self,
                                         'Confirm exit',
                                         'Are you sure you want to quit?',
                                         QtGui.QMessageBox.Yes,
                                         QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
    ###########################################################################
    """
    Čitanje podataka.
    Unos uređaja, priprema za autovalidaciju,priprema za inicijalno agregiranje
    """
    def read_csv(self):
        
        listaUredjaja = [uredjaj.M100E(), uredjaj.M100C()]
        listaStart = [datetime(2000, 1, 1), datetime(2014, 2, 24, 0, 10)]
        listaKraj = [datetime(2014, 2, 24, 0, 10), datetime(2015, 1, 1)]        
        autoValidator = self.autovalidator_setup(listaUredjaja,
                                               listaStart,
                                               listaKraj)
        
        # read csv
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open CSV file', '')

        reader = citac.WlReader()
        self.data = reader.citaj(str(filename))
        self.agdata = {}
        self.nizNizova = {}
        # autovalidacija i agregiranje
        for i in list(self.data):
            # agregator mora biti unutar petlje ili ga treba inicijalizirati za 
            # svaku komponentu unutar petlje jer nacelno nije isti validator za 
            # svaku komponentu.
            # Ako je unutar petlje onda ne treba biti member varijable, a ako postoji
            # dobar razlog da bude member (a postoji zbog ragregacije) onda mora biti 
            # mapa (komponenta, agregator)
            self.ag = agregator.Agregator(listaUredjaja)  # izbaciti izvan petlje?
            autoValidator.validiraj(self.data[i])                
            self.ag.setDataFrame(self.data[i])
            self.agdata[i] = self.ag.agregirajNiz()
            self.nizNizova[i] = self.ag.nizNiz()
            
        # tu bi trabao opaliti event za draw_request_satni
        self.combo1.addItems(list(self.data))
        self.update_trenutni_kanal()
        self.draw_request_satni()
            
        """
        self.data - originalni podatci
        self.agdata - agregirani satni srednjaci
        self.nizNizova - lista satnih sliceova koncentracije
        """
    ###########################################################################
    def autovalidator_setup(self, uredjaj, start, end):
        """
        inicijalizacija autovalidatora, argumenti su:
        lista uredjaja, lista pocetnih vremena, lista krajnjih vremena.
        """
        autoValidator = auto_validacija.AutoValidacija()
        for i in list(range(len(uredjaj))):
            uredjaj[i].pocetak = start[i]
            uredjaj[i].kraj = end[i]
            autoValidator.dodaj_uredjaj(uredjaj[i])
            
        return autoValidator
        
    ###########################################################################
    def draw_request_satni(self):
        """
        boxplot satnih prosjeka
        """
        
        # umjesot ovoga bi bilo bolje da je kanal member i to trenutniKanal koji
        # se update-a na on init i on change combo1
        
        # init je nakon read na neki random, combo1 spojen
        
        kanal = str(self.trenutniKanal)
        self.axes1.clear()
        
        temp = self.nizNizova[kanal]
        # test
        self.axes1.boxplot(temp)
        self.axes1.plot(self.agdata[kanal]['avg'], picker=5)
        self.axes1.plot(self.agdata[kanal]['q05'], picker=5)
        self.axes1.plot(self.agdata[kanal]['q95'], picker=5)
        self.axes1.set_title('Boxplot satnih podataka s q05.q95 i average')
        self.canvas1.draw()
        
    ###########################################################################
    def draw_request_minutni(self, timeslice):
        """
        plot satnog slicea, minutne vrijednosti - neki color code kasnije
        temp bi trebao biti plot koncentracije slicea
        temp1 bi trebao biti scatter plot koncentracije ali flag > 0
        temp2 bi trebao biti scatter plot koncentracije ali flag < 0
        """
  
        kanal = str(self.trenutniKanal)
        self.axes2.clear()
        
        minIndex = self.aktivniNizNizova[timeslice].index.min()
        maxIndex = self.aktivniNizNizova[timeslice].index.max()
        naslov = 'slice od ' + str(minIndex) + ' do ' + str(maxIndex)

        dfComplete = self.data[kanal].loc[minIndex:maxIndex]
        temp = dfComplete.loc[:, u'koncentracija']
        temp1 = dfComplete[dfComplete.loc[:, u'flag'] >= 0]
        temp2 = dfComplete[dfComplete.loc[:, u'flag'] < 0]

        """
        Srediti x os kao integer minute od 1 do 60, timestamp ne valja.
        Problem moze nastati s rupama u podatcima, ali indeksiram graf
        po minutnim vrijednostima, pa ne bi trebao biti problem.
        """
        minuteTemp = []
        minuteTemp1 = []
        minuteTemp2 = []
        for i in temp.index:
            if i.minute != 0:
                minuteTemp.append(i.minute)
            else:
                minuteTemp.append(60)
        
        for i in temp1.index:
            if i.minute != 0:
                minuteTemp1.append(i.minute)
            else:
                minuteTemp1.append(60)
                
        for i in temp2.index:
            if i.minute != 0:
                minuteTemp2.append(i.minute)
            else:
                minuteTemp2.append(60)

        self.axes2.plot(minuteTemp, temp)
        if len(temp1) != 0:
            self.axes2.scatter(
                minuteTemp1,
                temp1.loc[:, u'koncentracija'],
                marker='o',
                color='g')
        if len(temp2) != 0:
            self.axes2.scatter(
                minuteTemp2,
                temp2.loc[:, u'koncentracija'],
                marker='s',
                color='r')
        self.axes2.set_title(naslov)
        self.canvas2.draw()
    ###########################################################################
    def on_select_satni(self, xmin, xmax):
        """
        uzima veći index, pretvara ga u integer zaokruživanjem, poziva
        draw_request_minutni
        """
        trenutak = int(np.round(max([xmin, xmax]))) - 1
        self.zadnjiSatniSlice = trenutak
        self.draw_request_minutni(trenutak)
        
    # test1   
    def onpick(self, event):
        thisline = event.artist
        xdata = thisline.get_xdata()
        ydata = thisline.get_ydata()
        ind = event.ind
        print('onpick points, izabrani interval:', xdata[ind], ydata[ind])
        trenutak = int(xdata[ind]) - 1
        self.zadnjiSatniSlice = trenutak
        self.draw_request_minutni(trenutak)
        
    ###########################################################################
    def toggle_span(self):
        self.spanToggleStatus = not self.spanToggleStatus
        if self.spanToggleStatus == True:
            self.span1 = SpanSelector(self.axes1,
                                    self.on_select_satni,
                                    'horizontal',
                                    useblit=True,
                                    rectprops=dict(alpha=0.5, facecolor='red')
                                    )
            self.span2 = SpanSelector(self.axes2,
                               self.flip_flag,
                               'horizontal',
                               useblit=True,
                               rectprops=dict(alpha=0.5, facecolor='red')
                               )
        else:
            self.span1 = None
            self.span2 = None
    ###########################################################################
    def flip_flag(self, xmin, xmax):
        """
        flip flag
        """
        kanal = str(self.trenutniKanal)
        
        print('sirovi podatak s grafa, min ', xmin)
        print('sirovi podatak s grafa, max ', xmax)
        
        """
        -konverzija u integer (vrijednost minute)
        -provjera da rubne vrijednosti ne iskaču izvan granica jednog sata
        """        
        xmin = int(xmin)
        if xmin < 1:
            xmin = 1
        xmax = int(xmax)
        if xmax > 60:
            xmax = 60
        
        """
        -konverzija minutih podataka u time index dataframea, problem je
        sa punim satom... nadam se da timedelta radi inače imamo problem s
        prebacivanjem dana/mjeseca/godine
        """
        # slice info - samo da dobijemo podatak o datumu i satu na trenutnom
        # minutnom grafu
        firstIndex = self.aktivniNizNizova[self.zadnjiSatniSlice].index[0]
        godina = str(firstIndex.year)
        mjesec = str(firstIndex.month)
        dan = str(firstIndex.day)
        sat = str(firstIndex.hour)
        minuta = str(firstIndex.minute)
        sekunda = '00'
               
        if xmin == 60:
            tmin = godina + '-' + mjesec + '-' + dan + ' ' + sat + ':' + '00' + ':' + sekunda
            tmin = tmin + timedelta(hours=1)
        else:
            tmin = godina + '-' + mjesec + '-' + dan + ' ' + sat + ':' + str(xmin) + ':' + sekunda
        

        if xmax == 60:
            tmax = godina + '-' + mjesec + '-' + dan + ' ' + sat + ':' + '00' + ':' + sekunda
            tmax = tmax + timedelta(hours=1)
        else:
            tmax = godina + '-' + mjesec + '-' + dan + ' ' + sat + ':' + str(xmax) + ':' + sekunda

        
        tmin = pd.to_datetime(tmin)
        tmax = pd.to_datetime(tmax)
        
        # raspon za flip flag
        print('min: ', tmin)
        print('max: ', tmax)     
              
        # flip flag mnozenjem s -1, u slucaju nule, flag stavi na -1
        raspon = pd.date_range(tmin, tmax, freq='Min')
        for index in raspon:
            if self.data[kanal].loc[index, u'flag'] == 0:
                self.data[kanal].loc[index, u'flag'] = (-1)
            else:
                self.data[kanal].loc[index, u'flag'] = (-1) * self.data[kanal].loc[index, u'flag']
            
        # reagregacija.
        self.ag.setDataFrame(self.data[kanal])
        self.agdata[kanal] = self.ag.agregirajNiz()
        self.nizNizova[kanal] = self.ag.nizNiz()
        self.aktivniNizNizova = self.nizNizova[kanal]
        self.trenutniKanal = kanal
        
        # update grafova
        self.draw_request_satni()
        self.draw_request_minutni(self.zadnjiSatniSlice)
        
    ###########################################################################

if __name__ == '__main__':
    aplikacija = QtGui.QApplication(sys.argv)
    glavni = GlavniProzor()
    glavni.show()
    sys.exit(aplikacija.exec_())
