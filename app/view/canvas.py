# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 12:27:25 2015

@author: DHMZ-Milic
"""
#TODO! integracija i testing ovog canvasa u applikaciju

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
    def __init__(self, konfig, pomocni, parent = None, width = 6, height = 5, dpi=100):
        """
        Canas se inicijalizira sa svojim konfig objektom, mapom pomocnih grafova
        definiranom u objektu tipa KonfigAplikacije u memberu dictPomocnih.
        """
        #osnovna definicija figure, axes i canvasa
        self.fig = Figure(figsize = (width, height), dpi = dpi)
        self.axes = self.fig.add_subplot(111)
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
        self.pomocniGrafovi = pomocni
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

        self.initialize_interaction() #inicijalni setup za interakciju (pick, zoom, ticks...)

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
        self.cid1 = None
        self.cid2 = None

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

    def disconnect_pick_evente(self):
        """Opceniti disconnect pick eventa. Pick eventi se trebaju odspojiti prilikom
        zoom akcije i prilikom izbora vise tocaka uz pomoc span selektora (izbjegavanje
        konfliktnih signala)."""
        if self.cid1:
            self.mpl_disconnect(self.cid1)
            self.cid1 = None
        if self.cid2:
            self.mpl_disconnect(self.cid2)
            self.cid2 = None

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
        Matplotlib connection ovisno o tipu canvasa. Reimplementiraj za pojedini graf
        """
        #TODO! reimmplement
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
        self.axes.set_ylabel(self.tip)
        self.draw()

    def crtaj(self, ulaz):
        """
        Glavna metoda za crtanje grafa. Poziva se nakon sto kontroler prosljedi
        zahtjev za crtanjem. Reimplementiraj za pojedini canvas.
        """
        #TODO! reimplement za svaki canvas odvojeno
        pass
################################################################################
class SatniMinutniKanvas(Kanvas):
    """
    Kanvas klasa sa zajednickim elementima za satni i minutni graf.
    """
    def __init__(self, konfig, parent = None, width = 6, height = 5, dpi=100):
        super(SatniMinutniKanvas, self).__init__(konfig)

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
        if not flag:
            frejm = frejm[frejm['flag'] == flag]
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
            x = list(frejm.index)
            y = list(frejm[self.MIDLINE])
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
        if self.tKontejner is not None:
                arg = {'kanal':self.tKontejner,
                       'od':self.pocetnoVrijeme,
                       'do':self.zavrsnoVrijeme}
                self.emit_request_za_podacima(arg)

        if self.tKontejner in self.data.keys():
            frejm = self.data[self.tKontejner]
            frejm = frejm[frejm['flag'] > 0]
            if len(frejm):
                overlimit = frejm[frejm[self.MIDLINE] > tempMax]
                underlimit = frejm[frejm[self.MIDLINE] < tempMin]
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
        #TODO! reimplement metodu za pojedini graf
        """
        Definiranje teksta za prikaz annotationa (sto ce biti unutar annotationa).
        Ulazni parametar je tocka za koju radimo annotation. Funkcija vraca string
        teksta annotationa.
        """
        pass
#        if xpoint in list(self.data[self.gKanal].index):
#            if self.tip_grafa is SatniEnum:
#                yavg = self.data[self.gKanal].loc[xpoint, u'avg']
#                ymin = self.data[self.gKanal].loc[xpoint, u'min']
#                ymax = self.data[self.gKanal].loc[xpoint, u'max']
#                ystatus = self.data[self.gKanal].loc[xpoint, u'status']
#                ycount = self.data[self.gKanal].loc[xpoint, u'count']
#                tekst = 'Vrijeme: '+str(xpoint)+'\nAverage: '+str(yavg)+'\nMin:'+str(ymin)+'\nMax:'+str(ymax)+'\nStatus:'+str(ystatus)+'\nCount:'+str(ycount)
#            elif self.tip_grafa is MinutniEnum:
#                ykonc = self.data[self.gKanal].loc[xpoint, u'koncentracija']
#                ystat = self.data[self.gKanal].loc[xpoint, u'status']
#                yflag = self.data[self.gKanal].loc[xpoint, u'flag']
#                tekst = 'Vrijeme: '+str(xpoint)+'\nKoncentracija: '+str(ykonc)+'\nStatus:'+str(ystat)+'\nFlag:'+str(yflag)
#        else:
#            tekst = 'Vrijeme: '+str(xpoint)+'\nNema podataka'
#        return tekst

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
        #TODO!
        pass
#        #zaokruzi na najblizi puni sat (bitno za podudaranje indeksa u frejmu)
#        if self.tip_grafa is SatniEnum:
#            xpoint = pomocne_funkcije.zaokruzi_vrijeme(xpoint, 3600)
#        elif self.tip_grafa is MinutniEnum:
#            xpoint = pomocne_funkcije.zaokruzi_vrijeme(xpoint, 60)

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
        self.zaokruzi_na_najblize_vrijeme(xpoint) #round na najblize vrijeme
        xpoint = pd.to_datetime(xpoint) #konverzija iz datetime.datetime objekta u pandas.tislib.Timestamp
        #pazimo da x vrijednost ne iskace od zadanih granica
        if xpoint >= self.zavrsnoVrijeme:
            xpoint = self.zavrsnoVrijeme
        if xpoint <= self.pocetnoVrijeme:
            xpoint = self.pocetnoVrijeme
        #kooridinate ako nedostaju podaci za highlight
        if xpoint in list(self.data[self.gKanal].index):
            ypoint = self.data[self.gKanal].loc[xpoint, self.MIDLINE]
        else:
            miny = self.data[self.gKanal][self.MIDLINE].min()
            maxy = self.data[self.gKanal][self.MIDLINE].max()
            ypoint = (miny + maxy)/2

        return xpoint, ypoint


    def on_pick(self, event):
        """
        Resolve pick eventa za satni i minutni graf.
        """
        #TODO! reimplement za pojedini graf
        if self.statusGlavniGraf and event.inaxes == self.axes:
            xpoint, ypoint = self.adaptiraj_tocku_od_pick_eventa(event)
            """
            Ponasanje ovisno o pritisnutom gumbu na misu.
            """
            pass
#            if event.button == 1:
#                if self.tip_grafa is SatniEnum:
#                    #left click, naredi crtanje minutnog i highlight tocku
#                    self.emit(QtCore.SIGNAL('crtaj_minutni_graf(PyQt_PyObject)'), xpoint) #crtanje minutnog
#                    self.highlight_pick((xpoint, ypoint), self.highlightSize) #highlight odabir, size pointa
#            elif event.button == 2:
#                tekst = self.setup_annotation_text(xpoint)
#                offset = self.setup_annotation_offset(event)
#                datacords = (xpoint, ypoint)
#                self.annotate_pick(datacords, offset, tekst)
#            elif event.button == 3:
#                loc = QtGui.QCursor.pos() #lokacija klika
#                self.show_context_menu(loc, xpoint, xpoint) #interval koji treba promjeniti


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

    def promjena_flaga_top(self, tmin, tmax, flag):
        """
        pakiranje i emit zahtjeva za promjenom flaga
        """
        arg = {'od': tmin,
               'do': tmax,
               'noviFlag': flag,
               'kanal': self.gKanal}
        #generalni emit za promjenu flaga
        self.emit(QtCore.SIGNAL('promjeni_flag(PyQt_PyObject)'), arg)


    def promjena_flaga(self, flag = 1):
        """
        Metoda sluzi za promjenu flaga
        ovisno o keyword argumentu tip.
        """
        #TODO! reimplement za pojedni graf (satni treba odmaknuti 59 minuta od donjeg ruba)
        #dohvati rubove intervala (spremljeni su u membere prilikom poziva dijaloga)
        tmin = self.__lastTimeMin
        tmax = self.__lastTimeMax
        self.promjena_flaga_top(tmin, tmax, flag)







#    def toggle_tgl(self):
#        self.toggle_ticks(self.graf_konfig.Ticks)
#        self.toggle_grid(self.graf_konfig.Grid)
#        self.toggle_legend(self.graf_konfig.Legend)

















#    def crtaj(self, ulaz, konfig = None):
#        #reimplement for each canvas
#        """
#        Glavna metoda za crtanje na canvas. Eksplicitne naredbe za crtanje.
#
#        Crtanje ide kroz nekoliko koraka:
#        1. reinicijalizacija membera ovisno o ulaznim podacima
#        2. priprema i dohvacanje podataka za crtanje
#        3. crtanje glavnog kanala
#        4. crtanje pomocnih kanala
#        5. crtanje temperature kontejnera
#        6. provjera za crtanje highlighta (markera trenutno izabrane tocke)
#        7. setup granica, tickova, grida, interakcije....
#
#        ulaz je dict podataka
#        ulaz['kanalId'] --> int ,programMjerenjaId glavnog kanala [int]
#        ulaz['pocetnoVrijeme'] --> pocetno vrijeme [pandas timestamp]
#        ulaz['zavrsnoVrijeme'] --> zavrsno vrijeme [pandas timestamp]
#        ulaz['tempKontejner'] --> temperatura kontejnera id (ili None) [int]
#        """
#        ###priprema za crtanje... reset i inicijalizacija membera###
#        self.axes.clear()
#        self.data = {}
#        self.statusGlavniGraf = False
#        self.statusAnnotation = False
#        self.pocetnoVrijeme = ulaz['pocetnoVrijeme']
#        self.zavrsnoVrijeme = ulaz['zavrsnoVrijeme']
#        self.gKanal = ulaz['kanalId']
#        self.tKontejner = ulaz['tempKontejner']
#
#        #redo Axes labels
#        self.axes.set_xlabel('Vrijeme')
#        self.axes.set_ylabel(self.tip)
#
#        ###emit zahtjev za podacima glavnog kanala, return se vraca u member self.data
#        arg = {'kanal':self.gKanal,
#               'od':self.pocetnoVrijeme,
#               'do':self.zavrsnoVrijeme}
#
#        self.emit_request_za_podacima(arg)
#
#        #Provjera za postojanjem podataka glavnog kanala.
#        if self.gKanal in self.data.keys():
#            """temperatura kontejnera i pomocni grafovi se koriste samo kod
#            satnog i minutnog grafa"""
#
#            if self.tip_grafa is SatniEnum or self.tip_grafa is MinutniEnum:
#                #ucitaj temperaturu kontejnera ako postoji
#                #kreni ucitavati pomocne kanale po potrebi
#                for programKey in self.dto.dictPomocnih.keys():
#                    if programKey not in self.data.keys():
#                        arg = {'kanal':programKey,
#                               'od':self.pocetnoVrijeme,
#                               'do':self.zavrsnoVrijeme}
#                        self.emit_request_za_podacima(arg)
#
#            #naredba za crtanje glavnog grafa
#            self.crtaj_glavni_kanal()
#            #set dostupnih pomocnih kanala za crtanje
#            pomocni = set(self.data.keys()) - set([self.gKanal, self.tKontejner])
#            self.crtaj_pomocne(pomocni)
#
#
#            ###micanje tocaka od rubova, tickovi, legenda...
#            self.setup_limits()
#            self.setup_legend()
#            self.setup_ticks()
#
#            self.toggle_tgl()
#
#            #crtanje temperature kontejnera
#            self.crtaj_oznake_temperature(15,30)
#            #highlight prijasnje tocke
#            if self.statusHighlight:
#                hx, hy = self.lastHighlight
#                if hx in self.data[self.gKanal].index:
#                    #pronadji novu y vrijednosti indeksa
#                    hy = self.data[self.gKanal].loc[hx, self.midline]
#                    self.make_highlight(hx, hy, self.highlightSize)
#                else:
#                    self.statusHighlight = False
#                    self.lastHighlight = (None, None)
#
#            self.draw()
#            #promjeni cursor u normalan cursor
#            QtGui.QApplication.restoreOverrideCursor()
#        else:
#            self.axes.clear()
#            self.axes.text(0.5,
#                           0.5,
#                           'Nije moguce pristupiti podacima za trazeni kanal.',
#                           horizontalalignment='center',
#                           verticalalignment='center',
#                           fontsize = 8,
#                           transform = self.axes.transAxes)
#            self.draw()
#            #promjeni cursor u normalan cursor
#            QtGui.QApplication.restoreOverrideCursor()
################################################################################
################################################################################
################################################################################
#    def crtaj_oznake_temperature(self, tempMin, tempMax):
#        """
#        Crtanje oznaka za temperaturu kontejnera ako su izvan zadanih granica
#        """
#
#        if self.tip_grafa is SatniEnum or self.tip_grafa is MinutniEnum:
#            if self.tKontejner is not None:
#                    arg = {'kanal':self.tKontejner,
#                           'od':self.pocetnoVrijeme,
#                           'do':self.zavrsnoVrijeme}
#                    self.emit_request_za_podacima(arg)
#
#            if self.tKontejner in self.data.keys():
#                frejm = self.data[self.tKontejner]
#                frejm = frejm[frejm['flag'] > 0]
#                if len(frejm):
#                    overlimit = frejm[frejm[self.midline] > tempMax]
#                    underlimit = frejm[frejm[self.midline] < tempMin]
#                    frejm = overlimit.append(underlimit)
#                    x = list(frejm.index)
#                    brojLosih = len(x)
#                    if brojLosih:
#                        y1, y2 = self.ylim_original
#                        c = y2 - 0.05 * abs(y2 - y1)  # odmak od gornjeg ruba za 5% max raspona
#                        y = [c for i in range(brojLosih)]
#                        self.axes.plot(x,
#                                       y,
#                                       marker='*',
#                                       color='Red',
#                                       linestyle='None',
#                                       alpha=0.4)
################################################################################
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
################################################################################
#    def crtaj_scatter_value_ovisno_o_flagu(self, komponenta, konfig, flag):
#        """
#        Pomocna funkcija za crtanje scatter tipa grafa (samo tocke).
#        -komponenta je opisni string ( ['min', 'max', 'koncentracija', 'avg'])
#        -konfig je objekt sa postavkama grafa
#        -flag je int vrijednost flaga za razlikovanje validacije ili None (za sve
#        tocke neovisno o flagu)
#
#        Metodu koristi satni i minutni graf jer jedino oni crtaju tocke ovisno
#        o flagu. Flag moze biti None, u tom slucaju se crtaju sve tocke (primjer
#        je crtanje ekstremnih vrijednosti na satnom grafu).
#        """
#        frejm = self.data[self.gKanal]
#        if not flag:
#            frejm = frejm[frejm['flag'] == flag]
#        x = list(frejm.index)
#        #crtaj samo ako ima podataka
#        if len(x):
#            if komponenta == 'min':
#                y = list(frejm['min'])
#            elif komponenta == 'max':
#                y = list(frejm['max'])
#            elif komponenta == 'koncentracija':
#                y = list(frejm['koncentracija'])
#            elif komponenta == 'avg':
#                y = list(frejm['avg'])
#            else:
#                return
#            #naredba za plot
#            self.crtaj_scatter(x, y, konfig)
#            self.statusGlavniGraf = True
################################################################################
################################################################################
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
            y = self.data[self.gKanal].loc[x, self.midline]
            minD = self.data[self.gKanal].loc[x, self.warningLow]
            maxD = self.data[self.gKanal].loc[x, self.warningHigh]
            # ako postoje vise istih indeksa, uzmi zadnji
            if type(y) is pd.core.series.Series:
                y = y[-1]
                minD = minD[-1]
                maxD = maxD[-1]
            if y >= minD and y<= maxD:
                status = 'Dobar'
            else:
                status = 'Ne valja'

            #newArgList = [str(x), str(y), str(minD), str(maxD), str(status)]
            newArgList = {'xtocka': str(x),
                          'ytocka': str(y),
                          'minDozvoljenoOdstupanje': str(minD),
                          'maxDozvoljenoOdstupanje': str(maxD),
                          'status': str(status)}

            self.highlight_pick((x, y), self.highlightSize)
            self.updateaj_labele_na_panelu('normal', newArgList)
################################################################################
#    def setup_annotation_offset(self, event):
#        """
#        Funkcija postavlja annotation offset ovisno o polozaju klika na canvas.
#        """
#        size = self.frameSize()
#        x, y = size.width(), size.height()
#        x = x//2
#        y = y//2
#        clickedx = event.x
#        clickedy = event.y
#
#        if clickedx >= x:
#            clickedx = -80
#            if clickedy >= y:
#                clickedy = -30
#            else:
#                clickedy = 30
#        else:
#            clickedx = 30
#            if clickedy >= y:
#                clickedy = -30
#            else:
#                clickedy = 30
#        return (clickedx, clickedy)
#################################################################################
#    def setup_annotation_text(self, xpoint):
#        """
#        Definiranje teksta za prikaz annotationa (sto ce biti unutar annotationa).
#        Ulazni parametar je tocka za koju radimo annotation. Funkcija vraca string
#        teksta annotationa.
#        """
#        if xpoint in list(self.data[self.gKanal].index):
#            if self.tip_grafa is SatniEnum:
#                yavg = self.data[self.gKanal].loc[xpoint, u'avg']
#                ymin = self.data[self.gKanal].loc[xpoint, u'min']
#                ymax = self.data[self.gKanal].loc[xpoint, u'max']
#                ystatus = self.data[self.gKanal].loc[xpoint, u'status']
#                ycount = self.data[self.gKanal].loc[xpoint, u'count']
#                tekst = 'Vrijeme: '+str(xpoint)+'\nAverage: '+str(yavg)+'\nMin:'+str(ymin)+'\nMax:'+str(ymax)+'\nStatus:'+str(ystatus)+'\nCount:'+str(ycount)
#            elif self.tip_grafa is MinutniEnum:
#                ykonc = self.data[self.gKanal].loc[xpoint, u'koncentracija']
#                ystat = self.data[self.gKanal].loc[xpoint, u'status']
#                yflag = self.data[self.gKanal].loc[xpoint, u'flag']
#                tekst = 'Vrijeme: '+str(xpoint)+'\nKoncentracija: '+str(ykonc)+'\nStatus:'+str(ystat)+'\nFlag:'+str(yflag)
#        else:
#            tekst = 'Vrijeme: '+str(xpoint)+'\nNema podataka'
#        return tekst
#################################################################################
#    def span_select(self, xmin, xmax):
#        """
#        Metoda je povezana sa span selektorom (ako je inicijaliziran).
#        Metoda je zaduzena da prikaze kontekstni dijalog za promjenu flaga
#        na mjestu gdje "releasamo" ljevi klik za satni i minutni graf.
#
#        t1 i t2 su timestampovi, ali ih treba adaptirati iz matplotlib vremena u
#        "zaokruzene" pandas timestampove. (na minutnom grafu se zaokruzuje na najblizu
#        minutu, dok na satnom na najblizi sat)
#        """
#        if self.statusGlavniGraf: #glavni graf mora biti nacrtan
#            #konverzija ulaznih vrijednosti u pandas timestampove
#            t1 = matplotlib.dates.num2date(xmin)
#            t2 = matplotlib.dates.num2date(xmax)
#            t1 = datetime.datetime(t1.year, t1.month, t1.day, t1.hour, t1.minute, t1.second)
#            t2 = datetime.datetime(t2.year, t2.month, t2.day, t2.hour, t2.minute, t2.second)
#            #vremena se zaokruzuju
#            if self.tip_grafa is SatniEnum:
#                t1 = pomocne_funkcije.zaokruzi_vrijeme(t1, 3600)
#                t2 = pomocne_funkcije.zaokruzi_vrijeme(t2, 3600)
#            elif self.tip_grafa is MinutniEnum:
#                t1 = pomocne_funkcije.zaokruzi_vrijeme(t1, 60)
#                t2 = pomocne_funkcije.zaokruzi_vrijeme(t2, 60)
#            t1 = pd.to_datetime(t1)
#            t2 = pd.to_datetime(t2)
#
#            #osiguranje da se ne preskoce granice glavnog kanala (izbjegavanje index errora)
#            if t1 < self.pocetnoVrijeme:
#                t1 = self.pocetnoVrijeme
#            if t1 > self.zavrsnoVrijeme:
#                t1 = self.zavrsnoVrijeme
#            if t2 < self.pocetnoVrijeme:
#                t2 = self.pocetnoVrijeme
#            if t2 > self.zavrsnoVrijeme:
#                t2 = self.zavrsnoVrijeme
#            #tocke ne smiju biti iste (izbjegavamo paljenje dijaloga na ljevi klik)
#            if t1 != t2:
#                #pozovi dijalog za promjenu flaga
#                loc = QtGui.QCursor.pos()
#                self.show_context_menu(loc, t1, t2)
################################################################################
#    def show_context_menu(self, pos, tmin, tmax):
#        """
#        Metoda iscrtava kontekstualni meni sa opcijama za promjenom flaga
#        na minutnom i satnom grafu.
#        """
#        #zapamti rubna vremena intervala, trebati ce za druge metode
#        self.__lastTimeMin = tmin
#        self.__lastTimeMax = tmax
#        #definiraj menu i postavi akcije u njega
#        menu = QtGui.QMenu(self)
#        menu.setTitle('Promjeni flag')
#        action1 = QtGui.QAction("Flag: dobar", menu)
#        action2 = QtGui.QAction("Flag: los", menu)
#        menu.addAction(action1)
#        menu.addAction(action2)
#        #povezi akcije menua sa metodama
#        action1.triggered.connect(functools.partial(self.promjena_flaga, flag = 1000))
#        action2.triggered.connect(functools.partial(self.promjena_flaga, flag = -1000))
#        #prikazi menu na definiranoj tocki grafa
#        menu.popup(pos)
################################################################################
#    def promjena_flaga_top(self, tmin, tmax, flag):
#        arg = {'od': tmin,
#               'do': tmax,
#               'noviFlag': flag,
#               'kanal': self.gKanal}
#        #generalni emit za promjenu flaga
#        self.emit(QtCore.SIGNAL('promjeni_flag(PyQt_PyObject)'), arg)
#
#
#    def promjena_flaga(self, flag = 1):
#        """
#        Metoda sluzi za promjenu flaga
#        ovisno o keyword argumentu tip.
#        """
#        #dohvati rubove intervala (spremljeni su u membere prilikom poziva dijaloga)
#        tmin = self.__lastTimeMin
#        tmax = self.__lastTimeMax
#        self.promjena_flaga_top(tmin, tmax, flag)
#
 ################################################################################
    def connect_pick_evente(self):
        """mpl connection ovisno o tipu canvasa. Pick tocke ili pick bilo gdje
        na grafu."""
        pass

################################################################################
################################################################################
################################################################################
################################################################################
    def setup_limits(self):
        """
        Prosirivanje granica grafa da ticke nisu na rubu.
        Pomak ovisi o tipu grafa (1 sat, 5 minuta ili 1 dan)
        Konacne granice se spremaju u member xlim_original i ylim_original
        radi implementacije zoom out metode.
        """
        #dohvati trenutne granice x osi
        xmin, xmax = self.axes.get_xlim()
        xmin = pomocne_funkcije.mpl_time_to_pandas_datetime(xmin)
        xmax = pomocne_funkcije.mpl_time_to_pandas_datetime(xmax)

        #odmakni x granice za specificni interval ovisno o tipu
        if self.tip_grafa is SatniEnum:
            tmin, tmax = pomocne_funkcije.prosiri_granice_grafa(xmin, xmax, 60)
        elif self.tip_grafa is MinutniEnum:
            tmin, tmax = pomocne_funkcije.prosiri_granice_grafa(xmin, xmax, 5)
        elif self.tip_grafa is ZeroEnum or self.tip_grafa is SpanEnum:
            tmin, tmax = pomocne_funkcije.prosiri_granice_grafa(xmin, xmax, 1440)
        else:
            tmin, tmax = xmin, xmax
        #set granice za max zoom out
        self.xlim_original = (tmin, tmax)
        self.ylim_original = self.axes.get_ylim()
        #set granice grafa
        self.axes.set_xlim(self.xlim_original)
        self.axes.set_ylim(self.ylim_original)
################################################################################
    def toggle_ticks(self, x):
        """
        Toggle minor tickova on i off ovisno o ulaznoj vrijednosti x (boolean).
        """
        if x and self.statusGlavniGraf:
            self.axes.minorticks_on()
        else:
            self.axes.minorticks_off()
        self.draw()
################################################################################
    def toggle_grid(self, x):
        """
        Toggle grida on i off, ovisno o ulaznoj vrijednosti x (boolean)
        """
        if x and self.statusGlavniGraf:
            self.axes.grid(True)
        else:
            self.axes.grid(False)
        self.draw()
################################################################################
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
################################################################################
    def setup_legend(self):
        """
        Setup legende na canvas. Lokacija, stil, alpha...
        """
        self.legenda = self.axes.legend(loc = 1,
                                        fontsize = 8,
                                        fancybox = True)
        self.legenda.get_frame().set_alpha(0.8)
################################################################################
################################################################################
#    def annotate_pick(self, point, offs, tekst):
#        """
#        Mangage annotation za tocku point, na offsetu offs, sa tekstom tekst
#        point - (x, y) tuple
#        offs - (xoff, yoff) tuple
#        tekst - string
#        """
#        if self.statusAnnotation:
#            self.annotation.remove()
#            self.statusAnnotation = False
#            if point[0] != self.lastAnnotation:
#                self.make_annotation(point, offs, tekst)
#        else:
#            self.make_annotation(point, offs, tekst)
#        self.draw()
#################################################################################
#    def make_annotation(self, point, offs, tekst):
#        """Annotation instance object, pozicija na grafu"""
#        self.annotation = self.axes.annotate(
#                    tekst,
#                    xy = point,
#                    xytext = offs,
#                    textcoords = 'offset points',
#                    ha = 'left',
#                    va = 'center',
#                    fontsize = 7,
#                    zorder = 102,
#                    bbox = dict(boxstyle = 'square', fc = 'cyan', alpha = 0.7),
#                    arrowprops = dict(arrowstyle = '->'))
#        self.lastAnnotation = point[0]
#        self.statusAnnotation = True
#################################################################################
    def highlight_pick(self, tpl, size):
        """
        crta highlight tocku na grafu sa koridinatama tpl = (x, y), velicine size
        """
        x, y = tpl
        if self.statusHighlight:
            if not tpl == self.lastHighlight:
                self.axes.lines.remove(self.highlight[0])
                self.make_highlight(x, y, size)
        else:
            self.make_highlight(x, y, size)

        self.draw()
################################################################################
    def make_highlight(self, x, y, size):
        """
        napravi instancu highlight tocke na kooridinati x, y.
        Velicina markera je definirana sa ulaznim parametrom size
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
################################################################################
#    def clear_graf(self):
#        """
#        clear grafa
#        """
#        self.data = {} #spremnik za frejmove (ucitane)
#        self.statusGlavniGraf = False
#        self.statusAnnotation = False
#        self.statusHighlight = False
#        self.lastHighlight = (None, None)
#        self.lastAnnotation = None
#
#        self.axes.clear()
#
#        #redo Axes labels
#        self.axes.set_xlabel('Vrijeme')
#        self.axes.set_ylabel(self.tip)
#
#        self.draw()
################################################################################
    def sync_x_zoom(self, x):
        """
        Postavi novi raspon x osi. Metoda sluzi za sinhronizaciju zooma po x osi
        za zero i span graf
        """
        for ax in self.fig.axes:
            ax.set_xlim(x)
        self.draw()
################################################################################
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
################################################################################
    def set_minutni_kanal(self, argMap):
        """
        BITNA METODA! - mehanizam s kojim se ucitavaju frejmovi za crtanje.
        -metoda crtaj trazi od kontrolera podatke
        -ovo je predvidjeni slot gdje kontroler vraca trazene podatke
        -ulaz je mapa

        metoda postavlja frejm minutnih podataka u self.__data
        argMap['kanal'] -> int, ime kanala
        argMap['dataFrejm'] -> pandas dataframe, minutni podaci
        """
        self.data[argMap['kanal']] = argMap['dataFrejm']
################################################################################
    def set_agregirani_kanal(self, ulaz):
        """
        BITNA METODA! - mehanizam s kojim se ucitavaju frejmovi za crtanje.
        -metoda crtaj trazi od kontrolera podatke
        -ovo je predvidjeni slot gdje kontroler vraca trazene podatke
        - ulaz je mapa koja sadrzi kanalId i agregirani frejm

        metoda postavlja agregirani frejm u self.data
        ulaz['kanal'] -> int, 'ime' kanala
        ulaz['agregirani'] -> pandas dataframe, agregirani podaci
        """
        self.data[ulaz['kanal']] = ulaz['agregirani']
################################################################################
    def set_zero_span_frejm(self, ulaz):
        """
        BITNA METODA! - mehanizam s kojim se ucitavaju frejmovi za crtanje.
        -metoda crtaj trazi od kontrolera podatke
        -ovo je predvidjeni slot gdje kontroler vraca trazene podatke
        - ulaz je mapa koja sadrzi kanalId i zero/span graf

        metoda postavlja zero (ili span) frejm u self.data
        ulaz['kanal'] -> int, 'ime' kanala
        ulaz['zsFrejm'] -> pandas dataframe, zero span podaci
        """
        self.data[ulaz['kanal']] = ulaz['zsFrejm']
################################################################################
################################################################################

#class SatniMinutniKanvas(Kanvas):
#    def __init__(self, konfig, appKonfig, parent = None, width = 6, height = 5, dpi=100):
#        self.tip = 'SATNI'
#        self.midline = 'avg'
#        self.minimum = 'min'
#        self.maksimum = 'max'
#
#        super(SatniMinutniKanvas, self).__init__(konfig, appKonfig)
#
#    def toggle_tgl(self):
#        self.toggle_ticks(self.graf_konfig.Ticks)
#        self.toggle_grid(self.graf_konfig.Grid)
#        self.toggle_legend(self.graf_konfig.Legend)


#TODO!
class SatniKanvas(SatniMinutniKanvas):
    def __init__(self, konfig, appKonfig, parent = None, width = 6, height = 5, dpi=100):
        self.graf_konfig = konfig.satni
        self.tip_grafa = SatniEnum
        super(SatniKanvas, self).__init__(konfig, appKonfig)
        self.highlightSize = 1.5 * self.graf_konfig.VOK.markerSize
        self.axes.set_ylabel(SatniEnum.tip.value)
        self.midline = 'avg'


    def crtaj_glavni_kanal(self):
            #midline
            frejm = self.data[self.gKanal]
            x = list(frejm.index)
            y = list(frejm[self.midline])
            self.crtaj_line(x, y, self.dto.satniMidline)
            #fill izmedju komponenti
            if self.dto.satniFill.crtaj:
                self.crtaj_fill(x,
                                list(frejm[self.dto.satniFill.komponenta1]),
                                list(frejm[self.dto.satniFill.komponenta2]),
                                self.dto.satniFill)
            #ekstremi min i max
            if self.dto.satniEksMin.crtaj:
                self.crtaj_scatter_value(self.minimum, self.dto.satniEksMin, None)
                self.crtaj_scatter_value(self.maksimum, self.dto.satniEksMax, None)
            #plot tocaka ovisno o flagu i validaciji
            self.crtaj_scatter_value(self.midline, self.dto.satniVOK, 1000)
            self.crtaj_scatter_value(self.midline, self.dto.satniVBAD, -1000)
            self.crtaj_scatter_value(self.midline, self.dto.satniNVOK, 1)
            self.crtaj_scatter_value(self.midline, self.dto.satniNVBAD, -1)
            self.statusGlavniGraf = True


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


    def promjena_flaga(self, flag = 1):
        """
        Metoda sluzi za promjenu flaga
        ovisno o keyword argumentu tip.
        """
        #dohvati rubove intervala (spremljeni su u membere prilikom poziva dijaloga)
        tmin = self.__lastTimeMin
        tmax = self.__lastTimeMax

        tmin = tmin - datetime.timedelta(minutes = 59)
        tmin = pd.to_datetime(tmin)
        self.promjena_flaga_top(tmin, tmax, flag)
# #########################################


    def connect_pick_evente(self):
        self.cid1 = self.mpl_connect('button_press_event', self.on_pick)

    def emit_request_za_podacima(self, arg):
        """
        Slanje zahtjeva za podacima. Kontroler vraca trazene podatke u member
        self.data. Opis zahtjeva (sto se tocno trazi) zadan je preko ulaznog argumenta
        arg (specificni dictionary podataka, ovisno o tipu grafa).
        """
        self.emit(QtCore.SIGNAL('dohvati_agregirani_frejm(PyQt_PyObject)'), arg)


class MinutniKanvas(SatniMinutniKanvas):
    def __init__(self, konfig, appKonfig, parent = None, width = 6, height = 5, dpi=100):
        self.tip_grafa = MinutniEnum
        self.graf_konfig = konfig.minutni
        self.tip = 'MINUTNI'
        self.midline = 'koncentracija'

        super(MinutniKanvas, self).__init__(konfig, appKonfig)
        self.axes.set_ylabel(MinutniEnum.tip.value)
        self.midline = 'Koncentracija'


    def crtaj_glavni_kanal(self):
            #midline plot
            frejm = self.data[self.gKanal]
            x = list(frejm.index)
            y = list(frejm[self.midline])
            self.crtaj_line(x, y, self.dto.minutniMidline)
            #plot tocaka ovisno o flagu i validaciji
            self.crtaj_scatter_value(self.midline, self.graf_konfig.VOK, 1000)
            self.crtaj_scatter_value(self.midline, self.graf_konfig.VBAD, -1000)
            self.crtaj_scatter_value(self.midline, self.graf_konfig.NVOK, 1)
            self.crtaj_scatter_value(self.midline, self.graf_konfig.NVBAD, -1)
            self.statusGlavniGraf = True

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

    def connect_pick_evente(self):
        self.cid1 = self.mpl_connect('button_press_event', self.on_pick)

    def emit_request_za_podacima(self, arg):
        """
        Slanje zahtjeva za podacima. Kontroler vraca trazene podatke u member
        self.data. Opis zahtjeva (sto se tocno trazi) zadan je preko ulaznog argumenta
        arg (specificni dictionary podataka, ovisno o tipu grafa).
        """
        self.emit(QtCore.SIGNAL('dohvati_minutni_frejm(PyQt_PyObject)'), arg)

class ZeroSpanKanvas(Kanvas):
    def __init__(self, konfig, appKonfig, parent = None, width = 6, height = 5, dpi=100):
        super(ZeroSpanKanvas, self).__init__(konfig, appKonfig)
        self.midline = 'Vrijednost'




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
        frejm = self.data[self.gKanal]
        x = list(frejm.index) #svi indeksi
        y = list(frejm[self.midline]) #sve vrijednosti
        warningUp = list(frejm[self.warningHigh]) #warning up
        warningLow = list(frejm[self.warningLow]) #warning low
        #pronalazak samo ok tocaka
        tempfrejm = self.data[self.gKanal].copy()
        okTocke = tempfrejm[tempfrejm[self.midline] <= tempfrejm[self.warningHigh]]
        okTocke = okTocke[okTocke[self.midline] >= okTocke[self.warningLow]]
        xok = list(okTocke.index)
        yok = list(okTocke[self.midline])
        #pronalazak losih tocaka
        tempfrejm = self.data[self.gKanal].copy()
        badOver = tempfrejm[tempfrejm[self.midline] > tempfrejm[self.warningHigh]]
        tempfrejm = self.data[self.gKanal].copy()
        badUnder = tempfrejm[tempfrejm[self.midline] < tempfrejm[self.warningLow]]
        badTocke = badUnder.append(badOver)
        badTocke.sort()
        badTocke.drop_duplicates(subset='vrijeme',
                                 take_last=True,
                                 inplace=True) # za svaki slucaj ako dodamo 2 ista indeksa
        xbad = list(badTocke.index)
        ybad = list(badTocke[self.midline])

        return {'x':x,
                'y':y,
                'warningUp':warningUp,
                'warningLow':warningLow,
                'xok':xok,
                'yok':yok,
                'xbad':xbad,
                'ybad':ybad}

    def rect_zoom(self, eclick, erelease):
        super(ZeroSpanKanvas,self).rect_zoom(eclick, erelease)
        self.emit(QtCore.SIGNAL('sync_x_zoom(PyQt_PyObject)'), sorted([eclick.xdata, erelease.xdata]))

    def on_pick_point(self, event):
        """
        Callback za pick na ZERO ili SPAN grafu.
        """
        #definiraj x i y preko izabrane tocke
        x = self.data[self.gKanal].index[event.ind[0]]
        y = self.data[self.gKanal].loc[x, self.midline]
        minD = self.data[self.gKanal].loc[x, self.warningLow]
        maxD = self.data[self.gKanal].loc[x, self.warningHigh]
        # ako postoje vise istih indeksa, uzmi zadnji
        if type(y) is pd.core.series.Series:
            y = y[-1]
            minD = minD[-1]
            maxD = maxD[-1]
        if y >= minD and y<= maxD:
            status = 'Dobar'
        else:
            status = 'Ne valja'

        if event.mouseevent.button == 1 or event.mouseevent.button == 2:
            #left click or middle click
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

    def connect_pick_evente(self):
        self.cid2 = self.mpl_connect('pick_event', self.on_pick_point)

    def toggle_tgl(self):
        self.toggle_legend(self.graf_konfig.Legend)

################################################################################

################################################################################
class SpanKanvas(ZeroSpanKanvas):
    def __init__(self, konfig, appKonfig,  parent = None, width = 6, height = 5, dpi=100):
        self.graf_konfig = konfig.span
        self.tip_grafa = SpanEnum
        self.tip = 'SPAN'
        self.midline = 'vrijednost'
        self.warningLow = 'minDozvoljeno'
        self.warningHigh = 'maxDozvoljeno'
        super(SpanKanvas, self).__init__(konfig, appKonfig)
        self.highlightSize = 1.5 * self.dto.spanVOK.markerSize
        self.axes.xaxis.set_ticks_position('top')
        self.axes.figure.subplots_adjust(bottom = 0.02)
        self.axes.figure.subplots_adjust(right = 0.98)
        self.axes.set_ylabel(SpanEnum.tip.value)



    def crtaj_glavni_kanal(self):
        #priprema podataka za crtanje
        tocke = self.pripremi_zero_span_podatke_za_crtanje()

        linestyle = self.dto.spanMidline.lineStyle
        linewidth =  self.dto.spanMidline.lineWidth
        color = self.dto.spanMidline.color
        zorder = self.dto.spanMidline.zorder
        label = self.dto.spanMidline.label
        vok = self.dto.spanVOK
        vbad = self.dto.spanVBAD
        warning1 = self.dto.spanWarning1
        warning2 = self.dto.spanWarning2
        fill1 = self.dto.spanFill1
        fill2 = self.dto.spanFill2

        #midline (plot je drugacije definiran zbog pickera)
        self.axes.plot(tocke['x'],
                       tocke['y'],
                       linestyle = linestyle,
                       linewidth = linewidth,
                       color = color,
                       zorder = zorder,
                       label = label,
                       picker = 5)
        #ok values
        if len(tocke['xok']) > 0:
            self.crtaj_scatter(tocke['xok'], tocke['yok'], vok)
        #bad values
        if len(tocke['xbad']) > 0:
            self.crtaj_scatter(tocke['xbad'], tocke['ybad'], vbad)

        if warning1.crtaj:
            self.crtaj_line(tocke['x'], tocke['warningUp'], warning1)
            self.crtaj_line(tocke['x'], tocke['warningLow'], warning2)
        #fill
        ledge, hedge = self.axes.get_ylim() #y granice canvasa za fill
        if fill1.crtaj:
            self.crtaj_fill(tocke['x'], tocke['warningLow'], tocke['warningUp'], fill1)
            self.crtaj_fill(tocke['x'], tocke['warningUp'], hedge, fill2)
            self.crtaj_fill(tocke['x'], ledge, tocke['warningLow'], fill2)
        self.statusGlavniGraf = True

    def emit_request_za_podacima(self, arg):
        """
        Slanje zahtjeva za podacima. Kontroler vraca trazene podatke u member
        self.data. Opis zahtjeva (sto se tocno trazi) zadan je preko ulaznog argumenta
        arg (specificni dictionary podataka, ovisno o tipu grafa).
        """
        self.emit(QtCore.SIGNAL('request_span_frejm(PyQt_PyObject)'), arg)

    def crtaj_oznake_temperature(self, tempMin, tempMax):
        pass

    def updateaj_labele_na_panelu(self, tip, argList):
        """
        update labela na zero span panelu (istovremeno i trigger za pick najblize
        tocke na drugom canvasu, npr. click na zero canvasu triggera span canvas...)
        """
        if tip == 'pick':
            self.emit(QtCore.SIGNAL('pick_nearest(PyQt_PyObject)'),argList)
            self.emit(QtCore.SIGNAL('prikazi_info_span(PyQt_PyObject)'),argList)
        else:
            self.emit(QtCore.SIGNAL('prikazi_info_span(PyQt_PyObject)'),argList)


################################################################################
class ZeroKanvas(ZeroSpanKanvas):
    def __init__(self, konfig, appKonfig,  parent = None, width = 6, height = 5, dpi=100):
        self.tip = 'ZERO'
        self.midline = 'vrijednost'
        self.warningLow = 'minDozvoljeno'
        self.warningHigh = 'maxDozvoljeno'

        self.graf_konfig = konfig.zero

        super(ZeroKanvas, self).__init__(konfig, appKonfig)

        self.highlightSize = 1.5 * self.dto.zeroVOK.markerSize
        self.axes.xaxis.set_ticks_position('top')
        self.axes.figure.subplots_adjust(bottom = 0.02)
        self.axes.figure.subplots_adjust(right = 0.98)
        self.axes.set_ylabel(ZeroEnum.tip.value)




    def crtaj_glavni_kanal(self):
        #priprema podataka za crtanje
        tocke = self.pripremi_zero_span_podatke_za_crtanje()

        linestyle = self.dto.zeroMidline.lineStyle
        linewidth =  self.dto.zeroMidline.lineWidth
        color = self.dto.zeroMidline.color
        zorder = self.dto.zeroMidline.zorder
        label = self.dto.zeroMidline.label
        vok = self.dto.zeroVOK
        vbad = self.dto.zeroVBAD
        warning1 = self.dto.zeroWarning1
        warning2 = self.dto.zeroWarning2
        fill1 = self.dto.zeroFill1
        fill2 = self.dto.zeroFill2

        #midline (plot je drugacije definiran zbog pickera)
        self.axes.plot(tocke['x'],
                       tocke['y'],
                       linestyle = linestyle,
                       linewidth = linewidth,
                       color = color,
                       zorder = zorder,
                       label = label,
                       picker = 5)
        #ok values
        if len(tocke['xok']) > 0:
            self.crtaj_scatter(tocke['xok'], tocke['yok'], vok)
        #bad values
        if len(tocke['xbad']) > 0:
            self.crtaj_scatter(tocke['xbad'], tocke['ybad'], vbad)

        if warning1.crtaj:
            self.crtaj_line(tocke['x'], tocke['warningUp'], warning1)
            self.crtaj_line(tocke['x'], tocke['warningLow'], warning2)
        #fill
        ledge, hedge = self.axes.get_ylim() #y granice canvasa za fill
        if fill1.crtaj:
            self.crtaj_fill(tocke['x'], tocke['warningLow'], tocke['warningUp'], fill1)
            self.crtaj_fill(tocke['x'], tocke['warningUp'], hedge, fill2)
            self.crtaj_fill(tocke['x'], ledge, tocke['warningLow'], fill2)
        self.statusGlavniGraf = True

    def emit_request_za_podacima(self, arg):
        """
        Slanje zahtjeva za podacima. Kontroler vraca trazene podatke u member
        self.data. Opis zahtjeva (sto se tocno trazi) zadan je preko ulaznog argumenta
        arg (specificni dictionary podataka, ovisno o tipu grafa).
        """
        self.emit(QtCore.SIGNAL('request_zero_frejm(PyQt_PyObject)'), arg)

    def updateaj_labele_na_panelu(self, tip, argList):
        """
        update labela na zero span panelu (istovremeno i trigger za pick najblize
        tocke na drugom canvasu, npr. click na zero canvasu triggera span canvas...)
        """
        if tip =='pick':
            self.emit(QtCore.SIGNAL('pick_nearest(PyQt_PyObject)'),argList)
            self.emit(QtCore.SIGNAL('prikazi_info_zero(PyQt_PyObject)'),argList)
        else:
            self.emit(QtCore.SIGNAL('prikazi_info_zero(PyQt_PyObject)'),argList)

################################################################################

