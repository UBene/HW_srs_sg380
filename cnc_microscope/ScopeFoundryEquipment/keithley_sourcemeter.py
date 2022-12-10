'''

Kaiyuan Yao
12/08/2018

Reference: https://pymeasure.readthedocs.io/en/latest/api/instruments/keithley/keithley2400.html

'''

from __future__ import division
import numpy as np
import time
import matplotlib.pyplot as plt
import serial
from pymeasure.instruments.keithley import Keithley2400



class KeithleySourceMeter(object):#object -->KeithleySourceMeterComponent
    '''
    classdocs
    '''
    
    def __init__(self, port="GPIB::23", debug=False):
        self.port = port
        self.debug = debug
        
        #self.ser = serial.Serial(port=self.port, baudrate = self.KeithleyBaudRate)#,  stopbits=1, xonxoff=0, rtscts=0, timeout=5.0       
        #self.ser.flush()
        #time.sleep(0.1)      
        
        self.sourcemeter = Keithley2400(self.port) 
        time.sleep(0.1) 
        
        
    def close(self):
        self.sourcemeter.shutdown()
        print ('closed keithley')   
        
    
    def get_ID(self):
        resp = self.sourcemeter.id  
        return resp   
    
    def beep_test(self):
        #Parameters:    
        #frequency: A frequency in Hz between 65 Hz and 2 MHz
        #duration: A time in seconds between 0 and 7.9 seconds
        self.sourcemeter.beep(frequency=100, duration = 1) #100Hz, 3 seconds

    def reset(self):
        ##### Resets the instrument and clears the queue
        self.sourcemeter.reset()
    
    def reset_buffer(self):
        ##### Resets the buffer
        self.sourcemeter.reset_buffer()
     
    def set_auto_range(self):
        self.sourcemeter.auto_range_source()    
        
    def configure_current_source(self, Irange, Vcomp):
        ###unit in [A] and [V]
        self.sourcemeter.apply_current(current_range = Irange, compliance_voltage = Vcomp)
    
    def configure_voltage_source(self, Vrange, Icomp):
        ###unit in [A] and [V]
        self.sourcemeter.apply_voltage(voltage_range = Vrange, compliance_current = Icomp)    
        
    def enable_source(self):
        ####Enable the source depending on the setup
        self.sourcemeter.enable_source()
        
    def disable_source(self):
        ####Disables the source of current or voltage depending on the configuration of the instrument
        self.sourcemeter.disable_source()
        
    def configure_measure_voltage(self, nplc_val=1, voltage_lim=21.0, auto_range=True):
        #Configures the measurement of voltage.
        #Parameters:    
        # nplc_val: Number of power line cycles  from 0.01 to 10
        #voltage: Upper limit of voltage in Volts, from -210 V to 210 V
        #auto_range: Enables auto_range if True, else uses the set voltage
        self.sourcemeter.measure_voltage(nplc_val, voltage_lim, auto_range)
        
    def configure_measure_current(self, nplc_val=1, current_lim=0.000105, auto_range=True):
        #Configures the measurement of current
        #Parameters:    
        #nplc_val: Number of power line cycles  from 0.01 to 10
        #current: Upper limit of current in Amps, from -1.05 A to 1.05 A
        #auto_range: Enables auto_range if True, else uses the set current
        self.sourcemeter.measure_current(nplc_val, current_lim, auto_range)
        
    def ramp_source_voltage(self, target_voltage, steps=30, pause=0.02):
        self.sourcemeter.ramp_to_voltage(target_voltage, steps, pause)
        
    def ramp_source_current(self, target_current, steps = 30, pause=0.02):
        self.sourcemeter.ramp_to_current(target_current, steps, pause)
        
    def set_source_voltage(self, target_voltage):
        self.sourcemeter.source_voltage = target_voltage
         
    def set_source_current(self, target_current):
        self.sourcemeter.source_current = target_current
        
    def read_current(self):
        ####read the I in Amps using current configurations.
        return self.sourcemeter.current
    
    def read_voltage(self):
        ###read the V in volts using current configurations.
        ## Note: when in voltage source mode, this actually returns source current
        return self.sourcemeter.voltage
    
    def read_source_enabled(self):
        ###Reads a boolean value that is True if the source is enabled.
        print (self.sourcemeter.source_enabled)
        return self.sourcemeter.source_enabled
    
    def read_source_mode(self):
        ###A string property that controls the source mode
        return self.sourcemeter.source_mode 
    
    def set_source_mode(self, target_mode = 'voltage'):
        ###A string property that controls the source mode, which can take the values 
        self.sourcemeter.source_mode = target_mode
        
        
        

    
 
        
        
        


   
#############################################


if __name__ == '__main__':
    
    K1 = KeithleySourceMeter()

    K1.reset()
    #K1.reset_buffer() #doing this will result in Err 800
    #K1.beep_test()
    
    resp_ID = K1.get_ID()
    print (resp_ID)
    
    #####Test measurements
    K1.set_auto_range()
    K1.configure_voltage_source(Vrange=None, Icomp=1e-3)
    K1.configure_measure_current(nplc_val = 1, current_lim = 1e-3, auto_range = True)
    
    K1.enable_source()
    #K1.ramp_source_voltage(target_voltage=3.0, steps=10, pause=0.5)
    K1.set_source_voltage(target_voltage=3.0)
    
    for i in range(0, 60):
        print( 'Voltage = {}[V], Current = {}[A]'.format(K1.read_voltage() ,K1.read_current() ) )
        time.sleep(0.1)
   
    
    K1.close()
    #K1.disable_source()
