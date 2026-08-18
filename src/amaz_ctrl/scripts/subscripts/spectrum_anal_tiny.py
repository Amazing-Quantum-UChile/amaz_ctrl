
from amaz_ctrl.scripts.base.amaz_instrument import AmazingInstrument
import serial
import numpy as np
import pylab as pl
import struct
from serial.tools import list_ports

VID = 0x0483 #1155
PID = 0x5740 #22336
REF_LEVEL = (1<<9)


class SpectrumAnalyzerTiny(AmazingInstrument):
	def_params = {
			"SA Tiny connected": True,
			"SA Tiny freq center (MHz)": 80,
			"SA Tiny freq span (MHz)": 5,
			"SA Tiny RBW (kHz)": 10,
			"SA Tiny Average trace No": 5,
		}
	serial = None
	_frequencies = None
	points = 101

	def __init__(self, *arg,**kwargs):
        # Call the parent class __init__ method
		super().__init__( *arg,**kwargs) 

	def connect(self):
		self._is_connected = self.params["SA Tiny connected"]
		if self._is_connected:
			device_list = list_ports.comports()
			for device in device_list:
				if device.vid == VID and device.pid == PID:
					self.dev =  device.device
					return
			self.log.error("The Tiny SA was not found in serial ports. Please turn it ON. ")
			self.dev  = None
			return
		else:
			self.log.info("Not conected to the Tiny SA.")
			self.dev = None
			return 


	def set_params(self): 
		if not self._is_connected:
			return
		self.set_span(int(self.params["SA Tiny freq span (MHz)"]*1e6))
		self.set_center(int(self.params["SA Tiny freq center (MHz)"]*1e6))
		self.rbw(data = self.params["SA Tiny RBW (kHz)"])
		self.repeat(number = int(self.params["SA Tiny Average trace No"]))
		
		
	def get_trace(self):
		"""return the frequencies (in MHz) and the power (in dBm)"""
		if not self._is_connected:
			self.log.info("Tiny SA in dummy mode: generating fake data.")
			return np.linspace(
				self.params["SA Tiny freq center (MHz)"]-self.params["SA Tiny freq span (MHz)"]/2,
				self.params["SA Tiny freq center (MHz)"]+self.params["SA Tiny freq span (MHz)"]/2,
				101), np.zeros(101) - 100
		data = self.data()
		self.fetch_frequencies()
		return self.frequencies, data


	

	##########################################################################
	## Following is from http://dfu.tinydevices.org/tinySA/python/tinySA.py ##
	##########################################################################
	@property
	def frequencies(self):
		return self._frequencies

	def set_frequencies(self, start = 1e6, stop = 350e6, points = None):
		if points:
			self.points = points
		self._frequencies = np.linspace(start, stop, self.points)

	def open(self):
		if self.serial is None:
			self.serial = serial.Serial(self.dev)

	def close(self):
		if self.serial:
			self.serial.close()
		self.serial = None

	def send_command(self, cmd):
		self.open()
		self.serial.write(cmd.encode())
		self.serial.readline() # discard empty line

	def cmd(self, text):
		self.open()
		self.serial.write((text + "\r").encode())
		self.serial.readline() # discard empty line
		data = self.fetch_data()
		return data

	def set_sweep(self, start, stop):
		if start is not None:
			self.send_command("sweep start %d\r" % start)
		if stop is not None:
			self.send_command("sweep stop %d\r" % stop)

	def set_span(self, span):
		if span is not None:
			self.send_command("sweep span %d\r" % span)

	def set_center(self, center):
		if center is not None:
			self.send_command("sweep center %d\r" % center)

	def set_level(self, level):
		if level is not None:
			self.send_command("level %d\r" % level)

	
	def set_output(self, on):
		if on is not None:
			if on:
				self.send_command("output on\r")
			else:
				self.send_command("output off\r")

	def set_low_output(self):
		self.send_command("mode low output\r")

	def set_low_input(self):           
		self.send_command("mode low input\r")
	
	def set_high_input(self):           
		self.send_command("mode high input\r")
	
	def set_frequency(self, freq):
		if freq is not None:
			self.send_command("freq %d\r" % freq)

	def measure(self, freq):
		if freq is not None:
			self.send_command("hop %d 2\r" % freq)
			data = self.fetch_data()
			for line in data.split('\n'):
				if line:
					return float(line)

	def temperature(self):
		self.send_command("k\r")
		data = self.fetch_data()
		for line in data.split('\n'):
			if line:
				return float(line)

	def repeat(self, number:int=1):
		"""sets the number of measurements that should be taken at every frequency
		usage: repeat 1..1000
		increasing the repeat reduces the noise per frequency, repeat 1 is the normal scanning mode. """
		if  not isinstance(number, int):
			self.log.error("Failed to set the number of repetition for the Tiny SA. Please set an integer number of repetitions.")
			return

		if number >1000:
			self.log.error(f"The number of repetitions for the Tiny SA must be lower than 1000 (currently:{number}).")
			return
		self.send_command("repeat %d\r" % number)


	def rbw(self, data=0):
		"""sets the rbw to either automatic or a specific value
		usage: rbw auto|3..600
		the number specifies the target rbw in kHz 
		"""
		if data == 0:
			self.send_command("rbw auto\r")
			return
		if data<1:
			self.send_command("rbw %f\r" % data)
			return
		if data >= 1:
			self.send_command("rbw %d\r" % data)
		
	def fetch_data(self):
		result = ''
		line = ''
		while True:
			c = self.serial.read().decode('utf-8')
			if c == chr(13):
				next # ignore CR
			line += c
			if c == chr(10):
				result += line
				line = ''
				next
			if line.endswith('ch>'):
				# stop on prompt
				break
		return result

#	def fetch_array(self, sel):
#		self.send_command("data %d\r" % sel)
#		data = self.fetch_data()
#		x = []
#		for line in data.split('\n'):
#			if line:
#				x.extend([float(d) for d in line.strip().split(' ')])
#		return np.array(x[0::2]) + np.array(x[1::2]) * 1j

#	def fetch_gamma(self, freq = None):
#		if freq:
#			self.set_frequency(freq)
#		self.send_command("gamma\r")
#		data = self.serial.readline()
#		d = data.strip().split(' ')
#		return (int(d[0])+int(d[1])*1.j)/REF_LEVEL

	def resume(self):
		self.send_command("resume\r")
	
	def pause(self):
		self.send_command("pause\r")
	
	def marker_value(self, nr = 1):
		self.send_command("marker %d\r" % nr)
		data = self.fetch_data()
		line = data.split('\n')[0]
#		print(line)
		if line:
			dl = line.strip().split(' ')
			if len(dl) >= 4:
				d = line.strip().split(' ')[3]
				return float(d)
		return 0

	def data(self, array = 2):
		"""dumps the trace data
		usage: data 0..2
		0=temp value, 1=stored trace, 2=measurement 
		"""
		self.send_command("data %d\r" % array)
		data = self.fetch_data()
		x = []
		for line in data.split('\n'):
			if line:
				d = line.strip().split(' ')
				x.append(float(line))
		return np.array(x)

	def fetch_frequencies(self):
		"""dumps the frequencies used by the last sweep"""
		self.send_command("frequencies\r")
		data = self.fetch_data()
		x = []
		for line in data.split('\n'):
			if line:
				x.append(float(line))
		self._frequencies = np.array(x)

	def send_scan(self, start = 1e6, stop = 900e6, points = None):
		if points:
			self.send_command("scan %d %d %d\r"%(start, stop, points))
		else:
			self.send_command("scan %d %d\r"%(start, stop))

	def scan(self):
		segment_length = 101
		array0 = []
		array1 = []
		if self._frequencies is None:
			self.fetch_frequencies()
		freqs = self._frequencies
		while len(freqs) > 0:
			seg_start = freqs[0]
			seg_stop = freqs[segment_length-1] if len(freqs) >= segment_length else freqs[-1]
			length = segment_length if len(freqs) >= segment_length else len(freqs)
			#print((seg_start, seg_stop, length))
			self.send_scan(seg_start, seg_stop, length)
			array0.extend(self.data(0))
			array1.extend(self.data(1))
			freqs = freqs[segment_length:]
		self.resume()
		return (array0, array1)
	
	def capture(self):
		from PIL import Image
		self.send_command("capture\r")
		b = self.serial.read(320 * 240 * 2)
		x = struct.unpack(">76800H", b)
		# convert pixel format from 565(RGB) to 8888(RGBA)
		arr = np.array(x, dtype=np.uint32)
		arr = 0xFF000000 + ((arr & 0xF800) >> 8) + ((arr & 0x07E0) << 5) + ((arr & 0x001F) << 19)
		return Image.frombuffer('RGBA', (320, 240), arr, 'raw', 'RGBA', 0, 1)

	def logmag(self, x):
		pl.grid(True)
		pl.xlim(self.frequencies[0], self.frequencies[-1])
		pl.plot(self.frequencies, x)
		
	def writeCSV(self,x,name):
		f = open(name, "w")
		for i in range(len(x)):
			print("%d, "%self.frequencies[i], "%2.2f"%x[i], file=f)



if __name__=="__main__":
	sa_tiny = SpectrumAnalyzerTiny(params = {})
	# sa_tiny.set_span(5000000)
	# sa_tiny.set_center(80000000)
	sa_tiny.set_params()
	## Get the trace
	freq, data = sa_tiny.get_trace()
	power = 10**(data/10)/1000
	import matplotlib.pyplot as plt
	fig, ax = plt.subplots()
	ax2 = ax.twinx()
	ax.plot(freq/1e6, data, color = "black")
	ax.set_xlabel("Frequencies (MHz)")
	ax.set_ylabel("Power (dBm)")
	ax2.plot(freq/1e6, power, color = "grey")
	plt.show()

