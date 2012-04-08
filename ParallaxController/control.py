#!/usr/local/bin/python

#import serial
from subprocess import check_call

def main():
	takePicture()


def takePicture():
	try:
		check_call(["gphoto2","-v"])
	except subprocess.CalledProcessError as e:
		print "Error occured while attempting to take image!"
		print type(e)
		print e
