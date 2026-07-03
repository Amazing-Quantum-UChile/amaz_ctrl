
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
    result = {}
    numb_of_div = 14 # horizontal number of division
    raw_data = {"ch1":np.zeros(10), 
                    "ch2":np.zeros(10),
                    "ch3":np.zeros(10),
                    "ch4":np.zeros(10),
                    "time":np.zeros(10)}


    def connect(self):
        self.visa_adress =  self.get_param("Scope Rigol4 VISA")
        self.instr = rm.open_resource(self.visa_adress)
        self.set_parameters()
        # for i in range(1, 5):
        #     if self.get_param(f"Scope Rigol4 ch{i}"):
        #         v_range = self.get_param(f"Scope Rigol4 ch{i} range (V)")
        #         self.instr.write(f":CHANnel{i}:RANGe {v_range}")


    def set_parameters(self):
        self.instr.write(":WAV:FORM ASCii")
        self.instr.write(":WAV:MODE NORM")


    def set_timebase(self, total_time:float):
        """set the total aquisition time of the scope. total_time is in seconds
        """
        self.log.warning("The set_timebase function is not yet programmed.")


    def get_voltage_trace(self, channel=1)->NDArray:
        self.instr.write(f":WAV:SOUR CHAN{channel}")
        raw_data = self.instr.query(":WAV:DATA?")
        data_str = raw_data[11:] 
        volts = np.fromstring(data_str, sep=',')
        return volts


    def get_trace(self, channel=1)->tuple[NDArray[np.float64], NDArray[np.float64]]:
        """return the time and voltage of a channel"""
        volts = self.get_voltage_trace(channel)
        times = self.get_timebase()
        return times, volts
    

    def get_timebase(self):
        x_inc = float(self.instr.query(":WAV:XINC?"))
        x_orig = float(self.instr.query(":WAV:XOR?"))
        num_points = int(self.instr.query(":WAV:POIN?"))
        times =x_orig + np.arange(num_points) * x_inc
        return times

    
    def set_single_bus_triggered(self):
        self.instr.write(':TRIGger:MODE EDGE')
        self.instr.write(':TRIGger:EDGe:SOURce BUS')
        self.instr.write(':TRIGger:SWEep NORMal')
        self.instr.write(':SINGle')


    def measure(self, result:dict=None)->dict:
        if result is None:
            result = {}
        self.result = {}
        self.raw_data["time"] = self.get_timebase()
        for i in range(1, 5):
            try:
                self.measure_channel(i)
            except Exception as e:
                self.log.warning(f"Rigol4 Driver failed to measure channel {i}. Error is {e}.", 
                         exc_info=True)
        result.update(self.result)
        return result

    def measure_channel(self, i):
        if not self.get_param(f"Scope Rigol4 ch{i}"):
            # return if no measurement required
            self.raw_data[f"ch{i}"] = np.zeros(len(self.raw_data["time"]))
            return
        volts = self.get_voltage_trace(channel = i)
        self.raw_data[f"ch{i}"] = volts
        ch_name = self.get_param(f"Scope Rigol4 ch{i} name")
        if "(" in ch_name and ")" in ch_name:
            suffix = ""
        else:
            suffix =" (mV)" # we add the unit
        self.result[ch_name + " mean"+ suffix] = float(np.mean(volts)*1000)
        self.result[ch_name + " std"+ suffix] = float(np.std(volts)*1000)












