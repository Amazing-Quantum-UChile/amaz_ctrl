
from amaz_ctrl.scripts.base.amaz_instrument import AmazingInstrument
import numpy as np
from amaz_ctrl.tools.misc import get_windows_pyvisa_ressuorce_manager
rm = get_windows_pyvisa_ressuorce_manager()
from numpy.typing import NDArray
class ScopeRigolDS1104(AmazingInstrument):
    def_params = {
        "Scope Rigol4 VISA": "USB0::0x1AB1::0x04CE::DS1ZA200602016::INSTR",
        "Scope Rigol4 ch1":True,
        "Scope Rigol4 ch1 name":"Channel 1",
        "Scope Rigol4 ch1 range (V)":5,
        "Scope Rigol4 ch2":True,
        "Scope Rigol4 ch2 name":"Channel 2",
        "Scope Rigol4 ch2 range (V)":5,
        "Scope Rigol4 ch3":True,
        "Scope Rigol4 ch3 name":"Channel 3",
        "Scope Rigol4 ch3 range (V)":5,
        "Scope Rigol4 ch4":True,
        "Scope Rigol4 ch4 name":"Channel 4",
        "Scope Rigol4 ch4 range (V)":5
        }
    numb_of_div = 14 # horizontal number of division


    def connect(self):
        self.visa_adress =  self.get_param("Scope Rigol4 VISA")
        self.instr = rm.open_resource(self.visa_adress)


    def set_timebase(self, total_time:float):
        """set the total aquisition time of the scope. total_time is in seconds
        """
        self.log.warning("The set_timebase function is not yet programmed.")

    def get_voltage_trace(self, channel=1)->NDArray:
        self.instr.write(f":WAV:SOUR CHAN{channel}")
        self.instr.write(":WAV:FORM ASCii")
        self.instr.write(":WAV:MODE NORM")
        raw_data = self.instr.query(":WAV:DATA?")
        data_str = raw_data[11:] 
        volts = np.fromstring(data_str, sep=',')
        return volts

    def get_trace(self, channel=1)->tuple[NDArray[np.float64], NDArray[np.float64]]:
        """return the time and voltage of a channel"""
        volts = self.get_voltage_trace(channel)
        x_inc = float(self.instr.query(":WAV:XINC?"))
        x_orig = float(self.instr.query(":WAV:XOR?"))
        num_points = len(volts)
        x_end = x_orig + (num_points * x_inc)
        times = np.arange(x_orig, x_end, x_inc)[:num_points]
        return times, volts
    
    
    def set_single_bus_triggered(self):
        self.instr.write(':TRIGger:MODE EDGE')
        self.instr.write(':TRIGger:EDGe:SOURce BUS')
        self.instr.write(':TRIGger:SWEep NORMal')
        self.instr.write(':SINGle')