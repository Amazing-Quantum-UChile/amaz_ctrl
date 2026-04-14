
from amaz_ctrl.scripts.base.amaz_script import AmazingScript
import time, os, logging
log = logging.getLogger("SCRIPT")
import numpy as np
import math,random

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
        log.info("I am now connected to sensors...")
    
    def disconnect_sensors(self):
        log.info("... Disconnected !")


    def acquire(self)->dict:
        time.sleep(.1)
        freq = self._exp_params["laser 2ph detuning (MHz)"]
        if self.j_run == 10:
            print(self.run_prefix)
        result = {"Res1": math.sin(freq * self.j_run/60 ) + .2*(random.random()-.5),
                  "Res2":np.sinc((self.j_run-50) *0.1)*(1+.1*random.random()) + .2*(random.random()-.5),
                  "Res3":1- np.exp(-(self.j_run)*(0.003*self.seq_number) + + .2*(random.random()-.5)) 
                  }
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



if __name__ == "__main__":
    script = Script()
    # scanned_params_dict = script.load_scanned_parameters()
    # list_of_experiments = script.build_list_of_experiments(scanned_params_dict)
    script.main()

