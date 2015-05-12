# -*- coding: utf-8 -*-
"""
Created on Wed Apr 29 12:15:30 2015

@author: DHMZ-Milic
"""
import sys
import os
from PyQt4 import QtGui, QtCore
import pandas as pd
import requests
import xml.etree.ElementTree as ET

class RESTZahtjev(object):
    """
    TODO!
    -Ova klasa sluzi za komunikaciju sa rest servisom.
    """

    def __init__(self):
        self.auth = ("","")
        self.svePostajeUrl = 'http://172.20.1.166:9090/SKZ-war/webresources/dhz.skz.aqdb.entity.postaja'
        self.sviUredjajiUrl = 'http://172.20.1.166:9090/SKZ-war/webresources/dhz.skz.aqdb.entity.uredjaj'
        self.uredjajUrl = 'http://172.20.1.166:9090/SKZ-war/webresources/uredjaj'
        #self.uredjajUrl = 'http://SKZ-war/webresources/uredjajnakvadrat' #namjerno kriv

    def set_auth(self, x):
        self.auth = x

    def get_sve_postaje(self):
        r = requests.get(self.svePostajeUrl, auth=self.auth)
        assert r.ok is True, "Bad response, status code:{0}, url:{1}".format(r.status_code, r.url)
        return self.parse_xml_postaje(r.text)

    def get_svi_uredjaji(self):
        r = requests.get(self.sviUredjajiUrl, auth=self.auth)
        assert r.ok is True, "Bad response, status code:{0}, url:{1}".format(r.status_code, r.url)
        return self.parse_xml_uredjaji(r.text)

    def get_lokaciju_uredjaja(self, serial):
        url = "/".join([self.uredjajUrl, str(serial),'lokacija'])
        r = requests.get(url, auth=self.auth)
        assert r.ok is True, "Bad response, status code:{0}, url:{1}".format(r.status_code, r.url)
        return self.parse_xml_lokacija_uredjaja(r.text)

    def get_komponente_uredjaja(self, serial):
        url = "/".join([self.uredjajUrl, str(serial),'komponente'])
        r = requests.get(url, auth=self.auth)
        assert r.ok is True, "Bad response, status code:{0}, url:{1}".format(r.status_code, r.url)
        return self.parse_xml_komponenti_uredjaja(r.text)

    def parse_xml_komponenti_uredjaja(self, xmlstring):
        root = ET.fromstring(xmlstring)
        rezultat = []
        for formula in root:
            val = str(formula.find('formula').text)
            rezultat.append(val)
        return rezultat

    def parse_xml_lokacija_uredjaja(self, xmlstring):
        root = ET.fromstring(xmlstring)
        return str(root.find('nazivPostaje').text)

    def parse_xml_postaje(self, xmlstring):
        rezultat = []
        root = ET.fromstring(xmlstring)
        for postaja in root:
            naziv = str(postaja.find('nazivPostaje').text)
            rezultat.append(naziv)
        return rezultat

    def parse_xml_uredjaji(self, xmlstring):
        rezultat = []
        root = ET.fromstring(xmlstring)
        for uredjaj in root:
            serial = str(uredjaj.find('serijskaOznaka').text)
            rezultat.append(serial)
        return rezultat
################################################################################
################################################################################
class CarobnjakZaCitanjeFilea(QtGui.QWizard):
    """
    Wizard dijalog klasa za ucitavanje fileova za umjeravanje
    """
    def __init__(self, parent=None, rest=None):
        QtGui.QWizard.__init__(self, parent)

        self.rest = rest
        self.komponente = []

        self.setWizardStyle(QtGui.QWizard.ModernStyle)
        self.setMinimumSize(600,600)
        self.setWindowTitle("Read config file wizard")

        self.setOption(QtGui.QWizard.IndependentPages, on=False)

        self.P1 = Page1Wizarda(parent=self)
        self.P2 = Page2Wizarda(parent=self)
        self.P3 = Page3Wizarda(parent=self)

        self.setPage(1, self.P1)
        self.setPage(2, self.P2)
        self.setPage(3, self.P3)
        self.setStartId(1)



    def set_komponente(self, lista):
        self.komponente = lista
        if not 'None' in self.komponente:
            self.komponente.append('None')

    def get_frejm(self):
        outFrejm = pd.DataFrame()
        stupci = self.P3.model.cols
        for i in range(len(stupci)):
            if stupci[i] != 'None':
                outFrejm[stupci[i]] = self.P3.df.iloc[:,i]
        return outFrejm
################################################################################
################################################################################
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
################################################################################
################################################################################
class Page2Wizarda(QtGui.QWizardPage):
    """
    Stranica wizarda za izbor uredjaja i postaje
    """
    def __init__(self, parent = None):
        QtGui.QWizard.__init__(self, parent)
        self.setTitle('Izbor postaje i uredjaja')
        self.setSubTitle('Provjeri izbor postaje i uredjaja prije nastavka.')
        self.svePostaje = []
        self.sviUredjaji = []

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
        try:
            #lokacija sa resta
            lokacija = self.wizard().rest.get_lokaciju_uredjaja(currentUredjaj)
            ind = self.comboPostaje.findText(lokacija)
            self.comboPostaje.setCurrentIndex(ind)
            #komponente sa resta
            self.komponente = self.wizard().rest.get_komponente_uredjaja(currentUredjaj)
        except AssertionError as err1:
            msg = 'Nije moguce dohvatiti podatke o postajama i uredjajima sa REST servisa.'
            msg = "\n".join([msg, str(err1)])
            QtGui.QMessageBox.information(self, 'Problem.', msg)
            self.wizard().done(0) #close wizard
        except requests.exceptions.RequestException as err2:
            msg = 'Nije moguce dohvatiti podatke o postajama i uredjajima sa REST servisa.'
            msg = "\n".join([msg, str(err2)])
            QtGui.QMessageBox.information(self, 'Problem.', msg)
            self.wizard().done(0) #close wizard

        self.uredjaj.clear()
        self.uredjaj.setText(currentUredjaj)

    def change_postaja(self, x):
        """
        Promjena postaje dinamicki mjenja sadrzaj comboboxa sa uredjajima
        """
        currentPostaja = self.comboPostaje.itemText(x)
        self.postaja.clear()
        self.postaja.setText(currentPostaja)

    def initializePage(self):
        """
        Funkcija se poziva prilikom inicijalizacije stranice. Treba populirati
        comboboxeve i postaviti izbor
        """
        try:
            self.svePostaje = self.wizard().rest.get_sve_postaje()
            self.sviUredjaji = self.wizard().rest.get_svi_uredjaji()
        except AssertionError as err1:
            msg = 'Nije moguce dohvatiti podatke o postajama i uredjajima sa REST servisa.'
            msg = "\n".join([msg, str(err1)])
            QtGui.QMessageBox.information(self, 'Problem.', msg)
            self.wizard().done(0) #close wizard
        except requests.exceptions.RequestException as err2:
            msg = 'Nije moguce dohvatiti podatke o postajama i uredjajima sa REST servisa.'
            msg = "\n".join([msg, str(err2)])
            QtGui.QMessageBox.information(self, 'Problem.', msg)
            self.wizard().done(0) #close wizard
        #clear, set iteme u comboboxeve
        self.comboPostaje.blockSignals(True)
        self.comboPostaje.clear()
        self.comboPostaje.addItems(sorted(self.svePostaje))
        self.comboPostaje.blockSignals(False)
        self.comboUredjaji.blockSignals(True)
        self.comboUredjaji.clear()
        self.comboUredjaji.addItems(sorted(self.sviUredjaji))
        self.comboUredjaji.blockSignals(False)
        ###UREDJAJ COMBO###
        #pokusaj naci serial iz imena filea
        serial = self.parse_filename()
        #ako je serial pronadjen postavi ga kao defaultni izbor u comboboxu
        if serial != None:
            ind = self.comboUredjaji.findText(serial)
            self.comboUredjaji.setCurrentIndex(ind)
        #clear & set hidden lineEdit widget - hack1
        self.uredjaj.clear()
        self.uredjaj.setText(self.comboUredjaji.currentText())

        ###POSTAJA COMBO###
        #dohvati trenutni izbor uredjaja
        currentUredjaj = str(self.comboUredjaji.currentText())
        #pokusaj za taj uredjaj naci komponente i lokaciju
        try:
            #lokacija sa resta
            lokacija = self.wizard().rest.get_lokaciju_uredjaja(currentUredjaj)
            #set lokaciju
            ind = self.comboPostaje.findText(lokacija)
            self.comboPostaje.setCurrentIndex(ind)
            #komponente sa resta
            komponente = self.wizard().rest.get_komponente_uredjaja(currentUredjaj)
            self.wizard().set_komponente(komponente)
        except AssertionError as err1:
            msg = 'Nije moguce dohvatiti podatke o postajama i uredjajima sa REST servisa.'
            msg = "\n".join([msg, str(err1)])
            QtGui.QMessageBox.information(self, 'Problem.', msg)
            self.wizard().done(0)
        except requests.exceptions.RequestException as err2:
            msg = 'Nije moguce dohvatiti podatke o postajama i uredjajima sa REST servisa.'
            msg = "\n".join([msg, str(err2)])
            QtGui.QMessageBox.information(self, 'Problem.', msg)
            self.wizard().done(0)
        #clear & set hidden lineEdit widget - hack1
        self.postaja.clear()
        self.postaja.setText(self.comboPostaje.currentText())


    def parse_filename(self):
        """
        Pokusaj pronalaska stanice i uredjaja iz naziva filea
        """
        fileName = os.path.split(self.field('filepath'))[1]
        for serial in self.sviUredjaji:
            if serial in fileName:
                return str(serial)
################################################################################
################################################################################
class Page3Wizarda(QtGui.QWizardPage):
    def __init__(self, parent = None):
        """
        Inicijalne postavke i layout
        """
        QtGui.QWizard.__init__(self, parent)
        self.setTitle('Stranica 3')
        self.setSubTitle('Izaberite u komponente')

        self.tableView = QtGui.QTableView()
        self.tableView.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.tableView.setWordWrap(True)
        #self.tableView.horizontalHeader().setVisible(False)
        self.tableView.setMouseTracking(True)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.tableView)
        self.setLayout(layout)

    def dinamicki_update_opcija_comboa(self, ind):
        """
        Pomocna metoda za promjenu popisa itema unutar comboboxa. Na ovu metodu su
        spojeni svi comboboxevi i pozivaju ju prilikom promjene trenutno aktivnog
        indeksa.
        """
        self.setMogucih = set(self.mjerenja)
        kutije = []
        for i in range(self.model.columnCount()):
            kutije.append(self.tableView.indexWidget(self.model.index(0, i)))
        for combo in kutije:
            #pronadji listu ostalih comboboxeva
            x = [kutije[i] for i in range(len(kutije)) if kutije[i] != combo]
            #pozovi na update popisa
            self.update_sadrzaj_comboboxa(combo, x, self.setMogucih)

    def update_sadrzaj_comboboxa(self, combo, ostali, moguci):
        """
        pomocna metoda za promjenu popisa itema unutar comboboxa
        """
        combo.blockSignals(True)
        #zapamti trenutni Izbor
        trenutni = combo.currentText()
        #pronadji koristene u drugim comboima
        used = set()
        for item in ostali:
            used.add(item.currentText())
        if 'None' in used:
            used.remove('None')
        dozvoljeni = moguci.difference(used)
        #clear starog comboa
        combo.clear()
        #dodavanje novog popisa
        combo.addItems(sorted(list(dozvoljeni)))
        #reset na pocetnu vrijednosti
        ind = combo.findText(trenutni)
        combo.setCurrentIndex(ind)
        combo.blockSignals(False)

    def initializePage(self):
        """
        Funkcija se pokrece prilikom inicijalizacije stranice
        """
        self.mjerenja = self.wizard().komponente
        self.path = self.field('filepath')
        self.postaja = self.field('postaja')
        self.uredjaj = self.field('uredjaj')

        txt = " ".join(['Podaci za postaju', self.postaja, 'i uredjaj', self.uredjaj])
        self.setSubTitle(txt)
        try:
            self.df = self.read_csv_file(self.path)
            self.model = BaseFrejmModel(frejm=self.df)
            self.delegat = ComboBoxDelegate(stupci = self.mjerenja, parent=self.tableView)
            self.tableView.setModel(self.model)
            self.tableView.setItemDelegateForRow(0, self.delegat)
            for col in range(len(self.df.columns)):
                self.tableView.openPersistentEditor(self.model.index(0, col))
                self.tableView.indexWidget(self.model.index(0, col)).currentIndexChanged.connect(self.dinamicki_update_opcija_comboa)
        except OSError as err:
            msg = 'error kod citanja filea: {0}\n'.format(str(err))
            QtGui.QMessageBox.information(self, 'Problem.', msg)
            self.wizard().done(0)

    def validatePage(self):
        """
        Validator za stranicu. return True ako je sve u redu, inace vrati False.

        -svi nazivi stupaca moraju biti unikatni (osim 'None')
        -mora biti barem jedan stupac
        """
        izabraniStupci = [i for i in self.model.cols if i != 'None']
        izabraniStupci = [i for i in izabraniStupci if i != '']
        setIzabranih = set(izabraniStupci)

        if len(izabraniStupci) > 0:
            if len(setIzabranih) == len(izabraniStupci):
                return True
            else:
                msg = 'Isti naziv je koristen na vise stupaca. Naziv se smije koristiti samo jednom.'
                QtGui.QMessageBox.information(self, 'Problem.', msg)
                return False
        else:
            msg = 'Barem jedan stupac mora biti izabran za nastavak.'
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
################################################################################
################################################################################
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
        editor.addItems(sorted(self.stupci))
        ind = editor.findText('None')
        editor.setCurrentIndex(ind)
        editor.setFocusPolicy(QtCore.Qt.StrongFocus)
        return editor

    def setEditorData(self, editor, index):
        """
        Inicijalizacija editora sa podacima, setup izgleda editora
        """
        pass

    def setModelData(self, editor, model, index):
        """
        Nakon kraja editiranja, metoda postavlja novo unesenu vrijednost u model
        """
        data = str(editor.currentText())
        model.setData(index, data)
################################################################################
################################################################################
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
        self.cols = ['None' for i in range(len(frejm.columns))]

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
                return round(float(self.dataFrejm.iloc[row-1, col]),2)

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
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                return str(self.dataFrejm.columns[section])
################################################################################
################################################################################
class TempWindow(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setMinimumSize(400,400)

        self.rest = RESTZahtjev()
        self.rest.set_auth(("t1","t1"))


        layout = QtGui.QHBoxLayout()
        self.gumb = QtGui.QPushButton('pressme')
        layout.addWidget(self.gumb)
        self.setLayout(layout)

        self.gumb.clicked.connect(self.prikazi_wizard)

    def prikazi_wizard(self):
        self.wiz = CarobnjakZaCitanjeFilea(rest=self.rest)
        ok = self.wiz.exec_() # -->pokretanje wizarda (ok je sattus odgovora dijaloga 1 ili 0)
        if ok:
            frejm=self.wiz.get_frejm() # -->output frejm
            print(frejm.head())
################################################################################
################################################################################
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