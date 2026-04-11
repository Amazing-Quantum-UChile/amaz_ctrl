
from amaz_ctrl.scripts.base.amaz_script import AmazingScript
import time, os, logging
log = logging.getLogger("SCRIPT")



class Script(AmazingScript):
    def __init__(self,exp_params_dir: str = None,
                 data_root_dir: str = None,
                 log_level="INFO"):
        super().__init__(exp_params_dir=exp_params_dir,
                         data_root_dir = data_root_dir,
                         log_level="INFO")

    def prepare_experiment(self):
        time.sleep(1)
        log.info("I just prepared the experiment!!")

    def connect_sensors(self):
        log.info("I am now connected to sensors...")
    
    def disconnect_sensors(self):
        log.info("... Disconnected !")


    def acquire(self)->dict:
        time.sleep(1)
        self.log.info(f"Acquired run {self.j_run}")
        result = {"Res1":1,
                  "Res2":20}
        return result
    
    def on_experiment_about_to_start(self):
        """method called before an experiment starts so that the user can do whatever they want at this stage."""
        pass

    def on_experiment_about_to_end(self):
        """method called before after an experiment finished so that the user can do whatever they want at this stage."""
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

