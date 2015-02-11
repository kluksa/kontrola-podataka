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
def make_step_value(inputLista, endpoint):
    #TODO! NOT IMPLEMENTED
    """
    od ulazne liste [(vrijeme, vrijednost), ] napravi vrijednosti za step funkkciju
    Cilj ove funkcije stvaranje "step" granice upozorenja od certificiranih
    vrijednosti za zero i span.
    
    ulaz:
    inputLista
        --> lista podataka
        --> struktura je jos nije definirana do kraja, ali se lako moze
            preformulirati na trazeni oblik
    
    endpoint
        --> krajnja tocka
        --> zbog nacina rada algoritma, potrebno je definirati dodatnu
            tocku na x osi kao krajnju tocku buduceg grafa
        --> idealno bi trebala biti najveca x tocka na grafu
    
    izlaz:
    lista tocaka koje iscrtavaju step oblik kada bi se nacrtale
    
    alogritam radi na sljedeci nacin:
    1. petlja ide kroz sve tocke inputListe osim zadnje
    2. raspakirava x i y kooridinate tocke i sljedece tocke u nizu (x1, y1), (x2, y2)
    3. prepisuje tocke u novu listu tocno odredjenim redom
        3.a -ako je izlazna lista "prazna" --> (x1,y1) , (x2,y1), (x2,y2)
        3.b -ako je izlazna lista "puna" --> (x2,y1), (x2, y2)
        
    alogirtam dodaje tocku izmedju zadanih tocaka tako da umjesto "kosog"
    prijelaza napravi "step". parametar endpoint dodaje tocku na kraju
    kao horizontalnu liniju od zadnje step vrijednosti do tocke
    (x = endpoint, zadnja vrijednost y)
    """
    out = []
    for i in range(len(inputLista)-1):
        x, y = inputLista[i]
        j, k = inputLista[i+1]
        if len(out):
            #ako je lista puna, nemoj naljepiti prvi element, vec je dodan
            out.append((j, y))
            out.append((j, k))
        else:
            #ako je lista prazna... dodaj prvi element
            out.append((x, y))
            out.append((j, y))
            out.append((j, k))
    
    #zadnja tocka... treba potegnuti horizontalnu liniju do endpointa
    x, y = out[-1]
    out.append((endpoint, y))
    return out
###############################################################################
def make_warning_line(inputLista, postotak):
    #TODO! NOT IMPLEMENTED
    """
    Napravi granice tolerancije za zero ili span iz liste tocaka "step" funkcije.
    
    ulaz:
    inputLista
        -->izlazna vrijednost funkcije make_step_value(lista, endpoint)
        -->lista tocaka granice tolerancije u stilu "step" funkcije
    postotak:
        --> int, vrijednost postotka za koje ce se granica tolerancije
            pomaknuti. npr. postotak = 5 --> 5% odmak od centralne linije.
            
    izlaz:
        -->3 liste iste duljine zapakirane u tuple
        --> x ,tocke na x osi, nepromjenjene
        --> ymin, tocke na y osi pomaknute za postotak vrijednosti nize
            od y vrijednosti "step" vrijednosti
        --> ymax, tocke na y osi pomaknute za postotak vrijednosti vise
            od y vrijednosti "step" vrijednosti
            
    algoritam radi liste uz pomoc list comprehensiona (kraci i brzi nacin)
    """
    #napravi listu x podataka
    x = [i for i, j in inputLista]
    #napravi listu y podataka "centralnih" step vrijednosti
    y = [j for i, j in inputLista]
    
    #pomakni vrijednosti za neki postotak
    ymin = [broj-(broj*int(postotak)/100) for broj in y]
    ymax = [broj+(broj*int(postotak)/100) for broj in y]
    
    #vrati rezultate
    return x, ymin, ymax
###############################################################################
def provjeri_zero_span_odstupanje(graf, tpl):
    #TODO! NOT IMPLEMENTED
    """
    Provjera ispravnosti tocaka za zero i span graf (da li su unutar granica
    tolerancije)
    
    ulaz:
    graf
        -->graf je izlaz funkcije make_warning_line(lista, postotak)
        -->odredjuje parametre granica tolerancije
    tpl
        -->tuple (x, y), tocka ciju ispravnost zelimo provjeriti
    
    izlaz:
        --> boolean
        
    algoritam:
    nakon unpackinga tupleova i pripreme podataka, krecemo sa petljom
    koja pokusava pronaci poziciju zadane tocke unutar step intervala.
    
    za svaku x vrijednost step podataka 'X', 
    provjeri da li je zadani x unutar [X, X+1>
    Ako je provjeri da li je vrijednost y tocke izmedju vrijednosti
    step funkcije za taj interval.
    Ako je unutar vrijednosti vrati True
    Ako nije, vrati False i probaj drugi interval
    """
    x, y = tpl
    xgraf, ymin, ymax = graf
    
    for i in range(len(xgraf)-1):
        if x >= xgraf[i] and x < xgraf[i+1]:
            if y >= ymax[i] or y <= ymin[i]:
                return False
            else:
                return True    
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