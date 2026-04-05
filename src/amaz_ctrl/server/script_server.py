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
Content of script_server.py

Please document your code ;-).

'''
from amaz_ctrl.tools.amaz_exception import ExperimentIsRunning, ExperimentIsPreparing, NoScriptToRun
from amaz_ctrl.server.amaz_server import AmazingServer
import importlib, sys, time
import Pyro5.api
import traceback, logging

class ScriptServer(AmazingServer):
    _script_class = "Script" #the name of the class we import
    _path_to_scripts = "amaz_ctrl.scripts" #the path within the module of the script. 
    script = None
    current_module = None
    _thread_running = None
    _thread_setting_params = None
    _is_setting_parameters = False 
    _are_params_set = False
    _set_parameters_timeout = 30 #timeout before we terminate the function
    def __init__(self,
                 logger_name="SCRIPT_SERVER",
                 max_log=100,
                 log_level="INFO"
                 ):
        super().__init__(
            logger_name=logger_name, 
            max_log=max_log,
            log_level=log_level
            )
        self.set_up_log("SCRIPT")
    ###################################################################
    ########################  Private methods  ########################
    ###################################################################
    @property
    def is_setting_parameters(self)->bool:
        """returns wether the _thread_setting_params is alive or not, i.e. if we are setting parameters up."""
        return self._thread_setting_params is not None and self._thread_setting_params.is_alive()
    
    @property
    def is_running(self)->bool:
        """returns wether the _thread_running is alive or not, i.e. if an experiment is running."""
        return self._thread_running is not None and self._thread_running.is_alive()


    ###################################################################
    ####---------- PUBLIC METHODS EXPOSED TO PYRO SERVER ----------####
    #### these methods can be called by the server because of the  ####
    #### property @Pyro5.api.expose on top of them.                ####
    ###################################################################
    
    @Pyro5.api.expose
    def upload_script(self, script_name):
        """_summary_

        Parameters
        ----------
        script_name : _type_
            _description_
        """
        try:
            self._upload_script(script_name)
        except Exception as e:
            msg = "ScriptNotUploaded: Look at previous logs for " \
            "more information.".format(
                sn=script_name,
                dir = self._path_to_scripts.replace(".", " / "))
            self.log.warning(msg)


    def _upload_script(self, script_name:str):
        """upload the script script_name from the script folder and set
        it as the new script. The method rise errors when the script cannot be loaded.

        Parameters
        ----------
        script_name : str
            the name of the script to be loaded. Should be located in the _path_to_scripts folder. 

        Raises
        ------
        ExperimentIsRunning
            Exception raised when the experiment is already running a sequence.
        ExperimentIsPreparing
            Exception raised when the experiment is already preparing a sequence (setting parameter).
        ModuleNotFoundError
            Exception raised when the module is not found.
        AttributeError
            Exception raised if the script does not have a "Script" class. Any script must be of Script class.
        SyntaxError
            Exception raised when a syntax error prevents the loading of the module. 
        """
        if self.is_running :
            msg="ExperimentIsRunning: The server is running an experiment." \
            " Please stop data acquisition to upload a new script."
            self.log.error(msg)
            raise ExperimentIsRunning(msg)
        if self._is_setting_parameters:
            msg="ExperimentIsPreparing: The server is busy setting parameters." \
            " A new script cannot be uploaded at this stage."
            self.log.error(msg)
            raise ExperimentIsPreparing(msg)
            
        try:
            ## check if .py is in the name
            if script_name[-3:] == ".py":
                script_name=script_name[:-3]
            complete_module_name = self._path_to_scripts +"."+script_name
            if complete_module_name in sys.modules:
                self.current_module = importlib.reload(sys.modules[complete_module_name])
            else:
                self.current_module = importlib.import_module(complete_module_name)
            class_script = getattr(self.current_module, "Script")
            self.script = class_script()
            self.log.info(f"Script '{script_name}´ successfully uploaded.")
            return
        except ModuleNotFoundError as e:
            msg = "{t}: {e}. Comment: The script '{name}' was not found. Please " \
            "make sure your file exist in the directory {dir}".format(
                t=type(e).__name__, 
                e=e,
                name = script_name,
                dir = self._path_to_scripts.replace(".", " / ") )
            self.log.error(msg)
            raise 
        except AttributeError as e:
            ## this means the script has no class Script
            if "Script" in str(e):
                msg = "{t}: {e}. Make sure that your script does define a class 'Script' which inherits from AmazingScript.".format(
                t=type(e).__name__, 
                e=e, 
                name = script_name,
                dir = self._path_to_scripts.replace(".", " / "))
                self.log.error(msg)
            else:
                self.log.error("{}: {}".format(type(e).__name__, e))
            raise 
        except Exception as e:
            msg = "{t}: {e}.".format(
                t=type(e).__name__, 
                e=e, 
                name = script_name,
                dir = self._path_to_scripts.replace(".", " / "))
            self.log.error(msg)
            raise

    def _check_script_attributes(self):
        pass
    
    @Pyro5.api.expose
    def run(self):
        self._run()

    def _run(self):
        ## 1. Checks: script is uploaded? Is already running? Has acquire method?
        if self.script is None:
            msg="No script to run. Please upload a script first."
            self.log.error(msg)
            raise NoScriptToRun(msg)
        
        if self.is_running :
            msg="ExperimentIsRunning: The server is running an experiment." \
            " Please stop data acquisition to run a new sequence."
            self.log.error(msg)
            raise ExperimentIsRunning(msg)
        
        method = getattr(self.script, "acquire", None)
        if not callable(method):
            msg="The uploaded Script does not have an acquire method. Script cannot be run."
            self.log.error(msg)
            raise AttributeError(msg)

        if not self._are_params_set:
            self.set_parameters()


    @Pyro5.api.expose
    def set_parameters(self):
        self._are_params_set = False
        try:
           self._set_parameters()
           self._are_params_set = True
        except Exception as e:
            self._are_params_set = False
    def start_sequence(self):
        pass
    
    def _set_parameters(self):
        ## 1. Checks: script is uploaded? Is already running? Has acquire method?
        if self.script is None:
            msg="No script to run. Please upload a script first."
            self.log.error(msg)
            raise NoScriptToRun(msg)
        
        if self.is_running :
            msg="ExperimentIsRunning: The server is running an experiment." \
            " Please stop data acquisition before setting new parameters."
            self.log.error(msg)
            raise ExperimentIsRunning(msg)
        
        



    
if __name__ == "__main__":
    
    server = ScriptServer()
    server._path_to_scripts = "amaz_ctrl.scripts.base"
    server._upload_script("dummy_script.py")
    
    # # server._is_setting_parameters = True
    # server.upload_script("simple_script.py")
    # # server.run()
    # try:
    #     server.is_running=True
    #     server._run()
    # except Exception as e:
    #     print(type(e), type(e)==ExperimentIsRunning)
    # # print(server.script.pomme)
    # method = getattr(obj, 'method_name', None)
    # if callable(method):
    #     print("Hello")
