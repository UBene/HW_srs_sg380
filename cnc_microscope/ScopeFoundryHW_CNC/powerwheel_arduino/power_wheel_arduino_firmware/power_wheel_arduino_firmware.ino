// ND PowerWheel Arduino Firmware
// Controls Pololu A4988 Stepper Motor Driver

#include <AccelStepper.h>

#define STEP 13
#define DIR A0
#define RST 8
#define MS1 5
#define MS2 6
#define MS3 7

#define HAND  -1


AccelStepper stepper1(1 , STEP, DIR); 

const char DEFAULT_LED_BRIGHTNESS = 127; 
const int INPUTBUFFER_LENGTH = 150;

String inputString = "";         // a string to hold incoming data
boolean stringComplete = false;  // whether the string is complete
long inputNumber;
char inputNumberBuffer[INPUTBUFFER_LENGTH];

char cmd_charM;
char cmd_charC;

char led_brightness = DEFAULT_LED_BRIGHTNESS;
int8_t led_brightness_dir = 1;
boolean led_state = true;
int led_timer = millis();
int t0 = 0;

boolean is_moving_to = false;


long speed = 500;



void setup()
{

    Serial.begin(57600);             // set up Serial library at 57600 bps
    
    
    stepper1.setMaxSpeed(10000);
    stepper1.setSpeed(speed);
    
    //Serial.println(stepper1.speed());
  
    //Turn off reset
    digitalWrite(RST, HIGH);
    
    // 16th microstepping 0b111	
    digitalWrite(MS1, HIGH);	
    digitalWrite(MS2, HIGH);	
    digitalWrite(MS3, HIGH);

}



void loop()
{    
    if (is_moving_to){
        stepper1.runSpeedToPosition();
        //Serial.println("is moving");
        //Serial.println(stepper1.distanceToGo());
        if (stepper1.distanceToGo() == 0){
          is_moving_to = false;
          //delay(200);
          //Ada_Stepper1->release(); 
          //Serial.println("arrived");
                   
          ///delay(200);         
        }
    }
   
    serialEvent();

    if (stringComplete) {
        
        //Serial.println(inputString); // echo


        cmd_charM = tolower(inputString[0]);   
        cmd_charC = tolower(inputString[1]);

        
        switch(cmd_charM){
           case 'a'://Stepp Motor

        
            switch(cmd_charC) {
                   case 's': //set speed
                    inputNumber = interpret_int_from_string(inputString.substring(2));
                    speed = abs(inputNumber);
                    stepper1.setSpeed(speed);
                 
                    //Serial.print("set speed to ");
                    //Serial.println(speed);
                    //Serial.println(stepper1.speed());

                    break;
                 case 'b': //brake
                    stepper1.stop();                 
                    is_moving_to = false;
                    break;
                 case 'f': //turn motor off 
                    stepper1.stop();                 
                    is_moving_to = false;
                   //Serial.println("release");
                    //Ada_Stepper1->release();
                    break;
    
                 case 'e': // get encoder position
                    Serial.println(HAND*stepper1.currentPosition());
                    break;
                    
                 case 'z': // zero encoder
                     stepper1.stop();
                     stepper1.setCurrentPosition(0);
                     is_moving_to = false;
                     break;
                     
                 case 'm': //delta move
                     inputNumber = interpret_int_from_string(inputString.substring(2));
            
                      //Serial.println(inputNumber);
                      //Serial.println(sign(inputNumber));
                     //speed = stepper1.speed();
                     //Serial.println(  sign(inputNumber) * abs(stepper.speed()) );
                     //stepper1.setSpeed( float(sign(inputNumber) * abs(speed)));
                     //stepper1.setSpeed( float(abs(speed)) );
                     //Serial.println(  stepper1.speed() );
                     stepper1.move(HAND*inputNumber);
                     //stepper1.setSpeed( float(sign(inputNumber) * abs(stepper1.speed())));              
                     stepper1.setSpeed( float(abs(speed)) ); //Caution: moveTo() also recalculates the speed for the next step. If you are trying to use constant speed movements, you should call setSpeed() after calling moveTo().


                     is_moving_to = true; 
                                   
                     break;
                 case '?': // query status
                     Serial.print(is_moving_to); Serial.print(",");
                     Serial.print(int(abs(stepper1.speed()))); Serial.print(",");
                     Serial.print(HAND*stepper1.currentPosition()); Serial.print(",");
                     Serial.print(HAND*stepper1.distanceToGo()); Serial.println("");
    
                     break;
            }
            break;
             case 'b'://Servo
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
