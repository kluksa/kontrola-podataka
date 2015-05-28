#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 14:20:39 2014

@author: User

"""
import logging
from PyQt4 import QtCore, QtGui, uic

import app.view.rest_izbornik as rest_izbornik
import app.view.grafovi_panel as grafovi_panel
import app.general.app_dto as app_dto
import app.control.kontroler as kontroler
import app.view.auth_login as auth_login
import app.view.glavni_dijalog as glavni_dijalog
###############################################################################
###############################################################################
base, form = uic.loadUiType('./app/view/ui_files/display.ui')
class GlavniProzor(base, form):
    def __init__(self, cfg = None, parent = None):
        super(base, self).__init__(parent)
        self.setupUi(self)

        self.config = cfg

        #set up inicijalizaciju
        self.setup_main_window()

        """
        Todo... treba srediti toggle tickova grida isl do kraja
        """
###############################################################################
    def setup_main_window(self):
        """
        setup glavnog prozora koristeci podatke iz self.config
        """
        #inicijalizacija konfiguracijskog objekta
        self.konfiguracija = app_dto.KonfigAplikacije(self.config)

        #set state chekcable akcija
        #satni
        self.action_satni_grid.setChecked(self.konfiguracija.satni.Grid)
        self.action_satni_cursor.setChecked(self.konfiguracija.satni.Cursor)
        self.action_satni_minor_ticks.setChecked(self.konfiguracija.satni.Ticks)
        self.action_satni_legend.setChecked(self.konfiguracija.satni.Legend)
        #minutni
        self.action_minutni_grid.setChecked(self.konfiguracija.minutni.Grid)
        self.action_minutni_cursor.setChecked(self.konfiguracija.minutni.Cursor)
        self.action_minutni_minor_ticks.setChecked(self.konfiguracija.minutni.Ticks)
        self.action_minutni_legend.setChecked(self.konfiguracija.minutni.Legend)
        #zero
        self.action_ZERO_grid.setChecked(self.konfiguracija.zero.Grid)
        self.action_ZERO_cursor.setChecked(self.konfiguracija.zero.Cursor)
        self.action_ZERO_minor_ticks.setChecked(self.konfiguracija.zero.Ticks)
        self.action_ZERO_legend.setChecked(self.konfiguracija.zero.Legend)
        #span
        self.action_SPAN_grid.setChecked(self.konfiguracija.span.Grid)
        self.action_SPAN_cursor.setChecked(self.konfiguracija.span.Cursor)
        self.action_SPAN_minor_ticks.setChecked(self.konfiguracija.span.Ticks)
        self.action_SPAN_legend.setChecked(self.konfiguracija.span.Legend)
        #satniRest
        self.action_rest_satni_grid.setChecked(self.konfiguracija.satniRest.Grid)
        self.action_rest_satni_cursor.setChecked(self.konfiguracija.satniRest.Cursor)
        self.action_rest_satni_minor_ticks.setChecked(self.konfiguracija.satniRest.Ticks)
        self.action_rest_satni_legend.setChecked(self.konfiguracija.satniRest.Legend)

        #inicijalizacija panela sa grafovima koncentracije
        self.koncPanel = grafovi_panel.KoncPanel(self.konfiguracija)
        self.koncPanelLayout.addWidget(self.koncPanel)

        #inicijalizacija panela sa zero/span grafovima
        self.zsPanel = grafovi_panel.ZeroSpanPanel(self.konfiguracija)
        self.zsPanelLayout.addWidget(self.zsPanel)

        #inicijalizacija panela za pregled agregiranih (visednevni)
        self.visednevniPanel = grafovi_panel.RestPregledSatnih(self.konfiguracija)
        self.visednevniLayout.addWidget(self.visednevniPanel)

        #inicijalizacija i postavljanje kontrolnog widgeta (tree view/kalendar...)
        self.restIzbornik = rest_izbornik.RestIzbornik()
        self.dockWidget.setWidget(self.restIzbornik)

        #toggle koji je gumb u rest izborniku aktivan (ovisno o aktivnom tabu)
        ind = self.tabWidget.currentIndex()

        #setup icons
        self.setup_ikone()

        #definiranje signala gui elemenata
        self.setup_signals()

        #na kraju inicijalizacije stavi inicijalizaciju kontorlora u event loop
        QtCore.QTimer.singleShot(0, self.setup_kontroler)
###############################################################################
    def promjeniTabRef(self, x):
        """
        promjena tab, koji je od panela trenutno prikazan na ekranu.
        """
        #emit promjene aktivnog taba
        self.emit(QtCore.SIGNAL('promjena_aktivnog_taba(PyQt_PyObject)'), x)
###############################################################################
    def setup_ikone(self):
        """
        Postavljanje ikona za definirane QAkcije (toolbar/menubar...)
        """
        self.action_exit.setIcon(QtGui.QIcon('./app/view/icons/close19.png'))
        self.action_log_in.setIcon(QtGui.QIcon('./app/view/icons/enter3.png'))
        self.action_log_out.setIcon(QtGui.QIcon('./app/view/icons/door9.png'))
        self.action_reconnect.setIcon(QtGui.QIcon('./app/view/icons/cogwheel9.png'))
        self.action_stil_grafova.setIcon(QtGui.QIcon('./app/view/icons/bars7.png'))
###############################################################################
    def setup_signals(self):
        """
        Metoda difinira signale koje emitiraju dijelovi sucelja prema kontrolnom
        elementu.
        """
        self.tabWidget.currentChanged.connect(self.promjeniTabRef)
        self.action_exit.triggered.connect(self.close)
        self.action_log_in.triggered.connect(self.request_log_in)
        self.action_log_out.triggered.connect(self.request_log_out)
        self.action_reconnect.triggered.connect(self.request_reconnect)
        self.action_satni_grid.triggered.connect(self.request_satni_grid_toggle)
        self.action_satni_cursor.triggered.connect(self.request_satni_cursor_toggle)
        self.action_satni_minor_ticks.triggered.connect(self.request_satni_ticks_toggle)
        self.action_satni_legend.triggered.connect(self.request_satni_legend_toggle)
        self.action_minutni_grid.triggered.connect(self.request_minutni_grid_toggle)
        self.action_minutni_cursor.triggered.connect(self.request_minutni_cursor_toggle)
        self.action_minutni_minor_ticks.triggered.connect(self.request_minutni_ticks_toggle)
        self.action_minutni_legend.triggered.connect(self.request_minutni_legend_toggle)
        self.action_stil_grafova.triggered.connect(self.promjeni_stil_grafova)
        self.action_ZERO_grid.triggered.connect(self.request_zero_grid_toggle)
        self.action_ZERO_cursor.triggered.connect(self.request_zero_cursor_toggle)
        self.action_ZERO_minor_ticks.triggered.connect(self.request_zero_ticks_toggle)
        self.action_ZERO_legend.triggered.connect(self.request_zero_legend_toggle)
        self.action_SPAN_grid.triggered.connect(self.request_span_grid_toggle)
        self.action_SPAN_cursor.triggered.connect(self.request_span_cursor_toggle)
        self.action_SPAN_minor_ticks.triggered.connect(self.request_span_ticks_toggle)
        self.action_SPAN_legend.triggered.connect(self.request_span_legend_toggle)
        self.action_rest_satni_grid.triggered.connect(self.request_rest_satni_grid_toggle)
        self.action_rest_satni_cursor.triggered.connect(self.request_rest_satni_cursor_toggle)
        self.action_rest_satni_minor_ticks.triggered.connect(self.request_rest_satni_ticks_toggle)
        self.action_rest_satni_legend.triggered.connect(self.request_rest_satni_legend_toggle)
###############################################################################
    def closeEvent(self, event):
        """
        Overloadani signal za gasenje aplikacije. Dodatna potvrda za izlaz.
        """
        saveState = self.exit_check()
        if not saveState:
            reply=QtGui.QMessageBox.question(
                self,
                'Potvrdi izlaz:',
                'Da li ste sigurni da hocete ugasiti aplikaciju?\nNeki podaci nisu spremljeni na REST servis.',
                QtGui.QMessageBox.Yes,
                QtGui.QMessageBox.No)

            if reply==QtGui.QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            #izlaz iz aplikacije bez dodatnog pitanja.
            event.accept()
###############################################################################
    def exit_check(self):
        """
        Funkcija sluzi za provjeru spremljenog rada prije izlaska iz aplikacije.

        provjerava za svaki ucitani glavni kanal, datume ucitanih i datume
        uspjesno spremljenih na REST.

        Funkcija vraca boolean ovisno o jednakosti skupova datuma.

        poziva ga glavniprozor.py - u overloadanoj metodi za izlaz iz aplikacije
        """
        out = True #default je sve u redu
        for kanal in self.kontrola.setGlavnihKanala:
            if kanal in self.kontrola.kalendarStatus:
                if set(self.kontrola.kalendarStatus[kanal]['ok']) == set(self.kontrola.kalendarStatus[kanal]['bad']):
                    out = out and True
                else:
                    out = out and False
        #return rezultat (upozori da neki podaci NISU spremljeni na REST)
        return out
###############################################################################
    def promjeni_stil_grafova(self):
        opis = self.kontrola.mapaMjerenjeIdToOpis
        drvo = self.kontrola.modelProgramaMjerenja
        if opis is not None and drvo is not None:
            logging.info('Pozvan dijalog za promjenu stila grafova')
            dijalog = glavni_dijalog.GlavniIzbor(defaulti = self.konfiguracija, opiskanala = opis, stablo = drvo, parent = self)

            #connect apply gumb
            self.connect(dijalog,
                         QtCore.SIGNAL('apply_promjene_izgleda'),
                         self.naredi_promjenu_izgleda_grafova)

            if dijalog.exec_():
                logging.debug('Dialog za stil closed, accepted')
                self.naredi_promjenu_izgleda_grafova()
            else:
                logging.debug('Dialog za stil closed')
                self.naredi_promjenu_izgleda_grafova()

            #disconnect apply gumb
            self.disconnect(dijalog,
                            QtCore.SIGNAL('apply_promjene_izgleda'),
                            self.naredi_promjenu_izgleda_grafova)

        else:
            QtGui.QMessageBox.information(self, 'Problem:', 'Nije moguce pokrenuti dijalog.\nProvjeri da li su programi mjerenja uspjesno ucitani.')
            logging.debug('Nije moguce inicijalizirati dijalog za stil grafova, nedostaje model mjerenja')
###############################################################################
    def naredi_promjenu_izgleda_grafova(self):
        """
        emitiraj zahtjev prema kontorlolu za update izgleda grafova
        """
        self.emit(QtCore.SIGNAL('apply_promjena_izgleda_grafova'))
###############################################################################
    def request_log_in(self):
        """
        - prikazi dijalog za unos korisnickog imena i lozinke
        - enable/disable odredjene akcije
        - emitiraj signal sa tuple objektom (korisnicko ime, sifra)
        """
        dijalog = auth_login.DijalogLoginAuth()
        if dijalog.exec_():
            info = dijalog.vrati_postavke()
            logging.info('User logged in. User = {0}'.format(info[0]))
            #disable log in action, enable log out action
            self.action_log_in.setEnabled(False)
            self.action_log_out.setEnabled(True)
            self.emit(QtCore.SIGNAL('user_log_in(PyQt_PyObject)'), info)
###############################################################################
    def request_log_out(self):
        """
        - prikazi dijalog za potvrdu log outa
        - enable/diable odredjene akcije
        - emitiraj signal za log out
        """
        dijalog = QtGui.QMessageBox.question(self,
                                             'Log out:',
                                             'Potvrdi log out.',
                                             QtGui.QMessageBox.Yes,
                                             QtGui.QMessageBox.No)
        if dijalog == QtGui.QMessageBox.Yes:
            logging.info('User logged out.')
            self.action_log_in.setEnabled(True)
            self.action_log_out.setEnabled(False)
            self.emit(QtCore.SIGNAL('user_log_out'))
###############################################################################
    def request_reconnect(self):
        """
        metoda emitira request za reconnect proceduru
        """
        self.emit(QtCore.SIGNAL('reconnect_to_REST'))
###############################################################################
    def request_rest_satni_grid_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.konfiguracija.satniRest.set_grid(x)
        self.visednevniPanel.satniRest.toggle_grid(x)
###############################################################################
    def request_rest_satni_cursor_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.konfiguracija.satniRest.set_cursor(x)
        self.visednevniPanel.satniRest.toggle_cursor(self.konfiguracija.satniRest.Cursor)
###############################################################################
    def request_rest_satni_ticks_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.konfiguracija.satniRest.set_ticks(x)
        self.visednevniPanel.satniRest.toggle_ticks(x)
###############################################################################
    def request_rest_satni_legend_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.konfiguracija.satniRest.set_legend(x)
        self.visednevniPanel.satniRest.toggle_legend(x)
###############################################################################
    def request_satni_grid_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.konfiguracija.satni.set_grid(x)
        self.koncPanel.satniGraf.toggle_grid(x)
###############################################################################
    def request_satni_cursor_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.konfiguracija.satni.set_cursor(x)
        self.koncPanel.satniGraf.toggle_cursor(self.konfiguracija.satni.Cursor)
###############################################################################
    def request_satni_ticks_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.konfiguracija.satni.set_ticks(x)
        self.koncPanel.satniGraf.toggle_ticks(x)
###############################################################################
    def request_satni_legend_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.konfiguracija.satni.set_legend(x)
        self.koncPanel.satniGraf.toggle_legend(x)
###############################################################################
    def request_minutni_grid_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.konfiguracija.minutni.set_grid(x)
        self.koncPanel.minutniGraf.toggle_grid(x)
###############################################################################
    def request_minutni_cursor_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.konfiguracija.minutni.set_cursor(x)
        self.koncPanel.minutniGraf.toggle_cursor(self.konfiguracija.minutni.Cursor)
###############################################################################
    def request_minutni_ticks_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.konfiguracija.minutni.set_ticks(x)
        self.koncPanel.minutniGraf.toggle_ticks(x)
###############################################################################
    def request_minutni_legend_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.konfiguracija.minutni.set_legend(x)
        self.koncPanel.minutniGraf.toggle_legend(x)
###############################################################################
    def request_zero_grid_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.konfiguracija.zero.set_grid(x)
        self.zsPanel.zeroGraf.toggle_grid(x)
###############################################################################
    def request_zero_cursor_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.konfiguracija.zero.set_cursor(x)
        self.zsPanel.zeroGraf.toggle_cursor(self.konfiguracija.zero.Cursor)
###############################################################################
    def request_zero_ticks_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.konfiguracija.zero.set_ticks(x)
        self.zsPanel.zeroGraf.toggle_ticks(x)
###############################################################################
    def request_zero_legend_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.konfiguracija.zero.set_legend(x)
        self.zsPanel.zeroGraf.toggle_legend(x)
###############################################################################
    def request_span_grid_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.konfiguracija.span.set_grid(x)
        self.zsPanel.spanGraf.toggle_grid(x)
###############################################################################
    def request_span_cursor_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.konfiguracija.span.set_cursor(x)
        self.zsPanel.spanGraf.toggle_cursor(self.konfiguracija.span.Cursor)
###############################################################################
    def request_span_ticks_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.konfiguracija.span.set_ticks(x)
        self.zsPanel.spanGraf.toggle_ticks(x)
###############################################################################
    def request_span_legend_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.konfiguracija.span.set_legend(x)
        self.zsPanel.spanGraf.toggle_legend(x)
###############################################################################
    def setup_kontroler(self):
        """
        Metoda inicijalizira kontroler dio aplikacije.
        """
        self.kontrola = kontroler.Kontroler(parent = None, gui = self)
###############################################################################
###############################################################################
