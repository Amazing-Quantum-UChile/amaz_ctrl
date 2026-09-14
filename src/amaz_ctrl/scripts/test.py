
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
from amaz_ctrl.scripts.subscripts.arduino import  Arduino
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import pyvisa
from amaz_ctrl.tools.misc import get_windows_pyvisa_ressuorce_manager
rm = get_windows_pyvisa_ressuorce_manager()
import pandas as pd
from amaz_ctrl.scripts.subscripts.thorlabs_elliptec_rotation_mount import ElliptecRotationStage
from amaz_ctrl.scripts.subscripts.wfg_rigol import RigolDSG815, RigolDSG830

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
        self.rigoldsg830 = RigolDSG830(params= self.exp_params)
        self.rigoldsg815 = RigolDSG815(params= self.exp_params)
        self.scope_rigol4 = ScopeRigolDS1104(params= self.exp_params)
        self.pump_rotation = ElliptecRotationStage(self.exp_params,
                                                port = self.exp_params["laser lock pump power USB address"])
        self.arduino = Arduino(params= self.exp_params)
        self.laser = Laser(params=self.exp_params, 
                           parent=self, 
                           rigoldsg830 = self.rigoldsg830,
                           rigoldsg815 = self.rigoldsg815,
                           pump_rotation = self.pump_rotation,
                           arduino = self.arduino,
                           scope =self.scope_rigol4
                           )

    
    def prepare_experiment(self):
        # we get the list of instruments which inherit the AmazingInstrument class
        instrs = self.get_instruments()
        for instr in instrs:
            #-. We update the parameter of each instrument 
            # to match the one of the experiment
            instr.params = self.exp_params
            instr.set_parameters()


    
    def acquire(self)->dict:
        result={}
        result["Test"] = 1
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
    # script.main()

