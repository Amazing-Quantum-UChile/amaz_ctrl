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
import serial.tools.list_ports
import serial

class RbCellHeaterPID(PID_server):
    _serial_no= "AE015VCIA"
    _timeout = 1.
    _baudrate = 115200
    temp_sensor = None
    def connect(self):
        """writes here the method that connects to your sensor device."""
        ports = serial.tools.list_ports.comports()
        ##-. We look for the port that matches the good serial number
        selected_port = []
        for port in ports:
            if port.serial_number == self._serial_no:
                selected_port.append(port.device)
        if len(selected_port)==0:
            msg = f"The serial number {self._serial_no} was not identified. Is it really plug?"
            self.log.error(msg)
            self.list_usb_ports()
            raise serial.SerialException(msg)
        elif len(selected_port)>1:
            msg = f"The serial number {self._serial_no} is found on {len(selected_port)} different ports. This is weird. Please take a look."
            self.log.error(msg)
            self.list_usb_ports()
            raise serial.SerialException(msg)
        else:
            self._port = selected_port[0]
            self.temp_sensor = serial.Serial(port = self._port,
                                             baudrate= self._baudrate, 
                                             timeout =self._timeout)
            self.log.info(f"Connected to {self._serial_no}  on port {self._port}")
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