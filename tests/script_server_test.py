#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Created on the Sun Apr 05 2026 by Victor
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
Content of script_server_test.py

Please document your code ;-).

'''

# Standard library imports:
import pytest
import os

# Local imports
from amaz_ctrl.server.script_server import ScriptServer
from amaz_ctrl.tools.amaz_exception import ExperimentIsRunning, ExperimentIsPreparing, NoScriptToRun

def script_server_instance():
    instance = ScriptServer()
    instance._path_to_scripts = "amaz_ctrl.scripts.base"
    return instance

################################################################
######## TESTING THE _UPLOAD METHOD OF SCRIPT_SERVER ###########
### We test here the _upload_script method of the ScriptServer #
### class.                                                     #
################################################################

def test_upload_error_running():
    server = script_server_instance()
    server._is_running=True
    try:
        server._upload_script("dummy_script.py")
    except Exception as e:
        assert type(e)==ExperimentIsRunning

def test_upload_error_preparing():
    server = script_server_instance()
    server._is_setting_parameters=True
    try:
        server._upload_script("dummy_script.py")
    except Exception as e:
        assert type(e)==ExperimentIsPreparing


def test_upload_error_fake_module():
    server = script_server_instance()
    try:
        server._upload_script("a_script_that_does_not_exist.py")
    except Exception as e:
        assert type(e)==ModuleNotFoundError

def test_upload_success():
    server = script_server_instance()
    server._upload_script("dummy_script.py")
    assert type(server.script).__name__ == "Script"

################################################################
###### TESTING THE _SET_PARAMETERS METHOD OF SCRIPT_SERVER #####
################################################################
def test_set_params_error_no_script_uploaded():
    server = script_server_instance()
    try:
        server._set_parameters()
    except Exception as e:
        assert type(e)==NoScriptToRun

def test_set_params_error_running():
    server = script_server_instance()
    server._upload_script("dummy_script.py")
    server._is_running=True
    try:
        server._set_parameters()
    except Exception as e:
        assert type(e)==ExperimentIsRunning


################################################################
########## TESTING THE _RUN METHOD OF SCRIPT_SERVER ############
################################################################
def test_run_no_script_uploaded():
    server = script_server_instance()
    try:
        server._run()
    except Exception as e:
        assert type(e)==NoScriptToRun

def test_run_error_running():
    server = script_server_instance()
    server._upload_script("dummy_script.py")
    server._is_running=True
    try:
        server._run()
    except Exception as e:
        assert type(e)==ExperimentIsRunning



# def test_run_error_running():
#     server = script_server_instance()
#     server._upload_script("dummy_script.py")
#     server._is_running=True
#     try:
#         server._run()
#     except Exception as e:
#         assert type(e)==ExperimentIsRunnings

# # We do not have hardware so all classes in dummy mode
# IS_DUMMY=True



# @pytest.fixture(scope="session")
# def database_instance():
#     return Database(port=8086, name="my_database", is_dummy=IS_DUMMY)


# @pytest.fixture(scope="session")
# def arduino_instance():
#     return Arduino(port=1, baudrate=9600, is_dummy=IS_DUMMY)

# ######## SENSORS BASE CLASS ########
# @pytest.fixture(scope="function")
# def subsensor_instance(database_instance):
#     return SubSensor(database_instance, descr="My amazing sensor", is_dummy=IS_DUMMY)

# @pytest.fixture(scope="function")
# def multi_sensor_instance(database_instance):
#     subsensors_parameters = [
#             {
#                 "sensor_number": 1,
#                 "descr": "temp_k_door",
#                 "unit": "°C",
#                 "category": "temperature",
#                 "sensor_type": "type K thermocouple",
#                 "save_to_database": True,
#             }
#         ]
#     multisensor = DummyMultiSensor(
#         database=database_instance,
#         number_of_sensors=3,
#         sensor_parameters=subsensors_parameters,
#         descr="My amazing Multi-sensor",
#     )
#     return multisensor

# ######## ARDUINO SENSORS ########

# @pytest.fixture(scope="function")
# def arduino_adc_instance(database_instance,arduino_instance ):
#     subsensors_parameters = [
#             {
#                 "sensor_number": 9,
#                 "descr": "voltage monitoring photodiode",
#                 "unit": "V",
#                 "category": "voltage",
#                 "sensor_type": "Photodiode",
#                 "save_to_database": True,
#             }
#         ]
#     adc_sensor = Arduino_ADC_Sensor(
#         database=database_instance,
#         board= arduino_instance,
#         sensor_parameters=subsensors_parameters,
#         descr="My amazing Multi-sensor",
#         is_dummy=IS_DUMMY
#     )
#     return adc_sensor

# ######## PHIDGETS ########
# @pytest.fixture(scope="function")
# def lab_temp_phidget(database_instance):
#     """Return sensor object for lab temp phidget."""
#     tc0 = PhidgetTC(
#         hub_serial=622701,
#         hub_port=0,
#         hub_channel=0,
#         database=database_instance,
#         descr="temp_k_table_rb_vapor",
#         location="Optical table, optics near the science Rb Cell",
#         is_dummy=IS_DUMMY
#         )
#     return tc0