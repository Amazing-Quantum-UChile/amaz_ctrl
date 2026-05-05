from amaz_ctrl.scripts.base.amaz_instrument import AmazingInstrument
import pyvisa
rm = pyvisa.ResourceManager()




class Laser():
    pass

class RigolDSG815(AmazingInstrument):
    def_params = {
        "Laser Rigol DSG830 LAN": "172.17.55.113",
        "Laser Rigol DSG830 freq (GHz)": 1.510,
        "Laser Rigol DSG830 power (dBm)": 15,
        "RF output state": "ON",
    }

    def connect(self):
        """Connect to the Rigol DSG815 signal generator via LAN (SCPI socket)."""
        self.ip = self.params["Laser Rigol DSG830 LAN"]
        self.instr = rm.open_resource(f"TCPIP0::{self.ip}::INSTR")
        self.instr.read_termination = '\n'
        self.instr.write_termination = '\n'

    def set_params(self, params={}):
        """Configure RF generator parameters."""

        self.params = params
        self.connect()
        self.set_frequency(self.params["Laser Rigol DSG830 freq (GHz)"])
        self.set_power(self.params["Laser Rigol DSG830 power (dBm)"])
        self.instr.write(":OUTP ON")


    # -------------------------
    # Frequency control
    # -------------------------
    def set_frequency(self, freq_ghz: float):
        """Set RF output frequency in GHz."""
        if freq_ghz>3:
            self.log.error("The RF frequency of the RigolDSG815 cannot exceed 3GHz.")
            return
        self.instr.write(f":FREQ {freq_ghz}GHz")

    # -------------------------
    # Power control (with safety check)
    # -------------------------
    def set_power(self, power_dbm: float):
        """
        Set RF output power in dBm.
        Safety limit: max +15 dBm.
        """
        MAX_POWER_DBM = 16
        if power_dbm > MAX_POWER_DBM:
            self.log.error("THe power of the RigolDSG815 cannot exceed 15 dBm.")
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
    

if __name__=="__main__":
    wfg = RigolDSG815()
    wfg.set_params()

