#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Created on the Sat Mar 28 2026 by Victor
# Copyright (c) 2026 - AmazingQuantum@UChile
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
# ---------------------------------------------------------------------------

'''
Content of mainwidget.py

Please document your code ;-).

'''



from amaz_ctrl.gui.views.parameters_widget import ParameterWidget
from amaz_ctrl.gui.views.info_widget import InfoWidget
from amaz_ctrl.gui.views.buttons_widget import ButtonsWidget
from amaz_ctrl.gui.views.log_widget import LogWidget
from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np

# import snoop

WIDGET_HEIGHT = 350
PARAMETERS_WIDTH=600
INFO_WIDTH = 300
MARGIN = 10
import logging
log = logging.getLogger("AmazingGUI")

class MainWidget(QtWidgets.QWidget):
    color_theme = {"darker":"rgb(87, 17, 170)",
                   "dark":"rgb(90, 72, 211)",
                   "medium": "rgb(139, 93, 198)",
                   "medium2":"rgb(161, 139, 218)",
                   "light":"rgb(189, 164, 223)",
                   "lighter":"rgb(223, 214, 241)"}
    def __init__(self, parent, model):
        """Main widget in which we 
        Setup the different part of the GUI.  
        +---------------------------+-----------------------+-----------------------+
        |                           |                       |                       |
        |      ParameterWidget      |       InfoWidget      |       LogWidget       |
        |       (QTabWidget)        |     (QScrollArea)     |    (QPlainTextEdit)   |
        |                           |                       |                       |
        |  +---------------------+  |  +-----------------+  |  +-----------------+  |
        |  | Tab 1 | Tab 2 | ... |  |  | Info 1: Value   |  |  | [10:00] Init... |  |
        |  +---------------------+  |  | Info 2: Status  |  |  | [10:05] Scan... |  |
        |  | Name   | Val  | Scan|  |  +-----------------+  |  | [10:10] Data... |  |
        |  |--------|------|-----|  |                       |  |                 |  |
        |  | Param1 | 10.5 | [X] |  |     ButtonsWidget     |  |                 |  |
        |  | Param2 | True | [ ] |  |  +-----------------+  |  |                 |  |
        |  +---------------------+  |  | [ START SCAN ]  |  |  |                 |  |
        |                           |  | [  STOP SCAN ]  |  |  |                 |  |
        |                           |  | [ SAVE DATA  ]  |  |  |                 |  |
        |                           |  +-----------------+  |  +-----------------+  |
        +---------------------------+-----------------------+-----------------------+
        Parameters
        ----------
        parent : _type_
            _description_
        model : _type_
            _description_
        """
        super().__init__(parent)
        self._model = model
        # self.parent = parent #--> I do not need it : parent = mainwindow

        self._tab_keys_list = self._model.tab_keys_list
        self._tab_names_list = self._model.tabs
        self._parameter = self._model.parameter_dic
        self.keys = self._model.keys

        ## ---------------
        ## Set up the GUI
        ## ---------------
        # self.setup_main_widget()
        self.params_widget = ParameterWidget( self,
                                         model = self._model,
                                        geometry=(MARGIN, MARGIN,  PARAMETERS_WIDTH, WIDGET_HEIGHT)
                                              )
        self.info_widget = InfoWidget(self,
                                    model = self._model, 
                                    geometry=(PARAMETERS_WIDTH+MARGIN*2, MARGIN,  INFO_WIDTH, 150)
                                    )
        self.buttons_widget = ButtonsWidget(self,
                                    model = self._model, 
                                    geometry=(PARAMETERS_WIDTH+20, 170,  INFO_WIDTH, 190)
                                    )
        self.log_widget = LogWidget(self, model = self._model,
                                    geometry=(PARAMETERS_WIDTH+INFO_WIDTH+MARGIN*3, 
                                              MARGIN,  600, WIDGET_HEIGHT)
                                    )


    def save(self):
        """action when the user saves the configuration"""
        self.params_widget.update_parameters_on_save()
        ## in case the model did not accepted the value of the user
        self.params_widget.update_GUI_from_model()
        self.info_widget.refresh()
