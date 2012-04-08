#!/usr/bin/env python3

import sys, subprocess, serial, json, threading, time

DEFAULT_BAUDRATE = 9600
DEFAULT_ENCODING = 'UTF-8'
DEFAULT_EOF = '\n'


#----------------------------------------------------------------------
def main():
	import optparse
	
	parser = optparse.OptionParser(
		usage = "%prog [options] [port [baoudrate]]",
		description = "Controller program for the orchestration between Arduino and gphoto2")
		
	parser.add_option("-d", "--device",
		dest = "device",
		help = "device, the device (tty.*) at which the Arduino is attached")
		
	parser.add_option("-b", "--baudrate",
		dest = "baudrate",
		help = "set baud rate, default %default",
		default = DEFAULT_BAUDRATE)
		
	(options, args) = parser.parse_args()
	
	
	
	#takePicture()
	sendCommand()

#----------------------------------------------------------------------
def takePicture():
	try:
		subprocess.check_call(["gphoto2","-v"])
	except subprocess.CalledProcessError as e:
		sys.stderr.write("Error occured while attempting to take image!" % (e))
		#print ("Error occured while attempting to take image!")
		#print (type(e))
		#print (e)
	
def sendCommand():
	arduino = Arduino('/dev/tty.usbmodemfd3311',9600,1)
	arduino.connect()
	
	request = json.dumps({"command":"initialize","port":"2","total-steps":"200","step-angle":"1.80","max-speed":"20","acceleration":"10"})

	response = arduino.sendCommand(request)
	
	responseObject = json.loads(response)
	sys.stdout.write(responseObject["status"] + DEFAULT_EOF)
	
	arduino.disconnect()

#
# Arduino communciations class
# This class will run in it's own thread in order to send and receive data.
#
class Arduino(threading.Thread):
	def __init__(self, device, baudrate, timeout):
		threading.Thread.__init__(self)
		self.port = serial.Serial(device,baudrate,timeout=timeout)
		self.hasReceivedResponse = False
		self.stopProcessing = False
		self.response = bytearray();
	
	def run(self):
		while (self.stopProcessing != True):
			if(self.hasReceivedResponse == False):
				self.response = self.port.readline()
				if(len(self.response) > 0):
					self.hasReceivedResponse = True
	
	def connect(self):
		self.port.open()
		self.start()
		time.sleep(1)
	
	def disconnect(self):
		self.stopProcessing = True
		self.port.close()
	
	def sendCommand(self, command):
		self.hasReceivedResponse = False
		self.port.write(command.encode(DEFAULT_ENCODING) + DEFAULT_EOF.encode(DEFAULT_ENCODING))
		#self.port.flush()
		while (self.hasReceivedResponse == False):
			time.sleep(0.001)
		return self.response.decode(DEFAULT_ENCODING)

#----------------------------------------------------------------------
if __name__ == "__main__":
    main()