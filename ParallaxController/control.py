#!/usr/bin/env python3


'''
 Parallax Head Control Software

 Copyright 2012 Michael Mimo Moratti

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
'''

import sys, subprocess, serial, json, threading, time, argparse

DEFAULT_BAUDRATE = 9600
DEFAULT_ENCODING = 'UTF-8'
DEFAULT_LF = '\n'

JSON_ATTRIBUTE_STATUS = "status";
JSON_ATTRIBUTE_ERROR = "error";

STATUS_ERROR_VALUE = "Error";

POWER_TOGGLE_ON = "on"
POWER_TOGGLE_OFF = "off"


#----------------------------------------------------------------------
def main():
	results = setupArgumentParser()
	
	if((results.direction != "clockwise") & (results.direction != "counterclockwise")):
		print("The rotation direction can either by [clockwise] or [counterclockwise]")
		return
	
	if(divmod(360,int(results.degrees))[1] > 0):
		print("The choosen amount of degrees are not valid, Please choose any number which wraps around 360!")
		return
	
	arduino = Arduino(results.device,results.baudrate,4)
	arduino.connect()
	
	try:
		initialize(arduino,results.shieldport,results.steps,results.stepangle,results.maxspeed,results.acceleration)
		powerToggle(arduino,POWER_TOGGLE_ON)
		steps = divmod(360,int(results.degrees))[0]
		counter = 0
		while(counter < steps):
			shoot(results.aperture,results.shutterspeed)
			rotate(arduino,results.direction,results.degrees)
			counter = counter + 1
		powerToggle(arduino,POWER_TOGGLE_OFF)
	except ArduinoCommandExecutionException as e:
		print("Error occured: %s \n" % (e))
	
	arduino.disconnect()
	
#----------------------------------------------------------------------

def shoot(aperture, shutterspeed):
	for speed in shutterspeed:
		captureImage(aperture,speed)
	
def captureImage(aperture, shutterspeed):
	try:
		start = time.strftime('%s')
		subprocess.check_call(["gphoto2","--set-config","capturetarget=1","--set-config","/main/capturesettings/aperture=" + aperture,"--set-config","/main/capturesettings/shutterspeed=" + shutterspeed,"--capture-image"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		end = time.strftime('%s')
		total = int(end) - int(start)
		sys.stdout.write("image captured with aperture: %s and shutterspeed: %s time used: %s sec. \n" % (aperture,shutterspeed,total))
	except subprocess.CalledProcessError as e:
		print("Error occured while attempting to take image: %s \n" % (e))

def initialize(arduino, motorPort, motorSteps, motorStepAngle, motorSpeed, motorAcceleration):
	request = json.dumps({"command":"initialize","port":motorPort,"total-steps":motorSteps,"step-angle":motorStepAngle,"max-speed":motorSpeed,"acceleration":motorAcceleration})
	send(arduino,request)
	
def powerToggle(arduino, status):
	send(arduino,json.dumps({"command":"power","toggle":status}))
	
def rotate(arduino, direction, degrees):
	request = json.dumps({"command":"rotate","direction":direction,"degrees":degrees})
	send(arduino,request)
	
def send(arduino, command):
	response = arduino.send(command)
	responseObject = json.loads(response)
	if(responseObject[JSON_ATTRIBUTE_STATUS] == STATUS_ERROR_VALUE):
		raise ArduinoCommandExecutionException(responseObject[JSON_ATTRIBUTE_ERROR])
	else:
		sys.stdout.write(responseObject[JSON_ATTRIBUTE_STATUS] + DEFAULT_LF)

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
			print("The communication port is already in use\n")
		self.start()
		time.sleep(1)
	
	def disconnect(self):
		self.stopProcessing = True
		self.port.close()
	
	def send(self, command):
		self.hasReceivedResponse = False
		self.port.write(command.encode(DEFAULT_ENCODING) + DEFAULT_LF.encode(DEFAULT_ENCODING))
		self.port.flush()
		while (self.hasReceivedResponse == False):
			time.sleep(0.001)
		return self.response.decode(DEFAULT_ENCODING)


#
# Arduino communications Exception
#
class ArduinoCommandExecutionException(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

#----------------------------------------------------------------------
def setupArgumentParser():
	parser = argparse.ArgumentParser(description="Arduino Parallax Motor Controller Script")
	
	# ---- communication arguments ----
	
	communication = parser.add_argument_group("communication arguments")
	
	communication.add_argument("--device",required=True,
		help="USB device where the Arduino is listening, normally found at /dev/tty.usbmodem*")
		
	communication.add_argument("--baudrate",required=False,
		default="9600",
		help="RX/TX Baudrate")
		
	# ---- rotation arguments ----
	
	rotation = parser.add_argument_group("rotation arguments")
	
	rotation.add_argument("--direction",required=True,
		help = "Rotation direction, clockwise or counterclockwise")
	
	rotation.add_argument("--degrees",required=True,
		help = "Degrees per rotation step")
	
	# ---- image arguments ----
	
	image = parser.add_argument_group("image arguments")
	
	image.add_argument("--aperture",required=True,
		help = "the aperture to be used for all exposures")
	
	image.add_argument("--shutterspeed",required=True,
		action = "append",
		help = "List of shutterspeeds to execute in the given order")
	
	# ---- motor arguments ----
	
	motor = parser.add_argument_group("motor arguments")
	
	motor.add_argument("--shieldport",required=False,
		default="2",
		help = "The output port on the Arduino Motor Shield.")
	
	motor.add_argument("--steps",required=False,
		default="200",
		help = "The total amount of steps for one full 360 deg. rotation")	
		
	motor.add_argument("--stepangle",required=False,
		default="1.80",
		help = "The degrees for one Step.")	
		
	motor.add_argument("--maxspeed",required=False,
		default="20",
		help = "Maximum speed for the motor")
		
	motor.add_argument("--acceleration",required=False,
		default="10",
		help = "Rotation acceleration")
	
	return parser.parse_args()

#----------------------------------------------------------------------
if __name__ == "__main__":
    main()