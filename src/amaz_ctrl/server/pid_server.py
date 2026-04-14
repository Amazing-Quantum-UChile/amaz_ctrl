#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Created on the Tue Mar 31 2026 by Victor
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
Content of pid_server.py

Implements the abstract class PID.
"""
from abc import abstractmethod
from amaz_ctrl.server.amaz_server import AmazingServer
import Pyro5.api
import numpy as np
from collections import deque
import threading
import time 

@Pyro5.api.expose
class PID_server(AmazingServer):
    kp = .5
    ki = 0
    kd = 0
    input = 0
    setpoint = 0
    error = 0
    int_error = 0
    _is_running = False
    thread = None
    

    def __init__(
        self,
        setpoint=0,
        pid_parameters={"kp": .5, "ki": 0, "kd": 0},
        output_limits=(-np.inf, np.inf),
        sampling_period = 1., # in seconds
        history_size=50,
        **kwargs,
    ):
        """Instanciate the abstract PID class

        Parameters
        ----------
        setpoint : int, optional
            The target value the controller is attempting to reach, by default 0
        pid_parameters : dict, optional
            Dictionary containing 'p', 'i', and 'd' gains, by default {"kp": 1, "ki": 0, "kd": 0}
        output_limits : tuple, optional
            (min, max) values to clamp the controller output, by default (-np.inf, np.inf)
        sampling_period : int, optional
            The time interval in seconds between compute steps, by default 1

        Other keywords argument (kwargs) are given to the AmazingServer mother class.
        """
        super().__init__(**kwargs)
        self.set_pid_parameters(**pid_parameters)
        self._output_limits = output_limits
        self._sampling_period = sampling_period
        self.set_setpoint(setpoint)
        self.input_history = deque(maxlen=history_size)
        self.error_history = deque(maxlen=history_size)
        self.output_history = deque(maxlen=history_size)
        self.connect()
        self.log.info(f"PID {self.__class__.__name__} ready to start. Call the start method to initiate the loop.")


    
    @property
    def is_running(self):
        """returns if the pid is running or not"""
        return self._is_running
    
    def set_pid_parameters(self, kp:float=None, ki:float=None, kd:float=None):
        """set PID parameters kp, ki and kd

        Parameters
        ----------
        kp : float, optional
            proportional gain of the PID, by default None
        ki : float, optional
            integral gain of the PID, by default None
        kd : float, optional
            derivative gain of the PID, by default None
        """

        ## We store the old value of the pid in case the new one are not correct
        if isinstance(kp, (int, float)):
            self.kp = kp
        elif kp is not None:
            self.log.critical(
                f"ValueError. Failed to set the PID value kp={kp}. Old values {self.kp} is kept."
            )

        if isinstance(ki, (int, float)):
            self.ki = ki
        elif ki is not None:
            self.log.critical(
                f"ValueError. Failed to set the PID value ki={ki}. Old values {self.ki} is kept."
            )
        
        if isinstance(kd, (int, float)):
            self.kd = kd
        elif kd is not None:
            self.log.critical(
                f"ValueError. Failed to set the PID value kd={kd}. Old values {self.kd} is kept."
            )
            

    def compute_output(self):
        """compute the PID output using the input, last input, integrated 
        error, setpoint and PID parameters."""
        last_error = self.error #store last error
        self.error = self.setpoint - self.input
        self.int_error += self.error
        diff_error = self.error - last_error
        pid = self.kp * self.error + self.ki * self.int_error + self.kd * diff_error
        return pid

    def _pid_loop(self):
        """implements the pid loop"""
        while self._is_running:
            self.input = self.measure_input()
            
            output = self.compute_output()
            output = self.check_output(output)
            self.log.debug(f"Output value is {output}.")
            self.set_output(output)
            ## Update history
            self.input_history.append(self.input)
            self.error_history.append(self.error)
            self.output_history.append(output)
            ## -. wait for the samplig period
            time.sleep(self._sampling_period)

    def check_output(self, output):
        """check that the output is within the authorized range."""
        if output >  max(self._output_limits):
            return max(self._output_limits)
        if  output <  min(self._output_limits):
            return min(self._output_limits)
        return output
            
    ###################################################################
    ##### ABSTRACT METHOD TO BE DEFINED IN EACH DAUGHTER CLASSES ######
    ###################################################################

    @abstractmethod
    def connect(self):
        """writes here the method that connects to your sensor device."""
        pass

    @abstractmethod
    def set_output(self, output: float):
        """defines here the method that generate the output signal"""
        pass

    @abstractmethod
    def measure_input(self) -> float:
        """returns the value that we aim to stabilize."""
        return 0


    ###################################################################
    ####---------- PUBLIC METHODS EXPOSED TO PYRO SERVER ----------####
    #### these methods can be called by the server because of the  ####
    #### property @Pyro5.api.expose on top of them.                ####
    ###################################################################


    @Pyro5.api.expose
    def set_setpoint(self, value):
        self.setpoint = value

    @Pyro5.api.expose
    def start(self):
        """start the PID loop via thread (so that we can stop it)."""
        if not self._is_running: 
            self._is_running = True
            # daemon=True allow to stop automatically the code 
            # if the main script closes
            self._thread = threading.Thread(target=self._pid_loop, daemon=True)
            self._thread.start()
            self.log.info("PID thread started.")
    
    @Pyro5.api.expose
    def stop(self):
        """stop the PID loop started with thread."""
        self._is_running = False
        if self._thread:
            self._thread.join()
        self.log.info("PID thread stopped.")

    @Pyro5.api.expose
    def get_value(self):
        return self.input
    
    @Pyro5.api.expose
    def is_running(self):
        return self._is_running
    
    @Pyro5.api.expose
    def get_input_history(self):
        return list(self.input_history)
    
    @Pyro5.api.expose
    def get_output_history(self):
        return list(self.output_history)
    
    @Pyro5.api.expose
    def get_error_history(self):
        return list(self.error_history)
    
    @Pyro5.api.expose
    def clear_history(self):
        self.input_history.clear()
        self.error_history.clear()
        self.output_history.clear()    

    @Pyro5.api.expose
    def set_sampling_period(self, val:float):
        """sets the sampling period of the PID in seconds

        Parameters
        ----------
        val : float
            time in seconds for the PID sampling period.
        """
        self._sampling_period = val

    

    
    

    
