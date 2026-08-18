
from amaz_ctrl.scripts.base.amaz_instrument import AmazingInstrument
import numpy as np
from amaz_ctrl.tools.misc import get_windows_pyvisa_ressuorce_manager
rm = get_windows_pyvisa_ressuorce_manager()


class SpectrumAnalyzerRigol(AmazingInstrument):
    def_params = {
        "SA Rigol VISA": "USB0::0x1AB1::0x0960::DSA8H200600069::INSTR",
        "SA Rigol freq center (MHz)": 80,
        "SA Rigol freq span (MHz)": 5,
        "SA Rigol RBW (kHz)": 10,
        "SA Rigol VBW (kHz)": 1,
        "SA Rigol sweep time (s)":1
        }
    def connect(self):
        self.visa_adress =  self.get_param("SA Rigol VISA")
        self.instr = rm.open_resource(self.visa_adress)

    def disconnect(self):
        self.instr.close()


    def set_parameters(self):
        SA = self.instr
        SA.write(':SENS:FREQ:CENT 1MHz')
        # Configura span a 0 Hz (modo Zero Span)
        SA.write(':SENS:FREQ:SPAN 0Hz')
        # Configura RBW adecuada para mediciones de ruido (ajustable)
        SA.write(':SENS:BAND:RES 30kHz')
        # Configura VBW (opcional, puede ser igual a RBW)
        SA.write(':SENS:BAND:VID 30Hz')
        # Configura detector a RMS para mediciones de ruido
        SA.write(':DET RMS')
        # Configura tiempo de barrido (ajustable según necesidades)

        SA.write(':SENS:SWE:TIME 1s') 
        # freq = self.get_param('SA Rigol freq center (MHz)')
        # self.instr.write(f"SENS:FREQ:CENT {freq} MHz")
        # span = self.get_param('SA Rigol freq span (MHz)')
        # if span ==0:
        #     ## set the SA sweep time
        #     self.instr.write(f"SENS:FREQ:SPAN 0Hz")
        #     sweep_time_param = self.get_param('SA Rigol sweep time (s)')
        #     self.instr.write(':SWEep:TIME:AUTO OFF')
        #     ## Configure le sweep time sur l'appareil
        #     self.instr.write(f':SWEep:TIME {sweep_time_param}')
        # else:
        #     self.instr.write(':SWEep:TIME:AUTO ON')
        #     self.instr.write(f"SENS:FREQ:SPAN {span}MHz")
        # self.instr.write("SENS:BAND:RES:AUTO OFF")
        # rbw = self.get_param('SA Rigol RBW (kHz)')
        # self.instr.write(f"SENS:BAND:RES {rbw}kHz")
        # self.instr.write("SENS:BAND:VID:AUTO OFF")
        # vbw = self.get_param('SA Rigol VBW (kHz)')
        # self.instr.write(f"SENS:BAND:VID {vbw}kHz")
        # # Configura detector a RMS para mediciones de ruido
        # self.instr.write(':DET RMS')
        
        # ## Set timeout using the sweep time + 1 second
        # sweep_time_raw = self.instr.query(':SWEep:TIME?')
        # sweep_time = float(sweep_time_raw)
        # self.instr.timeout = (sweep_time * 1000) + 1000

    def get_trace(self):
        """
        Returns frequency (MHz) and amplitude (V or dBm depending on instrument setting)
        from a spectrum analyzer trace.
        """
        trace = self.instr.query("TRAC? TRACE1")
        amplitudes = np.fromstring(trace[11:],sep=',')
        return amplitudes
    
    def get_spectrum(self):
        amplitudes = self.get_trace()
        # --- Get frequency settings ---
        center = float(self.instr.query("SENS:FREQ:CENT?"))
        span = float(self.instr.query("SENS:FREQ:SPAN?"))
        # --- Build frequency axis ---
        start_freq = center - span / 2
        stop_freq = center + span / 2
        frequencies = np.linspace(start_freq, stop_freq, len(amplitudes))
        # --- Return both ---
        return frequencies/1e6, amplitudes
    
    def get_sweep_time(self)-> float:
        """return the sweep time of the SA (seconds)"""
        return float(self.instr.query(':SWEep:TIME?'))
