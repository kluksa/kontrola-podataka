# -*- coding: utf-8 -*-
"""
Created on Fri Feb  6 13:10:01 2015

@author: User
"""

from PyQt4 import QtGui, uic

import pomocne_funkcije
###############################################################################
###############################################################################
base9, form9 = uic.loadUiType('./ui_files/opcije_pomocnih.ui')
class OpcijePomocnog(base9, form9):
    """
    Klasa je dijalog preko kojeg se bira i odredjuju postavke pomocnog
    grafa.
    """
###############################################################################
    def __init__(self, parent = None, default = [], stablo = None, copcije = None, mapa = {}):
        """
        inicijalizacija sa :
            -*listom defaultnih postavki za graf (postojeci izbor ili neki default)
            -stablo, instanca modela programa mjerenja (izbor stanice/kanala/usporedno)
            -copcije - lista combobox opcija [[markeri], [linije]]
            -opisna mapa (nested),  {programMjerenjaId:{stanica, kanal, usporedno....}}

        *lista sadrzi redom elemente:
        [kanal id, postaja, komponenta, usporedno, marker, markersize, line,
        linewidth, rgb tuple, alpha, zorder, label]
        """
        super(base9, self).__init__(parent)
        self.setupUi(self)

        self.markeri = copcije[0] #popis svih stilova markera
        self.linije = copcije[1] #popis svih stilova linije
        self.transformMapa = mapa #nested dict, programMjerenjaId:info o tom mjerenju

        #provjeri da li je default zadan, spremi default u privatni member
        if default == []:
            #definiraj defaultnu vrijednost
            self.defaultGraf = [None,
                            None,
                            None,
                            None,
                            'Bez markera',
                            12,
                            'Puna linija',
                            1.0,
                            (0,0,255),
                            1.0,
                            5,
                            '']
        else:
            self.defaultGraf = default

        #spremi stablo u privatni member
        self.stablo = stablo

        self.inicijaliziraj()
        self.veze()
###############################################################################
    def vrati_default_graf(self):
        """
        funkcija vraca member self.defaultGraf u kojemu su trenutne postavke
        pomocnog grafa
        """
        return self.defaultGraf
###############################################################################
    def inicijaliziraj(self):
        """
        Inicijaliztacija dijaloga.
        Postavljanje defaultnih vrijednosti u comboboxeve, spinboxeve...
        """
        #postavi model programa mjerenja u qtreeview
        self.treeView.setModel(self.stablo)

        #marker combo
        self.comboMarkerStil.clear()
        self.comboMarkerStil.addItems(self.markeri)
        self.comboMarkerStil.setCurrentIndex(self.comboMarkerStil.findText(self.defaultGraf[4]))

        #marker size
        self.spinMarker.setValue(self.defaultGraf[5])

        #linija combo
        self.comboLineStil.clear()
        self.comboLineStil.addItems(self.linije)
        self.comboLineStil.setCurrentIndex(self.comboLineStil.findText(self.defaultGraf[6]))

        #linija width
        self.doubleSpinLine.setValue(self.defaultGraf[7])

        #alpha vrijednost boje
        self.alphaBoja.setValue(self.defaultGraf[9])

        #boja, stil gumba
        rgb = self.defaultGraf[8]
        a = self.defaultGraf[9]
        self.set_widget_color_style(rgb, a, "QPushButton", self.bojaButton)

        #label
        self.lineEditLabel.clear()
        postaja = str(self.defaultGraf[1])
        komponenta = str(self.defaultGraf[2])
        usporedno = str(self.defaultGraf[3])
        nazivGrafa = postaja+':'+komponenta+':'+usporedno
        self.lineEditLabel.setText(nazivGrafa)
        self.defaultGraf[11] = nazivGrafa

        #pokusaj izabrati isti element u stablu (ako je element izabran)
        if self.defaultGraf[0] != None:
            self.postavi_novi_glavni_kanal(self.defaultGraf[0])
###############################################################################
    def veze(self):
        """
        povezivanje signala koji se emitiraju prilikom interakcije sa widgetima
        sa funkcijama koje mjenjaju stanje grafa.
        """
        self.lineEditLabel.textChanged.connect(self.promjeni_label)
        self.comboMarkerStil.currentIndexChanged.connect(self.promjeni_marker_stil)
        self.spinMarker.valueChanged.connect(self.promjeni_marker_size)
        self.comboLineStil.currentIndexChanged.connect(self.promjeni_line_stil)
        self.doubleSpinLine.valueChanged.connect(self.promjeni_line_width)
        self.bojaButton.clicked.connect(self.promjeni_boju)
        self.treeView.clicked.connect(self.promjeni_izbor_stabla)
        self.alphaBoja.valueChanged.connect(self.promjeni_alpha)
###############################################################################
    def promjeni_alpha(self, x):
        """
        promjena prozirnosti boje pomocnog kanala.
        """
        value = round(float(x), 2)
        #postavi novu vrijednost
        self.defaultGraf[9] = value
        #update boju gumba
        rgb = self.defaultGraf[8]
        self.set_widget_color_style(rgb, value, "QPushButton", self.bojaButton)
###############################################################################
    def pronadji_index_od_kanala(self, kanal):
        """
        Za zadani kanal (mjerenjeId) pronadji odgovarajuci QModelIndex u
        stablu.
        ulaz je trazeni kanal, izlaz je QModelIndex
        """
        #"proseci" stablom u potrazi za indeksom
        for i in range(self.stablo.rowCount()):
            ind = self.stablo.index(i, 0) #index stanice, (parent)
            otac = self.stablo.getItem(ind)
            for j in range(otac.childCount()):
                ind2 = self.stablo.index(j, 0, parent = ind) #indeks djeteta
                komponenta = self.stablo.getItem(ind2)
                #provjera da li kanal u modelu odgovara zadanom kanalu
                if int(komponenta._data[2]) == kanal:
                    return ind2
        return None
###############################################################################
    def postavi_novi_glavni_kanal(self, kanal):
        """
        Metoda postavlja zadani kanal kao selektirani u treeView.
        Koristi se tijekom inicijalizacije
        """
        noviIndex = self.pronadji_index_od_kanala(kanal)
        if noviIndex != None:
            #postavi novi indeks
            self.treeView.setCurrentIndex(noviIndex)
            #javi za promjenu izbora stabla
            self.promjeni_izbor_stabla(True)
###############################################################################
    def promjeni_izbor_stabla(self, x):
        """
        promjena/izbor programa mjerenja sa stabla (Postaja/Kanal/Usporedno)
        """
        ind = self.treeView.currentIndex() #dohvati trenutni aktivni indeks
        item = self.stablo.getItem(ind) #dohvati specificni objekt pod tim indeksom
        prog = item._data[2] #dohvati program mjerenja iz liste podataka
        """
        Ako netko izabere stanicu u stablu, prog == None
        Ako netko izabere komponentu u stablu, prog == programMjerenjaId

        nastavi samo ako je izabrana komponenta!
        """
        if prog != None:
            prog = int(prog)
            #uz pomoc mape self.transformMapa dohvati postaju/komponentu/usporedno
            postaja = str(self.transformMapa[prog]['postajaNaziv'])
            komponenta = str(self.transformMapa[prog]['komponentaNaziv'])
            usporedno = str(self.transformMapa[prog]['usporednoMjerenje'])

            #promjeni self.defaultGraf ciljane vrijednosti
            self.defaultGraf[0] = prog
            self.defaultGraf[1] = postaja
            self.defaultGraf[2] = komponenta
            self.defaultGraf[3] = usporedno

            #promjeni label da odgovara izboru
            tekst = postaja+':'+komponenta+':'+usporedno
            self.lineEditLabel.clear()
            self.lineEditLabel.setText(tekst)
###############################################################################
    def promjeni_label(self, tekst):
        """
        promjeni/zamapti promjenu labela
        """
        self.defaultGraf[11] = str(tekst)
###############################################################################
    def promjeni_marker_stil(self):
        """
        promjeni/zapamti promjenu stila makrera
        """
        marker = self.comboMarkerStil.currentText()
        self.defaultGraf[4] = marker
###############################################################################
    def promjeni_line_stil(self):
        """
        promjeni/zapamti promjenu stila linije
        """
        marker = self.comboLineStil.currentText()
        self.defaultGraf[6] = marker
###############################################################################
    def promjeni_marker_size(self):
        """
        promjeni/zapamti promjenu velicine markera
        """
        self.defaultGraf[5] = self.spinMarker.value()
###############################################################################
    def promjeni_line_width(self):
        """
        promjeni/zapamti promjenu sirine linije
        """
        self.defaultGraf[7] = self.doubleSpinLine.value()
###############################################################################
    def promjeni_boju(self):
        """
        promjeni/zapamti promjenu boje grafa
        """
        #defaultni izbor
        rgb = self.defaultGraf[8]
        a = self.defaultGraf[9]
        #convert u QColor
        boja = pomocne_funkcije.default_color_to_qcolor(rgb, a)
        #poziv dijaloga za promjenu boje
        color, test = QtGui.QColorDialog.getRgba(boja.rgba(), self)
        if test: #test == True ako je boja ispravno definirana
            color = QtGui.QColor.fromRgba(color) #bitni adapter izlaza dijaloga
            rgb, a = pomocne_funkcije.qcolor_to_default_color(color)
            #zapamti novu boju
            self.defaultGraf[8] = rgb
            self.defaultGraf[9] = a

            #set novu alpha vrijednost u odgovarajuci QDoubleSpinBox
            self.alphaBoja.setValue(a)

            #promjeni boju gumba
            self.set_widget_color_style(rgb, a, "QPushButton", self.bojaButton)
###############################################################################
    def set_widget_color_style(self, rgb, a, tip, target):
        """
        izrada stila widgeta
        tip - qwidget tip, npr "QPushButton"
        target - instanca widgeta kojem mjenjamo stil
        """
        #get string name of target object
        name = str(target.objectName())
        #napravi stil
        stil = pomocne_funkcije.rgba_to_style_string(rgb, a , tip, name)
        #set stil u target
        target.setStyleSheet(stil)
###############################################################################
###############################################################################