# -*- coding: utf-8 -*-
"""
Created on Mon May 12 11:23:36 2014

@author: velimir

-treba dodavati grafičke elemente po potrebi
-napisati metode za prikazivanje pojedinih elemenata (npr. update Comboboxeva)
"""

import sys

from PyQt4 import QtGui,QtCore

import dokument
import kontroler
import graf_signal

class GlavniProzor(QtGui.QMainWindow):
    def __init__(self,parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle('Kontrola podataka')
        self.resize(800, 600)
        self.sizePolicy=QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,
                                          QtGui.QSizePolicy.Expanding)
        self.setMinimumSize(QtCore.QSize(640, 480))
        self.setMouseTracking(True)
        
        """
        Inicijalizacija kontrolnog sucelja (menu,toolbar,status bar)
        """
        #napravi status bar
        self.statusBar().showMessage('Poruka na status baru.')
        #napravi menu bar, napuni ga sa naredbama
        self.create_menu()
        #napravi toolbar, napuni ga sa naredbama
        tbar=self.create_tool_bar()
        self.addToolBar(tbar)
        
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

        #layout kontrolnih elemenata (QComboBox, QPushButton, QLabel ... )
        selektorKanalaLabel=QtGui.QLabel('Izbor kanala')
        self.selektorKanala=QtGui.QComboBox()
        self.selektorKanala.setMinimumContentsLength(20)
        selektorSataLabel=QtGui.QLabel('Izbor sata')
        self.selektorSata=QtGui.QComboBox()
        self.selektorSata.setMinimumContentsLength(20)
        self.gumbCrtajSatni=QtGui.QPushButton('CRTAJ SATNI')
        self.gumbCrtajMinutni=QtGui.QPushButton('CRTAJ MINUTNI')
        
        IOLayout=QtGui.QVBoxLayout()
        IOLayout.addWidget(selektorKanalaLabel)
        IOLayout.addWidget(self.selektorKanala)
        IOLayout.addWidget(self.gumbCrtajSatni)
        IOLayout.addWidget(selektorSataLabel)
        IOLayout.addWidget(self.selektorSata)
        IOLayout.addWidget(self.gumbCrtajMinutni)

        #zavrsni layout
        final=QtGui.QHBoxLayout(self.mainWidget)
        final.addLayout(grafLayout)
        final.addLayout(IOLayout)
        
        """
        Kontrolni dio
        """
        #inicijalizacija dokumenta i kontrolera
        self.doc=dokument.Dokument()
        self.kontrola=kontroler.KontrolerSignala(view=self,model=self.doc)


###############################################################################
    def set_odabrani_sat(self,sat):
        """
        Postavi izbor comboboxa sa satnim podatcima na određenu vrijednost
        """
        sat=str(sat)
        indeks=self.selektorSata.findText(sat)
        self.selektorSata.setCurrentIndex(indeks)

###############################################################################
    def get_odabrani_sat(self):
        """
        Emitiraj signal sa treutno odabranim satom
        """
        sat=self.selektorSata.currentText()
        self.emit(QtCore.SIGNAL('set_odabrani_sat(PyQt_PyObject)'),sat)
        
###############################################################################
    def set_selektorSata(self,lista):
        """
        Punjenje comboboxasa satnim indeksima. Drugi nacin za crtanje minutnog
        grafa.
        """
        self.selektorSata.clear()
        self.selektorSata.addItems(lista)
###############################################################################
    def get_kanal(self):
        """
        Emitiraj signal sa trenutno odabranim kanalom
        """
        kanal=self.selektorKanala.currentText()
        self.emit(QtCore.SIGNAL('kanal_odabran(PyQt_PyObject)'),kanal)
###############################################################################
    def signal_request_read_csv(self):
        """
        Shows file dialog, forwards the choice by emitting QtCore custom signal
        """
        filename=QtGui.QFileDialog.getOpenFileName(self, 'Open CSV file', '')
        self.emit(QtCore.SIGNAL('request_read_csv(PyQt_PyObject)'),filename)
###############################################################################
    def update_kljuc(self,listaKljuceva):
        """
        Update kljuceva, tj. update elemenata QComboBox-a (selektorKanala)
        """
        self.selektorKanala.clear()
        self.selektorKanala.addItems(listaKljuceva)
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
                                            
        self.action_read_csv=self.create_action('&Read CSV file',
                                                slot=self.signal_request_read_csv,
                                                shortcut='Alt+R',
                                                tooltip='Read file')
                                            
                                            
        fileMenuList=[self.action_read_csv,None,self.action_exit]
                
        self.add_actions_to(self.fileMenu, fileMenuList)
###############################################################################
    def create_tool_bar(self):
        """
        By using create_action i add_actions_to methods, create a tool bar
        """
        toolBar=self.addToolBar('Main toolbar')
        
        toolBarList=[self.action_read_csv,
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
    def closeEvent(self, event):
        """
        Exit dialog for application. Additional confirmation
        """
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
###############################################################################


if __name__ == '__main__':
    aplikacija = QtGui.QApplication(sys.argv)
    glavni = GlavniProzor()
    glavni.show()
    sys.exit(aplikacija.exec_())