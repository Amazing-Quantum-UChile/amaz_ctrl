#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Created on the Sat Apr 04 2026 by Victor
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
Content of simple_script.py

Please document your code ;-).

'''


import threading
import time
class Script:
    pomme = 100000
    e=1
    stop_event = threading.Event() 
    
    
    def set_parameters(self):
        pass

    
    def start_sequence(self):
        print("Starting the acquistion.")
        self.load_parameters()
        no_of_exp = 3
        for i_exp in range(no_of_exp):
            if self.stop_event.is_set(): 
                break 
            print(f"Starting experiment {i_exp}/{no_of_exp}")
            ## we change one parameter of the experiment 
            self._exp_params["X"] = i_exp
            self.start_experiment(i_exp)

    def start_experiment(self, i_exp):
        experiment_results=[]
        for j_run in range(30):
            ## We break if the event flag is raise
            if self.stop_event.is_set(): 
                break 
            result = self.aquire()
            experiment_results.append(result)

    def load_parameters(self):
        self._exp_params = {"X":1, "Y":2, "Z":3}

    def aquire(self)->dict:
        ## We simulate here a long data aquisition
        time.sleep(1)
        res = {"result 1":self._exp_params["X"]**2,
               "result 2":self._exp_params["X"]*1.5+self._exp_params["Y"]}






