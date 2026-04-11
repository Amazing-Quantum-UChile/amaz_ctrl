#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Created on the Tue Mar 31 2026 by Victor
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
Content of log_widget.py

Defines the Logging widget in which we print log from both the GUI (i.e. this program) and the server. 
'''
import logging, csv, os, random
from PyQt5 import QtWidgets, QtCore, QtGui
from amaz_ctrl.tools.amaz_logs import connect_logger_to_call_out


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
        "INFO": "#89D89A",
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
        
        ## 4. Connect the logger to the console print
        self.log = self._model.log
        connect_logger_to_call_out(self.log, self._append_log)
        self.set_log_level(self._log_level)

    def set_log_level(self,lvl):
        self._log_level = lvl
        self.log.setLevel(lvl)


    def _append_log(self, message:str, level="INFO"):
        """Add a message to the log."""
        formatted_log = self.format_log(message, level)
        self.console.appendHtml(formatted_log)
        self.console.moveCursor(QtGui.QTextCursor.End)
        
    def _append_many_log(self, list_of_logs:list):
        """_summary_

        Parameters
        ----------
        dict_of_logs : list of dict
            dictionary of 
        """
        if not list_of_logs:
            return
        formatted_log = ""
        for log in list_of_logs:
            formatted_log=self.format_log(log["message"],
                                           log["level"])+"\n"
            self.console.appendHtml(formatted_log)
        self.console.moveCursor(QtGui.QTextCursor.End)

    def format_log(self, message, level):
        ## set color
        if level in self._levelname_colors.keys():
            color = self._levelname_colors[level]
        else:
            color=self._levelname_colors["NOTSET"]
        return f'<span style="color:{color};">{message}</span>'
        

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