# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 14:42:54 2015

@author: User
"""
import logging

import pomocne_funkcije

###############################################################################
###############################################################################
class AppSettingsDTO():
    """
    Storage & config objekt za elemente aplikacije
    """
    def __init__(self, cfg):
        logging.debug('Inicijalizacija DTO za gui elemente, start')
        #satni graf
        self.satniGrid = pomocne_funkcije.load_config_item(cfg, 'MAIN_WINDOW', 'action_satni_grid', False, bool)
        self.satniCursor = pomocne_funkcije.load_config_item(cfg, 'MAIN_WINDOW', 'action_satni_cursor', False, bool)
        self.satniLegend = pomocne_funkcije.load_config_item(cfg, 'MAIN_WINDOW', 'action_satni_legend', False, bool)
        self.satniTicks = pomocne_funkcije.load_config_item(cfg, 'MAIN_WINDOW', 'action_satni_minor_ticks', False, bool)
        self.satniSelector = pomocne_funkcije.load_config_item(cfg, 'MAIN_WINDOW', 'action_satni_span_selector', False, bool)
        #minutni graf
        self.minutniGrid = pomocne_funkcije.load_config_item(cfg, 'MAIN_WINDOW', 'action_minutni_grid', False, bool)
        self.minutniCursor = pomocne_funkcije.load_config_item(cfg, 'MAIN_WINDOW', 'action_minutni_cursor', False, bool)
        self.minutniLegend = pomocne_funkcije.load_config_item(cfg, 'MAIN_WINDOW', 'action_minutni_legend', False, bool)
        self.minutniTicks = pomocne_funkcije.load_config_item(cfg, 'MAIN_WINDOW', 'action_minutni_minor_ticks', False, bool)
        self.minutniSelector = pomocne_funkcije.load_config_item(cfg, 'MAIN_WINDOW', 'action_minutni_span_selector', False, bool)
        #zoom
        self.zoom = pomocne_funkcije.load_config_item(cfg, 'MAIN_WINDOW', 'action_zoom', False, bool)
        """
        rest servis info
        """
        self.RESTBaseUrl = pomocne_funkcije.load_config_item(cfg, 'REST_INFO', 'base_url', 'http://172.20.1.166:9090/SKZ-war/webresources/', str)
        self.RESTProgramMjerenja = pomocne_funkcije.load_config_item(cfg, 'REST_INFO', 'program_mjerenja', 'dhz.skz.aqdb.entity.programmjerenja', str)
        self.RESTSiroviPodaci = pomocne_funkcije.load_config_item(cfg, 'REST_INFO', 'sirovi_podaci', 'dhz.skz.rs.sirovipodaci', str)
        self.RESTZeroSpan = pomocne_funkcije.load_config_item(cfg, 'REST_INFO', 'zero_span', 'dhz.skz.rs.zerospan', str)
        self.RESTSatniPodaci = pomocne_funkcije.load_config_item(cfg, 'REST_INFO', 'satni_podaci', 'dhz.skz.rs.satnipodatak', str)
        logging.debug('Inicijalizacija DTO za gui elemente, end')
###############################################################################
    def set_satniGrid(self, x):
        self.satniGrid = x
        logging.info('Satni grid state promjenjen, nova vrijednost = {0}'.format(x))
###############################################################################
    def set_satniCursor(self, x):
        self.satniCursor = x
        logging.info('Satni cursor state promjenjen, nova vrijednost = {0}'.format(x))
###############################################################################
    def set_satniLegend(self, x):
        self.satniLegend = x
        logging.info('Satni legend state promjenjen, nova vrijednost = {0}'.format(x))
###############################################################################
    def set_satniTicks(self, x):
        self.satniTicks = x
        logging.info('Satni ticks state promjenjen, nova vrijednost = {0}'.format(x))
###############################################################################
    def set_satniSelector(self, x):
        self.satniSelector = x
        logging.info('Satni span selector state promjenjen, nova vrijednost = {0}'.format(x))
###############################################################################
    def set_minutniGrid(self, x):
        self.minutniGrid = x
        logging.info('Minutni grid state promjenjen, nova vrijednost = {0}'.format(x))
###############################################################################
    def set_minutniCursor(self, x):
        self.minutniCursor = x
        logging.info('Minutni cursor state promjenjen, nova vrijednost = {0}'.format(x))
###############################################################################
    def set_minutniLegend(self, x):
        self.minutniLegend = x
        logging.info('Minutni legend state promjenjen, nova vrijednost = {0}'.format(x))
###############################################################################
    def set_minutniTicks(self, x):
        self.minutniTicks = x
        logging.info('Minutni ticks state promjenjen, nova vrijednost = {0}'.format(x))
###############################################################################
    def set_minutniSelector(self, x):
        self.minutniSelector = x
        logging.info('Minutni span selector state promjenjen, nova vrijednost = {0}'.format(x))
###############################################################################
    def set_zoom(self, x):
        self.zoom = x
        logging.info('Zoom state promjenjen, nova vrijednost = {0}'.format(x))
###############################################################################
    def set_RESTBaseUrl(self, x):
        self.RESTBaseUrl = x
        logging.info('REST base url promjenjen, novi = {0}'.format(x))
###############################################################################
    def set_RESTProgramMjerenja(self, x):
        self.RESTProgramMjerenja = x
        logging.info('REST programMjerenja relative url promjenjen, novi = {0}'.format(x))
###############################################################################
    def set_RESTSiroviPodaci(self, x):
        self.RESTSiroviPodaci = x
        logging.info('REST siroviPodaci relative url promjenjen, novi = {0}'.format(x))
###############################################################################
    def set_RESTZeroSpan(self, x):
        self.RESTZeroSpan = x
        logging.info('REST zerospan relative url promjenjen, novi = {0}'.format(x))
###############################################################################
###############################################################################
class GrafSettingsDTO():
    """
    Storage & config objekt u kojem se pohranjuje popis GrafDTO za crtanje
    """
    def __init__(self, cfg):
        """
        cfg je instanca configparser objekta sa ucitanim config.ini
        """
        logging.debug('Inicijalizacija DTO za sve grafove, start')
        self.conf = cfg
        #lista dto objekata pomocnih grafova
        self.dictPomocnih = {}

        #definicija DTO za satni graf
        self.satniMidline = GrafDTO(cfg, tip = 'SATNI', podtip = 'midline', oblik = 'line')
        self.satniVOK = GrafDTO(cfg, tip = 'SATNI', podtip = 'VOK', oblik = 'scatter')
        self.satniVBAD = GrafDTO(cfg, tip = 'SATNI', podtip = 'VBAD', oblik = 'scatter')
        self.satniNVOK = GrafDTO(cfg, tip = 'SATNI', podtip = 'NVOK', oblik = 'scatter')
        self.satniNVBAD = GrafDTO(cfg, tip = 'SATNI', podtip = 'NVBAD', oblik = 'scatter')
        self.satniEksMin = GrafDTO(cfg, tip = 'SATNI', podtip = 'ekstrem', oblik = 'scatter')
        self.satniEksMax = GrafDTO(cfg, tip = 'SATNI', podtip = 'ekstrem', oblik = 'scatter')
        self.satniFill = GrafDTO(cfg, tip = 'SATNI', podtip = 'fill1', oblik = 'fill')

        #definicija DTO za minutni graf
        self.minutniMidline = GrafDTO(cfg, tip = 'MINUTNI', podtip = 'midline', oblik = 'line')
        self.minutniVOK = GrafDTO(cfg, tip = 'MINUTNI', podtip = 'VOK', oblik = 'scatter')
        self.minutniVBAD = GrafDTO(cfg, tip = 'MINUTNI', podtip = 'VBAD', oblik = 'scatter')
        self.minutniNVOK = GrafDTO(cfg, tip = 'MINUTNI', podtip = 'NVOK', oblik = 'scatter')
        self.minutniNVBAD = GrafDTO(cfg, tip = 'MINUTNI', podtip = 'NVBAD', oblik = 'scatter')

        #definicija DTO za SPAN graf
        self.spanMidline = GrafDTO(cfg, tip = 'SPAN', podtip = 'midline', oblik = 'line')
        self.spanVOK = GrafDTO(cfg, tip = 'SPAN', podtip = 'VOK', oblik = 'scatter')
        self.spanVBAD = GrafDTO(cfg, tip = 'SPAN', podtip = 'VBAD', oblik = 'scatter')
        self.spanFill1 = GrafDTO(cfg, tip = 'SPAN', podtip = 'fill1', oblik = 'fill')
        self.spanFill2 = GrafDTO(cfg, tip = 'SPAN', podtip = 'fill2', oblik = 'fill')
        self.spanWarning1 = GrafDTO(cfg, tip = 'SPAN', podtip = 'warning', oblik = 'line')
        self.spanWarning2 = GrafDTO(cfg, tip = 'SPAN', podtip = 'warning', oblik = 'line')

        #definicija DTO za ZERO graf
        self.zeroMidline = GrafDTO(cfg, tip = 'ZERO', podtip = 'midline', oblik = 'line')
        self.zeroVOK = GrafDTO(cfg, tip = 'ZERO', podtip = 'VOK', oblik = 'scatter')
        self.zeroVBAD = GrafDTO(cfg, tip = 'ZERO', podtip = 'VBAD', oblik = 'scatter')
        self.zeroFill1 = GrafDTO(cfg, tip = 'ZERO', podtip = 'fill1', oblik = 'fill')
        self.zeroFill2 = GrafDTO(cfg, tip = 'ZERO', podtip = 'fill2', oblik = 'fill')
        self.zeroWarning1 = GrafDTO(cfg, tip = 'ZERO', podtip = 'warning', oblik = 'line')
        self.zeroWarning2 = GrafDTO(cfg, tip = 'ZERO', podtip = 'warning', oblik = 'line')

        logging.debug('Inicijalizacija DTO za sve grafove, end')
###############################################################################
    def dodaj_pomocni(self, key):
        name = 'plot' + str(key)
        self.dictPomocnih[key] = GrafDTO(self.conf, tip = 'POMOCNI', podtip = name, oblik = 'plot')
        logging.info('Pomocni graf dodan, mjerenjeId = {0}'.format(key))
###############################################################################
    def makni_pomocni(self, key):
        self.dictPomocnih.pop(key)
        logging.info('Pomocni graf maknut, mjerenjeId = {0}'.format(key))
###############################################################################
###############################################################################
class GrafDTO():
    """
    Objekt u kojem se pohranjuju postavke pojedinog grafa.
    Samo se pohranjuje informacija o izgledu grafa (markeri, linije ...)

    ulazni parametri:
    cfg
        -instanca configparser objekta
    tip
        -string
        -section naziv unutar cfg
        -dozvoljeni su [SATNI, MINUTNI, POMOCNI, ZERO, SPAN]
    podtip
        -string
        -prvi dio optiona npr. 'midline'
        -dozvoljeni su [midline, ekstrem, VOK, VBAD, NVOK, NVBAD, fill1,
                        fill2, warning]

    oblik
        -string
        -oblik grafa za crtanje [plot, line, scatter, fill]
        -regulira tjek inicijalizacije, tj. sto se inicijalizira
        -npr. scatter graf nemaju podatke o liniji, line grafu ne treba
        informacija o izgledu markera...
    """
    def __init__(self, cfg, tip = '', podtip = '', oblik = 'plot'):
        #bitni memberi
        self._sviMarkeri = ['None', 'o', 'ˇ', '^', '<', '>', '|', '_',
                            's', 'p', '*', 'h', '+', 'x', 'd']

        self._sveLinije = ['None', '-', '--', '-.', ':']

        self._sveAgregiraneKomponente = ['avg', 'q05', 'q95', 'min', 'max', 'medijan']

        self.tip = tip
        self.podtip = podtip
        self.oblik = oblik
        """neovisno o obliku se definiraju:
        rgb, alpha, status crtanja, zorder, label grafa
        """
        self.rgb = self.init_rgb(cfg, self.tip, self.podtip)
        self.alpha = self.init_alpha(cfg, self.tip, self.podtip)
        self.color = pomocne_funkcije.make_color(self.rgb, self.alpha)
        self.crtaj = self.init_crtaj(cfg, self.tip, self.podtip)
        self.zorder = self.init_zorder(cfg, self.tip, self.podtip)
        self.label = self.init_label(cfg, self.tip, self.podtip)

        if oblik == 'plot':
            #marker i linija
            self.markerStyle = self.init_markerStyle(cfg, self.tip, self.podtip)
            self.markerSize = self.init_markerSize(cfg, self.tip, self.podtip)
            self.lineStyle = self.init_lineStyle(cfg, self.tip, self.podtip)
            self.lineWidth = self.init_lineWidth(cfg, self.tip, self.podtip)
        elif oblik == 'line':
            #samo linija
            self.markerStyle = 'None'
            self.markerSize = 12
            self.lineStyle = self.init_lineStyle(cfg, self.tip, self.podtip)
            self.lineWidth = self.init_lineWidth(cfg, self.tip, self.podtip)
        elif oblik == 'scatter':
            #samo marker
            self.markerStyle = self.init_markerStyle(cfg, self.tip, self.podtip)
            self.markerSize = self.init_markerSize(cfg, self.tip, self.podtip)
            self.lineStyle = 'None'
            self.lineWidth = 1.0
        elif oblik == 'fill':
            self.markerStyle = 'None'
            self.markerSize = 12
            self.lineStyle = 'None'
            self.lineWidth = 1.0
            if tip == 'SATNI':
                #fill between satnog grafa, izmedju kojih komponenti se sjenca
                self.komponenta1 = self.init_komponenta1(cfg, self.tip, self.podtip)
                self.komponenta2 = self.init_komponenta2(cfg, self.tip, self.podtip)
###############################################################################
    def init_label(self, cfg, tip, podtip):
        placeholder = podtip + ' label placeholder'
        podtip = podtip+'_label_'
        val = pomocne_funkcije.load_config_item(cfg, tip, podtip, placeholder, str)
        return str(val)
###############################################################################
    def set_label(self, x):
        self.label = str(x)
###############################################################################
    def init_zorder(self, cfg, tip, podtip):
        podtip = podtip+'_zorder_'
        val = pomocne_funkcije.load_config_item(cfg, tip, podtip, 2, int)
        if self.test_zorder(val):
            return int(val)
        else:
            return 2
###############################################################################
    def set_zorder(self, x):
        if self.test_zorder(x):
            self.zorder = x
###############################################################################
    def test_zorder(self, x):
        if x > 1:
            return True
        else:
            return False
###############################################################################
    def init_komponenta1(self, cfg, tip, podtip):
        podtip = podtip+'_komponenta1_'
        val = pomocne_funkcije.load_config_item(cfg, tip, podtip, 'q05', str)
        if self.test_fill_komponenta(val):
            return val
        else:
            return 'q05'
###############################################################################
    def init_komponenta2(self, cfg, tip, podtip):
        podtip = podtip+'_komponenta2_'
        val = pomocne_funkcije.load_config_item(cfg, tip, podtip, 'q95', str)
        if self.test_fill_komponenta(val):
            return val
        else:
            return 'q95'
###############################################################################
    def set_komponenta1(self, x):
        if self.test_fill_komponenta:
            self.komponenta1 = x
            logging.info('Promjena fill komponente za {0} - {1}, nova vrijednost = {2}'.format(self.tip, self.podtip, x))
###############################################################################
    def set_komponenta2(self, x):
        if self.test_fill_komponenta:
            self.komponenta2 = x
            logging.info('Promjena fill komponente za {0} - {1}, nova vrijednost = {2}'.format(self.tip, self.podtip, x))
###############################################################################
    def test_fill_komponenta(self, x):
        if x in self._sveAgregiraneKomponente:
            return True
        else:
            return False
###############################################################################
    def init_rgb(self, cfg, tip, podtip):
        podtip = podtip+'_rgb_'
        rgb = pomocne_funkcije.load_config_item(cfg, tip, podtip, (0,0,255), tuple)
        #dohvati samo prva 3 elementa
        rgb = rgb[:3]
        #convert to integer vrijednost
        rgb = tuple([int(i) for i in rgb])
        if self.test_rgb(rgb):
            return rgb
        else:
            return (0,0,255)
###############################################################################
    def init_alpha(self, cfg, tip, podtip):
        podtip = podtip+'_alpha_'
        alpha = pomocne_funkcije.load_config_item(cfg, tip, podtip, 1.0, float)
        if self.test_alpha(alpha):
            return alpha
        else:
            return 1.0
###############################################################################
    def init_crtaj(self, cfg, tip, podtip):
        podtip = podtip+'_crtaj_'
        boolCrtaj = pomocne_funkcije.load_config_item(cfg, tip, podtip, True, bool)
        return boolCrtaj
###############################################################################
    def init_markerStyle(self, cfg, tip, podtip):
        podtip = podtip+'_markerStyle_'
        marker = pomocne_funkcije.load_config_item(cfg, tip, podtip, 'o', str)
        if self.test_markerStyle(marker):
            return marker
        else:
            return 'o'
###############################################################################
    def init_markerSize(self, cfg, tip, podtip):
        podtip = podtip+'_markerSize_'
        size = pomocne_funkcije.load_config_item(cfg, tip, podtip, 12, int)
        if self.test_markerSize(size):
            return size
        else:
            return 12
###############################################################################
    def init_lineStyle(self, cfg, tip, podtip):
        podtip = podtip+'_lineStyle_'
        stil = pomocne_funkcije.load_config_item(cfg, tip, podtip,'-', str)
        if self.test_lineStyle(stil):
            return stil
        else:
            return '-'
###############################################################################
    def init_lineWidth(self, cfg, tip, podtip):
        podtip = podtip+'_lineWidth_'
        sirina = pomocne_funkcije.load_config_item(cfg, tip, podtip, 1.0, float)
        if self.test_lineWidth(sirina):
            return sirina
        else:
            return 1.0
###############################################################################
    def test_rgb(self, x):
        out = True
        for i in x:
            if i>=0 and i<=255:
                out = (out and True)
            else:
                out = (out and False)
        return out
###############################################################################
    def test_alpha(self, x):
        if x >= 0.0 and x<= 1.0:
            return True
        else:
            return False
###############################################################################
    def test_markerStyle(self, x):
        if x in self._sviMarkeri:
            return True
        else:
            return False
###############################################################################
    def test_markerSize(self, x):
        if x > 0:
            return True
        else:
            return False
###############################################################################
    def test_lineStyle(self, x):
        if x in self._sveLinije:
            return True
        else:
            return False
###############################################################################
    def test_lineWidth(self, x):
        if x > 0:
            return True
        else:
            return False
###############################################################################
    def set_alpha(self, x):
        if self.test_alpha(x):
            self.alpha = x
            self.color = pomocne_funkcije.make_color(self.rgb, x)
            logging.info('Promjena alfe za {0} - {1}, nova vrijednost = {2}'.format(self.tip, self.podtip, x))
###############################################################################
    def set_rgb(self, x):
        if self.test_rgb(x):
            self.rgb = x
            self.color = pomocne_funkcije.make_color(x, self.alpha)
            logging.info('Promjena rgb za {0} - {1}, nova vrijednost = {2}'.format(self.tip, self.podtip, x))
###############################################################################
    def set_crtaj(self, x):
        self.crtaj = x
        logging.info('Promjena crtaj booleana za {0} - {1}, nova vrijednost = {2}'.format(self.tip, self.podtip, x))
###############################################################################
    def set_markerStyle(self, x):
        if self.test_markerStyle(x):
            self.markerStyle = x
            logging.info('Promjena stila markera za {0} - {1}, nova vrijednost = {2}'.format(self.tip, self.podtip, x))
###############################################################################
    def set_markerSize(self, x):
        if self.test_markerSize(x):
            self.markerSize = x
            logging.info('Promjena velicine markera za {0} - {1}, nova vrijednost = {2}'.format(self.tip, self.podtip, x))
###############################################################################
    def set_lineStyle(self, x):
        if self.test_lineStyle(x):
            self.lineStyle = x
            logging.info('Promjena stila linije za {0} - {1}, nova vrijednost = {2}'.format(self.tip, self.podtip, x))
###############################################################################
    def set_lineWidth(self, x):
        if self.test_lineWidth(x):
            self.lineWidth = x
            logging.info('Promjena sirine linije za {0} - {1}, nova vrijednost = {2}'.format(self.tip, self.podtip, x))
###############################################################################
###############################################################################