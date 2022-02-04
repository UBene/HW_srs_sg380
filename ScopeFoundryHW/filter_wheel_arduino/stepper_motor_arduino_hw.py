'''
Created on Mar 1, 2018
Assumes only one motor (defined as Motor 'a' in arduino firmware)
@author: Benedikt Ursprung
Based on power_wheel_arduino
Does NOT support (yet): two or more motors on a arduino/driver pair.
'''

from ScopeFoundry import HardwareComponent
import time
from builtins import int

try:
    from .stepper_motor_arduino_dev import StepperMottorArduinoDev
except Exception as err:
    print("Cannot load required modules for filter_wheel_arduino_hw:", err)

class StepperMotorArduinoHw(HardwareComponent):
    
    name = 'stepper_motor_arduino_hw'
    debug = False

    def setup(self):

        # logged quantity        
        self.ser_port = self.settings.New('ser_port', dtype=str, initial='COM10')
        
        self.encoder_pos = self.settings.New('encoder_pos', dtype=int, unit='steps', ro=True)
        self.move_steps  = self.settings.New('move_steps',  dtype=int, unit='steps', vmin=1, vmax=3200, initial=10, ro=False)
        self.max_speed = self.settings.New('max_speed', dtype=int, unit='steps/s', ro=False)
        self.acceleration = self.settings.New('acceleration', dtype=int, unit='steps/s2', ro=False)

        #  operations
        self.add_operation("zero_encoder", self.zero_encoder)
        self.add_operation("move_fwd", self.move_fwd)
        self.add_operation("move_bkwd", self.move_bkwd)

    def connect(self):
        if self.debug: print("connecting to", self.name)
        # Open connection to hardware
        D = self.stepper_motor_dev = StepperMottorArduinoDev(port=self.ser_port.val, debug=self.debug_mode.val, name=self.name)
        
        # connect logged quantities
        self.encoder_pos.hardware_read_func=D.read_encoder
        self.max_speed.connect_to_hardware(D.read_max_speed,D.write_max_speed)
        self.acceleration.connect_to_hardware(D.read_accerleration,D.write_acceleration)

        print('connected to ',self.name)

    def disconnect(self):

        #disconnect logged quantities from hardware
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
    
        if hasattr(self, 'stepper_motor_dev'):
            #disconnect hardware
            self.stepper_motor_dev.close()
            
            # clean up hardware object
            del self.stepper_motor_dev
        
        print('disconnected ',self.name)

    def move_relative(self, d_steps):
        self.stepper_motor_dev.write_steps_and_wait(d_steps)
        #self.stepper_motor_dev.write_steps_and_wait(d_steps)
        time.sleep(0.2)
        self.encoder_pos.read_from_hardware()

    def move_fwd(self):
        self.move_relative(self.move_steps.val)
        
    def move_bkwd(self):
        self.move_relative(-self.move_steps.val)

    def zero_encoder(self):
        self.stepper_motor_dev.write_zero_encoder()
        self.encoder_pos.read_from_hardware()
        
    def write_speed(self, speed):
        self.stepper_motor_dev.write_speed(speed)




