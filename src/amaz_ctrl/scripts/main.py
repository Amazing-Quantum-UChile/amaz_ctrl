
from amaz_ctrl.scripts.base.amaz_script import AmazingScript
import time, os, logging
log = logging.getLogger("SCRIPT")
import numpy as np
import math,random
from amaz_ctrl.scripts.subscripts.spectrum_anal_agilent import SpectrumAnalyzerAgilent
from amaz_ctrl.scripts.subscripts.laser import RigolDSG815
from scipy.optimize import curve_fit


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
    def __init__(self,exp_params_dir: str = None,
                 data_root_dir: str = None,
                 log_level="INFO"):
        super().__init__(exp_params_dir=exp_params_dir,
                         data_root_dir = data_root_dir,
                         log_level=log_level)

    def prepare_experiment(self):
        time.sleep(1)
        log.info("I just prepared the experiment!!")

    def connect_sensors(self):
        self.sa_agilent = SpectrumAnalyzerAgilent()
        self.sa_agilent.set_params()
        self.wfg_rigolGHz = RigolDSG815()
        self.wfg_rigolGHz.set_params()

        log.info("Setting up sensors...")
    
    def disconnect_sensors(self):
        log.info("... Disconnected !")


    def acquire(self)->dict:
        result={}
        ### We set the frequency of the analyser.
        freq = 1515.5 + +.25*(self.j_run%25)
        result["freq (MHz)"] = freq
        self.wfg_rigolGHz.set_frequency(freq/1000.)
        time.sleep(.4)



        freq, ampli = self.sa_agilent.get_trace()
        p0=[80, np.max(ampli), .5, 0 ]
        popt, pcov = curve_fit(lorentzian,
                               freq,
                               ampli, p0=p0,
                        bounds=([78, 0, .001, 0],[83, 200,5,10])
                        )
        perr = np.sqrt(np.diag(pcov))
        result["Amplitude"] = popt[1]
        result["Gamma (kHz)"] = popt[2] *1000
        result["U(Amplitude)"] = perr[1]
        result["U(Gamma) (kHz)"] = perr[2] *1000
        error = np.sum((lorentzian(freq, *popt)-ampli)**2)
        result["Fit error"] =error
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


if __name__ == "__main__":
    script = Script()
    # scanned_params_dict = script.load_scanned_parameters()
    # list_of_experiments = script.build_list_of_experiments(scanned_params_dict)
    script.main()

