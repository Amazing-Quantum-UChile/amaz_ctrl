"""
Note:
Victor on May, 2026. I did not succeed in using a pyvisa protocol so I directly coded a driver using the DLL. 
"""


from amaz_ctrl.scripts.base.amaz_instrument import AmazingInstrument
import sys
import clr
import System
import System.Text
sys.path.append(r"C:\Program Files\IVI Foundation\VISA\VisaCom64\Primary Interop Assemblies")
clr.AddReference("Thorlabs.TLPMX_64.Interop")
from Thorlabs.TLPMX_64.Interop import TLPMX

class PowerMeterThorlabsPM16(AmazingInstrument):
    is_connected = False
    device_name = "PM16-405"
    def_params = {"powermeter thorlabs":False}
    
    def connect(self):
        if self.params["powermeter thorlabs"]:
            self.open()
    def disconnect(self):
        self.close() 
    def set_parameters(self):
        pass



    def open(self):
        try:
            tlpmx = TLPMX(System.IntPtr.Zero)
            ## Get all devices
            ## I need to do this line twice otherwise it fails
            status, device_count = tlpmx.findRsrc()
            status, device_count = tlpmx.findRsrc()
            for i in range(device_count):
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
                
                if model_buffer.ToString()==self.device_name:
                    ## we have found the device
                    if dev_status==0:
                        self.log.error(f"The {model_buffer.ToString()}  with VISA address {addr_buffer.ToString()} is LOCKED. The reason for this are the following one. (1) The Thorlabs Optical Power Monitor application is opened and has locked the device. (2) An other instance of the script opened the device and never closed it. Remember to always always call the close method if you open it. We recommand to call the open method in the connect_sensors method and the close method in the disconnect_sensors method. In this case, you need to shutdown the terminal, fix your script and restart. (3) Some other reason. ")
                        self.is_connected = False
                        tlpmx.Dispose()

                        return
                    else:
                        self.address = System.String(addr_buffer.ToString())
                        self.device = TLPMX(self.address, True, False)
                        self.is_connected = True
                        self.log.info(f"Connected to {model_buffer.ToString()}  with VISA address {addr_buffer.ToString()}.")
                        tlpmx.Dispose()
                        return
            tlpmx.Dispose()
            return
        except Exception as e:
            self.log.error("Failed to instanciate ")
            self.is_connected = False

    def set_wavelength(self, wavelenght:float):
        if not self.is_connected:
            self.show_not_connected_error()
            return 
        wavelength = System.Double(wavelenght) 
        channel = System.UInt16(1) 
        status = self.device.setWavelength(wavelength, channel)


    def get_wavelength(self)->float:
        """Get the current wavelngth of the device. Relies on the getWavelength function 
            print(tlpmx_testB.getWavelength.__doc__) -> Int32 getWavelength(Int16, Double ByRef, UInt16)
             
        """
        if not self.is_connected:
            self.show_not_connected_error()
            return 795e-9
        
        action_mode = System.Int16(0) #0: current wavelenght, 1: minimum wavelenght: 2: maximum wavelength
        wavelength_buffer = System.Double(0.0) # buffer for the value
        channel = System.UInt16(1)  # The channel (1 here)

        status, current_wavelength = self.device.getWavelength(action_mode, wavelength_buffer, channel)
        return current_wavelength
    
    def get_power(self) -> float:
        """Get the current power measurement of the device. Relies on the measPower function 
            print(tlpmx_testB.measPower.__doc__) -> Int32 measPower(Double ByRef, UInt16)
             
        """
        if not self.is_connected:
            self.show_not_connected_error()
            return 0.0
        
        power_buffer = System.Double(0.0) # buffer for the value
        channel = System.UInt16(1)        # The channel (1 here)

        status, current_power = self.device.measPower(power_buffer, channel)
        return current_power

    def show_not_connected_error(self):
        #we only show the error if the user wanted to connect to the device.
        if self.params["powermeter thorlabs"]:
            self.log.warning("The Thorlabs Power meter device is not connected or opened. Please call the open method and once finished close it using the close method.")

    def get_unit(self) -> str:
        """Get the current power unit of the device. Relies on the getPowerUnit function 
            print(tlpmx_testB.getPowerUnit.__doc__) -> Int32 getPowerUnit(Int16 ByRef, UInt16)
        """
        if not self.is_connected:
            self.show_not_connected_error()
            return None
        
        unit_buffer = System.Int16(0)  # buffer for the value (ByRef)
        channel = System.UInt16(1)      # The channel (1 here)

        status, current_unit = self.device.getPowerUnit(unit_buffer, channel)
        if current_unit==0:
            return "W"
        else:return "dBm"
    
    def close(self):
        if self.is_connected is False:
            return
        self.device.Dispose()
        self.log.info(f"Diconnected from {self.device_name}.")
        self.is_connected = False
        return 

    

if __name__=="__main__":
    pm = PowerMeterThorlabsPM16(params = {})
    try:
        pm.open()
        l = pm.get_wavelength()
        print(l)
        print(pm.get_unit())
        pm.close()
    except:
        pm.close()
    