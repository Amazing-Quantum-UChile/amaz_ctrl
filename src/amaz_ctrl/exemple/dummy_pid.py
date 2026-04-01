#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Created on the Tue Mar 31 2026 by Victor
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
Content of dummy_pid.py

Please document your code ;-).

'''

import Pyro5.api
from amaz_ctrl.server.pid_server import PID_server

@Pyro5.api.expose
class Dummy_PID_Server(PID_server):
    _new_input_value = 0
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def connect(self):
        """writes here the method that connects to your sensor device."""
        self.log.info("Connection to the dummy measurement device succeeded.")

    def set_output(self, output: float):
        """defines here the method that generate the output signal"""
        ## simulate the retroaction
        self._new_input_value = output + self.input
        self.log.info(f"Setting the output of the dummy device to {output}.")

    def measure_input(self) -> float:
        """returns the value that we aim to stabilize."""
        return self._new_input_value

    @Pyro5.api.expose
    def some_dummy_function(self):
        """this function is not useful but it illustrates that we must add the property """
        return self._new_input_value, "Hi"

if __name__ == "__main__":
    ## -. The Daemon is a background process that listens for incoming network requests on a given ip/port, here 9091 (otherwise Pyro5 would just pick a random one). 
    # Currently we set IP to "localhost" for single-machine testing.
    # To access this via VPN later, replace with the host by IP address or "0.0.0.0" (but this is dangerous, be carreful not to open too much your computer).
    daemon = Pyro5.api.Daemon(host="localhost", port=9091)
    ## Register the Pyro5 using a specific name so that it is predictable.
    ## here: PYRO:dummy.pid@localhost:9091
    obj = Dummy_PID_Server()
    uri = daemon.register(obj, "dummy.pid")
    print(f"Temperature Server ready on Port 9091\nURI: {uri}")
    daemon.requestLoop()







