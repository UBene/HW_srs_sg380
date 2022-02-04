#define FLIPPER_PIN 12
#define LED_PIN 13

char inByte = 0;
int flip_state = 0;


void setup()
{
  // start serial port at 9600 bps:
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for Leonardo only
  }

  pinMode(FLIPPER_PIN, OUTPUT);
  digitalWrite(FLIPPER_PIN, flip_state);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, flip_state);
}

void loop()
{
  
  if (Serial.available() > 0) {
    // get incoming byte:
    inByte = Serial.read();
    if (inByte == '0') {
      digitalWrite(FLIPPER_PIN, LOW);
      digitalWrite(LED_PIN, LOW);
      flip_state = 0;
    }
    else if (inByte == '1') {
      digitalWrite(FLIPPER_PIN, HIGH);
      digitalWrite(LED_PIN, HIGH);      
      flip_state = 1;  
    }
    else if (inByte == '?') {
      Serial.print(flip_state); 
      //Serial.write("\n"); 
    }
  }
}

