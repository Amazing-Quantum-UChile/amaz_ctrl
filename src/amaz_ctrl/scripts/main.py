
from amaz_ctrl.scripts.base.amaz_script import AmazingScript
import time, os, logging
log = logging.getLogger("SCRIPT")
import numpy as np
import math,random
from amaz_ctrl.scripts.subscripts.spectrum_anal_agilent import SpectrumAnalyzerAgilent
from amaz_ctrl.scripts.subscripts.laser import RigolDSG815
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import pyvisa
rm = pyvisa.ResourceManager()
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
        time.sleep(1)
        log.info("I just prepared the experiment!!")

    def connect_sensors(self):
        log.info("Setting up sensors...")
        self.sa_agilent = SpectrumAnalyzerAgilent()
        self.sa_agilent.set_params(self.exp_params)
        self.wfg_rigolGHz = RigolDSG815()
        self.wfg_rigolGHz.set_params(self.exp_params)
        self.wfg_rigolGHz.connect()

        ip = "169.254.205.155"
        # self.scope = rm.open_resource(f"TCPIP0::{ip}::INSTR")
        log.info("Sensors ready")

    
    def disconnect_sensors(self):
        log.info("... Disconnected !")


    def acquire(self)->dict:
        result={}


        NO_PTS =20
        if self.j_run%NO_PTS==0:
            time.sleep(4.)
        ### We set the frequency of the analyser.
        freq = 1513 +.5*(self.j_run%NO_PTS)
        
        # freq = 1517.5
        result["freq (MHz)"] = freq
        # if self.j_run==0:
        self.wfg_rigolGHz.set_frequency(freq/1000.)
        time.sleep(1.)



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

        # result["Laser Piezo (V)"] = float(self.scope.query(":MEASure:ITEM? VAVG,CHAN1"))
        # result["Laser Error (V)"] = float(self.scope.query(":MEASure:ITEM? VAVG,CHAN2"))

        

        if random.random()<0.03:
            fig, ax = plt.subplots()
            ax.plot(freq, ampli,label = "exp",color = "C0", alpha = .7 )
            ax.plot(freq[mask],ampli[mask],label = "exp",color = "C1", alpha = .7 )
            ax.plot(freq, lorentzian(freq, *popt),
                    "--", label = r"$\Gamma=${:.0f} kHz".format(1000*popt[2]), color = "black",)
            ax.set_xlabel("Frequency (MHz)")
            ax.set_ylabel("Power (V)")
            ax.legend()
            fig.savefig(self.run_prefix+"plot.png")
            plt.close()
            
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

