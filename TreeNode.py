# -*- coding: utf-8 -*-
"""
Created on Tue Nov 18 09:59:51 2014

@author: User

"""
import sys
from PyQt4 import QtGui, QtCore, uic
import networking_funkcije
import agregator

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

    def child(self, row):
        """
        vrati child za pozicije row
        """
        return self._childItems[row]

    def childCount(self):
        """
        ukupan broj child itema
        """
        return len(self._childItems)

    def childNumber(self):
        """
        vrati indeks pod kojim se ovaj objekt nalazi u listi djece
        parent objekta
        """
        if self._parent != None:
            return self._parent._childItems.index(self)
        return 0

    def columnCount(self):
        """
        TreeItem objekt se inicijalizira sa "spremnikom" podataka
        ova funkcija vraca broj podataka u spremniku
        """
        return len(self._data)

    def data(self, column):
        """
        funkcija koja dohvaca element iz "spremnika" podataka
        TODO! promjeni implementaciju ako se promjeni 'priroda' spremnika
        npr. ako je spremnik integer vrijednost ovo nece raditi
        """
        return self._data[column]

    def parent(self):
        """
        vrati instancu parent objekta
        """
        return self._parent
    
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

    def rowCount(self, parent = QtCore.QModelIndex()):
        """
        vrati broj redaka (children objekata) za parent
        """
        parentItem = self.getItem(parent)
        return parentItem.childCount()
        
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
            
            
    def headerData(self, section, orientation, role):
        """
        headeri
        """
        headeri = ['Stanica/komponenta', 'Mjerna Jedinica', 'Program mjerenja']
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return headeri[section]

        return None
###############################################################################
###############################################################################
base5, form5 = uic.loadUiType('treeTest.ui')
class TreeTest(base5, form5):
    """
    Nazovimo ovo prototipom REST izbornika (gumbi?, treeView, kalendar, ??).
    
    Smisao je testiranje treeView - ModelDrva funkcionalnosti
    """
    def __init__(self, parent = None):
        super(base5, self).__init__(parent)
        self.setupUi(self)
        
        baza = "http://172.20.1.166:9090/SKZ-war/webresources/"
        resursi = {"siroviPodaci":"dhz.skz.rs.sirovipodaci", 
                   "programMjerenja":"dhz.skz.aqdb.entity.programmjerenja"}
                   
        self.wz = networking_funkcije.WebZahtjev(baza, resursi)
                
        self.model = self.napravi_model(baza, resursi)
        self.treeView.setModel(self.model)
        
        
        self.calendarWidget.activated.connect(self.get_mjerenje_datum) #doubleclick/enter
        self.treeView.activated.connect(self.get_mjerenje_datum) #doubleclick/enter
        
        #agregator        
        self.agreg = agregator.Agregator()
        
        #frejmovi
        self.frejm = None
        self.agFrejm = None
        
        
    def get_mjerenje_datum(self, x):
        """funkcija se poziva prilikom doubleclicka na valjani program mjerenja
        ili na datum u kalendaru"""

        #dohvacanje trenutno aktivnog datuma u kalendaru        
        qdan = self.calendarWidget.selectedDate() #dohvaca QDate objekt
        pdan = qdan.toPyDate() #convert u datetime.datetime python objekt
        dan = pdan.strftime('%Y-%m-%d') #transformacija u zadani string format
        
        #dohvacanje programa mjerenja
        ind = self.treeView.currentIndex() #dohvati trenutni aktivni indeks
        item = self.model.getItem(ind) #dohvati specificni objekt pod tim indeksom
        prog = item._data[2] #dohvati program mjerenja iz liste podataka
        
        if prog != None:
            output = (int(prog), dan)
            print('izabrana kombinacija: ', output)
            #poziv za dohvacanje frejma
            self.frejm = self.wz.get_sirovi(int(prog), dan)
            print(self.frejm.head())
        else:
            print('izaberi neki program mjerenja')
                        
    def napravi_model(self, baza, resursi):
        """
        komplicirana funkcija.. radi redom:
        2. posalji request REST servisu da dohvati sve programe mjerenja te
        prihvati dict sa informacijom stanica, mjerenje....
        3.prepisi tako dobiveni dict u tree strukturu baziranu na TreeItem
        objektima
        4. postavi tree strukturu u treeView widget
        """
        #dohvati sva mjerenja
        programMjerenja = self.wz.get_sve_programe_mjerenja()

        #ovisno o "grani", drugacije instanciramo objekt
        #[stanica/naziv mjerenja, None/mjerna jedinica, None/id mjerenja]
        
        #root objekt
        tree = TreeItem(['stanice', None, None], parent = None)
        #za svaku individualnu stanicu napravi TreeItem objekt, reference objekta spremi u dict
        stanice = {}
        for i in sorted(list(programMjerenja.keys())):
            stanica = programMjerenja[i]['postajaNaziv']
            if stanica not in stanice:
                stanice[stanica] = TreeItem([stanica, None, None], parent = tree)
        #za svako individualnu komponentu napravi TreeItem sa odgovarajucim parentom (stanica)
        for i in programMjerenja.keys():
            stanica = programMjerenja[i]['postajaNaziv'] #parent = stanice[stanica]
            komponenta = programMjerenja[i]['komponentaNaziv']
            mjernaJedinica = programMjerenja[i]['komponentaMjernaJedinica']
            #komponentaId = programMjerenja[i]['komponentaId']
            data = [komponenta, mjernaJedinica, i]
            TreeItem(data, parent = stanice[stanica]) #kreacija TreeItem objekta
        
        mod = ModelDrva(tree) #napravi model
        
        return mod
###############################################################################
###############################################################################

if __name__ == '__main__':
    #bitno za web zahtjev (networking_funkcije.py)
    baza = "http://172.20.1.166:9090/SKZ-war/webresources/"
    resursi = {"siroviPodaci":"dhz.skz.rs.sirovipodaci", 
                "programMjerenja":"dhz.skz.aqdb.entity.programmjerenja"}
    
    app = QtGui.QApplication(sys.argv)
     
    tt = TreeTest()
#    mod = tt.napravi_model(baza, resursi)
#    tt.postavi_model(mod)
    tt.show()
    
    sys.exit(app.exec_())