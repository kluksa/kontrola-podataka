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
def sredi_xtickove_zerospan(timestampovi):
    """
    funkcija pretvara listu y vrijednosti zero i span grafa u tickove prema datumu
    npr. timestamp jedne vrijednosti za zerospan je '2015-02-14 12:34:56'
    i treba se 'normalizirati' u '14.02' radi kraceg zapisa
    
    input je lista timestampova
    output je lista stringova (labeli za tickove), lista timestampova (tick location)
    """
    tmin = min(timestampovi)
    tmax = max(timestampovi)
    raspon = pd.date_range(start = tmin, end = tmax, freq = 'D')
    tickLoc = [pd.to_datetime(i.date())for i in raspon]
    tickLab = [str(i.day)+'.'+str(i.month) for i in tickLoc]
    
    return tickLoc, tickLab
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
def make_step_values(x, y):
    """
    od ulaznih lista kooridinatax, y tocaka napravi vrijednosti za step 
    funkkciju.
    
    Cilj ove funkcije stvaranje "step" granice upozorenja od certificiranih
    vrijednosti za zero i span.
    
    ulaz:
    x
        --> lista x kooridinata (vrijeme)
    y
        --> lista y kooridinata (vrijednost)
    
    izlaz:
    listste x i y kooridinata "step grafa"
    
    alogritam radi na sljedeci nacin:
    1. petlja ide kroz sve x tocke osim zadnje
    2. uzima i sljedecu vrijednost x kooridinate
    3. prepisuje tocke u novu listu tocno odredjenim redom
        3.a -ako je izlazna lista "prazna" --> (x1,y1) , (x2,y1), (x2,y2)
        3.b -ako je izlazna lista "puna" --> (x2,y1), (x2, y2)
        
    """
    outx = []
    outy = []
    for i in range(len(x)-1):
        x1 = x[i]
        y1 = y[i]
        x2 = x[i+1]
        y2 = y[i+1]

        if len(outx):
            #ako je lista puna, nemoj naljepiti prvi element, vec je dodan
            outx.append(x2)
            outy.append(y1)
            outx.append(x2)
            outy.append(y2)
        else:
            #ako je lista prazna... dodaj prvi element
            outx.append(x1)
            outy.append(y1)
            outx.append(x2)
            outy.append(y1)
            outx.append(x2)
            outy.append(y2)

    return outx, outy
###############################################################################
def fit_line(x, y):
    #TODO! NOT IMPLEMENTED
    """
    Za 1-D liste x i y iste duljine, vrati parametre linearne regresije, 
    nagib a i odsjecak na y osi b
    
    y = a * x + b
    
    !!!EKSTERNI DEPENDANCY!!!
    statsmodels
        --> model za statistiku
        --> dolazi zapakiran sa nekim stackovima (scipy, winpython..) pa je
            lako moguce da je vec postavljen
        --> ako nije ::: pip install statsmodels
    
    Metoda fita:
    fit least squares ordinary linear regression
    """
    try:
        import statsmodels.api as sm
        #STEP1 definiraj matrice Left Hand Side (LHS) and Right Hand Side (RHS)
        X = sm.add_constant(x) #RHS
        Y = y #LHS
        #STEP2 inicijaliziraj model (modeli su klase)
        model = sm.OLS(Y, X, missing = 'drop') #ignore NaN podatke (ne bi ih trebalo biti ali just in case...)
        #STEP3 pozovi metodu modela fit
        fit = model.fit()
        #vrati parametre calleru
        return fit.params[1], fit.params[0]
    except ImportError:
        print('eksterni modul --  statsmodels -- nije instaliran\npip install statsmodels')
        return None, None
###############################################################################
def pripremi_ref_zero_span(frejm, endpoint):
    """
    Od ulazne liste napravi podatke
    za plot warning i fill linije za zero i span.

    input:
    -> dataframe
    
    output:
    -> tuple "step" podataka
    """    
    #napravi 3 liste podataka za zero x , ymin, ymax
    stepx = list(frejm.index)
    stepymin = list(frejm['vrijednost'] - frejm['dozvoljenoOdstupanje'])
    stepymax = list(frejm['vrijednost'] + frejm['dozvoljenoOdstupanje'])
    
    """
    HACK PART 
    Treba nam tocka na rubu do koje povlacimo warning line.
    Uzmi zadnje vrijednosti zeroymin, zeroymax i kao zero x zadati endzero
    i endspan vremena
    """       
    #Dodaj vrijednosit na listu
    stepx.append(endpoint)
    stepymin.append(stepymin[-1])
    stepymax.append(stepymax[-1])
    
    ###podaci za step funkciju###
    StepX, StepYMin = make_step_values(stepx, stepymin)
    StepX, StepYMax = make_step_values(stepx, stepymax)
    
    return (StepX, StepYMin, StepYMax)
###############################################################################
def time_to_int(x):
    """
    Funkcija pretvara vrijeme x (pandas.tslib.Timestamp) u unix timestamp
    
    testirano sa:
    http://www.onlineconversion.com/unix_time.htm
    
    bilo koji pandas timestamp definiran rucno preko string reprezentacije ili
    programski (npr.funkcij pandas.tslib.Timestamp.now() ) vraca int koji
    odgovara zadanom vremenu.
    
    BITNO!
    based on seconds since standard epoch of 1/1/1970
    vrijeme je u GMT
    """
    return x.value / 1000000000        
###############################################################################