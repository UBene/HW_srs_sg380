/* stepper_motor_arduino_firmware
 * uses AccelStepper Objects and provides serial command API to controll a .
 * 
  Serial Commands (baudrate=57600) are of the form
  b"<char Motor><char Cmd><int Number>\n"
  Motor: 'a' or 'b'
  Cmd: (see bellow)
  Number:  integeter value (if any) associated with the Cmd

  Example 1: b"as100\n"
   sets the motor speed to 100
  Example 2: b"b?"
   returns the byte representation of a string discribing the state of motor 'b'
   b"<bool is_moving>,<int speed>,<int currentPosition()>,<int distanceToGo()>,<int maxSpeed()>,<int acceleration>\r\n"

  Author:  Benedikt Ursprung (BenediktUrsprung@gmail.com)
           heavily inspired by Edward Barnard
  Created: 03/01/2018
  Last updated: 03/01/2018
*/


#include <Wire.h>
#include <AccelStepper.h>

// DEFINE THIS SETTINGS FOR EACH MOTOR:
// In particular define <int HAND_i> and <AccelStepper stepperi> where i is A,B
#include <Adafruit_MotorShield.h>
// Create the motor shield object with the default I2C address
Adafruit_MotorShield AFMStop(0x60); // Default address, no jumpers

//DEFINE MOTOR 'a'
Adafruit_StepperMotor *myStepperA = AFMStop.getStepper(200, 2); //uses M3 and M4 and has 200 steps per rev.
void forwardstepA() {
  myStepperA->onestep(FORWARD, DOUBLE);// you can change these to SINGLE, DOUBLE or INTERLEAVE or MICROSTEP!
}
void backwardstepA() {
  myStepperA->onestep(BACKWARD, DOUBLE);
}
AccelStepper stepperA(forwardstepA, backwardstepA);
int HAND_A = -1; //-1 Flips the direction


//DEFINE MOTOR 'b'
Adafruit_StepperMotor *myStepperB = AFMStop.getStepper(200, 1);
void forwardstepB() {
  myStepperB->onestep(FORWARD, DOUBLE);
}
void backwardstepB() {
  myStepperB->onestep(BACKWARD, DOUBLE);
}
AccelStepper stepperB(forwardstepB, backwardstepB);
int HAND_B = -1;



//IDEPEDANT OF MOTORS AND MOTOR SHIELD:
const int INPUTBUFFER_LENGTH = 150;
String inputString = "";         // a string to hold incoming data
boolean stringComplete = false;  // whether the string is complete
long inputNumber;
char inputNumberBuffer[INPUTBUFFER_LENGTH];

char cmd_charM; //stepper A or B
char cmd_charC; //cmd char

//convience pointers
AccelStepper *stepper;
boolean *is_moving_to;
int *HAND;
float *acceleration;

// other state variables
boolean is_moving_to_A = false;
boolean is_moving_to_B = false;

float acceleration_A = 100; //AccelStepper has no getAccerleration() Method
float acceleration_B = 100;



void setup()
{
  Serial.begin(57600);             // set up Serial library at 57600 bps

  AFMStop.begin();
  stepperA.setMaxSpeed(100);
  stepperA.setAcceleration(acceleration_A);

  stepperB.setMaxSpeed(100);
  stepperB.setAcceleration(acceleration_B);

  delay(500);
}

int m;


void loop()
{
  if (is_moving_to_A) {
    stepperA.run();
    if (stepperA.distanceToGo() == 0) {
      is_moving_to_A = false;
    }
  }
  if (is_moving_to_B) {
    stepperB.run();
    if (stepperB.distanceToGo() == 0) {
      is_moving_to_B = false;
    }
  }

  serialEvent(); //checks for incoming serial commands

  if (stringComplete) {

    cmd_charM = tolower(inputString[0]);
    switch (cmd_charM) {
      case 'a': { //Stepper Motor a{
          stepper = &stepperA;
          is_moving_to = &is_moving_to_A;
          HAND = &HAND_A;
          acceleration = &acceleration_A;
          break;
        }
      case 'b': {
          stepper = &stepperB;
          is_moving_to = &is_moving_to_B;
          HAND = &HAND_B;
          acceleration = &acceleration_B;
          break;
        }
    }


    cmd_charC = tolower(inputString[1]);
    inputNumber = interpret_int_from_string(inputString.substring(2));
    switch (cmd_charC) {
      case 's': //set speed
        stepper->setSpeed(abs(inputNumber));
        break;
      case 'b': //brake
        stepper->stop();
        *is_moving_to = false;
        break;
      case 'f': //turn motor off
        stepper->stop();
        *is_moving_to = false;
        break;
      case 'e': // get encoder position
        Serial.println(*HAND * stepper->currentPosition());
        break;
      case 'z': // zero encoder
        stepper->stop();
        stepper->setCurrentPosition(0);
        *is_moving_to = false;
        break;
      case 'm': //delta move
        stepper->move(*HAND * inputNumber);
        *is_moving_to = true;
        break;

      case 'c': //delta move constant
        stepper->move(*HAND * inputNumber);
        //Caution: moveTo() also recalculates the speed for the next step.
        //If you are trying to use constant speed movements, you should call setSpeed() after calling moveTo().
        stepper->setSpeed(float(sign(*HAND * inputNumber) * abs(stepper->speed())));
        *is_moving_to = true;
        break;

      case '?': // query status
        Serial.print(*is_moving_to); Serial.print(",");
        Serial.print(int(abs(stepper->speed()))); Serial.print(",");
        Serial.print(*HAND * stepper->currentPosition()); Serial.print(",");
        Serial.print(*HAND * stepper->distanceToGo()); Serial.print(",");
        Serial.print(int(stepper->maxSpeed())); Serial.print(",");
        Serial.print(*acceleration);
        Serial.println(""); //sends \r\n
        break;
      case 'y':
        stepper->setMaxSpeed(inputNumber);
        break;
      case 'a':
        stepper->setAcceleration(float(inputNumber));
        *acceleration = float(inputNumber);
        break;
    }

    // clear the string:
    inputString = "";
    stringComplete = false;
  }
}
// end of loop




long interpret_int_from_string(String in) {
  in.trim();
  in.toCharArray(inputNumberBuffer, INPUTBUFFER_LENGTH);
  return atol(inputNumberBuffer);
}

int sign(int x) {
  return (x > 0) - (x < 0);
}


// serial interrupt handler
void serialEvent() {
  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();
    // add it to the inputString:
    inputString += inChar;
    // if the incoming character is a newline, set a flag
    // so the main loop can do something about it:
    if (inChar == '\n') {
      stringComplete = true;
      //Serial.println(inputString);
    }
  }
}
