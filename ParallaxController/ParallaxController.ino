/**
 *
 * Parallax Head Control Software
 *
 * Copyright 2012 Michael Mimo Moratti
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#include <AFMotor.h>
#include <AccelStepper.h>

const int   KEY_ROTATE = 10;
const int   KEY_POWER  = 20;
const int   KEY_RESET  = 30;

const int   INPUT_ROTATE_CLOCKWISE        = 1;
const int   INPUT_ROTATE_COUNTERCLOCKWISE = 0;
const int   INPUT_POWER_ON                = 1;
const int   INPUT_POWER_OFF               = 0;

const int   RESET_POSITION = 0;

const int   MOTOR_STEPS         = 200;
const float MOTOR_STEP_ANGLE    = 1.8;
const int   MOTOR_PORT          = 2;
const int   MOTOR_MAX_SPEED     = 20;
const int   MOTOR_ACCELERATION  = 10;
const int   SERIAL_BAUD         = 9600;
const int   INPUT_STRING_SIZE   = 200;

boolean stringComplete = false;
String inputString = "";
boolean powerOn = false;

AF_Stepper motor(MOTOR_STEPS,MOTOR_PORT);

void forwardstep() {  
  motor.onestep(FORWARD,DOUBLE);
}
void backwardstep() {  
  motor.onestep(BACKWARD,DOUBLE);
}

AccelStepper stepper(forwardstep,backwardstep);

void setup() {
    // initialize communications
    Serial.begin(SERIAL_BAUD);
    inputString.reserve(INPUT_STRING_SIZE);
    // initialize stepper
    stepper.setMaxSpeed(MOTOR_MAX_SPEED);
    stepper.setAcceleration(MOTOR_ACCELERATION);
    stepper.disableOutputs();
}

void loop() {
  if(stringComplete) {
    int key, input, value;
    char charBuf[INPUT_STRING_SIZE];
    inputString.toCharArray(charBuf,INPUT_STRING_SIZE);
    sscanf(charBuf,"%d %d %d",&key,&input,&value);
    switch(key) {
      case KEY_ROTATE:
        if(!powerOn) {
          Serial.println("POWER IS OFF");
          break;
        }
        if(fmod(value,MOTOR_STEP_ANGLE) > 0) {
          value = value - fmod(value,MOTOR_STEP_ANGLE);
        }
        value = value / MOTOR_STEP_ANGLE;
        if(input == INPUT_ROTATE_CLOCKWISE) {
          value=abs(value);
        } else if(input == INPUT_ROTATE_COUNTERCLOCKWISE) {
          value=-abs(value);
        } else {
          Serial.println("Invalid rotation direction, valid values are [0|1]");
          break;
        }
        stepper.runToNewPosition(stepper.currentPosition() + value);
        Serial.println("ROTATION FINISHED");
        break;
      case KEY_POWER:
        if(input == INPUT_POWER_ON) {
          stepper.enableOutputs();
          stepper.runSpeed();
          powerOn = true;
          Serial.println("POWER IS ON");
        } else if(input == INPUT_POWER_OFF) {
          stepper.disableOutputs();
          motor.release();
          powerOn = false;
          Serial.println("POWER IS OFF");
        } else {
          Serial.println("Power command not understood, valid values are [0|1)");
        }
        break;
      case KEY_RESET:
        stepper.setCurrentPosition(RESET_POSITION);
        Serial.println("RESET SUCCESSFUL");
        break;
      default:
        Serial.println("Command not understood, valud values are [10,20,30]");
        break;
    }    
    key = 0;
    input = -1;
    value = 0;
    inputString = "";
    stringComplete = false;
    if(powerOn) {
      stepper.run();
    }
  }
}

void serialEvent() {
  while(Serial.available()) {
    char inChar = (char)Serial.read();
    inputString += inChar;
    if(inChar == '\n') {
      stringComplete = true;
    }
  }
}
