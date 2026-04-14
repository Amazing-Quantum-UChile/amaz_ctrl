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
import Pyro5.api
import pyvisa as visa


class RbCellHeaterPID(PID_server):
    """This PID locks the Rb Cell temperature. Inherit the following methods and properties from the PID_server:

    Methods:
    -------
    * set_pid_parameters(kp, ki, kd),
    * start: this starts the PID loop in a thread. Every sampling_period, it does the following:
        input <- measure_input()
        output <- compute_output(input)
        output <- convert_output(output)
        output <- self.check_output(output)
        set_output(output)
        sleep(sampling_period)
    * stop: stops the PID loop,
    """
    temp_sensor_properties={"serial no":"AE015VCIA", "timeout":1.,"baudrate":115200}
    temp_sensor = None
    _voltage_offset = 1.
    _temperature = None

    

    def connect(self):
        """writes here the method that connects to your sensor device."""
        ## 1. Connect to the Temperature sensor
        self.temp_sensor_properties["port"] = self.get_serial_port_from_serial_number(self.temp_sensor_properties["serial no"])
        self.temp_sensor = serial.Serial(port = self.temp_sensor_properties["port"],
                                            baudrate= self.temp_sensor_properties["baudrate"], 
                                            timeout =self.temp_sensor_properties["timeout"])
        self.log.info("Connected to the temperature sensor No {}  on port {}.".format(
            self.temp_sensor_properties["serial no"],
            self.temp_sensor_properties["port"]
        ))
        ## 2. Connect to the Temperature sensor
        self.rm = visa.ResourceManager()
        print(self.get_visa_usb_resources())
        # options=self.rm.list_resources('USB0::??????::??????::DP?*::INSTR')
       

    def set_output(self, output: float):
        """defines here the method that generate the output signal"""
        pass

    def convert_output(self, output:float)->float:
        """applies an offset to the computed value of the PID voltage."""
        ## 1. If temperature really away from the goal temperature, we go to maximum 
        actual_temp = self.get_temperature()
        if actual_temp < self.setpoint - 5:
            output = max(self._output_limits)
            return output
        ## 2. If temperature is really too large, we set to zero.
        elif actual_temp >self.setpoint+5:
            return 0
        return output
        
    def measure_input(self) -> float:
        """Returns the measured temperature."""
        return self.measure_temperature()
    
    def measure_temperature(self):
        """measure temperature based on 
        https://media.thorlabs.com/globalassets/items/t/tc/tc2/tc200/12597-d02.pdf?v=0116031151
        """
        self.temp_sensor.write(b'tact?\r')
        full_read_temp=self.temp_sensor.read(1000)#.decode('ascii')
        #print(FullReadTemps[6:-5].decode('ascii'))
        self._temperature =float(full_read_temp[6:-5].decode('ascii'))        
        return self._temperature 

    @Pyro5.api.expose
    def get_temperature(self):
        """returns the last measured temperature"""
        if self._temperature is None:
            return self.measure_temperature()
        else:
            return self._temperature
if __name__ == "__main__":
    server= RbCellHeaterPID(
        setpoint=0,
        pid_parameters={"kp": .15, "ki": 0, "kd": 0},
        output_limits=(0, 10),
        sampling_period = 1., # in seconds
        history_size=50,
    )
    print(server.get_temperature())
