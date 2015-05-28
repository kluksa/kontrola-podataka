# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 14:42:54 2015

@author: User
"""
import logging

import app.general.pomocne_funkcije as pomocne_funkcije

################################################################################
class KonfigAplikacije():
    """
    Glavni konfiguracijski objekt aplikacije
    """

    def __init__(self, cfg):
        """
        Inicijalizacija sa cfg configparser objektom.

        Konfig sadrzava podatke za:
        -satni graf
        -minutni graf
        -zero graf
        -span graf
        -REST servis
        -opcenite postavke grafa
        """
        logging.debug('Inicijalizacija DTO za sve grafove, start')
        self.conf = cfg
        # mapa dto objekata pomocnih grafova - spremljnih pod kljucem programMjerenjaId
        self.dictPomocnih = {}

        self.satni = SatniGrafKonfig(cfg)
        self.minutni = MinutniGrafKonfig(cfg)
        self.zero = ZeroGrafKonfig(cfg)
        self.span = SpanGrafKonfig(cfg)
        self.REST = RESTKonfig(cfg)
        self.satniRest = SatniRestGrafKonfig(cfg)
        logging.debug('Inicijalizacija DTO za sve grafove, end')

    def dodaj_pomocni(self, key):
        name = 'plot' + str(key)
        self.dictPomocnih[key] = GrafDTO(self.conf, tip='POMOCNI', podtip=name, oblik='plot')
        logging.info('Pomocni graf dodan, mjerenjeId = {0}'.format(key))

    def makni_pomocni(self, key):
        self.dictPomocnih.pop(key)
        logging.info('Pomocni graf maknut, mjerenjeId = {0}'.format(key))


################################################################################
class MetaConfig():
    def __init__(self):
        """
        Definira zajednicke metoda za konfig graf klase.
        """
        self.Midline = None
        self.VOK = None
        self.VBAD = None
        self.NVOK = None
        self.NVBAD = None
        self.EksMin = None
        self.EksMax = None
        self.Fill = None
        self.Grid = False
        self.Cursor = False
        self.Legend = False
        self.Ticks = False
        self.Selector = False
        self.Fill1 = None
        self.Fill2 = None
        self.Warning1 = None
        self.Warning2 = None

    ###definicije setter metoda za boolean vrijednosti (za toggle).
    def set_grid(self, x):
        """boolean setter za prikaz cursora"""
        self.Grid = x
        logging.info('Grid boolean value promjenjen, nova vrijednost = {0}'.format(x))

    def set_cursor(self, x):
        """boolean setter za prikaz cursora"""
        self.Cursor = x
        logging.info('Cursor boolean value promjenjen, nova vrijednost = {0}'.format(x))

    def set_legend(self, x):
        """boolean setter za prikaz legende"""
        self.Legend = x
        logging.info('Legend boolean value promjenjen, nova vrijednost = {0}'.format(x))

    def set_ticks(self, x):
        """boolean setter za prikaz minor tickova"""
        self.Ticks = x
        logging.info('Ticks boolean value promjenjen, nova vrijednost = {0}'.format(x))
################################################################################
class SatniRestGrafKonfig(MetaConfig):
    def __init__(self, cfg):
        super(SatniRestGrafKonfig, self).__init__()
        #konstante
        self.TIP = 'SATNO AGREGIRANI, REST'
        self.MIDLINE = 'avg'
        self.STATUS = 'status'
        self.COUNT = 'obuhvat'
        #podaci o grafovima
        self.Midline = GrafDTO(cfg, tip='SATNI_REST', podtip='midline', oblik='line')
        self.VOK = GrafDTO(cfg, tip='SATNI', podtip='VOK', oblik='scatter') #potreban za highlight
        #interakcija sa grafom
        self.Grid = pomocne_funkcije.load_config_item(cfg,
                                                      'MAIN_WINDOW',
                                                      'action_satni_rest_grid',
                                                      False,
                                                      bool)
        self.Cursor = pomocne_funkcije.load_config_item(cfg,
                                                        'MAIN_WINDOW',
                                                        'action_satni_rest_cursor',
                                                        False,
                                                        bool)
        self.Legend = pomocne_funkcije.load_config_item(cfg,
                                                        'MAIN_WINDOW',
                                                        'action_satni_rest_legend',
                                                        False,
                                                        bool)
        self.Ticks = pomocne_funkcije.load_config_item(cfg,
                                                       'MAIN_WINDOW',
                                                       'action_satni_rest_minor_ticks',
                                                       False,
                                                       bool)
################################################################################
class SatniGrafKonfig(MetaConfig):
    def __init__(self, cfg):
        super(SatniGrafKonfig, self).__init__()
        # konstante
        self.TIP = 'SATNI'
        self.MIDLINE = 'avg'
        self.MINIMUM = 'min'
        self.MAKSIMUM = 'max'
        self.STATUS = 'status'
        self.COUNT = 'count'
        self.FLAG = 'flag'
        #podaci o grafovima
        self.Midline = GrafDTO(cfg, tip='SATNI', podtip='midline', oblik='line')
        self.VOK = GrafDTO(cfg, tip='SATNI', podtip='VOK', oblik='scatter')
        self.VBAD = GrafDTO(cfg, tip='SATNI', podtip='VBAD', oblik='scatter')
        self.NVOK = GrafDTO(cfg, tip='SATNI', podtip='NVOK', oblik='scatter')
        self.NVBAD = GrafDTO(cfg, tip='SATNI', podtip='NVBAD', oblik='scatter')
        self.EksMin = GrafDTO(cfg, tip='SATNI', podtip='ekstrem', oblik='scatter')
        self.EksMax = GrafDTO(cfg, tip='SATNI', podtip='ekstrem', oblik='scatter')
        self.Fill = GrafDTO(cfg, tip='SATNI', podtip='fill1', oblik='fill')
        #interakcija sa grafom
        self.Grid = pomocne_funkcije.load_config_item(cfg,
                                                      'MAIN_WINDOW',
                                                      'action_satni_grid',
                                                      False,
                                                      bool)
        self.Cursor = pomocne_funkcije.load_config_item(cfg,
                                                        'MAIN_WINDOW',
                                                        'action_satni_cursor',
                                                        False,
                                                        bool)
        self.Legend = pomocne_funkcije.load_config_item(cfg,
                                                        'MAIN_WINDOW',
                                                        'action_satni_legend',
                                                        False,
                                                        bool)
        self.Ticks = pomocne_funkcije.load_config_item(cfg,
                                                       'MAIN_WINDOW',
                                                       'action_satni_minor_ticks',
                                                       False,
                                                       bool)
        #status warning plot
        self.statusWarning = GrafDTO(cfg, tip='MAIN_WINDOW',
                                     podtip='status_warning',
                                     oblik='scatter')
################################################################################
class MinutniGrafKonfig(MetaConfig):
    def __init__(self, cfg):
        super(MinutniGrafKonfig, self).__init__()
        # konstante
        self.TIP = 'MINUTNI'
        self.MIDLINE = 'koncentracija'
        self.STATUS = 'status'
        self.FLAG = 'flag'
        #podaci o grafovima
        self.Midline = GrafDTO(cfg, tip='MINUTNI', podtip='midline', oblik='line')
        self.VOK = GrafDTO(cfg, tip='MINUTNI', podtip='VOK', oblik='scatter')
        self.VBAD = GrafDTO(cfg, tip='MINUTNI', podtip='VBAD', oblik='scatter')
        self.NVOK = GrafDTO(cfg, tip='MINUTNI', podtip='NVOK', oblik='scatter')
        self.NVBAD = GrafDTO(cfg, tip='MINUTNI', podtip='NVBAD', oblik='scatter')
        #interakcija sa grafom
        self.Grid = pomocne_funkcije.load_config_item(cfg,
                                                      'MAIN_WINDOW',
                                                      'action_minutni_grid',
                                                      False,
                                                      bool)
        self.Cursor = pomocne_funkcije.load_config_item(cfg,
                                                        'MAIN_WINDOW',
                                                        'action_minutni_cursor',
                                                        False,
                                                        bool)
        self.Legend = pomocne_funkcije.load_config_item(cfg,
                                                        'MAIN_WINDOW',
                                                        'action_minutni_legend',
                                                        False,
                                                        bool)
        self.Ticks = pomocne_funkcije.load_config_item(cfg,
                                                       'MAIN_WINDOW',
                                                       'action_minutni_minor_ticks',
                                                       False,
                                                       bool)
        #status warning
        self.statusWarning = GrafDTO(cfg, tip='MAIN_WINDOW',
                                     podtip='status_warning',
                                     oblik='scatter')
################################################################################
class ZeroGrafKonfig(MetaConfig):
    def __init__(self, cfg):
        super(ZeroGrafKonfig, self).__init__()
        # konstante
        self.TIP = 'ZERO'
        self.MIDLINE = 'vrijednost'
        self.WARNING_LOW = 'minDozvoljeno'
        self.WARNING_HIGH = 'maxDozvoljeno'
        #podaci o grafovima
        self.Midline = GrafDTO(cfg, tip='ZERO', podtip='midline', oblik='line')
        self.VOK = GrafDTO(cfg, tip='ZERO', podtip='VOK', oblik='scatter')
        self.VBAD = GrafDTO(cfg, tip='ZERO', podtip='VBAD', oblik='scatter')
        self.Fill1 = GrafDTO(cfg, tip='ZERO', podtip='fill1', oblik='fill')
        self.Fill2 = GrafDTO(cfg, tip='ZERO', podtip='fill2', oblik='fill')
        self.Warning1 = GrafDTO(cfg, tip='ZERO', podtip='warning', oblik='line')
        self.Warning2 = GrafDTO(cfg, tip='ZERO', podtip='warning', oblik='line')
        #interakcija sa grafom
        self.Grid = pomocne_funkcije.load_config_item(cfg,
                                                      'MAIN_WINDOW',
                                                      'action_ZERO_grid',
                                                      False,
                                                      bool)
        self.Cursor = pomocne_funkcije.load_config_item(cfg,
                                                        'MAIN_WINDOW',
                                                        'action_ZERO_cursor',
                                                        False,
                                                        bool)
        self.Legend = pomocne_funkcije.load_config_item(cfg,
                                                        'MAIN_WINDOW',
                                                        'action_ZERO_legend',
                                                        False,
                                                        bool)
        self.Ticks = pomocne_funkcije.load_config_item(cfg,
                                                       'MAIN_WINDOW',
                                                       'action_ZERO_minor_ticks',
                                                       False,
                                                       bool)
################################################################################
class SpanGrafKonfig(MetaConfig):
    def __init__(self, cfg):
        super(SpanGrafKonfig, self).__init__()
        # konstante
        self.TIP = 'SPAN'
        self.MIDLINE = 'vrijednost'
        self.WARNING_LOW = 'minDozvoljeno'
        self.WARNING_HIGH = 'maxDozvoljeno'
        #podaci o grafovima
        self.Midline = GrafDTO(cfg, tip='SPAN', podtip='midline', oblik='line')
        self.VOK = GrafDTO(cfg, tip='SPAN', podtip='VOK', oblik='scatter')
        self.VBAD = GrafDTO(cfg, tip='SPAN', podtip='VBAD', oblik='scatter')
        self.Fill1 = GrafDTO(cfg, tip='SPAN', podtip='fill1', oblik='fill')
        self.Fill2 = GrafDTO(cfg, tip='SPAN', podtip='fill2', oblik='fill')
        self.Warning1 = GrafDTO(cfg, tip='SPAN', podtip='warning', oblik='line')
        self.Warning2 = GrafDTO(cfg, tip='SPAN', podtip='warning', oblik='line')
        #interakcija sa grafom
        self.Grid = pomocne_funkcije.load_config_item(cfg,
                                                      'MAIN_WINDOW',
                                                      'action_SPAN_grid',
                                                      False,
                                                      bool)
        self.Cursor = pomocne_funkcije.load_config_item(cfg,
                                                        'MAIN_WINDOW',
                                                        'action_SPAN_cursor',
                                                        False,
                                                        bool)
        self.Legend = pomocne_funkcije.load_config_item(cfg,
                                                        'MAIN_WINDOW',
                                                        'action_SPAN_legend',
                                                        False,
                                                        bool)
        self.Ticks = pomocne_funkcije.load_config_item(cfg,
                                                       'MAIN_WINDOW',
                                                       'action_SPAN_minor_ticks',
                                                       False,
                                                       bool)
################################################################################
class RESTKonfig():
    def __init__(self, cfg):
        # konstante za REST
        self.RESTBaseUrl = pomocne_funkcije.load_config_item(cfg,
                                                             'REST_INFO',
                                                             'base_url',
                                                             'http://172.20.1.166:9090/SKZ-war/webresources/',
                                                             str)
        self.RESTProgramMjerenja = pomocne_funkcije.load_config_item(cfg,
                                                                     'REST_INFO',
                                                                     'program_mjerenja',
                                                                     'dhz.skz.aqdb.entity.programmjerenja',
                                                                     str)
        self.RESTSiroviPodaci = pomocne_funkcije.load_config_item(cfg,
                                                                  'REST_INFO',
                                                                  'sirovi_podaci',
                                                                  'dhz.skz.rs.sirovipodaci',
                                                                  str)
        self.RESTZeroSpan = pomocne_funkcije.load_config_item(cfg,
                                                              'REST_INFO',
                                                              'zero_span',
                                                              'dhz.skz.rs.zerospan',
                                                              str)
        self.RESTSatniPodaci = pomocne_funkcije.load_config_item(cfg,
                                                                 'REST_INFO',
                                                                 'satni_podaci',
                                                                 'dhz.skz.rs.satnipodatak',
                                                                 str)
        self.RESTStatusMap = pomocne_funkcije.load_config_item(cfg,
                                                               'REST_INFO',
                                                               'status_map',
                                                               'dhz.skz.rs.sirovipodaci/statusi',
                                                               str)
################################################################################
class GrafDTO():
    """
    Objekt u kojem se pohranjuju postavke pojedinog grafa.
    Samo se pohranjuje informacija o izgledu grafa (markeri, linije ...)

    ulazni parametri za inicijalizaciju:
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

    def __init__(self, cfg, tip='', podtip='', oblik='plot'):
        # bitni memberi
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

    def init_label(self, cfg, tip, podtip):
        placeholder = podtip + ' label placeholder'
        podtip += '_label_'
        val = pomocne_funkcije.load_config_item(cfg, tip, podtip, placeholder, str)
        return str(val)

    def set_label(self, x):
        self.label = str(x)

    def init_zorder(self, cfg, tip, podtip):
        podtip += '_zorder_'
        val = pomocne_funkcije.load_config_item(cfg, tip, podtip, 2, int)
        if self.test_zorder(val):
            return int(val)
        else:
            return 2

    def set_zorder(self, x):
        if self.test_zorder(x):
            self.zorder = x

    def test_zorder(self, x):
        if x > 1:
            return True
        else:
            return False

    def init_komponenta1(self, cfg, tip, podtip):
        podtip += '_komponenta1_'
        val = pomocne_funkcije.load_config_item(cfg, tip, podtip, 'q05', str)
        if self.test_fill_komponenta(val):
            return val
        else:
            return 'q05'

    def init_komponenta2(self, cfg, tip, podtip):
        podtip += '_komponenta2_'
        val = pomocne_funkcije.load_config_item(cfg, tip, podtip, 'q95', str)
        if self.test_fill_komponenta(val):
            return val
        else:
            return 'q95'

    def set_komponenta1(self, x):
        if self.test_fill_komponenta:
            self.komponenta1 = x
            logging.info(
                'Promjena fill komponente za {0} - {1}, nova vrijednost = {2}'.format(self.tip, self.podtip, x))

    def set_komponenta2(self, x):
        if self.test_fill_komponenta:
            self.komponenta2 = x
            logging.info(
                'Promjena fill komponente za {0} - {1}, nova vrijednost = {2}'.format(self.tip, self.podtip, x))

    def test_fill_komponenta(self, x):
        if x in self._sveAgregiraneKomponente:
            return True
        else:
            return False

    def init_rgb(self, cfg, tip, podtip):
        podtip += '_rgb_'
        rgb = pomocne_funkcije.load_config_item(cfg, tip, podtip, (0, 0, 255), tuple)
        # dohvati samo prva 3 elementa
        rgb = rgb[:3]
        #convert to integer vrijednost
        rgb = tuple([int(i) for i in rgb])
        if self.test_rgb(rgb):
            return rgb
        else:
            return 0, 0, 255

    def init_alpha(self, cfg, tip, podtip):
        podtip += '_alpha_'
        alpha = pomocne_funkcije.load_config_item(cfg, tip, podtip, 1.0, float)
        if self.test_alpha(alpha):
            return alpha
        else:
            return 1.0

    def init_crtaj(self, cfg, tip, podtip):
        podtip += '_crtaj_'
        boolCrtaj = pomocne_funkcije.load_config_item(cfg, tip, podtip, True, bool)
        return boolCrtaj

    def init_markerStyle(self, cfg, tip, podtip):
        podtip += '_markerStyle_'
        marker = pomocne_funkcije.load_config_item(cfg, tip, podtip, 'o', str)
        if self.test_markerStyle(marker):
            return marker
        else:
            return 'o'

    def init_markerSize(self, cfg, tip, podtip):
        podtip += '_markerSize_'
        size = pomocne_funkcije.load_config_item(cfg, tip, podtip, 12, int)
        if self.test_markerSize(size):
            return size
        else:
            return 12

    def init_lineStyle(self, cfg, tip, podtip):
        podtip += '_lineStyle_'
        stil = pomocne_funkcije.load_config_item(cfg, tip, podtip, '-', str)
        if self.test_lineStyle(stil):
            return stil
        else:
            return '-'

    def init_lineWidth(self, cfg, tip, podtip):
        podtip += '_lineWidth_'
        sirina = pomocne_funkcije.load_config_item(cfg, tip, podtip, 1.0, float)
        if self.test_lineWidth(sirina):
            return sirina
        else:
            return 1.0

    def test_rgb(self, x):
        out = True
        for i in x:
            if 0 <= i <= 255:
                out = (out and True)
            else:
                out = (out and False)
        return out

    def test_alpha(self, x):
        if x >= 0.0 and x <= 1.0:
            return True
        else:
            return False

    def test_markerStyle(self, x):
        if x in self._sviMarkeri:
            return True
        else:
            return False

    def test_markerSize(self, x):
        if x > 0:
            return True
        else:
            return False

    def test_lineStyle(self, x):
        if x in self._sveLinije:
            return True
        else:
            return False

    def test_lineWidth(self, x):
        if x > 0:
            return True
        else:
            return False

    def set_alpha(self, x):
        if self.test_alpha(x):
            self.alpha = x
            self.color = pomocne_funkcije.make_color(self.rgb, x)
            logging.info('Promjena alfe za {0} - {1}, nova vrijednost = {2}'.format(self.tip, self.podtip, x))

    def set_rgb(self, x):
        if self.test_rgb(x):
            self.rgb = x
            self.color = pomocne_funkcije.make_color(x, self.alpha)
            logging.info('Promjena rgb za {0} - {1}, nova vrijednost = {2}'.format(self.tip, self.podtip, x))

    def set_crtaj(self, x):
        self.crtaj = x
        logging.info('Promjena crtaj booleana za {0} - {1}, nova vrijednost = {2}'.format(self.tip, self.podtip, x))

    def set_markerStyle(self, x):
        if self.test_markerStyle(x):
            self.markerStyle = x
            logging.info('Promjena stila markera za {0} - {1}, nova vrijednost = {2}'.format(self.tip, self.podtip, x))

    def set_markerSize(self, x):
        if self.test_markerSize(x):
            self.markerSize = x
            logging.info(
                'Promjena velicine markera za {0} - {1}, nova vrijednost = {2}'.format(self.tip, self.podtip, x))

    def set_lineStyle(self, x):
        if self.test_lineStyle(x):
            self.lineStyle = x
            logging.info('Promjena stila linije za {0} - {1}, nova vrijednost = {2}'.format(self.tip, self.podtip, x))

    def set_lineWidth(self, x):
        if self.test_lineWidth(x):
            self.lineWidth = x
            logging.info('Promjena sirine linije za {0} - {1}, nova vrijednost = {2}'.format(self.tip, self.podtip, x))
            ################################################################################