from amaz_ctrl.scripts.base.amaz_instrument import AmazingInstrument
from amaz_ctrl.scripts.subscripts.thorlabs_elliptec_rotation_mount import ElliptecRotationStage
import pyvisa
rm = pyvisa.ResourceManager()
import numpy as np
import time


class Laser(AmazingInstrument):
    f_25P = 377.107385960 *10**12 + 1.7708439228 * 10 ** 9 # transición F=2 --> 5P_{1/2}
    f_22 =f_25P - 210.923*10**6 # transición F=2-->F'=2
    f_23 =f_25P + 150.659*10**6 # transición F=2-->F'=3
    f_2_23 = (f_22+f_23)/2 # Crossover
    f_12 = 3.0357324390 * 10**9 # distancia estados basales F=2-->F=3
    _def_params = {"laser 2ph detuning (MHz)": 10.0,
    "laser 1ph detuning (MHz)": 1203.0,
    "laser locking transition": "22",
    "laser Rigol DSG830 LAN": "172.17.55.99",
    "laser Rigol DSG815 LAN": "172.17.55.37",
    "laser lock pump power": True,
    "laser target pump power (mW)":350,
    "laser pump tolerance (mW)":5 ,# we allow a small deviation from the pump power target
    "laser lock pump power minimal step (deg)":0.5,
    "laser lock pump power maximal step (deg)":10,
    "laser lock pump power slope (deg/mW)":0.075, #basically total laser power / 45 degrees
    "laser lock pump power proportional PID":0.9,
    "laser lock pump power max iterations":10
    }

    def __init__(self, params, parent, log_level="INFO"):
        super().__init__(params, log_level)
        self.parent = parent #this is the script class so that we have access to the methods of the script class
        
        self.rigoldsg830 = RigolDSG830(self.params, log_level)
        self.rigoldsg815 = RigolDSG815(params, log_level)
        self.pump_rotation = ElliptecRotationStage(self.params,
                                                port = self.params["laser lock pump power USB address"])
        self.instruments = [
            self.rigoldsg830,
            self.rigoldsg815,
            self.pump_rotation
        ]
        
        # if self.lock_pump:
        #     self.connect_rotation_stage()
        #     a = self.get_pump_power()
        #     self.verify_pump_rotation_position()
   

    def connect(self):
        for instr in self.instruments:
            self.log.info("Trying to connect to: {c}".format(
                c=type(instr).__name__))
            instr.connect()
        

    def disconnect(self):
        for instr in self.instruments:
            try:
                instr.disconnect()
            except Exception as e:
                self.log.info("Deconnecting to: {c}".format(
                                c=type(instr).__name__))
                self.log.error("{t}: {e}. Failed to disconnect to the object {c}. Continuing the disconnection protocol.".format(
                t=type(e).__name__, 
                e=e,
                c=type(instr).__name__
            ))
       
    def set_parameters(self):
        for instr in self.instruments:
            instr.set_parameters()
        self.lock_pump = self.params["laser lock pump power"]
        self.lock_pump_step_min = np.abs(self.params["laser lock pump power minimal step (deg)"])
        self.lock_pump_step_max = np.abs(self.params["laser lock pump power maximal step (deg)"])
        self.update_photon_detuning_from_device_frequency()


    def update_photon_detuning_from_device_frequency(self):
        """update the parameter dictionary using the locking transition and the frequency of the AOM."""
        self.locking_frequency = 0
        transition_str = self.params["laser locking transition"].lower()
        if transition_str in "crossover":
            self.locking_frequency = self.f_2_23
        elif transition_str in "22 f=2->f'=2":
            self.locking_frequency = self.f_22
        elif transition_str in "23 f=2->f'=3":
            self.locking_frequency = self.f_23
        else:
            self.log.warning(f"The transition frequency on which you locked the laser '{transition_str}' was not recognized. Setting it to the default transition peak: the crossover F'=2/F'=3.")
            self.locking_frequency = self.f_2_23

        aom1500 = self.rigoldsg830.get_frequency()
        aom200 = self.rigoldsg815.get_frequency()
        self.params["laser 1st AOM frequency (MHz)"] = aom1500 / 1e6
        self.params["laser 2nd AOM frequency (MHz)"] = aom200 / 1e6
        delta_2ph = 2*aom1500 -self.f_12
        delta_1ph =  - 2*aom200 + self.locking_frequency  + aom1500 - self.f_25P
        self.params["laser 2ph detuning (MHz)"] = delta_2ph / 1e6
        self.params["laser 1ph detuning (MHz)"] = delta_1ph / 1e6


    #############################
    #### Pump rotation stage ####
    #############################
    def connect_rotation_stage(self):
        try:
            self.pump_rotation = ElliptecRotationStage(self.params,
                                                       port = self.params["laser lock pump power USB address"])
        except Exception as e:
            self.log.error("{t}: {e}. Failed to connect to the EllipteC Rotation Stage. Not servo looping the pump power.".format(
                t=type(e).__name__, 
                e=e,
            ))
            self.params["laser lock pump power"] = False
            self.lock_pump = self.params["laser lock pump power"]

    def verify_pump_rotation_position(self):
            if not self.lock_pump:
                return
            angle = self.pump_rotation.angle
            self.pump_rotation_history = [{"Time":time.time(), "Angle (deg)":angle}]
            if angle >90 or angle < 45:
                self.log.warning(f"The pump rotation mount was at {angle} which is outside the authorized range [45,90]. We moove it to 80 degrees.")
                delta = 80 - angle
                self.pump_rotation.move_by(delta)
                time.sleep(2.)
    def get_pump_power(self):
        try:
            # calibration done in week 32 of 2026.
            return 92.7*np.mean(self.parent.scope_rigol4.get_voltage_trace(channel = 1)) - 7
        except Exception as e:
            self.log.error("{t}: {e}. Failed to measure the pump power. Not servo looping the pump power.".format(
                t=type(e).__name__, 
                e=e,
            ))
            self.params["laser lock pump power"] = False
            self.lock_pump = self.params["laser lock pump power"]
            return 0

    
        
    def rotate_pump_lambda(self, degs = 1.):
        """
        Rotate the pump by a given number of degree. The function verifies that
        - the new angles is between 45 and 90 degrees (positive slope part of the cosinus**2),
        - the step is not too large neither too low
        """
        angle  = self.pump_rotation.angle

        ## Check that the angle is neither too large nor too small.
        if np.abs(degs)> self.lock_pump_step_max:
            self.log.debug(f"The rotation stage command angle displacement is {degs} but it cannot turn by more than {self.lock_pump_step_max}.")
            degs = self.lock_pump_step_max * np.sign(degs)
        if np.abs(degs)< self.lock_pump_step_min:
            self.log.debug(f"The rotation stage command angle displacement is {degs} but it cannot turn by less than {self.lock_pump_step_min}.")
            degs = self.lock_pump_step_min * np.sign(degs)
        ## check if the final angle belongs to the allowed range [45, 90]
        new_angle =  angle + degs 
        if new_angle> 90 or new_angle < 45 :
            ## if the step was too large, just do a smaller step. 
            if np.abs(degs) > self.lock_pump_step_min:
                self.rotate_pump_lambda(degs = degs / 1.5)
            pump_power = self.get_pump_power()
            target_power = self.params["laser target pump power (mW)"]
            msg = f"[ElliptecRotationStage]: The rotation mount Elliptec is currently at theta = {angle:.1f} and cannot move further. Indeed, its value must always remain between  45 and 90 degrees to ensure that we are in a positive slope region. We thus cannot reach the value of the power you want (P={target_power}mW) and the value will stay at {pump_power} mW. A possible explanation is that you lack power and hence you should reoptimize the fiber optimization power. An other possibility is that the HOME angle (i.e. the reference for the angle of the roation mount) does not match the maximum of the Malus law. In this case, you must set the HOME angle using the ELLO software (see the lab notebook week33 of 2026)."
            self.log.error(msg)
            self.log.info("Deactivating the pump power lock.")
            self.params["laser lock pump power"] = False
            self.lock_pump = self.params["laser lock pump power"]
            return
        ## If everything is OK, we turn the rotation stage
        self.log.debug(f"Moving by {degs:.2f} degrees to reach {new_angle:.2f} deg.")
        self.pump_rotation.move_by(degs)
        self.last_positions.append(new_angle)
        ## We need to wait a bit, like .5 seconds
        time.sleep(.5)
        ## the following code does not work because the rotation stage does not read out the angle.
        # start = time.time()
        # timeout = 4
        # posi_evolution = []
        # power_evol = [round(float( self.get_pump_power()), 1)]
        # while np.abs(new_angle -self.pump_rotation.angle) < self.lock_pump_step_min:
        #     time.sleep(.1)
        #     posi_evolution.append(self.pump_rotation.angle)
        #     power_evol.append(round(float( self.get_pump_power()), 1))
        #     if  time.time() - start > timeout:
        #         self.log.warning(f"It seems the pump rotation did not mooved in {timeout} second. That is weird. Here is the recorded position {power_evol} and {posi_evolution}.")
        #         break
        

        
    def check_pump_power(self, initialize_memory = True):
        """check if the pump power is different from the necesatry power. If initialize_memory is True, it will keep tracks from this time to the following mooves."""
        if not self.lock_pump:
            return
        if initialize_memory:
            self.last_positions = []
        print(self.pump_rotation.is_open)
        pump_power = self.get_pump_power()
        target_power = self.params["laser target pump power (mW)"]
        tol = np.abs(self.params["laser pump tolerance (mW)"])
        err = pump_power - target_power
        self.log.debug(f"The difference between the pump power and its target value is {err:.0f} mW.") 
        if -tol < err < tol:
            self.log.debug("This value is within the accepted range ({} mW).".format(self.params["laser pump tolerance (mW)"]))
            if len(self.last_positions)>0:
                self.log.info(f"The rotation stage succesfully changed the pump power after {len(self.last_positions)} steps.")
            ## deconnect the rotation
            if self.pump_rotation.is_open:
                self.pump_rotation.close()
            return
        ## We do not want to break the experiment because of this loop
        if len(self.last_positions)>self.params["laser lock pump power max iterations"]:
            self.log.warning(f"The difference between the pump power and its target value is {err:.0f} which is beyond the tolerance range. The servo loop stopped because the numer of iteration steps ({len(self.last_positions)}) is above the limit.")
            if self.pump_rotation.is_open:
                self.pump_rotation.close()
            return 
             
        ### We rotate the lambda to compensate the difference: minus sign because the slope is positive. 
        degs = - err * self.params["laser lock pump power slope (deg/mW)"] * self.params["laser lock pump power proportional PID"]
        self.rotate_pump_lambda(degs = degs)
        self.check_pump_power(initialize_memory=False)
        

def malus_law(x,  A, B, C, D):
    """
    A = Amplitude, B = Frequency (deg-1), C = Phase shift, D = Vertical offset
    """
    return A * np.cos(B * x / 180 * np.pi + C / 180 * np.pi) ** 2+ D


class RigolWFG(AmazingInstrument):
    max_freq_MHz = 200
    max_power_dBm = -5
    name="RigolDevice"
    def set_frequency(self, freq_MHz: float):
        """Set RF output frequency in GHz."""
        if freq_MHz>self.max_freq_MHz:
            self.log.error(f"The RF frequency of the {self.name} cannot exceed {self.max_freq_MHz}MHz.")
            return
        self.instr.write(f":FREQ {freq_MHz}MHz")

    def set_power(self, power_dbm: float):
        """
        Set RF output power in dBm.
        """
        if power_dbm > self.max_power_dBm:
            self.log.error(f"THe power of the {self.name} cannot exceed {self.max_power_dBm} dBm.")
            return
        self.instr.write(f":POW {power_dbm}DBM")

    def get_output_state(self):
        """Return RF output state (ON/OFF)."""
        return self.instr.query(":OUTP?")

    def get_frequency(self):
        """Query current RF frequency."""
        return float(self.instr.query(":FREQ?"))

    def get_power(self):
        """Query current RF output power."""
        return float(self.instr.query(":POW?"))


class RigolDSG815(RigolWFG):
    max_freq_MHz = 200
    max_power_dBm = -5

    def set_parameters(self):
        return
        self.log.warning("This is not yet implemented")

    def connect(self):
        """Connect to the Rigol DSG815 signal generator via LAN (SCPI socket)."""
        self.ip = self.params["laser Rigol DSG815 LAN"]
        self.instr = rm.open_resource(f"TCPIP0::{self.ip}::INSTR")
        self.instr.read_termination = '\n'
        self.instr.write_termination = '\n'
    def disconnect(self):
        self.instr.close()

class RigolDSG830(RigolWFG):
    ## set the default parameters
    max_freq_MHz = 3000
    max_power_dBm = 30

    def connect(self):
        """Connect to the Rigol DSG830 signal generator via LAN (SCPI socket)."""
        self.ip = self.params["laser Rigol DSG830 LAN"]
        self.instr = rm.open_resource(f"TCPIP0::{self.ip}::INSTR")
        self.instr.read_termination = '\n'
        self.instr.write_termination = '\n'
    def disconnect(self):
        self.instr.close()

    def set_parameters(self):
        """Configure RF generator parameters using the parameters."""
        return
        self.set_frequency(self.params["laser Rigol DSG830 freq (GHz)"])
        self.set_power(self.params["laser Rigol DSG830 power (dBm)"])
        self.instr.write(":OUTP ON")



if __name__=="__main__":
    import json, os
    # wfg = RigolDSG830()
    # wfg.set_params()
    # laser = Laser
    script_dir = os.path.dirname(os.path.abspath(__file__))
    fpath = os.path.abspath(os.path.join(script_dir, "..", "exp_params.json"))
    with open(fpath, 'r', encoding='utf-8') as file:
        exp_params = json.load(file)
    laser = Laser(params=exp_params)
    laser.update_photon_detuning_from_device_frequency()
