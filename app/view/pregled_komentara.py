# -*- coding: utf-8 -*-
"""
Created on Fri Mar 11 13:26:36 2016

@author: DHMZ-Milic
"""
import sys
from PyQt4 import QtGui, QtCore
from app.model.table_model import KomentarModel

class PregledKomentara(QtGui.QWidget):
    def __init__(self, parent=None):
        super(PregledKomentara, self).__init__(parent)

        self.modelKomentara = KomentarModel()

        self.splitter = QtGui.QSplitter()

        self.plainTextEdit = QtGui.QPlainTextEdit()
        self.plainTextEdit.setEnabled(False)

        self.tableView = QtGui.QTableView()
        self.tableView.setModel(self.modelKomentara)

        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.addWidget(self.tableView)
        self.splitter.addWidget(self.plainTextEdit)

        lay = QtGui.QVBoxLayout()
        lay.addWidget(self.splitter)

        self.setLayout(lay)

        self.tableView.clicked.connect(self.prikazi_puni_tekst)

    def set_frejm_u_model(self, frejm):
        self.modelKomentara.set_frejm(frejm)

    def prikazi_puni_tekst(self, x):
        red = x.row()
        tekst = self.modelKomentara.dohvati_tekst_za_red(red)
        self.plainTextEdit.setPlainText(tekst)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    x = PregledKomentara()
    x.show()
    sys.exit(app.exec_())