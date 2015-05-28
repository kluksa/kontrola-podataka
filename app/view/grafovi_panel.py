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
    Klasa za prikaz grafova
    Sadrzaj ovog panela je sljedeci (kako se prikazuje odozgo prema dolje):

    1. self.glavniLabel
        -QLabel koji sluzi za prikaz trenutno aktivnog kanala
        (stanica, formula, kanal, mjerna jedinica...)

    2. self.verticalLayoutSatni
        -placeholder definiran u QtDesigneru (layout)
        -sluzi da se u njega stavi satni canvas

    3. self.horizontalLayout
        -horiznotalni layout koji sadrzi 3 elementa
        2.1. self.buttonPrethodni
            -QPushButton koji sluzi za prebacivanje dana na prethodni dan
        2.2. self.satLabel
            -QLabel koji sluzi za prikaz naziva glavnog kanala i vremenkog intervala
        2.3. self.buttonSljedeci
            -QPushButton koji slizi za prebacivanje dana na sljedeci dan

    4. self.verticalLayoutMinutni
        -placeholder definiran u QtDesigneru (QWidget)
        -sluzi da se u njega stavi minutni canvas



    self.satniGraf --> instanca satnog canvasa
    self.minutniGraf --> instanca minutnog canvasa
    """
    def __init__(self, konfig, parent = None):
        """
        za inicijalizaciju panela potreban je konfig objekt aplikacije (konfig)
        """
        super(base2, self).__init__(parent)
        self.setupUi(self)

        #inicijalizacija canvasa (samo sa djelom konfiga koji je potreban za
        #funkcioniranje klase i sa mapom pomocnih kanala)
        self.satniGraf = canvas.SatniKanvas(konfig.satni, konfig.dictPomocnih)
        self.minutniGraf = canvas.MinutniKanvas(konfig.minutni, konfig.dictPomocnih)

        #dodavanje canvasa u layout panela
        self.verticalLayoutSatni.addWidget(self.satniGraf)
        self.verticalLayoutMinutni.addWidget(self.minutniGraf)

        #gumbi zaduzeni za prebacivanje dana naprijed i nazad
        self.buttonSljedeci.clicked.connect(self.prebaci_dan_naprijed)
        self.buttonPrethodni.clicked.connect(self.prebaci_dan_nazad)
        self.buttonPonisti.clicked.connect(self.ponisti_promjene)
        self.buttonRestSave.clicked.connect(self.save_na_rest)
        self.brojDanaCombo.currentIndexChanged.connect(self.promjeni_broj_dana)
        self.zoomOutSatni.clicked.connect(self.satniGraf.zoom_out)
        self.zoomOutMinutni.clicked.connect(self.minutniGraf.zoom_out)
###############################################################################
    def ponisti_promjene(self):
        """emitiraj signal kontroleru da 'ponisti' promjene za trenutni dan i postaju"""
        self.emit(QtCore.SIGNAL('ponisti_izmjene'))
###############################################################################
    def save_na_rest(self):
        """emitiraj signal kontroleru da spremi podatke za trenutni dan i postaju na
        rest servis"""
        self.emit(QtCore.SIGNAL('upload_minutne_na_REST'))
###############################################################################
    def promjeni_broj_dana(self, x):
        """
        emitiraj signal za promjenu broja dana za prikaz
        """
        value = int(self.brojDanaCombo.currentText())
        self.emit(QtCore.SIGNAL('promjeni_max_broj_dana_satnog(PyQt_PyObject)'), value)
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
        #inicijalizacija canvasa (pomocni nisu potrebni)
        self.zeroGraf = canvas.ZeroKanvas(konfig.zero)
        self.spanGraf = canvas.SpanKanvas(konfig.span)
        #dodavanje canvasa u layout panela
        self.zeroLayout.addWidget(self.zeroGraf)
        self.spanLayout.addWidget(self.spanGraf)

        #povezivanje akcija widgeta sa funkcijama
        self.brojDana.currentIndexChanged.connect(self.promjeni_broj_dana)
        self.dodajZSRef.clicked.connect(self.dodaj_novu_zs_ref_vrijednost)
        self.zoomOutZero.clicked.connect(self.zeroGraf.zoom_out)
        self.zoomOutSpan.clicked.connect(self.spanGraf.zoom_out)
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

        #set dateEdit na danasnji datum
        temp = QtCore.QDate.currentDate().addDays(-10)
        self.dateEditOd.setDate(temp)
        self.dateEditDo.setDate(QtCore.QDate.currentDate())

        self.satniRest = canvas.SatniRestKanvas(konfig.satniRest)
        self.grafLayout.addWidget(self.satniRest)

        self.buttonCrtaj.clicked.connect(self.get_podatke)
        self.zoomOutRestSatni.clicked.connect(self.satniRest.zoom_out)

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