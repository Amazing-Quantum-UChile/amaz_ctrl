

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
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import pyvisa
from amaz_ctrl.tools.misc import get_windows_pyvisa_ressuorce_manager
rm = get_windows_pyvisa_ressuorce_manager()
import pandas as pd
import datetime

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
        print("Preparing an experiment.")
        ##################
        ## -- Agilent Spectrum Analyzer
        ##################
        self.sa_agilent = SpectrumAnalyzerAgilent(params=self.exp_params)
        self.sa_agilent.set_params()
        

        # ##################
        # ## -- Laser -- 
        # ##################
        # self.laser = Laser(params=self.exp_params)
        # self.laser.update_photon_detuning_from_device_frequency()

        # ##################
        # ## -- Rigol Scope 2202A (locking scope) --
        # ##################
        # self.scope_rigol4 = ScopeRigolDS1104(params= self.exp_params)
        

        # ##################
        # ## Thorlabs Power Meter
        # ##################
        self.power_meter = PowerMeterThorlabsPM16(params=self.exp_params)

    

    def connect_sensors(self):
        
        self.power_meter.open()
        return
    
    def disconnect_sensors(self):
        # rm.close()
        
        time.sleep(1.)
        self.power_meter.close()
        time.sleep(1.)
        self.power_meter.close()
        return



    def start_intensity_spectrum_measurement(self):
        self.sa_agilent.instr.write(":INITiate:CONTinuous OFF")
        self.sa_agilent.instr.write("INIT:CONT OFF")
        self.sa_agilent.instr.write("AVER:COUN 500")
        self.sa_agilent.instr.write("AVER:STAT ON")
        self.sa_agilent.instr.write(":INITiate")

    def get_intensity_spectrum(self, result):
        ## wait a bit so that we are sure the measurement started
        time.sleep(.3)
        ## We wait for the device to finish the measurement
        t = time.time()
        max_timeout = 50 #seconds
        timeout = False
        max_timeout = 50 #seconds
        timeout = False
        while not timeout:
            #This query returns the decimal value of the sum of the bits in the 
            # Status operation condition register.
            opc_value = int(self.sa_agilent.instr.query(":STATus:OPERation:CONDition?"))
            ## Bit 4 gives the measurement status
            is_still_measuring =(opc_value >> 4) & 1
            
            if not is_still_measuring:
                timeout = True
                # self.log.info(f"The agilent finished in { int(time.time() - t )}s!")
            else:
                time.sleep(1.)
            if time.time() - t >max_timeout:
                timeout=True
                self.log.warning("Timeout from the rigol measurement of the intensity noise...")
                return result
        ## the measurement is finished!
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
    
    def acquire(self)->dict:
        result={}
        self.start_intensity_spectrum_measurement()
        
        result = self.get_intensity_spectrum(result)
        pw_th = self.power_meter.get_power()
        result["Thorlabs power meter (W)"] = pw_th
        try:
            result["Thorlabs power meter (W)"] = pw_th * 1000 
            result["Det10A voltage (mV)"] = 0.785*pw_th * 1000 
        except Exception as e:
            self.log.warning("Failed to convert the thorlabs power.", exc_info=True)
            result["Thorlabs power meter (W)"] = None
            result["Det10A voltage (mV)"] = None


        return result
        
    def average_over_traces(self, result = {}):
        self.sa_agilent.instr.write(":INITiate:CONTinuous OFF")
        self.sa_agilent.instr.write("INIT:CONT OFF")
        self.sa_agilent.instr.write("AVER:COUN 500")
        self.sa_agilent.instr.write("AVER:STAT ON")
        self.sa_agilent.instr.write(":INITiate")
        ## wait a bit so that measurement starts
        time.sleep(.3)
        
        t = time.time()
        max_timeout = 50 #seconds
        timeout = False

         
        # scope_results = [self.scope_rigol4.measure()]
        # thorlabs_power = [ 1000 * self.power_meter.get_power()]
         
        while not timeout:
            #This query returns the decimal value of the sum of the bits in the 
            # Status operation condition register.
            opc_value = int(self.sa_agilent.instr.query(":STATus:OPERation:CONDition?"))
            ## Bit 4 gives the measurement status
            is_still_measuring =(opc_value >> 4) & 1
            
            if not is_still_measuring:
                timeout = True
                self.log.info(f"The agilent finished in { int(time.time() - t )}s!")
            else:
                time.sleep(1.)
            if time.time() - t >max_timeout:
                timeout=True
                self.log.warning("Timeout from the rigol measurement...")

            # scope_results.append(self.scope_rigol4.measure())
            # thorlabs_power.append( 1000 * self.power_meter.get_power())
        # ## Process scope results
        # # take the mean and the std of each result
        # columns = list(scope_results[0].keys())
        # scope_results = pd.DataFrame(scope_results)
        # self.log.info(f"The number of measured power is {len(scope_results)}")
        # result = scope_results.mean().to_dict()
        # res_std = scope_results.std().to_dict()
        # for key, val in res_std.items():
        #     result[key+" std"] = val
        # result["Thorlabs power meter (mW)"] = np.mean(thorlabs_power)
        # result["Thorlabs power meter std (mW)"] = np.std(thorlabs_power)
        return result
        
        ## Other parameter measurements
        # result = self.scope_rigol4.measure(result)
        # result["Thorlabs power meter (mW)"] = 1000 * self.power_meter.get_power()
       
        try:
            pass
            ## calibration done on week 22.
            # result["Seed power (uW)"] = 0.03956*result["Seed power mean (mV)"] - 0.833
            # ## calibration done on week 22.
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

