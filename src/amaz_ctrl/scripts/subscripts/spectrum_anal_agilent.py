
from amaz_ctrl.scripts.base.amaz_instrument import AmazingInstrument
import pyvisa
import numpy as np

rm = pyvisa.ResourceManager()

class SpectrumAnalyzerAgilent(AmazingInstrument):
    def_params = {
            "SA Agil LAN": "172.17.55.214",
            "SA Agil port": "5025",
            "SA Agil freq center (MHz)": 80,
            "SA Agil freq span (MHz)": 5,
            "SA Agil RBW (kHz)": 10,
            "SA Agil VBW (kHz)": 1,
            "SA Agil y scale": "lin",
            'SA Agil y max (dBm)':0,
            'SA Agil y div (dB)':20,
            'SA Agil y max (V)': 130e-6,
            "SA Agil attenuation (dB)": 0,
        }

    def connect(self):
        self.ip = self.get_param("SA Agil LAN")
        self.port =  self.get_param("SA Agil port")
        self.instr = rm.open_resource(f"TCPIP0::{self.ip}::{self.port}::SOCKET")
        self.instr.read_termination = '\n'
        self.instr.write_termination = '\n'

    def set_params(self, params={}):
        self.params = params
        self.connect()
        self.instr.write(f"SENS:FREQ:CENT {self.params['SA Agil freq center (MHz)']} MHz")
        self.instr.write(f"SENS:FREQ:SPAN {self.params['SA Agil freq span (MHz)']} MHz")
        self.instr.write("SENS:BAND:RES:AUTO OFF")
        self.instr.write(f"SENS:BAND:RES {self.params['SA Agil RBW (kHz)']} kHz")
        self.instr.write("SENS:BAND:VID:AUTO OFF")
        self.instr.write(f"SENS:BAND:VID {self.params['SA Agil VBW (kHz)']} kHz")
        ## Set amplitude
        if self.params["SA Agil y scale"].lower() in "linear":
            self.instr.write("DISP:WIND:TRAC:Y:SPAC LIN")
            self.instr.write("UNIT:POW V")
            self.instr.write(f"DISP:WIND:TRAC:Y:RLEV {self.params['SA Agil y max (V)']}V")
        else:
            self.instr.write("DISP:WIND:TRAC:Y:SPAC LOG")
            self.instr.write("UNIT:POW DBM")
            self.instr.write(f"DISP:WIND:TRAC:Y:RLEV {self.params['SA Agil y max (dBm)']}DBM")
            self.instr.write(
                f"DISP:WIND:TRAC:Y:PDIV {self.params['SA Agil y div (dB)']}"
            )

        ## Input atenuation
        self.instr.write("INP:ATT:AUTO OFF")
        self.instr.write(f"INP:ATT {self.params['SA Agil attenuation (dB)']} dB")

    def get_trace(self):
        """
        Returns frequency (MHz) and amplitude (V or dBm depending on instrument setting)
        from a spectrum analyzer trace.
        """

        # --- Get trace data (amplitude only) ---
        trace = self.instr.query("TRAC? TRACE1")
        amplitudes = np.array(trace.split(","), dtype=float)

        # --- Get frequency settings ---
        center = float(self.instr.query("SENS:FREQ:CENT?"))
        span = float(self.instr.query("SENS:FREQ:SPAN?"))

        # --- Build frequency axis ---
        start_freq = center - span / 2
        stop_freq = center + span / 2
        frequencies = np.linspace(start_freq, stop_freq, len(amplitudes))

        # --- Return both ---
        return frequencies/1e6, amplitudes

if __name__=="__main__":
    sa = SpectrumAnalyzerAgilent()
    sa.set_params()
    print(sa.instr.query("*IDN?"))
    import matplotlib.pyplot as plt
    x, y = sa.get_trace()
    plt.plot(x, y)
    plt.show()
