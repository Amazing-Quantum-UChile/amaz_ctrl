#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Created on the Thu Apr 02 2026 by Victor
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
Content of simple_script_server.py

Please document your code ;-).

'''
import importlib, sys, time
import Pyro5.api


class ScriptServer():
    _script_class = "Script" #the name of the class we import
    _script_loaded = False
    current_script_module = None
    _path_to_scripts = "amaz_ctrl.example.script_client_server"

    def upload_script(self, script_name):
        ## check if .py is in the name
        print(f"Starting to upload {script_name}")
        if script_name[-3:] == ".py":
            self.script_name=script_name[:-3]
        complete_module_name = self._path_to_scripts +"."+script_name

        if complete_module_name in sys.modules:
            self.current_module = importlib.reload(sys.modules[complete_module_name])
        else:
            self.current_module = importlib.import_module(complete_module_name)
        class_script = getattr(self.current_module, "Script")
        self.script = class_script()
            



if __name__ == "__main__":
    server = ScriptServer()
    server.upload_script("simple_script")
    print(server.script.pomme)
    time.sleep(10)
    server.upload_script("simple_script")
    print(server.script.pomme)


    # ## -. The Daemon is a background process that listens for incoming network requests on a given ip/port, here 9091 (otherwise Pyro5 would just pick a random one). 
    # # Currently we set IP to "localhost" for single-machine testing.
    # # To access this via VPN later, replace with the host by IP address or "0.0.0.0" (but this is dangerous, be carreful not to open too much your computer).
    # daemon = Pyro5.api.Daemon(host="localhost", port=9091)
    # ## Register the Pyro5 using a specific name so that it is predictable.
    # ## here: PYRO:dummy.pid@localhost:9091
    # import numpy as np
    # obj = ScriptServer()
    # uri = daemon.register(obj, "dummy.pid")
    # print(f"Dummy Server ready on Port 9091\nURI: {uri}")
    # daemon.requestLoop()










