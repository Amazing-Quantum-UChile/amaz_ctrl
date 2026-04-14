#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Created on the Sat Mar 28 2026 by Victor
# Copyright (c) 2026 - AmazingQuantum@UChile
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
# ---------------------------------------------------------------------------

"""
Content of mainwindow.py

Access to model using self._model and the main widget doing self._main_widget
"""

import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.Qt as Qt
import sys

from amaz_ctrl.gui.views.dialogs.help import HelpDialog
from amaz_ctrl.gui.views.dialogs.about import AboutDialog


class MainWindow(QtWidgets.QMainWindow):
    geometry = (3, 3, 1550, 900)
    title= "Quantum Light Controller"
    def __init__(self, model, main_widget_type):
        super().__init__()
        self._model = model
        ## we are passing a class as an argument and we will build the object later (in the _setup_main_widget method)
        self._main_widget_type = main_widget_type
        self._main_widget = None #for now
        self._actions = {}
        self._initialize_ui()
        self.log = self._model.log

        # This magic timer is used to handel SIGINT cleanly. See
        # below.

        # self._model.start_threads()

    def _initialize_ui(self):
        self._setup_main_widget()
        self._setup_actions()

        self.statusBar()
        self._setup_menubar()

        self.setGeometry(*self.geometry)
        self.setWindowTitle(self.title)
        self.show()

    def _setup_main_widget(self):
        self._main_widget = self._main_widget_type(self, self._model)
        self.setCentralWidget(self._main_widget)
    

    def _setup_actions(self):
        """method that connects action (i.e. kehyboard shortcut, pressed button) to other methods."""
        ## --  Action exit
        action_exit = QtWidgets.QAction("Quit", self)
        action_exit.setShortcut("Ctrl+Q")
        action_exit.setStatusTip("Exit Application")
        action_exit.triggered.connect(self.close)
        self._actions["exit"] = action_exit
        
        ## --  Action Save
        action_save = QtWidgets.QAction("Save", self)
        action_save.setShortcut("Ctrl+S")
        action_save.setStatusTip("Save config")
        action_save.triggered.connect(self._save)
        self._actions["save"] = action_save

        ## --  Action Reset Plot data
        action_reset_plots = QtWidgets.QAction("Reset Plot data", self)
        action_reset_plots.setShortcut("Ctrl+R")
        action_reset_plots.setStatusTip("Reset Plot data")
        action_reset_plots.triggered.connect(self._reset_plot_data)
        self._actions["reset plots"] = action_reset_plots

        ## --  Action About
        action_about = QtWidgets.QAction("About", self)
        action_about.setStatusTip(
            "About the app")
        action_about.triggered.connect(self._on_about)
        self._actions["about"] = action_about

        ## --  Action Help
        action_help = QtWidgets.QAction("Help", self)
        action_help.setStatusTip(
            "Help")
        action_help.setShortcut("Ctrl+H")
        action_help.triggered.connect(self._on_help)
        self._actions["help"] = action_help

        
    def _setup_menubar(self):
        if sys.platform == "darwin":
            self.menuBar().setNativeMenuBar(False)
        self._setup_menu_file()
        self._setup_menu_help()
    
    

    def _setup_menu_help(self):
        m = self.menuBar()
        hm = m.addMenu("&Help")
        hm.addAction(self._actions["about"])
        return hm


    def _save(self):
        self._main_widget.save()
        self._model.save()

    def _setup_menu_file(self):
        m = self.menuBar()
        fm = m.addMenu("&File")
        fm.addAction(self._actions["save"])
        fm.addAction(self._actions["exit"])
        fm.addAction(self._actions["reset plots"])
        return fm

    def _setup_menu_help(self):
        """Set up the menu bar: [About, Help]"""
        m = self.menuBar()
        hm = m.addMenu("&Help")
        hm.addAction(self._actions["about"])
        hm.addAction(self._actions["help"])
        return hm

    def _on_help(self):
        dialog = HelpDialog(self, self._model)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

    def _on_about(self):
        dialog = AboutDialog(self, self._model)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

    def _reset_plot_data(self):
        self._model.reset_script_server_data()
        try:
            self._main_widget.plots_container.update_all_plots()
        except Exception as e:
            self.log.warning(f"The plots failed to reset. Error is {type(e).__name__}:{e}")
        