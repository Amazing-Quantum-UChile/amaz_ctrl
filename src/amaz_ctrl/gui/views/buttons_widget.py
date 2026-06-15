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
import time, os
class ButtonsWidget(QtWidgets.QScrollArea):
    button_height = 30
    default_script_name = "main.py"
    _run_buttons = {"run_protocol": "Start new\nprotocol", 
                    "continue_protocol": "Continue\nprotocol",
                    "run_test":"Run test"}#["Run Protocol", "Run Test", "Run Sequence"]

    def __init__(self, parent, model, geometry):
        super().__init__(parent)
        self._model = model
        self.setGeometry(QtCore.QRect(*geometry))

        self.layout = QtWidgets.QGridLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)

        ## Set up all buttons
        self.set_up_script_combobox()
        self.set_up_upload_btn()
        self.set_up_run_btn()
        self.set_up_stop_btn()

    # def set_up_script_line(self):# depreciated
    #     label = QtWidgets.QLabel("Script:")
    #     self.layout.addWidget(label, 0, 0, 1, 1)
    #     self.script_name = QtWidgets.QLineEdit()
    #     self.script_name.setText(self.default_script_name)
    #     self.layout.addWidget(self.script_name, 0, 1, 1, 2)

    def set_up_script_combobox(self):
        label = QtWidgets.QLabel("Script:")
        self.layout.addWidget(label, 0, 0, 1, 1)
        
        # 1. Create the ComboBox (dropdown) instead of LineEdit
        self.script_combobox = QtWidgets.QComboBox()
        
        self.refresh_script_list()
            
        self.layout.addWidget(self.script_combobox, 0, 1, 1, 2)
    def refresh_script_list(self):
        """Refreshes the items in the combobox while preserving the current selection."""
        # 1. Remember what was previously selected
        last_chosen = self.script_combobox.currentText()
        
        # 2. Clear the current items
        self.script_combobox.clear()
        self.script_combobox.setEnabled(True)
        
        # 3. Fetch the updated file list
        scripts = self._get_available_scripts()
        
        if scripts:
            self.script_combobox.addItems(scripts)
            
            # 4. Try to re-select the last chosen script if it still exists
            if last_chosen in scripts:
                self.script_combobox.setCurrentText(last_chosen)
            else:
                # Fallback to the first item if the old one is gone
                self.script_combobox.setCurrentIndex(0)
        else:
            self.script_combobox.addItem("None")
            self.script_combobox.setEnabled(False)

    def _get_available_scripts(self):
        """Helper method to scan the directory for specific extensions."""
        # Fallback to current directory if _script_dir isn't set/found
        script_dir = getattr(self._model, 'exp_par_directory', '.') 
        extensions = getattr(self._model, '_script_ext', ['py'])
        
        if not os.path.exists(script_dir):
            return []

        valid_files = []
        # List all files in the directory
        for file in os.listdir(script_dir):
            # Check if the file ends with any of the extensions in the list
            if any(file.endswith(f".{ext}") for ext in extensions):
                valid_files.append(file)
                
        return sorted(valid_files)

    ### --  UPLOAD BUTTON  --
    def set_up_upload_btn(self):
        self.btn_upload = QtWidgets.QPushButton("Upload Script")
        self.btn_upload.setFixedHeight(self.button_height)
        self.layout.addWidget(self.btn_upload, 1, 0, 1, 3)
        self.btn_upload.clicked.connect(self._upload_btn_pushed)

    def _upload_btn_pushed(self):
        """connect the action when the upload button is pushed to 
        the model: we call the load_script function of the ScriptServer."""
        # script_name = self.script_name.text()
        script_name = self.script_combobox.currentText()
        # Don't trigger if it's set to "None"
        if script_name == "None":
            self._model.log.error("No script to upload was selected.")
            return
        self._model.server_script_connector.load_script(script_name)

    

    ### --  RUN BUTTON  --
    def set_up_run_btn(self):
        # def set_up_run_btn(self):
        self.run_buttons = {}
        
        for index, (button_cmd, button_name) in enumerate(self._run_buttons.items()):
            # Instantiate our custom class
            btn = RunButton(
                button_name=button_name, 
                callback=self._run_btn_pushed, 
                button_command = button_cmd,
                parent=self
            )
            btn.setFixedHeight(2*self.button_height)
            
            self.layout.addWidget(btn, 2, index, 1, 1)
            self.run_buttons[button_name] = btn
        # self.btn_run = QtWidgets.QPushButton("Run Script")
        # self.btn_run.setFixedHeight(self.button_height)
        # self.layout.addWidget(self.btn_run, 2, 0, 1, 3)
        # self.btn_run.clicked.connect(self._run_btn_pushed)

    def _run_btn_pushed(self, button_name="default"):
        # self._model.btn_run_pushed()
        self.parent().parent()._save()

        self._model.server_script_connector.run_script(script_options = button_name)
        

    ### --  STOP BUTTON  --
    def set_up_stop_btn(self):
        self.btn_stop = QtWidgets.QPushButton("Stop")
        self.btn_stop.setFixedHeight(self.button_height)
        self.layout.addWidget(self.btn_stop, 3, 0, 1, 3)
        self.btn_stop.clicked.connect(self._stop_btn_pushed)

    def _stop_btn_pushed(self):
        self._model.server_script_connector.stop()


class RunButton(QtWidgets.QPushButton):
    def __init__(self, button_name, callback, button_command ,  parent=None):
        """Run button object to connect a push action into sending a command to a script with a given command. """
        super().__init__(button_name, parent)
        self.name = button_name
        self.command = button_command
        self.callback = callback
        
        # Connect Qt's clicked signal directly to our internal method
        self.clicked.connect(self._on_clicked)

    def _on_clicked(self):
        # We explicitly forward the button name to the main view's callback
        self.callback(button_name=self.command)