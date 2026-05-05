#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Created on the Tue Apr 21 2026 by Victor
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
Content of utils.py

Please document your code ;-).

'''

import logging
import serial
import pyvisa
from amaz_ctrl.tools.amaz_logs import set_console_log
def_logger = logging.getLogger()
set_console_log(logger_name=def_logger.name, log_level="INFO")



def list_usb_ports(logger:logging.Logger=def_logger):
    """list all USB port and their description on the logger."""
    ports = serial.tools.list_ports.comports()
    msg = "Hereafter, we list all USB port of the computer.\n"+"----"*15

    logger.info(msg)
    for port in ports:
        msg=f"Device: {port.device} | "
        msg+=f"Name: {port.name} | "
        msg+=f"Description: {port.description} | "
        msg+=f"HWID: {port.hwid} | "
        msg+=f"VID: {port.vid} | "
        msg+=f"PID: {port.pid} | "
        msg+=f"Serial number: {port.serial_number} | "
        logger.info(msg)


def get_serial_port_from_serial_number(serial_number:str, logger:logging.Logger=def_logger)->str:
    """Return the serial port device path matching a given USB serial number.

    This method scans all available serial ports and returns the device
    name (e.g. 'COM3', '/dev/ttyUSB0') corresponding to the provided
    serial number.

    Parameters
    ----------
    serial_number : str
        The USB serial number of the device to find.

    Returns
    -------
    str
        The device path of the matching serial port.

    Raises
    ------
    serial.SerialException
        If no matching device is found or if multiple devices share the same
        serial number.
    """
    ports = serial.tools.list_ports.comports()
    ##-. We look for the port that matches the good serial number
    selected_ports = []
    for port in ports:
        if port.serial_number == serial_number:
            selected_ports.append(port.device)
    if len(selected_ports)==0:
        msg = "The serial number {} was not identified. Is the device plugged in?".format(serial_number)
        logger.error(msg)
        list_usb_ports(logger)
        raise serial.SerialException(msg)
    elif len(selected_ports)>1:
        msg = "The serial number {} is found on {} different ports. This is weird. Please take a look.".format(serial_number,len(selected_ports) )
        logger.error(msg)
        list_usb_ports(logger)
        raise serial.SerialException(msg)
    else:
        return selected_ports[0]
    
def get_visa_usb_resources(rm:pyvisa.ResourceManager=None):
    if rm is None:
        rm = pyvisa.ResourceManager()
    return rm.list_resources("USB?*::INSTR")

def get_visa_usb_resource_from_serial(serial_no: str,
                                      logger:logging.Logger=def_logger,
                                      rm:pyvisa.ResourceManager=None) -> str:
    """Return the VISA USB resource matching a given serial number.

    This function searches only USB VISA devices and filters them
    by checking if the serial number is contained in the resource string.

    Parameters
    ----------
    serial_no : str
        Serial number of the instrument.

    Returns
    -------
    str
        VISA resource string (e.g. 'USB0::0xXXXX::0xXXXX::SERIAL::INSTR')

    Raises
    ------
    serial.SerialException
        If no device or multiple devices match the serial number.
    """

    # Only USB VISA instruments
    resources = get_visa_usb_resources(rm=rm)
    
    # Filter by serial number inside VISA string
    matches = [r for r in resources if serial_no in r]

    if len(matches) == 0:
        msg = f"No VISA USB device found with serial number '{serial_no}'"
        logger.error(msg)
        raise serial.SerialException(msg)

    if len(matches) > 1:
        msg = f"Multiple VISA USB devices found with serial '{serial_no}': {matches}"
        logger.error(msg)
        raise serial.SerialException(msg)
    return matches[0]

