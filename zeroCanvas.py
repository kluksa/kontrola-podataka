# -*- coding: utf-8 -*-
"""
Created on Mon Feb  2 11:22:25 2015

@author: User

Klasa (canvas) za prikaz Zero vrijednosti (zero/span).
"""
import matplotlib as mpl
import pandas as pd

import pomocneFunkcije #import pomocnih funkcija
import opcenitiCanvas #import opcenitog (abstract) canvasa
###############################################################################
###############################################################################
class Graf(opcenitiCanvas.MPLCanvas):
    """
    Klasa za prikaz Zero vrijednosti
    """
    def __init__(self, *args, **kwargs):
        """konstruktor"""
        opcenitiCanvas.MPLCanvas.__init__(self, *args, **kwargs)

        self.data = None
        self.zeroNacrtan = False

        self.annotationStatus = False
        self.zadnjiAnnotation = None
                      
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
        
        #TODO! prebaci na zero opis...
        self.detalji = ulaz[1]
        self.data = ulaz[0]
        
        #TODO! mangle frame data
        #center line graf data  
        lineFrame = ulaz[0].copy()
        self.data = lineFrame
        x = list(lineFrame.index)
        y = list(lineFrame['vrijednost'])
        
        #scatter plot data - pickable tocke        
        #TODO! za sada neki hardcoded crud
        okFrame = ulaz[0].copy()
        badFrame = ulaz[0].copy()
        
        #neke default granice? ovo se mora bolje srediti... neka funkcija?
        lower = -0.5
        upper = 0.5
        #TODO! plot horizontalnih linija u step obliku za zadane datume...
        #self.axes.ahline(y = lower)


        okTocke = okFrame[okFrame['vrijednost'] >= lower]
        okTocke = okTocke[okTocke['vrijednost'] <= upper]
        xok = list(okTocke.index)
        yok = list(okTocke['vrijednost'])
        
        
        for indeks in lineFrame.index:
            if indeks in xok:
                badFrame = badFrame.drop([indeks])
        
        xbad = list(badFrame.index)
        ybad = list(badFrame['vrijednost'])
        
        #sredi tickove
        tickLoc, tickLab = pomocneFunkcije.sredi_xtickove_zerospan(x)
        self.axes.set_xticks(tickLoc)
        self.axes.set_xticklabels(tickLab)
        
        #PLOT LINIJE IZMEDJU TOCAKA PODATAKA        
        self.axes.plot(x, 
                       y, 
                       color = pomocneFunkcije.normalize_rgb(self.detalji['zero']['midline']['rgb']), 
                       alpha = self.detalji['zero']['midline']['alpha'], 
                       linestyle = self.detalji['zero']['midline']['line'], 
                       linewidth = self.detalji['zero']['midline']['linewidth'], 
                       zorder = self.detalji['zero']['midline']['zorder'],
                       picker = self.detalji['zero']['midline']['picker'])

        if len(xok) > 0:
            #PLOT OK TOCAKA
            boja = pomocneFunkcije.normalize_rgb(self.detalji['zero']['ok']['rgb'])
            a = self.detalji['zero']['ok']['alpha']
            #convert rgb to hexcode, then convert hexcode to valid rgba
            hexcolor = mpl.colors.rgb2hex(boja)
            edgeBoja = mpl.colors.colorConverter.to_rgba(hexcolor, alpha = a)            
            self.axes.plot(xok, 
                           yok, 
                           marker = self.detalji['zero']['ok']['marker'],
                           markersize = self.detalji['zero']['ok']['markersize'], 
                           color = edgeBoja,
                           alpha = a,
                           linestyle = 'None',
                           zorder = self.detalji['zero']['ok']['zorder'])

        if len(xbad) > 0:
            #PLOT BAD TOCAKA
            boja = pomocneFunkcije.normalize_rgb(self.detalji['zero']['bad']['rgb'])
            a = self.detalji['zero']['bad']['alpha']
            #convert rgb to hexcode, then convert hexcode to valid rgba
            hexcolor = mpl.colors.rgb2hex(boja)
            edgeBoja = mpl.colors.colorConverter.to_rgba(hexcolor, alpha = a)
            self.axes.plot(xbad, 
                           ybad, 
                           marker = self.detalji['zero']['bad']['marker'],
                           markersize = self.detalji['zero']['bad']['markersize'], 
                           color = edgeBoja, 
                           alpha = a,
                           linestyle = 'None',
                           zorder = self.detalji['zero']['bad']['zorder'])

        self.axes.set_xlabel('Vrijeme')
        self.axes.set_ylabel('Zero')
        
        xLabels = self.axes.get_xticklabels()
        for label in xLabels:
            #cilj je lagano zaokrenuti labele da nisu jedan preko drugog
            label.set_rotation(30)
            label.set_fontsize(8)
        
        self.zeroNacrtan = True
        self.defaultRasponX = self.axes.get_xlim()
        self.defaultRasponY = self.axes.get_ylim()
        
        self.draw()
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
        tekst = 'Vrijeme: '+str(x)+'\nSpan: '+str(y)
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
