# -*- coding: utf-8 -*-
"""
Created on Tue Nov  4 15:56:53 2014

@author: User
"""

from PyQt4 import QtGui, QtCore
import app.general.pomocne_funkcije as pomocne_funkcije
import math


class PomocniGrafovi(QtCore.QAbstractTableModel):
    """
    Ova klasa je "model" za dinamicki prikaz pomocnih grafova u qtableview widgetu

    P.S. imenovanje funkcija odskace od nacina na koji su pisane drugdje, ali
    Qt frejmwork inszistira da se funkcije zovu rowCount,  a ne row_count

    P.P.S. za inicijalizaciju su bitne 4 stvari
    1. grafInfo -> treba dati nested listu pomocnih grafova (inace je nested dictionary)
    2. markeri ->lista svih markera koji ulaze u izbor, opisni ('Krug'...)
    3. linije ->lista svih stilova linija, opisni ('Dash-Dot'...)
    """
    def __init__(self, grafInfo=None, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.headeri = ['Postaja', 'Komponenta', 'Usporedno']
        if grafInfo == None:
            self.grafInfo = []
        else:
            self.grafInfo = grafInfo

    def rowCount(self, parent=QtCore.QModelIndex()):
        """
        Nuzna metoda za rad klase
        -vraca informaciju o broju redaka display djelu
        """
        return len(self.grafInfo)

    def columnCount(self, parent=QtCore.QModelIndex()):
        """
        Nuzna metoda za rad klase
        -vraca informaciju o broju stupaca display djelu
        HARDCODED, samo 3 stupca:
            ['Postaja', 'Komponenta', 'Usporedno']
        """
        return 3

    def flags(self, index):
        """
        -vraca van stanje svakog indeksa u prikazu tablice.
        -enabled, selectable i editable
        """
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """
        Metoda zaduzena za postavljanje novih vrijednosti u model(editable).

        Cilj je delegirati editiranje na posebni dijalog.
        """
        if not index.isValid():
            return False

        if role == QtCore.Qt.EditRole:
            row = index.row()
            col = index.column()
            if col == 0:  # promjena Postaje
                self.grafInfo[row][1] = value  #promjeni Postaju
                #promjeni i programMjerenjaId
                postaja = self.grafInfo[1]
                komponenta = self.grafInfo[2]
                usporedno = self.grafInfo[3]
                self.grafInfo[row][0] = self.pomocnaMapa[postaja][komponenta][usporedno]
                return True
            elif col == 1:
                self.grafInfo[row][2] = value  # promjeni komponentu
                self.grafInfo[row][11] = value  # promjeni i label
                # promjeni i programMjerenjaId
                postaja = self.grafInfo[1]
                komponenta = self.grafInfo[2]
                usporedno = self.grafInfo[3]
                self.grafInfo[row][0] = self.pomocnaMapa[postaja][komponenta][usporedno]
                return True
            elif col == 2:
                self.grafInfo[row][3] = value  # promjeni usporedno
                # promjeni i programMjerenjaId
                postaja = self.grafInfo[1]
                komponenta = self.grafInfo[2]
                usporedno = self.grafInfo[3]
                self.grafInfo[row][0] = self.pomocnaMapa[postaja][komponenta][usporedno]
                return True

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
                value = self.grafInfo[row][1]  # stupac "Postaja"
            elif column == 1:
                value = self.grafInfo[row][2]  # stupac "Komponenta"
            elif column == 2:
                value = self.grafInfo[row][3]  # stupac "Usporedno"
            return value
        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()
            if column == 0:
                value = self.grafInfo[row][1]  # stupac "Postaja"
            elif column == 1:
                value = self.grafInfo[row][2]  # stupac "Komponenta"
            elif column == 2:
                value = self.grafInfo[row][3]  # stupac "Usporedno"
            return value
        if role == QtCore.Qt.DecorationRole:
            row = index.row()
            column = index.column()
            if column == 0:
                # na stupcima 1 (komponenta)
                rgb = self.grafInfo[row][8]
                alpha = self.grafInfo[row][9]
                #stvaranje tocne nijanse kao QColor
                boja = pomocne_funkcije.default_color_to_qcolor(rgb, alpha)
                #izrada pixmapa i ikone koju dodajemo kao ukras
                pixmap = QtGui.QPixmap(20, 20)
                pixmap.fill(boja)
                icon = QtGui.QIcon(pixmap)
                return icon

    def headerData(self, section, orientation, role):
        """
        Metoda postavlja headere u tablicu
        """
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.headeri[section]
            else:
                return section

    def insertRows(self, position, rows, parent=QtCore.QModelIndex(), sto=None):
        """
        metoda za umetanje redova u tablicu
        insert na poziciji : position
        broj redova za insertanje : rows
        parent = defaultni q model index
        """
        # mora se pozvati zbog sinhorizacije view-ova
        self.beginInsertRows(parent, position, position + rows - 1)
        #insert u podatke
        for i in range(rows):
            value = sto[i]
            self.grafInfo.insert(position, value)
        #mora se pozvati zbog sinhorizacije view-ova
        self.endInsertRows()
        #funkcija mora vratiti True da signalizira da su redovi umetnuti
        return True

    def removeRows(self, position, rows, parent=QtCore.QModelIndex()):
        """
        metoda za brisanje redova iz tablice
        delete na poziciji : position
        broj redova za delete : rows
        parent = defaultni q model index
        """
        # mora se pozvati zbog sinhronizacije view-ova
        self.beginRemoveRows(parent, position, position + rows - 1)
        #sami delete
        for i in range(rows):
            self.grafInfo.pop(position)
        #mora se pozvati zbog sinhronizacije view-ova
        self.endRemoveRows()
        #funkcija mora vratiti True da signalizira da su redovi umetnuti
        return True

    def vrati_nested_listu(self):
        """
        funkcija vraca nested listu koja sadrzi podatke u modelu
        """
        return self.grafInfo


class BitModel(QtCore.QAbstractTableModel):
    """
    Model za prikaz statusa bit po bit.
    """
    def __init__(self, data=None, smap=None, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent=parent)
        self.data = data # lista boolean vrijednosti
        self.smap = smap # status mapa

    def set_data_and_smap(self, lista, mapa):
        self.data = lista
        self.smap = mapa
        self.layoutChanged.emit()

    def rowCount(self, parent=QtCore.QModelIndex()):
        if isinstance(self.smap, dict):
            return math.ceil(len(list(self.smap.keys()))/8)
        else:
            return 0

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 8

    def flags(self, index):
        if index.isValid():
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def data(self, index, role):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        ind = row * 8 + col #indeks u listi
        if role == QtCore.Qt.DisplayRole:
            if ind in self.smap:
                return str(self.smap[ind])
        if role == QtCore.Qt.BackgroundColorRole:
            try:
                if self.data[ind] == True:
                    return QtGui.QBrush(QtGui.QColor(255, 0, 0, 80))
                elif self.data[ind] == False:
                    return QtGui.QBrush(QtGui.QColor(0, 255, 0, 80))
            except LookupError:
                return QtGui.QBrush(QtGui.QColor(255, 255, 255))
        if role == QtCore.Qt.ToolTipRole:
            try:
                description = str(self.smap[ind])
                check = str(self.data[ind])
                msg = '{0} : {1}'.format(description, check)
                return msg
            except LookupError:
                pass
