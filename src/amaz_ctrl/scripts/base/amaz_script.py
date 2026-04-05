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

import os, threading, logging, json, copy, collections
log = logging.getLogger("SCRIPT")

import inspect


class AmazingScript():
    stop_event = threading.Event() 
    _home = os.path.expanduser("~")
    _exp_param_fn = "exp_params.json"
    _scanned_param_fn = "scanned_params.json"
    _script_require_info="\n[Additional information]: Any script that inherits the AmazingScript class requires the following methods. \n" \
    "(1) A prepare_experiment method that is called to prepare actuators and sensor devices. Note that in this method, we should connect and disconnect to all actuators and sensors.\n" \
    "(2) A connect_sensors method that is called before the acquire method. Sensors stay connected during all the acquisition process.\n" \
    "(3) An acquire method that is called at each realization of the experiment. This method should return a dictionary with the results of the realization.\n" \
    "(4) A disconnect_sensors method that is called once the sequence of experiments is finished or whenever the stop button is pushed."
    _default_exp_params = {"Experiment No of realizations":100}
    _last_results = collections.deque(maxlen=200) 
    
    
    def __init__(self, 
                 exp_params_dir: str = None,
                 data_root_dir: str = None):
        self._script_fn =inspect.getfile(self.__class__)
        self._script_dir = os.path.dirname(os.path.abspath(self._script_fn))
        if exp_params_dir is None:
            exp_params_dir = self._script_dir
        if data_root_dir is None:
            data_root_dir = os.path.join(os.path.expanduser("~"),
                                          "AMAZING_DATA")
            log.info(f"Data directory was not given. Default data directory is {data_root_dir}.")
        self.exp_params_dir = exp_params_dir
        self.load_exp_param()

        self.data_root_dir = data_root_dir
        self._check_data_dir(self.data_root_dir)


    def load_exp_param(self):
        """load the exp_params dictionary to set replace the exp_params argument."""
        fpath = os.path.join(self.exp_params_dir, self._exp_param_fn)
        if not os.path.isfile(fpath):
            msg = f"The experiment parameter file does not exist. Either provide the path to the file in the initialisation or make sure a file '{_exp_param_fn}' where you define your script."
        with open(fpath, 'r', encoding='utf-8') as file:
            exp_params = json.load(file)
        self.exp_params = self._check_exp_params(exp_params=exp_params)
        self._init_exp_params = copy.deepcopy(self.exp_params)


    def _check_exp_params(self, exp_params:dict)->dict:
        """verifies the exp_params dictionary does possess mandatory keys. Check also the type of important keys.

        Parameters
        ----------
        exp_params : dict
            dictionary that contains the experimental parameters

        Returns
        -------
        dict
            dictionary that contains the experimental parameters updated with mandatory parameters
        """
        for key, val in self._default_exp_params.items():
            if key not in exp_params.keys():
                log.warning(f"{key} not in the exp_params dictionary. Setting it to its default value {val}")
                exp_params[key]= val
        ## Check that the number of realization per experiment is an int
        key = "Experiment No of realizations"
        val = exp_params[key] 
        if type(val) != int:
            log.warning(f"The type of {key} is not an integers. Setting it to integer.")
            try:
                exp_params[key] = int(val)
            except ValueError:
                def_val = self._default_exp_params[key]
                log.error(f"Failed to convert to int the {key}. Setting it to the default value {def_val}.")
                exp_params[key]= def_val
        return exp_params

    def _check_data_dir(self, data_dir:str):
        """check that the data directory does exists.

        Parameters
        ----------
        data_dir : str
            data directory basename

        Raises
        ------
        TypeError
            In case of the data_directory is not a directory (i.e. a file)
        """
        if not os.path.exists(data_dir):
            log.info(f"The data directory {data_dir} does not exist. We create it.")
            os.makedirs(data_dir, exist_ok=True)
            return
        if not os.path.isdir(data_dir):
            raise TypeError(f"The data directory {data_dir} is not a directory. Please provide a correct base data directory. The data directory is the root of the tree DATA_DIR/YYYY/MM/DD/SEQ in which we store the sequence.")


    def start_acquisition(self):
        for i_exp in range(no_of_experiments):
            for j_run in range(self.exp_params["Experiment No of realizations"]):
                if 
    def save_experiment(self, ):
        pas 

    def stop_acquisition(self):
        self.stop_event.set()

    ###############################################################
    ######## FUNCTIONS TO BE REDEFINED IN DAUGHTER CLASS ##########
    ###############################################################
    def prepare_experiment(self):
        msg="AttributeError: The Script {name} does not have a " \
        "'prepare_experiment' method. ".format(name=inspect.getfile(self.__class__))+self._script_require_info
        
        log.error(msg)
        raise AttributeError(msg)

    def connect_sensors(self):
        msg="AttributeError: The Script {name} does not have a " \
        "'connect_sensors' method. ".format(name=self._script_fn)+self._script_require_info
        log.error(msg)
        raise AttributeError(msg)
    
    def disconnect_sensors(self):
        msg="AttributeError: The Script {name} does not have a " \
        "'disconnect_sensors' method. ".format(name=self._script_fn)+self._script_require_info
        log.error(msg)
        raise AttributeError(msg)

    def acquire(self)->dict:
        msg="AttributeError: The Script {name} does not have a " \
        "'acquire' method. ".format(name=self._script_fn)+self._script_require_info
        log.error(msg)
        raise AttributeError(msg)

# import Pyro5.api
# import time

# # Connexion au serveur
# remote_lab = Pyro5.api.Proxy("PYRO:my.lab@localhost:9090")

# print("--- Sending command to server ---")
# remote_lab.run_sequence(12.5)

# print("--- Checking logs from server ---")
# # On simule un petit rafraîchissement (ce que ferait ton QTimer)
# for _ in range(3):
#     messages = remote_lab.get_logs()
#     for m in messages:
#         print(f"SERVER LOG: {m}")
#     time.sleep(0.5)





