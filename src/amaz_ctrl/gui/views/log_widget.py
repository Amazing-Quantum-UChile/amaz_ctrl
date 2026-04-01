#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Created on the Tue Mar 31 2026 by Victor
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
Content of log_widget.py

Defines the Logging widget in which we print log from both the GUI (i.e. this program) and the server. 
'''
import logging, csv, os, random
log = logging.getLogger("AmazingGUI")
from PyQt5 import QtWidgets, QtCore, QtGui


class LogWidget(QtWidgets.QGroupBox):
    """Logger level for the GUI. Change the level here.

    Parameters
    ----------
    QtWidgets : _type_
        _description_
    """


    _log_level = "DEBUG"


    _levelname_colors = {
        # white
        "NOTSET": "#FFFFFF",
        "DEBUG": "#8C8C8C",
        # theme
        "INFO": "#DFD6F1",
        # orange
        "WARNING": "#FFBE57",
        "WARN":  "#FFBE57",
        # red
        "ERROR": "#FC7E7E",
        "CRITICAL": "#FF0000",
        "FATAL": "#FF0000",
    }
    

    def __init__(self, parent, model, geometry):
        super().__init__("Logs", parent)
        self._model = model
        self.setGeometry(*geometry)

        ## 1. Create the text
        self.console = QtWidgets.QPlainTextEdit(self)
        self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(200)
        
        ## 2. Set the style for the console
        self.console.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #333;
            }
        """)

        # 3. layout of the console
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(5, 15, 5, 5)
        layout.addWidget(self.console)
        
        ## 4. Connect to logger
        self.setup_GUI_logging_bridge()
        self.set_log_level(self._log_level)

    def set_log_level(self,lvl):
        self._log_level = lvl
        self.log.setLevel(lvl)

    def setup_GUI_logging_bridge(self):
        """Connects the AmazingGUI logger to the QWidget. The AmazingGUI logging is the one that we use in the GUI part of the amaz_ctrl program."""
        self.handler = QtLogHandler()
        self.handler.new_record.connect(self._append_log)
        formatter = logging.Formatter('GUI: %(asctime)s: %(message)s', '%H:%M:%S')
        self.handler.setFormatter(formatter)
        self.log = logging.getLogger("AmazingGUI")
        self.log.addHandler(self.handler)
        

    def _append_log(self, message, level="INFO"):
        """Add a message to the log."""
        # self.console.appendPlainText(message)
        ## set color
        if level in self._levelname_colors.keys():
            color = self._levelname_colors[level]
        else:
            color=self._levelname_colors["NOTSET"]
        self.console.appendHtml(f'<span style="color:{color};">{message}</span>')
        self.console.moveCursor(QtGui.QTextCursor.End)



class QtLogHandler(logging.Handler, QtCore.QObject):
    """Custom handler that sends a signal to the GUI when a message is logged."""
    new_record = QtCore.pyqtSignal(str, str)

    def __init__(self):
        # On initialise les deux parents
        logging.Handler.__init__(self)
        QtCore.QObject.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        self.new_record.emit(msg, record.levelname)