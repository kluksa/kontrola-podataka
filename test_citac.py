#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 23 09:13:30 2014

@author: velimir
"""

import citac
import pandas as pd
import numpy as np
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
              
        self.assertRaises(TypeError, 
                          self.Reader.provjeri_headere, 
                          12.12345, './data/pj.csv', 
                          greska = None)

    #test metode "citaj"
###############################################################################
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
        -mock file, sve koncentracije su 10, status/flag su 0
        """
        x = self.Reader.citaj('./data/pj-20140715A.csv')
        kljucevi = list(x.keys())
        for kljuc in kljucevi:
            for i in x[kljuc].index:
                self.assertEqual(x[kljuc].loc[i, u'koncentracija'], 10)
                self.assertEqual(x[kljuc].loc[i, u'status'], 0)
                self.assertEqual(x[kljuc].loc[i, u'flag'], 0)

    #test metode "citaj_listu"
###############################################################################
#TODO!
#1. srediti slicne testove kao i za slucaj citaca.
#2. provjera spajanja liste, ponasanje merge/update funkcija

    def test_citaj_listu_1(self):
        """
        vrati none ako je funkcija pozvana s praznom listom, ili s nekim krivim
        argumentom
        """
        self.assertIsNone(self.Reader.citaj_listu([]))
        self.assertIsNone(self.Reader.citaj_listu('pekmez'))
        
    def test_citaj_listu_2(self):
        """
        raise TypeError ako se funkcija pozove s krivim brojem argumenata
        """
        self.assertRaises(TypeError, self.Reader.citaj_listu)
        
        self.assertRaises(TypeError, self.Reader.citaj_listu, ['prvi', 2], None, greska = 12)
        
    def test_citaj_listu_3(self):
        """
        funkcija treba vratiti None ako su svi elementi u listi "necitljivi"
        jer ne postoje, jer su corruptani jer nisu csv
        """
        lista = ['./data/janepostojim.csv', 
                 './data/pj_corrupted.csv', 
                 './data/pjtest.txt']
                 
        x = self.Reader.citaj_listu(lista)
        self.assertIsNone(x)
    
    def test_citaj_listu_4(self):
        """
        funkcija treba vratiti neki dict datafrejmova ako je barem jedan 
        element liste citljiv
        """
        lista = ['./data/janepostojim.csv', 
                 './data/pj-20140715A.csv', 
                 './data/pj_corrupted.csv', 
                 './data/pjtest.txt']
        
        x = self.Reader.citaj_listu(lista)
        #uz hrpu neispravnih fileova u listi je i jedan ok poznati csv file
        #ucitavamo poznati kratki csv... svi statusi i flagovi su 0, konc. su 10
        kljucevi = list(x.keys())
        for kljuc in kljucevi:
            for i in x[kljuc].index:
                self.assertEqual(x[kljuc].loc[i, u'koncentracija'], 10)
                self.assertEqual(x[kljuc].loc[i, u'status'], 0)
                self.assertEqual(x[kljuc].loc[i, u'flag'], 0)
        
    def test_citaj_listu_5(self):
        """
        Test spajanja frejmova
        """
        lista = ['./data/pj-20140715A.csv', 
                 './data/pj-20140715B.csv', 
                 './data/pj-20140715C.csv', 
                 './data/pj-20140715D.csv']
        x = self.Reader.citaj_listu(lista)
        #provjera svih kljuceva                 
        kljucevi = list(x.keys())
        mjerenja = ['1-SO2', '10-NO', '49-O3', 'PM1']
        for mjerenje in mjerenja:
            self.assertIn(mjerenje, kljucevi)
        
        #ruzan i nezgrapan blok provjera...
        #'1-SO2'
        self.assertEqual(x['1-SO2'].loc[self.pdt('24-02-2014 00:00'),u'koncentracija'],10)
        self.assertEqual(x['1-SO2'].loc[self.pdt('24-02-2014 00:01'),u'koncentracija'],10)
        self.assertEqual(x['1-SO2'].loc[self.pdt('24-02-2014 00:02'),u'koncentracija'],30)
        self.assertEqual(x['1-SO2'].loc[self.pdt('24-02-2014 00:03'),u'koncentracija'],30)
        self.assertEqual(x['1-SO2'].loc[self.pdt('24-02-2014 00:04'),u'koncentracija'],30)
        self.assertEqual(x['1-SO2'].loc[self.pdt('24-02-2014 00:05'),u'koncentracija'],30)
        self.assertEqual(x['1-SO2'].loc[self.pdt('24-02-2014 00:06'),u'koncentracija'],40)
        self.assertEqual(x['1-SO2'].loc[self.pdt('24-02-2014 00:07'),u'koncentracija'],40)
        self.assertEqual(x['1-SO2'].loc[self.pdt('24-02-2014 00:08'),u'koncentracija'],40)
        self.assertEqual(x['1-SO2'].loc[self.pdt('24-02-2014 00:09'),u'koncentracija'],30)
        self.assertEqual(x['1-SO2'].loc[self.pdt('24-02-2014 00:10'),u'koncentracija'],30)
        self.assertEqual(x['1-SO2'].loc[self.pdt('24-02-2014 00:11'),u'koncentracija'],30)
        self.assertEqual(x['1-SO2'].loc[self.pdt('24-02-2014 00:12'),u'koncentracija'],30)
        self.assertEqual(x['1-SO2'].loc[self.pdt('24-02-2014 00:13'),u'koncentracija'],40)
        self.assertEqual(x['1-SO2'].loc[self.pdt('24-02-2014 00:14'),u'koncentracija'],40)
        self.assertEqual(x['1-SO2'].loc[self.pdt('24-02-2014 00:15'),u'koncentracija'],40)
        self.assertEqual(x['1-SO2'].loc[self.pdt('24-02-2014 00:16'),u'koncentracija'],40)
        self.assertEqual(x['1-SO2'].loc[self.pdt('24-02-2014 00:17'),u'koncentracija'],40)
        self.assertEqual(x['1-SO2'].loc[self.pdt('24-02-2014 00:18'),u'koncentracija'],40)
        
        #'10-NO'
        self.assertEqual(x['10-NO'].loc[self.pdt('24-02-2014 00:00'),u'koncentracija'],10)
        self.assertEqual(x['10-NO'].loc[self.pdt('24-02-2014 00:01'),u'koncentracija'],10)
        self.assertEqual(x['10-NO'].loc[self.pdt('24-02-2014 00:02'),u'koncentracija'],10)
        self.assertEqual(x['10-NO'].loc[self.pdt('24-02-2014 00:03'),u'koncentracija'],10)
        self.assertEqual(x['10-NO'].loc[self.pdt('24-02-2014 00:04'),u'koncentracija'],10)
        self.assertEqual(x['10-NO'].loc[self.pdt('24-02-2014 00:05'),u'koncentracija'],10)
        self.assertEqual(x['10-NO'].loc[self.pdt('24-02-2014 00:06'),u'koncentracija'],10)
        self.assertEqual(x['10-NO'].loc[self.pdt('24-02-2014 00:07'),u'koncentracija'],10)
        self.assertEqual(x['10-NO'].loc[self.pdt('24-02-2014 00:08'),u'koncentracija'],10)
        self.assertEqual(x['10-NO'].loc[self.pdt('24-02-2014 00:09'),u'koncentracija'],10)
        self.assertEqual(x['10-NO'].loc[self.pdt('24-02-2014 00:10'),u'koncentracija'],10)
        
        #'49-O3'
        self.assertEqual(x['49-O3'].loc[self.pdt('24-02-2014 00:02'),u'koncentracija'],30)
        self.assertEqual(x['49-O3'].loc[self.pdt('24-02-2014 00:03'),u'koncentracija'],30)
        self.assertEqual(x['49-O3'].loc[self.pdt('24-02-2014 00:04'),u'koncentracija'],30)
        self.assertEqual(x['49-O3'].loc[self.pdt('24-02-2014 00:05'),u'koncentracija'],30)
        self.assertEqual(x['49-O3'].loc[self.pdt('24-02-2014 00:06'),u'koncentracija'],30)
        self.assertEqual(x['49-O3'].loc[self.pdt('24-02-2014 00:07'),u'koncentracija'],30)
        self.assertEqual(x['49-O3'].loc[self.pdt('24-02-2014 00:08'),u'koncentracija'],30)
        self.assertEqual(x['49-O3'].loc[self.pdt('24-02-2014 00:09'),u'koncentracija'],30)
        self.assertEqual(x['49-O3'].loc[self.pdt('24-02-2014 00:10'),u'koncentracija'],30)
        self.assertEqual(x['49-O3'].loc[self.pdt('24-02-2014 00:11'),u'koncentracija'],30)
        self.assertEqual(x['49-O3'].loc[self.pdt('24-02-2014 00:12'),u'koncentracija'],30)
        self.assertEqual(x['49-O3'].loc[self.pdt('24-02-2014 00:13'),u'koncentracija'],30)
        self.assertEqual(x['49-O3'].loc[self.pdt('24-02-2014 00:14'),u'koncentracija'],20)
        self.assertEqual(x['49-O3'].loc[self.pdt('24-02-2014 00:15'),u'koncentracija'],20)
        
        #'PM1'
        self.assertEqual(x['PM1'].loc[self.pdt('24-02-2014 00:06'),u'koncentracija'],40)
        self.assertEqual(x['PM1'].loc[self.pdt('24-02-2014 00:07'),u'koncentracija'],40)
        self.assertEqual(x['PM1'].loc[self.pdt('24-02-2014 00:08'),u'koncentracija'],40)
        self.assertEqual(x['PM1'].loc[self.pdt('24-02-2014 00:09'),u'koncentracija'],40)
        #eksplicitno zadane vrijednosti -999.00 koje se trebaju tumaciti kao np.NaN
        self.assertTrue(np.isnan(x['PM1'].loc[self.pdt('24-02-2014 00:10'),u'koncentracija']))
        self.assertTrue(np.isnan(x['PM1'].loc[self.pdt('24-02-2014 00:11'),u'koncentracija']))
        self.assertTrue(np.isnan(x['PM1'].loc[self.pdt('24-02-2014 00:12'),u'koncentracija']))
        self.assertTrue(np.isnan(x['PM1'].loc[self.pdt('24-02-2014 00:13'),u'koncentracija']))
        self.assertTrue(np.isnan(x['PM1'].loc[self.pdt('24-02-2014 00:14'),u'koncentracija']))
        self.assertTrue(np.isnan(x['PM1'].loc[self.pdt('24-02-2014 00:15'),u'koncentracija']))
        self.assertTrue(np.isnan(x['PM1'].loc[self.pdt('24-02-2014 00:16'),u'koncentracija']))
        self.assertTrue(np.isnan(x['PM1'].loc[self.pdt('24-02-2014 00:17'),u'koncentracija']))
        self.assertTrue(np.isnan(x['PM1'].loc[self.pdt('24-02-2014 00:18'),u'koncentracija']))
           
###############################################################################
    def tearDown(self):
        self.Reader = None
        
    def pdt(self, vrijeme):
        """
        helper funkcija koja vraca timestamp iz stringa
        """
        return pd.to_datetime(vrijeme)

if __name__ == '__main__':
    print('\n\nRezultati unit testa:')
    #unittest.main(verbosity = 2)
    unittest.main()