# -*- coding: utf-8 -*-
"""
Created on Mon Feb  2 11:22:25 2015

@author: User

Klasa (canvas) za prikaz ZERO ili SPAN vrijednosti.
"""
import matplotlib as mpl

import pomocneFunkcije #import pomocnih funkcija
import opcenitiCanvas #import opcenitog (abstract) canvasa
###############################################################################
###############################################################################
class ZeroSpanGraf(opcenitiCanvas.MPLCanvas):
    """
    Klasa za prikaz Zero vrijednosti
    """
    def __init__(self, *args, tip = None, lok = None, **kwargs):
        """konstruktor"""
        opcenitiCanvas.MPLCanvas.__init__(self, *args, **kwargs)

        self.data = None
        self.zeroNacrtan = False

        self.annotationStatus = False
        self.zadnjiAnnotation = None
        
        #tip odredjuje da li je ovo zero ili span graf
        self.tipGrafa = tip
        #lokacija odredjuje da li je graf na vrhu ili dnu ('top', 'bottom')
        self.lokacija = lok
        
        """
        SETTER POZICIJE GRAFA
        - pomicanje canvasa
        - pomicanje kooridinatnih osi
        - odredjivanje na kojoj osi se crtaju tickovi
        """
        if self.lokacija == 'top':
            #prebaci lokaciju tickova
            self.axes.xaxis.set_ticks_position('top')
            #makni splneove sa dna
            #self.axes.spines['bottom'].set_visible(False)
            #pomakni figure da pokrije sto vise prostora udesno i dolje
            self.axes.figure.subplots_adjust(bottom = 0.02)
            self.axes.figure.subplots_adjust(right = 0.98)
        else:
            self.axes.xaxis.set_ticks_position('bottom')
            """
            Ako maknemo gornji spine, 2 canvasa ce se sljepiti bez vidljivog
            ruba...
            """
            #self.axes.spines['top'].set_visible(False)
            self.axes.figure.subplots_adjust(top = 0.98)
            self.axes.figure.subplots_adjust(right = 0.98)
        
        
        self.veze()
###############################################################################
    def crtaj(self, ulaz):
        """
        crtanje frejma Zero na canvasu
        
        Problem sa crtanjem... moram nacrtati liniju odvojeno bez picka
        scatter podataka sa pickom.

        inace i linija je pickable objekt koji dovodi do konfuznih situacija
        
        dodatno, prosljedi member u kojemu se nalazi opis grafa (marker, line...)

        """
        self.axes.clear()

        self.data = ulaz[0]
        self.detalji = ulaz[1]
        self.raspon = ulaz[2]

        #zadnji ulazni datum
        #endpoint = self.data.loc[self.data.index[-1], 'vrijeme']
        endpoint = self.raspon[1]
        #prvi ulazni datum
        #beginpoint = self.data.loc[self.data.index[0], 'vrijeme']
        beginpoint = self.raspon[0]
        
        #pomak xlimita grafa da tocke nisu na rubu
        tmin, tmax = pomocneFunkcije.prosiri_granice_grafa(beginpoint, endpoint, 1440)
        self.axes.set_xlim([tmin, tmax])
                
        #center line graf data  
        lineFrame = ulaz[0].copy()
        self.data = lineFrame
        x = list(lineFrame.index)
        y = list(lineFrame['vrijednost'])

        okFrame = ulaz[0].copy()
        badFrameMin = ulaz[0].copy()
        badFrameMax = ulaz[0].copy()
        
        okTocke = okFrame[okFrame['vrijednost'] <= okFrame['maxDozvoljeno']]
        okTocke = okTocke[okTocke['vrijednost'] >= okTocke['minDozvoljeno']]
        
        #x, y kooridinate "dobrih" podataka
        xok = list(okTocke.index)
        yok = list(okTocke['vrijednost'])
        
        badTocke1 = badFrameMax[badFrameMax['vrijednost'] > badFrameMax['maxDozvoljeno']]
        badTocke2 = badFrameMin[badFrameMin['vrijednost'] < badFrameMin['minDozvoljeno']]
        
        #x, y kooridinate "losih" podataka vecih od dozvoljenih
        xbadh = list(badTocke1.index)
        ybadh = list(badTocke1['vrijednost'])
        #x, y kooridinate "losih" podataka manjih od dozvoljenih
        xbadl = list(badTocke2.index)
        ybadl = list(badTocke2['vrijednost'])
        
                
        #sredi tickove
        tickLoc, tickLab = pomocneFunkcije.sredi_xtickove_zerospan(x)
        self.axes.set_xticks(tickLoc)
        self.axes.set_xticklabels(tickLab)

        self.xWarning = x
        self.yMinWarning = list(lineFrame['minDozvoljeno'])
        self.yMaxWarning = list(lineFrame['maxDozvoljeno'])

                
        """PLOT LINIJE IZMEDJU TOCAKA PODATAKA"""
        self.axes.plot(x, 
                       y, 
                       color = pomocneFunkcije.normalize_rgb(self.detalji[self.tipGrafa]['midline']['rgb']), 
                       alpha = self.detalji[self.tipGrafa]['midline']['alpha'], 
                       linestyle = self.detalji[self.tipGrafa]['midline']['line'], 
                       linewidth = self.detalji[self.tipGrafa]['midline']['linewidth'], 
                       zorder = self.detalji[self.tipGrafa]['midline']['zorder'],
                       picker = self.detalji[self.tipGrafa]['midline']['picker'])

        """plot grafa granice tolerancije (waning line)"""
        boja = pomocneFunkcije.normalize_rgb(self.detalji[self.tipGrafa]['warning']['rgb'])
        a = self.detalji[self.tipGrafa]['warning']['alpha']
        hexcolor = mpl.colors.rgb2hex(boja)
        edgeBoja = mpl.colors.colorConverter.to_rgba(hexcolor, alpha = a)
        if self.detalji[self.tipGrafa]['warning']['crtaj']:
            #upper
            self.axes.plot(self.xWarning, 
                           self.yMaxWarning, 
                           linestyle = self.detalji[self.tipGrafa]['warning']['line'], 
                           color = edgeBoja, 
                           alpha = a, 
                           linewidth = self.detalji[self.tipGrafa]['warning']['linewidth'], 
                           zorder = self.detalji[self.tipGrafa]['warning']['zorder'])
            #lower
            self.axes.plot(self.xWarning, 
                           self.yMinWarning, 
                           linestyle = self.detalji[self.tipGrafa]['warning']['line'], 
                           color = edgeBoja, 
                           alpha = a, 
                           linewidth = self.detalji[self.tipGrafa]['warning']['linewidth'], 
                           zorder = self.detalji[self.tipGrafa]['warning']['zorder'])
                           
        if len(xok) > 0:
            """PLOT OK TOCAKA"""
            boja = pomocneFunkcije.normalize_rgb(self.detalji[self.tipGrafa]['ok']['rgb'])
            a = self.detalji[self.tipGrafa]['ok']['alpha']
            #convert rgb to hexcode, then convert hexcode to valid rgba
            hexcolor = mpl.colors.rgb2hex(boja)
            edgeBoja = mpl.colors.colorConverter.to_rgba(hexcolor, alpha = a)            
            self.axes.plot(xok, 
                           yok, 
                           marker = self.detalji[self.tipGrafa]['ok']['marker'],
                           markersize = self.detalji[self.tipGrafa]['ok']['markersize'], 
                           color = edgeBoja,
                           alpha = a,
                           linestyle = 'None',
                           zorder = self.detalji[self.tipGrafa]['ok']['zorder'])

        if len(xbadh) > 0:
            """PLOT BAD TOCAKA"""
            boja = pomocneFunkcije.normalize_rgb(self.detalji[self.tipGrafa]['bad']['rgb'])
            a = self.detalji[self.tipGrafa]['bad']['alpha']
            #convert rgb to hexcode, then convert hexcode to valid rgba
            hexcolor = mpl.colors.rgb2hex(boja)
            edgeBoja = mpl.colors.colorConverter.to_rgba(hexcolor, alpha = a)
            self.axes.plot(xbadh, 
                           ybadh, 
                           marker = self.detalji[self.tipGrafa]['bad']['marker'],
                           markersize = self.detalji[self.tipGrafa]['bad']['markersize'], 
                           color = edgeBoja, 
                           alpha = a,
                           linestyle = 'None',
                           zorder = self.detalji[self.tipGrafa]['bad']['zorder'])

        if len(xbadl) > 0:
            """PLOT BAD TOCAKA"""
            boja = pomocneFunkcije.normalize_rgb(self.detalji[self.tipGrafa]['bad']['rgb'])
            a = self.detalji[self.tipGrafa]['bad']['alpha']
            #convert rgb to hexcode, then convert hexcode to valid rgba
            hexcolor = mpl.colors.rgb2hex(boja)
            edgeBoja = mpl.colors.colorConverter.to_rgba(hexcolor, alpha = a)
            self.axes.plot(xbadl, 
                           ybadl, 
                           marker = self.detalji[self.tipGrafa]['bad']['marker'],
                           markersize = self.detalji[self.tipGrafa]['bad']['markersize'], 
                           color = edgeBoja, 
                           alpha = a,
                           linestyle = 'None',
                           zorder = self.detalji[self.tipGrafa]['bad']['zorder'])


        self.axes.set_xlabel('Vrijeme')
        self.axes.set_ylabel(self.tipGrafa.upper())
        
        xLabels = self.axes.get_xticklabels()
        for label in xLabels:
            #cilj je lagano zaokrenuti labele da nisu jedan preko drugog
            label.set_rotation(30)
            label.set_fontsize(8)

        """plot filla izmedju warning linija"""
        boja = pomocneFunkcije.normalize_rgb(self.detalji[self.tipGrafa]['fill']['rgb'])
        a = self.detalji[self.tipGrafa]['fill']['alpha']
        hexcolor = mpl.colors.rgb2hex(boja)
        edgeBoja = mpl.colors.colorConverter.to_rgba(hexcolor, alpha = a)
        if self.detalji[self.tipGrafa]['fill']['crtaj']:
            #fill izmedju warning linija
            self.axes.fill_between(self.xWarning, 
                                   self.yMinWarning,
                                   self.yMaxWarning, 
                                   color = edgeBoja, 
                                   alpha = a, 
                                   zorder = 1)
                                   
        self.defaultRasponX = self.axes.get_xlim()
        self.defaultRasponY = self.axes.get_ylim()
        
        self.draw()
        
        #zapamti max granice grafa za full zoom out!
        self.xlim_original = (tmin, tmax)
        self.ylim_original = self.axes.get_ylim()
        #unpacking tuple za fill2
        ylimmin, ylimmax = self.ylim_original
        
        """plot filla izvan warning linija"""
        boja = pomocneFunkcije.normalize_rgb(self.detalji[self.tipGrafa]['fill2']['rgb'])
        a = self.detalji[self.tipGrafa]['fill2']['alpha']
        hexcolor = mpl.colors.rgb2hex(boja)
        edgeBoja = mpl.colors.colorConverter.to_rgba(hexcolor, alpha = a)
        if self.detalji[self.tipGrafa]['fill2']['crtaj']:
            #fill below
            self.axes.fill_between(self.xWarning, 
                                   self.yMinWarning,
                                   ylimmin, 
                                   color = edgeBoja, 
                                   alpha = a, 
                                   zorder = 1)
            #fill above
            self.axes.fill_between(self.xWarning, 
                                   self.yMaxWarning,
                                   ylimmax, 
                                   color = edgeBoja, 
                                   alpha = a, 
                                   zorder = 1)
                        
        self.draw()
        
        self.zeroNacrtan = True
###############################################################################
    def veze(self):
        """
        povezivanje callback funkcija matplotlib canvasa (pick...)
        """
        self.mpl_connect('scroll_event', self.scroll_zoom)
        self.mpl_connect('pick_event', self.on_pick)
###############################################################################
    def on_pick(self, event):
        """
        pick callback, ali funkcionira samo ako se pickaju tocke na grafu
        """
        if self.MODEPICK:
            #definiraj x i y preko izabrane tocke
            x = self.data.index[event.ind[0]]
            y = self.data.loc[x, 'vrijednost']
    
            if event.mouseevent.button == 2:
                #middle click
                if self.annotationStatus:
                    self.annotation.remove()
                    self.annotationStatus = False
                    self.draw()
                    if self.zadnjiAnnotation != x:
                        self.napravi_annotation(x, y, event.mouseevent)
                else:
                    self.napravi_annotation(x, y, event.mouseevent)
###############################################################################
    def napravi_annotation(self, x, y, event):
        """
        Napravi annotation na grafu, sa opisom x i y kooridinate.
        
        ulaz:
        x, y vrijednosti tocke u data kooridinatama
        event je instanca event.mouseevent dogadjaja
        
        output je self.annotation - specificna instanca annotationa
        """
        tekst = 'Vrijeme: '+str(x)+'\n'+self.tipGrafa.upper()+': '+str(y)
        #definicija offseta anootationa
        px = float(event.x)
        py = float(event.y)
        if px > 200:
            aox = px - 180
        else:
            aox = px + 50
            
        if py > 100:
            aoy = py - 50
        else:
            aoy = py + 20
        
        #instanca annotationa
        self.annotation = self.axes.annotate(
            tekst, 
            xy = (str(x), y), 
            xycoords = 'data', 
            xytext = (aox, aoy), 
            textcoords = 'axes pixels', 
            ha = 'left', 
            va = 'center', 
            fontsize = 7, 
            zorder = 5, 
            bbox = dict(boxstyle = 'square', fc = 'cyan', alpha = 0.7), 
            arrowprops = dict(arrowstyle = '->'))
        
        #zapamti koji je annotation aktivan.
        self.annotationStatus = True
        self.zadnjiAnnotation = x
        #nacrtaj
        self.draw()
###############################################################################
    def clear_me(self):
        """
        clear grafa
        """
        self.axes.clear()
        #nema podataka ili do njih nije moguce pristupiti
        self.axes.text(0.5, 
                       0.5, 
                       'Nemoguce pristupiti podacima', 
                       horizontalalignment='center', 
                       verticalalignment='center', 
                       fontsize = 8, 
                       transform = self.axes.transAxes)
        self.draw()
###############################################################################
    def scroll_zoom(self, event):
        """
        Implementacija zooma uz pomoc scroll gumba.
        
        scroll up   --> zoom in
        scroll down --> zoom out
        
        Zoom je centriran okolo pozicije misa kada se scrolla. ta tocka ce uvijek
        ostati tamo gdje je i bila, samo ce se skala pomaknuti za predefinirani
        faktor povecanja.
        
        BITNO JE NAPOMENUTI! zoom samo redefinira granice koje se prikazuju
        """
        #zanemari ako je cursor izvan canvasa
        if event.inaxes:
            #nadji trenutni raspon x i y osi
            xRaspon = self.axes.get_xlim()
            yRaspon = self.axes.get_ylim()
            #nadji tocku iznad koje je aktiviran scroll_event
            trenutniX = event.xdata
            trenutniY = event.ydata
            #definiraj povecanje zooma, gradacija zooma
            faktorPovecanja = 1.5
            #odredi novu skalu (raspon) ovisno o smjeru scrolla
            if event.button == 'down':
                #zoom out
                skala = faktorPovecanja
            elif event.button == 'up':
                #zoom in
                skala = 1.0 / faktorPovecanja
            else:
                """
                potencijalni visak, ali za svaki slucaj da event.button ne bude
                'up' ili 'down' vec nesto trece.
                """
                #tj. nemoj niti povecati niti smanjiti raspon x i y osi
                skala = 1
            
            if self.zeroNacrtan:
                #nova duljina / raspon skale xmax-xmin
                lenNoviX = (xRaspon[1] - xRaspon[0]) * skala
                lenNoviY = (yRaspon[1] - yRaspon[0]) * skala
            
                #relativni polozaj tocke od koje radimo zoom
                relPosX = (xRaspon[1] - trenutniX) / (xRaspon[1] - xRaspon[0])
                relPosY = (yRaspon[1] - trenutniY) / (yRaspon[1] - yRaspon[0])
                
                #racunanje novih x granica grafa
                xmin = trenutniX - lenNoviX * (1 - relPosX)
                xmax = trenutniX + lenNoviX * relPosX
            
                #racunanje novih y granica grafa
                ymin = trenutniY - lenNoviY * (1 - relPosY)
                ymax = trenutniY + lenNoviY * relPosY
            
                #onemoguci zoom out izvan granica originalnog grafa
                if self.defaultRasponX[0] > xmin:
                    xmin = self.defaultRasponX[0]
                if self.defaultRasponX[1] < xmax:
                    xmax = self.defaultRasponX[1]
                if self.defaultRasponY[0] > ymin:
                    ymin = self.defaultRasponY[0]
                if self.defaultRasponY[1] < ymax:
                    ymax = self.defaultRasponY[1]
            
                #postavi nove granice
                self.axes.set_xlim([xmin, xmax])
                self.axes.set_ylim([ymin, ymax])
                
                #prikazi promjenu
                self.draw()
###############################################################################
###############################################################################