#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 14:20:39 2014

@author: User
"""
import sys
from PyQt4 import QtCore, QtGui, uic

import functools
import pomocneFunkcije #samo zbog definicije custom exceptiona
import kontroler
import rest_izbornik
import grafoviPanel

###############################################################################
###############################################################################
base, form = uic.loadUiType('display.ui')
class Display(base, form):
    """
    Glavni display okvir applikacije.
        -glavni prozor
        -toolbar
        -msg bar
    """
    def __init__(self, parent = None):
        super(base, self).__init__(parent)
        self.setupUi(self)
        
        #init sa full screenom?
        self.setWindowState(QtCore.Qt.WindowMaximized)
        
        """inicijalizacija komponenti"""
        #inicijalizacija panela za grafove
        self.panel = grafoviPanel.GrafPanel(parent = self)
        #inicjalizacija izbornika, trenutno samo weblogger
        self.restIzbornik = rest_izbornik.RestIzbornik()
        #inicjalizacija zero/span panela
        self.zspanel = grafoviPanel.ZeroSpanPanel(parent = self)
        """postavljanje panela i izbornika u dock widgete"""
        #postavljanje panela u dockable widget self.dockWidget_grafovi
        self.dockWidget_grafovi.setWidget(self.panel)
        #postavi self.restIzbornik u kontrolni dock widget
        self.dockWidget_kontrola.setWidget(self.restIzbornik)
        #postavi ZeroSpanPanel u dock widget
        self.dockWidget_zerospan.setWidget(self.zspanel)
        """inicijalizacija kontrolora"""
#        self.kontrola = kontroler.Kontroler(parent = None, gui = self)
#        """povezivanje akcija vezanih za gui elemente"""
        
        QtCore.QTimer.singleShot(0, self.pokreni_kontrolu)
#        self.setup_akcije()
###############################################################################
    def pokreni_kontrolu(self):
        """
        alternativan nacin loada aplikacije, forsira iscrtavanje primitivnog displaya
        i stavlja dulji load kontrolnog elementa u event loop
        
        tj. init displaya ce zavrsiti prvo, zatim ce se instancirati kontroler
        itd...
        """
        self.kontrola = kontroler.Kontroler(parent = None, gui = self)
        """povezivanje akcija vezanih za gui elemente"""
        self.setup_akcije()
###############################################################################
    def setup_akcije(self):
        """
        Povezivanje QAction sa ciljanim slotovima (toolbar).
        Connectioni izmedju menu, toolbarova, i drugih opcija gui-a.
        
        Pattern svih akcija je sljedeci:
        -Nakon klika na akciju emitiraj specificni signal
        -kontroler osluskuje i hvata te signale te ih realizira
        """
        
        #set ikone u odredjene akcije (zoom in, zoom out, pick)
        self.actionZoomIn.setIcon(QtGui.QIcon('zoomin.jpeg'))
        self.actionZoomOut.setIcon(QtGui.QIcon('zoomout.jpeg'))
        self.actionPick.setIcon(QtGui.QIcon('select.jpeg'))

        #file i generalni actioni
        self.action_Exit.triggered.connect(self.close)
        self.action_reconnectREST.triggered.connect(self.reinitialize_REST)
        self.action_Save_preset.triggered.connect(self.request_save_preset)
        self.action_Load_preset.triggered.connect(self.request_load_preset)
        self.action_Log_in.triggered.connect(self.request_log_in)
        self.action_Log_out.triggered.connect(self.request_log_out)
        
        #toggle zoom / pick opcije
        self.actionZoomIn.triggered.connect(functools.partial(self.zoom_pick_toggle, tip = 'zoom'))
        self.actionPick.triggered.connect(functools.partial(self.zoom_pick_toggle, tip = 'pick'))
        self.actionZoomOut.triggered.connect(self.zoom_out)

        #toolbar, satno agregirani graf
        self.connect(self.action_SatniGrid, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.emit_update_satni_grid)
        self.connect(self.action_SatniCursor, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.emit_update_satni_cursor)
        self.connect(self.action_SatniSpan, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.emit_update_satni_span)
        self.connect(self.action_SatniMinorTicks, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.emit_update_satni_ticks)
        self.connect(self.action_SatniLegenda, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.emit_update_satni_legenda)

        #toolbar, minutni graf
        self.connect(self.action_MinutniGrid, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.emit_update_minutni_grid)
        self.connect(self.action_MinutniCursor, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.emit_update_minutni_cursor)
        self.connect(self.action_MinutniSpan, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.emit_update_minutni_span)
        self.connect(self.action_MinutniMinorTicks, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.emit_update_minutni_ticks)
        self.connect(self.action_MinutniLegenda, 
                     QtCore.SIGNAL('triggered(bool)'), 
                     self.emit_update_minutni_legenda)
###############################################################################
    def zoom_pick_toggle(self, x, tip = ''):
        """
        Toggle izmedju zoom i pick opcije na grafovima
        x je tipa boolean
        tip je keyword koji oznacava koji "gumb" ga poziva ('zoom' ili 'pick')
        """
        if tip == 'zoom':
            #toggle suprotnu akciju na suprotno stanje od trenutne
            self.actionPick.setChecked(not x)
            #zapamti novo stanje zoom i pick opcije
            arg = [x, not x]
            #emitiraj promjenu stanja
            self.emit(QtCore.SIGNAL('zoom_pick_state(PyQt_PyObject)'), arg)
        elif tip == 'pick':
            self.actionZoomIn.setChecked(not x)
            arg = [not x, x]
            self.emit(QtCore.SIGNAL('zoom_pick_state(PyQt_PyObject)'), arg)
###############################################################################
    def zoom_out(self):
        """
        Javi kontroloru da pokrene Zoom out svih grafova na pocetni polozaj.
        """
        self.emit(QtCore.SIGNAL('zoom_out_all'))
###############################################################################
    def reinitialize_REST(self):
        """
        Toolbar akcija za reinicijlalizaciju REST servisa
        
        Javlja kontrolnom dijelu programa da ponovi dio inicijalizacije vezane
        za rest servis (ponovno definira reader/writer, sastavljanje novog stabla
        programa mjerenja...)
        """
        self.emit(QtCore.SIGNAL('gui_reinitialize_REST'))
###############################################################################
    def emit_update_satni_legenda(self, x):
        """
        Ulazni parametar je tipa boolean. Metoda reemitira signal sa novim
        stanjem checkable akcije za promjenu prikaza legende na satnom grafu.
        """
        self.emit(QtCore.SIGNAL('update_satni_legenda(PyQt_PyObject)'), x)
################################################################################
    def emit_update_minutni_legenda(self, x):
        """
        Ulazni parametar je tipa boolean. Metoda reemitira signal sa novim
        stanjem checkable akcije za promjenu prikaza legende na minutnom grafu.
        """
        self.emit(QtCore.SIGNAL('update_minutni_legenda(PyQt_PyObject)'), x)
################################################################################
    def emit_update_satni_grid(self, x):
        """
        Ulazni parametar je tipa boolean. Metoda reemitira signal sa novim
        stanjem checkable akcije za promjenu prikaza grida na satnom grafu.
        """
        self.emit(QtCore.SIGNAL('update_satni_grid(PyQt_PyObject)'), x)
###############################################################################
    def emit_update_satni_span(self, x):
        """
        Ulazni parametar je tipa boolean. Metoda reemitira signal sa novim
        stanjem checkable akcije za promjenu span selektora na satnom grafu.
        """
        self.emit(QtCore.SIGNAL('update_satni_span(PyQt_PyObject)'), x)
###############################################################################
    def emit_update_satni_cursor(self, x):
        """
        Ulazni parametar je tipa boolean. Metoda reemitira signal sa novim
        stanjem checkable akcije za promjenu prikaza cursora na satnom grafu.
        """
        self.emit(QtCore.SIGNAL('update_satni_cursor(PyQt_PyObject)'), x)
###############################################################################
    def emit_update_satni_ticks(self, x):
        """
        Ulazni parametar je tipa boolean. Metoda reemitira signal sa novim
        stanjem checkable akcije za promjenu prikaza minor tickova na satnom grafu.
        """
        self.emit(QtCore.SIGNAL('update_satni_ticks(PyQt_PyObject)'), x)
###############################################################################
    def emit_update_minutni_grid(self, x):
        """
        Ulazni parametar je tipa boolean. Metoda reemitira signal sa novim
        stanjem checkable akcije za promjenu prikaza grida na minutnom grafu.
        """
        self.emit(QtCore.SIGNAL('update_minutni_grid(PyQt_PyObject)'), x)
###############################################################################
    def emit_update_minutni_cursor(self, x):
        """
        Ulazni parametar je tipa boolean. Metoda reemitira signal sa novim
        stanjem checkable akcije za promjenu prikaza cursora na minutnom grafu.
        """
        self.emit(QtCore.SIGNAL('update_minutni_cursor(PyQt_PyObject)'), x)
###############################################################################
    def emit_update_minutni_span(self, x):
        """
        Ulazni parametar je tipa boolean. Metoda reemitira signal sa novim
        stanjem checkable akcije za promjenu span selektora na minutnom grafu.
        """
        self.emit(QtCore.SIGNAL('update_minutni_span(PyQt_PyObject)'), x)
###############################################################################
    def emit_update_minutni_ticks(self, x):
        """
        Ulazni parametar je tipa boolean. Metoda reemitira signal sa novim
        stanjem checkable akcije za promjenu prikaza minor tickova na minutnom
        grafu.
        """
        self.emit(QtCore.SIGNAL('update_minutni_ticks(PyQt_PyObject)'), x)
###############################################################################
    def request_save_preset(self):
        """
        Prosljedi zahtjev kontroloru da spremi trenutne postavke aplikacije
        u file
        """
        self.emit(QtCore.SIGNAL('request_save_preset'))
###############################################################################
    def request_load_preset(self):
        """
        Prosljedi zahtjev kontroloru da ucita postavke aplikacije iz filea
        """
        self.emit(QtCore.SIGNAL('request_load_preset'))
###############################################################################
    def request_log_in(self):
        """
        Prosljedi kontroloru zahtjev za poziv log in dijaloga.
        """
        self.emit(QtCore.SIGNAL('request_log_in'))
###############################################################################
    def request_log_out(self):
        """
        Prosljedi kontroloru zahtjev za log out korisnika
        """
        self.emit(QtCore.SIGNAL('request_log_out'))
###############################################################################
    def set_action_state(self, mapaStanja):
        """
        Funkcija je zaduzena da postavi checkable akcije (satnigrid...) u stanje
        koje odgovara kontroloru(*). Dodatno, funkcija mora privremeno "utisati" 
        sve signale koje emitira display.
        
        *
        -kontorlor je zaduzen da 'pamti' defaultno stanje sto ce se prikazivati
        i kako (span, ticks...).
        """
        self.blockSignals(True)
        self.action_SatniGrid.setChecked(mapaStanja['satnigrid'])
        self.action_SatniCursor.setChecked(mapaStanja['satnicursor'])
        self.action_SatniSpan.setChecked(mapaStanja['satnispan'])
        self.action_SatniMinorTicks.setChecked(mapaStanja['satniticks'])
        self.action_SatniLegenda.setChecked(mapaStanja['satnilegend'])
        self.action_MinutniGrid.setChecked(mapaStanja['minutnigrid'])
        self.action_MinutniCursor.setChecked(mapaStanja['minutnicursor'])
        self.action_MinutniSpan.setChecked(mapaStanja['minutnispan'])
        self.action_MinutniMinorTicks.setChecked(mapaStanja['minutniticks'])
        self.action_MinutniLegenda.setChecked(mapaStanja['minutnilegend'])
        self.blockSignals(False)
###############################################################################
    def closeEvent(self, event):
        """
        Overloadani signal za gasenje aplikacije. Dodatna potvrda za izlaz.
        """
        saveState = self.kontrola.exit_check()
        if not saveState:
            reply=QtGui.QMessageBox.question(
                self,
                'Potvrdi izlaz:',
                'Da li ste sigurni da hocete ugasiti aplikaciju?\nNeki podaci nisu spremljeni na REST servis.',
                QtGui.QMessageBox.Yes,
                QtGui.QMessageBox.No)
                
            if reply==QtGui.QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            #izlaz iz aplikacije bez dodatnog pitanja.
            event.accept()
###############################################################################
        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    x = Display()
    x.show()
    sys.exit(app.exec_())