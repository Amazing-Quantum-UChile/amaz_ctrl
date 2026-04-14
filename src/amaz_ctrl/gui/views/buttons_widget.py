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
Content of buttons_widget.py

ButtonsPanel (QWidget)
----------------------
Control panel for script management and execution.
Provides a 3-column grid layout for script selection and command triggers.

Layout Grid Mapping:
+-----------------------------------------------------------+
| [Row 0] | Label "Script:" |      QLineEdit (Span 2)       |
+---------+-----------------+-------------------------------+
| [Row 1] |          QPushButton "Upload Script" (Span 3)   |
+---------+-------------------------------------------------+
| [Row 2] |          QPushButton "Run Script"    (Span 3)   |
+---------+-------------------------------------------------+
| [Row 3] |          QPushButton "Stop"          (Span 3)   |
+-----------------------------------------------------------+

Key Components:
* script_name (QLineEdit): Displays/Edits the target script name.
* btn_upload (QPushButton): Triggers the script upload logic.
* btn_run    (QPushButton): Starts the execution of the loaded script.
* btn_stop   (QPushButton): Emergency stop or script interruption.

Methods:
- set_up_xxxx_btn(): Initializes and places widgets in the grid.
- _xxxx_btn_pushed(): Handles signals and connects to the model.
"""

from PyQt6 import QtCore, QtWidgets
import time
class ButtonsWidget(QtWidgets.QScrollArea):
    button_height = 35
    default_script_name = "main.py"

    def __init__(self, parent, model, geometry):
        super().__init__(parent)
        self._model = model
        self.setGeometry(QtCore.QRect(*geometry))

        self.layout = QtWidgets.QGridLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)

        ## Set up all buttons
        self.set_up_script_line()
        self.set_up_upload_btn()
        self.set_up_run_btn()
        self.set_up_stop_btn()

    def set_up_script_line(self):
        label = QtWidgets.QLabel("Script:")
        self.layout.addWidget(label, 0, 0, 1, 1)
        self.script_name = QtWidgets.QLineEdit()
        self.script_name.setText(self.default_script_name)
        self.layout.addWidget(self.script_name, 0, 1, 1, 2)

    ### --  UPLOAD BUTTON  --
    def set_up_upload_btn(self):
        self.btn_upload = QtWidgets.QPushButton("Upload Script")
        self.btn_upload.setFixedHeight(self.button_height)
        self.layout.addWidget(self.btn_upload, 1, 0, 1, 3)
        self.btn_upload.clicked.connect(self._upload_btn_pushed)

    def _upload_btn_pushed(self):
        """connect the action when the upload button is pushed to 
        the model: we call the load_script function of the ScriptServer."""
        script_name = self.script_name.text()
        self._model.server_script_connector.load_script(script_name)

    ### --  RUN BUTTON  --
    def set_up_run_btn(self):
        self.btn_run = QtWidgets.QPushButton("Run Script")
        self.btn_run.setFixedHeight(self.button_height)
        self.layout.addWidget(self.btn_run, 2, 0, 1, 3)
        self.btn_run.clicked.connect(self._run_btn_pushed)

    def _run_btn_pushed(self):
        # self._model.btn_run_pushed()
        self.parent().parent()._save()
        self._model.server_script_connector.run_script()
        

    ### --  STOP BUTTON  --
    def set_up_stop_btn(self):
        self.btn_stop = QtWidgets.QPushButton("Stop")
        self.btn_stop.setFixedHeight(self.button_height)
        self.layout.addWidget(self.btn_stop, 3, 0, 1, 3)
        self.btn_stop.clicked.connect(self._stop_btn_pushed)

    def _stop_btn_pushed(self):
        self._model.server_script_connector.stop()
