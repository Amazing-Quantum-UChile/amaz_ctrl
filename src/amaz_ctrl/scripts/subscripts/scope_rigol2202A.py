
from amaz_ctrl.scripts.base.amaz_instrument import AmazingInstrument
import numpy as np
from amaz_ctrl.tools.misc import get_windows_pyvisa_ressuorce_manager
rm = get_windows_pyvisa_ressuorce_manager()

class ScopeRigol2202A(AmazingInstrument):
    def_params = {
        "Scope Rigol2 VISA": "USB0::0x1AB1::0x04B0::DS2D224202244::INSTR",
        }
    numb_of_div = 14 # horizontal number of division


    def connect(self):
        self.visa_adress =  self.get_param("Scope Rigol2 VISA")
        self.instr = rm.open_resource(self.visa_adress)

    def configure_for_squeezing(self):
        scope = self.instr
        # Configuración de canales (ajusta según tu experimento)
        scope.write(f":chan1:scale 1")  # Escala vertical (ej: 1 V/div)
        scope.write(f":chan2:scale 1")   # Misma escala para el canal conjugado

        # Impedancia de entrada (1 MΩ o 50 Ω, depende de tu fotodiodo)
        scope.write(f":chan1:imp 1MEG")   # 1 MEG o FIFTY//(imp 50)
        scope.write(f":chan2:imp 1MEG")

        # Acoplamiento DC (para señales ópticas)
        scope.write(f":chan1:coupl DC")
        scope.write(f":chan2:coupl DC")

        # Limitar ancho de banda (reduce ruido de alta frecuencia)
        scope.write(f":chan1:bwl OFF")    # 20 MHz // OFF // 100M
        scope.write(f":chan2:bwl OFF")

        # Base de tiempo (ajusta según la dinámica de tu señal)
        scope.write(":timebase:scale 0.02")  # 100 ms/div (ejemplo)
        
        # Modo de disparo (para señales periódicas)
        scope.write(":trig:mode edge")  
        scope.write(":trig:edge:sour ext")  # Trigger por entrada externa
        
    def set_timebase(self, total_time:float):
        """set the total aquisition time of the scope. total_time is in seconds
        """
        time_per_div = total_time / self.numb_of_div
        self.instr.write(f':TIMebase:MAIN:SCALe {time_per_div}')

    def get_trace_volts(self,channel=1 ):
        self.instr.write(f":WAV:SOUR CHAN{channel}")
        self.instr.write(":WAV:FORM ASCii")
        # self.instr.write(":WAV:MODE NORM")
        raw_data = self.instr.query(":WAV:DATA?")
        # 
        volts = np.fromstring(raw_data[:-1],sep=',')
        data_str=raw_data.replace(",\n", "")
        # volts = [float(val) for val in data_str.split(',')]
        return volts
    def get_trace(self, channel=1):
        volts = self.get_trace_volts(channel=channel)
        x_inc = float(self.instr.query(":WAV:XINC?"))
        x_orig = float(self.instr.query(":WAV:XOR?"))
        times = [x_orig + (i * x_inc) for i in range(len(volts))]
        return times, volts
    
    
    def set_single_bus_triggered(self):
        # Set to normal sweep so it waits for a trigger and doesn't auto-trigger
        self.instr.write(":TRIGger:MODE USB")
        # Prime the scope to look for a single acquisition
        # self.instr.write(':SINGle')

    def trigger_now(self):
        """Call this method when you want to manually force the trigger."""
        # For Rigol DS2000/MSO2000 series, :TRIGger:FORCe or just :FORCe works
        self.instr.write(':TFORce')