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
#include<stdlib.h>
#include <AFMotor.h>
#include <AccelStepper.h>
#include <aJSON.h>

const int SERIAL_BAUD = 9600;

const int COMMAND_INITIALIZE = 10;
const int COMMAND_ROTATE = 20;
const int COMMAND_POWER = 30;
const int COMMAND_RESET = 40;
const int COMMAND_ERROR = 999;

const char* JSON_PARAMETER_COMMAND = "command";

const String COMMAND_NAME_INITIALIZE = "initialize";
const String COMMAND_NAME_ROTATE = "rotate";
const String COMMAND_NAME_POWER = "power";
const String COMMAND_NAME_RESET = "reset";

const char* JSON_PARAMETER_DIRECTION = "direction";

const String DIRECTION_CLOCKWISE = "clockwise";
const String DIRECTION_COUNTERCLOCKWISE = "counterclockwise";

const char* JSON_PARAMETER_DEGREES = "degrees";
const char* JSON_PARAMETER_STEPS = "steps";

const char* JSON_PARAMETER_TOGGLE = "toggle";

const String TOGGLE_ON = "on";
const String TOGGLE_OFF = "off";

const char* JSON_PARAMETER_POSITION = "position";
const char* JSON_PARAMETER_STATUS = "status";

const char* STATUS_INITIALIZATION_FINISHED = "Motor initialization finished";
const char* STATUS_ROTATION_FINISHED = "Rotation finished";
const char* STATUS_POWER_ON = "Power is on";
const char* STATUS_POWER_OFF = "Power is off";
const char* STATUS_RESET = "Position is reset to current position";
const char* STATUS_ERROR = "Error";

const char* JSON_PARAMETER_ERROR = "error";
const char* JSON_PARAMETER_ERROR_VALUE = "error-value";

const char* ERROR_MOTOR_IS_NOT_INITIALIZED = "The motor has not been initialized yet, please do so now!";
const char* ERROR_MOTOR_PORT_WRONG = "Please specify a valid motor port value";
const char* ERROR_MOTOR_TOTAL_STEPS_WRONG = "Please specify the total steps for the motor";
const char* ERROR_MOTOR_STEP_ANGLE_WRONG = "Please specify a valid step angle for the motor";
const char* ERROR_MOTOR_MAX_SPEED_WRONG = "Please specify a maximum speed value for the motor";
const char* ERROR_MOTOR_ACCELERATION_WRONG = "Please specify a acceleration value for the motor";
const char* ERROR_ROTATION_DIRECTION_NOT_UNDERSTOOD = "The rotation direction was not understood";
const char* ERROR_ROTATION_DEGREE_VALUE_TOO_SMALL = "The rotation degree value has to be greater 0";
const char* ERROR_ROTATION_POWER_IS_OFF = "Unable to rotate motor due to the power beeing of, please switch the power on first!";
const char* ERROR_POWER_TOGGLE_VALUE_NOT_UNDERSTOOD = "The power toggle value was not understood";
const char* ERROR_REQUEST_NOT_UNDERSTOOD = "The request could not be parsed";

const char* JSON_PARAMETER_MOTOR_PORT = "port";
const char* JSON_PARAMETER_MOTOR_TOTAL_STEPS = "total-steps";
const char* JSON_PARAMETER_MOTOR_STEP_ANGLE = "step-angle";
const char* JSON_PARAMETER_MOTOR_MAX_SPEED = "max-speed";
const char* JSON_PARAMETER_MOTOR_ACCELERATION = "acceleration";

const int   RESET_POSITION = 0;

boolean isInputComplete = false;
String inputData = "";
boolean isPowerOn = false;

AF_Stepper motor(NULL,NULL);
AccelStepper stepper;
float motorStepAngle;
boolean isMotorInitialized = false;

void setup() {
  Serial.begin(SERIAL_BAUD);
}

void loop() {
  if(isInputComplete) {
    char data[inputData.length()];
    inputData.toCharArray(data,inputData.length());
    aJsonObject* request = aJson.parse(data);
    aJsonObject* response = aJson.createObject();
    executeCommand(request,response);
    Serial.println(aJson.print(response));
    aJson.deleteItem(request);
    aJson.deleteItem(response);
    inputData = "";
    isInputComplete = false;
    if(isMotorInitialized & isPowerOn) {
      stepper.run();
    }  
  }
}

void serialEvent() {
  while(Serial.available()) {
    char inChar = (char)Serial.read();
    inputData += inChar;
    if(inChar == '\n') {
      isInputComplete = true;
    }
  }
}

void executeCommand(aJsonObject* request, aJsonObject* response) {
  int command = validateInput(request,response);
  switch(command) {
    case COMMAND_INITIALIZE:
      initialize(request,response);
    break;
    case COMMAND_ROTATE:
      rotate(request,response);
    break;
    case COMMAND_POWER:
      power(request,response);
    break;
    case COMMAND_RESET:
      reset(request,response);
    break;
    case COMMAND_ERROR:
      addJsonParameter(response,JSON_PARAMETER_STATUS,STATUS_ERROR);
    break;
    default:
      addJsonParameter(response,JSON_PARAMETER_STATUS,STATUS_ERROR);
    break;
  }
}

void initialize(aJsonObject* request, aJsonObject* response) {
  motor = AF_Stepper(atoi(getJsonParameter(request,JSON_PARAMETER_MOTOR_TOTAL_STEPS)),atoi(getJsonParameter(request,JSON_PARAMETER_MOTOR_PORT)));
  stepper = AccelStepper(forwardstep,backwardstep);
  stepper.setMaxSpeed(atoi(getJsonParameter(request,JSON_PARAMETER_MOTOR_MAX_SPEED)));
  stepper.setAcceleration(atoi(getJsonParameter(request,JSON_PARAMETER_MOTOR_ACCELERATION)));
  motorStepAngle = atof(getJsonParameter(request,JSON_PARAMETER_MOTOR_STEP_ANGLE));
  isMotorInitialized = true;
  addJsonParameter(response,JSON_PARAMETER_STATUS,STATUS_INITIALIZATION_FINISHED);
}

void forwardstep() {  
  motor.onestep(FORWARD,DOUBLE);
}
void backwardstep() {  
  motor.onestep(BACKWARD,DOUBLE);
}

void rotate(aJsonObject* request, aJsonObject* response) {
  if(!isPowerOn) {
    addJsonParameter(response,JSON_PARAMETER_ERROR,ERROR_ROTATION_POWER_IS_OFF);
    addJsonParameter(response,JSON_PARAMETER_STATUS,STATUS_ERROR);
    return;
  }
  float stepAngle = atof(getJsonParameter(request,JSON_PARAMETER_DEGREES));
  String directionIndication = getJsonParameter(request,JSON_PARAMETER_DIRECTION);
  if(fmod(stepAngle,motorStepAngle) > 0) {
    stepAngle = stepAngle - fmod(stepAngle,motorStepAngle);
  }
  int steps = stepAngle / motorStepAngle;
  if(directionIndication == DIRECTION_CLOCKWISE) {
    steps=abs(steps);
  } else {
    steps=-abs(steps);
  }
  stepper.runToNewPosition(stepper.currentPosition() + steps);
  char stepAngleAsString[16];
  dtostrf(stepAngle,3,2,stepAngleAsString);
  char currentPosition[16];
  itoa(stepper.currentPosition(),currentPosition,10);
  char stepsAsString[16];
  itoa(abs(steps),stepsAsString,10);
  addJsonParameter(response,JSON_PARAMETER_DEGREES,stepAngleAsString);
  addJsonParameter(response,JSON_PARAMETER_STEPS,stepsAsString);
  addJsonParameter(response,JSON_PARAMETER_POSITION,currentPosition);
  addJsonParameter(response,JSON_PARAMETER_STATUS,STATUS_ROTATION_FINISHED);
}

void power(aJsonObject* request, aJsonObject* response) {
  String powerToggle = getJsonParameter(request,JSON_PARAMETER_TOGGLE);
  if(powerToggle == TOGGLE_ON) {
    stepper.enableOutputs();
    stepper.runSpeed();
    isPowerOn = true;
    addJsonParameter(response,JSON_PARAMETER_STATUS,STATUS_POWER_ON);
  } else {
    stepper.disableOutputs();
    motor.release();
    isPowerOn = false;
    addJsonParameter(response,JSON_PARAMETER_STATUS,STATUS_POWER_OFF);
  }
}

void reset(aJsonObject* request, aJsonObject* response) {
  stepper.setCurrentPosition(RESET_POSITION);
  addJsonParameter(response,JSON_PARAMETER_STATUS,STATUS_RESET);
}

int validateInput(aJsonObject* request, aJsonObject* response) {
  if(request) {
    String commandString = getJsonParameter(request,JSON_PARAMETER_COMMAND);
    if(commandString != COMMAND_NAME_INITIALIZE & !isMotorInitialized) {
      addJsonParameter(response,JSON_PARAMETER_ERROR,ERROR_MOTOR_IS_NOT_INITIALIZED);
      return COMMAND_ERROR;
    }
    if(commandString == COMMAND_NAME_INITIALIZE) {
      if(atoi(getJsonParameter(request,JSON_PARAMETER_MOTOR_PORT)) <= 0) {
        addJsonParameter(response,JSON_PARAMETER_ERROR,ERROR_MOTOR_PORT_WRONG);
        return COMMAND_ERROR;
      } else if(atoi(getJsonParameter(request,JSON_PARAMETER_MOTOR_TOTAL_STEPS)) <= 0) {
        addJsonParameter(response,JSON_PARAMETER_ERROR,ERROR_MOTOR_TOTAL_STEPS_WRONG);
        return COMMAND_ERROR;
      } else if(atof(getJsonParameter(request,JSON_PARAMETER_MOTOR_STEP_ANGLE)) <= 0) {
        addJsonParameter(response,JSON_PARAMETER_ERROR,ERROR_MOTOR_STEP_ANGLE_WRONG);
        return COMMAND_ERROR;
      } else if(atoi(getJsonParameter(request,JSON_PARAMETER_MOTOR_MAX_SPEED)) <= 0) {
        addJsonParameter(response,JSON_PARAMETER_ERROR,ERROR_MOTOR_MAX_SPEED_WRONG);
        return COMMAND_ERROR;
      } else if(atoi(getJsonParameter(request,JSON_PARAMETER_MOTOR_ACCELERATION)) <= 0) {
        addJsonParameter(response,JSON_PARAMETER_ERROR,ERROR_MOTOR_ACCELERATION_WRONG);
        return COMMAND_ERROR;
      }
      return COMMAND_INITIALIZE;
    } else if(commandString == COMMAND_NAME_ROTATE) {
      String directionString = getJsonParameter(request,JSON_PARAMETER_DIRECTION);
      if(directionString != DIRECTION_CLOCKWISE & directionString != DIRECTION_COUNTERCLOCKWISE) {
        addJsonParameter(response,JSON_PARAMETER_ERROR,ERROR_ROTATION_DIRECTION_NOT_UNDERSTOOD);
        addJsonParameter(response,JSON_PARAMETER_ERROR_VALUE,getJsonParameter(request,JSON_PARAMETER_DIRECTION));
        return COMMAND_ERROR;
      }
      if(atof(getJsonParameter(request,JSON_PARAMETER_DEGREES)) <= 0) {
        addJsonParameter(response,JSON_PARAMETER_ERROR,ERROR_ROTATION_DEGREE_VALUE_TOO_SMALL);
        addJsonParameter(response,JSON_PARAMETER_ERROR_VALUE,getJsonParameter(request,JSON_PARAMETER_DEGREES));
        return COMMAND_ERROR;
      }
      return COMMAND_ROTATE;
    } else if(commandString == COMMAND_NAME_POWER) {
      String toggleString = getJsonParameter(request,JSON_PARAMETER_TOGGLE);
      if(toggleString != TOGGLE_ON & toggleString != TOGGLE_OFF) {
        addJsonParameter(response,JSON_PARAMETER_ERROR,ERROR_POWER_TOGGLE_VALUE_NOT_UNDERSTOOD);
        addJsonParameter(response,JSON_PARAMETER_ERROR_VALUE,getJsonParameter(request,JSON_PARAMETER_TOGGLE));        
        return COMMAND_ERROR;
      }
      return COMMAND_POWER;
    } else if(commandString == COMMAND_NAME_RESET) {
      return COMMAND_RESET;
    }
  }
  addJsonParameter(response,JSON_PARAMETER_ERROR,ERROR_REQUEST_NOT_UNDERSTOOD);
  return COMMAND_ERROR;
}

char* getJsonParameter(aJsonObject* item,const char* parameter) {
  return aJson.getObjectItem(item,parameter)->valuestring;
}

void addJsonParameter(aJsonObject* item,const char* parameter, const char* value) {
  aJson.addItemToObject(item,parameter,aJson.createItem(value));
}
