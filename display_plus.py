# -*- coding: utf-8 -*-
"""
Created on Mon Oct 20 10:45:18 2014

@author: User
"""

import sys
from PyQt4 import QtCore, QtGui, uic

import dokument
import kontroler
import graf_signal_plus
import weblogger_izbornik

###############################################################################
###############################################################################
base, form = uic.loadUiType('display_plus.ui')
class Display(base, form):
    def __init__(self, parent = None):
        super(base, self).__init__(parent)
        self.setupUi(self)
        #load defaults #TODO! mora se srediti bolje, xml ili nesto u tom stilu
        self.load_defaults(None)
        """
        memberi
        """        
        self.wlReaderLoaded = False
        
        """inicijalizacija kontrolnih / display objekata na gui"""
        #inicjalizacija webLoggerIzbornika
        self.webLoggerIzbornik = weblogger_izbornik.WebloggerIzbornik()
        #inicijalizacija satnog canvasa
        self.satniCanvas = graf_signal_plus.SatniGraf(parent = None, defaulti = self.__defaulti, frejmovi = None)
        #inicijalizacija minutnog canvasa
        self.minutniCanvas = graf_signal_plus.MinutniGraf(parent = None, defaulti = self.__defaulti, frejmovi = None)
        
        self.dockWidget_satni.setWidget(self.satniCanvas)
        self.dockWidget_minutni.setWidget(self.minutniCanvas)

        """povezivanje akcija"""
        self.setup_akcije()
        
        """postavljanje dokumenta i kontrolera"""
        #dokument
        self.doc = dokument.Dokument()
        #kontroler
        self.kontrola = kontroler.Kontrola(gui = self, dokument = self.doc)

###############################################################################
    def read_file_dijalog(self):
        tipovi = ("weblogger", "PLACEHOLDER1", "PLACEHOLDER2")
        izbor, ok = QtGui.QInputDialog.getItem(self, 
            "Izbor citaca:", 
            "Citac:", 
            tipovi, 
            0, 
            False)
        if ok and izbor:
            return izbor
###############################################################################
    def gui_action_read_file(self):
        """
        Akcija za read file.
        """
        izbor = self.read_file_dijalog()        
        if (izbor == 'weblogger') and (not self.wlReaderLoaded):
            self.wlReaderLoaded = True
            self.dockWidget_kontrola.setWidget(self.webLoggerIzbornik)
        else:
            self.wlReaderLoaded = False
            self.dockWidget_kontrola.setWidget(QtGui.QWidget())
###############################################################################
    def load_defaults(self, defaulti):
        #inicijalno postavljanje opcenitih membera? Grafovi, useri....
        #NIJE IMPLEMENTIRANO DO KRAJA! neki xml file? pickled objekt?
        if defaulti == None:
            validanOK = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'marker':'p', 'color':(0,255,0), 'alpha':1, 'zorder':20}
            validanNOK = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'marker':'p', 'color':(255,0,0), 'alpha':1, 'zorder':20}
            nevalidanOK = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'marker':'o', 'color':(0,255,0), 'alpha':1, 'zorder':20}
            nevalidanNOK = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'marker':'o', 'color':(255,0,0), 'alpha':1, 'zorder':20}
            glavnikanal1 = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'stupac1':'min', 'marker':'+', 'line':'None', 'color':(0,0,0), 'alpha':0.9, 'zorder':8}
            glavnikanal2 = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'stupac1':'max', 'marker':'+', 'line':'None', 'color':(0,0,0), 'alpha':0.9, 'zorder':9}
            glavnikanal3 = {'crtaj':True, 'tip':'plot', 'kanal':None, 'stupac1':'median', 'marker':'None', 'line':'-', 'color':(45,86,90), 'alpha':0.9, 'zorder':10}
            glavnikanal4 = {'crtaj':True, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'--', 'color':(73,189,191), 'alpha':0.9, 'zorder':11}
            glavnikanalfill = {'crtaj':True, 'tip':'fill', 'kanal':None, 'stupac1':'q05', 'stupac2':'q95', 'marker':'None', 'line':'--', 'color':(31,117,229), 'alpha':0.4, 'zorder':7}
            pomocnikanal1 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(186,113,123), 'alpha':0.9, 'zorder':1}
            pomocnikanal2 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(213,164,255), 'alpha':0.9, 'zorder':2}
            pomocnikanal3 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(111,118,255), 'alpha':0.9, 'zorder':3}
            pomocnikanal4 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(149,255,147), 'alpha':0.9, 'zorder':4}
            pomocnikanal5 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(214,255,137), 'alpha':0.9, 'zorder':5}
            pomocnikanal6 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'avg', 'marker':'None', 'line':'-', 'color':(255,64,47), 'alpha':0.9, 'zorder':6}
            opcenito = {'grid':False, 'cursor':False, 'span':False, 'minorTicks':True}
            m_validanOK = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'marker':'p', 'color':(0,255,0), 'alpha':1, 'zorder':20}
            m_validanNOK = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'marker':'p', 'color':(255,0,0), 'alpha':1, 'zorder':20}
            m_nevalidanOK = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'marker':'o', 'color':(0,255,0), 'alpha':1, 'zorder':20}
            m_nevalidanNOK = {'crtaj':True, 'tip':'scatter', 'kanal':None, 'marker':'o', 'color':(255,0,0), 'alpha':1, 'zorder':20}
            m_glavnikanal = {'crtaj':True, 'tip':'plot', 'kanal':None, 'stupac1':'koncentracija', 'marker':'None', 'line':'-', 'color':(45,86,90), 'alpha':0.9, 'zorder':10}
            m_pomocnikanal1 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'koncentracija', 'marker':'None', 'line':'-', 'color':(186,113,123), 'alpha':0.9, 'zorder':1}
            m_pomocnikanal2 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'koncentracija', 'marker':'None', 'line':'-', 'color':(213,164,255), 'alpha':0.9, 'zorder':2}
            m_pomocnikanal3 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'koncentracija', 'marker':'None', 'line':'-', 'color':(111,118,255), 'alpha':0.9, 'zorder':3}
            m_pomocnikanal4 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'koncentracija', 'marker':'None', 'line':'-', 'color':(149,255,147), 'alpha':0.9, 'zorder':4}
            m_pomocnikanal5 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'koncentracija', 'marker':'None', 'line':'-', 'color':(214,255,137), 'alpha':0.9, 'zorder':5}
            m_pomocnikanal6 = {'crtaj':False, 'tip':'plot', 'kanal':None, 'stupac1':'koncentracija', 'marker':'None', 'line':'-', 'color':(255,64,47), 'alpha':0.9, 'zorder':6}
            m_opcenito = {'grid':False, 'cursor':False, 'span':True, 'minorTicks':True}
            self.__defaulti = {'validanOK':validanOK, 
                               'validanNOK':validanNOK, 
                               'nevalidanOK':nevalidanOK, 
                               'nevalidanNOK':nevalidanNOK, 
                               'glavnikanal1':glavnikanal1, 
                               'glavnikanal2':glavnikanal2, 
                               'glavnikanal3':glavnikanal3, 
                               'glavnikanal4':glavnikanal4, 
                               'glavnikanalfill':glavnikanalfill, 
                               'pomocnikanal1':pomocnikanal1, 
                               'pomocnikanal2':pomocnikanal2, 
                               'pomocnikanal3':pomocnikanal3, 
                               'pomocnikanal4':pomocnikanal4, 
                               'pomocnikanal5':pomocnikanal5, 
                               'pomocnikanal6':pomocnikanal6, 
                               'opcenito':opcenito, 
                               'm_validanOK':m_validanOK, 
                               'm_validanNOK':m_validanNOK, 
                               'm_nevalidanOK':m_nevalidanOK, 
                               'm_nevalidanNOK':m_nevalidanNOK, 
                               'm_glavnikanal':m_glavnikanal, 
                               'm_pomocnikanal1':m_pomocnikanal1, 
                               'm_pomocnikanal2':m_pomocnikanal2, 
                               'm_pomocnikanal3':m_pomocnikanal3, 
                               'm_pomocnikanal4':m_pomocnikanal4, 
                               'm_pomocnikanal5':m_pomocnikanal5, 
                               'm_pomocnikanal6':m_pomocnikanal6, 
                               'm_opcenito':m_opcenito}
        else:
            self.__defaulti = defaulti
        #setup widgeta za opceniti dio grafa prilikom loadanja defaulta
        self.action_SatniGrid.setChecked(self.__defaulti['opcenito']['grid'])
        self.action_SatniCursor.setChecked(self.__defaulti['opcenito']['cursor'])
        self.action_SatniSpan.setChecked(self.__defaulti['opcenito']['span'])
        self.action_SatniMinorTicks.setChecked(self.__defaulti['opcenito']['minorTicks'])
        self.action_MinutniGrid.setChecked(self.__defaulti['m_opcenito']['grid'])
        self.action_MinutniCursor.setChecked(self.__defaulti['m_opcenito']['cursor'])
        self.action_MinutniSpan.setChecked(self.__defaulti['m_opcenito']['span'])
        self.action_MinutniMinorTicks.setChecked(self.__defaulti['m_opcenito']['minorTicks'])

###############################################################################
    def setup_akcije(self):
        """
        Povezivanje QAction sa ciljanim slotovima.
        
        Connectioni izmedju menu, toolbarova, i drugih opcija gui-a
        """
        #file i generalni actioni
        self.action_ReadFile.triggered.connect(self.gui_action_read_file)
        self.action_Exit.triggered.connect(self.close)
        #satno agregirani graf
        self.connect(self.action_SatniGrid, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.satniCanvas.enable_grid)
        self.connect(self.action_SatniCursor, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.satniCanvas.enable_cursor)
        self.connect(self.action_SatniSpan, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.satniCanvas.enable_spanSelector)
        self.connect(self.action_SatniMinorTicks, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.satniCanvas.enable_minorTick)
        
        self.connect(self.action_MinutniGrid, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.minutniCanvas.enable_grid)
        
        self.connect(self.action_MinutniCursor, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.minutniCanvas.enable_cursor)
                     
        self.connect(self.action_MinutniSpan, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.minutniCanvas.enable_spanSelector)
        
        self.connect(self.action_MinutniMinorTicks, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.minutniCanvas.enable_minorTicks)        
###############################################################################    
    def provjera(self):
        """testni slot za provjeru signala"""
        print('spojen')
###############################################################################
#    def closeEvent(self, event):
#        """Exit dialog for application. Additional confirmation"""
#        reply=QtGui.QMessageBox.question(
#            self,
#            'Confirm exit',
#            'Are you sure you want to quit?',
#            QtGui.QMessageBox.Yes,
#            QtGui.QMessageBox.No)
#                
#        if reply==QtGui.QMessageBox.Yes:
#            event.accept()
#        else:
#            event.ignore()
###############################################################################
###############################################################################

if __name__ == '__main__':
    aplikacija = QtGui.QApplication(sys.argv)
    glavni = Display()
    glavni.show()
    sys.exit(aplikacija.exec_())
