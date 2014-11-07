# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 14:20:39 2014

@author: User
"""

import pickle
import copy
from PyQt4 import QtCore, QtGui, uic

import dokument
import kontroler
import weblogger_izbornik
import minutniPanel
import satniPanel

###############################################################################
###############################################################################
base, form = uic.loadUiType('display.ui')
class Display(base, form):
    def __init__(self, parent = None):
        super(base, self).__init__(parent)
        self.setupUi(self)

        #inicjalizacija izbornika, trenutno samo weblogger
        self.webLoggerIzbornik = weblogger_izbornik.WebloggerIzbornik()

        
        #ucitaj defaultne vrijednosti za opcije grafova (sto i kako se crta)
        #ova funkcija ce definitivno napraviti member self.__defaulti
        self.load_defaults(None)
        
        """
        memberi
        """
        self.__grafInfo = None #informacija o dostupnim podatcima za crtanje
                
        #inicijalizacija satnog panela
        self.agregiraniPanel = satniPanel.SatniPanel(parent = None, defaulti = self.__defaulti, infoFrejmovi = None)
        #inicijalizacija minutnog canvasa
        self.normalniPanel = minutniPanel.MinutniPanel(parent = None, defaulti = self.__defaulti, infoFrejmovi = None)
        
        #neka se defaultno prikazuje weblogger izbornik        
        self.wlReaderLoaded = True
        #postavi self.webLoggerIzbornik u kontrolni dock widget
        self.dockWidget_kontrola.setWidget(self.webLoggerIzbornik)
        
        #postavi panel sa satno agregiranim grafom u "satni" dock widget
        self.dockWidget_satni.setWidget(self.agregiraniPanel)
        #postavi panel sa minutnim grafom u "minutno" dock widget
        self.dockWidget_minutni.setWidget(self.normalniPanel)


        """povezivanje akcija"""
        self.setup_akcije()
        
        """postavljanje dokumenta i kontrolera"""
        #instanciranje dokumenta
        self.doc = dokument.Dokument()
        #instanciranje kontrolora (gui, dokument)
        #za gui dio mu prosljedjuje referencu na samog sebe
        #za dokument mu prosljeduje instancirani dokument
        self.kontrola = kontroler.Kontrola(gui = self, dokument = self.doc)
###############################################################################
    def setup_akcije(self):
        """
        Povezivanje QAction sa ciljanim slotovima.
        
        Connectioni izmedju menu, toolbarova, i drugih opcija gui-a
        
        npr. moram aplikaciji objasniti sto se tocno treba napraviti kada
        netko klikne da zeli omoguciti span selekciju podataka na satnom grafu.
        """
        #file i generalni actioni
        self.action_ReadFile.triggered.connect(self.gui_action_read_file)
        self.action_Exit.triggered.connect(self.close)
        self.action_Save_preset.triggered.connect(self.save_preset)
        self.action_Load_preset.triggered.connect(self.load_preset)
        #satno agregirani graf
        self.connect(self.action_SatniGrid, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.update_satni_grid)
        self.connect(self.action_SatniCursor, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.update_satni_cursor)
        self.connect(self.action_SatniSpan, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.update_satni_span)
        self.connect(self.action_SatniMinorTicks, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.update_satni_ticks)
        self.connect(self.action_SatniLegenda, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.update_satni_legenda)

        #minutni graf
        self.connect(self.action_MinutniGrid, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.update_minutni_grid)
        self.connect(self.action_MinutniCursor, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.update_minutni_cursor)
        self.connect(self.action_MinutniSpan, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.update_minutni_span)
        self.connect(self.action_MinutniMinorTicks, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.update_minutni_ticks)
        self.connect(self.action_MinutniLegenda, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.update_minutni_legenda)

###############################################################################
    def update_satni_legenda(self, x):
        """
        Metoda odradjuje promjenu stanja legende na satnom grafu.
        Mjenja ciljanu varijablu u self.__defaulti te poziva na ponovno
        iscrtavanje grafa. Ulazni parametar je tipa boolean
        """
        self.__defaulti['ostalo']['opcijesatni']['legend'] = x
        self.emit(QtCore.SIGNAL('promjena_defaulta(PyQt_PyObject)'), self.__defaulti)
###############################################################################
    def update_minutni_legenda(self, x):
        """
        Metoda odradjuje promjenu stanja legende na minutnom grafu.
        Mjenja ciljanu varijablu u self.__defaulti te poziva na ponovno
        iscrtavanje grafa. Ulazni parametar je tipa boolean
        """
        self.__defaulti['ostalo']['opcijeminutni']['legend'] = x
        self.emit(QtCore.SIGNAL('promjena_defaulta(PyQt_PyObject)'), self.__defaulti)
###############################################################################
    def update_satni_grid(self, x):
        """
        Metoda odradjuje promjenu stanja grida na satnom grafu. Mjenja trazenu 
        varijablu u self.__defaulti te poziva na crtanje grafa.
        Ulazni parametar je tipa boolean (True ili False)
        """
        self.__defaulti['ostalo']['opcijesatni']['grid'] = x
        self.emit(QtCore.SIGNAL('promjena_defaulta(PyQt_PyObject)'), self.__defaulti)
###############################################################################
    def update_satni_span(self, x):
        """
        Metoda odradjuje promjenu stanja span selektora na satnom grafu. 
        Mjenja trazenu varijablu u self.__defaulti te poziva na crtanje grafa.
        Ulazni parametar je tipa boolean (True ili False)
        """
        self.__defaulti['ostalo']['opcijesatni']['span'] = x
        self.emit(QtCore.SIGNAL('promjena_defaulta(PyQt_PyObject)'), self.__defaulti)
###############################################################################
    def update_satni_cursor(self, x):
        """
        Metoda odradjuje promjenu stanja pomocnog cursora na satnom grafu. 
        Mjenja trazenu varijablu u self.__defaulti te poziva na crtanje grafa.
        Ulazni parametar je tipa boolean (True ili False)
        """
        self.__defaulti['ostalo']['opcijesatni']['cursor'] = x
        self.emit(QtCore.SIGNAL('promjena_defaulta(PyQt_PyObject)'), self.__defaulti)
###############################################################################
    def update_satni_ticks(self, x):
        """
        Metoda odradjuje promjenu stanja dodatnih tickova na satnom grafu. 
        Mjenja trazenu varijablu u self.__defaulti te poziva na crtanje grafa.
        Ulazni parametar je tipa boolean (True ili False)
        """
        self.__defaulti['ostalo']['opcijesatni']['ticks'] = x
        self.emit(QtCore.SIGNAL('promjena_defaulta(PyQt_PyObject)'), self.__defaulti)
###############################################################################
    def update_minutni_grid(self, x):
        """
        Metoda odradjuje promjenu stanja grida na minutnom grafu. 
        Mjenja trazenu varijablu u self.__defaulti te poziva na crtanje grafa.
        Ulazni parametar je tipa boolean (True ili False)
        """
        self.__defaulti['ostalo']['opcijeminutni']['grid'] = x
        self.emit(QtCore.SIGNAL('promjena_defaulta(PyQt_PyObject)'), self.__defaulti)
###############################################################################
    def update_minutni_cursor(self, x):
        """
        Metoda odradjuje promjenu stanja pomocnog cursora na minutnom grafu. 
        Mjenja trazenu varijablu u self.__defaulti te poziva na crtanje grafa.
        Ulazni parametar je tipa boolean (True ili False)
        """
        self.__defaulti['ostalo']['opcijeminutni']['cursor'] = x
        self.emit(QtCore.SIGNAL('promjena_defaulta(PyQt_PyObject)'), self.__defaulti)
###############################################################################
    def update_minutni_span(self, x):
        """
        Metoda odradjuje promjenu stanja span selektora na minutnom grafu. 
        Mjenja trazenu varijablu u self.__defaulti te poziva na crtanje grafa.
        Ulazni parametar je tipa boolean (True ili False)
        """
        self.__defaulti['ostalo']['opcijeminutni']['span'] = x
        self.emit(QtCore.SIGNAL('promjena_defaulta(PyQt_PyObject)'), self.__defaulti)
###############################################################################
    def update_minutni_ticks(self, x):
        """
        Metoda odradjuje promjenu stanja grida na minutnom grafu. 
        Mjenja trazenu varijablu u self.__defaulti te poziva na crtanje grafa.
        Ulazni parametar je tipa boolean (True ili False)
        """
        self.__defaulti['ostalo']['opcijeminutni']['ticks'] = x
        self.emit(QtCore.SIGNAL('promjena_defaulta(PyQt_PyObject)'), self.__defaulti)
###############################################################################
    def save_preset(self):
        """
        Zapamti stanje (izgled, geometriju, postavke) aplikaicje
        
        ova metoda pamti polozaj i velicinu elemenata displaya, te pamti 
        postavke sto i kako se treba crtati.

        Ideja je da korisnik sam moze podesiti sto i kako ga volja, te da te
        postavke moze brzo i jasno vratiti po volji.

        npr. Netko hoce da su grafovi drugih boja ili zapamti preset koji 
        istovremeno crta NO kao glavni kanal, a NOX i NO2 kao pomocne kanale...        
        """
        #zapamti state toolbarove,dock widgeta....
        preset = self.saveState()
        #zapamti geometriju glavnog prozora
        geometrija =self.geometry()
        #informacija o defaultnim podatcima za crtanje grafova, ista je kopija
        #u oba canvasa pa dohvati bilo koji
        info = copy.deepcopy(self.dockWidget_satni.widget().get_defaulti())
                
        #konzistentno zapakiraj u dict        
        data = {'preset':preset, 'geometrija':geometrija, 'ostalo':info}
        
        #sredi ime i lokaciju filea u koji ces spremiti postavke
        fileName = QtGui.QFileDialog.getSaveFileName(
            self, 
            caption = 'Spremi postavke u:', 
            filter = "Dat Files(*.dat);;All Files(*)")
        
        #napisi sve u file u binarnom obliku
        if fileName:
            with open(fileName, 'wb') as fwrite:
                pickle.dump(data, fwrite)

###############################################################################
    def load_preset(self):
        """
        Ucitaj stanje (izgled, geometriju, postavke) aplikaicje.
        
        Metoda ucitava stanje spremljeno sa save_preset.
        Vidi docstring od save_preset za generalnu ideju zasto metoda postoji.
        """
        data = None
        #dohvati ime i lokaciju filea
        fileName = QtGui.QFileDialog.getOpenFileName(
            self, 
            caption = 'Ucitaj spremljene postavke iz:', 
            filter = "Dat Files(*.dat);;All Files(*)")
        
        #implicitno trvdimo da su ucitani podatci krivi
        test = False
        #loadaj podatke iz filea
        if fileName:
            with open(fileName, 'rb') as fread:
                data = pickle.load(fread)
                if type(data) == dict: #provjera da li je data dict
                    kljucevi = list(data.keys())
                    if ('geometrija' in kljucevi) and ('preset' in kljucevi) and ('ostalo' in kljucevi):
                        #svi bitni kljucevi postoje, provjeri tipove
                        t1 = type(data['geometrija']) == QtCore.QRect
                        t2 = type(data['preset']) == QtCore.QByteArray
                        t3 = type(data['ostalo']) == dict
                        #provjera da li je "odkiseljen" file dobar
                        #pokusaj da se izbjegnu greske ako netko krene ucitavati bezvezne fileove
                        test = t1 and t2 and t3
        
        if test:
            #postavi geometriju glavnog prozora
            self.setGeometry(data['geometrija'])
            #postavi lokaciju dock widgeta, nihovu geometriju....
            self.restoreState(data['preset'])
            #postavi opcije za crtanje grafova
            self.load_defaults(data['ostalo'])
            #informaciju o novim defaultnim vrijednostima treba prosljediti grafovima
            self.agregiraniPanel.zamjeni_defaulte(self.__defaulti)
            self.normalniPanel.zamjeni_defaulte(self.__defaulti)
            #TODO!informaciju treba prosljediti i webloggeru
###############################################################################
    def gui_action_read_file(self):
        """
        Akcija za read file, kada se triggera otvara dijalog za odabir 
        izbornika koji ce biti postavljen u kontrolni dock widget.
        
        Trebati ce doraditi kada se ubace drugi kontrolni elementi.
        """
        izbor = self.read_file_dijalog()
        if (izbor == 'weblogger'):
            if not self.wlReaderLoaded:
                self.wlReaderLoaded = True
                self.dockWidget_kontrola.setWidget(self.webLoggerIzbornik)
                self.dockWidget_kontrola.setWindowTitle('Weblogger izbornik')
        else:
            self.wlReaderLoaded = False
            self.dockWidget_kontrola.setWidget(QtGui.QWidget())
            self.dockWidget_kontrola.setWindowTitle('Kontrolni dio')
###############################################################################
    def read_file_dijalog(self):
        """
        Dijalog za odabir izbornika za kontrolni dock widget.
        
        Trebati ce doraditi kada se ubace drugi kontrolni elementi.
        """
        tipovi = ("weblogger", "PLACEHOLDER1", "PLACEHOLDER2")
        izbor, ok = QtGui.QInputDialog.getItem(self, 
            "Izbor citaca:", 
            "Citac:", 
            tipovi, 
            0, 
            False)
        if ok:
            return izbor
###############################################################################
#    def closeEvent(self, event):
#        """
#        Overloadani signal za gasenje aplikacije. Dodatna potvrda za izlaz.
#        """
#        reply=QtGui.QMessageBox.question(
#            self,
#            'Potvrdi izlaz:',
#            'Da li ste sigurni da hocete ugasiti aplikaciju?',
#            QtGui.QMessageBox.Yes,
#            QtGui.QMessageBox.No)
#                
#        if reply==QtGui.QMessageBox.Yes:
#            event.accept()
#        else:
#            event.ignore()
###############################################################################
    def load_defaults(self, defaulti):
        """
        Prilikom pokretanja aplikacije Display prozor se mora inicijalizirati.
        Ova funkcija vraca defaultne postavke ako se prosljedi None kao argument, 
        ali se moze koristiti za loadanje vec prije spremljenih postavki.
        """
        if defaulti == None:
            self.__defaulti = {
                'glavniKanal':{
                    'midline':{'kanal':None, 'line':'-', 'rgb':(0,0,0), 'alpha':1.0, 'zorder':100, 'label':'average'},
                    'validanOK':{'kanal':None, 'marker':'d', 'rgb':(0,255,0), 'alpha':1.0, 'zorder':100, 'label':'validiran, dobar'}, 
                    'validanNOK':{'kanal':None, 'marker':'d', 'rgb':(255,0,0), 'alpha':1.0, 'zorder':100, 'label':'validiran, los'}, 
                    'nevalidanOK':{'kanal':None, 'marker':'o', 'rgb':(0,255,0), 'alpha':1.0, 'zorder':100, 'label':'nije validiran, dobar'}, 
                    'nevalidanNOK':{'kanal':None, 'marker':'o', 'rgb':(255,0,0), 'alpha':1.0, 'zorder':100, 'label':'nije validiran, los'},
                    'fillsatni':{'kanal':None, 'crtaj':True, 'data1':'q05', 'data2':'q95', 'rgb':(0,0,255), 'alpha':0.5, 'zorder':1}, 
                    'ekstremimin':{'kanal':None, 'crtaj':True, 'marker':'+', 'rgb':(90,50,10), 'alpha':1.0, 'zorder':100, 'label':'min'}, 
                    'ekstremimax':{'kanal':None, 'crtaj':True, 'marker':'+', 'rgb':(90,50,10), 'alpha':1.0, 'zorder':100, 'label':'max'}
                                },
                'pomocniKanali':{}, 
                'ostalo':{
                    'opcijeminutni':{'cursor':False, 'span':True, 'ticks':True, 'grid':False, 'legend':False}, 
                    'opcijesatni':{'cursor':False, 'span':False, 'ticks':True, 'grid':False, 'legend':False}
                        }
                                }
        else:
            self.__defaulti = defaulti
        
        #setup widgeta za opceniti dio grafa prilikom loadanja defaulta
        #postavljanje stanja checkable akcija
        self.blockSignals(True) #BLOKIRAJ SIGNALE, prevent hrpe istih emita
        self.action_SatniGrid.setChecked(self.__defaulti['ostalo']['opcijesatni']['grid'])
        self.action_SatniCursor.setChecked(self.__defaulti['ostalo']['opcijesatni']['cursor'])
        self.action_SatniSpan.setChecked(self.__defaulti['ostalo']['opcijesatni']['span'])
        self.action_SatniMinorTicks.setChecked(self.__defaulti['ostalo']['opcijesatni']['ticks'])
        self.action_SatniLegenda.setChecked(self.__defaulti['ostalo']['opcijesatni']['legend'])
        self.action_MinutniGrid.setChecked(self.__defaulti['ostalo']['opcijeminutni']['grid'])
        self.action_MinutniCursor.setChecked(self.__defaulti['ostalo']['opcijeminutni']['cursor'])
        self.action_MinutniSpan.setChecked(self.__defaulti['ostalo']['opcijeminutni']['span'])
        self.action_MinutniMinorTicks.setChecked(self.__defaulti['ostalo']['opcijeminutni']['ticks'])
        self.action_MinutniLegenda.setChecked(self.__defaulti['ostalo']['opcijeminutni']['legend'])
        self.webLoggerIzbornik.set_defaulti(self.__defaulti)
        self.blockSignals(False) #ODBLOKIRAJ SIGNALE
        #reemit signal da su defaulti promjenjeni
        self.emit(QtCore.SIGNAL('promjena_defaulta(PyQt_PyObject)'), self.__defaulti)
