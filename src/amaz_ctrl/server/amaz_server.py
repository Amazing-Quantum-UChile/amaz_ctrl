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

"""
Content of amaz_server.py

Please document your code ;-).

"""

import logging
from abc import ABC, abstractmethod
import Pyro5.api


class AmazingServer(ABC):# Inherits from ABC to be an abstract base class
    def __init__(self, logger_name="SERVER", max_log=100, log_level="INFO"):
        self.logger_name = logger_name
        self._max_log = max_log
        self._log_level = log_level

    def set_up_logs(self):
        """connects the class to the logger to sotre the log message. These message can then be queried by the client."""
        self._log_buffer = collections.deque(maxlen=self._max_log)
        self.log = logging.getLogger(self.logger_name)
        self.log.setLevel(self._log_level)

        ## Set up the link between the log and this class.
        handler = InternalBufferHandler(self)
        formatter = logging.Formatter(
            f"{self.logger_name}: %(asctime)s: %(message)s", "%H:%M:%S"
        )
        handler.setFormatter(formatter)
        self.log.addHandler(handler)

    @Pyro5.api.expose
    def get_logs(self):
        logs = list(self._log_buffer)
        self._log_buffer.clear()
        return logs

    def _internal_log(self, msg, lvl):
        self._log_buffer.append({"level": lvl, "message": msg})


class InternalBufferHandler(logging.Handler):
    def __init__(self, server_instance):
        super().__init__()
        self.server = server_instance

    def emit(self, record):
        msg = self.format(record)
        self.server._internal_log(msg)



