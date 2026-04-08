#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Created on the Mon Mar 30 2026 by Victor
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
Content of amazing_script.py

Please document your code ;-).

'''

import os, threading, logging, json, copy, collections
from datetime import datetime
from amaz_ctrl.tools.amaz_logs import set_console_log
from amaz_ctrl.tools.misc import ordinal
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
    _default_exp_params = {"No of realizations":100}
    _last_results = collections.deque(maxlen=200) 
    _sensors_are_connected = False
    _zero_time =datetime(2025, 1, 17, 14) ## the zero time of the quantum lab
    
    
    
    def __init__(self, 
                 exp_params_dir: str = None,
                 data_root_dir: str = None,
                 log_level="INFO"):
        self._script_fn =inspect.getfile(self.__class__)
        self._script_dir = os.path.dirname(os.path.abspath(self._script_fn))
        
        ## Set up logs
        LOG_NAME = "SCRIPT"
        self.log = logging.getLogger(LOG_NAME)
        set_console_log(logger_name = LOG_NAME, log_level=log_level)

        if exp_params_dir is None:
            exp_params_dir = self._script_dir
        if data_root_dir is None:
            data_root_dir = os.path.join(os.path.expanduser("~"),
                                          "AMAZING_DATA")
            self.log.info(f"Data directory was not given. Default data directory is {data_root_dir}.")
        self.exp_params_dir = exp_params_dir
        self.load_exp_param()

        self.data_root_dir = data_root_dir
        self._check_data_dir(self.data_root_dir)



    def load_exp_param(self):
        """load the exp_params dictionary to set replace the exp_params argument."""
        fpath = os.path.join(self.exp_params_dir, self._exp_param_fn)
        if not os.path.isfile(fpath):
            msg = f"The experiment parameter file does not exist. Either provide the path to the file in the initialisation or make sure a file '{self._exp_param_fn}' where you define your script."
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
                self.log.warning(f"{key} not in the exp_params dictionary. Setting it to its default value {val}")
                exp_params[key]= val
        ## Check that the number of realization per experiment is an int
        key = "No of realizations"
        val = exp_params[key] 
        if type(val) != int:
            self.log.warning(f"The type of {key} is not an integers. Setting it to integer.")
            try:
                exp_params[key] = int(val)
            except ValueError:
                def_val = self._default_exp_params[key]
                self.log.error(f"Failed to convert to int the {key}. Setting it to the default value {def_val}.")
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
            self.log.info(f"The data directory {data_dir} does not exist. We create it.")
            os.makedirs(data_dir, exist_ok=True)
            return
        if not os.path.isdir(data_dir):
            raise TypeError(f"The data directory {data_dir} is not a directory. Please provide a correct base data directory. The data directory is the root of the tree DATA_DIR/YYYY/MM/DD/SEQ in which we store the sequence.")


    def start_sequence(self):
        self.stop_event.clear()
        time_start_seq = datetime.now()
        self.create_sequence_folder()
        scanned_params_dict = self.load_scanned_parameters()
        list_of_experiments = self.build_experiment_list(scanned_params_dict)
        self.on_sequence_about_to_start()
        for i_exp in range(len(list_of_experiments)):
            if self.stop_event.is_set(): 
                break
            ## We update the experiment parameter dictiowith the scanned parameters
            self.log.info(f"Starting the {ordinal(i_exp+1)} experiment out of {len(list_of_experiments)} of sequence {self.seq_number}.")
            self.start_experiment(i_exp=i_exp)
        self.on_sequence_about_to_end()
        if self.stop_event.is_set():
            status = "stopped"
        else: status = "finished"
        duration = datetime.now() - time_start_seq
        minutes, seconds = divmod(int(duration.total_seconds()), 60)
        self.log.info(f"Sequence {self.seq_number} {status} after {minutes}min {seconds}s.")



    def start_experiment(self, i_exp):
        self.i_exp = i_exp
        
        self.prepare_experiment()
        self.on_experiment_about_to_start()
        self.connect_sensors()
        self._sensors_are_connected = True
        ## Set the ID of the Experiment 
        now = datetime.now()
        
        exp_id = round((now - self._zero_time).total_seconds(), 2)
        for j_run in range(self.exp_params["No of realizations"]):
            if self.stop_event.is_set(): 
                break
            ## Define run ID, time since epoch rounding in 10 ms
            now = datetime.now()
            run_id = round((now - self._zero_time).total_seconds(), 2)
            self.j_run = j_run
            
            run_result = self.acquire()
            if type(run_result)!=dict:
                msg="TypeError: The method acquire of the Script {name} does not " \
                "return a dictionary. ".format(name=self._script_fn)+self._script_require_info
                self.log.error(msg)
                self.log.error("The method of ")
            run_result["Run No"] = j_run
            run_result["Run ID"] = run_id
            run_result["Exp No"] = i_exp
            run_result["Exp ID"] = exp_id
            run_result["Seq No"] = self.seq_number
            run_result["Seq ID"] = self.seq_id
        self.disconnect_sensors()
        self._sensors_are_connected = False
        self.on_experiment_about_to_end()

    def load_scanned_parameters(self)->dict:
        """load the scanned_parameter dictionary."""
        try:
            fpath = os.path.join(self.exp_params_dir, self._scanned_param_fn)
            if not os.path.isfile(fpath):
                msg = f"The experiment parameter file does not exist. Either provide the path to the file in the initialisation or make sure a file '{self._scanned_param_fn}' where you define your script."
            with open(fpath, 'r', encoding='utf-8') as file:
                scanned_params_dict = json.load(file)
            return scanned_params_dict
        except:
            msg = "[AmazingScript.load_scanned_parameters] Loading the scanned parameter dictionary failed. Setting it to empty dictionary."
            self.log.error(msg)
            return  {}

    def build_experiment_list(self,scanned_params_dict, scanned_params_dic={})->list:
        if not scanned_params_dict:
            return [{}]
        else:
            return [{}]
            



    def save_experiment(self, ):
        pas 

    def load_scan_parameters(self):
        fpath = os.path.join(self.exp_params_dir, self._scanned_param_fn)

    def stop_acquisition(self):
        self.log.info("Request to stop the experiment...")
        self.stop_event.set()

    def create_sequence_folder(self):
        """creates the sequence folder. The sequence folder is a string of an integer i.e. '005' if this is the fifvth sequence of the day.
        The base directory is the data_root_dir argument passed to the AmazingScript class.

        Directory strucure:
        BASE_DIR/YYYY/MM/DD
                        |- 001
                        |- 002
                        ...
                        |- 008
        """
        now = datetime.now()
        ## Sequence ID is defined as the time since the Amazing lab inauguration (in seconds)
        self.seq_id = int((now - self._zero_time).total_seconds())
        day_dir = os.path.join(self.data_root_dir, 
                               now.strftime("%Y"),
                               now.strftime("%m"),
                               now.strftime("%d"))
        os.makedirs(day_dir, exist_ok=True)
        ## We now list all folders of the day to check the number of the 
        # last sequence and set it to the new one
        day_dir_elements = os.listdir(day_dir)
        directories = [elem for elem in day_dir_elements if os.path.isdir(os.path.join(day_dir,elem))]
        
        if not directories:
            self.seq_number = 1
        else: ##we try to find what is the last 
            directories.sort(reverse=True)
            last_seq_number = False ## we use that as a boolean
            for dir in directories:
                last_seq_num = dir
                try:
                    last_seq_num=int(last_seq_num)
                except ValueError:
                    pass
                if type(last_seq_num)==int:
                    self.seq_number = last_seq_num+1
                    break

        ## Last: we check that the directory does not exist yet
        sequence_directory = f"{self.seq_number:03}"
        while sequence_directory in day_dir_elements:
            self.seq_number +=1
            sequence_directory = f"{self.seq_number:03}"
        ## Set seq_dir to total path:
        self.seq_dir = os.path.join(day_dir, f"{self.seq_number:03}")
        self.log.info(f"Sequence directory created in {self.seq_dir}")
        os.makedirs(self.seq_dir, exist_ok=True)


    ###############################################################
    ######## FUNCTIONS TO BE REDEFINED IN DAUGHTER CLASS ##########
    ###############################################################
    def prepare_experiment(self):
        msg="AttributeError: The Script {name} does not have a " \
        "'prepare_experiment' method. ".format(name=inspect.getfile(self.__class__))+self._script_require_info
        self.log.error(msg)
        # raise AttributeError(msg)

    def connect_sensors(self):
        msg="AttributeError: The Script {name} does not have a " \
        "'connect_sensors' method. ".format(name=self._script_fn)+self._script_require_info
        self.log.error(msg)
        # raise AttributeError(msg)
    
    def disconnect_sensors(self):
        msg="AttributeError: The Script {name} does not have a " \
        "'disconnect_sensors' method. ".format(name=self._script_fn)+self._script_require_info
        self.log.error(msg)
        # raise AttributeError(msg)

    def acquire(self)->dict:
        msg="AttributeError: The Script {name} does not have a " \
        "'acquire' method. ".format(name=self._script_fn)+self._script_require_info
        self.log.error(msg)
        # raise AttributeError(msg)
    
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


if __name__ == "__main__":
    script = AmazingScript(exp_params_dir='/Users/victor/amaz_ctrl/src/amaz_ctrl/scripts')
    script.start_sequence()


