# -*- coding: utf-8 -*-
"""
Created on Mon Feb 16 10:13:58 2015

@author: User
"""
from PyQt4 import uic

base30, form30 = uic.loadUiType('auth_login.ui')
class DijalogLoginAuth(base30, form30):
    def __init__(self, parent = None):
        super(base30, self).__init__(parent)
        self.setupUi(self)
        
        #memberi za user/pass
        self.u = None
        self.p = None
        #connection input widgeta
        self.LEUser.textEdited.connect(self.set_user)
        self.LEPass.textEdited.connect(self.set_pswd)
        
    def set_user(self, x):
        self.u = str(x)
    
    def set_pswd(self, x):
        self.p = str(x)
        
    def vrati_postavke(self):
        return self.u, self.p