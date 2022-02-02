// Serial Communication
const int INPUTBUFFER_LENGTH = 150;

String inputString = "";         // a string to hold incoming data
boolean stringComplete = false;  // whether the string is complete
long inputNumber;
char inputNumberBuffer[INPUTBUFFER_LENGTH];



//Buttons, Pins,
#include <Bounce.h>


const int button1Pin = 21;
const int led1Pin = 23;
const int button2Pin = 20;
const int led2Pin = 22;
const int button3Pin = 14;
const int led3Pin = 16;
const int button4Pin = 15;
const int led4Pin = 17;


Bounce pushbutton1 = Bounce(button1Pin, 10);  // 10 ms debounce
Bounce pushbutton2 = Bounce(button2Pin, 10);  // 10 ms debounce
Bounce pushbutton3 = Bounce(button3Pin, 10);  // 10 ms debounce
Bounce pushbutton4 = Bounce(button4Pin, 10);  // 10 ms debounce



byte button1State = LOW;         // what state was the button last time
byte button2State = LOW;         // what state was the button last time
byte button3State = LOW;         // what state was the button last time
byte button4State = LOW;         // what state was the button last time

// OLED ssd1351 15'' 128x128

// You can use any (4 or) 5 pins 
#define sclk 2
#define mosi 3
#define dc   4
#define cs   5
#define rst  6
// Color definitions
#define	BLACK           0x0000
#define	BLUE            0x001F
#define	RED             0xF800
#define	GREEN           0x07E0
#define CYAN            0x07FF
#define MAGENTA         0xF81F
#define YELLOW          0xFFE0  
#define WHITE           0xFFFF

#include <Adafruit_GFX.h>
#include <Adafruit_SSD1351.h>
#include <SPI.h>


// Option 1: use any pins but a little slower
Adafruit_SSD1351 tft = Adafruit_SSD1351(cs, dc, mosi, sclk, rst);  

// Option 2: must use the hardware SPI pins 
// (for UNO thats sclk = 13 and sid = 11) and pin 10 must be 
// an output. This is much faster - also required if you want
// to use the microSD card (see the image drawing example)
//Adafruit_SSD1351 tft = Adafruit_SSD1351(cs, dc, rst);


int button1_cursor[2]={
  0,40};
int button2_cursor[2]={
  0,60};
int button3_cursor[2]={
  0,80};
int button4_cursor[2]={
  0,100};

int button1_color= BLUE;
int button2_color= GREEN;
int button3_color= YELLOW;
int button4_color= RED;

void printTextCursor(int cursor_[], char *text, uint16_t color){
  tft.setCursor(cursor_[0],cursor_[1]);
  tft.setTextSize(1);
  tft.setTextColor(color,BLACK);
  tft.print(text);  
}

void updateDisplayButton(char *textHigh,char *textLow,boolean buttonState, int button_color, int *button_cursor){
  if (buttonState == HIGH) printTextCursor(button_cursor, textHigh, button_color);
  else printTextCursor(button_cursor, textLow, WHITE);
} 

void updateLed(int ledPin,boolean buttonState){
  digitalWrite(ledPin,buttonState);
}  


void setup() {
  Serial.begin(9600);
  Serial.println("Pushbutton Bounce library test:");
  pinMode(button1Pin, INPUT_PULLUP);
  pinMode(led1Pin, OUTPUT); 

  pinMode(button2Pin, INPUT_PULLUP);
  pinMode(led2Pin, OUTPUT); 

  pinMode(button3Pin, INPUT_PULLUP);
  pinMode(led3Pin, OUTPUT); 

  pinMode(button4Pin, INPUT_PULLUP);
  pinMode(led4Pin, OUTPUT); 

  tft.setRotation(0);
  // NOTE: The test pattern at the start will NOT be rotated!  The code
  // for rendering the test pattern talks directly to the display and
  // ignores any rotation.
  tft.begin();
  uint16_t time = millis();
  tft.fillRect(0, 0, 128, 128, BLACK);
  time = millis() - time;
  tft.fillScreen(BLACK);


  //int titleCursor[2] = {
  //  0,0                };
  //printTextCursor(titleCursor, "WELCOME TO \nTRPL MICROSCOPE\n---------------------", WHITE);
  //updateDisplayButton("Shutter open.",
  //"Shutter closed.",  
  //button1State,button1_color,button1_cursor);
  updateLed(led1Pin,button1State);
}


unsigned int button1PressedSinceLastSinc = 0;
unsigned int button2PressedSinceLastSinc = 0;
unsigned int button3PressedSinceLastSinc = 0;
unsigned int button4PressedSinceLastSinc = 0;

void loop() {

  //LISENING (Update LED, Display)
  serialEvent();
  if (stringComplete) {
    if (inputString[0] == '?') {
      //Serial.println("asked");
      String o1 = btoc(button1State);
      String o2 = btoc(button2State);
      String o3 = btoc(button3State);
      String o4 = btoc(button4State);

      if (button1PressedSinceLastSinc%2 != 0) o1 = btoc(!button1State);
      if (button2PressedSinceLastSinc%2 != 0) o2 = btoc(!button2State);
      if (button3PressedSinceLastSinc%2 != 0) o3 = btoc(!button3State);
      if (button4PressedSinceLastSinc%2 != 0) o4 = btoc(!button4State);      

      String outPut = o1+','+o2+','+o3+','+o4;
      Serial.println(outPut);

      button1PressedSinceLastSinc = 0;
      button2PressedSinceLastSinc = 0;
      button3PressedSinceLastSinc = 0;
      button4PressedSinceLastSinc = 0;
    }

    else if (inputString[0] == 'L') {
      // Black out line
      int lineNo = (inputString[1] - 0x30);
      int yPos = lineNo*20;
      int boxh = 20;
      int boxw = 100;
      tft.fillRect(0, yPos, boxw, boxh, BLACK);
      
      // Print out new line
      int linecursor[2]={0, lineNo*20};
      String message = inputString.substring(2);
      //Serial.println(message);
      int color = WHITE;
      if (lineNo == 1) {
        color = BLUE;
      }
      else if (lineNo == 2) {
        color = GREEN;
      }
      else if (lineNo == 3) {
        color = YELLOW;
      }
      else if (lineNo == 4) {
        color = RED;
      }
      else {
        color = WHITE;
      }
      printTextCursor(linecursor, (char*) message.c_str(), color);
    }

    else if (inputString[0] == 'D') {
      // Black out line only
      int lineNo = (inputString[1] - 0x30);
      int yPos = lineNo*20;
      int boxh = 20;
      int boxw = 100;
      tft.fillRect(0, yPos, boxw, boxh, BLACK);
    }

    else if (inputString[0] == 'B') {
      tft.fillScreen(BLACK);      
    }

    else if (inputString[0] == 'R') {
      updateLed(led1Pin, 0);
      updateLed(led2Pin, 0);
      updateLed(led3Pin, 0);
      updateLed(led4Pin, 0);
    }
    
    else {
      int buttonNumber = interpret_int_from_string(inputString);
      switch (buttonNumber){
      case 1:
        button1State = !button1State;
        //updateDisplayButton("Shutter open.",
        //"Shutter closed.",
        //button1State,button1_color,button1_cursor);
        updateLed(led1Pin,button1State);
        break;     
      case 2:
        button2State = !button2State;
        //updateDisplayButton("button2 not defined   ",
        //"button2 not defined  ",
        //button2State,button2_color,button2_cursor);
        updateLed(led2Pin,button2State);
        break;      
      case 3:
        button3State = !button3State;
        //updateDisplayButton("button3 not defined   ",
        //"button3 not defined  ",
        //button3State,button3_color,button3_cursor);
        updateLed(led3Pin,button3State);
        break;      
      case 4:
        button4State = !button4State;
        //updateDisplayButton("button4 not defined   ",
        //"button4 not defined  ",
        //button4State,button4_color,button4_cursor);
        updateLed(led4Pin,button4State);
        break;          

        //Serial.println("updated buttom 1");
      }
    }

    // clear the string:
    inputString = "";
    stringComplete = false;

  }



  // ON BUTTON push
  if (pushbutton1.update()) {
    if (pushbutton1.fallingEdge()) {
      Serial.println('1');
      //button1PressedSinceLastSinc++;
    }
  }    
  if (pushbutton2.update()) {
    if (pushbutton2.fallingEdge()) {
      Serial.println('2');
      //button2PressedSinceLastSinc++;
    }
  }    
  if (pushbutton3.update()) {
    if (pushbutton3.fallingEdge()) {
      Serial.println('3');
      //button3PressedSinceLastSinc++;
    }
  }    
  if (pushbutton4.update()) {
    if (pushbutton4.fallingEdge()) {
      Serial.println('4');
      //button4PressedSinceLastSinc++;
    }      
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



    // if the incoming character is a newline, set a flag
    // so the main loop can do something about it:
    if (inChar == '\n') {
      stringComplete = true;
      //Serial.println(inputString);
    }  
    else{
      // add it to the inputString:
      inputString += inChar;
    }
  }
}


char btoc(boolean in){
  char r='0';
  if (in == true) 
    r = '1';    
  return r;
}









