from amaz_ctrl.tools.amaz_logs import set_console_log
import logging
class AmazingInstrument():
    _params ={}
    def_params ={}
    instr = None
    
    def __init__(self,params, log_level="INFO"):
        ## Set up logs
        LOG_NAME = "INSTR"
        self.log = logging.getLogger(LOG_NAME)
        set_console_log(logger_name = LOG_NAME, log_level=log_level)
        self.params = params
        self.connect()

    def connect(self):
        self.log.error(f"The Device {self.__class__.__name__} does not have a connect function.")

        
    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, params:dict):
        self._params = params
        for key, elem in self.def_params.items():
            if key not in self._params:
                self.log.warning(
                f"The key parameter {key} of {self.__class__.__name__} "
                f"is missing. Using default value {elem}."
                )
                self._params[key] = elem

    def get_param(self, key):
        if key in self.params:
            return self.params[key]
        if key in self.def_params:
            val = self.def_params[key]
            self.log.warning(f"The parameter key '{key}' is not in your parameters dictionary. Taking the default value {val}.")
            self.params[key] =val
            return val
        else:
            self.log.error(f"Instrument {self.__class__.__name__} does not find the parameter {key} in its parameter dictionary, including the default one. Please fix me.")
            return None


    def write(self, cmd:str):
        """Write command to instrument"""
        if self.instr is None:
            self.log.warning(f"No connexion to {self.__class__.__name__}. Trying to connect.")
            self.connect()
        self.instr.write(cmd)

    def query(self, cmd:str):
        """Query to instrument"""
        if self.instr is None:
            self.log.warning(f"No connexion to {self.__class__.__name__}. Trying to connect.")
            self.connect()
        return self.instr.query(cmd)

# %% Tests 
if __name__=="__main__":
    instrument = AmazingInstrument()
    instrument.def_params = {"var1":0, "var2":2}
    instrument.params = {"var1":1, }
    print(instrument.get_param("var1"))
    print(instrument.get_param("var2"))
    print(instrument.get_param("var3"))