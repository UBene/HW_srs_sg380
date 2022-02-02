'''
Created on May 17, 2018

@author: Benedikt Ursprung
         Edward Barnard
'''

import serial
import time


class ArduinoTc4Dev(object):
    
    def __init__(self, port="COM12", debug = False):
        self.port = port
        self.debug = debug
        
        self.ser = serial.Serial(port=self.port, baudrate=57600, timeout=1.0)
        self.ser.flushOutput()
        self.ser.flushInput()
        
        time.sleep(1.0)
        
    def read_temp(self):
        retry_counter = 0
        MAX_RETRY_COUNTER = 3
        while retry_counter < MAX_RETRY_COUNTER:
            try:
                line = self.ser.readline().decode()
                time_, temp_ = line.split(",")
                temp = float(temp_)
                break
            except(ValueError):
                retry_counter += 1
                time.sleep(0.1)
                temp = -273.15        
        return temp

        
    def close(self):
        self.ser.close()
        
        
if __name__ =='__main__':
    A = ArduinoTc4Dev()
    for i in range(20):
        print(i,A.read_temp())
