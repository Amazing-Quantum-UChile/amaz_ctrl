
from amaz_ctrl.scripts.base.amaz_script import AmazingScript
import time, os, logging, sys, serial
import numpy as np
from amaz_ctrl.tools.misc import get_windows_pyvisa_ressuorce_manager
from thorlabs_elliptec import ELLx

rm = get_windows_pyvisa_ressuorce_manager()


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
        ## List USB Visa device
        self.list_USB_devices()
        self.list_serial_ports()
        self.list_thorlabs_devices(show_thorlabs_methods = False)
        return
    
    def list_USB_devices(self):
        self.log.info("### --- Listing USB devices. --- ###")
        devices = rm.list_resources()
        if not devices:
            self.log.warning("No USB VISA devices found.")
            return
        

        for i, dev in enumerate(devices, 1):
            try:
                instrument = rm.open_resource(dev)
                instrument.timeout = 2000 
                dev_name = instrument.query('*IDN?')
                msg = f"""Identification : {dev_name.strip()} with
                VISA location: {dev}
                """
                self.log.info(msg)
                instrument.close()
            except Exception as e:
                self.log.info(f"No IDN answer from {dev}. Error is: {e}")


    def list_serial_ports(self):
        """We only list the serials ports using pyserial"""
        ports = serial.tools.list_ports.comports()
        self.log.info("### --- Listing Serial Port devices. --- ###")
        for port in ports:
            self.log.info(f"Port {port.description} with hardware ID: {port.hwid}, vendor ID (VID): {port.vid}, product ID (PID): {port.pid} and serial number: {port.serial_number}")


    def list_thorlabs_devices(self, show_thorlabs_methods = False):
        self.log.info("### --- Listing Thorlabs devices. --- ###")
        self.list_thorlabs_power_detector(show_thorlabs_methods = show_thorlabs_methods)
        self.list_thorlabs_rotating_mounts()

    def list_thorlabs_rotating_mounts(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            try:
                stage = ELLx(serial_port = port.device)
                msg = f"Motorized mount {stage.model_number} (with unit {stage.units}) is available on USB port {port.device}."
                self.log.info(msg)
                stage.close()
            except Exception as e:
                pass


    def list_thorlabs_power_detector(self,  show_thorlabs_methods = False):
        try:
            import clr
        except Exception as e:
            self.log.error(f"Error loading the clr package: {e}.Please chack that you did install pythonnet in your virtual environment: 'pip install pythonnet'.")
            return
        try:
            import System.Text
            import System
        except Exception as e:
            self.log.error(f"Error when importing Windows/CLR components: {e}")
            return
        try:
            sys.path.append(r"C:\Program Files\IVI Foundation\VISA\VisaCom64\Primary Interop Assemblies")
            clr.AddReference("Thorlabs.TLPMX_64.Interop")
            from Thorlabs.TLPMX_64.Interop import TLPMX
            if show_thorlabs_methods:
                all_fns = dir(TLPMX)
                msg = ", ".join(all_fns)
                self.log.info("Thorlabs available functions for devices: "+ msg)
        except Exception as e:
            self.log.error(f"Error loading DLL: {e}. Please verify the file 'Thorlabs.TLPMX_64.Interop.dll' exists in the path above.")
            return
        try:
            tlpmx = TLPMX(System.IntPtr.Zero)
            status, device_count = tlpmx.findRsrc()
            
        except Exception as e:
            self.log.error(f"Failed to detect Thorlabs devices: {e}.")
            return 
        if device_count == 0 :
            self.log.info("No Thorlabs device was recognized. Make sure that the Thorlabs Optical Power Monitor is closed.")
            return
        self.log.info(f"Number of Thorlab device identified: {device_count}")
        for i in range(device_count):
            try:
                
                # 0. Buffer to stock texts from the DLL
                addr_buffer = System.Text.StringBuilder(256)
                model_buffer = System.Text.StringBuilder(256)
                serial_buffer = System.Text.StringBuilder(256) #serial number
                manuf_buffer = System.Text.StringBuilder(256)
                
                # 1. Get USB address
                tlpmx.getRsrcName(i, addr_buffer)
                
                # 2. Get Id informations
                # dev_status return 1 if the device is free, 0 if not
                status, dev_status = tlpmx.getRsrcInfo(
                    i, model_buffer, serial_buffer, manuf_buffer
                )
                status ='AVAILABLE' if dev_status == 1 else 'LOCKED'

                # 3. show info
                self.log.info(f"{manuf_buffer.ToString()} device {model_buffer.ToString()} is {status} with VISA address {addr_buffer.ToString()}")
            except Exception as e:
                self.log.error(f"Error when looking at Thorlabs device number {i}. Error is {e}.")

   





    def connect_sensors(self):
        pass

    
    def disconnect_sensors(self):
        pass


    def acquire(self)->dict:
        self.stop_acquisition()
        return {}

    
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

