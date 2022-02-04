'''
Created on 03/01/2018
@author: Benedikt Ursprung
'''

from .stepper_motor_arduino_hw import StepperMotorArduinoHw
import time

class FilterWheelArduinoHW(StepperMotorArduinoHw):
    
    name = 'filter_wheel'
    debug = False

    steps_per_rev = 200
    num_filter = 6 

    def setup(self):
        StepperMotorArduinoHw.setup(self)
        
        #filters will be zero indexed
        self.filter_encoder_position = { int(i) : int(i*self.steps_per_rev/self.num_filter) 
                                        for i in range(self.num_filter)}
        
        self.current_filter = self.settings.New('current_filter', initial = 0, dtype=int, ro=False, 
                                                vmin=0, vmax=self.num_filter-1)
        self.target_filter = self.settings.New('target_filter',   initial = 0, dtype=int, ro=False, 
                                               vmin=0, vmax=self.num_filter-1)
        self.calibrated=self.settings.New('is_explicitly_calibrated', dtype=bool, initial=False, ro=True)      

        self.add_operation('zero_filter', self.zero_filter)
        self.add_operation('filter_fwd', self.increase_target_filter)
        self.add_operation('filter_bkwd', self.decrease_target_filter)        


    def increase_target_filter(self):
        target = self.settings['target_filter'] + 1
        if target>(self.num_filter-1):
            target = target%self.num_filter
        self.target_filter.update_value(target)
            
    def decrease_target_filter(self):
        target = self.settings['target_filter'] - 1
        if target<0:
            target = self.num_filter+target 
        self.target_filter.update_value(target)

    def connect(self):
        StepperMotorArduinoHw.connect(self)    
        self.target_filter.add_listener(self.update_filter)    
        self.read_from_hardware()
                
    def zero_filter(self):
        #set encoder position to zero and current_filter to 0
        print('Current filter set to 0')
        self.current_filter.update_value(0)
        self.calibrated.update_value(True)
        self.zero_encoder()
        time.sleep(0.1)
        self.target_filter.update_value(0) 
        
    def update_filter(self):
        S = self.settings
        
        if S['target_filter'] > self.num_filter or S['target_filter'] < 0:
            self.logger(self.name,'target_filter (',S['target_filter'],') does not exist')
            pass
        
        target_position = self.filter_encoder_position[S['target_filter']]
        current_position = S['encoder_pos']
        d_steps = target_position-current_position
    
        if d_steps == 0:
            pass
        if d_steps > self.steps_per_rev/2:
            d_steps -= self.steps_per_rev
        if d_steps < -self.steps_per_rev/2:
            d_steps += self.steps_per_rev
        
        #print(target_position,current_position,d_steps)
        
        self.move_relative(d_steps)
        self.current_filter.update_value(S['target_filter'])
            