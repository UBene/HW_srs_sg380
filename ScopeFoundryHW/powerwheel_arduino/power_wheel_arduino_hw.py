'''
Created on Sep 23, 2014

@author: Benedikt 

updated on 2022/02/11 MIGHT NOT BE BACKWARD COMPADIBLE
'''
from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.powerwheel_arduino.power_wheel_arduino_dev import PowerWheelArduino

import time


class PowerWheelArduinoHW(HardwareComponent):
    
    name = 'power_wheel'
    
    def __init__(self, app, debug=False, name=None, conv=3200 / 360):
        self.conv = conv  # steps per deg
        HardwareComponent.__init__(self, app, debug=debug, name=name)
    
    def setup(self): 
        S = self.settings     
        self.settings.New('encoder_pos', dtype=int, unit='steps', ro=True)
        self.settings.New('port', dtype=str, initial='COM4')
        self.settings.New('position', float, unit='deg', ro=True)
        self.settings.New('jog', initial=10.0, unit='deg')
        self.settings.New('target_position', float, unit='deg')
        self.settings.target_position.add_listener(self.move_to_position)
        self.settings.New('reverse', bool, initial=False)
        #  operations
        self.add_operation("zero_encoder", self.zero_encoder)
        self.add_operation("jog_forward", self.jog_forward)
        self.add_operation("jog_backward", self.jog_backward)

    def connect(self):
                
        if self.debug_mode.val: print("connecting to arduino power wheel")
        S = self.settings
        
        self.dev = PowerWheelArduino(port=S['port'], debug=S['debug_mode'])        
        self.dev.write_speed(120)
        S.encoder_pos.connect_lq_scale(S.position, self.conv)
        S.encoder_pos.connect_to_hardware(self.dev.read_encoder)
        
        if S['debug_mode']: print('connected to ', self.name)

    def disconnect(self):
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev        
        if self.settings['debug_mode']: print('disconnected ', self.name)

    def move_relative(self, d_steps):
        if self.settings['debug_mode']:
            print(self.name, 'move relative', d_steps)
        self.dev.write_steps_and_wait(d_steps)
        time.sleep(0.5)
        
        # TODO really should wait until done
        pos = self.settings.encoder_pos.read_from_hardware()
        if self.settings['debug_mode']:
            print(self.name, 'new encoder pos', pos)
    
    def move_to_position(self):
        S = self.settings
        d_steps = (S['target_position'] - S['position']) * self.conv
        self.move_relative(d_steps)
    
    def jog_forward(self):
        S = self.settings
        target = S['target_position'] + S['jog']
        if S['debug_mode']:
            print(self.name, 'jog_forward', target)
        self.settings['target_position'] = target
        # self.dev.write_steps_and_wait(self.move_steps.val)
        time.sleep(0.2)
        S.encoder_pos.read_from_hardware()

    def jog_backward(self):
        S = self.settings
        target = S['target_position'] - S['jog']
        if S['debug_mode']:
            print(self.name, 'jog_backward', target)
        self.settings['target_position'] = target        
        time.sleep(0.1)
        S.encoder_pos.read_from_hardware()

    def zero_encoder(self):
        self.dev.write_zero_encoder()
        time.sleep(0.1)
        pos = self.settings.encoder_pos.read_from_hardware()
        self.settings['position'] = pos / self.conv
        self.settings['target_position'] = pos / self.conv

