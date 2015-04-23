# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 11:08:52 2015

@author: DHMZ-Milic
"""

from PyQt4 import uic

BASE1, FORM1= uic.loadUiType('terenska_provjera_rezultati.ui')
class TerenskaProvjeraRezultati(BASE1, FORM1):
    """
    Tab sa rezultatima
    """
    def __init__(self, parent=None, tocke=None):
        super(BASE1, self).__init__(parent)
        self.setupUi(self)
        self.tocke = tocke #enum raspona za pojedine tocke
