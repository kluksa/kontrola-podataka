# -*- coding: utf-8 -*-
"""
Created on Mon Feb  2 12:34:36 2015

@author: User
"""

import pomocneFunkcije #import pomocnih funkcija
import opcenitiCanvas #import opcenitog (abstract) canvasa
###############################################################################
###############################################################################
class Graf(opcenitiCanvas.MPLCanvas):
    """
    Klasa za prikaz span vrijednosti
    """
    def __init__(self, *args, **kwargs):
        """konstruktor"""
        opcenitiCanvas.MPLCanvas.__init__(self, *args, **kwargs)
        self.zeroNacrtan = False
        self.data = {} #privremeni spremnik za frejmove (ucitane)
        self.veze()
###############################################################################
    def crtaj(self, frejm):
        """
        crtanje frejma span na canvasu
        """
        self.axes.clear()
        
        x = list(frejm.index)
        y = list(frejm['vrijednost'])
        
        #sredi tickove
        tickLoc, tickLab = pomocneFunkcije.sredi_xtickove_zerospan(x)
        self.axes.set_xticks(tickLoc)
        self.axes.set_xticklabels(tickLab)
        
        self.axes.plot(x, y)
        self.axes.set_xlabel('Vrijeme')
        self.axes.set_ylabel('Span')

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