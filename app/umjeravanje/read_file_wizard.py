# -*- coding: utf-8 -*-
"""
Created on Wed Apr 29 12:15:30 2015

@author: DHMZ-Milic
"""
import sys
import os
from PyQt4 import QtGui, QtCore
import pandas as pd

class CarobnjakZaCitanjeFilea(QtGui.QWizard):
    """
    Wizard dijalog klasa za ucitavanje fileova za umjeravanje
    #TODO! treba mi konfig sa bitnim podacima o uredjajima....
    """
    def __init__(self, parent=None):
        QtGui.QWizard.__init__(self, parent)
        self.setWizardStyle(QtGui.QWizard.ModernStyle)
        self.setMinimumSize(600,600)
        self.setWindowTitle("Read config file wizard")

        self.P1 = Page1Wizarda(self)
        self.P2 = Page2Wizarda()
        self.P3 = Page3Wizarda()

        self.setPage(1, self.P1)
        self.setPage(2, self.P2)
        self.setPage(3, self.P3)
        self.setStartId(1)

    def get_frejm(self):
        stupci = self.P3.model.cols
        stupci = [i for i in stupci if i != 'None'] #izbaci None iz liste
        return self.P3.df[stupci]

class Page1Wizarda(QtGui.QWizardPage):
    def __init__(self, parent = None):
        QtGui.QWizard.__init__(self, parent)
        self.setTitle('Izaberi file')
        self.setSubTitle('Browse ili direktno upisi path do filea')

        self.lineEditPath = QtGui.QLineEdit()
        self.buttonBrowse = QtGui.QPushButton('Browse')
        self.buttonBrowse.clicked.connect(self.locate_file)

        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.lineEditPath)
        layout.addWidget(self.buttonBrowse)
        self.setLayout(layout)

        """
        --> registriram sadrzaj widgeta self.lineEditPath kao 'filepath'
        --> dostupan je svim drugim stanicama wizarda
        --> * na kraju stringa oznacava mandatory field
        """
        self.registerField('filepath*', self.lineEditPath)

    def initializePage(self):
        """
        overloaded funkcija koja odradjuje inicijalizaciju prilikom prvog prikaza
        """
        self.lineEditPath.clear()

    def locate_file(self):
        """
        Funkcija je povezana sa gumbom browse, otvara file dijalog i sprema
        izabrani path do konfiguracijske datoteke u self.lineEditPath widget
        """
        self.lineEditPath.clear()
        path = QtGui.QFileDialog.getOpenFileName(parent=self,
                                         caption="Open file",
                                         directory="",
                                         filter="CSV files (*.csv)")
        self.lineEditPath.setText(str(path))

    def validatePage(self):
        """
        funkcija se pokrece prilikom prelaza na drugi wizard page.
        Funkcija mora vratiti boolean. True omogucava ucitavanje druge stranice
        wizarda, False blokira prijelaz.
        """
        path = str(self.lineEditPath.text())
        #provjeri da li je file path validan prije nastavka
        if not os.path.isfile(path):
            msg = 'File ne postoji. Provjerite path za pogreske prilikom unosa.'
            QtGui.QMessageBox.information(self, 'Problem.', msg)
            return False
        return True


class Page2Wizarda(QtGui.QWizardPage):
    """
    Stranica wizarda za izbor uredjaja i postaje
    """
    def __init__(self, parent = None):
        QtGui.QWizard.__init__(self, parent)
        self.setTitle('Izbor postaje i uredjaja')
        self.setSubTitle('Provjeri izbor postaje i uredjaja prije nastavka.')

        #TODO! privremeni placeholder dok ne smislim konfig
        self.svePostaje = {'postaja1': ['uredjaj1', 'uredjaj2', 'uredjaj3'],
                           'postaja2': ['uredjaj4', 'uredjaj5', 'uredjaj6'],
                           'postaja3': ['uredjaj7', 'uredjaj8', 'uredjaj9']}

        self.comboPostaje = QtGui.QComboBox()
        self.comboUredjaji = QtGui.QComboBox()
        self.labelPostaje = QtGui.QLabel('Postaje: ')
        self.labelUredjaji = QtGui.QLabel('Uredjaji: ')

        #komplikacija broj 1, jednostavniji share podataka izmedju stranica widgeta
        self.postaja = QtGui.QLineEdit()
        self.postaja.setVisible(False)
        self.uredjaj = QtGui.QLineEdit()
        self.uredjaj.setVisible(False)

        layoutPostaje = QtGui.QHBoxLayout()
        layoutUredjaji = QtGui.QHBoxLayout()
        layout = QtGui.QVBoxLayout()
        layoutPostaje.addWidget(self.labelPostaje)
        layoutPostaje.addWidget(self.comboPostaje)
        layoutPostaje.addWidget(self.postaja)
        layoutUredjaji.addWidget(self.labelUredjaji)
        layoutUredjaji.addWidget(self.comboUredjaji)
        layoutUredjaji.addWidget(self.uredjaj)
        layout.addLayout(layoutPostaje)
        layout.addLayout(layoutUredjaji)
        self.setLayout(layout)

        self.comboPostaje.currentIndexChanged.connect(self.change_postaja)
        self.comboUredjaji.currentIndexChanged.connect(self.change_uredjaj)

        self.registerField('postaja', self.postaja)
        self.registerField('uredjaj', self.uredjaj)

    def change_uredjaj(self, x):
        """
        Promjena unutar comboboxa uredjaj
        """
        currentUredjaj = self.comboUredjaji.itemText(x)
        self.uredjaj.clear()
        self.uredjaj.setText(currentUredjaj)

    def change_postaja(self, x):
        """
        Promjena postaje dinamicki mjenja sadrzaj comboboxa sa uredjajima
        """
        currentPostaja = self.comboPostaje.itemText(x)
        self.postaja.clear()
        self.postaja.setText(currentPostaja)
        self.comboUredjaji.clear()
        self.comboUredjaji.addItems(sorted(list(self.svePostaje[currentPostaja])))

    def initializePage(self):
        """
        Funkcija se poziva prilikom inicijalizacije stranice. Treba populirati
        comboboxeve i postaviti izbor
        """
        try:
            self.comboPostaje.addItems(sorted(list(self.svePostaje.keys())))
            currentPostaja = self.comboPostaje.currentText()
            self.postaja.clear()
            self.postaja.setText(currentPostaja)
            self.comboUredjaji.clear()
            self.comboUredjaji.addItems(sorted(list(self.svePostaje[currentPostaja])))
            self.uredjaj.clear()
            self.uredjaj.setText(self.comboUredjaji.currentText())
        except KeyError:
            msg = 'Podaci sa postajama i uredjajima nisu ucitani.'
            QtGui.QMessageBox.information(self, 'Problem.', msg)


class Page3Wizarda(QtGui.QWizardPage):
    def __init__(self, parent = None):
        """
        Inicijalne postavke i layout
        """
        QtGui.QWizard.__init__(self, parent)
        self.setTitle('Stranica 3')

        self.tableView = QtGui.QTableView()
        self.tableView.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.tableView.setWordWrap(True)
        self.tableView.horizontalHeader().setVisible(False)
        self.tableView.setMouseTracking(True)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.tableView)
        self.setLayout(layout)

    def initializePage(self):
        """
        Funkcija se pokrece prilikom inicijalizacije stranice
        """
        self.path = self.field('filepath')
        self.postaja = self.field('postaja')
        self.uredjaj = self.field('uredjaj')
        txt = " ".join(['Podaci za postaju', self.postaja, 'i uredjaj', self.uredjaj])
        self.setSubTitle(txt)
        try:
            self.df = self.read_csv_file(self.path)
            self.model = BaseFrejmModel(frejm=self.df)
            #popis stupaca
            stupci = [str(i) for i in self.df.columns]
            stupci.append('None')
            self.delegat = ComboBoxDelegate(stupci = stupci, parent=self.tableView)
            self.tableView.setModel(self.model)
            self.tableView.setItemDelegateForRow(0, self.delegat)
            for col in range(len(self.df.columns)):
                self.tableView.openPersistentEditor(self.model.index(0, col))
			"""
			Prilikom rada, tablica se nece updateati sve dokle god je editor aktivan.
			Potrebno je promjeniti "fokus"" sa comboboxa (tab, scoll, select bilo kojeg elementa tablice...)
			"""

        except OSError as err:
            print('error kod citanja filea:\n'+str(err))

    def validatePage(self):
        """
        Validator za stranicu. return True ako je sve u redu, inace vrati False.
        """
        test1 = [i for i in self.model.cols if i != 'None']
        if len(test1) > 0:
            return True
        else:
            msg = 'Barem jedan stupac mora biti izabran.'
            QtGui.QMessageBox.information(self, 'Problem.', msg)
            return False

    def read_csv_file(self, path):
        """
        reader csv filea
        """
        frejm = pd.read_csv(path,
                            index_col=0,
                            parse_dates=[0],
                            dayfirst=True,
                            header=0,
                            sep=",",
                            encoding="iso-8859-1")
        return frejm

class ComboBoxDelegate(QtGui.QItemDelegate):
    def __init__(self, stupci=['None'], parent=None):
        QtGui.QItemDelegate.__init__(self, parent=parent)
        self.stupci = stupci

    def createEditor(self, parent, option, index):
        """
        return editor widget

        parent
        --> argument sluzi da stvoreni editor ne bude "garbage collected" (parent drzi referencu na njega)
        option
        --> Qt style opcije... nebitno (ali mora biti kao positional argument)
        index
        --> indeks elementa iz tablice (veza sa modelom)
        """
        editor = QtGui.QComboBox(parent=parent)
        editor.clear()
        editor.addItems(self.stupci)
        editor.setFocusPolicy(QtCore.Qt.StrongFocus)
        return editor

    def setEditorData(self, editor, index):
        """
        Inicijalizacija editora sa podacima, setup izgleda editora
        """
        col = index.column()
        value = index.model().cols[col]
        ind = editor.findText(value)
        editor.setCurrentIndex(ind)

    def setModelData(self, editor, model, index):
        """
        Nakon kraja editiranja, metoda postavlja novo unesenu vrijednost u model
        """
        data = str(editor.currentText())
        model.setData(index, data)

class BaseFrejmModel(QtCore.QAbstractTableModel):
    """
    Definiranje qt modela za qt table view klase.
    Osnova modela ce biti pandas dataframe.
    Must reimplement:
        rowCount()
        columnCount()
        data()
        headerData()
    Implemented by default:
        parent()
        index()
    """
    def __init__(self, frejm=pd.DataFrame(), parent=None):
        """
        Initialize with pandas dataframe with data
        """
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.dataFrejm = frejm
        self.cols = list(self.dataFrejm.columns)

    def rowCount(self, parent=QtCore.QModelIndex()):
        """
        MUST BE IMPLEMENTED.
        Return number of rows of pandas dataframe
        """
        return len(self.dataFrejm)+1
        #return min(15, len(self.dataFrejm))+1 #prikaz max 15 vrijednosti u tablici

    def columnCount(self, parent=QtCore.QModelIndex()):
        """
        MUST BE IMPLEMENTED
        Return number of columns of pandas dataframe. (add one for time index)
        """
        return len(self.dataFrejm.columns)

    def flags(self, index):
        """
        Flags each item in table as enabled and selectable
        """
        if index.isValid():
            if index.row() == 0:
                return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
            else:
                return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """
        must be enabled for editable models
        """
        if not index.isValid():
            return False

        row = index.row()
        col = index.column()
        if role == QtCore.Qt.EditRole and row == 0:
            self.cols[col] = str(value)
            """emit sigala da je doslo do promjene u modelu. View se nece
            updateati sve dokle god je fokus na comboboxu (smatra da editing
            nije gotov)."""
            self.dataChanged.emit(index, index)
            return True
        else:
            return False

    def data(self, index, role):
        """
        MUST BE IMPLEMENTED.
        Return value for each index and role
        """
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        if row == 0:
            if role == QtCore.Qt.DisplayRole:
                return self.cols[col]
        else:
            if role == QtCore.Qt.DisplayRole:
                stupac = self.index(0, col).data()
                for i in range(len(self.dataFrejm.columns)):
                    if self.dataFrejm.columns[i] == stupac:
                        return round(float(self.dataFrejm.iloc[row-1, i]),2)
                return None

    def headerData(self, section, orientation, role):
        """
        Sets the headers of the table...
        """
        if orientation == QtCore.Qt.Vertical:
            if role == QtCore.Qt.DisplayRole:
                if section == 0:
                    return 'Vrijeme'
                else:
                    return str(self.dataFrejm.index[section-1])

class TempWindow(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setMinimumSize(400,400)

        layout = QtGui.QHBoxLayout()
        self.gumb = QtGui.QPushButton('pressme')
        layout.addWidget(self.gumb)
        self.setLayout(layout)

        self.gumb.clicked.connect(self.prikazi_wizard)

    def prikazi_wizard(self):
        self.wiz = CarobnjakZaCitanjeFilea()
        self.wiz.exec_() # -->pokretanje wizarda

        frejm=self.wiz.get_frejm() # -->output frejm
        print(frejm.head())

if __name__ == '__main__':
    """
    Token app, otvara prozor sa jednim gumbom koji pokrece wizard
    nakon sto wizard zavrsi, printa prvih 5 redova frejma.

    Nije 100% gotovo, nedostaje:
    -inicijalizacija sa postajama / uredjajima...
    -update nakon promjene malo zafrkava
    """
    app = QtGui.QApplication(sys.argv)
    widgi = TempWindow()
    widgi.show()
    sys.exit(app.exec_())