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

'''
Content of help_dialog.py

This code creates a windows in which we display a text that helps the user if they want to realize simple tasks such as adding a parameter to their experiment.
'''

import os
import sys

from PyQt5 import QtCore, QtGui, QtWidgets


class HelpDialog(QtWidgets.QDialog):
    def __init__(self, parent, model):
        super().__init__(parent)
        self._model = model
        self._initialize_ui()


    def _initialize_ui(self):
        self.setWindowTitle("Help on the Amazing Controller GUI")
        v_layout = QtWidgets.QVBoxLayout(self) 
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            md_path = os.path.join(current_dir, "..", "..","..", "..", "..",  "docs", "gui_how_to.md")
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.text_display = QtWidgets.QTextBrowser()
                v_layout.addWidget(self.text_display)
                self.text_display.setMarkdown(content)
                self.resize(700, 450)
        except Exception as e:
            print(e)
            try:
                self.resize(600, 450)
                label_gif = QtWidgets.QLabel()
                label_gif.setAlignment(QtCore.Qt.AlignCenter) 
                self.movie = QtGui.QMovie(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            "img",
                                            "travolta.gif"))
                label_gif.setMovie(self.movie)
                self.movie.start()
                v_layout.addWidget(label_gif, alignment=QtCore.Qt.AlignCenter)
            except:
                pass
        self.setLayout(v_layout)
