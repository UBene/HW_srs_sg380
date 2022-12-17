
#include <Servo.h> 
 
Servo myservo;  // create servo object to control a servo 
                // twelve servo objects can be created on most boards
 
int pos = 0;    // variable to store the servo position 


const int INPUTBUFFER_LENGTH = 150;

String inputString = "";         // a string to hold incoming data
boolean stringComplete = false;  // whether the string is complete
long inputNumber;
char inputNumberBuffer[INPUTBUFFER_LENGTH];



void setup() {
  // put your setup code here, to run once:
    Serial.begin(9600);             // set up Serial library at 57600 bps
    myservo.attach(8);  // attaches the servo on pin 9 to the servo object 

}

void loop() {
  // put your main code here, to run repeatedly:
    serialEvent();

    if (stringComplete) {
      if (inputString[0] == '?') {
        Serial.println(pos);
      }
      else {
        inputNumber = interpret_int_from_string(inputString);
        pos = inputNumber;
        myservo.write(pos);
      }
      
        // clear the string:
        inputString = "";
        stringComplete = false;
    }
}



long interpret_int_from_string(String in) {
    in.trim();
    /*for (int i=2; i<INPUTBUFFER_LENGTH; i++){
      inputNumberBuffer[i-2]=in[i];
    }
    */
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
