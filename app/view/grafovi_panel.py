# -*- coding: utf-8 -*-
"""
Created on Mon Nov 10 08:50:02 2014

@author: User

Panel za grafove.
Wrapper koji sadrzi:
    1. label sa informacijom o glavnom kanalu te vremenskom slajsu.
    2. gumbe za navigaciju (prethodni i sljedeci dan)
    3. satni canvas (canvas za prikaz satno agregiranih podataka)
    4. minutni canvas (canvas za prikaz minutnih podataka)
"""

import logging
import datetime
from PyQt4 import QtCore, QtGui, uic

import app.view.canvas as canvas
###############################################################################
###############################################################################
base2, form2 = uic.loadUiType('./app/view/ui_files/konc_graf_panel.ui')
class KoncPanel(base2, form2):
    """
    Klasa panela u kojem se nalaze koncentracijski grafovi i kontrole za pojedini graf
    """
    def __init__(self, konfig, parent = None):
        """
        za inicijalizaciju panela potreban je konfig objekt aplikacije (konfig)
        """
        super(base2, self).__init__(parent)
        self.setupUi(self)

        self.konfig = konfig
        #inicijalizacija canvasa (samo sa djelom konfiga koji je potreban za
        #funkcioniranje klase i sa mapom pomocnih kanala)
        self.satniGraf = canvas.SatniKanvas(konfig.satni, konfig)
        self.minutniGraf = canvas.MinutniKanvas(konfig.minutni, konfig)

        #dodavanje canvasa u layout panela
        self.verticalLayoutSatni.addWidget(self.satniGraf)
        self.verticalLayoutMinutni.addWidget(self.minutniGraf)

        self.setup_icons()

        #kontrolni gumbi
        self.buttonSljedeci.clicked.connect(self.prebaci_dan_naprijed)
        self.buttonPrethodni.clicked.connect(self.prebaci_dan_nazad)
        self.buttonPonisti.clicked.connect(self.ponisti_promjene)
        self.brojDanaCombo.currentIndexChanged.connect(self.promjeni_broj_dana)
        self.zoomInSatni.clicked.connect(self.satniGraf.toggle_zoom)
        self.zoomOutSatni.clicked.connect(self.satniGraf.zoom_out)
        self.zoomOutSatniFull.clicked.connect(self.satniGraf.zoom_out_full)
        self.toggleGridSatni.clicked.connect(self.toggle_satni_grid)
        self.toggleLegendSatni.clicked.connect(self.toggle_satni_legend)
        self.zoomInMinutni.clicked.connect(self.minutniGraf.toggle_zoom)
        self.zoomOutMinutni.clicked.connect(self.minutniGraf.zoom_out)
        self.zoomOutMinutniFull.clicked.connect(self.minutniGraf.zoom_out_full)
        self.toggleGridMinutni.clicked.connect(self.toggle_minutni_grid)
        self.toggleLegendMinutni.clicked.connect(self.toggle_minutni_legend)
        self.brojSatiCombo.currentIndexChanged.connect(self.promjeni_broj_sati)

        #inicijalno stanje check statusa kontrola
        self.toggleGridSatni.setChecked(self.konfig.satni.Grid)
        self.toggleLegendSatni.setChecked(self.konfig.satni.Legend)
        self.toggleGridMinutni.setChecked(self.konfig.minutni.Grid)
        self.toggleLegendMinutni.setChecked(self.konfig.minutni.Legend)
###############################################################################
    def toggle_satni_grid(self, x):
        """prosljeduje naredbu za toggle grida na satnom grafu"""
        self.konfig.satni.set_grid(x)
        self.satniGraf.toggle_grid(x)
###############################################################################
    def toggle_satni_legend(self, x):
        """prosljeduje naredbu za toggle legende na satnom grafu"""
        self.konfig.satni.set_legend(x)
        self.satniGraf.toggle_legend(x)
###############################################################################
    def toggle_minutni_grid(self, x):
        """prosljeduje naredbu za toggle grida na minutnom grafu"""
        self.konfig.minutni.set_grid(x)
        self.minutniGraf.toggle_grid(x)
###############################################################################
    def toggle_minutni_legend(self, x):
        """prosljeduje naredbu za toggle legende na minutnom grafu"""
        self.konfig.minutni.set_legend(x)
        self.minutniGraf.toggle_legend(x)
###############################################################################
    def setup_icons(self):
        """
        Postavljanje ikona za gumbe
        """
        self.zoomInSatni.setIcon(QtGui.QIcon('./app/view/icons/zoomin.png'))
        self.zoomOutSatni.setIcon(QtGui.QIcon('./app/view/icons/zoomout.png'))
        self.zoomOutSatniFull.setIcon(QtGui.QIcon('./app/view/icons/zoomoutfull.png'))
        self.toggleGridSatni.setIcon(QtGui.QIcon('./app/view/icons/grid.png'))
        self.toggleLegendSatni.setIcon(QtGui.QIcon('./app/view/icons/listing.png'))
        self.zoomInMinutni.setIcon(QtGui.QIcon('./app/view/icons/zoomin.png'))
        self.zoomOutMinutni.setIcon(QtGui.QIcon('./app/view/icons/zoomout.png'))
        self.zoomOutMinutniFull.setIcon(QtGui.QIcon('./app/view/icons/zoomoutfull.png'))
        self.toggleGridMinutni.setIcon(QtGui.QIcon('./app/view/icons/grid.png'))
        self.toggleLegendMinutni.setIcon(QtGui.QIcon('./app/view/icons/listing.png'))
###############################################################################
    def ponisti_promjene(self):
        """emitiraj signal kontroleru da 'ponisti' promjene za trenutni dan i postaju"""
        self.emit(QtCore.SIGNAL('ponisti_izmjene'))
###############################################################################
    def promjeni_broj_dana(self, x):
        """
        emitiraj signal za promjenu broja dana za prikaz
        """
        value = int(self.brojDanaCombo.currentText())
        self.emit(QtCore.SIGNAL('promjeni_max_broj_dana_satnog(PyQt_PyObject)'), value)
###############################################################################
    def promjeni_broj_sati(self, x):
        """
        emitiraj signal za promjenu broja sati za prikaz na minutom grafu
        """
        value = int(self.brojSatiCombo.currentText())
        self.emit(QtCore.SIGNAL('promjeni_max_broj_sati_minutnog(PyQt_PyObject)'), value)
###############################################################################
    def change_glavniLabel(self, ulaz):
        """
        ova funkcija kao ulazni parametar uzima mapu koja ima 2 elementa.
        -'opis' = mapa, opis kanala (naziv, mjerna jedinica, postaja...)
        -'datum' = string, datum formata YYYY-MM-DD

        Informacija o izboru se postavlja u label.
        """
        mapa = ulaz['opis']
        mjerenjeId = ulaz['mjerenjeId']
        datum = ulaz['datum']
        postaja = mapa['postajaNaziv']
        komponenta = mapa['komponentaNaziv']
        formula = mapa['komponentaFormula']
        mjernaJedinica = mapa['komponentaMjernaJedinica']
        opis = '{0}, {1}( {2} ) [{3}]. Datum : {4} . mjerenjeId:{5}'.format(postaja, komponenta, formula, mjernaJedinica, datum, mjerenjeId)
        self.glavniLabel.setText(opis)
        logging.info('glavniLabel promjenjen, value = {0}'.format(opis))
###############################################################################
    def change_satLabel(self, sat):
        """
        funkcija postavlja string izabranog sata sa satno agregiranog grafa u
        satLabel.
        """
        msg = str(sat)
        self.satLabel.setText(msg)
        logging.info('satLabel promjenjen, value = {0}'.format(msg))
###############################################################################
    def prebaci_dan_naprijed(self):
        """
        Signaliziraj kontroleru da treba prebaciti kalendar 1 dan naprjed
        """
        self.emit(QtCore.SIGNAL('promjeni_datum(PyQt_PyObject)'), 1)
        logging.info('request pomak dana unaprijed')
###############################################################################
    def prebaci_dan_nazad(self):
        """
        Signaliziraj kontroleru da treba prebaciti kalendar 1 dan nazad
        """
        self.emit(QtCore.SIGNAL('promjeni_datum(PyQt_PyObject)'), -1)
        logging.info('request pomak dana unazad')
###############################################################################
    def set_labele_satne_tocke(self, arg):
        """
        Setter labela podataka za satno agregiranu tocku. Prikazuju se podaci:
        vrijeme, average, min, max, count, status. Ista metoda se koristi
        za clear, samo se treba poslati set praznih stringova.

        ulazni parametar arg je dictionary sa vrjiednostima labela. Sve vrijednosti
        moraju biti stringovi!
        """
        self.satniStatus.clear()
        self.satniVrijeme.setText(str(arg['vrijeme']))
        self.satniAverage.setText(str(arg['average']))
        self.satniMin.setText(str(arg['min']))
        self.satniMax.setText(str(arg['max']))
        self.satniCount.setText(str(arg['count']))
        self.satniStatus.setPlainText(str(arg['status']))
###############################################################################
    def set_labele_minutne_tocke(self, arg):
        """
        Setter labela podataka za minutnu tocku. Prikazuju se podaci:
        vrijeme, koncentracija, status. Ista metoda se koristi za clear,
        samo se treba poslati set praznih stringova.

        ulazni parametar arg je dictionary sa vrjiednostima labela. Sve vrijednosti
        moraju biti stringovi!
        """
        self.minutniStatus.clear()
        self.minutniVrijeme.setText(str(arg['vrijeme']))
        self.minutniKoncentracija.setText(str(arg['koncentracija']))
        self.minutniStatus.setPlainText(str(arg['status']))
###############################################################################
###############################################################################
base3, form3 = uic.loadUiType('./app/view/ui_files/zero_span_panel.ui')
class ZeroSpanPanel(base3, form3):
    def __init__(self, konfig, parent = None):
        """
        inicijalizacija sa konfig objektom aplikacije
        """
        super(base3, self).__init__(parent)
        self.setupUi(self)
        self.konfig = konfig
        self.zoomStackZS = []
        self.initial_zoom_level = (None, None, None)

        #inicijalizacija canvasa (pomocni nisu potrebni)
        self.zeroGraf = canvas.ZeroKanvas(konfig.zero)
        self.spanGraf = canvas.SpanKanvas(konfig.span)
        #dodavanje canvasa u layout panela
        self.zeroLayout.addWidget(self.zeroGraf)
        self.spanLayout.addWidget(self.spanGraf)

        self.setup_icons()

        #povezivanje akcija widgeta sa funkcijama
        self.brojDana.currentIndexChanged.connect(self.promjeni_broj_dana)
        self.dodajZSRef.clicked.connect(self.dodaj_novu_zs_ref_vrijednost)

        self.zoomInZero.clicked.connect(self.zeroGraf.toggle_zoom)
        self.zoomOutZero.clicked.connect(self.zoom_out)
        self.zoomOutZeroFull.clicked.connect(self.full_zoom_out)
        self.toggleGridZero.clicked.connect(self.toggle_zero_grid)
        self.toggleLegendZero.clicked.connect(self.toggle_zero_legend)
        self.zoomInSpan.clicked.connect(self.spanGraf.toggle_zoom)
        self.zoomOutSpan.clicked.connect(self.zoom_out)
        self.zoomOutSpanFull.clicked.connect(self.full_zoom_out)
        self.toggleGridSpan.clicked.connect(self.toggle_span_grid)
        self.toggleLegendSpan.clicked.connect(self.toggle_span_legend)

        #inicijalno stanje check statusa kontrola
        self.toggleGridZero.setChecked(self.konfig.zero.Grid)
        self.toggleLegendZero.setChecked(self.konfig.zero.Legend)
        self.toggleGridSpan.setChecked(self.konfig.span.Grid)
        self.toggleLegendSpan.setChecked(self.konfig.span.Legend)

        #zoom sinhronizacija
        #ZERO
        self.connect(self.zeroGraf,
                     QtCore.SIGNAL('clear_zerospan_zoomstack'),
                     self.clear_zoomStackZS)
        self.connect(self.zeroGraf,
                     QtCore.SIGNAL('report_original_size(PyQt_PyObject)'),
                     self.postavi_initial_zoom_stack)
        self.connect(self.zeroGraf,
                     QtCore.SIGNAL('add_zoom_level(PyQt_PyObject)'),
                     self.add_zoom_level_to_stack)
        #SPAN
        self.connect(self.spanGraf,
                     QtCore.SIGNAL('clear_zerospan_zoomstack'),
                     self.clear_zoomStackZS)
        self.connect(self.spanGraf,
                     QtCore.SIGNAL('report_original_size(PyQt_PyObject)'),
                     self.postavi_initial_zoom_stack)
        self.connect(self.spanGraf,
                     QtCore.SIGNAL('add_zoom_level(PyQt_PyObject)'),
                     self.add_zoom_level_to_stack)
###############################################################################
    def zoom_out(self):
        """
        zoom out jedan level
        """
        if len(self.zoomStackZS) > 1:
            self.zoomStackZS.pop()
            x, yz, ys = self.zoomStackZS[-1]
            self.zeroGraf.postavi_novi_zoom_level(x, yz)
            self.spanGraf.postavi_novi_zoom_level(x, ys)
        else:
            self.full_zoom_out()
###############################################################################
    def full_zoom_out(self):
        """
        implementacija full zoom outa za zero i span graf
        """
        self.zoomStackZS.clear()
        x, yz, ys = self.initial_zoom_level
        self.zeroGraf.postavi_novi_zoom_level(x, yz)
        self.spanGraf.postavi_novi_zoom_level(x, ys)
###############################################################################
    def add_zoom_level_to_stack(self, mapa):
        """
        Dodavanje novog zoom levela na stack, pozivanje na reskaliranje grafa
        """
        if len(self.zoomStackZS):
            oldx, oldyzero, oldyspan = self.zoomStackZS[-1]
        else:
            oldx, oldyzero, oldyspan = self.initial_zoom_level

        newx = mapa['x']
        newy = mapa['y']
        if mapa['tip'] == 'ZERO':
            self.zoomStackZS.append((newx, newy, oldyspan))
            #zoom in za svaki graf
            self.zeroGraf.postavi_novi_zoom_level(newx, newy)
            self.spanGraf.postavi_novi_zoom_level(newx, oldyspan)
        elif mapa['tip'] == 'SPAN':
            self.zoomStackZS.append((newx, oldyzero, newy))
            #zoom in za svaki graf
            self.zeroGraf.postavi_novi_zoom_level(newx, oldyzero)
            self.spanGraf.postavi_novi_zoom_level(newx, newy)
###############################################################################
    def postavi_initial_zoom_stack(self, mapa):
        """
        setup inicijalnog zoom stacka....
        """
        oldx, oldyzero, oldyspan = self.initial_zoom_level
        if mapa['tip'] == 'ZERO':
            self.initial_zoom_level = (mapa['x'], mapa['y'], oldyspan)
        elif mapa['tip'] == 'SPAN':
            self.initial_zoom_level = (mapa['x'], oldyzero, mapa['y'])
        potpunost = True
        for i in self.initial_zoom_level:
            potpunost = potpunost and (i != None)
        if potpunost:
            self.zoomStackZS.append(self.initial_zoom_level)
###############################################################################
    def clear_zoomStackZS(self):
        """
        clear zajednickog zoom stacka za zero i span graf
        """
        self.zoomStackZS.clear()
###############################################################################
    def toggle_span_grid(self, x):
        """prosljeduje naredbu za toggle grida na satnom grafu"""
        self.konfig.span.set_grid(x)
        self.spanGraf.toggle_grid(x)
###############################################################################
    def toggle_span_legend(self, x):
        """prosljeduje naredbu za toggle legende na satnom grafu"""
        self.konfig.span.set_legend(x)
        self.spanGraf.toggle_legend(x)
###############################################################################
    def toggle_zero_grid(self, x):
        """prosljeduje naredbu za toggle grida na minutnom grafu"""
        self.konfig.zero.set_grid(x)
        self.zeroGraf.toggle_grid(x)
###############################################################################
    def toggle_zero_legend(self, x):
        """prosljeduje naredbu za toggle legende na minutnom grafu"""
        self.konfig.zero.set_legend(x)
        self.zeroGraf.toggle_legend(x)
###############################################################################
    def setup_icons(self):
        """postavljanje ikona u gumbe"""
        self.zoomInSpan.setIcon(QtGui.QIcon('./app/view/icons/zoomin.png'))
        self.zoomOutSpan.setIcon(QtGui.QIcon('./app/view/icons/zoomout.png'))
        self.zoomOutSpanFull.setIcon(QtGui.QIcon('./app/view/icons/zoomoutfull.png'))
        self.toggleGridSpan.setIcon(QtGui.QIcon('./app/view/icons/grid.png'))
        self.toggleLegendSpan.setIcon(QtGui.QIcon('./app/view/icons/listing.png'))
        self.zoomInZero.setIcon(QtGui.QIcon('./app/view/icons/zoomin.png'))
        self.zoomOutZero.setIcon(QtGui.QIcon('./app/view/icons/zoomout.png'))
        self.zoomOutZeroFull.setIcon(QtGui.QIcon('./app/view/icons/zoomoutfull.png'))
        self.toggleGridZero.setIcon(QtGui.QIcon('./app/view/icons/grid.png'))
        self.toggleLegendZero.setIcon(QtGui.QIcon('./app/view/icons/listing.png'))
###############################################################################
    def dodaj_novu_zs_ref_vrijednost(self):
        """
        Dodavanje nove referentne vrijednosti za zero/span
        """
        logging.info('Request za dodavanjem nove zero/span referentne vrijednosti')
        self.emit(QtCore.SIGNAL('dodaj_novu_referentnu_vrijednost'))
###############################################################################
    def change_glavniLabel(self, ulaz):
        """
        ova funkcija kao ulazni parametar uzima mapu koja ima 2 elementa.
        -'opis' = mapa, opis kanala (naziv, mjerna jedinica, postaja...)
        -'datum' = string, datum formata YYYY-MM-DD

        Informacija o izboru se postavlja u label.
        """
        mapa = ulaz['opis']
        mjerenjeId = ulaz['mjerenjeId']
        datum = ulaz['datum']
        postaja = mapa['postajaNaziv']
        komponenta = mapa['komponentaNaziv']
        formula = mapa['komponentaFormula']
        mjernaJedinica = mapa['komponentaMjernaJedinica']
        opis = '{0}, {1}( {2} ) [{3}]. Datum : {4} . mjerenjeId:{5}'.format(postaja, komponenta, formula, mjernaJedinica, datum, mjerenjeId)
        self.glavniLabel.setText(opis)
        logging.info('glavniLabel promjenjen, value = {0}'.format(opis))
###############################################################################
    def promjeni_broj_dana(self, x):
        """
        -funkcija koja se poziva promjenom broja dana u comboboxu
        -update defaulte, pozovi na ponovno crtanje grafa
        """
        broj = int(self.brojDana.itemText(x))
        logging.info('request za prikazom drugog broja dana, novi = {0}'.format(str(broj)))
        self.emit(QtCore.SIGNAL('update_zs_broj_dana(PyQt_PyObject)'), broj)
###############################################################################
    def prikazi_info_zero(self, mapa):
        """
        funkcija updatea labele sa informacijom o zero tocki koja je izabrana
        na grafu.

        mapa['xtocka'] = vrijeme
        mapa['ytocka'] = vrijednost
        mapa['minDozvoljenoOdstupanje'] = min dozvoljeno odstupanje
        mapa['maxDozvoljenoOdstupanje'] = max dozvoljeno odstupanje
        mapa['status'] = status
        """
        self.zeroVrijeme.setText(mapa['xtocka'])
        self.zeroValue.setText(mapa['ytocka'])
        self.zeroMinD.setText(mapa['minDozvoljenoOdstupanje'])
        self.zeroMaxD.setText(mapa['maxDozvoljenoOdstupanje'])
        self.zeroStatus.setText(mapa['status'])
###############################################################################
    def prikazi_info_span(self, mapa):
        """
        funkcija updatea labele sa informacijom o span tocki koja je izabrana
        na grafu

        mapa['xtocka'] = vrijeme
        mapa['ytocka'] = vrijednost
        mapa['minDozvoljenoOdstupanje'] = min dozvoljeno odstupanje
        mapa['maxDozvoljenoOdstupanje'] = max dozvoljeno odstupanje
        mapa['status'] = status
        """
        self.spanVrijeme.setText(mapa['xtocka'])
        self.spanValue.setText(mapa['ytocka'])
        self.spanMinD.setText(mapa['minDozvoljenoOdstupanje'])
        self.spanMaxD.setText(mapa['maxDozvoljenoOdstupanje'])
        self.spanStatus.setText(mapa['status'])
###############################################################################
###############################################################################
base14, form14 = uic.loadUiType('./app/view/ui_files/visednevni_prikaz.ui')
class RestPregledSatnih(base14, form14):
    """
    Klasa za pregled vise dana agregiranih podataka povucenih sa REST servisa
    """
    def __init__(self, konfig, parent=None):
        super(base14, self).__init__(parent)
        self.setupUi(self)
        self.gKanal = None # id glavnog kanala za prikaz
        self.konfig = konfig

        #set dateEdit na danasnji datum
        temp = QtCore.QDate.currentDate().addDays(-10)
        self.dateEditOd.setDate(temp)
        self.dateEditDo.setDate(QtCore.QDate.currentDate())

        self.setup_icons()

        self.satniRest = canvas.SatniRestKanvas(konfig.satniRest)
        self.grafLayout.addWidget(self.satniRest)

        self.buttonCrtaj.clicked.connect(self.get_podatke)
        self.zoomInRestSatni.clicked.connect(self.satniRest.toggle_zoom)
        self.zoomOutRestSatni.clicked.connect(self.satniRest.zoom_out)
        self.zoomOutRestSatniFull.clicked.connect(self.satniRest.zoom_out_full)
        self.toggleGridRestSatni.clicked.connect(self.toggle_grid_satniRest)
        self.toggleLegendRestSatni.clicked.connect(self.toggle_legend_satniRest)

        #init na pocetno stanje
        self.toggleGridRestSatni.setChecked(self.konfig.satniRest.Grid)
        self.toggleLegendRestSatni.setChecked(self.konfig.satniRest.Legend)

    def toggle_grid_satniRest(self, x):
        """prosljeduje naredbu za toggle grida na satnom grafu"""
        self.konfig.satniRest.set_grid(x)
        self.satniRest.toggle_grid(x)

    def toggle_legend_satniRest(self, x):
        """prosljeduje naredbu za toggle legende na satnom grafu"""
        self.konfig.satniRest.set_legend(x)
        self.satniRest.toggle_legend(x)

    def setup_icons(self):
        """setup ikona za gumbe"""
        self.zoomInRestSatni.setIcon(QtGui.QIcon('./app/view/icons/zoomin.png'))
        self.zoomOutRestSatni.setIcon(QtGui.QIcon('./app/view/icons/zoomout.png'))
        self.zoomOutRestSatniFull.setIcon(QtGui.QIcon('./app/view/icons/zoomoutfull.png'))
        self.toggleGridRestSatni.setIcon(QtGui.QIcon('./app/view/icons/grid.png'))
        self.toggleLegendRestSatni.setIcon(QtGui.QIcon('./app/view/icons/listing.png'))


    def change_glavniLabel(self, ulaz):
        """
        Metoda postavlja opisni label na graf

        ulaz je mapa sa opisom kanala(naziv, mjerna jedinica...)
        """
        mapa = ulaz['opis']
        mjerenjeId = ulaz['mjerenjeId']
        postaja = mapa['postajaNaziv']
        komponenta = mapa['komponentaNaziv']
        formula = mapa['komponentaFormula']
        mjernaJedinica = mapa['komponentaMjernaJedinica']
        opis = '{0}, {1}( {2} ) [{3}]. mjerenjeId:{4}'.format(postaja, komponenta, formula, mjernaJedinica, mjerenjeId)
        self.glavniLabel.setText(opis)

    def set_gKanal(self, mapa):
        """
        Setter za glavni kanal
        mapa:
        {'programMjerenjaId':int, 'datumString':'YYYY-MM-DD'}
        """
        noviKanal = mapa['programMjerenjaId']
        if self.gKanal != noviKanal:
            self.gKanal = noviKanal

    def adapt_datum(self, datum):
        """
        Convert QDate objekt u pravilno formatiran string "YYYY-MM-DDThh:mm:ss"
        """
        dat = datum.toPyDate()
        dat = dat + datetime.timedelta(days=1)
        dat = dat.strftime('%Y-%m-%dT%H:%M:%S')
        return dat

    def get_podatke(self):
        """slanje requesta za crtanjem REST satnih podataka"""
        if self.gKanal is not None:
            datumOd = self.adapt_datum(self.dateEditOd.date())
            datumDo = self.adapt_datum(self.dateEditDo.date())
            valjani = self.checkSamoValjani.isChecked()
            nivoValidacije = self.spinNivoValidacije.value()
            output = {'datumOd': datumOd,
                      'datumDo': datumDo,
                      'kanal': self.gKanal,
                      'valjani': valjani,
                      'validacija': nivoValidacije}
            self.emit(QtCore.SIGNAL('nacrtaj_rest_satne(PyQt_PyObject)'), output)
        else:
            QtGui.QMessageBox.information(self, 'Problem kod crtanja', 'Nije moguce nacrtati graf, kanal nije izabran')

    def prikazi_info_satni_rest(self, mapa):
        """
        Funkcija updatea labele sa informacijom o izabranoj tocki sa grafa satno
        agregiranih vrijednosti direktno preuzetih sa REST servisa.

        mapa['vrijeme'] = vrijeme
        mapa['average'] = vrijednost
        mapa['status'] = status
        mapa['obuhvat'] = obuhvat
        """
        self.labelVrijeme.setText(str(mapa['vrijeme']))
        self.labelAverage.setText(str(mapa['average']))
        self.labelObuhvat.setText(str(mapa['obuhvat']))
        self.plainTextEditStatus.setPlainText(str(mapa['status']))