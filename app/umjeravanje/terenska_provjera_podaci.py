# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 11:08:19 2015

@author: DHMZ-Milic
"""
from PyQt4 import QtGui, QtCore, uic
import pandas as pd
import numpy as np

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

    def rowCount(self, parent=QtCore.QModelIndex()):
        """
        MUST BE IMPLEMENTED.
        Return number of rows of pandas dataframe
        """
        return len(self.dataFrejm)

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
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def data(self, index, role):
        """
        MUST BE IMPLEMENTED.
        Return value for each index and role
        """
        print('krivo sublkasana klasa')
        raise NotImplemented


    def headerData(self, section, orientation, role):
        """
        Sets the headers of the table...
        """
        if role == QtCore.Qt.DisplayRole: # "is" comparison ne radi
            if orientation == QtCore.Qt.Horizontal:
                return self.dataFrejm.columns[section]
            if orientation == QtCore.Qt.Vertical: # "is" comparison ne radi
                return str(self.dataFrejm.index[section])


class SiroviFrejmModel(BaseFrejmModel):
    """
    Klasa modela za prikaz SVIH 'sirovih' podataka preuzetih is csv filea.
    """
    def __init__(self, frejm=pd.DataFrame(), parent=None):
        BaseFrejmModel.__init__(self, frejm=frejm, parent=parent)
        self.izabraniPocetak = None

    def data(self, index, role):
        """
        MUST BE IMPLEMENTED.
        Return value for each index and role
        """
        if not index.isValid():
            return None

        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            col = index.column()
            return float(self.dataFrejm.iloc[row, col])

        if role == QtCore.Qt.BackgroundColorRole:
            if self.izabraniPocetak is not None and index.row() >= self.izabraniPocetak:
                return QtGui.QBrush(QtGui.QColor(0, 25, 220, 80))
            else:
                return QtGui.QBrush(QtGui.QColor(255, 255, 255, 255))

    def set_izabrani_pocetak_za_umjeravanje(self, index):
        """
        Pomocna funkcija, sluzi kao setter izabranog reda u tablici.
        Ulazni parametrar je QModelIndex(), od kojega samo zapamtimo broj
        redka.
        """
        self.izabraniPocetak = index.row()


class WorkingFrejmModel(BaseFrejmModel):
    """
    Implementacija modela za 3 minutne srednjake
    """
    def __init__(self, frejm=pd.DataFrame(), parent=None, tocke=None):
        BaseFrejmModel.__init__(self, frejm=frejm, parent=parent)
        self.tocke = tocke #enum raspona za pojedine tocke

    def data(self, index, role):
        """
        MUST BE IMPLEMENTED.
        Return value for each index and role

        color tocke: 15, 15, 10, 10, 10
        """
        if not index.isValid():
            return None

        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            col = index.column()
            return float(self.dataFrejm.iloc[row, col])

        if role == QtCore.Qt.BackgroundColorRole:
            if index.row() in self.tocke.tocka1.value:
                return QtGui.QBrush(QtGui.QColor(0, 25, 220, 80))
            if index.row() in self.tocke.tocka2.value:
                return QtGui.QBrush(QtGui.QColor(0, 220, 25, 80))
            if index.row() in self.tocke.tocka3.value:
                return QtGui.QBrush(QtGui.QColor(0, 25, 220, 80))
            if index.row() in self.tocke.tocka4.value:
                return QtGui.QBrush(QtGui.QColor(0, 220, 25, 80))
            if index.row() in self.tocke.tocka5.value:
                return QtGui.QBrush(QtGui.QColor(0, 25, 220, 80))

BASE2, FORM2 = uic.loadUiType('terenska_provjera_podaci.ui')
class TerenskaProvjeraPodaci(BASE2, FORM2):
    """
    Klaza sa ucitavanje sirovih podataka i prikaz

    MEMBERI:
    QPushButton
        self.buttonReadCSV --> ucitavanje csv filea preko dijaloga
    QTableView
        self.tableViewSirovi --> prikaz sirovih podataka ucitanih sa filea
        self.tableViewTocke --> prikaz agregiranih tocaka za umjeravanje
    """
    def __init__(self, parent=None, tocke=None):
        super(BASE2, self).__init__(parent)
        self.setupUi(self)
        self.tocke = tocke #enum raspona za pojedine tocke
        self.izabraniPocetak = None #QtModel index od kojega se koriste podaci

        #pandas datafrejmovi
        self.siroviFrejm = pd.DataFrame()
        self.workingFrejm = pd.DataFrame()
        self.siroviFrejmModel = None
        self.workingFrejmModel = None

        #QtableView initial setup
        self.tableViewSirovi.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tableViewSirovi.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.tableViewSirovi.setWordWrap(True)
        self.tableViewTocke.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tableViewTocke.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.tableViewTocke.setWordWrap(True)

        #connections
        self.buttonReadCSV.clicked.connect(self.make_model_from_csv)
        self.tableViewSirovi.activated.connect(self.echo_click)

    def make_model_from_csv(self):
        """
        Ucitaj csv file, inicijaliziraj data model za prikaz
        """
        #reset views
        self.izabraniPocetak = None
        self.tableViewSirovi.setModel(BaseFrejmModel())
        self.tableViewTocke.setModel(BaseFrejmModel())
        #get file
        try:
            self.siroviFrejm = self.citaj_csv_file()
            self.siroviFrejmModel = SiroviFrejmModel(frejm=self.siroviFrejm)
            #set model to view
            self.tableViewSirovi.setModel(self.siroviFrejmModel)
        except Exception as err:
            QtGui.QMessageBox.information(self, 'Problem prilikom rada', str(err))

    def citaj_csv_file(self):
        """
        Otvori dialog za izbor csv filea, ucitaj podatke u pandas dataframe i
        vrati dataframe.
        """
        path = QtGui.QFileDialog.getOpenFileName(parent=self,
                                                 caption="Open csv file",
                                                 directory="",
                                                 filter="CSV files (*.csv)")
        frejm = pd.read_csv(path,
                            index_col=0,
                            parse_dates=[0],
                            dayfirst=True,
                            header=0,
                            sep=",",
                            encoding="iso-8859-1")
        return frejm

    def echo_click(self, index):
        """
        test function
        """
        #informiraj model da je pocetak izabran
        self.siroviFrejmModel.set_izabrani_pocetak_za_umjeravanje(index)
        #model treba emitirati signal da view shvati da se view treba updateati
        self.siroviFrejmModel.layoutChanged.emit()
        #vrati slajs datafrejma za sve indekse koji su veci ili jednaki izabranom.
        try:
            vrijeme = self.siroviFrejm.index[index.row()]
            slajs = self.siroviFrejm[self.siroviFrejm.index >= vrijeme]
            self.workingFrejm = self.priredi_slajs_podataka(slajs)
            #napravi model 3 minutnih srednjaka i daj ga drugom viewu na prikaz
            self.workingFrejmModel = WorkingFrejmModel(frejm=self.workingFrejm, tocke=self.tocke)
            self.tableViewTocke.setModel(self.workingFrejmModel)
            self.emit(QtCore.SIGNAL('set_working_frejm(PyQt_PyObject)'), self.workingFrejm)
        except ValueError as err:
            QtGui.QMessageBox.information(self, 'Problem prilikom rada', str(err))

    def priredi_slajs_podataka(self, slajs):
        """
        funkcija prihvaca izabrani slajs frejma i resamplira ga na 3 minutne
        srednjake. interval je zatvoren sa desne strane, ali se koristi label
        lijeve strane.
        npr.
        za index 12:05:00
            -uzima se average indeksa 12:05, 12:06, 12:07
            -koristi se label 12:05
        """
        #samo 180 minutnih podataka (60 tocaka nakon 3 minutne agregacije)
        frejm = slajs.copy()
        if len(frejm) < 180:
            raise ValueError('Nema dovoljno podataka')
        frejm = frejm.iloc[0:180, :]
        listaIndeksa = []
        for i in range(0, len(frejm), 3):
            for column in frejm.columns:
                if i+2 <= len(frejm)-1:
                    kat = frejm.loc[frejm.index[i]:frejm.index[i+2], column]
                    srednjak = np.average(kat)
                    frejm.loc[frejm.index[i], column] = srednjak
                    if frejm.index[i] not in listaIndeksa:
                        listaIndeksa.append(frejm.index[i])
        frejm = frejm[frejm.index.isin(listaIndeksa)]
        return frejm
