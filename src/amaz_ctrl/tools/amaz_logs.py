#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Created on the Mon Apr 06 2026 by Victor
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
Content of amaz_logs.py

this file define the style of the logs printed in the terminal (or console)
'''

import logging, colorlog


log_formatter_console = colorlog.ColoredFormatter(
            "%(log_color)s%(name)s:%(message)s%(reset)s",
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

def set_console_log(logger_name, log_level="INFO"):
    """setups the log printed in the console for the server."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    ## If the log is already added, we do nothing
    if any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        return
    
    ch = logging.StreamHandler()
    ch.setFormatter(log_formatter_console)
    logger.addHandler(ch)

def connect_logger_to_call_out(logger:logging.Logger, call_out_fn):
    """connects the class to the logger to sotre the log message. These message can then be queried by the client."""
    # Check if an InternalBufferHandler is already attached to this logger
    # This prevents stacking handlers if the script/logger name is reused
    if any(isinstance(h, InternalBufferHandler) for h in logger.handlers):
        return
    ### ------------- PYRO READABLE LOGS -------------
    ## we also configure logs so that they can be read by clients. 
    ## To do so we add an other handler: InternalBufferHandler
    handler = InternalBufferHandler(call_out_fn)
    logger_name = logger.name
    formatter = logging.Formatter(
        f"{logger_name}: %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class InternalBufferHandler(logging.Handler):
    def __init__(self, call_out_fn):
        super().__init__()
        self.call_out_fn = call_out_fn

    def emit(self, record:logging.LogRecord)-> None:
        """when an information is logged, send the information into the internal buffer."""
        msg = self.format(record)
        self.call_out_fn(msg, record.levelname)


