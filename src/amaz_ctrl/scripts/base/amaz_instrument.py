from amaz_ctrl.tools.amaz_logs import set_console_log
import logging, json
from pathlib import Path

class AmazingInstrument():
    _params ={}
    def_params ={}
    instr = None
    _conf = {  
        }
    
    def __init__(self,params, log_level="DEBUG"):
        ## Set up logs
        LOG_NAME = "INSTR"
        self.log = logging.getLogger(LOG_NAME)
        set_console_log(logger_name = LOG_NAME, log_level=log_level)
        self.params = params
        # self.load_configuration()

        
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

    @property
    def _configuration_file(self) -> Path:
        """
        Return the path to the configuration file.

        The configuration file is located in:
            <class_file_directory>/conf/<ClassName>.json
        """
        class_file = Path(__file__).resolve()
        conf_dir = class_file.parent / "conf"

        return conf_dir / f"{self.__class__.__name__}.json"

    def load_configuration(self) -> None:
        """
        Load the configuration from the JSON file.

        The configuration directory and file are created automatically
        if they do not exist.

        Values loaded from the JSON file override the default values
        defined in self._conf.
        """
        configuration_file = self._configuration_file

        # Create the configuration directory if necessary.
        configuration_file.parent.mkdir(parents=True, exist_ok=True)

        # Create the configuration file with default values if necessary.
        if not configuration_file.exists():
            self.save_configuration()
            return

        try:
            with configuration_file.open("r", encoding="utf-8") as file:
                configuration = json.load(file)

            if not isinstance(configuration, dict):
                raise ValueError("Configuration file must contain a JSON object.")

            # Keep defaults and override them with values from the file.
            self._conf.update(configuration)
            self.save_configuration()

        except (json.JSONDecodeError, OSError, ValueError) as error:
            raise RuntimeError(
                f"Unable to load configuration from '{configuration_file}'."
            ) from error
    def save_configuration(self) -> None:
        """
        Save the current configuration to the JSON file.
        """
        configuration_file = self._configuration_file

        configuration_file.parent.mkdir(parents=True, exist_ok=True)

        with configuration_file.open("w", encoding="utf-8") as file:
            json.dump(
                self._conf,
                file,
                indent=4,
                ensure_ascii=False,
            )
    #### Methods to be defined in daughter class
    def connect(self):
        self.log.error(f"The Device {self.__class__.__name__} does not have a connect function.")

    def disconnect(self):
        self.log.error(f"The Device {self.__class__.__name__} does not have a disconnect function.")

    def set_parameters(self):
        self.log.error(f"The Device {self.__class__.__name__} does not have a set_parameters function.")
        
# %% Tests 
if __name__=="__main__":
    instrument = AmazingInstrument()
    instrument.def_params = {"var1":0, "var2":2}
    instrument.params = {"var1":1, }
    print(instrument.get_param("var1"))
    print(instrument.get_param("var2"))
    print(instrument.get_param("var3"))