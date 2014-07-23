#!/usr/bin/python3
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
    
    #test metode "provjeri_headere"
###############################################################################
    def test_provjeri_headere_1(self):
        """
        Funkcija mora vratiti 'False' ako file ne postoji
        """
        x = self.Reader.provjeri_headere('./data/janepostojim.csv')
        self.assertFalse(x)
    
    def test_provjeri_headere_2(self):
        """
        Funkcija mora vratiti 'False' ako headeri u fileu
        ne postuju strukturu [Date, Time, mjerenje1, status1, ... mjerenjeN,
        statusN, Flag, Zone]
        """
        x = self.Reader.provjeri_headere('./data/pj_corrupted.csv')
        self.assertFalse(x)
    
    def test_provjeri_headere_3(self):
        """
        Funkcija mora vratiti 'False' ako je file prazan
        """
        x = self.Reader.provjeri_headere('./data/pj_empty.csv')
        self.assertFalse(x)
    
    def test_provjeri_headere_4(self):
        """
        Funkcija mora vratiti 'True' ako headeri postuju strukturu 
        [Date, Time, mjerenje1, status1, ... mjerenjeN, statusN, Flag, Zone]
        """
        x = self.Reader.provjeri_headere('./data/pj.csv')
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
        x = self.Reader.provjeri_headere('./data/pjtest.txt')
        self.assertFalse(x)
    
    def test_provjeri_headere_7(self):
        """
        Funkcija mora raise TypeError ako se prosljedi krivi broj argumenata 
        u pozivu. Ideja je razlikovati gresku kada netko pravilno pozove funkciju
        od slucaja kada netko zezne s pozivom funkcije!!
        """
        self.assertRaises(TypeError, 
                          self.Reader.provjeri_headere, 
                          None, 
                          None)
              
        self.assertRaises(TypeError, 
                          self.Reader.provjeri_headere, 
                          12.12345, 
                          './data/pj.csv', 
                          greska = None)

    #test metode "citaj"
###############################################################################
#TODO!
#1. treba vratiti None ako citac faila s citanjem jer je file kriv
#2. treba provjeriti strukturu ulaza
#3. treba provjeriti strukturu izlaza (dictionary, dataframe, columns, index)
#4. treba provjeriti ucitavanjem nekog testnog csv filea da li su sve vrijednosti
#   na pravom mjestu

    def test_citaj_1(self):
        pass
    
    #test metode "citaj_listu"
###############################################################################
    def test_citaj_listu_1(self):
#TODO!
#1. srediti slicne testove kao i za slucaj citaca.
        pass
    
###############################################################################
    def tearDown(self):
        self.Reader = None
        

if __name__ == '__main__':
    print('\n\nRezultati unit testa:')
    unittest.main(verbosity = 2)