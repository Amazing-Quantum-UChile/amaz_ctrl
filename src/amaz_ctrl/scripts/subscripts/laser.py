from amaz_ctrl.scripts.base.amaz_instrument import AmazingInstrument
import pyvisa
rm = pyvisa.ResourceManager()




class Laser(AmazingInstrument):
    f_25P = 377.107385960 *10**12 + 1.7708439228 * 10 ** 9 # transición F=2 --> 5P_{1/2}
    f_22 =f_25P - 210.923*10**6 # transición F=2-->F'=2
    f_23 =f_25P + 150.659*10**6 # transición F=2-->F'=3
    f_2_23 = (f_22+f_23)/2 # Crossover
    f_12 = 3.0357324390 * 10**9 # distancia estados basales F=2-->F=3
    _def_params = {}

    def __init__(self, params, log_level="INFO"):
        super().__init__(params, log_level)
        self.rigoldsg830 = RigolDSG830(self.params, log_level)
        self.rigoldsg815 = RigolDSG815(params, log_level)

    def connect(self):
        # Conneciton is done in subdevice
        pass

    
    def update_photon_detuning_from_device_frequency(self):
        """update the parameter dictionary using the locking transition and the frequency of the AOM."""
        self.locking_frequency = 0
        transition_str = self.params["laser locking transition"].lower()
        if transition_str in "crossover":
            self.locking_frequency = self.f_2_23
        elif transition_str in "22 f=2->f'=2":
            self.locking_frequency = self.f_22
        elif transition_str in "23 f=2->f'=3":
            self.locking_frequency = self.f_23
        else:
            self.log.warning(f"The transition frequency on which you locked the laser '{transition_str}' was not recognized. Setting it to the default transition peak: the crossover F'=2/F'=3.")
            self.locking_frequency = self.f_2_23

        aom1500 = self.rigoldsg830.get_frequency()
        aom200 = self.rigoldsg815.get_frequency()
        self.params["laser 1st AOM frequency (MHz)"] = aom1500 / 1e6
        self.params["laser 2nd AOM frequency (MHz)"] = aom200 / 1e6
        delta_2ph = 2*aom1500 -self.f_12
        delta_1ph =  - 2*aom200 + self.locking_frequency  + aom1500 - self.f_25P
        self.params["laser 2ph detuning (MHz)"] = delta_2ph / 1e6
        self.params["laser 1ph detuning (MHz)"] = delta_1ph / 1e6
        

class RigolWFG(AmazingInstrument):
    max_freq_MHz = 200
    max_power_dBm = -5
    name="RigolDevice"
    def set_frequency(self, freq_MHz: float):
        """Set RF output frequency in GHz."""
        if freq_MHz>self.max_freq_MHz:
            self.log.error(f"The RF frequency of the {self.name} cannot exceed {self.max_freq_MHz}MHz.")
            return
        self.instr.write(f":FREQ {freq_MHz}MHz")

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
    max_freq_MHz = 200
    max_power_dBm = -5

    def set_params(self):
        self.log.warning("This is not yet implemented")

    def connect(self):
        """Connect to the Rigol DSG815 signal generator via LAN (SCPI socket)."""
        self.ip = self.params["laser Rigol DSG815 LAN"]
        self.log.info(f"Connecting to RigolDSG815 {self.ip}")
        self.instr = rm.open_resource(f"TCPIP0::{self.ip}::INSTR")
        self.instr.read_termination = '\n'
        self.instr.write_termination = '\n'


class RigolDSG830(RigolWFG):
    ## set the default parameters
    max_freq_MHz = 3000
    max_power_dBm = 30

    def connect(self):
        """Connect to the Rigol DSG830 signal generator via LAN (SCPI socket)."""
        self.ip = self.params["laser Rigol DSG830 LAN"]
        self.log.info(f"Connecting to RigolDSG830 {self.ip}")
        self.instr = rm.open_resource(f"TCPIP0::{self.ip}::INSTR")
        self.instr.read_termination = '\n'
        self.instr.write_termination = '\n'

    def set_params(self):
        """Configure RF generator parameters using the parameters."""
        self.connect()
        self.set_frequency(self.params["laser Rigol DSG830 freq (GHz)"])
        self.set_power(self.params["laser Rigol DSG830 power (dBm)"])
        self.instr.write(":OUTP ON")



if __name__=="__main__":
    import json, os
    # wfg = RigolDSG830()
    # wfg.set_params()
    # laser = Laser
    script_dir = os.path.dirname(os.path.abspath(__file__))
    fpath = os.path.abspath(os.path.join(script_dir, "..", "exp_params.json"))
    with open(fpath, 'r', encoding='utf-8') as file:
        exp_params = json.load(file)
    laser = Laser(params=exp_params)
    laser.update_photon_detuning_from_device_frequency()
