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

def set_console_log(logger_name:str, log_level="INFO"):
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


import logging

class PseudoConsoleToLogger:
    """Redirects standard output streams (like print statements) to a Python logger,

    skipping messages that already begin with designated script prefixes.
    """
    def __init__(self):
        logger_name = "CONSOLE"
        log_level = "DEBUG"
        self.log = logging.getLogger(logger_name)
        # Convert string level (e.g., "INFO") to the numeric logging level (20)
        self.level = getattr(logging, log_level.upper(), logging.INFO)
        self.log.setLevel("DEBUG") 
        set_console_log(logger_name,log_level )    


    def write(self, message: str) -> None:
        """Intercepts the written text and routes it to the logger
        """
        clean_message = message.strip()
        # Avoid logging empty lines/newlines
        if not clean_message:  
            return
        # Filtering strategy: ignore if it already comes from your log framework
        # if clean_message.startswith("\x1b[") or clean_message.startswith("CONSOLE:"):
        #     return  # Skip it, it's already a processed log message
            
        self.log.log(self.level, message.rstrip())
            

    def flush(self) -> None:
        """Required for stream compatibility, prevents buffer errors."""
        pass