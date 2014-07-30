#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 12 11:23:36 2014

@author: velimir

-treba dodavati grafičke elemente po potrebi
-napisati metode za prikazivanje pojedinih elemenata (npr. update Comboboxeva)

-izbrisao sve bitno osim layouta.
TODO:
3.spoji read filea sa grafovima
4.spoji promjene i update grafova u gui-u
"""

import sys

from PyQt4 import QtGui,QtCore

import dokument
import kontroler
import graf_signal
import weblogger_izbornik

class GlavniProzor(QtGui.QMainWindow):
    def __init__(self,parent=None):
        """
        -ideja je ovo kasnije pregaziti s nekim ui fileom iz designera
        -trenutno je lakse povezivati widgete etc...
        """
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle('Kontrola podataka')
        self.resize(800, 600)
        self.sizePolicy=QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,
                                          QtGui.QSizePolicy.Expanding)
        self.setMinimumSize(QtCore.QSize(640, 480))
        self.setMouseTracking(True)
        
        """
        memberi
        """        
        self.readerLoaded = False
        
        """
        Inicijalizacija kontrolnog sucelja (menu,toolbar,status bar)
        """
        #napravi status bar
        self.statusBar().showMessage('Ready')
        #napravi menu bar, napuni ga sa naredbama
        self.create_menu()
        #napravi toolbar, napuni ga sa naredbama
        tbar=self.create_tool_bar()
        self.addToolBar(tbar)

        #inicjalizacija weblogger_izbornik
        self.webLoggerIzbornik = weblogger_izbornik.WebloggerIzbornik()
        
        """
        Osnovni layout applikacije - pozicija widgeta etc...
        """
        #glavni kontenjer za ostale widgete        
        self.mainWidget=QtGui.QWidget()
        self.setCentralWidget(self.mainWidget)
        
        #layout grafova
        self.graf1=QtGui.QWidget()
        self.graf2=QtGui.QWidget()
        self.canvasSatni=graf_signal.GrafSatniSrednjaci(self.graf1,
                                                   width=4,
                                                   height=3,
                                                   dpi=150)
        self.canvasMinutni=graf_signal.GrafMinutniPodaci(self.graf2,
                                                    width=4,
                                                    height=3,
                                                    dpi=150)
        grafLayout=QtGui.QVBoxLayout()
        grafLayout.addWidget(self.canvasSatni)
        grafLayout.addWidget(self.canvasMinutni)

        
        #zavrsni layout
        final=QtGui.QVBoxLayout(self.mainWidget)
        #final.addLayout(IOLayout)
        final.addLayout(grafLayout)
        

        #povezivanje gui - kontoler - dokument
        self.doc = dokument.Dokument()
        self.kontrola = kontroler.Mediator(gui = self, model = self.doc)
###############################################################################
    
    """
    Gumbi i menu/toolbar akcije
    """
    
    def gui_action_read_file(self):
        """
        Akcija za read file.
        Otvara dialog za izbor tipa filea.
        Ovisno o izboru:
        -stvara widget za izbor filea za otvaranje i navigaciju
        -docka ga u main window
        """
        izbor = self.read_file_dijalog()
        
        #na istu shemu se dodaju i rezultati drugih gumba po potrebi
        if (izbor == 'weblogger') and (not self.readerLoaded):
            self.readerLoaded = True
            self.izborMape = QtGui.QDockWidget(self)
            self.izborMape.setWindowTitle('Odabir podataka')

            #definiraj sadrzaj dockable widgeta
            self.izborMapeSadrzaj = self.webLoggerIzbornik
            self.izborMape.setWidget(self.izborMapeSadrzaj)
            #dodaj ga na main window na lijevom rubu
            self.addDockWidget(QtCore.Qt.DockWidgetArea(1),self.izborMape)
            self.izborMape.closeEvent = self.reader_widget_close

###############################################################################
    def set_status_bar(self,tekst):
        """
        Update statusbara
        """
        self.statusBar().showMessage(tekst)        
###############################################################################
    def create_menu(self):
        """
        By using create_action i add_actions_to methods, create a menu
        """
        self.fileMenu=self.menuBar().addMenu("&File")
        
        self.action_exit=self.create_action('&Exit',
                                            slot=self.close,
                                            shortcut='Ctrl+Q',
                                            tooltip='Exit the application')
                                            
        self.action_read_file=self.create_action('&Read file',
                                                slot=self.gui_action_read_file,
                                                shortcut='Alt+R',
                                                tooltip='Read file')
                                            
                                            
        fileMenuList=[self.action_read_file,
                      None,
                      self.action_exit]
                
        self.add_actions_to(self.fileMenu, fileMenuList)
###############################################################################
    def create_tool_bar(self):
        """
        By using create_action i add_actions_to methods, create a tool bar
        """
        toolBar=self.addToolBar('Main toolbar')
        
        toolBarList=[self.action_read_file,
                     None,
                     self.action_exit]
        
        self.add_actions_to(toolBar, toolBarList)
        return toolBar
###############################################################################
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
###############################################################################
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
###############################################################################
    """
    def closeEvent(self, event):
        #Exit dialog for application. Additional confirmation
        
        reply=QtGui.QMessageBox.question(
                self,
                'Confirm exit',
                'Are you sure you want to quit?',
                QtGui.QMessageBox.Yes,
                QtGui.QMessageBox.No)
                
        if reply==QtGui.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
    """
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
    def reader_widget_close(self, event):
        """
        Ova funkcija hvata close event file readera (self.izborMape)
        Cilj je izbjeci otvaranje dva reaera istovremeno.
        """
        self.readerLoaded = False
###############################################################################
###############################################################################

if __name__ == '__main__':
    aplikacija = QtGui.QApplication(sys.argv)
    glavni = GlavniProzor()
    glavni.show()
    sys.exit(aplikacija.exec_())
