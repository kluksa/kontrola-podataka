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
        self.statusBar().showMessage('Ready')
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
        #lokalni connect dijelova gui
        self.connect(self.gumbCrtajSatni,
                     QtCore.SIGNAL('clicked()'),
                     self.gui_crtaj_satni)
        self.connect(self.gumbCrtajMinutni,
                     QtCore.SIGNAL('clicked()'),
                     self.gui_crtaj_minutni)
        #inicijalizacija dokumenta i kontrolera
        self.doc=dokument.Dokument()
        self.kontrola=kontroler.Mediator(gui=self,model=self.doc)


###############################################################################
    """
    Dio osnovnih funkcija za mediator (get/set...)
    """
    def get_kanali(self):
        """
        Emitira listu stringova (sve elemente comboboxa sa kanalima)
        """
        rezultat=[]
        for index in list(range(self.selektorKanala.count())):
            rezultat.append(self.selektorKanala.itemText(index))
        self.emit(QtCore.SIGNAL('gui_get_kanali(PyQt_PyObject)'),rezultat)
        
    def set_kanali(self,kanali):
        """
        Cleara combobox sa kanalima te postavlja nove kanale
        """
        self.selektorKanala.clear()
        self.selektorKanala.addItems(kanali)
        
    def get_sati(self):
        """
        Emitira listu stringova (sve elemente comboboxa sa vremenima satnih
        agregata)
        """
        rezultat=[]
        for index in list(range(self.selektorSata.count())):
            rezultat.append(self.selektorSata.itemText(index))
        self.emit(QtCore.SIGNAL('gui_get_sati(PyQt_PyObject)'),rezultat)
    
    def set_sati(self,sati):
        """
        Cleara combobox sa vremenima satnih agregata te postavlja nove
        """
        self.selektorSata.clear()
        self.selektorSata.addItems(sati)
        
    def get_kanal(self):
        """
        Emitira trenutno aktivni kanal u comboboxu s kanalima (string)
        """
        self.emit(QtCore.SIGNAL('gui_get_kanal(PyQt_PyObject)'),
                  self.selektorKanala.currentText())
    
    def set_kanal(self,kanal):
        """
        Postavlja kanal kao trenutno aktivni u comboboxu s kanalima
        """
        index=self.selektorSata.findText(kanal)
        self.selektorSata.setCurrentIndex(index)
    
    def get_sat(self):
        """
        Emitira trenutno aktivni sat u comboboxu sa vremenima agregata
        """
        self.emit(QtCore.SIGNAL('gui_get_sat(PyQt_PyObject)'),
                  self.selektorSata.currentText())
    
    def set_sat(self,vrijeme):
        """
        Postavlja sat kao trenutno aktivni u comboboxu sa vremenima agregata
        """
        index=self.selektorSata.findText(vrijeme)
        self.selektorSata.setCurrentIndex(index)
        
    def gui_request_read_csv(self):
        """
        Akcija za read novi csv file, otvara file dialog i emitira path do
        csv filea
        """
        filepath=QtGui.QFileDialog.getOpenFileName(self, 'Open CSV file', '')
        self.emit(QtCore.SIGNAL('gui_request_read_csv(PyQt_PyObject)'),
                  filepath)
                  
    def set_status_bar(self,tekst):
        """
        Update statusbara
        """
        self.statusBar().showMessage(tekst)
        
    def gui_crtaj_satni(self):
        """
        Zahtjev za crtanje satnih podataka (gumb)
        """
        kanal=self.selektorKanala.currentText()
        self.emit(QtCore.SIGNAL('gui_request_crtaj_satni(PyQt_PyObject)'),
                  kanal)
        
    def gui_crtaj_minutni(self):
        """
        Zahtjev za crtanje minutnih podataka (gumb)
        """
        sat=self.selektorSata.currentText()
        self.emit(QtCore.SIGNAL('gui_request_crtaj_minutni(PyQt_PyObject)'),
                  sat)









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
                                                slot=self.gui_request_read_csv,
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