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
Content of script_server.py

Please document your code ;-).

'''
from amaz_ctrl.tools.amaz_exception import ExperimentIsRunning, NoScriptToRun
from amaz_ctrl.server.amaz_server import AmazingServer
import importlib, sys
import Pyro5.api
import threading, os, datetime
from amaz_ctrl.tools.amaz_logs import connect_logger_to_call_out

class ScriptServer(AmazingServer):
    _script_class = "Script" #the name of the class we import
    _path_to_scripts = "amaz_ctrl.scripts" #the path within the module of the script. 
    script = None
    current_module = None
    _thread_running = None
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

    ###################################################################
    ##########################  Properties   ##########################
    ###################################################################
    @property
    def is_running(self)->bool:
        """returns wether the _thread_running is alive or not, i.e. if an experiment is running."""
        return self._thread_running is not None and self._thread_running.is_alive()
    

    ###################################################################
    ########################  Private methods  ########################
    ###################################################################
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
            return
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

            ## Connect logs of the Script to add them to the Server Log collection
            connect_logger_to_call_out(self.script.log, self._internal_log)
            self.log.info(f"Script '{script_name}´ successfully uploaded.")


            ## Get last modification date for user information when run is asked.
            file_path = self.current_module.__file__
            timestamp = os.path.getmtime(file_path)
            self._script_last_modified = datetime.datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
            self._loaded_file = script_name+".py"
            return
        except ModuleNotFoundError as e:
            msg = "{t}: {e}. Comment: The script '{name}' was not found. Please " \
            "make sure your file exist in the directory {dir}".format(
                t=type(e).__name__, 
                e=e,
                name = script_name,
                dir = self._path_to_scripts.replace(".", " / ") )
            self.log.error(msg)
            return 
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
            return 
        except Exception as e:
            msg = "{t}: {e}.".format(
                t=type(e).__name__, 
                e=e, 
                name = script_name,
                dir = self._path_to_scripts.replace(".", " / "))
            self.log.error(msg)
            return

    def _run_script(self):
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
        self.log.info(f"Running  {self._loaded_file} which was lastly modified at {self._script_last_modified}.")
        self._thread_running = threading.Thread(target=self.script.main)
        self._thread_running.start()


    
    ###################################################################
    ####---------- PUBLIC METHODS EXPOSED TO PYRO SERVER ----------####
    #### these methods can be called by the server because of the  ####
    #### property @Pyro5.api.expose on top of them.                ####
    ###################################################################
    
    @Pyro5.api.expose
    @Pyro5.api.oneway
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

    @Pyro5.api.expose
    @Pyro5.api.oneway
    def run_script(self):
        self._run_script()
    

    @Pyro5.api.expose
    @Pyro5.api.oneway
    def stop(self):
        self.script.stop_acquisition()
        



    
if __name__ == "__main__":
    ## -. The Daemon is a background process that listens for incoming network requests on a given ip/port, here 9090 (otherwise Pyro5 would just pick a random one). 
    # Currently we set IP to "localhost" for single-machine testing.
    # To access this via VPN later, replace with the host by IP address or "0.0.0.0" (but this is dangerous, be carreful not to open too much your computer).
    daemon = Pyro5.api.Daemon(host="localhost", port=9090)
    ## Register the Pyro5 using a specific name so that it is predictable.
    ## here: PYRO:script.server@localhost:9090
    obj = ScriptServer(
        logger_name="SCRIPT_SERVER",
        max_log=100, 
        log_level="INFO"
    )
    uri = daemon.register(obj, "script.server")
    print(f"Dummy Server ready on Port 9090\nURI: {uri}")
    daemon.requestLoop()
    
