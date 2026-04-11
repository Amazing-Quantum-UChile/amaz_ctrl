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
Content of app.py

Root file of the GUI part of the Amazing Controller.
'''



from amaz_ctrl.gui.views import mainwindow, mainwidget
from amaz_ctrl.gui.models import mainmodel


from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
)
from PyQt5.QtGui import QIcon
from PyQt5 import QtGui
import qdarkstyle
import sys, os
from PyQt5 import QtCore, QtGui, QtWidgets

class QuantumLightApp(QMainWindow):
    def __init__(self, model, main_window_type:QtWidgets.QMainWindow,
                 main_widget_type:QtWidgets.QWidget,
                  darkstyle=True):

        ## We must construct a QApplication before a QWidget
        app = QApplication(sys.argv)
        super().__init__()
        self._app = app
        self._model = model

        ## -- Styling
        # -. Set icon
        path_to_icon= os.path.join(
            os.path.dirname(__file__), 
            "assets", "logo", "128.png")
        icon = QIcon(path_to_icon)
        self._app.setWindowIcon(icon)
        # -. Load fontawesome
        try:
            base_path = os.path.dirname(os.path.abspath(__file__))
            font_path = os.path.join(base_path, "assets", "fonts", "Font Awesome 5 Free-Solid-900.otf")
            font_id = QtGui.QFontDatabase.addApplicationFont(font_path)
            FA_FAMILY = QtGui.QFontDatabase.applicationFontFamilies(font_id)[0]
        except Exception:
            self._model.log.debug("Failed to load fontawesome")
        
        if darkstyle: 
            self._app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

        ## -- Build application
        self._model._application = app
        self._main_window = main_window_type(model, main_widget_type)
        self._model.main_window = self._main_window
        self._model.log.info("App started")

   
    def run(self):
        sys.exit(self._app.exec_())




def main():
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    exp_param_dir = os.path.join(parent_dir, "scripts")
    ## we must provide to the model the directory of the exp_param.json file
    model = mainmodel.Model(exp_param_dir, 
                            log_level="INFO", logger_name="GUI")
    appl = QuantumLightApp(model,
                            mainwindow.MainWindow,
                            mainwidget.MainWidget)
    appl.run()


if __name__ == "__main__":
    main()

# scancontroller.py ends here.
