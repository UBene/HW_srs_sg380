'''
Created on May 17, 2018

@author: lab
'''
from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.arduino_tc4.arduino_tc4_dev import ArduinoTc4Dev

class ArduinoTc4HW(HardwareComponent):
    
    name = 'arduino_tc4'
    def setup(self):
        self.ser_port = self.settings.New('ser_port', dtype=str, initial='COM12')
        self.temp = self.settings.New('temperature', float, initial=-1.,ro=True, 
                                      spinbox_decimals=3, unit='C') 
        
    def connect(self):
        self.dev = ArduinoTc4Dev(self.ser_port.val)
        self.temp.connect_to_hardware(read_func=self.read_temp, write_func=None)
        
    def read_temp(self):
        return self.dev.read_temp()
    
    def disconnect(self):
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev