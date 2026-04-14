#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Created on the Tue Apr 14 2026 by Victor
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
Content of pid_rb_cell_server.py

Please document your code ;-).

'''
from amaz_ctrl.server.pid_server import PID_server


class EmptySensor():
    is_open = False


class RbCellHeaterPID(PID_server):
    temp_sensor = EmptySensor()
    def connect(self):
        """writes here the method that connects to your sensor device."""
        ports = serial.tools.list_ports.comports()

        for port in ports:
            print(f"Device: {port.device}")
            print(f"Name: {port.name}")
            print(f"Description: {port.description}")
            print(f"HWID: {port.hwid}")
            print(f"VID: {port.vid}")
            print(f"PID: {port.pid}")
            print(f"Serial number: {port.serial_number}")
            print("-" * 40)

        # ##-. Connect to the temperature sensor
        # self.temp_sensor = serial.Serial()
        # self.temp_sensor.baudrate = 115200
        # self.temp_sensor.timeout = 1

    def set_output(self, output: float):
        """defines here the method that generate the output signal"""
        pass

    def measure_input(self) -> float:
        """Returns the measured temperature."""
        return
    
if __name__ == "__main__":
    temp= RbCellHeaterPID()