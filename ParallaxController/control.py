#!/usr/bin/env python3

import sys, subprocess, serial, json, threading, time

DEFAULT_BAUDRATE = 9600
DEFAULT_ENCODING = 'UTF-8'
DEFAULT_EOF = '\n'

POWER_TOGGLE_ON = "on"
POWER_TOGGLE_OFF = "off"


#----------------------------------------------------------------------
def main():
	import optparse
	
	parser = optparse.OptionParser(
		usage = "%prog [options] [device [baoudrate]]",
		description = "Controller program for the orchestration between Arduino and gphoto2")
		
	parser.add_option("-d", "--device",
		dest = "device",
		help = "device, the device (tty.*) at which the Arduino is attached")
		
	parser.add_option("-b", "--baudrate",
		dest = "baudrate",
		help = "set baud rate, default %default",
		default = DEFAULT_BAUDRATE)
		
	parser.add_option("-p", "--motorPort",
		dest = "motorPort",
		help = "set the motor port on the shield, default %default",
		default = "2")
		
	parser.add_option("-s", "--motorSteps",
		dest = "motorSteps",
		help = "set the motor's steps for a full rotation, default %default",
		default = "200")
		
	parser.add_option("-a", "--motorStepAngle",
		dest = "motorStepAngle",
		help = "set the motor's step angle in degrees for one step, default %default",
		default = "1.80")
		
	parser.add_option("-m", "--motorMaximumSpeed",
		dest = "motorMaximumSpeed",
		help = "set the motor's maximum speed, default %default",
		default = "20")
		
	parser.add_option("-c", "--motorAcceleration",
		dest = "motorAcceleration",
		help = "set the motor's acceleration, default %default",
		default = "10")
		
	(options, args) = parser.parse_args()
	
	if(options.device is None):
		parser.error("Please specify a valid device to connect too.")
	
	
	#takePicture()
	#sendCommand()
	
	arduino = Arduino(options.device,options.baudrate,4)
	arduino.connect()
	
	initialize(arduino,options.motorPort,options.motorSteps,options.motorStepAngle,options.motorMaximumSpeed,options.motorAcceleration)
	powerToggle(arduino,POWER_TOGGLE_ON)
	rotate(arduino,"clockwise","36")
	rotate(arduino,"clockwise","36")
	rotate(arduino,"clockwise","36")
	rotate(arduino,"clockwise","36")
	rotate(arduino,"clockwise","36")
	rotate(arduino,"clockwise","36")
	rotate(arduino,"clockwise","36")
	rotate(arduino,"clockwise","36")
	rotate(arduino,"clockwise","36")
	rotate(arduino,"clockwise","36")
	powerToggle(arduino,POWER_TOGGLE_OFF)
	
	arduino.disconnect()
	
#----------------------------------------------------------------------
def takePicture():
	try:
		subprocess.check_call(["gphoto2","-v"])
	except subprocess.CalledProcessError as e:
		sys.stderr.write("Error occured while attempting to take image!" % (e))
		#print ("Error occured while attempting to take image!")
		#print (type(e))
		#print (e)

def initialize(arduino, motorPort, motorSteps, motorStepAngle, motorSpeed, motorAcceleration):
	request = json.dumps({"command":"initialize","port":motorPort,"total-steps":motorSteps,"step-angle":motorStepAngle,"max-speed":motorSpeed,"acceleration":motorAcceleration})
	send(arduino,request)
	
def powerToggle(arduino, status):
	send(arduino,json.dumps({"command":"power","toggle":status}))
	
def rotate(arduino, direction, degrees):
	request = json.dumps({"command":"rotate","direction":direction,"degrees":degrees})
	send(arduino,request)
	time.sleep(2)
	
def send(arduino, command):
	#arduino = Arduino(device,baudrate,timeout)
	#arduino.connect()
	sys.stdout.write(command + '\n')
	response = arduino.sendCommand(command)
	sys.stdout.write(response + '\n')
	#arduino.disconnect()
	responseObject = json.loads(response)
	sys.stdout.write(responseObject["status"] + DEFAULT_EOF)
	# TODO throw exception in case of error	

#
# Arduino communciations class
# This class will run in it's own thread in order to send and receive data.
#
class Arduino(threading.Thread):
	def __init__(self, device, baudrate, timeout):
		threading.Thread.__init__(self)
		self.device = device
		self.baudrate = baudrate
		self.timeout = timeout
		self.port = None
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
		try:
			self.port = serial.Serial(self.device,self.baudrate,timeout=self.timeout)
		except serial.serialutil.SerialException:
			sys.stderr.write("The communication port is already in use\n")
		self.start()
		time.sleep(1)
	
	def disconnect(self):
		self.stopProcessing = True
		self.port.close()
	
	def sendCommand(self, command):
		self.hasReceivedResponse = False
		self.port.write(command.encode(DEFAULT_ENCODING) + DEFAULT_EOF.encode(DEFAULT_ENCODING))
		self.port.flush()
		while (self.hasReceivedResponse == False):
			time.sleep(0.001)
		return self.response.decode(DEFAULT_ENCODING)

#----------------------------------------------------------------------
if __name__ == "__main__":
    main()