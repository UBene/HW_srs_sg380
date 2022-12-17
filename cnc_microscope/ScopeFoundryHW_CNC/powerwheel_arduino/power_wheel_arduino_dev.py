'''
Created on 21.09.2014

@author: Benedikt Ursprung
'''

import serial
import time

class PowerWheelArduino(object):
    """Arduino controlled Stepper motor Power ND filter Wheel"""
    
    def __init__(self, port="COM16", debug = False):
        self.port = port
        self.debug = debug
        
        if self.debug: print("PowerWheelArduino init, port=%s" % self.port)
        
        self.ser = serial.Serial(port=self.port, baudrate=57600, timeout=1.0)
                          
                          
        # Toggle DTR to reset Arduino
        #self.ser.setDTR(False)
        time.sleep(1)
        # toss any data already received, seeW
        # http://pyserial.sourceforge.net/pyserial_api.html#serial.Serial.flushInput
        self.ser.flushInput()
        #self.ser.flush()
        #self.ser.setDTR(True)       
        time.sleep(0.1)
        self.ser.readline()


    def send_cmd(self, cmd):
        if self.debug: print("send_cmd:", repr(cmd))
        self.ser.write(cmd + b"\n")
    
    def ask_cmd(self, cmd):
        if self.debug: print("ask:", repr(cmd))
        self.send_cmd(cmd)
        time.sleep(0.01)
        resp = self.ser.readline()
        if self.debug: print("resp:", repr(resp))
        return resp 

    def write_steps(self,steps):
        """ Non-blocking movement of :steps:
        """
        self.send_cmd(b'am%i' % steps)
        #print "steps ", steps
    
    def write_steps_and_wait(self,steps):
        """ Moves wheel by :steps:
        blocks until motion is complete
        """
        self.write_steps(steps)
        self.read_status()
        
        while(self.is_moving_to):
            if self.debug: print('sleep')
            time.sleep(0.050)
            self.read_status()
        
        
    
    def write_speed(self, speed):
        self.send_cmd(b'as%i'% speed)
    
    def read_speed(self):
        self.read_status()
        return self.stored_speed
        
    def read_status(self):
        status = self.ask_cmd(b"a?")
        status = status.strip().split(b',')
        self.is_moving_to = bool(int(status[0]))
        self.stored_speed = int(status[1])
        self.encoder_pos  = int(status[2])
        self.distance_to_go = int(status[3])
        
        if self.debug:
            print("read_status", status, self.is_moving_to, self.stored_speed, self.encoder_pos, self.distance_to_go)
        
        return status    
    
    def read_encoder(self):
        self.ser.write(b'ae\n')
        resp=self.ser.readline() 
        self.encoder_pos = int(resp)       
        if self.debug:
            print("read_encoder", self.encoder_pos)

        return self.encoder_pos
        
    def write_zero_encoder(self):
        self.send_cmd(b"az")


    def write_brake(self):
        self.send_cmd(b"ab")
        
    def close(self):
        self.ser.close()      
        


if __name__ == '__main__':
    W1 = PowerWheelArduino(debug=True);
    time.sleep(4)
    W1.write_steps(-400)
    time.sleep(4)
    W1.write_steps(400)    
    
    W1.read_status()
    
    
    W1.close()
    pass