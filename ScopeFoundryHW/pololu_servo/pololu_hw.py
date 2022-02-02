"""
Polulu Micro Maestro ScopeFoundry module
Created on Jul 19, 2017

@author: Alan Buckley

Logistical advice given by Ed Barnard.
"""

from __future__ import division, absolute_import, print_function
from ScopeFoundry import HardwareComponent

import logging

logger = logging.getLogger(__name__)

try:
    from ScopeFoundryHW.pololu_servo.pololu_interface import PololuMaestroDevice
except Exception as err:
    logger.error("Cannot load required modules for PololuMaestroDevice, {}".format(err))

class PololuHW(HardwareComponent):
    
    name = 'pololu_servo_hw'
    
    servo_type_choices = ("Linear", "Rotary")
                        
    servo_type_limit = {'Rotary': (544,2544),
                    'Linear': (1008,2000)}
    
    servo_toggle_settings = {'Rotary': (600, 2100),
                            'Linear': (1200, 1800),}

    
    
    def setup(self):
        """Sets up logged quantities. Sets presets and constants."""
        
        self.settings.New(name='port', initial='/dev/tty.usbmodem2333', dtype=str, ro=False)
        
        
        ## Increase/decrease number of servo slots by modifying the below value.
        self.servo_range = 3
        
        for i in range(self.servo_range):
            self.settings.New(name="servo{}_type".format(i), dtype=str, initial='Linear', choices=self.servo_type_choices, ro=False)
            _vmin, _vmax = self.servo_type_limit[self.settings['servo{}_type'.format(i)]]
            self.settings.New(name="servo{}_position".format(i), dtype=int, 
                                            vmin=_vmin, vmax=_vmax, ro=False)
            self.settings.New(name="servo{}_toggle".format(i), dtype=bool, initial=False, ro=False)
            
            self.settings.New(name="servo{}_toggle_on".format(i), dtype=int, 
                              initial=self.servo_toggle_settings[self.settings["servo{}_type".format(i)]][0], ro=False)
                                                            
            self.settings.New(name="servo{}_toggle_off".format(i), dtype=int, 
                              initial=self.servo_toggle_settings[self.settings["servo{}_type".format(i)]][1], ro=False)   
                                                                 
        ## In my particular setup, I want to override the default value set by the above for loop in the case of servo_0    
        self.settings.get_lq('servo0_type').update_value('Rotary')
        self.update_min_max(0)
        
        # Flip Mirror
        self.flip_mirror_chan = 5
        self.settings.New(name='flip_mirror', dtype=bool, initial=True, ro=False)
        
        
    def connect(self):
        """
        Instantiates device class object, sets up read/write signals, sets up listeners which: update software servo limits, 
        and reinstantiates device object, should the port value be updated. Finally, the function reads all values from hardware.
        """
        self.dev = PololuMaestroDevice(port=self.settings['port'])
        
        for i in range(self.servo_range):
            self.settings.get_lq('servo{}_position'.format(i)).connect_to_hardware(
                                                    write_func=getattr(self, 'write_position{}'.format(i)),
                                                    read_func=getattr(self, 'read_position{}'.format(i))
                                                    )
            self.settings.get_lq('servo{}_type'.format(i)).add_listener(
                    lambda servo_number=i: self.update_min_max(servo_number)
                    )
            self.settings.get_lq('servo{}_toggle'.format(i)).add_listener(
                    lambda servo_number=i: self.toggle_servo(servo_number)
                    )
            
        self.settings.get_lq('flip_mirror').connect_to_hardware(
            write_func= self.write_position5,
            read_func = self.read_position5)
                    
        self.settings.get_lq('port').add_listener(self.update_new_port)
        
        self.read_from_hardware()
        
    def disconnect(self):
        if self.debug_mode:
            print('disconnecting Pololu')
            
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
            
        #self.dev.close() #deletes serial connection object
        
    def update_flip_mirror(self, up):
        if up:
            self.dev.write_position(self.flip_mirror_chan, 1600)
        else:
            self.dev.write_position(self.flip_mirror_chan, 100)
     
    def update_new_port(self):
        """
        Upon update of LQ specified port, reinstantiates the device class.
        """
        del self.dev
        self.dev = PololuMaestroDevice(port=self.settings['port'])
        print('port updated:', self.settings['port'])
 
    
    def update_min_max(self, servo_number):
        """
        Reads the servo type from the logged quantity, updates servo specific software limits.
        """
        servo_type = self.settings['servo{}_type'.format(servo_number)]
        vmin, vmax = self.servo_type_limit[servo_type]
        self.settings.get_lq("servo{}_position".format(servo_number)).change_min_max(vmin,vmax)

    def toggle_servo(self, servo_number):
        servo_type = self.settings['servo{}_type'.format(servo_number)]
        value = self.settings['servo{}_toggle'.format(servo_number)]
        off, on = self.settings['servo{}_toggle_off'.format(servo_number)],self.settings['servo{}_toggle_on'.format(servo_number)]
        if value:
            self.dev.write_position(servo_number, on)
        else:
            self.dev.write_position(servo_number, off)
        self.read_from_hardware()
    
    
    def write_position0(self, position):
        self.dev.write_position(0, target=position)
    def write_position1(self, position):
        self.dev.write_position(1, target=position)
    def write_position2(self, position):
        self.dev.write_position(2, target=position)
    def write_position3(self, position):
        self.dev.write_position(3, target=position)
    def write_position4(self, position):
        self.dev.write_position(4, target=position)
    def write_position5(self, position):
        self.dev.write_position(5, target=position)
    
    
        
    def read_position0(self):
        return self.dev.read_position(0)/4
    def read_position1(self):
        return self.dev.read_position(1)/4
    def read_position2(self):
        return self.dev.read_position(2)/4
    def read_position3(self):
        return self.dev.read_position(3)/4
    def read_position4(self):
        return self.dev.read_position(4)/4
    def read_position5(self):
        return self.dev.read_position(5)/4