# -*- coding: utf-8 -*-
"""
Created on Fri Jan 23 12:01:49 2015

@author: User
"""

from PyQt4 import QtCore

###############################################################################
###############################################################################
class TreeItem(object):
    """
    Posebna klasa za tree strukturu.
    Posjeduje 3 bitna membera i hrpu metoda koje se trebaju brinuti da
    QtCore.QAbstractItemModel fonkcionira.
    
    self._parent --> referencira parent node (takodjer TreeItem objekt)
    self._childItems --> LISTA djece (svi child itemi su TreeItem objekti)
    self._data --> kontenjer koji sadrzi neke podatke (npr, lista, dict...)
    """
    def __init__(self, data, parent = None):
        self._parent = parent
        self._data = data
        self._childItems = []
        
        if self._parent != None:
            #sutomatski dodaj sebe u popis child objekata svog parenta
            self._parent._childItems.append(self)
###############################################################################
    def child(self, row):
        """
        vrati child za pozicije row
        """
        return self._childItems[row]
###############################################################################
    def childCount(self):
        """
        ukupan broj child itema
        """
        return len(self._childItems)
###############################################################################
    def childNumber(self):
        """
        vrati indeks pod kojim se ovaj objekt nalazi u listi djece
        parent objekta
        """
        if self._parent != None:
            return self._parent._childItems.index(self)
        return 0
###############################################################################
    def columnCount(self):
        """
        TreeItem objekt se inicijalizira sa "spremnikom" podataka
        ova funkcija vraca broj podataka u spremniku
        """
        return len(self._data)
###############################################################################
    def data(self, column):
        """
        funkcija koja dohvaca element iz "spremnika" podataka
        TODO! promjeni implementaciju ako se promjeni 'priroda' spremnika
        npr. ako je spremnik integer vrijednost ovo nece raditi
        """
        return self._data[column]
###############################################################################
    def parent(self):
        """
        vrati instancu parent objekta
        """
        return self._parent
###############################################################################
    def __repr__(self):
        """
        print() reprezentacija objekta
        TODO! promjeni implementaciju ako se promjeni 'priroda' spremnika
        npr. ako je spremnik integer vrijednost ovo nece raditi
        """
        return str(self.data(0))

###############################################################################
###############################################################################
class ModelDrva(QtCore.QAbstractItemModel):
    """
    Specificna implementacija QtCore.QAbstractItemModel, model nije editable!
    
    Za inicijalizaciju modela bitno je prosljediti root item neke tree strukture
    koja se sastoji od TreeItem instanci.
    """
    def __init__(self, data, parent = None):
        QtCore.QAbstractItemModel.__init__(self, parent)
        
        self.rootItem = data
###############################################################################
    def index(self, row, column, parent = QtCore.QModelIndex()):
        """
        funkcija vraca indeks u modelu za zadani red, stupac i parent
        """
        if parent.isValid() and parent.column() != 0:
            return QtCore.QModelIndex()
            
        parentItem = self.getItem(parent)
        childItem = parentItem.child(row)
        if childItem:
            #napravi index za red, stupac i child
            return self.createIndex(row, column, childItem)
        else:
            #vrati prazan QModelIndex
            return QtCore.QModelIndex()
###############################################################################
    def getItem(self, index):
        """
        funckija vraca objekt pod indeksom index, ili rootItem ako indeks 
        nije valjan
        """
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item

        return self.rootItem
###############################################################################
    def data(self, index, role = QtCore.Qt.DisplayRole):
        """
        primarni getter za vrijednost objekta
        za index i ulogu, vraca reprezentaciju view objektu
        
        TODO! ovaj dio ovisi o tipu "kontenjera" TreeItema, poziva se metoda
        TreeItema data. treba pripaziti da li je poziv metode smisleno srocen
        """
        if index.isValid() and role == QtCore.Qt.DisplayRole:
            item = self.getItem(index)
            if index.column() == 0:
                return item.data(0)
            elif index.column() == 1:
                return item.data(1)
            elif index.column() == 2:
                return item.data(2)
        else:
            return None
###############################################################################
    def rowCount(self, parent = QtCore.QModelIndex()):
        """
        vrati broj redaka (children objekata) za parent
        """
        parentItem = self.getItem(parent)
        return parentItem.childCount()
###############################################################################
    def columnCount(self, parent = QtCore.QModelIndex()):
        """
        vrati broj stupaca rootItema
        u principu, ova vrijednost odgovara broju stupaca u treeView widgetu
        te je jako bitna za metodu data ovog modela. Moguce ju je jednostavno
        hardcodirati na neku vrijednost.
        
        npr. return 1 (view ce imati samo jedan stupac (tree))
        npr. return 2 (view ce imati 2 stupca (tree, sto god odredis u metodi
        data da vrati u tom stupcu))
        
        TODO! pitanje je koliko informacija nam treba u view-u
        """
        return self.rootItem.columnCount()
###############################################################################
    def parent(self, index):
        """
        vrati parent od TreeItem objekta pod datim indeksom.
        Ako TreeItem name parenta, ili ako je indeks nevalidan, vrati
        defaultni QModelIndex (ostatak modela ga zanemaruje)
        """
        if not index.isValid():
            return QtCore.QModelIndex()
            
        childItem = self.getItem(index)
        parentItem = childItem.parent()
        if parentItem == self.rootItem:
            return QtCore.QModelIndex()
        else:
            return self.createIndex(parentItem.childNumber(), 0, parentItem)
            
###############################################################################
    def headerData(self, section, orientation, role):
        """
        headeri
        """
        #headeri = ['Stanica/komponenta', 'Mjerna Jedinica', 'Program mjerenja']
        headeri = ['Stanica/komponenta', 'Usporedno', 'Program mjerenja']
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return headeri[section]

        return None
###############################################################################
###############################################################################