
from amaz_ctrl.scripts.base.amaz_instrument import AmazingInstrument
import pyvisa
import numpy as np
import time

rm = pyvisa.ResourceManager()

class SpectrumAnalyzerAgilent(AmazingInstrument):
    last_trigg = time.time()
    def_params = {
            "SA Agil connected": True,
            "SA Agil address": "TCPIP0::172.17.55.58::5025::SOCKET",
            "SA Agil freq center (MHz)": 80,
            "SA Agil freq span (MHz)": 5,
            "SA Agil RBW (kHz)": 10,
            "SA Agil VBW (kHz)": 1,
            "SA Agil y scale": "lin",
            'SA Agil y max (dBm)':0,
            'SA Agil y div (dB)':20,
            'SA Agil y max (V)': 130e-6,
            "SA Agil attenuation (dB)": 0,
            "SA Agil Detection Method": "normal",
            "SA Agil Continuous mode": False,
            "SA Agil Average trace No": 100,
            "SA Agil timeout (s)":100,
        }

    def connect(self):
        self._is_connected = self.params["SA Agil connected"]
        self.addr =  self.get_param("SA Agil address")
        if not self._is_connected:
            self.log.info("SA Agilent is not connected: setting it in dummy mode.")
            return
        self.instr = rm.open_resource(self.addr)
        self.instr.read_termination = '\n'
        self.instr.write_termination = '\n'

    def set_params(self): 
        if not self._is_connected:
            return
        self.instr.write(f"SENS:FREQ:CENT {self.params['SA Agil freq center (MHz)']} MHz")
        self.instr.write(f"SENS:FREQ:SPAN {self.params['SA Agil freq span (MHz)']} MHz")
        self.instr.write("SENS:BAND:RES:AUTO OFF")
        self.instr.write(f"SENS:BAND:RES {self.params['SA Agil RBW (kHz)']} kHz")
        self.instr.write("SENS:BAND:VID:AUTO OFF")
        self.instr.write(f"SENS:BAND:VID {self.params['SA Agil VBW (kHz)']} kHz")
        ## Set amplitude
        self.instr.write(":POWer:ATTenuation:AUTO OFF")
        self.instr.write(f":POWer:ATTenuation {self.params['SA Agil attenuation (dB)']}")
        
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

        ### Set the continueous mode and the average number
        self.is_continuous = self.get_param("SA Agil Continuous mode")
        if self.is_continuous:
            self.instr.write("INIT:CONT ON")
        else:
            self.instr.write("INIT:CONT OFF")
        self.n_average= int(self.get_param("SA Agil Average trace No"))
        self.instr.write(f"AVER:COUN {self.n_average}")
        self.set_detection_type()
        self.timeout = self.get_param("SA Agil timeout (s)")


    def set_detection_type(self, ):
        """Specifies the detection mode.
        For each trace interval (bucket), average detection displays the average of all the samples within the interval. 
        The averaging can be done using two methods: 
            the power method (RMS) 
            the video method (Y Axis Units)
        • Negative peak detection displays the lowest sample taken during the interval being displayed. 
        • Positive peak detection displays the highest sample taken during the interval being displayed. 
        • Sample detection displays the sample taken during the interval being displayed, and is used primarily to display noise or noise-like signals. In sample mode, the instantaneous signal value at the present display point is placed into memory. This detection should not be used to make the most accurate amplitude measurement of non noise-like signals. 
        • Average detection is used when measuring the average value of the amplitude across each trace interval (bucket). The averaging method used by the average detector is set to either video or power as appropriate when the average type is auto coupled. 
        • Normal detection selects the maximum and minimum video signal values alternately. When selecting Normal detection, “Norm” appears in the upper-left corner.
        """
        if not self._is_connected:
            return
        info = [
          "Negative peak detection displays the lowest sample taken during the interval being displayed. ",
          "Positive peak detection displays the highest sample taken during the interval being displayed. ",
          "Sample detection displays the sample taken during the interval being displayed, and is used primarily to display noise or noise-like signals. In sample mode, the instantaneous signal value at the present display point is placed into memory. This detection should not be used to make the most accurate amplitude measurement of non noise-like signals. ",
          " Average detection is used when measuring the average value of the amplitude across each trace interval (bucket). The averaging method used by the average detector is set to either video (i.e. ) or power as appropriate when the average type is auto coupled. (not recommanded, check the doc) "
          "RMS average the power (recommanded)",
           "Normal detection selects the maximum and minimum video signal values alternately. When selecting Normal detection, “Norm” appears in the upper-left corner."


        ]

        # self.instr.write("SENS:DET:FUNC:AUTO OFF")
        user_cmd = self.params["SA Agil Detection Method"].lower()
        valid_cmd = ["NEGative", "POSitive", "SAMPle", "AVERage", "RMS", "NORMAL"]
        rec_cmd = []# list of recognized command
        for cmd in valid_cmd:
            if user_cmd in cmd.lower():
                rec_cmd.append(cmd)
        if len(rec_cmd)==1:
            cmd = rec_cmd[0]
            self.instr.write(f"SENS:DET:FUNC {cmd}")
        else:
            self.log.warning(f"The detection method of the Agilent scope was not recognized. Setting it to Normal mode. Possible commands are {valid_cmd}. We provide more informations below.")
            for i, j in zip(info,valid_cmd) :
                self.log.info(j +" | " + i)
            self.log.warning("Please look at the previous warning message.")
            self.instr.write(f"SENS:DET:FUNC NORMAL")

    
    def get_sweep_time(self)-> float:
        """return the sweep time of the SA (seconds)"""
        if not self._is_connected:
            return 0.000001
        return float(self.instr.query(':SWE:TIME?'))


    def trigg(self):
        if not self._is_connected:
            return
        self.instr.write(":INITiate")

    

    def get_trace(self):
        """
        Returns frequency (MHz) or time (s) and amplitude (V or dBm depending on instrument setting)
        from a spectrum analyzer trace.
        """
        if not self._is_connected:
            self.log.info("Agilent SA in dummy mode: generating fake data.")
            return np.linspace(
				self.params["SA Agil freq center (MHz)"]-self.params["SA Agil freq span (MHz)"]/2,
				self.params["SA Agil freq center (MHz)"]+self.params["SA Agil freq span (MHz)"]/2,
				101), np.zeros(101) - 100
             
        ## If the agilent was triggered, we wait that it finished his job
        if not self.is_continuous:
            time.sleep(.2)
        timeout = False
        t = time.time()
        while not timeout:
            #This query returns the decimal value of the sum of the bits in the 
            # Status operation condition register.
            opc_value = int(self.instr.query(":STATus:OPERation:CONDition?"))
            ## Bit 4 gives the measurement status
            is_still_measuring =(opc_value >> 4) & 1
            if not is_still_measuring:
                timeout = True
            
            else:
                time.sleep(1.)
            if time.time() - t >self.timeout:
                timeout=True
                self.log.error("The Agilent Spectrum analyzer did not finished the measurement. Timeout occured.")
                continue
            
            

        # --- Get trace data (amplitude only) ---
        trace = self.instr.query("TRAC? TRACE1")
        amplitudes = np.array(trace.split(","), dtype=float)
        # --- Get frequency settings ---
        center = float(self.instr.query("SENS:FREQ:CENT?"))
        span = float(self.instr.query("SENS:FREQ:SPAN?"))
        if span ==0:
             # --- ZERO SPAN MODE (time trace, not frequency) ---
            sweep_time = float(self.instr.query("SWE:TIME?"))
            # time axis
            frequencies = np.linspace(0, sweep_time, len(amplitudes))
        else:
            # --- Build frequency axis ---
            start_freq = center - span / 2
            stop_freq = center + span / 2
            frequencies = np.linspace(start_freq, stop_freq, len(amplitudes))
        
        return frequencies/1e6, amplitudes

if __name__=="__main__":
    sa = SpectrumAnalyzerAgilent()
    sa.set_params()
    print(sa.instr.query("*IDN?"))
    import matplotlib.pyplot as plt
    x, y = sa.get_trace()
    plt.plot(x, y)
    plt.show()
