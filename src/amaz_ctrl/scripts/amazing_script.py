#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Created on the Mon Mar 30 2026 by Victor
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
Content of amazing_script.py

Please document your code ;-).

'''

import os

class AmazingScript():
    def __init__(self, 
                 exp_params_directory:str,
                 data_directory:str):
        self.exp_params_directory = exp_params_directory
        self.data_directory = data_directory
        
    def check_data_dir(self):
        """check that the data directory does exist."""
        if not os.path.exists(self.data_directory):
            raise FileNotFoundError(f"The data directory {self.data_directory} does not exists. Please provide a base data directory which exists.")
        if not os.path.isdir(self.data_directory):
            raise TypeError(f"The data directory {self.data_directory} is not a directorys. Please provide a correct base data directory. The data directory is the root of the tree DATA_DIR/YYYY/MM/DD/SEQ in which we store the sequence.")








