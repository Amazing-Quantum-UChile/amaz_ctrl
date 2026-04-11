#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Created on the Fri Apr 10 2026 by Victor
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
Content of plot_widget.py

Implements the following classes:
    * PlotsContainer: a QGroupBox in which we put different  PlotUnit
    * PlotUnit: a QWidget with a vertical layout in which we store a pyqtgraph.PlotWidget and 3 QComboBox
'''

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QHBoxLayout, QLabel, QComboBox, QGridLayout
import pyqtgraph as pg
import pandas as pd
import numpy as np
import random
class PlotsContainer(QGroupBox):
    def __init__(self, parent, model, num_plots=3):
        super().__init__("Plots",parent)
        self._model = model
        self.log = self._model.log
        x = np.linspace(0, 5, 50)
        df_list = []
        for k in [1, 1.3, .6]:
             df_list.append(pd.DataFrame({"XX": x, 
                                              "sin":np.sin(x*k),"exp":np.exp(k*x/5),
                                              "sinc":np.sinc(k*x), "x2":k*x**2/25,
                                              "param":np.ones(len(x))*k})
             )
        self._model.data_user =pd.concat(df_list)
        
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10) # Espace entre chaque bloc de plot
        
        self.plot_units = []
        
        # Initialisation dynamique des N plots
        for _ in range(num_plots):
            unit = PlotUnit(model=self._model, parent = parent)
            self.main_layout.addWidget(unit)
            self.plot_units.append(unit)

        self.update_all_plots()
            
    def update_all_plots(self):
        for unit in self.plot_units:
            unit.update_column_menus()
            unit.refresh_plot()

class PlotUnit(QWidget):
    _pause_refresh = False
    control_variables = ["X", "Y", "color"]
    _symbols = "ostd+"*2
    _colors= [
        (46, 204, 113),   # Emerald Green (Mint)
        (255, 127, 80),   # Coral (Soft Orange)
        (93, 173, 226),   # Steel Blue (Sky Blue)
        (175, 122, 197),  # Amethyst (Soft Purple)
        (244, 208, 63),   # Gold (Corn Yellow)
        (231, 76, 60),    # Alizarin Red (Soft Red)
        (26, 188, 156),   # Turquoise (Teal)
        (236, 240, 241)   # Clouds (Off-white/Light Grey)
    ]
    _size_marker = 4
    _cmap = pg.colormap.get('CET-L19') # https://colorcet.com/gallery.html (do not put the "0" if you put CET-L5)
    def __init__(self, model, parent):
        super().__init__(parent)
        self._model = model 
        self.log = self._model.log

        # --- Layout Principal (Vertical) ---
        self.main_layout = QVBoxLayout(self)


        # 1. Le Graphique
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('k') # Fond noir classique
        self.curve = self.plot_widget.plot(pen='y') # Ligne jaune par défaut
        self.main_layout.addWidget(self.plot_widget, stretch=1) # Prend tout l'espace

        self.grid_layout = QGridLayout()

        self.control_layout={}
        for i, x in enumerate(self.control_variables):
            lab= QLabel(f"{x}:")
            combo=QComboBox()
            combo.currentIndexChanged.connect(self._callback_on_UI_changed)
            self.control_layout[x]={
                "label":lab,
                "combo":combo
            }
            self.grid_layout.addWidget(lab, i, 0)
            self.grid_layout.addWidget(combo, i, 1)

        # Set the grid strectching 
        self.grid_layout.setColumnStretch(0, 1) 
        self.grid_layout.setColumnStretch(1, 4)

        self.main_layout.addLayout(self.grid_layout)
        self.update_column_menus()
        self.refresh_plot()


        ## TO DELETE
        cols = ["sin", "XX", "exp", "x2", "sinc"]
        self.control_layout["X"]["combo"].setCurrentText("XX")
        self.control_layout["Y"]["combo"].setCurrentText(cols[random.randint(0, 4)])
        self.control_layout["color"]["combo"].setCurrentText("param")

        
        

    def update_column_menus(self):
        """Update the QCombo list where we chose """
        # We check if the list of possible variables changed since last update.
        self._pause_refresh = True
        var = self.control_variables[0]
        combo = self.control_layout[var]["combo"]
        liste_items = [combo.itemText(i) for i in range(combo.count())]
        data_cols =["None"]+ list(self._model.data_user.columns)
        if  liste_items == data_cols:
            self._pause_refresh = False
            return
        # self.log.info("Updating the columns {}")
        for i, var in enumerate(self.control_variables):
            combo = self.control_layout[var]["combo"]
            previous_column = combo.currentText()
            combo.clear()
            combo.addItems(data_cols)
            ## Set the previous one
            if previous_column in data_cols:
                combo.setCurrentText(previous_column)
        self._pause_refresh = False
    
    def _callback_on_UI_changed(self):
        self.plot_widget.enableAutoRange(axis='xy', enable=True)
        self.refresh_plot

    def refresh_plot(self):
        """Méthode appelée par le timer de l'application principale."""
        ## this condition allow not to refresh the plot during the time we update the column menue
        if self._pause_refresh:
            return
        df = self._model.data_user

        # On récupère les noms des colonnes choisies par l'utilisateur
        col_x = self.control_layout["X"]["combo"].currentText()
        col_y = self.control_layout["Y"]["combo"].currentText()
        
        if not (col_x in df.columns and col_y in df.columns):
            return
        plot_by = self.control_layout["color"]["combo"].currentText()
        
        if plot_by == "None":
            num_of_plots=1
        else:
            if not plot_by in df.columns:
                return
            num_of_plots = len(df[plot_by].unique())
        self.plot_widget.clear()
        if num_of_plots ==1: #Simple plot in yellow
            x_vals = df[col_x].values
            y_vals = df[col_y].values
            # Mise à jour de la courbe
            self.plot_widget.clear()
            curve = self.plot_widget.plot(pen=pg.mkPen("y"),
                                          symbol='o', 
                                          symbolSize=self._size_marker,
                                          symbolBrush=('y')) 
            curve.setData(x_vals, y_vals)
        elif num_of_plots < 9:# We do a plot by by looping over different values of 
            self.legend=self.plot_widget.addLegend()
            # self.legend.setBrush(pg.mkBrush(255, 255, 255, 20)) # Semi-transparent background
            # self.legend.setPen(pg.mkPen(200, 200, 200, 100))   # Subtle border
            for i, value in enumerate(df[plot_by].unique()):
                df1 = df[df[plot_by]==value]
                curve = self.plot_widget.plot(pen=pg.mkPen(self._colors[i] ),
                                          symbol=self._symbols[i], 
                                          symbolSize=self._size_marker,
                                          symbolBrush=(self._colors[i]), name = str(value)) 
                
                curve.setData(df1[col_x].values, df1[col_y].values)
        else : #hue type plot
            hue_values = df[plot_by].values
            #normalize data for maping
            v_min, v_max = hue_values.min(), hue_values.max()
            if v_max > v_min:
                norm_data = (hue_values - v_min) / (v_max - v_min)
            else:
                norm_data = np.zeros_like(hue_values)
            colors = self._cmap.map(norm_data, mode=self._cmap.BYTE)
            curve = pg.ScatterPlotItem(size=self._size_marker, pen=None)
            self.plot_widget.addItem(curve)
            x_vals = df[col_x].values
            y_vals = df[col_y].values
            curve.setData(x_vals, y_vals, brush=colors)

