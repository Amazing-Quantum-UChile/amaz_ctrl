#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Created on the Thu Apr 09 2026 by Victor
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
Content of server_connector.py

Please document your code ;-).

'''
import Pyro5.api
import logging
from datetime import datetime
from Pyro5.errors import CommunicationError, ConnectionClosedError, TimeoutError
class ServerConnector():
    """this class implements a buffer class to dialog with 

    Returns
    -------
    _type_
        _description_
    """
    _last_connection_time = datetime(2025, 1, 17, 14)
    _last_connection_try = datetime(2025, 1, 17, 14)
    _last_connection_try_warning = datetime(2025, 1, 17, 14)
    _device = None
    _pyroTimeout = .3


    def __init__(self, 
                 uri:str, 
                 log:logging.Logger,
                 dead_time = 3,
                 warning_period = 60
                 ):
        self._uri = uri
        self.log = log
        self.warning_period = warning_period
        self.dead_time = dead_time
        # self.instanciate_device()

    def instanciate_device(self):
        """Instanciates the connection with the PYRO server. We do not do it if the last connection was tried less than a dead_time (60s by default, )
        """
        now = datetime.now()
        if (now - self._last_connection_try).total_seconds() < self.dead_time:
            return
        self._last_connection_try = now
        try:
            proxy = Pyro5.api.Proxy(self._uri)
            proxy._pyroTimeout = self._pyroTimeout
            # check if we are connected
            proxy._pyroBind() 
            self._device = proxy
            self._last_connection_time = now
            self.log.info(f"Connection to {self._uri} as a {type(self).__name__}.")
            self._last_connection_try_warning = now
        except Exception as e:
            if (now - self._last_connection_try_warning).total_seconds() > self.warning_period:
                delay =int( (now-self._last_connection_time).total_seconds())
                if delay > 1e5:
                    delay = "the day you were born"
                else:
                    delay = f"{delay}s"
                msg=f"[{type(self).__name__}] Connection to Pyro server {self._uri} failed and is lost since {delay}. You can try again in {self.dead_time} s."
                self.log.warning(msg)
                self._device = None
                self._last_connection_try_warning = now
            
            
            
    
    @property
    def is_connected(self)->bool:
        if self._device is None: 
            return False
        return True
        

class LogServerConnector(ServerConnector):
    def get_logs(self)->list:
        #-. If disconnect, we try to reconect but if it is still not connected, f*#& it.
        if not self.is_connected:
            self.instanciate_device()
        if not self.is_connected: 
            return []
        try:
            return self._device.get_logs()
        except Exception as e:
            msg = f"[{type(self).__name__}] Failed to retrieve logs from server {self._uri}. Error is due to {type(e).__name__}: {e}"
            self.log.warning(msg)
            self._device = None
            return []


class DataServerConnector(ServerConnector):
    def get_data(self):
        #-. If disconnect, we try to reconect but if it is still not connected, f*#& it.
        if not self.is_connected:
            self.instanciate_device()
        if not self.is_connected: 
            return []
        try:
            return self._device.get_data()
        except Exception as e:
            msg = f"[{type(self).__name__}] Failed to retrieve data from server {self._uri}. Error is due to {type(e).__name__}: {e}"
            self.log.warning(msg)
            return {}

class ScriptServerConnector(ServerConnector):
    """this class implements the connector with the PYRO ScriptServer. The connected PYRO server must have the following methods which are Pyro exposed (@Pyro5.api.expose): upload_script, run_script and stop.
    """
    def load_script(self, script_name:str):
        """this methods calls out the PYRO accessible method upload_script of the amaz_ctrl.server.script_server.ScriptServer class

        Parameters
        ----------
        script_name : str
            _description_
        """
        if not self.is_connected:
            self.instanciate_device()
        if not self.is_connected: 
            self.log.error(f"[{type(self).__name__} Connection with the ScriptServer {self._uri} impossible. Try to relaunch the ScriptServer or update the URI address.")
            return 
        
        try:
            self._device.upload_script(script_name)
            return
        except (CommunicationError, ConnectionClosedError, TimeoutError):
            self.log.info(f"Connection to PYRO server {self._uri} failed. Trying to reconnect...")
            self._device = None  
        self.instanciate_device()
        if not self.is_connected:
            return
        try:
            self._device.upload_script(script_name)
            return
        except (CommunicationError, ConnectionClosedError, TimeoutError):
            self.log.error(f"{type(self).__name__}:Connection with the ScriptServer {self._uri} impossible. Try to relaunch the ScriptServer or update the URI address.")

        return 
    
    def run_script(self):
        """this methods calls out the PYRO accessible method run_script of the amaz_ctrl.server.script_server.ScriptServer class"""
        if not self.is_connected:
            self.instanciate_device()
        if not self.is_connected: 
            self.log.error(f"{type(self).__name__}:Connection with the ScriptServer {self._uri} impossible. Try to relaunch the ScriptServer or update the URI address.")
            return 
        try:
            self._device.run_script()
            return
        except (CommunicationError, ConnectionClosedError, TimeoutError):
            self.log.info(f"Connection to PYRO server {self._uri} failed. Trying to reconnect...")
            self._device = None  
        self.instanciate_device()
        if not self.is_connected:
            return
        try:
            self._device.run_script()
            return
        except (CommunicationError, ConnectionClosedError, TimeoutError):
            self.log.error(f"{type(self).__name__}:Connection with the ScriptServer {self._uri} impossible. Try to relaunch the ScriptServer or update the URI address.")
        return 
        
    def stop(self):
        """this methods calls out the PYRO accessible method stop of the amaz_ctrl.server.script_server.ScriptServer class"""
        if not self.is_connected:
            self.instanciate_device()
        if not self.is_connected: 
            self.log.error(f"[{type(self).__name__}] Connection with the ScriptServer {self._uri} impossible. Try to relaunch the ScriptServer or update the URI address.")
            return
        try:
            self._device.stop()
            return
        except (CommunicationError, ConnectionClosedError, TimeoutError):
            self.log.info(f"Connection to PYRO server {self._uri} failed. Trying to reconnect...")
            self._device = None  
        self.instanciate_device()
        if not self.is_connected:
            return
        try:
            self._device.stop()
            return
        except (CommunicationError, ConnectionClosedError, TimeoutError):
            self.log.error(f"{type(self).__name__}:Connection with the ScriptServer {self._uri} impossible. Try to relaunch the ScriptServer or update the URI address.")
        return  
