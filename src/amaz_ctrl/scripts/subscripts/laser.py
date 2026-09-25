from amaz_ctrl.scripts.base.amaz_instrument import AmazingInstrument
from amaz_ctrl.scripts.base.amaz_script import AmazingScript
import scipy
import matplotlib.pyplot as plt
from pathlib import Path
import pyvisa
rm = pyvisa.ResourceManager()
import numpy as np
import time, os
from datetime import datetime
## This is the file in which we save the plots of the laser
tmp_dir = Path(r"C:\Users\Carla Quantum Lab\Desktop\tmp")
PREFIX = "locking"

class Laser(AmazingInstrument):
    f_25P = 377.107385960 *10**12 + 1.7708439228 * 10 ** 9 # transición F=2 --> 5P_{1/2}
    f_22 =f_25P - 210.923*10**6 # transición F=2-->F'=2
    f_23 =f_25P + 150.659*10**6 # transición F=2-->F'=3
    f_2_23 = (f_22+f_23)/2 # Crossover
    transition_frequency = {"0":f_23,
                         "1":f_2_23,
                         "2":f_22
                         }
    f_12 = 3.0357324390 * 10**9 # distancia estados basales F=2-->F=3
    _def_params = {
        "laser lock frequency numerically":True,
        "laser 2ph detuning (MHz)": 10.0,
        "laser 1ph detuning (MHz)": 1203.0,
        "laser locking transition": "1",
        "laser Rigol DSG830 LAN": "172.17.55.99",
        "laser Rigol DSG815 LAN": "172.17.55.37",
        "laser lock pump power": True,
        "laser target pump power (mW)":350,
        "laser pump tolerance (mW)":5 ,# we allow a small deviation from the pump power target
        "laser lock pump power minimal step (deg)":0.5,
        "laser lock pump power maximal step (deg)":10,
        "laser lock pump power slope (mW/deg)":13.3, #basically total laser power / 45 degrees
        "laser lock pump power proportional PID":0.9,
        "laser lock pump power max iterations":10,
        ### SEED POWER
        "laser lock seed power": True,
        "laser target seed power (uW)":50,
        "laser seed tolerance (uW)":2 ,# we allow a small deviation from the seed power target
        "laser lock seed power minimal step (deg)":0.3,
        "laser lock seed power maximal step (deg)":10,
        "laser lock seed power slope (uW/deg)":4.2, #basically  max laser power / 45 degrees
        "laser lock seed power proportional PID":0.9,
        "laser lock seed power max iterations":10
        }
    seed_last_steps=[]
    _conf={
        "laser lock pump power minimal step (deg)":0.5,
        "laser lock pump power maximal step (deg)":10,
        "laser lock pump power slope (mW/deg)":13.3,
        "laser lock pump power last calibration":0,
        "Angle values (deg)":[],
        "Pump power":[]
    }

    def __init__(self, 
                 params:dict, 
                 rigoldsg830: AmazingInstrument,
                 rigoldsg815:AmazingInstrument,
                 pump_rotation:AmazingInstrument,
                 arduino:AmazingInstrument,
                 scope:AmazingInstrument,
                 log_level="DEBUG"):
        super().__init__(params, log_level)
        self.rigoldsg815 = rigoldsg815
        self.rigoldsg830 = rigoldsg830
        self.pump_rotation = pump_rotation
        self.arduino = arduino
        self.scope = scope
        
   

    def connect(self):
        pass

    def disconnect(self):
        pass
       
    def set_parameters(self):
        self.lock_pump = self.params["laser lock pump power"]
        self.lock_pump_step_min = np.abs(self.params["laser lock pump power minimal step (deg)"])
        self.lock_pump_step_max = np.abs(self.params["laser lock pump power maximal step (deg)"])

        self.lock_seed = self.params["laser lock seed power"]
        self.lock_seed_step_min = np.abs(self.params["laser lock seed power minimal step (deg)"])
        self.lock_seed_step_max = np.abs(self.params["laser lock seed power maximal step (deg)"])

        self.set_locking_transition()
        if self.params["laser lock frequency numerically"]:
            self.set_laser_frequency()
        else:
            self.update_photon_detuning_from_device_frequency()

    def set_locking_transition(self):
        self.locking_frequency = 0
        self.locking_transition_str = self.params["laser locking transition"].lower()
        if self.locking_transition_str not in self.transition_frequency:
            self.log.warning(f"The transition frequency on which you locked the laser '{self.locking_transition_str}' was not recognized. Setting it to the default transition peak: the crossover F'=2/F'=3 (peak 1).")
            self.params["laser locking transition"]="1"
            self.locking_transition_str = self.params["laser locking transition"]
    
        self.locking_transition_no = int(self.locking_transition_str)
        self.locking_frequency = self.transition_frequency[self.locking_transition_str]

    def update_photon_detuning_from_device_frequency(self):
        """update the parameter dictionary using the locking transition and the frequency of the AOM."""
        aom1500 = self.rigoldsg830.get_frequency()
        aom200 = self.rigoldsg815.get_frequency()
        self.params["laser 1st AOM frequency (MHz)"] = aom1500 / 1e6
        self.params["laser 2nd AOM frequency (MHz)"] = aom200 / 1e6
        delta_2ph = 2*aom1500 -self.f_12
        delta_1ph =  - 2*aom200 + self.locking_frequency  + aom1500 - self.f_25P
        self.params["laser 2ph detuning (MHz)"] = delta_2ph / 1e6
        self.params["laser 1ph detuning (MHz)"] = delta_1ph / 1e6

    def set_laser_frequency(self):
        self.arduino.unlock_laser()
        time.sleep(.3)
        ### Set frequency of the WFG
        delta_2ph = self.params["laser 2ph detuning (MHz)"] * 1e6
        delta_1ph = self.params["laser 1ph detuning (MHz)"] * 1e6
        aom1500 = (delta_2ph + self.f_12)/2
        aom200 = (+self.locking_frequency - delta_1ph -self.f_25P + aom1500  )/2   
        self.log.info(f"LASER-LOCK: Setting the AOM frequencies to {aom200/1e6:.0f} MHz and {aom1500/1e6:.0f} MHz.")
        aom1500 = int(aom1500)
        aom200 = int(aom200)
        self.params["laser 1st AOM frequency (MHz)"] = aom1500 / 1e6
        self.params["laser 2nd AOM frequency (MHz)"] = aom200 / 1e6
        # aom200 = 80000000
        self.rigoldsg830.set_frequency(freq_Hz = aom1500)
        self.rigoldsg815.set_frequency(freq_Hz = aom200)
        self.update_photon_detuning_from_device_frequency()
        self.set_piezo_frequency()
        self.arduino.lock_laser()
        time.sleep(.3)

        
    def measure_frequency_detuning(self, max_retry = 3, ax = None):
        """Query to the scope the absorption spectrum and finds out the detuning of the laser. 

        Args:
            max_retry (int, optional): the number of time we retry when failing to measure the detuning. Defaults to 3.
            ax (_type_, optional): plt.axis, the ax object on which to draw the figure if needed. Defaults to None.

        Returns:
            _type_: the detuning in MHz
        """
        try_number = 0
        while try_number<max_retry:        
            try_number+=1
            try:
                t, v = self.scope.get_trace(channel=2)
                detuning = get_frequency_detuning(np.array(t), np.array(v), 
                                                    locking_peak = self.locking_transition_no,
                                                    ax = ax)
                return detuning
            except Exception as e:
                self.log.info(f"LASER-LOCK: A problem occured when measuring the absorption spectrum. Try number {try_number}/{max_retry}.")
                self.arduino.unlock_laser()
                time.sleep(.2)
        t, v = self.scope.get_trace(channel=2)
        detuning = get_frequency_detuning(np.array(t), np.array(v), 
                                            locking_peak = self.locking_transition_no, ax = ax)
        return detuning
        

    def set_piezo_frequency(self):
        maxi_detuning = 10 # MHz. If the detuning is less than 10 MHz, we lock the laser
        is_unlocked = False
        ## We get the trace from channel two.
        detuning = self.measure_frequency_detuning(max_retry=3)

        
        motor_moove = 0
        detuning_list = [int(detuning)]

        ## clean up the tmp directory
        tmp_dir.mkdir(parents=True, exist_ok=True)
        for file in os.listdir(tmp_dir):
            os.remove(tmp_dir / file)
        while np.abs(detuning)>maxi_detuning:#we should be close to the transition by 10 MHz
            ## Based on week 37 of 2026, the number of steps per degree depends on the direction
            self.log.info(f"LASER-LOCK:We are away from the transition by {detuning:.0f} MHz.")
            ## If we are on the right,. we must do positive steps
            if detuning > 0:
                steps = int(detuning/0.61*0.95) #  0.61 MHz/paso, proportional 
            else:
                steps = int(detuning/0.55 * 0.95)
            
            self.rotate_locking_freq_motor(steps)
            time.sleep(.5)
            
            fig, ax = plt.subplots()
            detuning = self.measure_frequency_detuning(max_retry=3, ax = ax)
            detuning_list.append(int(detuning))
            plt.tight_layout()
            
            
            filename = tmp_dir / f"{PREFIX}{motor_moove}.png"
            plt.savefig(filename)
            plt.close()
            

            
            motor_moove+=1
            if motor_moove>20:
                
                self.log.error(f"LASER-FREQ:The laser failed to lock in less than 10 movements. The detuning list is [{detuning_list}].")
                break
        self.log.info(f"LASER-FREQ:The laser succesfully locked after {motor_moove} moves. The measured detunings during the locking process is {detuning_list}.")
        


    def rotate_locking_freq_motor(self, steps):
        """
        Rotate the locking motor of a given number of detuning.
        """
        minimal_step = 2 #minimum two steps.
        maximal_step = 500
        steps = int(steps)
        ## Check that the angle is neither too large nor too small.
        if np.abs(steps)> maximal_step:
            self.log.debug(f"LASER-FREQ:The command for the number of steps of the laser frequency is {steps} but it cannot turn by more than {maximal_step}.")
            steps = maximal_step * np.sign(steps)
        elif np.abs(steps)<minimal_step:
            self.log.debug(f"LASER-FREQ:The command for the number of steps of the laser frequency is {steps} but it cannot turn by less than {minimal_step}.")
            steps = minimal_step * np.sign(steps)
        self.log.info(f"LASER-FREQ:Rotating the motor by {steps} steps ({steps/2048*360:.0f} degs).")
        self.arduino.rotate_laser_frequency(steps)
        

        


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
                self.log.warning(f"PUMP-POW:The pump rotation mount was at {angle} which is outside the authorized range [45,90]. We moove it to 80 degrees.")
                delta = 80 - angle
                self.pump_rotation.move_by(delta)
                time.sleep(2.)

    def get_pump_power(self):
        try:
            # calibration done in week 32 of 2026.
            return 92.7*np.mean(self.scope.get_voltage_trace(channel = 1)) - 7
        except Exception as e:
            self.log.error("PUMP-POW:{t}: {e}. Failed to measure the pump power. Not servo looping the pump power.".format(
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
            self.log.debug(f"PUMP-POW:The rotation stage command angle displacement is {degs} but it cannot turn by more than {self.lock_pump_step_max}.")
            degs = self.lock_pump_step_max * np.sign(degs)
        if np.abs(degs)< self.lock_pump_step_min:
            self.log.debug(f"PUMP-POW:The rotation stage command angle displacement is {degs} but it cannot turn by less than {self.lock_pump_step_min}.")
            degs = self.lock_pump_step_min * np.sign(degs)
        ## check if the final angle belongs to the allowed range [45, 90]
        new_angle =  angle + degs 
        if new_angle> 90 or new_angle < 45 :
            ## if the step was too large, just do a smaller step. 
            if np.abs(degs) > self.lock_pump_step_min:
                self.rotate_pump_lambda(degs = degs / 1.5)
                return
            pump_power = self.get_pump_power()
            target_power = self.params["laser target pump power (mW)"]
            msg = f"[ElliptecRotationStage]: The rotation mount Elliptec is currently at theta = {angle:.1f} and cannot move further. Indeed, its value must always remain between  45 and 90 degrees to ensure that we are in a positive slope region. We thus cannot reach the value of the power you want (P={target_power}mW) and the value will stay at {pump_power} mW. A possible explanation is that you lack power and hence you should reoptimize the fiber optimization power. An other possibility is that the HOME angle (i.e. the reference for the angle of the roation mount) does not match the maximum of the Malus law. In this case, you must set the HOME angle using the ELLO software (see the lab notebook week33 of 2026)."
            self.log.error(msg)
            self.log.info("Deactivating the pump power lock.")
            self.params["laser lock pump power"] = False
            self.lock_pump = self.params["laser lock pump power"]
            return
        ## If everything is OK, we turn the rotation stage
        self.log.debug(f"PUMP-POW:Moving by {degs:.2f} degrees to reach {new_angle:.2f} deg.")
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
        
    def calibrate_pump_power(self):

        self.load_configuration()

        self.log.info(f"Last configuration was {round((time.time() - self._conf['laser lock pump power last calibration'])/(60*60*24))} days ago. Calibrating the Pump power. Please wait, this can take a while.")
        ## Set the pump rotation to home
        self.pump_rotation.home()
        time.sleep(1.5)
        power_list = []
        angle_list = []
        deg_step = 3
        for deg in range(0, 130, deg_step):
            
            try:
                angle_list.append(round(self.pump_rotation.angle, 2)%360)
                power_list.append(self.get_pump_power())
                self.log.debug(f"Angle: {angle_list[-1]}. Power: {power_list[-1]}")
                self.pump_rotation.move_by(deg_step)
            except Exception as e:
                self.log.warning(e)
            time.sleep(1.)
            
        self._conf["laser lock pump power last calibration"] = time.time()
        self._conf[ "Angle values (deg)"] = angle_list
        self._conf["Pump power"] = power_list
        self.save_configuration()

    def check_pump_power(self, initialize_memory = True):
        """check if the pump power is different from the necesatry power. If initialize_memory is True, it will keep tracks from this time to the following mooves."""
        if not self.lock_pump:
            return
        if initialize_memory:
            self.last_positions = []
        pump_power = self.get_pump_power()
        target_power = self.params["laser target pump power (mW)"]
        tol = np.abs(self.params["laser pump tolerance (mW)"])
        err = pump_power - target_power
        self.log.debug(f"PUMP-POW:The difference between the pump power and its target value is {err:.0f} mW.") 
        if -tol < err < tol:
            self.log.debug("PUMP-POW:This value is within the accepted range ({} mW).".format(self.params["laser pump tolerance (mW)"]))
            if len(self.last_positions)>0:
                pos = self.last_positions[-1]
                self.log.info(f"PUMP-POW:The rotation stage succesfully changed the pump power after {len(self.last_positions)} steps (now at {pos:.1f} deg).")
            return
        if len(self.last_positions)==0:
            self.log.info(f"PUMP-POW:The pump power error is too large by {err:.0f} mW. Starting to turn the waveplate.")
        ## We do not want to break the experiment because of this loop
        if len(self.last_positions)>self.params["laser lock pump power max iterations"]:
            self.log.warning(f"PUMP-POW:The difference between the pump power and its target value is {err:.0f} which is beyond the tolerance range. The servo loop stopped because the numer of iteration steps ({len(self.last_positions)}) is above the limit.")
            return 
             
        ### We rotate the lambda to compensate the difference: minus sign because the slope is positive. 
        degs = - err / self.params["laser lock pump power slope (mW/deg)"] * self.params["laser lock pump power proportional PID"]
        self.rotate_pump_lambda(degs = degs)
        self.check_pump_power(initialize_memory=False)
        

    #############################
    #### Seed rotation stage ####
    #############################
    def get_seed_power(self):
        """returns the seed power in uW"""
        self.arduino.reset_buffer()
        voltage = self.arduino.measure_ads_voltage(0)
        return voltage * 113
    
    def check_seed_power(self, initialize_memory = True):
        """check if the seed power is different from the necesatry power. If initialize_memory is True, it will keep tracks from this time to the following mooves."""
        if not self.lock_seed:
            return
        if initialize_memory:
            self.seed_last_steps = []
        seed_power = self.get_seed_power()
        target_power = self.params["laser target seed power (uW)"]
        tol = np.abs(self.params["laser seed tolerance (uW)"])
        err = seed_power - target_power
        self.log.debug(f"SEED-POW:The difference between the seed power and its target value is {err:.0f} uW.") 
        if -tol < err < tol:
            self.log.debug("SEED-POW:This value is within the accepted range ({} uW).".format(self.params["laser seed tolerance (uW)"]))
            if len(self.seed_last_steps)>0:
                pos = self.seed_last_steps[-1]
                self.log.info(f"SEED-POW:The rotation stage succesfully changed the seed power after {len(self.seed_last_steps)} steps (now at {pos:.1f} deg).")
            return
        if len(self.seed_last_steps)==0:
            self.log.info(f"SEED-POW:The seed power error is too large by {err:.0f} uW. Starting to turn the waveplate.")
        ## We do not want to break the experiment because of this loop
        if len(self.seed_last_steps)>self.params["laser lock seed power max iterations"]:
            self.log.warning(f"SEED-POW:The difference between the seed power and its target value is {err:.0f} which is beyond the tolerance range. The servo loop stopped because the numer of iteration steps ({len(self.seed_last_steps)}) is above the limit. The steps movements are {self.seed_last_steps}.")
            return 
                
        ### We rotate the lambda to compensate the difference: minus sign because we lock on a positive slope. 
        degs = - err / self.params["laser lock seed power slope (uW/deg)"] * self.params["laser lock seed power proportional PID"]
        self.rotate_seed_lambda(degs = degs)
        self.check_seed_power(initialize_memory=False)

    def rotate_seed_lambda(self, degs = 1.):
            """
            Just rotate the lambda.
            """
            ## Check that the angle is neither too large nor too small.
            if np.abs(degs)> self.lock_seed_step_max:
                self.log.debug(f"SEED-POW:The rotation stage command angle displacement is {degs} but it cannot turn by more than {self.lock_seed_step_max}.")
                degs = self.lock_seed_step_max * np.sign(degs)
            if np.abs(degs)< self.lock_seed_step_min:
                self.log.debug(f"SEED-POW:The rotation stage command angle displacement is {degs} but it cannot turn by less than {self.lock_seed_step_min}.")
                degs = self.lock_seed_step_min * np.sign(degs)
            ### Based on week 37 of 2026, the number of steps per degree depends on the direction
            if degs > 0 :
                steps = int(22.75*degs)
            else:
                steps = int(23.68*degs)
            self.arduino.rotate_seed_waveplate(steps)
            self.seed_last_steps.append(steps)
            
            
def malus_law(x,  A, B, C, D):
    """
    A = Amplitude, B = Frequency (deg-1), C = Phase shift, D = Vertical offset
    """
    return A * np.cos(B * x / 180 * np.pi + C / 180 * np.pi) ** 2+ D



def get_frequency_detuning(x, y, locking_peak = 2, ax = None):
    """takes the signal of the locking photodiode when the piezo is in ramp mode. The signal should show the three peaks structure. Returns the detuning of the transition 0 (2->3 transition), 1 (crossover) or 2 (2->2 transition). 
    Code written on week37 of 2026.
    """
    x, y = np.array(x), np.array(y)
    

    y_smoothed = scipy.signal.savgol_filter(
         y,  window_length=51, polyorder=6)
    deriv = - ( y_smoothed[1:]-y_smoothed[:-1])

    peaks_pos, _ = scipy.signal.find_peaks(
        deriv,
       width = 6,
    )
    ## We find the 3 maximums of the derivative to get the crossing points
    sorted_peaks = [peaks_pos[j] for j in np.flip(np.argsort(deriv[peaks_pos]))]
    sorted_peaks = sorted_peaks[0:3]

    ## Now we order them by increasing order because sometime the second is larger than the first
    sorted_peaks =  np.sort(sorted_peaks)
    ## Now we can get the x axis in terms of frequency 
    # first check is to look at the distance 0-1 and 0-2
    dist01 = x[sorted_peaks[1]] - x[sorted_peaks[0]]
    dist02 =  x[sorted_peaks[2]] - x[sorted_peaks[0]]
    error = np.abs(dist01/dist02 - 0.5)
    

    ## Now dist02 =  361.582 MHz
    try:
        idx = sorted_peaks[locking_peak]
        detuning = x[idx]
        detuningMHz = detuning * 361.582 / dist02
        xMHz = x * 361.582 / dist02
        ## Now we look for the 0 crossing point by scanning neigbhours
        idx_zero_cross = idx
        y_value = y_smoothed[idx_zero_cross]
        if y_value >0:
            ## if positive, we go right i.e. we look for the 0 by mooving to the right
            increment = 1
        elif y_value<=0:
            increment = -1
        bandwidth = 20 # MHz
        while np.abs(xMHz[idx_zero_cross] - detuningMHz) < 20 and y_value *y_smoothed[idx_zero_cross]>0:
            idx_zero_cross += increment
        zero_crossing = x[idx_zero_cross]
        zero_crossing_MHz =(xMHz[idx_zero_cross-increment]  + xMHz[idx_zero_cross])/2
    except:
        error = 1
    if error > 0.05:
        ## we do the plot and save it
        fig, ax = plt.subplots()
        axin = ax.inset_axes([.6,.7,.4,.3])
        ax.plot(x, y, "C0")
        axin.plot(x[1:], deriv)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ax.set_title("Problem locking the laser {}".format(now))
        try:
            [ax.annotate(str(i), (x[p+1], y_smoothed[p]), xytext=(5, 5),va="top", fontsize=8, textcoords="offset points") for i, p in enumerate(sorted_peaks)]
            axin.scatter(x[sorted_peaks], deriv[sorted_peaks], 
                                color = "black")
            [axin.annotate(str(i), (x[p], deriv[p]), xytext=(5, 5),va="top", fontsize=7, textcoords="offset points") for i, p in enumerate(sorted_peaks)]
        except:
            pass
        tmp_dir.mkdir(parents=True, exist_ok=True)
        filename = tmp_dir / "PROBLEM-{}.png".format(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        plt.savefig(filename)
        plt.close()
        raise Exception(f"LASER-FREQ:The relative distance between the three peaks is {dist01/dist02 } while it should be 1/2 (the crossover is at the middle). Please look at the graph in {filename} to see what was wrong.")
    if ax:
        x = xMHz
        ax.plot(x, y, "C0")
        ax.plot(x, y_smoothed, "C1")
        ax.scatter(x[sorted_peaks], y_smoothed[sorted_peaks], 
                    color = "black")
        [ax.annotate(str(i), (x[p+1], y_smoothed[p]), xytext=(5, 5),va="top", fontsize=8, textcoords="offset points") for i, p in enumerate(sorted_peaks)]
        axin = ax.inset_axes([.6,.7,.4,.3])
        axin.plot(x[1:], deriv)
        axin.scatter(x[sorted_peaks], deriv[sorted_peaks], 
                            color = "black")
        [axin.annotate(str(i), (x[p], deriv[p]), xytext=(5, 5),va="top", fontsize=7, textcoords="offset points") for i, p in enumerate(sorted_peaks)]
        dx = x[1] - x[0]
        axin.set_xticks([])
        axin.set_yticks([])
     #    ax.set_yticks([])
     #    ax.set_xticks([])
        ax.axhline(y = 0, color = "gray")
        ax.scatter([x[idx_zero_cross],x[idx_zero_cross-increment]], 
                   [y_smoothed[idx_zero_cross], y_smoothed[idx_zero_cross-increment]],
                     marker = "x",
                            color = "black")
        ax.text(zero_crossing_MHz, 0, f"{int(zero_crossing_MHz)} MHz",
                        ha="right", va="top", fontsize=9, )
    
    return zero_crossing_MHz

if __name__=="__main__":
    import json, os
    # wfg = RigolDSG830()
    # wfg.set_params()
    # laser = Laser
    script_dir = os.path.dirname(os.path.abspath(__file__))
    fpath = os.path.abspath(os.path.join(script_dir, "..", "exp_params.json"))
    with open(fpath, 'r', encoding='utf-8') as file:
        exp_params = json.load(file)
    from amaz_ctrl.scripts.subscripts.laser import Laser
    from amaz_ctrl.scripts.subscripts.scope_rigolDS1104 import ScopeRigolDS1104
    from amaz_ctrl.scripts.subscripts.powermeter_thorlabs import PowerMeterThorlabsPM16
    from amaz_ctrl.scripts.subscripts.arduino import  Arduino
    from amaz_ctrl.scripts.subscripts.thorlabs_elliptec_rotation_mount import ElliptecRotationStage
    from amaz_ctrl.scripts.subscripts.wfg_rigol import RigolDSG815, RigolDSG830
    ### Check the pump 
    scope_rigol4 = ScopeRigolDS1104(params= exp_params)
    pump_rotation = ElliptecRotationStage(exp_params,
                                            port = exp_params["laser lock pump power USB address"])
    pump_rotation.connect()
    scope_rigol4.connect()
    laser = Laser(params=exp_params,
                rigoldsg830 =None,
                rigoldsg815=None,
                pump_rotation=pump_rotation,
                arduino=None,
                scope=scope_rigol4,)
    
    laser.load_configuration()
    laser.calibrate_pump_power()
    # laser.update_photon_detuning_from_device_frequency()
