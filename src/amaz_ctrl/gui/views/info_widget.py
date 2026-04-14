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
Content of info_widget.py

This file defines the InfoWidget class which is a scrolling pannel in which we display informations such as the last save and the scanned parameters.

Final form of the widget:
+-----------------------------------------------------------+
|                                                           |
| Last saved at 14:30:05                                    |
|                                                           |
| Scanned Parameters :                                      |
|                                                           |
|  - Frequency from 10.0 to 20.0 with 5 steps of 2.50       |
|  - Amplitude from 0.1 to 1.0 with 10 steps of 0.10        |
|  - Phase from -180 to 180 with 36 steps of 10.00          |
|                                                           |
+-----------------------------------------------------------+

Hierarchy:
MainWidget (QWidget, parent) 
└── InfoWidget (QScrollArea)
    └── content (QWidget)
        └── rows (QFormLayout)
                └── [Label 1: Timestamp]
                └── [Label 2: Section Title]
                └── [Label 3: Scan Info Row] 
"""
import datetime
import numpy as np
from PyQt5 import QtCore, QtWidgets

class InfoWidget(QtWidgets.QScrollArea):
    def __init__(self, parent, model, geometry):
        super().__init__(parent)
        self._model = model
        self.color_theme = parent.color_theme
        self.setGeometry(QtCore.QRect(*geometry))
        self.keys = self._model.keys
        self.refresh()  ## Display information

    def refresh(self):
        """method that generates the informations displayed on the widget.
        We show the datetime of the last refresh (i.e. last time we saved) and the scanned parameters.
        """
        ## remove tab if already present
        content = QtWidgets.QWidget()
        # content.setContentsMargins(0,0,0,0)
        self.setWidget(content)
        self.setWidgetResizable(True)
        ## Display the last refresh moment.
        rows = QtWidgets.QFormLayout(content)
        rows.setContentsMargins(1,5,2,1)
        rows.setVerticalSpacing(0)
        
        self.show_refresh_time(rows)
        self.show_scanned_parameters(rows)
    
        
        
    def show_refresh_time(self, rows):
        """add the refresh time to the row"""
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")
        label = QtWidgets.QLabel("Last saved at {}".format(current_time))
        label.setWordWrap(True)
        color = self.color_theme["lighter"]
        label.setStyleSheet(" color : {}".format(color))
        rows.addRow(label)

    def show_scanned_parameters(self, rows):
        """add the scanned parameters to the raw."""
        ## - Loop over parameter to display parameters that are scanned.
        ## - Display color
        color = self.color_theme["lighter"]#"rgb(227,207,87)"
        # boolean to make sure we only show once "Scanned Parameters : "
        no_title = True
        for key in self.keys:
            if self._model.parameter_dic[key].scanned:
                if no_title:
                    title = QtWidgets.QLabel("Scanned Parameters : ")
                    title.setStyleSheet(" color : {}".format(color))
                    rows.addRow(title)
                    no_title = False
                if self._model.parameter_dic[key].type==bool:
                    msg = f" - {key} from true to false."
                else:
                    step = self._model.parameter_dic[key].get_step()
                    msg = " - {} from {} to {} with {} steps of {:,.2f}".format(
                        key,
                        self._model.parameter_dic[key].scan_start,
                        self._model.parameter_dic[key].scan_stop,
                        self._model.parameter_dic[key].scan_steps,
                        step,
                    )
                label = QtWidgets.QLabel(msg)
                label.setWordWrap(True)
                label.setStyleSheet(" color : {}".format(color))
                rows.addRow(label)
