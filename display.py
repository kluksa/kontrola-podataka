#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 14:20:39 2014

@author: User
"""
import sys
from PyQt4 import QtCore, QtGui, uic

import kontroler
import TreeNode
import grafoviPanel
###############################################################################
###############################################################################
base, form = uic.loadUiType('display.ui')
class Display(base, form):
    def __init__(self, parent = None):
        super(base, self).__init__(parent)
        self.setupUi(self)

        """inicijalizacija komponenti"""
        #inicijalizacija panela za grafove
        self.panel = grafoviPanel.GrafPanel(parent = self)
        #inicjalizacija izbornika, trenutno samo weblogger
        self.webLoggerIzbornik = TreeNode.TreeTest()
        #inicijalizacija kontrolora
        self.kontrola = kontroler.Kontroler(parent = None, gui = self)

        """postavljanje panela i izbornika u dock widgete"""
        #postavljanje panela u dockable widget self.dockWidget_grafovi
        self.dockWidget_grafovi.setWidget(self.panel)
        #postavi self.webLoggerIzbornik u kontrolni dock widget
        self.dockWidget_kontrola.setWidget(self.webLoggerIzbornik)


        """povezivanje akcija vezanih za gui elemente"""
        self.setup_akcije()
        
###############################################################################
    def setup_akcije(self):
        """
        Povezivanje QAction sa ciljanim slotovima.
        Connectioni izmedju menu, toolbarova, i drugih opcija gui-a
        
        npr. moram aplikaciji objasniti sto se tocno treba napraviti kada
        netko klikne da zeli omoguciti span selekciju podataka na satnom grafu.
        """
        #file i generalni actioni
        self.action_Exit.triggered.connect(self.close)
        self.action_Save_preset.triggered.connect(self.request_save_preset)
        self.action_Load_preset.triggered.connect(self.request_load_preset)
        #satno agregirani graf
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

        #minutni graf
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
    def emit_update_satni_legenda(self, x):
        """
        Ulazni parametar je tipa boolean. Metoda reemitira signal sa novim
        stanjem checkable akcije za promjenu prikaza legende na satnom grafu.
        """
        self.emit(QtCore.SIGNAL('update_satni_legenda(PyQt_PyObject)'), x)
###############################################################################
    def emit_update_minutni_legenda(self, x):
        """
        Ulazni parametar je tipa boolean. Metoda reemitira signal sa novim
        stanjem checkable akcije za promjenu prikaza legende na minutnom grafu.
        """
        self.emit(QtCore.SIGNAL('update_minutni_legenda(PyQt_PyObject)'), x)
###############################################################################
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
    def reset_action_state(self, mapaStanja):
        """
        Funkcija je zaduzena da postavi checkable akcije (satnigrid...) u stanje
        koje odgovara kontroloru. Dodatno, funkcija mora "utisati" sve signale
        da izbjegnemo bespotrebno iscrtavanje grafova.
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
        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    x = Display()
    x.show()
    sys.exit(app.exec_())