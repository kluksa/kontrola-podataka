#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 23 09:13:30 2014

@author: velimir
"""

import citac
import pandas as pd
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
                          self.Reader.provjeri_headere)
              
#        self.assertRaises(TypeError, 
#                          self.Reader.provjeri_headere, 
#                          12.12345, './data/pj.csv', 
#                          greska = None)

    #test metode "citaj"
###############################################################################
#TODO!
#4. treba provjeriti ucitavanjem nekog testnog csv filea da li su sve vrijednosti
#   na pravom mjestu

    def test_citaj_1(self):
        """
        Funkcija mora vratiti "None" ako se prosljedi nepostojeci csv file
        """
        x = self.Reader.citaj('./data/janepostojim.csv')
        self.assertIsNone(x)
    
    def test_citaj_2(self):
        """
        Funkcija mora vratiti "None" ako se prosljedi csv file koji ne postuje
        zadanu strukturu
        """
        x = self.Reader.citaj('./data/pj_corrupted.csv')
        self.assertIsNone(x)
        
    def test_citaj_3(self):
        """
        Funkcija mora vratiti "None" ako je ulazni csv file prazan
        """
        x = self.Reader.citaj('./data/pj_empty.csv')
        self.assertIsNone(x)
        
    def test_citaj_4(self):
        """
        Funkcija mora vratiti dictionary ako je file ispravne strukture
        """
        x = self.Reader.citaj('./data/pj.csv')
        self.assertEqual(type(x), type({}))
        
    def test_citaj_5(self):
        """
        Funkcija mora vratiti "None" ako se prosljedi neki file koji nije .csv
        """
        x = self.Reader.citaj('./data/pjtest.txt')
        self.assertIsNone(x)
        
    def test_citaj_6(self):
        """
        Funkcija mora raiseati TypeError ako se pozove s krivim brojem argumenata
        """
        self.assertRaises(TypeError, 
                          self.Reader.citaj)
                          
        self.assertRaises(TypeError, 
                          self.Reader.citaj, 
                          './data/pj.csv', None, 2, 
                          greska = 3)
    def test_citaj_7(self):
        """
        Funkcija mora vratiti "None", ako ulazni parametar nije string
        """
        x = self.Reader.citaj(123.456)
        self.assertIsNone(x)
        
    def test_citaj_8(self):
        """
        Za ispravni unos provjeri strukturu izlaza
        Dictionary pandas datafrejmova. Svaki frame mora imati:
        key dicta - string (ime komponente)
        indeks - tip pandas date_time
        stupci - redom: koncentracija, status, flag
        #TODO!
        #test vrijednosti u stupcima??? (float,int,int) or np.NaN???
        """
        x = self.Reader.citaj('./data/pj.csv')
        kljucevi = list(x.keys())
        for kljuc in kljucevi:
            self.assertEqual(type(kljuc),type('test'))
            headeri = x[kljuc].columns.values
            self.assertEqual(len(headeri),3)
            self.assertEqual(headeri[0],u'koncentracija')
            self.assertEqual(headeri[1],u'status')
            self.assertEqual(headeri[2],u'flag')
            #test index type
            indeks = x[kljuc].index
            okTip = pd.date_range('23-07-2014 12:00:00', periods = 10, freq = 'M')
            self.assertEqual(type(indeks), type(okTip))
    
    def test_citaj_9(self):
        """
        provjeri da li headeri odgovaraju kljucevima izlaznog dictionarija
        """
        x = self.Reader.citaj('./data/pj.csv')
        kljucevi = list(x.keys())
        #zadan je dobar testni file pa ne bi trebalo biti problema sa ucitavanjem
        file = open('./data/pj.csv')
        firstLine = file.readline()
        file.close()        
        #makni \n na kraju linije
        firstLine = firstLine[:-1]
        headerList = firstLine.split(sep=',')
        for i in range(2,len(headerList)-2,2):
            self.assertIn(headerList[i], kljucevi)

    def test_citaj_10(self):
        """
        test pojedinih frejmova nakon ucitavanja poznatog filea.
        """
        pass

    #test metode "citaj_listu"
###############################################################################
    def test_citaj_listu_1(self):
#TODO!
#1. srediti slicne testove kao i za slucaj citaca.
#2. provjera spajanja liste, ponasanje merge/update funkcija
        pass
    
###############################################################################
    def tearDown(self):
        self.Reader = None
        

if __name__ == '__main__':
    print('\n\nRezultati unit testa:')
    #unittest.main(verbosity = 2)
    unittest.main()