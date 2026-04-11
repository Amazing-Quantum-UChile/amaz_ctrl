#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Created on the Sun Apr 05 2026 by Victor
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
Content of script_test.py

Please document your code ;-).

'''


from amaz_ctrl.scripts.base.amaz_script import AmazingScript
import os

###################################
####### AmazingScript tests #######
###################################
def amaz_script_instance():
    exp_params_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..","src", "amaz_ctrl","scripts")
    instance = AmazingScript(exp_params_dir=exp_params_dir)
    return instance

def test_data_dir_error():
    script = amaz_script_instance()
    try:
        script._check_data_dir(os.path.abspath(__file__))
    except Exception as e:
        assert type(e)==TypeError

def test_load_parameters():
    script = amaz_script_instance()
    assert type(script.exp_params)==dict

def test_default_exp_params():
    """check that the default experimental parameters are always in the exp_params dictionary. """
    script = amaz_script_instance()
    for key in script._default_exp_params.keys():
        assert key in script.exp_params
    assert type(script.exp_params["No of realizations"])==int

def test_prepare_exp_error():
    script = amaz_script_instance()
    try:
        script.prepare_experiment()
    except Exception as e:
        assert type(e)==AttributeError


def test_connect_sensors_error():
    script = amaz_script_instance()
    try:
        script.connect_sensors()
    except Exception as e:
        assert type(e)==AttributeError

def test_disconnect_sensors_error():
    script = amaz_script_instance()
    try:
        script.disconnect_sensors()
    except Exception as e:
        assert type(e)==AttributeError

def test_acquire_error():
    script = amaz_script_instance()
    try:
        script.acquire()
    except Exception as e:
        assert type(e)==AttributeError

