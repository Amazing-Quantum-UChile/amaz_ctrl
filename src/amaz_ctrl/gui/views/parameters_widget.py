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

"""
Content of parameters_widget.py

Define the paramneter widget which inherits the QTabWidget. See doc below.
"""
from PyQt5 import QtCore, QtWidgets


class ParameterWidget(QtWidgets.QTabWidget):
    """
    This class implements the view of the Parameter widgets. We loop over
    all possible tabs as defined in the model and in each tab, we display parameter in a raw.

    +----------------------------------------------------------------------+
    | [ Tab: Laser ] [ Tab: Detection ] [ Tab: ... ]                       |
    +----------------------------------------------------------------------+
    | Name           Value  Scan  Start   Stop    Steps                  | |
    | Parameter 1    [ 10 ]  [X]  [ 5.0 ] [ 15.0 ] [ 10 ]                | |
    | Parameter 2     [X]                   (for boolean we do not scan) | |
    | Parameter 3    [ 0.5 ] [ ]  [ 0.0 ] [ 1.0 ]  [ 5  ]                | |
    | Parameter 4    [String parameter so we expand...  ]                | |
    | ...                                                                | |
    |                                                                    | |
    +----------------------------------------------------------------------+

    Parameters
    ----------
    QtWidgets : _type_
        _description_
    """
    def __init__(self, parent:QtWidgets.QWidget, model, geometry:tuple):
        """Instanciate the ParameterWidget class

        Parameters
        ----------
        parent : QtWidgets.QWidget
            the parent Widget of the Widget. 
        model : Model
            the model of the GUI.
        geometry : tuple
            the geometry in the GUI (x_start, y_start, width, height) of the widget
        """

        super().__init__(parent)
        self._model = model
        self.color_theme = parent.color_theme
        self.setGeometry(QtCore.QRect(*geometry))

        self._tab_keys_list = self._model.tab_keys_list
        self._tab_names_list = self._model.tabs
        self.keys = self._model.keys

        self._initialize_tab_Widget()
        ## Fill the GUI with the values of the model
        self.update_GUI_from_model()

    def _initialize_tab_Widget(self):
        """initialize the tab widget. 
        We follow https://stackoverflow.com/questions/20282965/how-to-display-a-list-of-qpushbutton
        """
        # To be changed
        self._tabs = {}  # list that contains all tab wigets
        self._tabs_content = {}
        self._tab_rows = {}
        self.widget_dict = (
            {}
        )  # contains all widgets (QButtons & QLineEdit) of the parameters
        ## We loop over the tab list i.e. [Laser, Detection,]
        for tab_name in self._tab_names_list:
            if len(self._tab_keys_list[tab_name]) > 0:
                # We add the tabs to the tabWidget
                self._tabs[tab_name] = QtWidgets.QScrollArea()
                ## -. Create tab and capitalize tab name title.
                self.addTab(self._tabs[tab_name], tab_name.title())
                # We must define the content in this way to have a scrollbar
                self._tabs_content[tab_name] = QtWidgets.QWidget()
                self._tabs[tab_name].setWidget(self._tabs_content[tab_name])
                self._tabs[tab_name].setWidgetResizable(True)

                self._setup_tab_content(tab_name)

    def _setup_tab_content(self, tab_name):
        """generates the content of each tab. We loop over all tabs and create the row for each parameter."""
        list_of_parameters = self._tab_keys_list[tab_name]
        ## Define the layout within the grid
        layout = QtWidgets.QGridLayout(self._tabs_content[tab_name])
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.setContentsMargins(1, 1, 20, 1)
        layout.setColumnStretch(0, 8)  # name
        layout.setColumnStretch(1, 2)  # value
        layout.setColumnStretch(2, 1)  # if scanned
        layout.setColumnStretch(3, 2)  # start
        layout.setColumnStretch(4, 2)  # stop
        layout.setColumnStretch(5, 2)  # steps
        # rows.setContentsMargins(1, 1, 20, 1) # the margin
        ##################
        ### Set up title:
        ##################
        color = self.color_theme["lighter"]

        label = QtWidgets.QLabel("Name")
        label.setStyleSheet("color : {}".format(color))
        layout.addWidget(label, 0, 0)
        label = QtWidgets.QLabel("Value")
        label.setStyleSheet("color : {}".format(color))
        layout.addWidget(label, 0, 1)
        label = QtWidgets.QLabel("Scan")
        label.setStyleSheet(" color : {}".format(color))
        layout.addWidget(label, 0, 2)
        label = QtWidgets.QLabel("Start")
        label.setStyleSheet(" color : {}".format(color))
        layout.addWidget(label, 0, 3)
        label = QtWidgets.QLabel("Stop")
        label.setStyleSheet(" color : {}".format(color))
        layout.addWidget(label, 0, 4)
        label = QtWidgets.QLabel("Steps")
        label.setStyleSheet(" color : {}".format(color))
        layout.addWidget(label, 0, 5)

        ## We now loop over the parameters of the tab to create buttons and labels.
        for i, key in enumerate(list_of_parameters):
            layout = self.add_parameter_to_layout(key, layout, row=i + 1)

        

    def add_parameter_to_layout(self, key:str, layout:QtWidgets.QGridLayout, row:int):
        """method that adds a row to the layout in which a parameter is displaid. The 
        layout of each row depends on the type of the parameter. In particular, if it 
        is a string, we expand the QEditLine.
        Note that we only create the layout but do not fill it with the correct values. 


        GUI Layout Schemes per Parameter Type:

        1. Numeric (int/float) - Full controls for scanning
        [ Name (8) ] [Val (2)] [S (1)] [Start(2)] [Stop (2)] [Steps(2)]
        +------------+--------+-------+---------+---------+---------+
        | Frequency  | [10.0] |  [X]  | [ 5.0 ] | [15.0 ] | [ 100 ] |
        +------------+--------+-------+---------+---------+---------+

        2. Boolean - Uses a CheckBox (Standard width)
        +------------+--------+
        | Shutter    |  [X]   |
        +------------+--------+

        3. String - QLineEdit expanded to the end of the row (Span 5)
        +------------+--------------------------------------------------+
        | Comment    | [String value expands here...                  ] |
        +------------+--------------------------------------------------+

        Parameters
        ----------
        key : str
            the key of the parameter we want to display, e.g. 'laser 1ph detuning (MHz)'
        layout : QtWidgets.QGridLayout
            the lay
        row : int
            the row number in which we add the parameter to the layout

        Returns
        -------
        _type_
            _description_
        """
        ## get the parameter (class Parameter of the model)
        parameter = self._model.parameter_dic[key]

        ## We add this specific parameter to the widget_dict dictionary in which we store Widgets
        self.widget_dict[key] = {}  # empty initialisation
        #################
        #### Fill layout
        #################
        # 1st column of the layout : Name of the parameter
        self.widget_dict[key]["name"] = QtWidgets.QLabel(parameter.short_name)
        layout.addWidget(self.widget_dict[key]["name"], row, 0)

        # 2nd column : value of the parameter

        # ## The following depends on the type of the parameter:
        # * if we can scan it (float, int), we add a button widgets and 3 LineEdit
        # * if we cannot (str, bool), we add empty to the widget dict an NullWidget so that the code works.
        #       * If the parameter is a string, we expand the QLineEdit to the end of the line.
        #       * If the parameter is a box, we use a QCheckBox
        if parameter.type == bool:
            self.widget_dict[key]["value"] = QtWidgets.QCheckBox(tristate=False)
            self.widget_dict[key]["value"].setStyleSheet(
                "QCheckBox::indicator" "{" "width :15px;" "height : 15px;" "}"
            )
            layout.addWidget(self.widget_dict[key]["value"], row, 1)
        elif parameter.type == str:
            self.widget_dict[key]["value"] = QtWidgets.QLineEdit()
            layout.addWidget(
                self.widget_dict[key]["value"], row, 1, 1, 5
            )  # span of 5 columns
        else:
            lab = QtWidgets.QLineEdit()
            layout.addWidget(lab, row, 1)
            self.widget_dict[key]["value"] = lab

        if parameter.type in [str, bool]:
            self.widget_dict[key]["scanned"] = NullWidget()
            self.widget_dict[key]["start"] = NullWidget()
            self.widget_dict[key]["stop"] = NullWidget()
            self.widget_dict[key]["steps"] = NullWidget()
        else:
            # Third column : if we want to scan it
            self.widget_dict[key]["scanned"] = QtWidgets.QCheckBox(tristate=False)
            layout.addWidget(self.widget_dict[key]["scanned"], row, 2)

            # Fourth column : scan start
            self.widget_dict[key]["start"] = QtWidgets.QLineEdit()
            layout.addWidget(self.widget_dict[key]["start"], row, 3)

            # Fifth column : scan stop
            line_edit = QtWidgets.QLineEdit()
            layout.addWidget(line_edit, row, 4)
            self.widget_dict[key]["stop"] = line_edit

            # Sixth column : scan step
            line_edit = QtWidgets.QLineEdit()
            layout.addWidget(line_edit, row, 5)
            self.widget_dict[key]["steps"] = line_edit
        return layout

    def update_GUI_from_model(self):
        """update the GUI using the parameters of the model."""
        
        for key in self.keys:
            parameter = self._model.parameter_dic[key]
            if parameter.type == bool:
                self.widget_dict[key]["value"].setChecked(parameter.value)
            else: 
                self.widget_dict[key]["value"].setText(str(parameter.value))
            self.widget_dict[key]["scanned"].setChecked(parameter.scanned)
            self.widget_dict[key]["start"].setText(str(parameter.scan_start))
            self.widget_dict[key]["stop"].setText(str(parameter.scan_stop))
            self.widget_dict[key]["steps"].setText(str(parameter.scan_steps))
            

    def update_parameters_on_save(self):
        """Callback method when save is press. The  model is updated using the 
        value of the GUI."""
        
        for key in self.keys:
            parameter = self._model.parameter_dic[key]
            if parameter.type == bool:
                parameter.set_value(self.widget_dict[key]["value"].isChecked())
            else:
                parameter.set_value(self.widget_dict[key]["value"].text())
            parameter.set_scan_start(self.widget_dict[key]["start"].text())
            parameter.set_scan_stop(self.widget_dict[key]["stop"].text())
            parameter.set_scan_steps(self.widget_dict[key]["steps"].text())
            parameter.set_scanned(self.widget_dict[key]["scanned"].isChecked())


class NullWidget:
    """implements the NullWidget. The idea is to instanciate this widget in the 
    widget_dict dictionary so that we do not have to check wether a widget was
    created (if the typo is a float or an int ) or not (string or boolean).  """
    def isChecked(self):
        return False

    def text(self):
        return "0"

    def setChecked(self, arg):
        pass

    def setText(self, arg):
        pass
    
