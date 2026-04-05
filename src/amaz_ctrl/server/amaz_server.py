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

This code implements 
"""

import logging, colorlog, textwrap
from abc import ABC, abstractmethod
import Pyro5.api
from collections import deque


class AmazingServer(ABC):# Inherits from ABC to be an abstract base class
    log_formatter_console = colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)s:%(message)s%(reset)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red",
            },
            secondary_log_colors={},
            style="%",
        )
    def __init__(self, logger_name="SERVER", max_log=100, log_level="INFO"):
        self.logger_name = logger_name
        self._max_log = max_log
        self._log_level = log_level
        # self.set_up_logs()
        self._log_buffer = deque(maxlen=self._max_log)
        self.log = logging.getLogger(self.logger_name)
        self.set_up_log(self.logger_name)


    def set_up_log(self, logger_name):
        """connects the class to the logger to sotre the log message. These message can then be queried by the client."""
        logger = logging.getLogger(logger_name)
        logger.setLevel(self._log_level)

        ### ------------- CONSOLE LOGS -------------
        ## Format logs so that they are printed in the server terminal
        
        ch = logging.StreamHandler()
        ch.setFormatter(self.log_formatter_console)
        logger.addHandler(ch)


        ### ------------- PYRO READABLE LOGS -------------
        ## we also configure logs so that they can be read by clients. 
        ## To do so we add an other handler: InternalBufferHandler
        handler = InternalBufferHandler(self)
        formatter = logging.Formatter(
            f"{logger_name}: %(asctime)s: %(message)s", "%H:%M:%S"
        )
        handler.setFormatter(formatter)
        self.log.addHandler(handler)


    @Pyro5.api.expose
    def get_logs(self):
        logs = list(self._log_buffer)
        self._log_buffer.clear()
        return logs
    
    @Pyro5.api.expose
    def set_log_level(self, lvl):
        try:
            self.log.setLevel(lvl)
            self._lo = lvl
        except ValueError:
            self.log.error(f"Failed to update the log level because '{lvl}' is not a valid logging level.")

    def _internal_log(self, msg, lvl):
        self._log_buffer.append({"level": lvl, "message": msg})


class InternalBufferHandler(logging.Handler):
    def __init__(self, server_instance):
        super().__init__()
        self.server = server_instance

    def emit(self, record:logging.LogRecord)-> None:
        """when an information is logged, send the information into the internal buffer."""
        msg = self.format(record)
        self.server._internal_log(msg, record.levelname)



class SimpleWrappedFormatter(colorlog.ColoredFormatter):
    """the idea of this class is to better format text."""
    def format(self, record):
        raw_msg = str(record.msg)
        wrapped_lines = []
        for i, line in enumerate(raw_msg.splitlines()):
            if i>0:
                line =" " * (len(record.levelname) + 1) +line
            wrapped = textwrap.fill(
                line,
                width=80,
                subsequent_indent=" " * (len(record.levelname) + 1),
                replace_whitespace=True,
                drop_whitespace=True
            )
            wrapped_lines.append(wrapped)

        record.msg = "\n".join(wrapped_lines)
        
        return super().format(record)


if __name__ == "__main__":
    ## -. The Daemon is a background process that listens for incoming network requests on a given ip/port, here 9091 (otherwise Pyro5 would just pick a random one). 
    # Currently we set IP to "localhost" for single-machine testing.
    # To access this via VPN later, replace with the host by IP address or "0.0.0.0" (but this is dangerous, be carreful not to open too much your computer).
    daemon = Pyro5.api.Daemon(host="localhost", port=9092)
    ## Register the Pyro5 using a specific name so that it is predictable.
    ## here: PYRO:dummy.pid@localhost:9091
    uri = daemon.register(AmazingServer, "amaz.server")
    print(f"The Amazing Server Mother class is on Port 9092\nURI: {uri}")
    daemon.requestLoop()
