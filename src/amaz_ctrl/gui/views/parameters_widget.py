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
Content of parameters_widget.py

Please document your code ;-).

'''
from PyQt5 import QtCore, QtWidgets

class ParameterWidget(QtWidgets.QTabWidget):
    _parameter_raw_size={"name":8,"value":2,"button":1}
    def __init__(self, parent, model, geometry):
        super().__init__(parent)
        self._model = model
        self.color_theme = parent.color_theme
        self.setGeometry(QtCore.QRect(*geometry))
        
        self._tab_keys_list = self._model.tab_keys_list
        self._tab_names_list = self._model.tabs
        self.keys = self._model.keys

        self._initialize_tab_Widget()

    def _initialize_tab_Widget(self):
        """initialize the tab widget
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
        layout.setColumnStretch(0, 8) # name
        layout.setColumnStretch(1, 2) # value
        layout.setColumnStretch(2, 1) # if scanned
        layout.setColumnStretch(3, 2) # start
        layout.setColumnStretch(4, 2) # stop
        layout.setColumnStretch(5, 2) # steps
        # rows.setContentsMargins(1, 1, 20, 1) # the margin 
        ##################
        ### Set up title:
        ##################
        color = self.color_theme["lighter"]

        label = QtWidgets.QLabel("Name")
        label.setStyleSheet("color : {}".format(color))
        layout.addWidget(label, 0,0)
        label = QtWidgets.QLabel("Value")
        label.setStyleSheet("color : {}".format(color))
        layout.addWidget(label, 0,1)
        label = QtWidgets.QLabel("Scan")
        label.setStyleSheet(" color : {}".format(color))
        layout.addWidget(label, 0,2)
        label = QtWidgets.QLabel("Start")
        label.setStyleSheet(" color : {}".format(color))
        layout.addWidget(label, 0,3)
        label = QtWidgets.QLabel("Stop")
        label.setStyleSheet(" color : {}".format(color))
        layout.addWidget(label, 0,4)
        label = QtWidgets.QLabel("Steps")
        label.setStyleSheet(" color : {}".format(color))
        layout.addWidget(label, 0,5)

        ## We now loop over the parameters of the tab to create buttons and labels.
        for i, key in enumerate(list_of_parameters):
            layout = self.add_parameter_to_layout( key, layout, row=i+1)

    def add_parameter_to_layout(self, key, layout, row):
        ## get the parameter (class Parameter of the model)
        parameter= self._model.parameter_dic[key]

        ## We add this specific parameter to the widget_dict dictionary in which we store Widgets  
        self.widget_dict[key] = {} #empty initialisation
        #################
        #### Fill layout
        #################
        # 1st column of the layout : Name of the parameter
        self.widget_dict[key]["name"] = QtWidgets.QLabel(
            parameter.short_name
        )
        layout.addWidget(self.widget_dict[key]["name"], row,0)

        # 2nd column : value of the parameter

        # ## The following depends on the type of the parameter:
        # * if we can scan it (float, int), we add a button widgets and 3 LineEdit
        # * if we cannot (str, bool), we add empty to the widget dict an NullWidget so that the code works. 
        #       * If the parameter is a string, we expand the QLineEdit to the end of the line.
        #       * If the parameter is a box, we use a QCheckBox
        if parameter.type == bool:
            self.widget_dict[key]["value"] = QtWidgets.QCheckBox(
                tristate=False
            )
            self.widget_dict[key]["value"].setStyleSheet(
                "QCheckBox::indicator" "{" "width :15px;" "height : 15px;" "}"
            )
            self.widget_dict[key]["value"].setChecked(
                parameter.value
            )
            layout.addWidget(self.widget_dict[key]["value"], row,1)
        elif parameter.type == str:
            self.widget_dict[key]["value"] = QtWidgets.QLineEdit()
            self.widget_dict[key]["value"].setText(
                parameter.value
            )
            layout.addWidget(self.widget_dict[key]["value"],row, 1, 1, 5) # span of 5 columns
        else:
            lab = QtWidgets.QLineEdit()
            lab.setText(
                str(parameter.value)
            )
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
            self.widget_dict[key]["scanned"].setChecked(
                parameter.scanned
            )
            layout.addWidget(self.widget_dict[key]["scanned"],row,2)

            # Fourth column : scan start
            self.widget_dict[key]["start"] = QtWidgets.QLineEdit()
            self.widget_dict[key]["start"].setText(
                str(parameter.scan_start)
            )
            layout.addWidget(self.widget_dict[key]["start"], row,3)

            # Fifth column : scan stop
            line_edit = QtWidgets.QLineEdit()
            line_edit.setText(
                str(parameter.scan_stop)
            )
            layout.addWidget(line_edit, row,4)
            self.widget_dict[key]["stop"] = line_edit

            # Sixth column : scan step
            line_edit =  QtWidgets.QLineEdit()
            line_edit.setText(
                str(parameter.scan_steps)
            )
            layout.addWidget(line_edit, row,5)
            self.widget_dict[key]["steps"] =line_edit

        return layout


    def set_up_raw_parameter_layout(self, key):
        """method that generates a row for a given parameter. The raw consists of a horizontal layout
        "Qlabel with the name" | Edit value | Scan button | Start edit | Stop edit | Steps edit |

        Parameters
        ----------
        key : str
            the key of the parameter of the sequence parameter. 

        Returns
        -------
        QtWidgets.QHBoxLayout
            the horizontal layout with all 
        """
        layout = QtWidgets.QHBoxLayout()
        ## get the parameter (class Parameter of the model)
        parameter= self._model.parameter_dic[key]

        ## We add this specific parameter to the widget_dict dictionary in which we store Widgets  
        self.widget_dict[key] = {} #empty initialisation

        # 1st column of the layout : Name of the parameter
        self.widget_dict[key]["name"] = QtWidgets.QLabel(
            parameter.short_name
        )
        layout.addWidget(self.widget_dict[key]["name"], self._parameter_raw_size["name"])

        # 2nd column : value of the parameter

        ### The following depends on the type of the parameter:
        # * if we can scan it (float, int), we add a button widgets and 3 LineEdit
        # * if we cannot (str, bool), we add empty to the widget dict an NullWidget so that the code works. 
        #       * If the parameter is a string, we expand the QLineEdit to the end of the line.
        #       * If the parameter is a box, we use a QCheckBox


        if parameter.type == bool:
            self.widget_dict[key]["value"] = QtWidgets.QCheckBox(
                tristate=False
            )
            self.widget_dict[key]["value"].setStyleSheet(
                "QCheckBox::indicator" "{" "width :15px;" "height : 15px;" "}"
            )
            self.widget_dict[key]["value"].setChecked(
                parameter.value
            )
            layout.addWidget(self.widget_dict[key]["value"], self._parameter_raw_size["value"])
        elif parameter.type == str:
            self.widget_dict[key]["value"] = QtWidgets.QLineEdit()
            self.widget_dict[key]["value"].setText(
                parameter.value
            )
            layout.addWidget(self.widget_dict[key]["value"], 4 * self._parameter_raw_size["value"]+self._parameter_raw_size["button"])
        else:
            self.widget_dict[key]["value"] = QtWidgets.QLineEdit()
            self.widget_dict[key]["value"].setText(
                str(parameter.value)
            )
            layout.addWidget(self.widget_dict[key]["value"], self._parameter_raw_size["value"])

        if parameter.type in [str, bool]:
            self.widget_dict[key]["scanned"] = NullWidget()
            self.widget_dict[key]["start"] = NullWidget()
            self.widget_dict[key]["stop"] = NullWidget()
            self.widget_dict[key]["steps"] = NullWidget()
        else:
            # Third column : if we want to scan it
            self.widget_dict[key]["scanned"] = QtWidgets.QCheckBox(tristate=False)
            self.widget_dict[key]["scanned"].setChecked(
                parameter.scanned
            )
            layout.addWidget(self.widget_dict[key]["scanned"], self._parameter_raw_size["button"])

            # Fourth column : scan start
            self.widget_dict[key]["start"] = QtWidgets.QLineEdit()
            self.widget_dict[key]["start"].setText(
                str(parameter.scan_start)
            )
            layout.addWidget(self.widget_dict[key]["start"], self._parameter_raw_size["value"])

            # Fifth column : scan stop
            self.widget_dict[key]["stop"] = QtWidgets.QLineEdit()
            self.widget_dict[key]["stop"].setText(
                str(parameter.scan_stop)
            )
            layout.addWidget(self.widget_dict[key]["stop"], self._parameter_raw_size["value"])

            # Sixth column : scan step
            self.widget_dict[key]["steps"] = QtWidgets.QLineEdit()
            self.widget_dict[key]["steps"].setText(
                str(parameter.scan_steps)
            )
            layout.addWidget(self.widget_dict[key]["steps"], self._parameter_raw_size["value"])
        return layout
            

    def get_parameter_line_layout(self):
        layout = QtWidgets.QHBoxLayout()
        ## set the stretching of each column
        
        return layout

    def update_parameters_on_save(self):
        """update the model on save"""
        for key in self.keys:
            parameter = self._model.parameter_dic[key]
            if parameter.type == bool:
                parameter.set_value(
                    self.widget_dict[key]["value"].isChecked()
                )
            else:
                parameter.set_value(
                    self.widget_dict[key]["value"].text()
                )
            parameter.set_scan_start(
                self.widget_dict[key]["start"].text()
            )
            parameter.set_scan_stop(
                self.widget_dict[key]["stop"].text()
            )
            parameter.set_scan_steps(
                self.widget_dict[key]["steps"].text()
            )
            parameter.set_scanned(
                self.widget_dict[key]["scanned"].isChecked()
            )


class NullWidget():
    def isChecked(self):
        return False
    def text(self):
        return "0"