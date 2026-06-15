

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
        # ## -- Rigol Scope 2202A (lockin scope) --
        # ##################
        # self.scope_rigol4 = ScopeRigolDS1104(params= self.exp_params)

        ##################
        ## Thorlabs Power Meter
        ##################
        self.power_meter = PowerMeterThorlabsPM16(params=self.exp_params)

    

    def connect_sensors(self):
        self.power_meter.open()
        return
    
    def disconnect_sensors(self):
        time.sleep(1.)
        self.power_meter.close()
        time.sleep(1.)
        self.power_meter.close()
        return

    def acquire(self)->dict:
        result={}
        # self.log.info("Reading squeezing...")

        t = self.sa_agilent.get_sweep_time()
        # self.log.info(f"Sweep time of the agilent: {t}s")
        # self.sa_agilent.instr.timeout = 20000 
        # self.sa_agilent.instr.write("INIT:IMM;*OPC?")
        # self.sa_agilent.instr.read()
        # self.sa_agilentinstr.write("INIT:CONT OFF")
        # self.sa_agilentinstr.write("INIT:IMM")
        time.sleep(t*2+.2)

        freq, ampli = self.sa_agilent.get_trace()
        df = pd.DataFrame({"Freq":freq, "Ampli":ampli})
        
        df.to_csv(self.run_prefix+"raw.csv")
        if self.exp_params['SA Agil freq span (MHz)'] ==0:
            noise = float(np.sqrt(np.mean(ampli**2)))
            result["Mean noise"] = noise
            fr = self.exp_params['SA Agil freq center (MHz)']
            self.log.info(f"Intensity noise @{fr}MHz: {noise}")
        else:
            for f in [0.5,1,1.5,2,2.5,3,4,5,6]:#loop over frequencies
                idx = np.argmin(np.abs(freq-f))
                result[f"Intensity noise @{f}MHz"]=ampli[idx]
            noise = result[f"Intensity noise @3MHz"]
            self.log.info(f"Intensity noise @3MHz: {noise}")
        ## Other parameter measurements
        # result = self.scope_rigol4.measure(result)
        result["Thorlabs power meter (mW)"] = 1000 * self.power_meter.get_power()
       
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

