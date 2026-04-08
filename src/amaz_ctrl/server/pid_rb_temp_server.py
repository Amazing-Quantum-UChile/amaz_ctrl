import Pyro5.api
import threading
import time
import random
import logging
import collections



@Pyro5.api.expose
class TempServer:
    def __init__(self):
        self.current_temp = 22.0
        self.target_temp = 22.0
        self.is_heating = False
        
        # Logging setup
        self._log_buffer = collections.deque(maxlen=20)
        self.logger = logging.getLogger("TempService")
        self.logger.setLevel(logging.INFO)
        
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.addHandler(logging.StreamHandler()) # See in terminal too

        # Start the "Background Physics" thread
        self.running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()


    def _update_loop(self):
        """Simulates the thermal inertia of a cryostat or oven"""
        while self.running:
            # Simple physics simulation: move towards target with noise
            diff = self.target_temp - self.current_temp
            self.current_temp += diff * 0.1 + (random.random() - 0.5) * 0.05
            time.sleep(0.5)

    # --- EXPOSED METHODS ---
    @Pyro5.api.expose
    def set_target(self, value):
        self.target_temp = float(value)
        self.logger.info(f"New setpoint: {self.target_temp}°C")
        return True
    
    @Pyro5.api.expose
    def get_data(self):
        """Returns the status for the GUI plots"""
        return {
            "current": round(self.current_temp, 3),
            "target": self.target_temp
        }
    
    @Pyro5.api.expose
    def get_logs(self):
        """Called by the GUI QTimer"""
        logs = list(self._log_buffer)
        self._log_buffer.clear()
        return logs

# Launch on Port 9091
daemon = Pyro5.api.Daemon(port=9091)
uri = daemon.register(TempServer, "lab.temp")
print(f"Temperature Server ready on Port 9091\nURI: {uri}")
daemon.requestLoop()