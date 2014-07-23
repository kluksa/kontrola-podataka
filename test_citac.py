# -*- coding: utf-8 -*-
"""
Created on Wed Jul 23 09:13:30 2014

@author: velimir
"""

import citac
import unittest

"""
Krenuo sam pisati unit testove za citac
"""


class TestWlReader(unittest.TestCase):
    def setUp(self):
        self.Reader = citac.WlReader()
    
    def test_provjeri_headere_1(self):
        """
        Funkcija mora vratiti 'False' ako file ne postoji
        """
        x = self.Reader.provjeri_headere('janepostojim.csv')
        self.assertFalse(x)
    
    def test_provjeri_headere_2(self):
        """
        Funkcija mora vratiti 'False' ako headeri u fileu
        ne postuju strukturu [Date, Time, mjerenje1, status1, ... mjerenjeN,
        statusN, Flag, Zone]
        """
        x = self.Reader.provjeri_headere('pj_corrupted.csv')
        self.assertFalse(x)
    
    def test_provjeri_headere_3(self):
        """
        Funkcija mora vratiti 'False' ako je file prazan
        """
        x = self.Reader.provjeri_headere('pj_empty.csv')
        self.assertFalse(x)
    
    def test_provjeri_headere_4(self):
        """
        Funkcija mora vratiti 'True' ako headeri postuju strukturu 
        [Date, Time, mjerenje1, status1, ... mjerenjeN, statusN, Flag, Zone]
        """
        x = self.Reader.provjeri_headere('pj.csv')
        self.assertTrue(x)
        
    def test_provjeri_headere_5(self):
        """
        Funkcija mora vratiti 'False' ako se prosljedi argument koji nije string
        """
        x = self.Reader.provjeri_headere(3.14)
        self.assertFalse(x)
        
    def test_provjeri_headere_6(self):
        """
        Funkcija mora vratiti false ako se prosljedi string koji ne zavrsava na
        .csv (samo csv fileovi mogu proci test)
        """
        x = self.Reader.provjeri_headere('pjtest.txt')
        self.assertFalse(x)
    
    def tearDown(self):
        self.Reader = None
        

if __name__ == '__main__':
    print('\n\nRezultati unit testa:')
    unittest.main(verbosity = 2)