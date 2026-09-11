from amaz_ctrl.scripts.base.amaz_instrument import AmazingInstrument
import serial, time
# # Initialize serial connection (match the baud rate of 9600)
# arduino = serial.Serial(port='COM3', baudrate=9600, timeout=1)
# time.sleep(2) # Wait 2 seconds for Arduino to reset/initialize

# print("Sending '1' to turn on LED...")
# arduino.write(b'1') # The 'b' prefix converts the string to bytes
# time.sleep(2)

# print("Sending '0' to turn off LED...")
# arduino.write(b'0')

# # Always close the connection when finished
# arduino.close()

class FakeArduinoBoard():
    def write(self, cmd):
        pass
    def readline(self):
        answer = "0\n".encode('utf-8')
        return answer
    def close(self):
        pass
    
class Arduino(AmazingInstrument):
    def_params = {"arduino address":"COM3",
                  "arduino baudrate":9600,
                  "arduino timeout (s)": 1}
    _is_connected = False
    board = FakeArduinoBoard()
    def connect(self):
        """connects to the arduino using the serial port.
        """
        self.board = serial.Serial(port=self.params["arduino address"],
                                     baudrate=self.params["arduino baudrate"], 
                                     timeout=self.params["arduino timeout (s)"])
        time.sleep(2.) 
        self.reset_buffer()
        idn = self.query("*IDN?")
        if idn:
            self.log.info(f"Connection to '{idn}' succeeded.")
            self._is_connected = True
        else:
            self.log.error("Connection to the arduino failed.")
            self._is_connected = False

        debug_mode = self.query("DEBUG?")
        if debug_mode:
            self.log.warning("The arduino code is in debug mode. Please update it in normal mode. See week 37 of 2026 code.")

    def reset_buffer(self):
        """reet the buffer i.e. all the lines sent by the arduino."""
        self.board.reset_input_buffer()

    def send(self, cmd:str):
        """Send a command to the arduino board making sure it ends with an endline.

        Args:
            cmd (str): the command to sent to the arduino
        """
        end_line = "\n"
        ## check that the command as "\n" at the end
        if len(cmd) < 2:
            cmd+=end_line
        if cmd[-2:]!=end_line:
            cmd+=end_line
        self.board.write(cmd.encode('utf-8'))

    def read(self):
        answer = self.board.readline().decode('utf-8').strip()
        return answer

    def query(self, cmd:str)-> str:
        """Query the arduino.

        Args:
            cmd (str): the command to sent to the arduino

        Returns:
            str: the decoded output from the arduino.
        """
        self.send(cmd)
        answer = self.read()
        return answer
    
    def disconnect(self):
        self.log.info("Disconnecting from the Arduino.")
        self.board.close()

    def measure_ads_voltage(self, channel:int = 0):
        """Measure the voltage on the ADS 1115 connected to the arduino."""
        if channel not in [0,1,2,3]:
            self.log.error(f"[Arduino] The channel {channel} of the ADS 1115 does not exist. Please choose among [0,1,2,3].")
            return 0
        voltage = self.query(f"ADS {channel}")
        try:
            voltage =  float(voltage)
            return voltage
        except ValueError:
            self.log.warning("First try of ADS measure failed. Trying a second time.")
            self.reset_buffer()
            time.sleep(.2)
        voltage = self.query(f"ADS {channel}")
        return float(voltage)

    def lock_laser(self):
        self.send("LOCK LASER")

    def unlock_laser(self):
            self.send("UNLOCK LASER")

    def rotate_laser_frequency(self, steps:int):
        """rotate the step motor associated to the laser frequency via the laser diode controller head (piezo of the diode).

        Args:
            steps (int): the signed number of steps to move by. 
        """
        is_finished = self.query(f"MOTOR-LASER-LOCK {steps}")
        if is_finished:
            return 
        else:
            self.log.warning(f"[Arduino] When rotating the laser frequency knob by {steps} steps, the arduino did not returned it was finished. Perhaps something went wrong.")
        return 

    def rotate_seed_waveplate(self, steps:int):
        """rotate the waveplate of the seed laser to change the power of the beam.

        Args:
            steps (int): the signed number of steps to move by.
        """
        
        is_finished = self.query(f"MOTOR-POW-SEED {steps}")
        if is_finished:
            return 
        else:
            self.log.warning(f"[Arduino] When rotating the seed waveplate by {steps} steps, the arduino did not returned it was finished. Perhaps something went wrong.")

    def set_parameters(self):
        pass


    
if __name__ == "__main__":
    import serial.tools.list_ports
    # Récupère la liste des ports actifs
    ports = serial.tools.list_ports.comports()

    if not ports:
        print("No dispotivo was found.")
    else:
        print("The following serial ports are connected:")
        for port in ports:
            print(f"{port.device}:{port.description}")

    arduino = Arduino(params = {"arduino address":"COM6",
                  "arduino baudrate":9600,
                  "arduino timeout (s)": 1})
    arduino.connect()
    v = arduino.measure_ads_voltage(1)
    print(f"The measured voltage is {v} V.")
    arduino.rotate_seed_waveplate(30)

    arduino.disconnect()