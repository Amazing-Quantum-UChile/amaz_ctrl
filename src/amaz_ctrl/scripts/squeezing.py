
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
from amaz_ctrl.scripts.subscripts.powermeter_thorlabs import PowerMeterThorlabsPM16
from amaz_ctrl.scripts.subscripts.spectrum_anal_tiny import  SpectrumAnalyzerTiny
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
        self.sa_rigol.set_params() # connect and set parameters
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

        ##################
        ## Thorlabs Power Meter
        ##################
        # self.power_meter = PowerMeterThorlabsPM16(params=self.exp_params)

        ##################
        ## TinySA
        ##################
        self.sa_tiny = SpectrumAnalyzerTiny(params=self.exp_params)
        self.sa_tiny.set_params()



    

    def connect_sensors(self):
        # self.power_meter.open()
        return
    
    def disconnect_sensors(self):
        # time.sleep(1.)
        # self.power_meter.close()
        # time.sleep(1.)
        # self.power_meter.close()
        return


    def measure_linewidth(self, result:dict)->dict:
        """measure the linewidth of the laser using the Tiny SA Spectrum analyzer"""
        freq, ampli = self.sa_tiny.get_trace()
        ## Go into W instead of dB
        ampli = 10**(ampli)/1000
        df = pd.DataFrame({"Freq":freq, "Ampli":ampli})
        if self.exp_params["SA Tiny save raw data"]:
            df.to_csv(self.run_prefix+"linewidth_raw.csv")
        central_freq = 80
        
        ## mask because we 
        mask_DX = self.exp_params["SA Tiny RBW (kHz)"] * 0.001 * 2
        mask = np.abs(freq-central_freq) > mask_DX
        p0=[central_freq, np.max(ampli[mask])*1.2, .35, 0 ]
        popt, pcov = curve_fit(lorentzian,
                               freq[mask],
                               ampli[mask], p0=p0,method="dogbox",
                        bounds=([78, 0, .001, 0],[83, 5400,5,10])
                        )
        
        perr = np.sqrt(np.diag(pcov))
        result["Amplitude"] = popt[1]
        result["Gamma (kHz)"] = popt[2] *1000
        result["U(Amplitude)"] = perr[1]
        result["U(Gamma) (kHz)"] = perr[2] *1000
        error = np.sum((lorentzian(freq, *popt)-ampli)**2)
        result["Fit error"] = error
        if self.j_run %30 ==0:
            fig,ax = plt.subplots()
            ax.plot(freq, ampli, "o", color ="C0")
            ax.plot(freq, lorentzian(freq, *popt), color = "C0")
            ax.plot(freq, lorentzian(freq, *p0), color = "grey", ls = "--")
            ax.axvspan(central_freq-mask_DX, central_freq+mask_DX, color = "red", alpha = .2)
            ax.set_xlabel("Frequency (MHz)")
            ax.set_ylabel("Amplitude (a.u.)")
            ax.set_ylim(top = max(np.max(ampli[mask])*1.4, popt[1])*1.15, bottom = 0)
            plt.tight_layout()
            fig.savefig(self.run_prefix+"beating_fig.png")
        return result
    

    def start_intensity_spectrum_measurement(self):
        self.sa_agilent.instr.write(":INITiate:CONTinuous OFF")
        self.sa_agilent.instr.write("INIT:CONT OFF")
        self.sa_agilent.instr.write("AVER:COUN 500")
        self.sa_agilent.instr.write("AVER:STAT ON")
        self.sa_agilent.instr.write(":INITiate")

    

    def get_intensity_spectrum(self, result):
        freq, ampli = self.sa_agilent.get_trace()
        ### save raw data
        df = pd.DataFrame({"Freq":freq, "Ampli":ampli})
        df.to_csv(self.run_prefix+"intensity_raw.csv")
        ### Now we want to save some raw data for easy analysis
        if self.exp_params['SA Agil freq span (MHz)'] ==0:
            return result
        # we have 1001 frequency measurement, we want 10 of them
        for idx in [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]:
            try:
                f = int(freq[idx])
                result[f"Intensity noise @{f}MHz"]=ampli[idx]
            except Exception as e:
                self.log.error(f"Error in the get intensity spectrum: {e}")
        return result

        
    
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
        if self.j_run % 10 ==0:
            self.log.info(f"Measured Squeezing: {measured_sqz:.03f} dB")
        return result

    def acquire(self)->dict:
        result={}
        ## trigg the measurement of the agilent
        self.sa_agilent.trigg()
        # self.log.info("Reading squeezing...")
        result = self.get_squeezing(result)
        # self.log.info("Squeezing: {:.2f} dB".format(result["Squeezing (dB)"]))
        # result = self.measure_linewidth(result)
        # result = self.get_intensity_spectrum(result)
        freq, ampli = self.sa_agilent.get_trace()
        df = pd.DataFrame({"Freq":freq, "Ampli":ampli})
        df.to_csv(self.run_prefix+"linewidth_raw.csv")
        ## Other parameter measurements
        result = self.scope_rigol4.measure(result)
        # result["Thorlabs power meter (mW)"] = 1000 * self.power_meter.get_power()
       
        try:
            ## calibration done on week 22.
            result["Seed power (uW)"] = 0.03956*result["Seed power mean (mV)"] - 0.833
            ## calibration done on week 22.
            # result["Pump power (mW)"] = 19.73*result["Thorlabs power meter (mW)"]-6.74
        except:
            self.log.warning("Failed to convert the seed power.", exc_info=True)
        
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

