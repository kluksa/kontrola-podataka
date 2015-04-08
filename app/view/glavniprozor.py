#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 14:20:39 2014

@author: User

"""
import logging

from PyQt4 import QtCore, QtGui, uic

from app.view import rest_izbornik, glavni_dijalog, grafovi_panel
import app_dto
import kontroler
import auth_login



###############################################################################
###############################################################################
base, form = uic.loadUiType('./ui_files/display.ui')
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
        #inicijaliuacija app dto objekta uz pomoc config filea
        self.appSettings = app_dto.AppSettingsDTO(self.config)
        #inicijalizacija graf dto objekata uz pomoc config filea
        self.grafSettings = app_dto.GrafSettingsDTO(self.config)

        #set state chekcable akcija
        self.action_satni_grid.setChecked(self.appSettings.satniGrid)
        self.action_satni_cursor.setChecked(self.appSettings.satniCursor)
        self.action_satni_minor_ticks.setChecked(self.appSettings.satniTicks)
        self.action_satni_span_selector.setChecked(self.appSettings.satniSelector)
        self.action_satni_legend.setChecked(self.appSettings.satniLegend)
        self.action_minutni_grid.setChecked(self.appSettings.minutniGrid)
        self.action_minutni_cursor.setChecked(self.appSettings.minutniCursor)
        self.action_minutni_minor_ticks.setChecked(self.appSettings.minutniTicks)
        self.action_minutni_span_selector.setChecked(self.appSettings.minutniSelector)
        self.action_minutni_legend.setChecked(self.appSettings.minutniLegend)
        self.action_zoom.setChecked(self.appSettings.zoom)

        #inicijalizacija panela sa grafovima koncentracije
        self.koncPanel = grafovi_panel.KoncPanel(self.grafSettings, self.appSettings)
        self.koncPanelLayout.addWidget(self.koncPanel)
        #inicijalizacija panela sa zero/span grafovima
        self.zsPanel = grafovi_panel.ZeroSpanPanel(self.grafSettings, self.appSettings)
        self.zsPanelLayout.addWidget(self.zsPanel)
        #inicijalizacija i postavljanje kontrolnog widgeta (tree view/kalendar...)
        self.restIzbornik = rest_izbornik.RestIzbornik()
        self.dockWidget.setWidget(self.restIzbornik)

        #toggle koji je gumb u rest izborniku aktivan (ovisno o aktivnom tabu)
        ind = self.tabWidget.currentIndex()
        self.toggle_upload_buttons(ind)

        #setup stanja grafova (ticks, grid, span, zoom....)
        self.koncPanel.satniGraf.set_interaction_mode(self.appSettings.zoom, self.appSettings.satniCursor, self.appSettings.satniSelector, "SATNI")
        self.koncPanel.minutniGraf.set_interaction_mode(self.appSettings.zoom, self.appSettings.minutniCursor, self.appSettings.minutniSelector, "MINUTNI")
        self.zsPanel.zeroGraf.set_interaction_mode(self.appSettings.zoom, False, False, "SPAN")
        self.zsPanel.spanGraf.set_interaction_mode(self.appSettings.zoom, False, False, "ZERO")

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
        #enable/disable gumbe na rest izborniku
        self.toggle_upload_buttons(x)
        #emit promjene aktivnog taba
        self.emit(QtCore.SIGNAL('tab_promjenjen(PyQt_PyObject)'), x)
###############################################################################
    def toggle_upload_buttons(self, x):
        """
        enable/disable toggle za gumbe na restIzborniku.
        Kada je aktivan tab sa koncentracijskim grafovima
            -upload agregiranih je enabled
            -dodavanje zero span ref vrijednosti je disabled
        Kada je aktivan tab sa zero/span grafovima situacija je obrnuta.
        """
        if x == 0:
            self.restIzbornik.uploadAgregirane.setEnabled(True)
        elif x == 1:
            self.restIzbornik.uploadAgregirane.setEnabled(False)
###############################################################################
    def setup_ikone(self):
        """
        Postavljanje ikona za definirane QAkcije (toolbar/menubar...)
        """
        self.action_exit.setIcon(QtGui.QIcon('./icons/close19.png'))
        self.action_log_in.setIcon(QtGui.QIcon('./icons/enter3.png'))
        self.action_log_out.setIcon(QtGui.QIcon('./icons/door9.png'))
        self.action_reconnect.setIcon(QtGui.QIcon('./icons/cogwheel9.png'))
        self.action_zoom.setIcon(QtGui.QIcon('./icons/zoom24.png'))
        self.action_zoom_out.setIcon(QtGui.QIcon('./icons/zoom25.png'))
        self.action_stil_grafova.setIcon(QtGui.QIcon('./icons/bars7.png'))
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
        self.action_satni_span_selector.triggered.connect(self.request_satni_span_toggle)
        self.action_satni_legend.triggered.connect(self.request_satni_legend_toggle)
        self.action_minutni_grid.triggered.connect(self.request_minutni_grid_toggle)
        self.action_minutni_cursor.triggered.connect(self.request_minutni_cursor_toggle)
        self.action_minutni_minor_ticks.triggered.connect(self.request_minutni_ticks_toggle)
        self.action_minutni_span_selector.triggered.connect(self.request_minutni_span_toggle)
        self.action_minutni_legend.triggered.connect(self.request_minutni_legend_toggle)
        self.action_zoom.triggered.connect(self.zoom_toggle)
        self.action_zoom_out.triggered.connect(self.zoom_out)
        self.action_stil_grafova.triggered.connect(self.promjeni_stil_grafova)
###############################################################################
    def closeEvent(self, event):
        """
        Overloadani signal za gasenje aplikacije. Dodatna potvrda za izlaz.
        """
        saveState = self.kontrola.exit_check()
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
    def promjeni_stil_grafova(self):
        opis = self.kontrola.mapaMjerenjeIdToOpis
        drvo = self.kontrola.modelProgramaMjerenja
        if opis != None and drvo != None:
            logging.info('Pozvan dijalog za promjenu stila grafova')
            dijalog = glavni_dijalog.GlavniIzbor(defaulti = self.grafSettings, opiskanala = opis, stablo = drvo, parent = self)

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
        self.emit(QtCore.SIGNAL('izgled_grafa_promjenjen'))
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
            self.emit(QtCore.SIGNAL('request_log_in(PyQt_PyObject)'), info)
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
            self.emit(QtCore.SIGNAL('request_log_out'))
###############################################################################
    def request_reconnect(self):
        """
        metoda emitira request za reconnect proceduru
        """
        self.emit(QtCore.SIGNAL('request_reconnect'))
###############################################################################
    def request_satni_grid_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.appSettings.set_satniGrid(x)
        self.koncPanel.satniGraf.toggle_grid(x)
###############################################################################
    def request_satni_cursor_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.appSettings.set_satniCursor(x)
        self.koncPanel.satniGraf.set_interaction_mode(self.appSettings.zoom, self.appSettings.satniCursor, self.appSettings.satniSelector, "SATNI")
###############################################################################
    def request_satni_ticks_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.appSettings.set_satniTicks(x)
        self.koncPanel.satniGraf.toggle_ticks(x)
###############################################################################
    def request_satni_span_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.appSettings.set_satniSelector(x)
        self.koncPanel.satniGraf.set_interaction_mode(self.appSettings.zoom, self.appSettings.satniCursor, self.appSettings.satniSelector, "SATNI")
###############################################################################
    def request_satni_legend_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.appSettings.set_satniLegend(x)
        self.koncPanel.satniGraf.toggle_legend(x)
###############################################################################
    def request_minutni_grid_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.appSettings.set_minutniGrid(x)
        self.koncPanel.minutniGraf.toggle_grid()
###############################################################################
    def request_minutni_cursor_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.appSettings.set_minutniCursor(x)
        self.koncPanel.minutniGraf.set_interaction_mode(self.appSettings.zoom, self.appSettings.minutniCursor, self.appSettings.minutniSelector, "MINUTNI")
###############################################################################
    def request_minutni_ticks_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.appSettings.set_minutniTicks(x)
        self.koncPanel.minutniGraf.toggle_ticks(x)
###############################################################################
    def request_minutni_span_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.appSettings.set_minutniSelector(x)
        self.koncPanel.minutniGraf.set_interaction_mode(self.appSettings.zoom, self.appSettings.minutniCursor, self.appSettings.minutniSelector, "MINUTNI")
###############################################################################
    def request_minutni_legend_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.appSettings.set_minutniLegend(x)
        self.koncPanel.minutniGraf.toggle_legend(x)
###############################################################################
    def zoom_toggle(self, x):
        """callback, spaja klik akcije sa promjenom u appSettings objektu"""
        self.appSettings.set_zoom(x)
        self.koncPanel.satniGraf.set_interaction_mode(self.appSettings.zoom, self.appSettings.satniCursor, self.appSettings.satniSelector, "SATNI")
        self.koncPanel.minutniGraf.set_interaction_mode(self.appSettings.zoom, self.appSettings.minutniCursor, self.appSettings.minutniSelector, "MINUTNI")
        #zs
        self.zsPanel.zeroGraf.set_interaction_mode(self.appSettings.zoom, False, False, "ZERO")
        self.zsPanel.spanGraf.set_interaction_mode(self.appSettings.zoom, False, False, "SPAN")
###############################################################################
    def zoom_out(self):
        """
        Prosljedjuje naredbu kontrolnom elementu da napravi full zoom out
        na svim grafovima
        """
        self.koncPanel.satniGraf.full_zoom_out()
        self.koncPanel.minutniGraf.full_zoom_out()
        self.zsPanel.spanGraf.full_zoom_out()
        self.zsPanel.zeroGraf.full_zoom_out()
###############################################################################
    def setup_kontroler(self):
        """
        Metoda inicijalizira kontroler dio aplikacije.
        """
        self.kontrola = kontroler.Kontroler(parent = None, gui = self)
###############################################################################
###############################################################################



