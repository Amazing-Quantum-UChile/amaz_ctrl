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
Content of about.py

Hmmm.... this is a nice eastern egg ;-).
'''
from PyQt5 import QtCore, QtGui, QtWidgets

import random, os
from datetime import datetime


class AboutDialog(QtWidgets.QDialog):

    about_data=[{
        "txt":"Nuestro objetivo es desarrollar en Chile ciencia de excelencia en óptica cuántica, tanto teórica como experimental, siempre valorando el disfrute y la pasión por hacer ciencia. Creemos firmemente en la importancia de construir un equipo de trabajo saludable, colaborativo y equilibrado, donde cada integrante pueda crecer profesional y personalmente. Nuestro lema lo refleja claramente: Avanzar lento pero seguro, llegar lejos y, sobre todo, hacerlo con alegría y satisfacción.",
        "img":"group_valpo.jpeg",
        "title":"the team"},
        {"txt": "Carla Hermann Avigliano realizó su doctorado en Óptica Cuántica Experimental en el equipo de Serge Haroche, Premio Nobel de Física 2012, en la Université Pierre et Marie Curie. En forma paralela, realizó un doctorado en la Universidad de Concepción, bajo la supervisión del profesor Carlos Saavedra Rubilar, actual Rector de dicha casa de estudios (2018-2026). Realizó un postdoctorado en el Instituto Joint Quantum, Universidad de Maryland - NIST. En 2017, realizó un segundo postdoctorado en la Universidad de Chile, donde a partir del 2018 es profesora asistente del Departamento de Física de la Facultad de Ciencias Físicas y Matemáticas. Desde el 2022, es investigadora asociada del Instituto Milenio de investigación en óptica, y lidera varios proyectos de investigación.",
        "title":"Carla",
        "img":"carla.jpg",
 },
 {"txt":"El rubidio es un elemento químico fascinante que se encuentra principalmente oculto dentro de minerales como la lepidolita, ya que no existe en estado puro en la naturaleza debido a su extrema reactividad. Para extraerlo, primero se tritura el mineral hasta convertirlo en polvo y se somete a procesos químicos complejos de disolución ácida. Como el rubidio es químicamente muy similar al potasio y al cesio, los científicos deben realizar una separación fraccionada muy meticulosa para poder aislarlo. Finalmente, se obtiene el metal puro mediante una reducción térmica en condiciones de vacío absoluto, lo que permite conservar este material plateado que, al contacto con el agua, reacciona de manera explosiva. Su uso es vital en tecnologías modernas como los relojes atómicos y sistemas de navegación GPS, convirtiéndolo en un componente esencial para la ciencia actual.",
  "img":"lepidolite.png",
  "title":"Rubidium"}
    ]
    def __init__(self, parent, model):
        super().__init__(parent)

        self._model = model
        
        i = random.randint(0, len(self.about_data)-1)
        self.name = self.about_data[i]["title"]
        self.picture_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "img",
                                         self.about_data[i]["img"])
        self.txt = self.about_data[i]["txt"]

        self._initialize_ui()
        self.adjustSize()


    def _create_label(
        self, text, font_type="Sans", font_size=None, bold=False, italic=False
    ):
        label = qt.QtWidgets.QLabel(text, parent=self)

        font = qt.QtGui.QFont(font_type)
        font.setBold(bold)
        font.setItalic(italic)
        if font_size is not None:
            font.setPointSize(font_size)
        label.setFont(font)
        return label

    def _initialize_ui(self):
        self.setWindowTitle("About {}".format(self.name))
        self.setMinimumSize(480, 0)
        # 1. Main layout
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 2. Picture on the left
        self.image_label = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap(self.picture_path) 
        pixmap.setDevicePixelRatio(3.0)
        # On redimensionne l'image pour qu'elle ne casse pas le layout
        self.image_label.setPixmap(pixmap.scaled(1300, 1300, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        main_layout.addWidget(self.image_label)

        self.text_label = QtWidgets.QLabel()
       
        color = "#DFD6F1"
        html_content=f"""
        <div style="color:{color};">
        <span style="font-family: 'Font Awesome 5 Free'; font-weight: 900; font-size: 50px; color: {color};">
                
                    &#xf10d;
                </span>
            <div style="text-align: center;">
                <p>{self.txt}</p>
            </div>
             <div style="text-align: right;">
                  <span style="font-family: 'Font Awesome 5 Free'; font-weight: 900; font-size: 50px; color: {color};">
                    &#xf10e;
                </span>
         </div>
    <br><br><br><br>
        © {datetime.now().year} Amazing Quantum Laboratory - Todos los derechos reservados
         </div>
        """
        self.text_label.setText(html_content)
        self.text_label.setAlignment(QtCore.Qt.AlignVCenter)
        self.text_label.setWordWrap(True) 
        self.text_label.setAlignment(QtCore.Qt.AlignTop)
        main_layout.addWidget(self.text_label)


