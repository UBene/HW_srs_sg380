'''
Created on 03/01/2018
@author: Benedikt Ursprung
Generalizes PowerWheelArduinoDev
assumes: stepper_motor_arduino_firmware_*
'''

import serial
import time

class StepperMottorArduinoDev(object):
    """Arduino controlled Stepper motor"""
    
    def __init__(self, port="COM10", debug = False, name='stepper_motor_arduino'):
        self.port = port
        self.debug = debug
        self.name = name
        
        if self.debug: print("StepperMottorArduinoDev {} init, port={}".format(self.name, self.port))
        
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

    def send_cmd(self, cmd, motor="a"):
        '''
        totals serial commands are of the form: 
        b"<char Motor><char Cmd><int Number>\n"
        where Motor is 'a' or 'b'
        '''
        cmd_ = str(motor + cmd + "\n").encode()
        if self.debug: print("send_cmd:", repr(cmd_))
        self.ser.write( cmd_ )
    
    def ask_cmd(self, cmd, motor='a'):
        if self.debug: print("ask:", repr(cmd))
        self.send_cmd(cmd,motor)
        time.sleep(0.01)
        resp = self.ser.readline()
        if self.debug: print("resp:", repr(resp))
        return resp 

    def write_steps(self,steps, motor='a'):
        """ 
        Non-blocking movement of :steps:cd
        """
        self.send_cmd('m%i' % steps, motor)
            
        
    def write_steps_and_wait(self,steps, motor='a'):
        """ 
        Moves wheel by :steps:
        blocks until motion is complete
        """
        self.write_steps(steps,motor)
        self.read_status()
        
        while(self.is_moving_to):
            if self.debug: print('sleep')
            time.sleep(0.050)
            self.read_status()
            
    def write_steps_constant(self, steps, motor='a'):
        """ 
        Non-blocking movement of :steps: at constant speed
        """
        self.send_cmd('c%i' % steps, motor)
            
    def write_steps_constant_and_wait(self,steps, motor='a'):
        """ 
        Moves wheel by :steps: at constant speed
        blocks until motion is complete
        """
        self.write_steps_constant(steps, motor)
        self.read_status()
        
        while(self.is_moving_to):
            if self.debug: print('sleep')
            time.sleep(0.050)
            self.read_status()
    
    def write_speed(self, speed, motor='a'):
        self.send_cmd("s{}".format(speed), motor)
    
    def read_speed(self, motor='a'):
        self.read_status(motor)
        return self.stored_speed
        
    def read_status(self, motor='a'):
        status = self.ask_cmd("?",motor).decode("utf-8") 
        status = status.strip().split(',')
        self.is_moving_to = bool(int(status[0]))
        self.stored_speed = int(status[1])
        self.encoder_pos  = int(status[2])
        self.distance_to_go = int(status[3])
        self.max_speed = int(status[4])
        self.acceleration = float(status[5])
        if self.debug:
            print("read_status", status, self.is_moving_to, self.stored_speed, 
                  self.encoder_pos, self.distance_to_go,self.max_speed, self.acceleration)
        return status    

    def read_max_speed(self, motor='a'):
        self.read_status(motor)
        if self.debug:
            print("max_speed", self.max_speed)
        return self.max_speed

    def read_accerleration(self, motor='a'):
        self.read_status(motor)
        if self.debug:
            print("acceleration", self.acceleration)
        return self.acceleration
    
    def read_encoder(self, motor='a'):
        self.read_status(motor)
        if self.debug:
            print("read_encoder", self.encoder_pos)
        return self.encoder_pos
        
    def write_zero_encoder(self, motor='a'):
        self.send_cmd("z", motor)
    
    def write_max_speed(self,max_speed, motor='a'):
        self.send_cmd('y{}'.format(int(max_speed)),motor)

    def write_acceleration(self, acc, motor='a'):
        self.send_cmd('a{}'.format(int(acc)),motor)
        
    def write_brake(self, motor='a'):
        self.send_cmd("b", motor)
        
    def close(self):
        self.ser.close()


if __name__ == '__main__':
    W1 = StepperMottorArduinoDev(debug=True);
    time.sleep(1)
    W1.write_steps_and_wait(-400)
    time.sleep(1)
    W1.write_steps(400)    
    
    W1.read_status()
    
    
    W1.close()
    pass