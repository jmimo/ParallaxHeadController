Photography Parallax Head Motorization
=============

This project controls stepper motors and a camera in order to take 360 deg.
Panoramic Photographs automatically.

Arduino Dependencies
-------------

The code controls an Arduino open source hardware Motorshield and requires
the following libraries:

- https://github.com/adafruit/Adafruit-Motor-Shield-library
<pre>
git clone git://github.com/adafruit/Adafruit-Motor-Shield-library.git AFMotor
</pre>

- https://github.com/adafruit/AccelStepper
<pre>
git clone git://github.com/adafruit/AccelStepper.git AccelStepper
</pre>

- https://github.com/interactive-matter/aJson
<pre>
git clone git://github.com/interactive-matter/aJson.git aJSON
</pre>

Python / Gphoto2
-------------

In order to run gphoto2 on mac we use Homebrew
make sure you have xcode and the xcode command line tools installed in order to
successfully install ghpoto2 via brew!

<pre>
	https://github.com/mxcl/homebrew
	/usr/bin/ruby -e "$(/usr/bin/curl -fksSL https://raw.github.com/mxcl/homebrew/master/Library/Contributions/install_homebrew.rb)"
	brew install gphoto2
</pre>

<pre>
	http://pyserial.sourceforge.net/
	python setup.py install
</pre>