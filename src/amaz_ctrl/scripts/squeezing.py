
from amaz_ctrl.scripts.base.amaz_script import AmazingScript
import time, os, logging
log = logging.getLogger("SCRIPT")
import numpy as np
import math,random
from amaz_ctrl.scripts.subscripts.spectrum_anal_agilent import SpectrumAnalyzerAgilent
from amaz_ctrl.scripts.subscripts.laser import Laser
from amaz_ctrl.scripts.subscripts.spectrum_anal_rigol import SpectrumAnalyzerRigol
from amaz_ctrl.scripts.subscripts.scope_rigol2202A import ScopeRigol2202A
from amaz_ctrl.scripts.subscripts.scope_rigolDS1104 import ScopeRigolDS1104
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import pyvisa
from amaz_ctrl.tools.misc import get_windows_pyvisa_ressuorce_manager
rm = get_windows_pyvisa_ressuorce_manager()
import pandas as pd


class Script(AmazingScript):
    """A Script that inherits the AmazingScript possesses the following attributs:
    * _exp_params: a dictionary with the parameters of the experiment to run. Updated in a sequence of experiments. Saved at the end of the experiment. 
    * seq_number: the number of the sequence,
    * i_exp: the ith experiment of the sequence,
    * j_run: the jth run of the experiment,
    * seq_directory: the path to the directory of the sequence,
    * exp_directory: the path to the directory of the experiment,
    * run_prefix: the prefix for the path to save data associated to the run /path/to/exp/folder/0045_

    --------------------
    
    It also inherits the following methods:
    * start_sequence: starts a sequence of experiments (or only one experiments). Load parameter
    """
    def __init__(self,exp_params_dir=r"C:\Users\Carla Quantum Lab\amaz_ctrl\src\amaz_ctrl\scripts",
                 data_root_dir=r"C:\Users\Carla Quantum Lab\Documents\Lab Folder\Data",
                 log_level="INFO"):
        super().__init__(exp_params_dir=exp_params_dir,
                         data_root_dir = data_root_dir,
                         log_level=log_level)

    def prepare_experiment(self):
        ##################
        ## -- Agilent Spectrum Analyzer
        ##################
        self.sa_agilent = SpectrumAnalyzerAgilent(params=self.exp_params)
        self.sa_agilent.set_params()
        

        ##################
        ## -- Rigol Spectrum Analyzer --
        ##################
        self.log.info("Trying to connect to the Rigol Spetrum Analyzer.")
        self.sa_rigol = SpectrumAnalyzerRigol(params=self.exp_params)
        # self.sa_rigol.set_params() # connect and set parameters
        ## Wait for the manual trigger
        self.sa_rigol.instr.write(":INITiate:CONTinuous OFF")
        self.log.info("Connected to the Rigol Spectrum analyzer.")
        
        ##################
        ## -- Rigol Scope 2202A (probe & conjugate) --
        ##################
        self.scope_rigol2 = ScopeRigol2202A(params=self.exp_params)
        self.scope_rigol2.connect()
        ### We want the Rigol scope to have the same timebase as the spectrum analyzer
        timebase = self.sa_rigol.get_sweep_time() #in seconds
        # self.scope_rigol2.set_timebase(total_time = timebase)
        # self.scope_rigol2.set_single_bus_triggered()
        self.scope_rigol2.configure_for_squeezing()
        self.log.info("Connected to the Rigol2 entries oscilloscope.")

        ##################
        ## -- Laser -- 
        ##################
        self.laser = Laser(params=self.exp_params)
        self.laser.update_photon_detuning_from_device_frequency()

        ##################
        ## -- Rigol Scope 2202A (lockin scope) --
        ##################
        self.scope_rigol4 = ScopeRigolDS1104(params= self.exp_params)
        




    def connect_sensors(self):
        log.info("Setting up sensors...")

        
        # ip = "169.254.205.155"
        # self.scope = rm.open_resource(f"TCPIP0::{ip}::INSTR")
        log.info("Sensors ready")



    def measure_linewidth(self, result:dict)->dict:
        """measure the linewidth of the laser using the Agilent Spectrum analyzer"""
        freq, ampli = self.sa_agilent.get_trace()
        p0=[80, np.max(ampli)*0.8, .35, 0 ]
        ## mask 
        mask = np.abs(freq-80) > 0.03
        popt, pcov = curve_fit(lorentzian,
                               freq[mask],
                               ampli[mask], p0=p0,method="dogbox",
                        bounds=([78, 0, .001, 0],[83, 200,5,10])
                        )
        df = pd.DataFrame({"Freq":freq, "Ampli":ampli})
        df.to_csv(self.run_prefix+"raw.csv")
        perr = np.sqrt(np.diag(pcov))
        result["Amplitude"] = popt[1]
        result["Gamma (kHz)"] = popt[2] *1000
        result["U(Amplitude)"] = perr[1]
        result["U(Gamma) (kHz)"] = perr[2] *1000
        error = np.sum((lorentzian(freq, *popt)-ampli)**2)
        result["Fit error"] =error


        

        # if random.random()<0.03:
        #     fig, ax = plt.subplots()
        #     ax.plot(freq, ampli,label = "exp",color = "C0", alpha = .7 )
        #     ax.plot(freq[mask],ampli[mask],label = "exp",color = "C1", alpha = .7 )
        #     ax.plot(freq, lorentzian(freq, *popt),
        #             "--", label = r"$\Gamma=${:.0f} kHz".format(1000*popt[2]), color = "black",)
        #     ax.set_xlabel("Frequency (MHz)")

        #     ax.set_ylabel("Power (V)")
        #     ax.legend()
        #     fig.savefig(self.run_prefix+"plot.png")
        #     plt.close()
        return result
    
    def disconnect_sensors(self):
        log.info("... Disconnected !")


    def get_squeezing(self, result:dict):
        """function that reads squeezing from the spectrum analyzer and normalize it with respect to the shot noise using the measured signal from the Rigol scope."""
        
        ## We trigg the scope and the spectrum analyzer
        self.scope_rigol2.trigger_now()
        ch1 = self.scope_rigol2.get_trace_volts(channel=1) 
        ch2 = self.scope_rigol2.get_trace_volts(channel=2)
        self.sa_rigol.write('init:cont 0')
        # self.sa_rigol.query(":INITiate:IMMediate;*OPC?") #this query block the rigol spectrum analyzer until it finished the trace
        t0 = time.time()
        while time.time()-t0<2.5:#bug SA until trace is done
            if not float(self.sa_rigol.query('swe:coun:curr?'))<1:
                break
            time.sleep(.1)
        sa_trace_points = self.sa_rigol.get_trace()
        time.sleep(.2)
        
        result["Probe voltage (V)"] = np.mean(ch1)
        result["Conjugate voltage (V)"] = np.mean(ch2)
        if np.mean(ch1) + np.std(ch1) < np.mean(ch2) -np.std(ch2):
            self.log.warning("The power of the probe is smaller than the power of the conjugate. Make sure the cables are not inversed. Probe in channel 1 and Conjugate in 2.")

        ##############################################
        ##### ---- Compute the associated shot noise
        ##############################################

        datapower = np.mean(ch1 + ch2)
        ## Shot noise 13-11-2025 No cell PM
        Shot_m=1.580273*10**-11
        Shot_y0=1.656814*10**-12
        shot_noise_watts = Shot_m * datapower + Shot_y0
        result["Shot noise (W)"] = shot_noise_watts
        result["Shot noise (dB)"] =WattstodBm(shot_noise_watts)

        noise_power = np.mean(dBmtoWatts(sa_trace_points))
        measured_sqz=10*np.log10(noise_power / shot_noise_watts)
        result["Squeezing (dB)"] = measured_sqz
        result["Noise Power (dB)"] = WattstodBm(noise_power)

        return result

    def acquire(self)->dict:
        result={}
        self.log.info("Reading squeezing...")
        result = self.get_squeezing(result)
        self.log.info("...done!")
        result = self.measure_linewidth(result)
        volt = self.scope_rigol4.get_voltage_trace(1)
        result["Power before 2km fiber (V)"] =float(np.mean(volt))
        volt = self.scope_rigol4.get_voltage_trace(3)
        result["Seed power (V)"] =float(np.mean(volt))

        # time.sleep(2.)
        # freq, ampli = self.sa_rigol.get_spectrum()

        # t, probe  = self.scope_rigol2.get_trace(channel = 1)
        # t, conj  = self.scope_rigol2.get_trace(channel = 2)
        

        # idx = np.argmin(np.abs(freq-1.5))
        # result["Noise power"] = ampli[idx]
        # result["Probe"] = np.mean(probe)
        # result["Conjugate"] = np.mean(conj)

        # 
            
        return result
    
    def on_experiment_about_to_start(self):
        """method called before an experiment starts so that the user can do whatever they want at this stage."""
        pass

    def on_experiment_about_to_end(self):
        """method called before after an experiment finished so that the user can do whatever they want at this stage. 
        We could modify the dataframe self.experiment_result 
        """
        pass
    def on_sequence_about_to_start(self):
        """method called before a sequence of experiments starts so that the user can do whatever they want at this stage."""
        pass
    
    def on_sequence_about_to_end(self):
        """method called before after a sequence of experiments finished so that the user can do whatever they want at this stage."""
        pass


def lorentzian( x, x0, a, gam, offset ):
    return a * (gam/2)**2 / ( (gam/2)**2 + ( x - x0 )**2) + offset

def dBmtoWatts(dBm):
    Watts=10**(dBm/10-3)
    return Watts

def WattstodBm(Watts):
    dBm=10*np.log10(Watts/10**-3)
    return dBm


if __name__ == "__main__":
    script = Script()
    # scanned_params_dict = script.load_scanned_parameters()
    # list_of_experiments = script.build_list_of_experiments(scanned_params_dict)
    script.main()

