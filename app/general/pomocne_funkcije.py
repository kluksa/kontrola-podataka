# -*- coding: utf-8 -*-
"""
@author: User


U ovom modulu nalaze se pomocne funkcije koje se koriste u drugim dijelovima
aplikacije. Cilj ih je sve staviti na jedno mjesto radi smanjivanja ponavljanja
koda u vise raznih modula.
"""


import logging
import matplotlib


from PyQt4 import QtGui
import datetime
import pandas as pd
import numpy as np

###############################################################################
###############################################################################
class AppExcept(Exception):
    """definicjia vlastite exception klase"""
    pass
###############################################################################
###############################################################################
def load_config_item(cfg, section, option, default, tip):
    """
    funkcija koja ucitava odredjenu opciju iz config objekta u zadani
    target objekt ako opcija postoji. Ako opcija ne postoji, koristi se
    zadani default.

    P.S. Objasnjenje za dosta ruzan komad koda:

    Problem je sto configparser po defaultu cita samo stringove
    i output get metode je string, coercanje u specificni tip se
    moze elegantno srediti sa eval(), ali to stvara sigurnosnu rupu u
    aplikaciji.

    npr.
    poziv funkcije eval("(1,'banana',2.34)") ima output tip tuple sa 3 clana.
    prvi je tipa int, drugi je tipa str, treci je tipa float.

    problem nastaje kada se u eval kao string prosljedi npr. naredba za
    formatiranje hard diska...
    """
    try:
        if tip == str:
            value = cfg.get(section, option)
            logging.debug('Config element {0} - {1} postoji, value = {2}'.format(section, option, value))
            return value
        elif tip == int:
            value = cfg.getint(section, option)
            logging.debug('Config element {0} - {1} postoji, value = {2}'.format(section, option, value))
            return value
        elif tip == float:
            value = cfg.getfloat(section, option)
            logging.debug('Config element {0} - {1} postoji, value = {2}'.format(section, option, value))
            return value
        elif tip == bool:
            value = cfg.getboolean(section, option)
            logging.debug('Config element {0} - {1} postoji, value = {2}'.format(section, option, value))
            return value
        elif tip == list:
            textValue = cfg.get(section, option)
            value = textValue.split(',')
            logging.debug('Config element {0} - {1} postoji, value = {2}'.format(section, option, value))
            return value
        elif tip == tuple:
            textValue = cfg.get(section, option)
            value = textValue.split(',')
            value = tuple(value)
            return value
    except Exception as err:
        #Ako bilo sto ne valja, vrati default i logiraj stack trace errora
        logging.debug(err, exc_info = True)
        logging.debug('Config element {0} - {1} ne postoji ili je lose zadan ,koristi se default = {2}'.format(section, option, default))
        return default
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
def make_color(rgb, a):
    """
    za zadani rgb i alpha vrati matplotlib valjani color
    """
    #normalize values na range [0-1]
    boja = normalize_rgb(rgb)
    #convert to hex color code
    hexcolor = matplotlib.colors.rgb2hex(boja)
    #convert to rgba pripremljen za crtanje
    color = matplotlib.colors.colorConverter.to_rgba(hexcolor, alpha = a)
    return color
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
def color_to_style_string(tip, target, color):
    """
    Helper funkcija za izradu styleSheet stringa. Funkcija se iskljucivo koristi za
    promjenu pozadinske boje QWidgeta.
    Formatiranje pozadinske boje moguce je izvesti uz pomoc setStyleSheet metode
    na zadanim QObjektima. Ta funkcija uzima kao argument string (slican CSS-u).
    Ova funkcija stvara taj string.

    input:
        tip -> string, tip widgeta koji se mjenja npr. QPushButton
        target -> string, naziv widgeta kojem mjenjamo boju
            npr. 'label1'
        color -> QtGui.QColor (QColor objekt, sadrzi informaciju o boji)
    output:
        string - styleSheet 'css' stil ciljanog elementa
    """
    r = color.red()
    g = color.green()
    b = color.blue()
    a = int(100*color.alpha()/255)
    stil = str(tip) + "#" + target + " {background: rgba(" +"{0},{1},{2},{3}%)".format(r,g,b,a)+"}"
    return stil
###############################################################################
def rgba_to_style_string(rgb, a, tip, target):
    """
    kombinacija funkcija color_to_style_string i default_color_to_qcolor
    rgb - tuple boje
    a - alpha vrijednost
    tip - klasa QWidgeta (string)
    target - specificna instanca tipa (string)
    """
    boja = default_color_to_qcolor(rgb, a)
    stil = color_to_style_string(tip, target, boja)
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
def prosiri_granice_grafa(tmin, tmax, t):
    """
    Funkcija 'pomice' rubove intervala [tmin, tmax] na [tmin-t, tmax+t].
    Koristi se da se malo prosiri canvas na kojem se crtaju podaci tako da
    rubne tocke nisu na samom rubu canvasa.

    -> t je integer, broj minuta
    -> tmin, tmax su pandas timestampovi (pandas.tslib.Timestamp)

    izlazne vrijednosti su 2 'pomaknuta' pandas timestampa
    """
    tmin = tmin - datetime.timedelta(minutes = t)
    tmax = tmax + datetime.timedelta(minutes = t)
    tmin = pd.to_datetime(tmin)
    tmax = pd.to_datetime(tmax)
    return tmin, tmax
###############################################################################
def pronadji_tickove_satni(tmin, tmax):
    """
    funkcija vraca listu tickmarkera i listu tick labela za satni graf.
    -vremenski raspon je tmin, tmax
    -tickovi su razmaknuti 1 sat
    vrati dict sa listama lokacija i labela za tickove
    """
    tmin = tmin - datetime.timedelta(minutes = 1)
    tmin = pd.to_datetime(tmin)
    majorTickovi = list(pd.date_range(start = tmin, end = tmax, freq = 'H'))
    majorLabeli = [str(ind.hour)+'h' for ind in majorTickovi]
    tempTickovi = list(pd.date_range(start = tmin, end = tmax, freq = '15Min'))
    minorTickovi = []
    minorLabeli = []
    for ind in tempTickovi:
        if ind not in majorTickovi:
            #formatiraj vrijeme u sat:min 12:15:00 -> 12h:15m
            #ftime = str(ind.hour)+'h:'+str(ind.minute)+'m'
            minorTickovi.append(ind)
            minorLabeli.append("")
            #minorLabeli.append(ftime)

    out = {'majorTickovi':majorTickovi,
           'majorLabeli':majorLabeli,
           'minorTickovi':minorTickovi,
           'minorLabeli':minorLabeli}

    return out
###############################################################################
def pronadji_tickove_minutni(tmin, tmax):
    """
    funkcija vraca liste tickmarkera (minor i major) i listu tick labela
    za minutni graf.
    """
    tmin = tmin - datetime.timedelta(minutes = 1)
    tmin = pd.to_datetime(tmin)
    majorTickovi = list(pd.date_range(start = tmin, end= tmax, freq = '5Min'))
    majorLabeli = [str(ind.hour)+'h:'+str(ind.minute)+'m' for ind in majorTickovi]
    tempTickovi = list(pd.date_range(start = tmin, end= tmax, freq = 'Min'))
    minorTickovi = []
    minorLabeli = []
    for ind in tempTickovi:
        if ind not in majorTickovi:
            minorTickovi.append(ind)
            #minorLabeli.append(str(ind.minute)+'m')
            minorLabeli.append("")

    out = {'majorTickovi':majorTickovi,
           'majorLabeli':majorLabeli,
           'minorTickovi':minorTickovi,
           'minorLabeli':minorLabeli}

    return out
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
        return None
    else:
        tmin = datetime.datetime.min
        delta = (dt_objekt - tmin).seconds
        zaokruzeno = ((delta + (nSekundi / 2)) // nSekundi) * nSekundi
        izlaz = dt_objekt + datetime.timedelta(0, zaokruzeno-delta, -dt_objekt.microsecond)
        return izlaz
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
def sync_zero_span_x_os(lista):
    """
    ulaz je lista od 2 datafrejma
    izlaz je vremenski raspon x osi
    """
    min1 = min(lista[0].index)
    min2 = min(lista[1].index)
    max1 = max(lista[0].index)
    max2 = max(lista[1].index)

    return [min(min1, min2), max(max1, max2)]
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
def pronadji_najblizi_time_indeks(lista, vrijednost):
    """
    Helper funkcija za pronalazak najblizeg indeksa (po vrijednosti) od zadane
    vrijednosti.
    Pretpostavka:
    -lista je pandas dataframe indeks (pandas timestampovi)
    -vrijednost je takodjer pandas timestamp
    """
    #1 sklepaj np.array od liste
    inList = np.array(lista)
    #2 sklepaj konstanti np.array sa vrijednosti iste duljine kao i ulazna lista
    const = [vrijednost for i in range(len(lista))]
    const = np.array(const, dtype = 'datetime64[ns]') #tip mora odgovarati
    #oduzmi dvije liste teprimjeni apsolutnu vrijednost na ostatak.
    #minimum tako dobivene liste je najbliza vrijednost
    return (np.abs(inList - const)).argmin()
###############################################################################
def mpl_time_to_pandas_datetime(vrijeme):
    """helper funkcija za pretvorbu vremenske kooridinate matplotlib vremena u
    pandas timestamp"""
    pdTime = matplotlib.dates.num2date(vrijeme) #datetime.datetime
    #problem.. rounding offset aware i offset naive datetimes..workaround
    pdTime = datetime.datetime(pdTime.year,
                               pdTime.month,
                               pdTime.day,
                               pdTime.hour,
                               pdTime.minute,
                               pdTime.second)
    #aktualna konverzija iz datetime.datetime objekta u pandas.tislib.Timestamp
    return pd.to_datetime(pdTime)
###############################################################################
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
                  'ERROR':logging.ERROR,
                  'CRITICAL': logging.CRITICAL}
    #lvl parametar
    if lvl in DOZVOLJENI:
        lvl = DOZVOLJENI[lvl]
    else:
        lvl = logging.ERROR
    #filemode
    if mode not in ['a','w']:
        mode = 'a'
    try:
        logging.basicConfig(level = lvl,
                            filename = file,
                            filemode = mode,
                            format = '{levelname}:::{asctime}:::{module}:::{funcName}:::{message}',
                            style = '{')
    except OSError as err:
        print('Error prilikom konfiguracije logera.', err)
        print('Application exit')
        #ugasi interpreter...exit iz programa.
        exit()
###############################################################################
def int_to_boolean(x):
    """
    ako je x vrijednost veca ili jednaka 0 vraca True,
    ako nije, vraca False

    Primarno sluzi kao adapter za flag vrijednost mintnih podataka prilikom uploada
    podataka na rest
    """
    if x >= 0:
        return True
    else:
        return False
###############################################################################