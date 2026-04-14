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

"""
Content of parameter.py

This file contains the most important object of the model : it contains all
the parameter properties
"""
import logging




class Parameter(object):
    """This class holds all datas of one parameter

    Parameters
    ----------
    key : string
        "the key of your parameter in the json file"
    value: float, int, str, boolean
        the value of the parameter in the json file
    scan_dict: dict
        the dictionary of default scan parameters. Example:
       { "laser 2ph detuning (MHz)": {"start": 0.0, "stop": 9.0, "steps": 10},
         "laser 1ph detuning (MHz)": {"start": 0.0, "stop": 9.0, "steps": 10},
         "laser locking transition": {"start": 0.0, "stop": 0.0, "steps": 0}, 
         ... }
    log: logging.Logger
        the log on which displays logs.
    """
    _scan_start=0.
    _scan_stop = 9
    _scan_steps = 10
    _to_hal=False
    _hal_display="%.2f"
    _scanned=False
    _tab = "Other"
    _can_be_scanned = False
    def __init__(
        self,
        key:str,
        value,
        scan_dict:dict,
        log:logging.Logger
    ):
        self._key = key
        self._short_name = key
        self._value = value
        self._type = type(value)
        self._scan_dict = scan_dict
        self.log = log
        self.update_attributes_from_scan_parameter()
       
            
        

    @property
    def key(self):
        return self._key

    @property
    def value(self):
        return self._value

    @property
    def unit(self):
        return self._unit

    @property
    def scan_start(self):
        return self._scan_start

    @property
    def scan_stop(self):
        return self._scan_stop

    @property
    def scan_steps(self):
        return self._scan_steps

    @property
    def tab(self):
        return self._tab

    @property
    def short_name(self):
        return self._short_name

    @property
    def scanned(self):
        return self._scanned

    @property
    def type(self):
        return self._type

    def set_key(self, val):
        self._key = val

    def set_tab(self, val):
        self._tab = val

    def set_value(self, val):
        try:
            if self._type == str:
                self._value = val
            elif self._type == float:
                self._value = float(val)
            elif self._type == int:
                ## we check if the integers value is equal to the float value
                try:
                    self._value = int(val)
                except ValueError:
                    self.log.warning(f"The new value of the parameter {self.key} seems to be a float {val} while the typo of this parameter was an integer. Changing type to float.")
                    self._value = float(val)
                    self._type=float
            elif self._type == bool:
                if type(val) == bool:
                    self._value = val
                elif val in ["True", "true", "yes", "Yes", "si", "Si"]:
                    self._value = True
                elif val in ["False", "false", "no", "No"]:
                    self._value = False
                else:
                    self.log.error(
                        "{} can not be set as {} : it is not a boolean".format(
                            self._key, val
                        )
                    )
        except ValueError:
            self.log.error(f"The value '{val}' you aim to store in parameter '{self.key}' does not match its type ({self._type.__name__}).")


    def set_scan_start(self, val:float):
        """sets the initial value of the scan of the parameter

        Parameters
        ----------
        val : float
            the initial value for the scan.
        """
        try:
            self._scan_start = float(val)
        except ValueError:
            self.log.error(f"The start value of a scan must be a number, not '{val}'. Start value of '{self.key}' not updated.")
    
    def get_step(self):
        if self.type == bool:
            return 1
        if not type(self.scan_steps) == int:
            self.log.error(f"The number of steps must be an integer my friend. Please modify for {self.key}.")
            return None
        if self.scan_steps < 2:
            self.log.warning(f"The number of steps for the scan of {key} is smaller than 2 (currently {parameter.scan_steps}). Note that the value of a parameter cannot be in a quantum superposition of {self.scan_start} and {self.scan_stop}.")
            return None
        try:
            dx =(self.scan_stop - self.scan_start)/(self.scan_steps-1)
            return dx
        except Exception as e:
            self.log.error(f"An unexpected error occured when requiring the number of steps for the scan of {self.key}, from {self.scan_start} to {self.scan_stop} with N={self.scan_steps}. Error is {type(e).__name__}:{e}.")
            
    def set_scan_stop(self, val:float):
        """sets the initial value of the scan of the parameter

        Parameters
        ----------
        val : float
            the final value for the scan.
        """
        try:
            self._scan_stop = float(val)
        except ValueError:
            self.log.error(f"The stop value of a scan must be a number, not '{val}'. Stop value of '{self.key}' not updated.")
        
    def set_scan_steps(self, val:int):
        """sets the number of steps for the scan of this parameter

        Parameters
        ----------
        val : int
            the number of steps for the scan
        """
        try:
            self._scan_steps = int(val)
        except ValueError:
            self.log.error(f"The number of steps value of a scan must be an integer, not '{val}'. Scan value of '{self.key}' not updated.")

    def set_short_name(self, val:str):
        """sets the short name of the parameter (name dispaid in the tab). 

        Parameters
        ----------
        val : str
            the short name of the parameter
        """
        self._short_name = val

    def set_scanned(self, val:bool):
        """sets if the parameter is scanned or not.

        Parameters
        ----------
        val : bool
            if the parameter is scanned
        """
        self._scanned = val

    def update_attributes_from_scan_parameter(self):
        self.set_scan_start(self._get_scan_parameters("start"))
        self.set_scan_stop(self._get_scan_parameters("stop"))
        self.set_scan_steps(self._get_scan_parameters("steps"))



    def _get_scan_parameters(self, key2="start"):
        """_summary_

        Parameters
        ----------
        key2 : str, optional
            _description_, by default "start"

        Returns
        -------
        _type_
            _description_
        """
        allowed_value = ['start', 'stop','steps']
        if key2 not in allowed_value:
            self.log.error(f"Error in the Parameter._get_scan_parameters() method of parameters.py. The key {key2} should be in {allowed_value}")
            return 0
        ## check that the parameters already exists in the dictionary. If not create it-
        if not (self.key in self._scan_dict):
            self._scan_dict[self.key] = {}

        if key2 in self._scan_dict[self.key]:
            return self._scan_dict[self.key][key2]
        else:
            self.log.info(
                "{} - {} scan parameters did not exist : setting to default".format(
                    self.key,  key2
                )
            )
            ## The default value is the value that was set
            default_val = Parameter.__dict__["_scan_"+key2]
            ## -. Update the scan dictionary
            self._scan_dict[self.key][key2] = default_val
            return default_val

    def set_tab_and_name(self, tab_list:list):
        """sets the tab and the short name of the parameter. Loop over the different elements of the tab_list and if it identifies if an element of the list match the beginning of the key. If it is the case, it attributes the tab name to the key and sets the short name as the key without the tab name.

        Exemples: if tab_list=["laser", "oscilloscope", ...]
        ---------
        key = "laser 2ph detuning (MHz)"
        -->    tab = "laser"
        -->    short_name = "2ph detuning (MHz)"
        
        if key = "oscilloscope Diego chC acquire"
        -->  tab = "oscilloscope" 
        -->  short_name = "Diego chC acquire"

        if key = "No of screw in the room"
        -->  tab = "Other"
        -->  short_name = "No of screw in the room"

        Parameters
        ----------
        key : str
            the key of the dictionary
        """
        for tab_name in tab_list:
            if tab_name==self.key[0:len(tab_name)]:
                short_name = self.key[len(tab_name):]
                ## remove the initial space
                while short_name[0]==" ":
                    short_name=short_name[1:]
                self.set_short_name(short_name)
                self.set_tab(tab_name)
                return
        return
    

