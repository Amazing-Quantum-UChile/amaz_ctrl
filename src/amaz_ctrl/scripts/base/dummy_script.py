#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Created on the Sun Apr 05 2026 by Victor
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
Content of dummy_script.py

This script is a dummy script that is used for testing.  
You can us it as a template but remember that by default, script should be put directlry in the script folder. In the testing folder, we have redefined the _path_to_scripts varible of the server so that we look into "amaz_ctrl.scripts.base" instead of "amaz_ctrl.scripts".
'''
from amaz_ctrl.scripts.base.amaz_script import AmazingScript
import time, os, logging
log = logging.getLogger("SCRIPT")



class Script(AmazingScript):
    def __init__(self,exp_params_dir: str = None,
                 data_root_dir: str = None,
                 log_level="INFO"):
        """Do not copy the initialisation function. Here we must redefine the experimental parameter file just because the locaiton of the dummy script is not standard. """
        exp_params_dir=os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
        super().__init__(exp_params_dir=exp_params_dir,
                         data_root_dir = data_root_dir,
                         log_level="INFO")

    def prepare_experiment(self):
        time.sleep(1)
        log.info("I just prepared the experiment!!")

    def connect_sensors(self):
        log.info("I am now connected to sensors...")
    
    def disconnect_sensors(self):
        log.info("... Disconnected !")


    def acquire(self)->dict:
        time.sleep(1)
        print("Acquired")
        result = {"Res1":1,
                  "Res2":20}
        return result
    
    def on_experiment_about_to_start(self):
        """method called before an experiment starts so that the user can do whatever they want at this stage."""
        pass

    def on_experiment_about_to_end(self):
        """method called before after an experiment finished so that the user can do whatever they want at this stage."""
        pass
    def on_sequence_about_to_start(self):
        """method called before a sequence of experiments starts so that the user can do whatever they want at this stage."""
        pass
    
    def on_sequence_about_to_end(self):
        """method called before after a sequence of experiments finished so that the user can do whatever they want at this stage."""
        pass



if __name__ == "__main__":
    script = Script(exp_params_dir='/Users/victor/amaz_ctrl/src/amaz_ctrl/scripts')
    script.start_sequence()

