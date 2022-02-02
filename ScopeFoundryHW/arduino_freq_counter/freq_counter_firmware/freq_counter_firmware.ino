#include "FreqCounter.h"

void setup() {
  Serial.begin(57600);                    // connect to the serial port
  Serial.println("Frequency Counter");


}

long int frq;
float hz;
int gate;
void loop() {
gate = 100 ;
 
 FreqCounter::f_comp= 55;             // Set compensation to works with delay
FreqCounter::f_comp= 550;             // Set compensation to 12

FreqCounter::f_comp= 55*(gate/100);             // Set compensation to works with delay

 
 FreqCounter::start(gate);            // Start counting with gatetime of 100ms

 while (FreqCounter::f_ready == 0)         // wait until counter ready
 {
  // read serial
 }
    
    
 frq=FreqCounter::f_freq;            // read result (counts per gate)


 hz = frq * 1000/gate;
 
 Serial.println(hz);                // print result
// Serial.println(millis()); // millis doesn't work with the timer interrupt
 delay(5);

}
