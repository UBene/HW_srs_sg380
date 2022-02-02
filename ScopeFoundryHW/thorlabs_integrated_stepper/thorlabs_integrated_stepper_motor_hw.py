'''
Created on Mar 7, 2018

@author: lab
'''
import time
from ScopeFoundry.hardware import HardwareComponent
from .thorlabs_integrated_stepper_motor_dev import ThorlabsIntegratedStepperMotorDev


class ThorlabsIntegratedStepperMottorHW(HardwareComponent):
    
    name = 'motorized_polarizer'
        
    def setup(self):
        self.settings.New('serial_num', dtype=int, initial=55000231)
        self.settings.New('position', dtype=float, initial=0, unit='deg')
        self.settings.New('target_position', dtype=float, initial=0, unit='deg')
        self.settings.New('steps_per_deg', initial=12288000 / 90., dtype=float, unit='steps/deg',
                          description='scales device units to degree')
        self.settings.New('jog_step', float, initial=5, unit='deg')
        self.add_operation('home', self.home)
        self.add_operation('jog_forward', self.jog_forward)
        self.add_operation('jog_backward', self.jog_backward)
        
    def connect(self):
        S = self.settings
        self.dev = ThorlabsIntegratedStepperMotorDev(dev_num=0,
                                                     serial_num=S['serial_num'],
                                                     debug=S['debug_mode'])        
        S.position.connect_to_hardware(self.read_position_deg)
        S.target_position.connect_to_hardware(write_func=self.move_and_wait_deg)
        self.read_from_hardware()
        
    def disconnect(self):
        if hasattr(self, 'dev'):
            self.dev.close_device()
            del self.dev
        
    def home(self):
        self.dev.home_and_wait()
        
    def move_and_wait_deg(self, new_pos, timeout=10):
        S = self.settings
        target_position_steps = int(round(S['steps_per_deg'] * new_pos))
        self.dev.write_move_to_position(target_position_steps)
        t0 = time.time()
        while(abs(S.position.read_from_hardware() - new_pos) > 0.05):
            if S['debug_mode']: 
                print(self.name, 'waiting - delta position', S['position'] - new_pos)
            time.sleep(0.1)
            if (time.time() - t0) > timeout:
                self.stop_profiled()
                raise(IOError("Failed to move"))

    def read_position_deg(self):
        return self.dev.read_position() / self.settings['steps_per_deg']
    
    def jog_forward(self):
        S = self.settings        
        S['target_position'] = S['position'] + S['jog_step']
        
    def jog_backward(self):
        S = self.settings
        S['target_position'] = S['position'] - S['jog_step']
