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
    
    P.P.S. za inicijalizaciju su bitne 4 stvari
    1. grafInfo -> treba dati nested listu pomocnih grafova (inace je nested dictionary)
    2. kanali -> lista svih kanala koje je moguce izabrati (SO2, NO2...). Bitno za izbor kanala
    3. markeri ->lista svih markera koji ulaze u izbor, opisni ('Krug'...)
    4. linije ->lista svih stilova linija, opisni ('Dash-Dot'...)
    """
    def __init__(self, grafInfo = [], kanali = [], linije = [], markeri = [], parent = None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        
        #spremi ulaznu mapu u privatni member
        self.grafInfo = grafInfo
        #headeri tablice
        self.headeri = ['Kanal', 'Stil markera', 'Velicina markera', 'Stil linije', 'Sirina linije', 'Boja', 'Makni graf']
        #lista imena svih kanala
        self.kanali = kanali
        #lista imena svih tipova linija
        self.linije = linije
        #lista imena svih tipova markera
        self.markeri = markeri
        
        
    def rowCount(self, parent = QtCore.QModelIndex()):
        """
        Nuzna metoda za rad klase
        -vraca informaciju o broju redaka display djelu
        """
        return len(self.grafInfo)
    
    def columnCount(self, parent = QtCore.QModelIndex()):
        """
        Nuzna metoda za rad klase
        -vraca informaciju o broju stupaca display djelu
        """
        #hardcoded, samo 7 stupca
        #['Kanal', 'Stil markera', 'Velicina markera', 'Stil linije', 'Sirina linije', 'Boja', 'Makni graf']
        return 7
        
    def flags(self, index):
        """
        -vraca van stanje svakog indeksa u prikazu tablice.
        -za sada samo enabled i selectable
        -iskljucivo prikaz podataka
        """
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
    
    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """
        Metoda zaduzena za postavljanje novih vrijednosti u model
        ako ih krenemo editirati. Promjena kanala automatski mjenja label.
        Pormjena markera ili linije updatea model, promjena boje i remove
        grafa rade drugacije. Vidi u sublkasi QTableView-a tj. u klasama 
        koje delegiraju (mjenjaju) standardni editor svakog stupca (vidi
        dijalog1.py).
        """
        if not index.isValid():
            return False
        
        if role == QtCore.Qt.EditRole:
            row = index.row()
            col = index.column()
            if col == 0: #promjena kanala
                self.grafInfo[row][col] = value #promjeni kanal
                self.grafInfo[row][8] = value #promjeni i label
                return True
            elif col == 1:
                self.grafInfo[row][col] = value #promjeni stil markera
                return True
            elif col == 2:
                self.grafInfo[row][col] = value #promjeni size markera
                return True
            elif col == 3:
                self.grafInfo[row][col] = value #promjeni stil linije
                return True
            elif col == 4:
                self.grafInfo[row][col] = value #promjeni sirinu linije
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
                value = self.grafInfo[row][0] #stupac "Kanal"
            elif column == 1:
                value = self.grafInfo[row][1] #stupac "Stil markera"
            elif column == 2:
                value = self.grafInfo[row][2] #stupac "Velicina markera"
            elif column == 3:
                value = self.grafInfo[row][3] #stupac "Stil linije"
            elif column == 4:
                value = self.grafInfo[row][4] #stupac "Sirina linije"
            elif column ==5:
                value = 'Boja' #stupac "Boja"
            elif column ==6:
                value = 'Makni graf' #stupac "Makni graf" decorator ikona?

            return value
        
        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()
            if column == 0:
                value = self.grafInfo[row][0] #stupac "Kanal"
            elif column == 1:
                value = self.grafInfo[row][1] #stupac "Stil markera"
            elif column == 2:
                value = self.grafInfo[row][2] #stupac "Velicina markera"
            elif column == 3:
                value = self.grafInfo[row][3] #stupac "Stil linije"
            elif column == 4:
                value = self.grafInfo[row][4] #stupac "Sirina linije"
            elif column ==5:
                value = 'Boja' #stupac "Boja"
            elif column ==6:
                value = 'Makni graf' #stupac "Makni graf" decorator ikona?
            return value
            
        if role == QtCore.Qt.DecorationRole:
            row = index.row()
            column = index.column()
            if column == 0 or column == 5:
                #na stupcima 0 i 5 (kanal i boja)
                rgb = self.grafInfo[row][5]
                alpha = self.grafInfo[row][6]
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
                return self.headeri[section]
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
            self.grafInfo.insert(position, value)
                
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