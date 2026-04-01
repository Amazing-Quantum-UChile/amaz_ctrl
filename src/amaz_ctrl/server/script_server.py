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
import Pyro5.api
import time
import collections

class FakeVoltmeter:
    def __init__(self):
        self.connected = False
    def connect(self): 
        self.connected = True
        print("Device: Connected to Voltage Source.")
    def read(self):
        return 2.5 if self.connected else 0.0
    def disconnect(self):
        self.connected = False
        print("Device: Disconnected.")

@Pyro5.api.expose
class LabServer:
    def __init__(self):
        self.meter = FakeVoltmeter()
        self.logs = collections.deque(maxlen=10)

    def log(self, msg):
        full_msg = f"[{time.strftime('%H:%M:%S')}] {msg}"
        self.logs.append(full_msg)
        print(full_msg)

    def get_logs(self):
        new_logs = list(self.logs)
        self.logs.clear()
        return new_logs

    def run_sequence(self, value_to_set):
        self.log(f"Starting sequence with param: {value_to_set}")
        try:
            self.meter.connect() # Open
            time.sleep(1)        # Simulate work
            val = self.meter.read()
            self.log(f"Measured value: {val}V")
        finally:
            self.meter.disconnect() # Always close, even if it crashes
            self.log("Sequence finished.")



# Lancement du serveur sur le port 9090
daemon = Pyro5.api.Daemon(port=9090)
uri = daemon.register(LabServer, "my.lab")
print(f"Server ready. URI: {uri}")
daemon.requestLoop()