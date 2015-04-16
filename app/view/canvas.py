# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 12:27:25 2015

@author: DHMZ-Milic
"""
import datetime
import matplotlib
import functools
import pandas as pd
from PyQt4 import QtGui, QtCore #import djela Qt frejmworka
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas #import specificnog canvasa za Qt
from matplotlib.figure import Figure #import figure
from matplotlib.widgets import RectangleSelector, SpanSelector, Cursor

import app.general.pomocne_funkcije as pomocne_funkcije

################################################################################
################################################################################
class Kanvas(FigureCanvas):
    """
    Canvas za prikaz i interakciju sa grafovima
    """
    def __init__(self, konfig, parent = None, width = 6, height = 5, dpi=100):
        """
        Canvas se inicijalizira sa svojim konfig objektom, mapom pomocnih grafova
        definiranom u objektu tipa KonfigAplikacije u memberu dictPomocnih.
        """
        #osnovna definicija figure, axes i canvasa
        self.fig = Figure(figsize = (width, height), dpi = dpi)
        self.axes = self.fig.add_subplot(111)
        #FigureCanvas.__init__(self, self.fig)
        super(Kanvas,self).__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(
            self,
            QtGui.QSizePolicy.Expanding,
            QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        #podrska za kontekstni meni
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        #bitni memberi
        self.konfig = konfig #konfig dto objekt
        self.data = {} #prazan dict koji ce sadrzavati frejmove sa podacima
        self.gKanal = None #kanal id glavnog kanala
        self.tKontejner = None #kanal id za temperaturu kontejnera za zadani glavni kanal
        self.pocetnoVrijeme = None #min zadano vrijeme za prikaz
        self.zavrsnoVrijeme = None #max zadano vrijeme za prikaz
        self.statusGlavniGraf = False #status glavnog grafa (da li je glavni kanal nacrtan)
        self.statusAnnotation = False #status prikaza annotationa
        self.lastAnnotation = None #kooridinate zadnjeg annotationa
        self.statusHighlight = False #status prikaza oznacene izabrane tocke
        self.lastHighlight = (None, None) #kooridinate zadnjeg highlighta
        self.legenda = None #placeholder za legendu
        self.highlightSize = 15 #dynamic size za highlight (1.5 puta veci od markera)
        self.xlim_original = self.axes.get_xlim() #definicija raspona x osi grafa (zoom)
        self.ylim_original = self.axes.get_ylim() #definicija raspona y osi grafa (zoom)

        self.initialize_interaction(self.span_select, self.rect_zoom)

    def initialize_interaction(self, span_func, zoom_func):
        """
        Setup inicijalnih postavki interakcije sa grafom (zoom, cursor, span selector, pick)

        Ulazni argumenti:

        span_func
        -referenca na funkciju koja ce biti callback za span selektor
        -ulazni parametri su 'min' i 'max' vrijednosti x kooridinate raspona.

        zoom_func
        -referenca na funkciju koja ce biti callback za zoom.
        -ulazni parametri su matplotlib canvas click eventi 'event_click' i 'event_release'
        -npr. kooridinate prve tocke su (event_click.xdata, event_click.ydata)
        """
        #caller id za pick callbackove
        self.cid = None

        #zoom implement, inicijalizacija rectangle selectora za zoom
        self.zoomBoxInfo = dict(facecolor = 'yellow',
                                edgecolor = 'black',
                                alpha = 0.5,
                                fill = True)
        self.zoomSelector = RectangleSelector(self.axes,
                                              zoom_func,
                                              drawtype = 'box',
                                              rectprops = self.zoomBoxInfo)
        self.zoomSelector.set_active(False)

        #cursor implement, inicijalizacija pomocnih lijija cursora
        self.cursorAssist = Cursor(self.axes, useblit = True, color = 'tomato', linewidth = 1)
        self.cursorAssist.visible = False

        #span selector, inicijalizacija span selectora (izbor vise tocaka po x osi)
        self.spanBoxInfo = dict(alpha = 0.3, facecolor = 'yellow')
        self.spanSelector = SpanSelector(self.axes,
                                         span_func,
                                         direction = 'horizontal',
                                         useblit = True,
                                         rectprops = self.spanBoxInfo)
        self.spanSelector.visible = False

    def crtaj_scatter(self, x, y, konfig):
        """
        pomocna funkcija za crtanje scatter grafova
        x, y, su liste kooridinata, konfig je cfg objekt sa postavkama grafa
        """
        self.axes.plot(x,
                       y,
                       marker = konfig.markerStyle,
                       markersize = konfig.markerSize,
                       linestyle = 'None',
                       color = konfig.color,
                       zorder = konfig.zorder,
                       label = konfig.label)

    def crtaj_line(self, x, y, konfig):
        """
        pomocna funkcija za crtanje line grafova
        x, y su liste kooridinata, konfig je cfg objekt sa postavkama grafa
        """
        self.axes.plot(x,
                       y,
                       linestyle = konfig.lineStyle,
                       linewidth = konfig.lineWidth,
                       color = konfig.color,
                       zorder = konfig.zorder,
                       label = konfig.label)

    def crtaj_fill(self, x, y1, y2, konfig):
        """
        pomocna funkcija za crtanje fill grafova
        x definira x os, y1 i y2 su granice izmedju kojih se sjenca,
        konfig je cfg objekt sa postavkama grafa"""
        self.axes.fill_between(x,
                               y1,
                               y2,
                               color = konfig.color,
                               zorder = konfig.zorder,
                               label = konfig.label)

    def toggle_ticks(self, x):
        """
        Toggle minor tickova on i off ovisno o ulaznoj vrijednosti x (boolean).
        """
        if x and self.statusGlavniGraf:
            self.axes.minorticks_on()
        else:
            self.axes.minorticks_off()
        self.draw()

    def toggle_grid(self, x):
        """
        Toggle grida on i off, ovisno o ulaznoj vrijednosti x (boolean)
        """
        if x and self.statusGlavniGraf:
            self.axes.grid(True)
        else:
            self.axes.grid(False)
        self.draw()

    def toggle_legend(self, x):
        """
        Toggle legende on i off, ovisno o ulaznoj vrijednosti x (boolean)
        """
        if self.legenda is not None:
            if x and self.statusGlavniGraf:
                self.legenda.set_visible(True)
            else:
                self.legenda.set_visible(False)
        self.draw()

    def disconnect_pick_evente(self):
        """Opceniti disconnect pick eventa. Pick eventi se trebaju odspojiti prilikom
        zoom akcije i prilikom izbora vise tocaka uz pomoc span selektora (izbjegavanje
        konfliktnih matplotlib signala)."""
        if self.cid:
            self.mpl_disconnect(self.cid)
            self.cid = None

    def set_interaction_mode(self, zoom, cursor, span):
        """
        Toggle nacina interakcije, ovisno o zeljenom nacinu interakcije sa canvasom.
        zoom --> boolean
        cursor --> boolean
        span --> boolean
        """
        #set up pick callbacks ovisno o tipu grafa
        self.disconnect_pick_evente()
        self.connect_pick_evente()
        if zoom:
            #zoom on, all else off
            self.zoomSelector.set_active(True)
            self.cursorAssist.visible = False
            self.spanSelector.visible = False
            self.disconnect_pick_evente()
        else:
            #zoom off
            self.zoomSelector.set_active(False)
            if cursor:
                self.cursorAssist.visible = True
            else:
                self.cursorAssist.visible = False
            if span:
                self.spanSelector.visible = True
                self.disconnect_pick_evente()
            else:
                self.spanSelector.visible = False

    def connect_pick_evente(self):
        """
        Matplotlib connection ovisno o tipu canvasa. Reimplementiraj za pojedini graf.
        Predvidjeni connection member je self.cid
        """
        pass

    def span_select(self, tmin, tmax):
        """
        span select placeholder, funkcija ima dva ulazna parametra. Minimalnu i
        maksimalnu vrijednosti izabarnog raspona po x kooridinati grafa.
        """
        pass

    def rect_zoom(self, eclick, erelease):
        """
        Primjer callback funkcije za zoom.
        Callback funkcija za rectangle zoom canvasa. Funkcija lovi click i release
        evente (rubovi kvadrata) te povecava izabrani dio slike preko cijelog
        canvasa.
        """
        x = sorted([eclick.xdata, erelease.xdata])
        y = sorted([eclick.ydata, erelease.ydata])
        #set nove granice osi za sve axese
        for ax in self.fig.axes:
            ax.set_xlim(x)
            ax.set_ylim(y)
        #redraw
        self.draw()

    def full_zoom_out(self):
        """
        Reset granica x i y osi da pokrivaju isti raspon kao i originalna slika.
        Full zoom out.

        vrijednosti su spremljene u memberima u obliku tuple
        self.xlim_original --> (xmin, xmax)
        self.ylim_original --> (ymin, ymax)
        """
        self.axes.set_xlim(self.xlim_original)
        self.axes.set_ylim(self.ylim_original)
        #nacrtaj promjenu
        self.draw()

    def clear_graf(self):
        """
        clear grafa
        """
        self.data = {} #spremnik za frejmove (ucitane)
        self.statusGlavniGraf = False
        self.statusAnnotation = False
        self.statusHighlight = False
        self.lastHighlight = (None, None)
        self.lastAnnotation = None
        self.axes.clear()
        #redo Axes labels
        self.axes.set_xlabel('Vrijeme')
        self.axes.set_ylabel(self.konfig.TIP)
        self.draw()

    def setup_ticks(self):
        """
        Postavljanje pozicije i formata tickova x osi.
        """
        tickovi = self.pronadji_tickove()
        self.majorTickLoc = tickovi['majorTickovi']
        self.majorTickLab = tickovi['majorLabeli']
        self.minorTickLoc = tickovi['minorTickovi']
        self.minorTickLab = tickovi['minorLabeli']

        self.axes.set_xticks(self.majorTickLoc, minor = False)
        self.axes.set_xticklabels(self.majorTickLab, minor = False)
        self.axes.set_xticks(self.minorTickLoc, minor = True)
        self.axes.set_xticklabels(self.minorTickLab, minor = True)

        allXLabels = self.axes.get_xticklabels(which = 'both') #dohvati sve labele
        for label in allXLabels:
            label.set_rotation(30)
            label.set_fontsize(8)

    def setup_legend(self):
        """
        Setup legende na canvas.
        """
        self.legenda = self.axes.legend(loc = 1,
                                        fontsize = 8,
                                        fancybox = True)
        self.legenda.get_frame().set_alpha(0.8)

    def crtaj(self, frejmovi, mapaParametara):
        """
        Glavna metoda za crtanje grafa.
        Ulazni parametri su:
        frejmovi --> mapa {programMjerenjaId:pandas datafrejm}
        mapaParametara --> dict sa 'meta' podacima (glavni kanal, pocetno vrijeme,
        zavrsno vrijeme....)
        """
        pass
################################################################################
class SatniMinutniKanvas(Kanvas):
    """
    Kanvas klasa sa zajednickim elementima za satni i minutni graf.
    Inicijalizacija sa konfig objektom i mapom pomocnih kanala.
    """
    def __init__(self, konfig, pomocni, parent = None, width = 6, height = 5, dpi=100):
        super(SatniMinutniKanvas, self).__init__(self, konfig)
        self.pomocniGrafovi = pomocni #mapa pomocnih kanala {kanalId:dto objekt za kanal}

    def connect_pick_evente(self):
        """
        connect canvas pick event sa metodom self.on_pick
        """
        self.cid = self.mpl_connect('button_press_event', self.on_pick)

    def crtaj_scatter_value_ovisno_o_flagu(self, komponenta, konfig, flag):
        """
        Pomocna funkcija za crtanje scatter tipa grafa (samo tocke).
        -komponenta je opisni string ( ['min', 'max', 'koncentracija', 'avg'])
        -konfig je objekt sa postavkama grafa
        -flag je int vrijednost flaga za razlikovanje validacije ili None (za sve
        tocke neovisno o flagu)

        Metodu koristi satni i minutni graf jer jedino oni crtaju tocke ovisno
        o flagu. Flag moze biti None, u tom slucaju se crtaju sve tocke (primjer
        je crtanje ekstremnih vrijednosti na satnom grafu).
        """
        frejm = self.data[self.gKanal]
        if flag:
            frejm = frejm[frejm[self.konfig.FLAG] == flag]
        x = list(frejm.index)
        #crtaj samo ako ima podataka
        if len(x):
            if komponenta == 'min':
                y = list(frejm['min'])
            elif komponenta == 'max':
                y = list(frejm['max'])
            elif komponenta == 'koncentracija':
                y = list(frejm['koncentracija'])
            elif komponenta == 'avg':
                y = list(frejm['avg'])
            else:
                return
            #naredba za plot
            self.crtaj_scatter(x, y, konfig)
            self.statusGlavniGraf = True

    def crtaj_pomocne(self, popis):
        """
        Metoda za crtanje pomocnih grafova. Ulazni parametar popis je set id
        oznaka programa mjerenja. Ulazni parametar tip, definira tip grafa
        (satni ili minutni)
        """
        for key in popis:
            frejm = self.data[key]
            if len(frejm):
                x = list(frejm.index)
                y = list(frejm[self.konfig.MIDLINE])
                self.axes.plot(x,
                               y,
                               marker=self.pomocniGrafovi[key].markerStyle,
                               markersize=self.pomocniGrafovi[key].markerSize,
                               linestyle=self.pomocniGrafovi[key].lineStyle,
                               linewidth=self.pomocniGrafovi[key].lineWidth,
                               color=self.pomocniGrafovi[key].color,
                               zorder=self.pomocniGrafovi[key].zorder,
                               label=self.pomocniGrafovi[key].label)

    def crtaj_oznake_temperature(self, tempMin, tempMax):
        """
        Crtanje oznaka za temperaturu kontejnera ako su izvan zadanih granica
        """
        if self.tKontejner in self.data.keys():
            frejm = self.data[self.tKontejner]
            frejm = frejm[frejm[self.konfig.FLAG] > 0]
            if len(frejm):
                overlimit = frejm[frejm[self.konfig.MIDLINE] > tempMax]
                underlimit = frejm[frejm[self.konfig.MIDLINE] < tempMin]
                frejm = overlimit.append(underlimit)
                x = list(frejm.index)
                brojLosih = len(x)
                if brojLosih:
                    y1, y2 = self.ylim_original
                    c = y2 - 0.05 * abs(y2 - y1)  # odmak od gornjeg ruba za 5% max raspona
                    y = [c for i in range(brojLosih)]
                    self.axes.plot(x,
                                   y,
                                   marker='*',
                                   color='Red',
                                   linestyle='None',
                                   alpha=0.4)

    def setup_annotation_offset(self, event):
        """
        Funkcija postavlja annotation offset ovisno o polozaju klika na canvas.
        """
        size = self.frameSize()
        x, y = size.width(), size.height()
        x = x//2
        y = y//2
        clickedx = event.x
        clickedy = event.y

        if clickedx >= x:
            clickedx = -80
            if clickedy >= y:
                clickedy = -30
            else:
                clickedy = 30
        else:
            clickedx = 30
            if clickedy >= y:
                clickedy = -30
            else:
                clickedy = 30
        return (clickedx, clickedy)

    def setup_annotation_text(self, xpoint):
        """
        Definiranje teksta za prikaz annotationa (sto ce biti unutar annotationa).
        Ulazni parametar je tocka za koju radimo annotation. Funkcija vraca string
        teksta annotationa.
        """
        pass

    def annotate_pick(self, point, event):
        """
        Mangage annotation za pick event
        point --> (x, y) tuple tocke
        event --> matplotlib click event
        """
        if self.statusAnnotation:
            self.annotation.remove()
            self.statusAnnotation = False
            if point[0] is not self.lastAnnotation:
                self.make_annotation(point, event)
        else:
            self.make_annotation(point, event)
        self.draw()

    def make_annotation(self, point, event):
        """
        Metoda stvara annotation objekt koji ce se prikazati na grafu.
        ulazni parametri su:
        point ---> tocka na grafu
        event ---> matplotlib event koji je triggerao annotation
        Annotation instance object, pozicija na grafu.
        """
        #set offset annotationa
        offs = self.setup_annotation_offset(event)
        #set tekst annotationa
        tekst = self.setup_annotation_text() #overload metodu za specificni graf
        self.annotation = self.axes.annotate(
                    tekst,
                    xy = point,
                    xytext = offs,
                    textcoords = 'offset points',
                    ha = 'left',
                    va = 'center',
                    fontsize = 7,
                    zorder = 102,
                    bbox = dict(boxstyle = 'square', fc = 'cyan', alpha = 0.7),
                    arrowprops = dict(arrowstyle = '->'))
        self.lastAnnotation = point[0]
        self.statusAnnotation = True

    def zaokruzi_na_najblize_vrijeme(self, x):
        """
        Metoda sluzi za zaokruzivanje vremena tocke na neku mjernu jedinicu.
        Reimplementiraj za pojedini canvas
        """
        pass

    def adaptiraj_tocku_od_pick_eventa(self, event):
        """
        Metoda je zaduzena da prilagodi podatke iz eventa.
        Metoda vraca x i y kooridinate tocke.
        """
        xpoint = matplotlib.dates.num2date(event.xdata) #datetime.datetime
        #problem.. rounding offset aware i offset naive datetimes..workaround
        xpoint = datetime.datetime(xpoint.year,
                                   xpoint.month,
                                   xpoint.day,
                                   xpoint.hour,
                                   xpoint.minute,
                                   xpoint.second)
        xpoint = self.zaokruzi_na_najblize_vrijeme(xpoint) #round na najblize vrijeme
        xpoint = pd.to_datetime(xpoint) #konverzija iz datetime.datetime objekta u pandas.tislib.Timestamp
        #pazimo da x vrijednost ne iskace od zadanih granica
        if xpoint >= self.zavrsnoVrijeme:
            xpoint = self.zavrsnoVrijeme
        if xpoint <= self.pocetnoVrijeme:
            xpoint = self.pocetnoVrijeme
        #kooridinate ako nedostaju podaci za highlight
        if xpoint in list(self.data[self.gKanal].index):
            ypoint = self.data[self.gKanal].loc[xpoint, self.konfig.MIDLINE]
        else:
            miny = self.data[self.gKanal][self.konfig.MIDLINE].min()
            maxy = self.data[self.gKanal][self.konfig.MIDLINE].max()
            ypoint = (miny + maxy)/2

        return xpoint, ypoint


    def on_pick(self, event):
        """
        Resolve pick eventa za satni i minutni graf.
        """
        pass

    def span_select(self, xmin, xmax):
        """
        Primjer callback metode za span selektor.
        Metoda je povezana sa span selektorom (ako je inicijaliziran).
        Metoda je zaduzena da prikaze kontekstni dijalog za promjenu flaga
        na mjestu gdje "releasamo" ljevi klik za satni i minutni graf.

        t1 i t2 su timestampovi, ali ih treba adaptirati iz matplotlib vremena u
        "zaokruzene" pandas timestampove. (na minutnom grafu se zaokruzuje na najblizu
        minutu, dok na satnom na najblizi sat)
        """
        if self.statusGlavniGraf: #glavni graf mora biti nacrtan
            #konverzija ulaznih vrijednosti u pandas timestampove
            t1 = matplotlib.dates.num2date(xmin)
            t2 = matplotlib.dates.num2date(xmax)
            t1 = datetime.datetime(t1.year, t1.month, t1.day, t1.hour, t1.minute, t1.second)
            t2 = datetime.datetime(t2.year, t2.month, t2.day, t2.hour, t2.minute, t2.second)
            #vremena se zaokruzuju
            t1 = self.zaokruzi_na_najblize_vrijeme(t1)
            t2 = self.zaokruzi_na_najblize_vrijeme(t2)
            #adapt from datetime.datetime objekta u pandas timestamp
            t1 = pd.to_datetime(t1)
            t2 = pd.to_datetime(t2)
            #osiguranje da se ne preskoce granice glavnog kanala (izbjegavanje index errora)
            if t1 < self.pocetnoVrijeme:
                t1 = self.pocetnoVrijeme
            if t1 > self.zavrsnoVrijeme:
                t1 = self.zavrsnoVrijeme
            if t2 < self.pocetnoVrijeme:
                t2 = self.pocetnoVrijeme
            if t2 > self.zavrsnoVrijeme:
                t2 = self.zavrsnoVrijeme
            #tocke ne smiju biti iste (izbjegavamo paljenje dijaloga na ljevi klik)
            if t1 != t2:
                #pronadji lokaciju desnog klika u Qt kooridinatama.
                loc = QtGui.QCursor.pos()
                self.show_context_menu(loc, t1, t2) #poziv kontekstnog menija

    def show_context_menu(self, pos, tmin, tmax):
        """
        Metoda iscrtava kontekstualni meni sa opcijama za promjenom flaga
        na minutnom i satnom grafu.
        Promjena se radi na minutnim podacima pa je nuzno pripaziti kod promjene
        na satnom grafu jer moramo prilikom poziva ove metode pomaknuti tmin
        59 minuta unazad da uhvatimo sve relevantne podatke.
        """
        #zapamti rubna vremena intervala, trebati ce za druge metode
        self.__lastTimeMin = tmin
        self.__lastTimeMax = tmax
        #definiraj menu i postavi akcije u njega
        menu = QtGui.QMenu(self)
        menu.setTitle('Promjeni flag')
        action1 = QtGui.QAction("Flag: dobar", menu)
        action2 = QtGui.QAction("Flag: los", menu)
        menu.addAction(action1)
        menu.addAction(action2)
        #povezi akcije menua sa metodama
        action1.triggered.connect(functools.partial(self.promjena_flaga, flag = 1000))
        action2.triggered.connect(functools.partial(self.promjena_flaga, flag = -1000))
        #prikazi menu na definiranoj tocki grafa
        menu.popup(pos)

    def promjena_flaga(self, flag = 1):
        """
        Metoda sluzi za promjenu flaga.
        """
        tmin = self.__lastTimeMin
        tmax = self.__lastTimeMax
        arg = {'od': tmin,
               'do': tmax,
               'noviFlag': flag,
               'kanal': self.gKanal}
        #generalni emit za promjenu flaga
        self.emit(QtCore.SIGNAL('promjeni_flag(PyQt_PyObject)'), arg)

################################################################################
class SatniKanvas(SatniMinutniKanvas):
    """
    Klasa kanvasa za satni graf.
    Inicijalizacija sa konfig objektom i mapom pomocnih kanala
    """
    def __init__(self, konfig, pomocni, parent = None, width = 6, height = 5, dpi=100):
        super(SatniKanvas, self).__init__(self, konfig, pomocni)
        self.highlightSize = 1.5 * self.konfig.VOK.markerSize
        self.axes.set_ylabel(self.konfig.TIP)
        #inicijalni setup za interakciju i display(pick, zoom, ticks...)
        self.initialize_interaction(self.span_select, self.rect_zoom)
        self.set_interaction_mode(self.konfig.Zoom, self.konfig.Cursor, self.konfig.Selector)
        self.toggle_grid(self.konfig.Grid)
        self.toggle_ticks(self.konfig.Ticks)

    def crtaj(self, frejmovi, mapaParametara):
        """
        PROMJENA : direktno prosljedjivanje frejmova za crtanje...bez signala

        Glavna metoda za crtanje na canvas. Eksplicitne naredbe za crtanje.
        ulazni argumenti:
        frejmovi:
        -Mapa programMjerenjaId:pandas dataframe.
        -Podaci za crtanje

        mapaParametara:
        -mapa sa potrebnim parametrima
        -mapaParametara['kanalId'] --> program mjerenja id glavnog kanala [int]
        -mapaParametara['pocetnoVrijeme'] --> pocetno vrijeme [pandas timestamp]
        -mapaParametara['zavrsnoVrijeme'] --> zavrsno vrijeme [pandas timestamp]
        -mapaParametara['tempKontejner'] --> temperatura kontejnera id (ili None) [int]
        """
        #clear prethodnog grafa, reinicijalizacija membera
        self.clear_graf()
        self.data = frejmovi
        self.pocetnoVrijeme = mapaParametara['pocetnoVrijeme']
        self.zavrsnoVrijeme = mapaParametara['zavrsnoVrijeme']
        self.gKanal = mapaParametara['kanalId']
        self.tKontejner = mapaParametara['tempKontejner']
        if self.gKanal in self.data.keys():
            #naredba za crtanje glavnog grafa
            self.crtaj_glavni_kanal()
            #set dostupnih pomocnih kanala za crtanje
            pomocni = set(self.data.keys()) - set([self.gKanal, self.tKontejner])
            #naredba za crtanje pomocnih
            self.crtaj_pomocne(pomocni)
            ###micanje tocaka od rubova, tickovi, legenda...
            self.setup_limits()
            self.setup_legend()
            self.setup_ticks()
            #toggle ticks, legend, grid
            self.toggle_tgl()
            self.crtaj_oznake_temperature(15,30)
            #highlight prijasnje tocke
            if self.statusHighlight:
                hx, hy = self.lastHighlight
                if hx in self.data[self.gKanal].index:
                    #pronadji novu y vrijednosti indeksa
                    hy = self.data[self.gKanal].loc[hx, self.konfig.MIDLINE]
                    self.make_highlight(hx, hy, self.highlightSize)
                else:
                    self.statusHighlight = False
                    self.lastHighlight = (None, None)
            self.draw()
        else:
            self.axes.text(0.5,
                           0.5,
                           'Nije moguce pristupiti podacima za trazeni kanal.',
                           horizontalalignment='center',
                           verticalalignment='center',
                           fontsize = 8,
                           transform = self.axes.transAxes)
            self.draw()

    def crtaj_glavni_kanal(self):
        """
        crtanje podataka glavnog kanala.
        """
        #midline
        frejm = self.data[self.gKanal]
        x = list(frejm.index)
        y = list(frejm[self.konfig.MIDLINE])
        self.crtaj_line(x, y, self.konfig.Midline)
        #fill izmedju komponenti
        if self.konfig.Fill.crtaj:
            self.crtaj_fill(x,
                            list(frejm[self.konfig.Fill.komponenta1]),
                            list(frejm[self.konfig.Fill.komponenta2]),
                            self.konfig.Fill)
        #ekstremi min i max
        if self.konfig.EksMin.crtaj:
            self.crtaj_scatter_value_ovisno_o_flagu(self.MINIMUM, self.konfig.EksMin, None)
            self.crtaj_scatter_value_ovisno_o_flagu(self.MAKSIMUM, self.konfig.EksMax, None)

        #plot tocaka ovisno o flagu i validaciji
        self.crtaj_scatter_value_ovisno_o_flagu(self.MIDLINE, self.konfig.VOK, 1000)
        self.crtaj_scatter_value_ovisno_o_flagu(self.MIDLINE, self.konfig.VBAD, -1000)
        self.crtaj_scatter_value_ovisno_o_flagu(self.MIDLINE, self.konfig.NVOK, 1)
        self.crtaj_scatter_value_ovisno_o_flagu(self.MIDLINE, self.konfig.NVBAD, -1)
        self.statusGlavniGraf = True

    def setup_limits(self):
        """
        Prosirivanje granica grafa da ticke nisu na rubu.
        Konacne granice se spremaju u member xlim_original i ylim_original
        radi implementacije zoom out metode.
        """
        #odmakni x granice za specificni interval ovisno o tipu
        tmin, tmax = pomocne_funkcije.prosiri_granice_grafa(self.pocetnoVrijeme, self.zavrsnoVrijeme, 60)
        #set granice za max zoom out
        self.xlim_original = (tmin, tmax)
        self.ylim_original = self.axes.get_ylim()
        #set granice grafa
        self.axes.set_xlim(self.xlim_original)
        self.axes.set_ylim(self.ylim_original)

    def pronadji_tickove(self):
        """
        funkcija vraca listu tickmarkera i listu tick labela za satni graf.
        -vremenski raspon je tmin, tmax
        -tickovi su razmaknuti 1 sat
        vrati dict sa listama lokacija i labela za tickove
        """
        tmin = self.pocetnoVrijeme
        tmax = self.zavrsnoVrijeme
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

    def toggle_tgl(self):
        self.toggle_ticks(self.konfig.Ticks)
        self.toggle_grid(self.konfig.Grid)
        self.toggle_legend(self.konfig.Legend)

    def setup_annotation_text(self, xpoint):
        """
        Definiranje teksta za prikaz annotationa (sto ce biti unutar annotationa).
        Ulazni parametar je tocka za koju radimo annotation. Funkcija vraca string
        teksta annotationa.
        """
        if xpoint in list(self.data[self.gKanal].index):
            yavg = self.data[self.gKanal].loc[xpoint, self.konfig.MIDLINE]
            ymin = self.data[self.gKanal].loc[xpoint, self.konfig.MINIMUM]
            ymax = self.data[self.gKanal].loc[xpoint, self.konfig.MAKSIMUM]
            ystatus = self.data[self.gKanal].loc[xpoint, self.konfig.STATUS]
            ycount = self.data[self.gKanal].loc[xpoint, self.konfig.COUNT]
            tekst = 'Vrijeme: '+str(xpoint)+'\nAverage: '+str(yavg)+'\nMin:'+str(ymin)+'\nMax:'+str(ymax)+'\nStatus:'+str(ystatus)+'\nCount:'+str(ycount)
        else:
            tekst = 'Vrijeme: '+str(xpoint)+'\nNema podataka'
        return tekst

    def zaokruzi_na_najblize_vrijeme(self, xpoint):
        """
        Metoda sluzi za zaokruzivanje vremena zadanog ulaznim parametrom xpoint na
        najblizi puni sat.
        """
        return pomocne_funkcije.zaokruzi_vrijeme(xpoint, 3600)

    def highlight_pick(self, tpl, size):
        """
        naredba za crtanje highlight tocke na grafu na koridinatama
        tpl = (x, y), velicine size.
        """
        x, y = tpl
        if self.statusHighlight:
            if tpl is not self.lastHighlight:
                self.axes.lines.remove(self.highlight[0])
                self.make_highlight(x, y, size)
        else:
            self.make_highlight(x, y, size)

        self.draw()

    def make_highlight(self, x, y, size):
        """
        Generiranje instance highlight tocke na kooridinati x, y za prikaz.
        Velicina markera je definirana sa ulaznim parametrom size.
        """
        self.highlight = self.axes.plot(x,
                                        y,
                                        marker = 'o',
                                        markersize = int(size),
                                        color = 'yellow',
                                        alpha = 0.5,
                                        zorder = 10)
        self.lastHighlight = (x, y)
        self.statusHighlight = True

    def on_pick(self, event):
        """
        Resolve pick eventa za satni graf.
        ljevi klik misa --> highlight tocke i naredba za crtanje minutnog grafa
        middle klik misa --> annotation sa agregiranim podacima
        desni klik misa --> poziv kontektsnog menija za promjenu flaga
        """
        if self.statusGlavniGraf and event.inaxes == self.axes:
            xpoint, ypoint = self.adaptiraj_tocku_od_pick_eventa(event)
            if event.button == 1:
                self.emit(QtCore.SIGNAL('crtaj_minutni_graf(PyQt_PyObject)'), xpoint) #crtanje minutnog
                self.highlight_pick((xpoint, ypoint), self.highlightSize) #highlight odabir, size pointa
            elif event.button == 2:
                self.annotate_pick((xpoint, ypoint), event)
            elif event.button == 3:
                loc = QtGui.QCursor.pos() #lokacija klika
                #odmakni donj limit intervala za 59 minuta od izabrane tocke xpoint
                lowlim = xpoint - datetime.timedelta(minutes = 59)
                lowlim = pd.to_datetime(lowlim)
                self.show_context_menu(loc, lowlim, xpoint) #interval koji treba promjeniti

    def span_select(self, xmin, xmax):
        """
        Primjer callback metode za span selektor.
        Metoda je povezana sa span selektorom (ako je inicijaliziran).
        Metoda je zaduzena da prikaze kontekstni dijalog za promjenu flaga
        na mjestu gdje "releasamo" ljevi klik za satni i minutni graf.

        t1 i t2 su timestampovi, ali ih treba adaptirati iz matplotlib vremena u
        "zaokruzene" pandas timestampove. (na minutnom grafu se zaokruzuje na najblizu
        minutu, dok na satnom na najblizi sat)
        """
        if self.statusGlavniGraf: #glavni graf mora biti nacrtan
            #konverzija ulaznih vrijednosti u pandas timestampove
            t1 = matplotlib.dates.num2date(xmin)
            t2 = matplotlib.dates.num2date(xmax)
            t1 = datetime.datetime(t1.year, t1.month, t1.day, t1.hour, t1.minute, t1.second)
            t2 = datetime.datetime(t2.year, t2.month, t2.day, t2.hour, t2.minute, t2.second)
            #vremena se zaokruzuju
            t1 = self.zaokruzi_na_najblize_vrijeme(t1)
            t2 = self.zaokruzi_na_najblize_vrijeme(t2)
            #adapt from datetime.datetime objekta u pandas timestamp
            t1 = pd.to_datetime(t1)
            t2 = pd.to_datetime(t2)
            #osiguranje da se ne preskoce zadane granice grafa
            if t1 < self.pocetnoVrijeme:
                t1 = self.pocetnoVrijeme
            if t1 > self.zavrsnoVrijeme:
                t1 = self.zavrsnoVrijeme
            if t2 < self.pocetnoVrijeme:
                t2 = self.pocetnoVrijeme
            if t2 > self.zavrsnoVrijeme:
                t2 = self.zavrsnoVrijeme
            #tocke ne smiju biti iste (izbjegavamo paljenje dijaloga na ljevi klik)
            if t1 != t2:
                #pronadji lokaciju u Qt kooridinatama.
                loc = QtGui.QCursor.pos()
                #odmakni donj limit intervala za 59 minuta od izabrane tocke xpoint
                lowlim = t1 - datetime.timedelta(minutes = 59)
                lowlim = pd.to_datetime(lowlim)
                self.show_context_menu(loc, lowlim, t2) #poziv kontekstnog menija
################################################################################
class MinutniKanvas(SatniMinutniKanvas):
    """
    Klasa kanvasa za minutni graf.
    Inicijalizacija sa konfig objektom i mapom pomocnih kanala
    """
    def __init__(self, konfig, pomocni, parent = None, width = 6, height = 5, dpi=100):
        super(SatniKanvas, self).__init__(self, konfig, pomocni)
        self.axes.set_ylabel(self.konfig.TIP)
        #inicijalni setup za interakciju i display(pick, zoom, ticks...)
        self.initialize_interaction(self.span_select, self.rect_zoom)
        self.set_interaction_mode(self.konfig.Zoom, self.konfig.Cursor, self.konfig.Selector)
        self.toggle_grid(self.konfig.Grid)
        self.toggle_ticks(self.konfig.Ticks)

    def crtaj(self, frejmovi, mapaParametara):
        """
        PROMJENA : direktno prosljedjivanje frejmova za crtanje...bez signala

        Glavna metoda za crtanje na canvas. Eksplicitne naredbe za crtanje.
        ulazni argumenti:
        frejmovi:
        -Mapa programMjerenjaId:pandas dataframe.
        -Podaci za crtanje

        mapaParametara:
        -mapa sa potrebnim parametrima
        -mapaParametara['kanalId'] --> program mjerenja id glavnog kanala [int]
        -mapaParametara['pocetnoVrijeme'] --> pocetno vrijeme [pandas timestamp]
        -mapaParametara['zavrsnoVrijeme'] --> zavrsno vrijeme [pandas timestamp]
        -mapaParametara['tempKontejner'] --> temperatura kontejnera id (ili None) [int]
        """
        #clear prethodnog grafa, reinicijalizacija membera
        self.clear_graf()
        self.data = frejmovi
        self.pocetnoVrijeme = mapaParametara['pocetnoVrijeme']
        self.zavrsnoVrijeme = mapaParametara['zavrsnoVrijeme']
        self.gKanal = mapaParametara['kanalId']
        self.tKontejner = mapaParametara['tempKontejner']
        if self.gKanal in self.data.keys():
            #naredba za crtanje glavnog grafa
            self.crtaj_glavni_kanal()
            #set dostupnih pomocnih kanala za crtanje
            pomocni = set(self.data.keys()) - set([self.gKanal, self.tKontejner])
            #naredba za crtanje pomocnih
            self.crtaj_pomocne(pomocni)
            ###micanje tocaka od rubova, tickovi, legenda...
            self.setup_limits()
            self.setup_legend()
            self.setup_ticks()
            #toggle ticks, legend, grid
            self.toggle_tgl()
            self.crtaj_oznake_temperature(15,30)
            self.draw()
        else:
            self.axes.text(0.5,
                           0.5,
                           'Nije moguce pristupiti podacima za trazeni kanal.',
                           horizontalalignment='center',
                           verticalalignment='center',
                           fontsize = 8,
                           transform = self.axes.transAxes)
            self.draw()


    def crtaj_glavni_kanal(self):
        """
        crtanje podataka glavnog kanala.
        """
        #midline
        frejm = self.data[self.gKanal]
        x = list(frejm.index)
        y = list(frejm[self.konfig.MIDLINE])
        self.crtaj_line(x, y, self.konfig.Midline)
        #plot tocaka ovisno o flagu i validaciji
        self.crtaj_scatter_value_ovisno_o_flagu(self.MIDLINE, self.konfig.VOK, 1000)
        self.crtaj_scatter_value_ovisno_o_flagu(self.MIDLINE, self.konfig.VBAD, -1000)
        self.crtaj_scatter_value_ovisno_o_flagu(self.MIDLINE, self.konfig.NVOK, 1)
        self.crtaj_scatter_value_ovisno_o_flagu(self.MIDLINE, self.konfig.NVBAD, -1)
        self.statusGlavniGraf = True

    def setup_limits(self):
        """
        Prosirivanje granica grafa da ticke nisu na rubu.
        Konacne granice se spremaju u member xlim_original i ylim_original
        radi implementacije zoom out metode.
        """
        #odmakni x granice za specificni interval ovisno o tipu
        tmin, tmax = pomocne_funkcije.prosiri_granice_grafa(self.pocetnoVrijeme, self.zavrsnoVrijeme, 5)
        #set granice za max zoom out
        self.xlim_original = (tmin, tmax)
        self.ylim_original = self.axes.get_ylim()
        #set granice grafa
        self.axes.set_xlim(self.xlim_original)
        self.axes.set_ylim(self.ylim_original)

    def pronadji_tickove(self):
        """
        funkcija vraca liste tickmarkera (minor i major) i listu tick labela
        za minutni graf.
        """
        tmin = self.pocetnoVrijeme
        tmax = self.zavrsnoVrijeme

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


    def toggle_tgl(self):
        self.toggle_ticks(self.konfig.Ticks)
        self.toggle_grid(self.konfig.Grid)
        self.toggle_legend(self.konfig.Legend)

    def setup_annotation_text(self, xpoint):
        """
        Definiranje teksta za prikaz annotationa (sto ce biti unutar annotationa).
        Ulazni parametar je tocka za koju radimo annotation. Funkcija vraca string
        teksta annotationa.
        """
        if xpoint in list(self.data[self.gKanal].index):
            ykonc = self.data[self.gKanal].loc[xpoint, self.konfig.MIDLINE]
            ystat = self.data[self.gKanal].loc[xpoint, self.konfig.STATUS]
            yflag = self.data[self.gKanal].loc[xpoint, self.konfig.FLAG]
            tekst = 'Vrijeme: '+str(xpoint)+'\nKoncentracija: '+str(ykonc)+'\nStatus:'+str(ystat)+'\nFlag:'+str(yflag)
        else:
            tekst = 'Vrijeme: '+str(xpoint)+'\nNema podataka'
        return tekst

    def zaokruzi_na_najblize_vrijeme(self, xpoint):
        """
        Metoda sluzi za zaokruzivanje vremena zadanog ulaznim parametrom xpoint na
        najblizu punu minutu.
        """
        return pomocne_funkcije.zaokruzi_vrijeme(xpoint, 60)

    def on_pick(self, event):
        """
        Resolve pick eventa za minutni graf.
        ljevi klik misa --> highlight tocke i naredba za crtanje minutnog grafa
        middle klik misa --> annotation sa agregiranim podacima
        desni klik misa --> poziv kontektsnog menija za promjenu flaga
        """
        if self.statusGlavniGraf and event.inaxes == self.axes:
            xpoint, ypoint = self.adaptiraj_tocku_od_pick_eventa(event)
            if event.button == 2:
                self.annotate_pick((xpoint, ypoint), event)
            elif event.button == 3:
                loc = QtGui.QCursor.pos() #lokacija klika
                self.show_context_menu(loc, xpoint, xpoint) #interval koji treba promjeniti
################################################################################
class ZeroSpanKanvas(Kanvas):
    """
    Kanvas klasa sa zajednickim elementima za zero i span graf.
    Inicijalizacija sa konfig objektom
    """
    def __init__(self, konfig, parent = None, width = 6, height = 5, dpi=100):
        super(ZeroSpanKanvas, self).__init__(self, konfig)

    def connect_pick_evente(self):
        """connect canvas pick point event sa metodom self.on_pick"""
        self.cid = self.mpl_connect('pick_event', self.on_pick)

    def toggle_tgl(self):
        """inicjalni toggle elemenata (grid, legend...). Za sada zero i span
        grafovi podrzavaju samo legendu"""
        self.toggle_legend(self.konfig.Legend)

    def pick_nearest(self, argList):
        """
        Nakon sto netko na komplementarnom grafu izabere index, pronadji najblizi
        te ga highlitaj i updateaj labele na panelu

        argList je dict

        argList = {'xtocka': str(x),
                   'ytocka': str(y),
                   'minDozvoljenoOdstupanje': str(minD),
                   'maxDozvoljenoOdstupanje': str(maxD),
                   'status': str(status)}
        """
        if self.statusGlavniGraf:
            ind = pomocne_funkcije.pronadji_najblizi_time_indeks(self.data[self.gKanal].index, argList['xtocka'])
            x = self.data[self.gKanal].index[ind]
            y = self.data[self.gKanal].loc[x, self.konfig.MIDLINE]
            minD = self.data[self.gKanal].loc[x, self.konfig.WARNING_LOW]
            maxD = self.data[self.gKanal].loc[x, self.konfig.WARNING_HIGH]
            # ako postoje vise istih indeksa, uzmi zadnji
            if type(y) is pd.core.series.Series:
                y = y[-1]
                minD = minD[-1]
                maxD = maxD[-1]
            if y >= minD and y<= maxD:
                status = 'Dobar'
            else:
                status = 'Ne valja'

            newArgMap = {'xtocka': str(x),
                          'ytocka': str(y),
                          'minDozvoljenoOdstupanje': str(minD),
                          'maxDozvoljenoOdstupanje': str(maxD),
                          'status': str(status)}

            self.highlight_pick((x, y), self.highlightSize)
            self.updateaj_labele_na_panelu('normal', newArgMap)

    def updateaj_labele_na_panelu(self, tip, argMap):
        """
        update labela na zero span panelu (istovremeno i trigger za pick najblize
        tocke na drugom canvasu, npr. click na zero canvasu triggera span canvas...)
        """
        if tip == 'pick':
            self.emit(QtCore.SIGNAL('pick_nearest(PyQt_PyObject)'),argMap)
            self.emit(QtCore.SIGNAL('prikazi_info_span(PyQt_PyObject)'),argMap)
        else:
            self.emit(QtCore.SIGNAL('prikazi_info_span(PyQt_PyObject)'),argMap)

    def pronadji_tickove(self):
        """
        Funkcija radi tickove za zero i span graf

        Dodatno, funkcija adaptira vrijeme npr. timestamp jedne vrijednosti
        je '2015-02-14 12:34:56' i treba se 'adaptirati' u '14.02' radi kraceg zapisa

        input je lista min i max vrijeme za prikaz (raspon grafa)
        output je lista stringova (labeli za tickove), lista timestampova (tick location)
        """
        tmin = self.pocetnoVrijeme
        tmax = self.zavrsnoVrijeme
        raspon = pd.date_range(start = tmin, end = tmax, freq = 'D')
        tickLoc = [pd.to_datetime(i.date())for i in raspon]
        tickLab = [str(i.day)+'.'+str(i.month) for i in tickLoc]
        #za sada zanemarimo minor tickove na zero/span grafu, prosljedi prazne liste
        out = {'majorTickovi':tickLoc,
               'majorLabeli':tickLab,
               'minorTickovi':[],
               'minorLabeli':[]}
        return out

    def pripremi_zero_span_podatke_za_crtanje(self):
        """Pripremanje podataka za crtanje zero/span. Funkcija vraca dictionary
        sa podacima koji se dalje koriste za crtanje"""
        #priprema podataka za crtanje
        frejm = self.data
        x = list(frejm.index) #svi indeksi
        y = list(frejm[self.konfig.MIDLINE]) #sve vrijednosti
        warningUp = list(frejm[self.konfig.WARNING_HIGH]) #warning up
        warningLow = list(frejm[self.konfig.WARNING_LOW]) #warning low
        #pronalazak samo ok tocaka
        tempfrejm = self.data.copy()
        okTocke = tempfrejm[tempfrejm[self.konfig.MIDLINE] <= tempfrejm[self.konfig.WARNING_HIGH]]
        okTocke = okTocke[okTocke[self.konfig.MIDLINE] >= okTocke[self.konfig.WARNING_LOW]]
        xok = list(okTocke.index)
        yok = list(okTocke[self.konfig.MIDLINE])
        #pronalazak losih tocaka
        tempfrejm = self.data.copy()
        badOver = tempfrejm[tempfrejm[self.konfig.MIDLINE] > tempfrejm[self.konfig.WARNING_HIGH]]
        tempfrejm = self.data[self.gKanal].copy()
        badUnder = tempfrejm[tempfrejm[self.konfig.MIDLINE] < tempfrejm[self.konfig.WARNING_LOW]]
        badTocke = badUnder.append(badOver)
        badTocke.sort()
        badTocke.drop_duplicates(subset='vrijeme',
                                 take_last=True,
                                 inplace=True) # za svaki slucaj ako dodamo 2 ista indeksa
        xbad = list(badTocke.index)
        ybad = list(badTocke[self.konfig.MIDLINE])

        return {'x':x,
                'y':y,
                'warningUp':warningUp,
                'warningLow':warningLow,
                'xok':xok,
                'yok':yok,
                'xbad':xbad,
                'ybad':ybad}

    def rect_zoom(self, eclick, erelease):
        """
        Pozovi rect_zoom metodu parent klase i emitiraj signal za sinhronizacijom
        raspona x osi.
        """
        super(ZeroSpanKanvas,self).rect_zoom(eclick, erelease)
        self.emit(QtCore.SIGNAL('sync_x_zoom(PyQt_PyObject)'), sorted([eclick.xdata, erelease.xdata]))

    def sync_x_zoom(self, x):
        """
        Postavi novi raspon x osi. Metoda sluzi za sinhronizaciju zooma po x osi
        za zero i span graf.
        """
        for ax in self.fig.axes:
            ax.set_xlim(x)
        self.draw()

    def clear_zero_span(self):
        """
        clear grafa i replace sa porukom da nema dostupnih podataka
        """
        self.clear_graf()
        self.axes.text(0.5,
                       0.5,
                       'Nije moguce pristupiti podacima',
                       horizontalalignment='center',
                       verticalalignment='center',
                       fontsize = 8,
                       transform = self.axes.transAxes)
        self.draw()

    def highlight_pick(self, tpl, size):
        """
        naredba za crtanje highlight tocke na grafu na koridinatama
        tpl = (x, y), velicine size.
        """
        x, y = tpl
        if self.statusHighlight:
            if tpl is not self.lastHighlight:
                self.axes.lines.remove(self.highlight[0])
                self.make_highlight(x, y, size)
        else:
            self.make_highlight(x, y, size)

        self.draw()

    def make_highlight(self, x, y, size):
        """
        Generiranje instance highlight tocke na kooridinati x, y za prikaz.
        Velicina markera je definirana sa ulaznim parametrom size.
        """
        self.highlight = self.axes.plot(x,
                                        y,
                                        marker = 'o',
                                        markersize = int(size),
                                        color = 'yellow',
                                        alpha = 0.5,
                                        zorder = 10)
        self.lastHighlight = (x, y)
        self.statusHighlight = True

    def on_pick(self, event):
        """
        Callback za pick na ZERO ili SPAN grafu.
        """
        #definiraj x i y preko izabrane tocke
        x = self.data[self.gKanal].index[event.ind[0]]
        y = self.data[self.gKanal].loc[x, self.konfig.MIDLINE]
        minD = self.data[self.gKanal].loc[x, self.konfig.WARNING_LOW]
        maxD = self.data[self.gKanal].loc[x, self.konfig.WARNING_HIGH]
        # ako postoje vise istih indeksa, uzmi zadnji
        if type(y) is pd.core.series.Series:
            y = y[-1]
            minD = minD[-1]
            maxD = maxD[-1]
        if y >= minD and y<= maxD:
            status = 'Dobar'
        else:
            status = 'Ne valja'

        if event.mouseevent.button == 1:
            #left click
            #update labels
            argList = {'xtocka': str(x),
                       'ytocka': str(y),
                       'minDozvoljenoOdstupanje': str(minD),
                       'maxDozvoljenoOdstupanje': str(maxD),
                       'status': str(status)}
            #highlight tocku
            self.highlight_pick((x, y), self.highlightSize)
            #emit update vrijednosti
            self.updateaj_labele_na_panelu('pick', argList)

    def setup_limits(self):
        """
        Prosirivanje granica grafa da ticke nisu na rubu.
        Konacne granice se spremaju u member xlim_original i ylim_original
        radi implementacije zoom out metode.
        """
        #dohvati trenutne granice x osi
        tmin, tmax = pomocne_funkcije.prosiri_granice_grafa(self.pocetnoVrijeme, self.zavrsnoVrijeme, 1440)
        #set granice za max zoom out
        self.xlim_original = (tmin, tmax)
        self.ylim_original = self.axes.get_ylim()
        #set granice grafa
        self.axes.set_xlim(self.xlim_original)
        self.axes.set_ylim(self.ylim_original)

    def crtaj_glavni_kanal(self):
        """
        metoda zaduzena za crtanje glavnog grafa zero (ili span) podataka
        """
        #priprema podataka za crtanje
        tocke = self.pripremi_zero_span_podatke_za_crtanje()
        #prije crtanja provjeri da li postoje podaci ili je prazan frejm
        if len(tocke['x']):
            #midline (plot je drugacije definiran zbog pickera)
            self.axes.plot(tocke['x'],
                           tocke['y'],
                           linestyle = self.konfig.Midline.lineStyle,
                           linewidth = self.konfig.Midline.lineWidth,
                           color = self.konfig.Midline.color,
                           zorder = self.konfig.Midline.zorder,
                           label = self.konfig.Midline.label,
                           picker = 5)
            #ok values
            if len(tocke['xok']) > 0:
                self.crtaj_scatter(tocke['xok'], tocke['yok'], self.konfig.VOK)
            #bad values
            if len(tocke['xbad']) > 0:
                self.crtaj_scatter(tocke['xbad'], tocke['ybad'], self.konfig.VBAD)

            if self.konfig.Warning1.crtaj:
                self.crtaj_line(tocke['x'], tocke['warningUp'], self.konfig.Warning1)
                self.crtaj_line(tocke['x'], tocke['warningLow'], self.konfig.Warning2)
            #fill
            ledge, hedge = self.axes.get_ylim() #y granice canvasa za fill
            if self.konfig.Fill1.crtaj:
                self.crtaj_fill(tocke['x'], tocke['warningLow'], tocke['warningUp'], self.konfig.Fill1)
                self.crtaj_fill(tocke['x'], tocke['warningUp'], hedge, self.konfig.Fill2)
                self.crtaj_fill(tocke['x'], ledge, tocke['warningLow'], self.konfig.Fill2)
            self.statusGlavniGraf = True
        else:
            self.clear_zero_span()

    def crtaj(self, frejm, mapaParametara):
        """
        PROMJENA : direktno prosljedjivanje frejmova za crtanje...bez signala

        Glavna metoda za crtanje na canvas. Eksplicitne naredbe za crtanje.
        ulazni argumenti:
        frejm:
        -pandas dataframe zero ili span podataka.
        -Podaci za crtanje

        mapaParametara:
        -mapa sa potrebnim parametrima
        -mapaParametara['kanalId'] --> program mjerenja id glavnog kanala [int]
        -mapaParametara['pocetnoVrijeme'] --> pocetno vrijeme [pandas timestamp]
        -mapaParametara['zavrsnoVrijeme'] --> zavrsno vrijeme [pandas timestamp]
        """
        self.clear_graf()
        self.data = frejm
        self.pocetnoVrijeme = mapaParametara['pocetnoVrijeme']
        self.zavrsnoVrijeme = mapaParametara['zavrsnoVrijeme']
        self.gKanal = mapaParametara['kanalId']

        self.crtaj_glavni_kanal()
        #TODO! funkcija nije gotova...
        self.setup_ticks()
        self.setup_limits()
        self.setup_legend()

        #toggle legende
        self.toggle_tgl()
        self.draw()

    def span_select(self, tmin, tmax):
        """
        Zero i span graf nemaju opciju za span selektor.
        """
        pass
################################################################################
class ZeroKanvas(ZeroSpanKanvas):
    """specificna implementacija Zero canvasa"""
    def __init__(self, konfig, parent = None, width = 6, height = 5, dpi=100):
        super(ZeroKanvas, self).__init__(self, konfig)
        self.highlightSize = 1.5 * self.konfig.VOK.markerSize
        self.axes.xaxis.set_ticks_position('bottom')
        self.axes.figure.subplots_adjust(top = 0.02)
        self.axes.figure.subplots_adjust(right = 0.98)
        self.axes.set_ylabel(self.konfig.TIP)
        #inicijalni setup za interakciju i display(pick, zoom, ticks...)
        self.initialize_interaction(self.span_select, self.rect_zoom)
        self.set_interaction_mode(self.konfig.Zoom, self.konfig.Cursor, self.konfig.Selector)
        self.toggle_grid(self.konfig.Grid)
        self.toggle_ticks(self.konfig.Ticks)

################################################################################
class SpanKanvas(ZeroSpanKanvas):
    """specificna implementacija span canvasa"""
    def __init__(self, konfig, parent = None, width = 6, height = 5, dpi=100):
        super(SpanKanvas, self).__init__(self, konfig)
        self.highlightSize = 1.5 * self.konfig.VOK.markerSize
        self.axes.xaxis.set_ticks_position('top')
        self.axes.figure.subplots_adjust(bottom = 0.02)
        self.axes.figure.subplots_adjust(right = 0.98)
        self.axes.set_ylabel(self.konfig.TIP)
        #inicijalni setup za interakciju i display(pick, zoom, ticks...)
        self.initialize_interaction(self.span_select, self.rect_zoom)
        self.set_interaction_mode(self.konfig.Zoom, self.konfig.Cursor, self.konfig.Selector)
        self.toggle_grid(self.konfig.Grid)
        self.toggle_ticks(self.konfig.Ticks)
################################################################################