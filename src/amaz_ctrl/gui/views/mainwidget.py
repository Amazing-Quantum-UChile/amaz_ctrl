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

from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np

# import snoop

WIDGET_HEIGHT = 350
PARAMETERS_WIDTH=600
INFO_WIDTH = 200


class MainWidget(QtWidgets.QWidget):
    color_theme = {"darker":"rgb(87, 17, 170)",
                   "dark":"rgb(90, 72, 211)",
                   "medium": "rgb(139, 93, 198)",
                   "medium2":"rgb(161, 139, 218)",
                   "light":"rgb(189, 164, 223)",
                   "lighter":"rgb(223, 214, 241)"}
    def __init__(self, parent, model):
        super().__init__(parent)
        self._model = model
        # self.parent = parent #--> I do not need it : parent = mainwindow

        self._tab_keys_list = self._model.tab_keys_list
        self._tab_names_list = self._model.tabs
        self._parameter = self._model.parameter_dic
        self.keys = self._model.keys
        self.setup_main_widget()

    def setup_main_widget(self):
        """main function that setup the different part of the GUI.  
        +-----------------------------------------------------------------------+
        |                             MAIN WINDOW                               |
        +---------------------------+---------------+---------------------------+
        |                           |               |                           |
        |      ParameterWidget      |   InfoWidget  |    ActionButtonsWidget    |
        |      (QTabWidget)         | (QScrollArea) |        (QWidget)          |
        |                           |               |                           |
        |  +---------------------+  |  +---------+  |  +---------------------+  |
        |  | Tab 1 | Tab 2 | ... |  |  | Info 1  |  |  |   [ START SCAN ]    |  |
        |  +---------------------+  |  | Info 2  |  |  |                     |  |
        |  | Name  | Value | Scan|  |  | ...     |  |  |   [  STOP SCAN ]    |  |
        |  |-------|-------|-----|  |  |         |  |  |                     |  |
        |  | Param1| 10.5  | [X] |  |  |         |  |  |   [ SAVE DATA  ]    |  |
        |  | Param2| True  | [ ] |  |  |         |  |  |                     |  |
        |  +---------------------+  |  +---------+  |  +---------------------+  |
        |                           |               |                           |
        +---------------------------+---------------+---------------------------+
        """
        # Initialize UI
        # 
        self.params_widget = ParameterWidget( self,
                                         model = self._model,
                                        geometry=(10, 10,  PARAMETERS_WIDTH, WIDGET_HEIGHT)
                                              )
        self.info_widget = InfoWidget(self,
                                    model = self._model, 
                                    geometry=(PARAMETERS_WIDTH+20, 10,  300, 150)
                                    )
        self.buttons_widget = ButtonsWidget(self,
                                    model = self._model, 
                                    geometry=(PARAMETERS_WIDTH+20, 170,  300, 190)
                                    )



    def save(self):
        """action when the user save the configuration"""

        self.params_widget.update_parameters_on_save()
        self.info_widget.refresh()
