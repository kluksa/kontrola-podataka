#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 31 14:06:55 2014

@author: User

VERZIJE EKSTERNIH MODULA
-PyQt4 4.11.3
-pandas 0.15.2
-numpy 1.9.2rc1
-matplotlib 1.4.3
-requests 2.5.3
-enum

- standard library python 3.4.3 (sys, configparser...)

"""
import sys
import configparser
import logging
from PyQt4 import QtGui

import app.view.glavniprozor as glavniprozor


def setup_logging(file='applog.log', mode='a', lvl='INFO'):
    """
    pattern of use:
    ovo je top modul, za sve child module koristi se isti logger sve dok
    su u istom procesu (konzoli). U child modulima dovoljno je samo importati
    logging module te bilo gdje pozvati logging.info('msg') (ili neku slicnu
    metodu za dodavanje u log).
    """
    DOZVOLJENI = {'DEBUG': logging.DEBUG,
                  'INFO': logging.INFO,
                  'WARNING': logging.WARNING,
                  'ERROR': logging.ERROR,
                  'CRITICAL': logging.CRITICAL}
    # lvl parametar
    if lvl in DOZVOLJENI:
        lvl = DOZVOLJENI[lvl]
    else:
        lvl = logging.ERROR
    #filemode
    if mode not in ['a', 'w']:
        mode = 'a'
    try:
        logging.basicConfig(level=lvl,
                            filename=file,
                            filemode=mode,
                            format='{levelname}:::{asctime}:::{module}:::{funcName}:::{message}',
                            style='{')
    except OSError as err:
        print('Error prilikom konfiguracije logera.', err)
        print('Application exit')
        #ugasi interpreter...exit iz programa.
        exit()


config = configparser.ConfigParser()
try:
    config.read('config.ini')
except Exception as err:
    print('Greska kod ucitavanja config.ini')
    print('Application exit')
    print(err)
    # kill interpreter
    exit()
# dohvati postevke za logger (section, option, fallback ako log ne postoji)
filename = config.get('LOG_SETUP', 'file', fallback='applog.log')
filemode = config.get('LOG_SETUP', 'mode', fallback='a')
level = config.get('LOG_SETUP', 'lvl', fallback='INFO')
#setup logging
#setup_logging(file = filename, mode = filemode, lvl=level)

#instancira QApplication objekt i starta main event loop
aplikacija = QtGui.QApplication(sys.argv)
#inicijaliziraj aplikaciju sa config objektom
glavniProzor = glavniprozor.GlavniProzor(cfg=config)
#prikaz GUI na ekran
glavniProzor.show()
#clean exit iz aplikacije
sys.exit(aplikacija.exec_())

"""
TODO!

potencijalni problemi
1. unresponsive gui.
- Implementacija thredova??
- implemetacija je malo komplicirana
    -instanciram QThreadObject()
    -taj thread pokrece svoj event loop nakon poziva start metode
    -bilo koji QObject mogu gurnuti u taj thread
    -signali imaju protokol pomocu kojih mogu komunicirati sa drugim threadovima

    -display i kontroler drzati u jednom threadu
    -blocking I/O prebaciti u drugi thread? (networking, dokument..)
    -potrebno je jos refaktorirati kod

2. dokument nema mehanizam da oslobodi memoriju.
- kako se dodaju podaci prostor u memoriji raste...
- test pandas dataframe od 512640 redaka (1 god minutnih podataka) sa
  180 stupaca sa random float podacima zauzima oko 700MB memorije.
- procjena memorije se moze izracunati preko sljedece funkcije
  memsize = df.index.nbytes+df.values.nbytes+df.columns.nbytes
"""