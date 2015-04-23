# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 11:09:37 2015

@author: DHMZ-Milic
"""
import sys
from PyQt4 import QtGui, QtCore, uic
from enum import Enum

from terenska_provjera_racun import TerenskaProvjeraRacun
from terenska_provjera_podaci import TerenskaProvjeraPodaci
from terenska_provjera_rezultati import TerenskaProvjeraRezultati

class ZahtjeviNormeProracuni(object):
    """
    Zahtjevi i podaci iz norme, za sada hardcoded, ideja je to povlaciti sa RESTA
    ili negog konfig filea kasnije...
    """
    def __init__(self):
        #plinovi
        self.SO2 = {'opseg': 376,
                    'jedinice': 'nmol/mol',
                    'srz': 2,
                    'srs': 1.5,
                    'rz': 5,
                    'rmax': 4,
                    'conveff': None,
                    'izvor': 'Boca pod tlakom SO2 u N2',
                    'oznaka norme': 'HRN EN 14212:2012',
                    'naziv': 'Vanjski zrak – Standardna metoda za mjerenje koncentracije sumporova dioksida u zraku ultraljubičastom fluorescencijom',
                    'oznaka': 'OB 5.2.1.1.1-1'}
        self.NOx = {'opseg': 400,
                    'jedinice': 'nmol/mol',
                    'srz': 4,
                    'srs': 0.75,
                    'rz': 5,
                    'rmax': 4,
                    'conveff': 95,
                    'izvor': 'Boca pod tlakom NO u N2',
                    'oznaka norme': 'HRN EN 14211:2012',
                    'naziv': 'Vanjski zrak – Standardna metoda za mjerenje koncentracije dušikova dioksida i dušikova monoksida u zraku kemiluminiscencijom',
                    'oznaka': 'OB 5.2.2.1.1-1'}
        self.CO = {'opseg': 15,
                   'jedinice': u'\u00B5' + 'mol/mol',
                   'srz': 6,
                   'srs': 3,
                   'rz': 0.5,
                   'rmax': 4,
                   'conveff': None,
                   'izvor': 'Boca pod tlakom CO u N2',
                   'oznaka norme': 'HRN EN 14626:2012',
                   'naziv': 'Vanjski zrak – Standardna metoda za mjerenje koncentracije ugljikova monoksida infracrvenom spektroskopijom',
                   'oznaka': 'OB 5.2.3.1.1-1'}
        self.O3 = {'opseg': 200,
                   'jedinice': 'nmol/mol',
                   'srz': 8,
                   'srs': 2,
                   'rz': 5,
                   'rmax': 4,
                   'conveff': None,
                   'izvor': 'Generator ozona Horiba ASGU-370',
                   'oznaka norme': 'HRN EN 14625:2012',
                   'naziv': 'Vanjski zrak – Standardna metoda za mjerenje ozona ultraljubičastom fotometrijom',
                   'oznaka': 'OB 5.2.4.1.1-1'}
        self.ASGU_370 = {'porizvodjac': 'Horiba',
                         'sljedivost': '1',
                         'MFC_NULL_PLIN_U': 0.26,
                         'MFC_NULL_PLIN_sljedivost': None,
                         'MFC_KAL_PLIN_U': 0.96,
                         'MFC_KAL_PLIN_sljedivost': None,
                         'O3_generator_U': None,
                         'O3_generator_sljedivost': None}
        self.T700 = {'porizvodjac': 'Teledyne API',
                     'sljedivost': 2,
                     'MFC_NULL_PLIN_U': 0.10,
                     'MFC_NULL_PLIN_sljedivost': 'sss',
                     'MFC_KAL_PLIN_U': 0.99,
                     'MFC_KAL_PLIN_sljedivost': 'wewe',
                     'O3_generator_U': 133.00,
                     'O3_generator_sljedivost': 'dddeweew'}
        self.T701 = {'proizvodjac': 'Teledyne API',
                     'max_udio_SO2': 0.51,
                     'max_udio_NOx': 0.52,
                     'max_udio_CO': 0.025,
                     'max_udio_O3': 0.53,
                     'max_udio_BTX': 0.54}
        self.T702 = {'proizvodjac': 'Teledyne API',
                     'max_udio_SO2': 1,
                     'max_udio_NOx': 2,
                     'max_udio_CO': 3,
                     'max_udio_O3': 4,
                     'max_udio_BTX': 5}
        self.ostali = {'CRM_C': 10000,
                       'CRM_sljedivost': 0.2}

class Tocke(Enum):
    """
    Enum definira raspone podataka u working datafrejmu za pojedinu tocku
    """
    tocka1 = range(0, 15)
    tocka2 = range(15, 30)
    tocka3 = range(30, 40)
    tocka4 = range(40, 50)
    tocka5 = range(50, 60)



BASE, FORM = uic.loadUiType('umjeravanje_glavni_prozor.ui')
class Umjeravanje(BASE, FORM):
    """
    Glavni prozor za umjeravanje.

    Sadrzava tabove sa racunom i rezultatima (unutar self.tabWidget)
    """
    def __init__(self, parent=None):
        super(BASE, self).__init__(parent)
        self.setupUi(self)

        self.norma = ZahtjeviNormeProracuni()

        self.racunWidget = TerenskaProvjeraRacun(tocke=Tocke)
        self.racunLayout.addWidget(self.racunWidget)
        self.rezultatiWidget = TerenskaProvjeraRezultati(tocke=Tocke)
        self.rezultatiLayout.addWidget(self.rezultatiWidget)
        self.podaciWidget = TerenskaProvjeraPodaci(tocke=Tocke)
        self.podaciLayout.addWidget(self.podaciWidget)

        #TODO! ovo treba zamjeniti sa necim smislenijim
        self.racunWidget.set_metadata(self.norma.SO2,
                                      self.norma.T700,
                                      self.norma.T702,
                                      self.norma.ostali)

        #connections
        self.connect(self.podaciWidget,
                     QtCore.SIGNAL('set_working_frejm(PyQt_PyObject)'),
                     self.racunWidget.set_working_frejm)


if __name__ == '__main__':
    umjeravanje = QtGui.QApplication(sys.argv)
    prozor = Umjeravanje()
    prozor.show()
    sys.exit(umjeravanje.exec_())
