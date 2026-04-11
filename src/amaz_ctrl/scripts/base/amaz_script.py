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

import os, threading, logging, json, copy, collections, shutil, random
from datetime import datetime
import itertools
import numpy as np
import pandas as pd
from amaz_ctrl.tools.amaz_logs import set_console_log
from amaz_ctrl.tools.misc import ordinal
log = logging.getLogger("SCRIPT")
from collections import ChainMap

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
    exp_folder = None
    _seq_number = None
    _seq_dir = None
    _i_exp = None
    
    
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
        self._exp_params_dir = exp_params_dir
        self.load_exp_param()

        self.data_root_dir = data_root_dir
        self._check_data_dir(self.data_root_dir)

    def main(self):
        self.start_sequence()

    def start_sequence(self):
        self.stop_event.clear()
        time_start_seq = datetime.now()
        #-. Load Data and experiment parameters
        self.load_exp_param() # update the experiment parameters
        scanned_params_dict = self.load_scanned_parameters()
        list_of_experiments = self.build_list_of_experiments(scanned_params_dict)

        #-. Create data directory and save current scripts
        self.create_sequence_folder()
        self.save_scripts()
        #-. Start sequence
        self._on_sequence_about_to_start()
        for i_exp, seq_update in enumerate(list_of_experiments):
            if self.stop_event.is_set(): 
                break
            ## We update the experiment parameter dictiowith the scanned parameters
            ## Copy the initial one and update it with the one of the new cycle
            self._exp_params = copy.deepcopy(self._init_exp_params)
            for key, elem in seq_update.items():
                self._exp_params[key]=elem
            self.log.info(f"Starting experiment {i_exp+1}/{len(list_of_experiments)} of sequence {self._seq_number}.")
            self.start_experiment(i_exp=i_exp)
        self.on_sequence_about_to_end()
        if self.stop_event.is_set():
            status = "stopped"
        else: status = "finished"
        duration = datetime.now() - time_start_seq
        minutes, seconds = divmod(int(duration.total_seconds()), 60)
        self.log.info(f"Sequence {self._seq_number} {status} after {minutes}min {seconds}s.")

    def start_experiment(self, i_exp):
        
        self._i_exp = i_exp
        self.exp_folder = self.create_experiment_folder()
        self._prepare_experiment()
        self._on_experiment_about_to_start()
        self._connect_sensors()
        self._sensors_are_connected = True
        ## Set the ID of the Experiment 
        now = datetime.now()
        exp_id = round((now - self._zero_time).total_seconds(), 2)
        run_result_list = []
        for j_run in range(self._exp_params["No of realizations"]):
            if self.stop_event.is_set(): 
                break
            ## Define run ID, time since epoch rounding in 10 ms
            now = datetime.now()
            run_id = round((now - self._zero_time).total_seconds(), 2)
            self.j_run = j_run
            run_result = self._acquire()
            run_result["Run No"] = j_run
            run_result["Run ID"] = run_id
            run_result["Exp No"] = i_exp
            run_result["Exp ID"] = exp_id
            run_result["Seq No"] = self._seq_number
            run_result["Seq ID"] = self.seq_id
            run_result["Time"] = now
            run_result_list.append(run_result)
        self.disconnect_sensors()
        self._sensors_are_connected = False
        self.experiment_result = pd.DataFrame(run_result_list)
        self._on_experiment_about_to_end()
        ## save results and exp. parameter
        self.experiment_result.to_csv(
            os.path.join(
                self.seq_directory,
                f"{i_exp:03}_result.csv" )
                )
        with open(os.path.join(
                self.seq_directory,
                f"{i_exp:03}_result.json"),
                  "w") as f:
            json.dump(self._exp_params, f, )
        
        self._i_exp, self.exp_folder = None, None

    
    

    def load_exp_param(self):
        """load the exp_params dictionary to set replace the exp_params argument."""
        fpath = os.path.join(self._exp_params_dir, self._exp_param_fn)
        if not os.path.isfile(fpath):
            msg = f"The experiment parameter file does not exist. Either provide the path to the file in the initialisation or make sure a file '{self._exp_param_fn}' where you define your script."
        with open(fpath, 'r', encoding='utf-8') as file:
            exp_params = json.load(file)
        self._exp_params = self._check_exp_params(exp_params=exp_params)
        self._init_exp_params = copy.deepcopy(self._exp_params)


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


    



    

    def load_scanned_parameters(self)->dict:
        """load the scanned_parameter dictionary."""
        try:
            fpath = os.path.join(self._exp_params_dir, self._scanned_param_fn)
            if not os.path.isfile(fpath):
                msg = f"The experiment parameter file does not exist. Either provide the path to the file in the initialisation or make sure a file '{self._scanned_param_fn}' where you define your script."
            with open(fpath, 'r', encoding='utf-8') as file:
                scanned_params_dict = json.load(file)
            return scanned_params_dict
        except:
            msg = "[AmazingScript.load_scanned_parameters] Loading the scanned parameter dictionary failed. Setting it to empty dictionary."
            self.log.error(msg)
            return  {}

    def build_list_of_experiments(self,scanned_params_dict, random_list = False)->list:
        if not scanned_params_dict:
            return [{}]
        else:
            # we build a list with all dictionaries
            product_list = []
            for key, dic in scanned_params_dict.items():
                values = np.linspace(dic["start"],
                dic["stop"],int(dic["steps"]))
                new_item = [{key:val} for val in values]
                product_list.append(new_item)
            all_list = list(itertools.product(*product_list))
            list_of_experiment = [dict(ChainMap(*t)) for t in all_list]
            if random_list:
                random.suffle(list_of_experiment)
            
            return list_of_experiment
            

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
            self._seq_number = 1
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
                    self._seq_number = last_seq_num+1
                    break

        ## Last: we check that the directory does not exist yet
        sequence_directory = f"{self._seq_number:03}"
        while sequence_directory in day_dir_elements:
            self._seq_number +=1
            sequence_directory = f"{self._seq_number:03}"
        ## Set seq_dir to total path:
        self._seq_dir = os.path.join(day_dir, f"{self._seq_number:03}")
        self.log.info(f"Sequence directory created in {self._seq_dir}")
        os.makedirs(self._seq_dir, exist_ok=True)

    def create_experiment_folder(self)->str:
        exp_folder = os.path.join(self._seq_dir,  f"{self._i_exp:03}")
        os.makedirs(exp_folder, exist_ok=True)
        return exp_folder

    def save_scripts(self):
        """this method copy and paste the elements of the script folder into the sequence folder so that the same experiment can be run again.
        
        Details:
        --------
        We copy the script file (self._script_fn), the experimental parameter files (e.g. exp_params.json, scanned_params.json) and the folders subscripts, base, into the the sequence directory self._seq_dir.
        """
        ## the script file
        backup_script_dir =  os.path.join(self._seq_dir,  "scripts")
        os.makedirs(backup_script_dir, exist_ok=True)
        # Copy the script file
        try:
            shutil.copy(src=self._script_fn, dst = backup_script_dir)
        except Exception as e:
                msg = "{t}: {e}. This exception was caught in the save_scripts " \
                "method while copying the file {fn} onto {backup_script_dir}. ".format(
                    t=type(e).__name__, 
                    e=e, 
                    fn=self._script_fn,
                    backup_script_dir=backup_script_dir
                    )
                self.log.warning(msg)

        for file in ["exp_params.json", "scanned_params.json" ]:
            try:
                 fn = os.path.join(self._exp_params_dir, file )
                 shutil.copy(src=fn, dst = backup_script_dir)
            except Exception as e:
                msg = "{t}: {e}. This exception was caught in the save_scripts " \
                "method while copying the file {fn} onto {backup_script_dir}. ".format(
                    t=type(e).__name__, 
                    e=e, 
                    fn=fn,
                    backup_script_dir=backup_script_dir
                    )
                self.log.warning(msg)
        self.log.info("Scripts files copied in the sequence directory.")

        # Copy the directories: subscripts, base
        for dir in ["base",  "subscripts"]:
            try:
                src_folder =os.path.join(self._script_dir, dir)
                shutil.copytree(src = src_folder, dst = os.path.join(backup_script_dir, dir ))
            except Exception as e:
                msg = "{t}: {e}. This exception was caught in the save_scripts " \
                "method while copying the folder {src_folder} onto {backup_script_dir}. ".format(
                    t=type(e).__name__, 
                    e=e, 
                    src_folder=src_folder,
                    backup_script_dir=backup_script_dir
                    )
                self.log.warning(msg)

        
    ####################################################
    ### PROPERTIES AND METHODS FOR THE SCRIPT CLASS ####
    ####################################################
    @property
    def seq_number(self)->int:
        return self._seq_number
    
    @property
    def exp_params(self)->dict:
        return self._exp_params
    
    def get_experimental_parameters(self)->dict:
        return self._exp_params
    
    @property
    def seq_directory(self):
        return self._seq_dir
    
    @property
    def exp_directory(self):
        return self._seq_dir
    
    ####################################################
    ### METHODS THAT CALL THE DAUGHTER CLASS METHODS ###
    ####################################################
    def _prepare_experiment(self):
        try:
            self.prepare_experiment()
        except Exception as e:
            msg=f"{type(e).__name__}:{e}. This error was caught in the prepare_experiment method of the Script {self._script_fn}."
            self.log.critical(msg)
            self.log.warning("Stopping the acquisition because of this critical error.")
            self.stop_acquisition()
            ## we raise the error to show the problem
            raise 

    def _acquire(self):
        try:
            run_result = self.acquire()
            if type(run_result)!=dict:
                msg="TypeError: The method acquire of the Script {name} does not " \
                "return a dictionary. ".format(name=self._script_fn)+self._script_require_info
                self.log.error(msg)
                run_result = {}
            return run_result
        except Exception as e:
            msg=f"{type(e).__name__}:{e}. This error was caught in the acquire method of the Script {self._script_fn}."
            self.log.critical(msg)
            return {}

    def _connect_sensors(self):
        try:
            self.connect_sensors()
        except Exception as e:
            msg=f"{type(e).__name__}:{e}. This error was caught in the connect_sensors method of the Script {self._script_fn}."
            self.log.error(msg)

    def _disconnect_sensors(self):
        try:
            self.disconnect_sensors()
        except Exception as e:
            msg=f"{type(e).__name__}:{e}. This error was caught in the disconnect_sensors method of the Script {self._script_fn}."
            self.log.error(msg)


    def _on_experiment_about_to_start(self):
        try:
            self.on_experiment_about_to_start()
        except Exception as e:
            msg=f"{type(e).__name__}:{e}. This error was caught in the on_experiment_about_to_start method of the Script {self._script_fn}."
            self.log.error(msg)

    def _on_experiment_about_to_end(self):
        try:
            self.on_experiment_about_to_end()
        except Exception as e:
            msg=f"{type(e).__name__}:{e}. This error was caught in the on_experiment_about_to_end method of the Script {self._script_fn}."
            self.log.error(msg)

    def _on_sequence_about_to_start(self):
        try:
            self.on_sequence_about_to_start()
        except Exception as e:
            msg=f"{type(e).__name__}:{e}. This error was caught in the on_sequence_about_to_start method of the Script {self._script_fn}."
            self.log.error(msg)

    def _on_sequence_about_to_end(self):
        try:
            self.on_sequence_about_to_end()
        except Exception as e:
            msg=f"{type(e).__name__}:{e}. This error was caught in the on_sequence_about_to_end method of the Script {self._script_fn}."
            self.log.error(msg)

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
    # script.main()


