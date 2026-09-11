from amaz_ctrl.scripts.base.amaz_instrument import AmazingInstrument
import pyvisa
import numpy as np
rm = pyvisa.ResourceManager()


class RigolWFG(AmazingInstrument):
    max_freq_MHz = 200
    _frequency_range_MHz = [50, 110]
    max_power_dBm = -5
    name="RigolDevice"

    def set_frequency(self, freq_Hz: float):
        """Set RF output frequency in Hz."""
        freq_MHz = float(freq_Hz) / 1e6
        if  np.min(self._frequency_range_MHz)< freq_MHz>np.max(self._frequency_range_MHz) :
            self.log.error(f"The RF frequency of the {self.name} cannot exceed {self.max_freq_MHz}MHz.")
            return
        self.instr.write(f":FREQ {freq_Hz}Hz")

    def set_power(self, power_dbm: float):
        """
        Set RF output power in dBm.
        """
        if power_dbm > self.max_power_dBm:
            self.log.error(f"THe power of the {self.name} cannot exceed {self.max_power_dBm} dBm.")
            return
        self.instr.write(f":POW {power_dbm}DBM")

    def get_output_state(self):
        """Return RF output state (ON/OFF)."""
        return self.instr.query(":OUTP?")

    def get_frequency(self):
        """Query current RF frequency."""
        return float(self.instr.query(":FREQ?"))

    def get_power(self):
        """Query current RF output power."""
        return float(self.instr.query(":POW?"))


class RigolDSG815(RigolWFG):
    _frequency_range_MHz = [70,130]
    max_freq_MHz = 200
    max_power_dBm = -5

    def set_parameters(self):
        return


    def connect(self):
        """Connect to the Rigol DSG815 signal generator via LAN (SCPI socket)."""
        self.ip = self.params["laser Rigol DSG815 LAN"]
        self.instr = rm.open_resource(f"TCPIP0::{self.ip}::INSTR")
        self.instr.read_termination = '\n'
        self.instr.write_termination = '\n'
    def disconnect(self):
        self.instr.close()

class RigolDSG830(RigolWFG):
    ## set the default parameters
    _frequency_range_MHz = [1450,1550]
    max_power_dBm = 30

    def connect(self):
        """Connect to the Rigol DSG830 signal generator via LAN (SCPI socket)."""
        self.ip = self.params["laser Rigol DSG830 LAN"]
        self.instr = rm.open_resource(f"TCPIP0::{self.ip}::INSTR")
        self.instr.read_termination = '\n'
        self.instr.write_termination = '\n'
    def disconnect(self):
        self.instr.close()

    def set_parameters(self):
        """Configure RF generator parameters using the parameters."""
        return
        self.set_frequency(self.params["laser Rigol DSG830 freq (GHz)"])
        self.set_power(self.params["laser Rigol DSG830 power (dBm)"])
        self.instr.write(":OUTP ON")
