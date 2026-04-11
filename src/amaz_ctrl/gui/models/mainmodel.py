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
Content of mainmodel.py

This file implement the model of the application.  It only needs a json dictionary file path to start. 

'''


import os

# mport traceback
import logging
# import snoop
from pathlib import Path
from os.path import expanduser


from amaz_ctrl.tools.amaz_logs import set_console_log
from amaz_ctrl.gui.models.parameter import Parameter
from amaz_ctrl.gui.models.server_connector import LogServerConnector, DataServerConnector, ScriptServerConnector
import json



class Model():
    """Main model of the app.

    Holds the data and threads.

    The following objects are the most importants

    From the config file :
    _parameter_path : string
        is the path to the json file where we store the experiment parameters
    _def_scan_path : string
        same but for the default scanning parameters. If it does not exist, it will create it.
    _tab_name_list : the list of subscript that will be display

    Built-in variables :
    _exp_params_dictionary : dic
        it is the content of the json file uploaded from _parameter_path. It is
        build using the method json.load (--> we do not use here the method using
        qunits because we want to keep the quantities as string. Once we load the json file,
        we flatten the dictionary with the _delimiter (chosen here as ' | '
        for readibility purpose). We use the keys of THIS dictionary and every
        object in the GUI is pointed using the key from this flatten dictionary.
    _default_scan_dic : dic
        uploaded from _def_scan_path. Each key is map to keys of _exp_params_dictionary. It is
        the default scan dictionry. Each key contains  scan_start, scan_stop, scan_steps
        and units --> To be changed ?
    _keys : list
        list of keys of _exp_params_dictionary and _default_scan_dic
    _tab_keys : dictionary of list
        for all ellement of subscript list, we give a list of keys that are in this tab

    _parameter_dic : dic
        The keys of this dictionay map to the _keys list.
        The value of each key is a Parameter object whose properties are
            key : string
                "path to the parameter in the json file"
            short_name : string
                what will be printed in the tab. It is often the key minus the subscript.
            value: qunits quantity or Boolean
                the value of the parameter in the json file
             scan_start, scan_stop, scan_steps : float
                start, end and number of steps for the scan
             tab : string
                in which tab we diplay the parameter

    """
    default_parameter= {
        "HALname" : "None",
        "display" : "%.2f",
        "saved" : False,
        "start" : 0,
        "steps" : 10,
        "stop" : 9,
        "unit" : "dimensionless",
    }
    _tab_name_list = ["laser", "oscilloscope", "spectrum analyzer"]
    default_tab = "Other"
    
    def __init__(self,exp_param_directory:str, 
                 script_server_address = "PYRO:script.server@localhost:9090",
                 data_server_addresses = ["PYRO:script.server@localhost:9090"],
                 log_server_addresses=["PYRO:script.server@localhost:9090"],
                 log_level="INFO", 
                 logger_name="GUI"):
        """_summary_

        Parameters
        ----------
        exp_param_directory : str
            _description_
        script_server_address : str, optional
            _description_, by default "PYRO:script.server@localhost:9090"
        data_server_addresses : list, optional
            _description_, by default ["PYRO:script.server@localhost:9090"]
        log_server_addresses : list, optional
            _description_, by default ["PYRO:script.server@localhost:9090"]
        log_level : str, optional
            _description_, by default "INFO"
        logger_name : str, optional
            _description_, by default "GUI"
        """
        
        ##-. Set up log properties
        self.logger_name = logger_name
        self.log = logging.getLogger(self.logger_name)
        self.exp_par_directory = exp_param_directory
        self._log_level = log_level
        set_console_log(self.logger_name, log_level = self._log_level)

        ##-. Set up parameters properties
        self._parameter_path =os.path.join(exp_param_directory, "exp_params.json")
        self._def_scan_path =os.path.join(os.path.dirname(__file__), ".cached_scan_params.json")
        self._scan_path = os.path.join(exp_param_directory, "scanned_params.json")

        self._delimiter = " | "
        self._generate_and_load()

        ##-. Set up the connection to Pyro servers
        self.server_logs_dict ={uri:LogServerConnector(uri, log = self.log) for uri in log_server_addresses}
        self.server_data_dict ={uri:DataServerConnector(uri,log = self.log) for uri in data_server_addresses}
        self.server_script_connector = ScriptServerConnector(script_server_address, 
                                                             log = self.log, 
                                                             dead_time=.3)

    @property
    def keys(self):
        return self._keys

    @property
    def delimiter(self):
        return self._delimiter

    @property
    def parameter_dic(self):
        return self._parameter_dic

    @property
    def tab_keys_list(self):
        return self._tab_keys

    @property
    def tabs(self):
        return list(self._tab_keys.keys())

    def _generate_and_load(self):
        self._load_exp_params()
        self._load_default_scan_dictionary()
        self._generate_parameters()
        self._keys = list(self._exp_params_dictionary.keys())
        self._generate_tab_keys()

    
    def _generate_parameters(self):
        """
        This function generates the dictionary that contains all parameters objects.
        Each object is from the Parameter class defined in the parameters.py file.
        """
        self._parameter_dic = {}
        for key, value in self._exp_params_dictionary.items():
            parameter = Parameter(
                key = key,
                value = value,
                scan_dict = self._default_scan_dic,
                log = self.log
            )
            ## generate the tab and the short name for each parameter 
            parameter.set_tab_and_name(self._tab_name_list)
            self._parameter_dic[key] = parameter

    def _generate_tab_keys(self):
        """
        Generates the _tab_keys dictionary in which we store where we store each key in the given dictionary. We will loop over this dictionary to create all items in the parameter widget.  
        Exemple:
        --------
        self._tab_keys = {
        'laser': ['laser 2ph detuning (MHz)', 'laser 1ph detuning (MHz)',...]
        'spectrum analyzer': ['spectrum analyzer Carlos freq central (MHz)', ...],
        'Other': []
        }
        """
        self._tab_keys = {}
        for element in self._tab_name_list:
            self._tab_keys[element] = []
        self._tab_keys[self.default_tab] = []
        for key, parameter in self._parameter_dic.items():
            tab = parameter.tab
            self._tab_keys[tab].append(key)


    ####################
    ## FUNCTIONS THAT DEAL WITH THE PARAMETER DICTIONARY SEQ_PAR_FLATTEN AND SEQ_PAR_UNFLATTEN
    ####################
    def _update_exp_params_dictionary(self):
        """
        Updates the dictionary from the values that were registered in the dictionary of Parameters objected. These objects were updated by the user using the GUI.
        """
        self._exp_params_dictionary = {}
        for key, parameter in self._parameter_dic.items():
            self._exp_params_dictionary[key] = parameter.value

    def _update_scan_dictionaries(self):
        """
        Updates the two scan dictionaries :
        the _default_scan_dic with the default values to scan the parameters
        the _parameters_to_be_scan dictionary with the parameters to be scan
        """
        self._default_scan_dic = {}
        self._parameters_to_be_scan = {}
        self._parameters_to_be_saved = {}
        for key, parameter in self._parameter_dic.items():
            self._default_scan_dic[key] = {}
            self._default_scan_dic[key]["start"] = parameter.scan_start
            self._default_scan_dic[key]["stop"] = parameter.scan_stop
            self._default_scan_dic[key]["steps"] = parameter.scan_steps
            if parameter.scanned:
                self._parameters_to_be_scan[key] = {}
                self._parameters_to_be_scan[key]["start"] = parameter.scan_start
                self._parameters_to_be_scan[key]["stop"] = parameter.scan_stop
                self._parameters_to_be_scan[key]["steps"] = parameter.scan_steps

    def _load_exp_params(self):
        """this function loads all experiment parameters from the json file.

        It maps after the _seq_par_unflat dictionay
        to the _seq_par_flat using the flatten_dic library.
        For exemple, if the dictionary is
        {"AOM": {"freq":100, "power":3}}
        the flatten method will transform it into
        {"AOM | freq":100, "AOM | power":3}
        where " | " is self._delimiter.
        If the dictionnary is already flattened, it does nothing. 
        """
        try:
            with open(self._parameter_path, "r") as file:
                self._exp_params_dictionary = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("The experiment parameter file was not found. Please instanciate the Model of the Amazing Control Application with the directory in which a exp_param.json file exists.")

    def _save_exp_params(self):
        """Save the experiment parameters to disk"""
        self._update_exp_params_dictionary()
        with open(self._parameter_path, "w", encoding="utf-8") as file:
            json.dump(self._exp_params_dictionary, file, ensure_ascii=False, indent=4)

    def _load_default_scan_dictionary(self):
        """loads the scan parameters.  Each key of the dictionary should map to a key of
        _exp_params_dictionary and contains the default value for the scan i.e. start,
         stop, step and it units.
         "AOM | freq":{"start": 90, "stop":105, "steps":10, "units": "MHz"}
        """
        if os.path.isfile(self._def_scan_path):
            with open(self._def_scan_path, "r") as file:
                self._default_scan_dic = json.load(file)
        else:
            self._default_scan_dic = {}
        self._parameters_to_be_scan = {}

    def _save_default_scan_dictionary(self):
        """Save the default scan dictionary and the scan dictionary to disk"""
        self._update_scan_dictionaries()
        with open(self._def_scan_path, "w", encoding="utf-8") as file:
            json.dump(self._default_scan_dic, file, ensure_ascii=False, indent=4)
        with open(self._scan_path, "w", encoding="utf-8") as file:
            json.dump(self._parameters_to_be_scan, file, ensure_ascii=False, indent=4)

    def save(self):
        """
        Callback method when the user selects "Save" in the menubar or use "Ctrl+S".
        """
        self._save_exp_params()
        self._save_default_scan_dictionary()

    def get_logs(self):
        log_list =[]
        for uri, server_log_connector in self.server_logs_dict.items():
            log_list+=server_log_connector.get_logs()
        return log_list