#!/usr/bin/env python


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

import sys, subprocess, serial, json, threading, time, argparse, ctypes, os

DEFAULT_BAUDRATE = 9600
DEFAULT_ENCODING = 'UTF-8'
DEFAULT_LF = '\n'

JSON_ATTRIBUTE_STATUS = "status";
JSON_ATTRIBUTE_ERROR = "error";

STATUS_ERROR_VALUE = "Error";

POWER_TOGGLE_ON = "on"
POWER_TOGGLE_OFF = "off"

PTR = ctypes.pointer

GP_OK = 0
GP_CAPTURE_IMAGE = 0
GP_FILE_TYPE_NORMAL = 1

gp = ctypes.CDLL('/usr/lib/libgphoto2.so.2')

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

	gpcontext = initializeGphotoContext()
	camera = initializeCamera(gpcontext)

	localtime = time.localtime()
	timestmp = time.strftime("%Y-%m-%d-%H:%M:%S", localtime)

	try:
		initialize(arduino,results.shieldport,results.steps,results.stepangle,results.maxspeed,results.acceleration)
		powerToggle(arduino,POWER_TOGGLE_ON)
		steps = divmod(360,int(results.degrees))[0]
		counter = 0
		while(counter < steps):
			shoot(gpcontext,results.location,results.aperture,results.shutterspeed,camera,timestmp,counter)
			rotate(arduino,results.direction,results.degrees)
			counter = counter + 1
		powerToggle(arduino,POWER_TOGGLE_OFF)
	except ArduinoCommandExecutionException as e:
		print("Error occured: %s \n" % (e))
	
	arduino.disconnect()
	disconnectCamera(gpcontext,camera)
	
	
#----------------------------------------------------------------------

def check(result):
    if result < 0:
        gp.gp_result_as_string.restype = ctypes.c_char_p
        message = gp.gp_result_as_string(result)
        raise libgphoto2error(result, message)
    return result

def initializeGphotoContext():
	context = gp.gp-context_new()
	return context

def initializeCamera(gpcontext):
	camera = ctypes.c_void_p()
	gp.gp_camera_new(ctypes.pointer(camera))
	gp.gp_camera_init(camera,gpcontext)
	return camera

def disconnectCamera(gpcontext,camera):
	gp.gp_camera_exit(camera, context)  
	gp.gp_camera_unref(camera)

def setConfig(camera, gpcontext, name, value):
	main = Widget()
	check(gp.gp_camera_get_config(camera,PTR(main._w),gpcontext))
	tokens = name.split('/')
	parent = main
	child = None
	for token in tokens:
		child = Widget()
		ret = gp.gp_widget_get_child_by_name(parent._w,str(name),PTR(child._w))
		if(ret != 0):
			check(gp.gp_widget_get_child_by_label(parent._w,str(name),PTR(child._w)))
		parent = child
	child.set_value(value)
	check(gp.gp_camera_set_config(camera,main._w,gpcontext))

def shoot(gpcontext, location, aperture, shutterspeed, camera,  timestmp, counter):
	microcounter = 1
	for speed in shutterspeed:
		captureImage(gpcontext,location,aperture,speed,camera,timestmp,counter,microcounter)
		microcounter = microcounter + 1
	
def captureImage(gpcontext, location, aperture, shutterspeed, camera, timestmp, counter, microcounter):
	setConfig(camera,gpcontext,'capturesettings/aperture',aperture)
	setConfig(camera,gpcontext,'capturesettings/shutterspeed',shutterspeed)
	cam_path = CameraFilePath()  
	gp.gp_camera_capture(camera,GP_CAPTURE_IMAGE,ctypes.pointer(cam_path),gpcontext)
	cam_file = ctypes.c_void_p()  
	fd = os.open("{0}/{1}-IMG-{2:03d}-{3:03d}.CR2".format(location,timestmp,counter,microcounter), os.O_CREAT | os.O_WRONLY)  
	gp.gp_file_new_from_fd(ctypes.pointer(cam_file), fd)  
	gp.gp_camera_file_get(camera,  
		              cam_path.folder,  
		              cam_path.name,  
		              GP_FILE_TYPE_NORMAL,  
		              cam_file,  
		              gpcontext)  
	gp.gp_camera_file_delete(camera,  
		                 cam_path.folder,  
		                 cam_path.name,  
		                 gpcontext)  
	gp.gp_file_unref(cam_file)

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

#
# gphoto2 classes and structs
#
class CameraFilePath(ctypes.Structure):
	_fields_=[('name', (ctypes.c_char * 128)),('folder', (ctypes.c_char * 1024))]

class Widget(object):
    	def __init__(self):
		self._w = ctypes.c_void_p()

    	def set_value(self,value):
		check(gp.gp_widget_set_value(self._w,str(value)))

class libgphoto2error(Exception):
   	def __init__(self, result, message):
        	self.result = result
        	self.message = message
    	def __str__(self):
        	return self.message + ' (' + str(self.result) + ')'

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
	
	image.add_argument("--location",required=True,
		help = "the location where to store all downladed files")

	image.add_argument("--aperture",required=True,
		help = "the aperture to be used for all exposures")
	
	image.add_argument("--shutterspeed",required=True,
		action = "append",
		help = "List of shutterspeeds to execute in the given order")
	
	# ---- motor arguments ----
	
	motor = parser.add_argument_group("motor arguments")
	
	motor.add_argument("--shieldport",required=False,
		default="1",
		help = "The output port on the Arduino Motor Shield.")
	
	motor.add_argument("--steps",required=False,
		default="200",
		help = "The total amount of steps for one full 360 deg. rotation")	
		
	motor.add_argument("--stepangle",required=False,
		default="0.1125",
		help = "The degrees for one Step.")	
		
	motor.add_argument("--maxspeed",required=False,
		default="300",
		help = "Maximum speed for the motor")
		
	motor.add_argument("--acceleration",required=False,
		default="20",
		help = "Rotation acceleration")
	
	return parser.parse_args()

#----------------------------------------------------------------------
if __name__ == "__main__":
    main()
