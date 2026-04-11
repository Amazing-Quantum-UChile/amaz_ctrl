#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Created on the Wed Apr 01 2026 by Victor
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
Content of dummy_pid_client.py


This small piece of code is a possible client part of the Dummy_PID_Server that was defined in dummy_pid_server.py.
'''

# %%
import Pyro5.api
import time 
import matplotlib.pyplot as plt
server_ip = "localhost" 
port = 9091
object_name = "dummy.pid"

# Construct the URI (Uniform Resource Identifier)
uri = f"PYRO:{object_name}@{server_ip}:{port}"

# Create the proxy to communicate with the server
device = Pyro5.api.Proxy(uri)

## Check Logs
def show_logs(logs):
    for elem in logs:
        print(f"[{elem['level']}]: {elem['message']}")
show_logs(device.get_logs())
## Try to set an other level
device.set_log_level("THIS IS NOT A CORRECT LOG LEVEL")
show_logs(device.get_logs())

# %%
# get history
pid_input_values =  device.get_input_history()
print(f"All input values: {pid_input_values}. History is empty because PID did not start.")


## Change PID parameters
device.set_pid_parameters(kp=.7, ki="hello", kd=0)

show_logs(device.get_logs())
#Start PID
device.start()
show_logs(device.get_logs())
time.sleep(5)

# %%
# change the setpoint
device.set_setpoint(1.)
time.sleep(3)

pid_input_values = device.get_input_history()
pid_err_values = device.get_error_history()
pid_output_values = device.get_output_history()
plt.plot(pid_input_values, label = "Input")
plt.plot(pid_err_values, label = "Error")
plt.plot(pid_output_values, label = "Output")
plt.xlabel("Steps of the PID.")
plt.ylabel("Input Value of the PID.")
plt.legend()
plt.show()

# %%
device.set_setpoint(0)
time.sleep(3)


# %%
device.set_pid_parameters(kp=1.6, ki=0, kd=0)
device.set_setpoint(1.)
time.sleep(3)
pid_input_values2 = device.get_input_history()
pid_err_values2 = device.get_error_history()
pid_output_values2 = device.get_output_history()

# %%
plt.plot(pid_input_values, label = "$k_p=0.7$")
plt.plot(pid_input_values2, label = "$k_p=1.6$")
plt.legend()
plt.xlabel("Steps of the PID.")
plt.ylabel("Input values of the PID.")
plt.show()

# %%
device.stop()


