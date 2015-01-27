# -*- coding: utf-8 -*-
"""
@author: User


U ovom modulu nalaze se pomocne funkcije koje se koriste u drugim dijelovima
aplikacije. Cilj ih je sve staviti na jedno mjesto radi smanjivanja ponavljanja
koda u vise raznih modula.
"""

from PyQt4 import QtGui
import datetime
from datetime import timedelta
import pandas as pd
###############################################################################
###############################################################################
"""definicjia vlastite exception klase"""
class AppExcept(Exception):
    pass
###############################################################################
###############################################################################
def pronadji_tickove_minutni(tmin, tmax):
    """
    funkcija vraca liste tickmarkera (minor i major) i listu tick labela
    za minutni graf(samo major tickovi)
    """
    tmin = tmin - timedelta(minutes = 1)
    tmin = pd.to_datetime(tmin)
    listaMajorTickova = list(pd.date_range(start = tmin, end= tmax, freq = '5Min'))
    listaMinorTickova = list(pd.date_range(start = tmin, end= tmax, freq = 'Min'))
    listaMajorTickLabela = []
    for ind in listaMajorTickova:
        #format major labela
        zeit = str(ind.hour)+':'+str(ind.minute)+'h'
        listaMajorTickLabela.append(zeit)
        #makni major label iz popisa minor tickova
        listaMinorTickova.remove(ind)
    
    return listaMajorTickova, listaMajorTickLabela, listaMinorTickova

###############################################################################
def pronadji_tickove_satni(tmin, tmax):
    """
    funkcija vraca listu tickmarkera i listu tick labela za satni graf.
    -vremenski raspon je tmin, tmax
    -tickovi su razmaknuti 1 sat
    """
    tmin = tmin - timedelta(minutes = 1)
    tmin = pd.to_datetime(tmin)
    listaTickova = list(pd.date_range(start = tmin, end= tmax, freq = 'H'))
    listaTickLabela = []
    for ind in listaTickova:
        #formatiraj vrijeme u sat+h npr. 12:00:00 -> 12h
        ftime = str(ind.hour)+'h'
        listaTickLabela.append(ftime)
    
    return listaTickova, listaTickLabela

###############################################################################
def prosiri_granice_grafa(tmin, tmax, t):
    """
    Funkcija 'pomice' rubove intervala [tmin, tmax] na [tmin-t, tmax+t].
    Koristi se da se malo prosiri canvas na kojem se crtaju podaci tako da
    rubne tocke nisu na samom rubu canvasa.
    
    -> t je integer, broj minuta
    -> tmin, tmax su pandas timestampovi (pandas.tslib.Timestamp)
    
    izlazne vrijednosti su 2 'pomaknuta' pandas timestampa
    """
    tmin = tmin - timedelta(minutes = t)
    tmax = tmax + timedelta(minutes = t)
    tmin = pd.to_datetime(tmin)
    tmax = pd.to_datetime(tmax)
    return tmin, tmax
###############################################################################
def zaokruzi_vrijeme(dt_objekt, nSekundi):
    """
    Funkcija zaokruzuje zlazni datetime objekt na najblize vrijeme zadano 
    sa nSekundi.
    
    dt_objekt -> ulaz je datetime.datetime objekt
    nSekundi -> broj sekundi na koje se zaokruzuje, npr.
        60 - minuta
        3600 - sat
    
    izlaz je datetime.datetime objekt ili None (po defaultu)
    """
    if dt_objekt == None:
        return
    else:
        tmin = datetime.datetime.min
        delta = (dt_objekt - tmin).seconds
        zaokruzeno = ((delta + (nSekundi / 2)) // nSekundi) * nSekundi
        izlaz = dt_objekt + timedelta(0, zaokruzeno-delta, -dt_objekt.microsecond)
        return izlaz
###############################################################################
def normalize_rgb(rgbTuple):
    """
    Adapter za crtanje.
    - matplotlib za boju ima niz vrijednosti izmedju [0-1], a ne izmedju [0-255]
    - ulaz je rgbTuple npr. (0,255,0)
    """
    r, g, b = rgbTuple
    return (r/255, g/255, b/255)
###############################################################################
def default_color_to_qcolor(rgb, a):
    """
    Helper funkcija za transformaciju boje u QColor. Funkcija je u biti adapter.
    RGB (tuple) se sastoji od tri broja u rasponu od 0-255 npr. (255,0,0) je crvena
    a (alpha, transparentnost) je float izmedju 0 i 1. Vece vrijednosti su manje prozirne
    Izlaz je QColor objekt, sa tim postavkama boje.
    input:
        rgb -> (r, g, b) tuple
        a -> float izmedju [0:1]
    output:
        QtGui.QColor objekt
    """
    boja = QtGui.QColor()
    #unpack tuple of rgb color
    r, g, b = rgb
    boja.setRed(r)
    boja.setGreen(g)
    boja.setBlue(b)
    #alpha je izmedju 0-1, input treba biti int 0-255
    a = int(a*255)
    boja.setAlpha(a)
    return boja
###############################################################################
def color_to_style_string(target, color):
    """
    Helper funkcija za izradu styleSheet stringa. Funkcija se iskljucivo koristi za
    promjenu pozadinske boje nekog QWidget elementa (gumb, combobox, label...).
    Formatiranje pozadinske boje moguce je izvesti uz pomoc setStyleSheet metode
    na zadanim QObjektima. Ta funkcija uzima kao argument string (slican CSS-u).
    Ova funkcija stvara taj string.
    
    input:
        target -> string, naziv widgeta kojem mjenjamo boju
            npr. 'QLabel#label1' (Odnosi se na QLabel, specificno na label1)
        color -> QtGui.QColor (QColor objekt, sadrzi informaciju o boji)
    output:
        string - styleSheet 'css' stil ciljanog elementa
    """
    r = color.red()
    g = color.green()
    b = color.blue()
    a = int(100*color.alpha()/255)
    stil = target + " {background: rgba(" +"{0},{1},{2},{3}%)".format(r,g,b,a)+"}"
    return stil
###############################################################################
def qcolor_to_default_color(color):
    """
    Helper funkcija za transformacije QColor u defaultnu boju, tj. rgb tuple i
    alphu (transparentrnost). Ulazni argument je QColor objekt, POSTOJE 2 izlazna
    argumenta, rgb tuple (3 vrijednosti izmedju 0 i 255) i alpha (float izmedju 0 i 1).
    input:
        color ->QtGui.QColor
    output:
        (r,g,b) tuple, i alpha
    """
    r = color.red()
    g = color.green()
    b = color.blue()
    a = color.alpha()/255
    return (r,g,b), a
###############################################################################