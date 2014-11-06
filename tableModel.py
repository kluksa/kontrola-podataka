# -*- coding: utf-8 -*-
"""
Created on Tue Nov  4 15:56:53 2014

@author: User
"""

from PyQt4 import QtGui, QtCore
import pomocneFunkcije

class PomocniGrafovi(QtCore.QAbstractTableModel):
    """
    Ova klasa je "model" za dinamicki prikaz pomocnih grafova u qtableview widgetu
    
    model je zaduzen za:
    -dinamicki unos i brisanje pomocnog grafa
    -konzistentan update QViewTable widgeta sa trenutno aktivnim kanalima
    -bolji prikaz QViewTable widgeta
    
    P.S. imenovanje funkcija odskace od nacina na koji su pisane drugdje, ali
    Qt frejmwork inszistira da se funkcije zovu rowCount,  a ne row_count
    """
    def __init__(self, grafInfo = [], parent = None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        
        #spremi ulaznu mapu u privatni member
        self.__grafInfo = grafInfo
        self.__headeri = ['Label', 'Kanal', 'Marker', 'Linija', 'Zorder']
        #pomocni dict za tip linije
        self.__linije = {'None':'Bez linije', 
                         '-':'Puna linija',
                         '--':'Dash - Dash', 
                         '-.':'Dash - Dot', 
                         ':':'Dot'}
        #pomocni dict za tip markera
        self.__markeri = {'None':'Bez markera', 
                          'o':'Krug', 
                          'v':'Trokut, dolje', 
                          '^':'Trokut, gore', 
                          '<':'Trokut, lijevo', 
                          '>':'Trokut, desno', 
                          's':'Kvadrat', 
                          'p':'Pentagon', 
                          '*':'Zvijezda', 
                          'h':'Heksagon', 
                          '+':'Plus', 
                          'x':'X', 
                          'd':'Dijamant', 
                          '_':'Horizontalna linija', 
                          '|':'Vertikalna linija'}
        
    def rowCount(self, parent = QtCore.QModelIndex()):
        """
        Nuzna metoda za rad klase
        -vraca informaciju o broju redaka display djelu
        """
        return len(self.__grafInfo)
    
    def columnCount(self, parent = QtCore.QModelIndex()):
        """
        Nuzna metoda za rad klase
        -vraca informaciju o broju stupaca display djelu
        """
        #hardcoded, samo 5 stupca ['Label', 'Kanal', 'Marker', 'Linija', 'Zorder']
        return 5
        
    def flags(self, index):
        """
        -vraca van stanje svakog indeksa u prikazu tablice.
        -za sada samo enabled i selectable
        -iskljucivo prikaz podataka
        """
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        
    def data(self, index, role):
        """
        Nuzna metoda za rad klase
        -za svaki role i indeks u tablici daje display djelu trazene vrijednosti
        """
        if not index.isValid():
            return None
        
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            column = index.column()
            if column == 0:
                value = self.__grafInfo[row][6] #stupac Label
            elif column == 1:
                value = self.__grafInfo[row][0] #stupac Kanal
            elif column == 2:
                value = self.__markeri[self.__grafInfo[row][1]] #stupac Marker
            elif column == 3:
                value = self.__linije[self.__grafInfo[row][2]] #stupac Linija
            elif column == 4:
                value = self.__grafInfo[row][5] #stupac Zorder

            return value
            
        if role == QtCore.Qt.DecorationRole:
            row = index.row()
            column = index.column()
            if column == 0:
                #samo na prvom stupcu (Label)
                
                #sirovi podaci o boji
                rgb = self.__grafInfo[row][3]
                alpha = self.__grafInfo[row][4]
                #stvaranje tocne nijanse kao QColor
                boja = pomocneFunkcije.default_color_to_qcolor(rgb, alpha)
                #izrada pixmapa i ikone koju dodajemo kao ukras
                pixmap = QtGui.QPixmap(20,20)
                pixmap.fill(boja)
                icon = QtGui.QIcon(pixmap)
                return icon
            
    def headerData(self, section, orientation, role):
        """
        Metoda postavlja headere u tablicu
        """
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.__headeri[section]
            else:
                return section
                
    def insertRows(self, position, rows, parent = QtCore.QModelIndex(), sto = None):
        """
        metoda za umetanje redova u tablicu
        insert na poziciji : position
        broj redova za insertanje : rows
        parent = defaultni q model index
        """
        #mora se pozvati zbog sinhorizacije view-ova
        self.beginInsertRows(parent, position, position+rows-1)
        
        #insert u podatke
        for i in range(rows):
            value = sto[i]
            self.__grafInfo.insert(position, value)
                
        #mora se pozvati zbog sinhorizacije view-ova
        self.endInsertRows()
        #funkcija mora vratiti True da signalizira da su redovi umetnuti
        return True
        
    def removeRows(self, position, rows, parent = QtCore.QModelIndex()):
        """
        metoda za brisanje redova iz tablice
        delete na poziciji : position
        broj redova za delete : rows
        parent = defaultni q model index
        """
        #mora se pozvati zbog sinhronizacije view-ova
        self.beginRemoveRows(parent, position, position+rows-1)
        
        #sami delete
        for i in range(rows):
            self.__grafInfo.pop(position)
        
        #mora se pozvati zbog sinhronizacije view-ova
        self.endRemoveRows()
        #funkcija mora vratiti True da signalizira da su redovi umetnuti
        return True
        
    def vrati_nested_listu(self):
        """
        funkcija vraca nested listu koja sadrzi podatke u modelu
        """
        return self.__grafInfo