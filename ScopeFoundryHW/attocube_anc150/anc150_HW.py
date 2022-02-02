'''
Created on Feb 23, 2017

@author: Alan Buckley
Helpful feedback and modifications from Ed Barnard
'''

from __future__ import division, absolute_import, print_function
from ScopeFoundry import HardwareComponent

import logging

logger = logging.getLogger(__name__)


try: 
    from ScopeFoundryHW.attocube_anc150.anc150_interface import ANC_Interface
except Exception as err:
    logger.error("Cannot load required modules for ANC150, {}".format(err))
    

class ANC_HW(HardwareComponent):
    
    name = 'anc150'
    
    def setup(self):
        
        self.port = self.settings.New(name="port", initial="COM6", dtype=str, ro=False)
#         self.settings.New(name='debug_mode', initial=False, dtype=bool, ro=False)
        
        self.settings.New('frequency', dtype=int, array=True,  ro=False, 
                  initial=[20,20,20,20,20,20])
        self.settings.New('voltage', dtype=int, array=True,  ro=False, 
                  initial=[30,30,30,30,30,30])
        self.settings.New('position', dtype=int, array=True,  ro=False, 
                  initial=[0,0,0,0,0,0])#keeps track of moves
        self.settings.New('chan_names', dtype=str, array=True,
                          initial=['pitch', 'y', 'x', 'yaw', 'nc', 'nc'])

        self.settings.New('scale_factor', dtype=int, array=True,
                          initial=[-1.0, -1.0, -1.0, -1.0, 1.0, 1.0])
        
        self.settings.New('ground_all', dtype=bool, initial=False, ro=False)

        self.add_operation(name="zero_position", op_func=self.zero_position)

        
        
    def connect(self): 
        self.anc_interface = ANC_Interface(port=self.port.val, debug=self.settings['debug_mode'])

        self.axis_name_dict = dict()
        for i, name in enumerate(self.settings['chan_names']):
            self.axis_name_dict[name] = i

        self.settings.frequency.connect_to_hardware(
            read_func= self.anc_interface.get_freqs,
            write_func= self.anc_interface.set_freqs
            )
        self.settings.voltage.connect_to_hardware(
            read_func= self.anc_interface.get_volts,
            write_func= self.anc_interface.set_volts,
            )
        self.settings.position.connect_to_hardware(
            read_func = self.anc_interface.get_positions
            )
        
        self.settings.ground_all.connect_to_hardware(
            write_func = self.anc_interface.ground_outputs
            )
        
    
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'anc_interface'):
            self.anc_interface.close()
            del self.anc_interface
    
    def zero_position(self):
        self.anc_interface.zero_positions()
        self.settings.position.read_from_hardware()
        print('position reset:', self.settings['position'])
            
    def move_axis_delta(self, axis_id, delta_steps):
        self.anc_interface.delta_pos(axis_id, delta_steps*self.settings['scale_factor'][axis_id],wait=True)
        self.settings.position.read_from_hardware()

    def move_axis_delta_by_name(self, axis_name, delta_steps):
        axis_id = self.axis_name_dict[axis_name]
        self.move_axis_delta(axis_id, delta_steps)
        
    def get_pos_by_name(self, axis_name):
        axis_id = self.axis_name_dict[axis_name]
        return self.settings['position'][axis_id]*self.settings['scale_factor'][axis_id]
        
        
    #######################
        
    def move_start(self):
        axis = self.settings['axis']
        mode = self.settings['move_mode{}'.format(axis)] 
        if mode == 'c':
            self.write_active_axis_step_continuous()
        elif mode == 'n':
            self.write_active_axis_step_discrete()
    
    def move_stop(self):
        self.write_active_axis_stop()
        
    


    def read_active_axis_mode(self):
        axis = self.settings['axis']
        resp = self.anc_interface.get_axis_mode(axis)
        return resp

    
    def read_active_axis_cap(self):
        axis = self.settings['axis']
        resp = self.anc_interface.get_capacity(axis)
        return resp

    def read_active_axis_freq(self):
        axis = self.settings['axis']
        resp = self.anc_interface.get_frequency(axis)
        return resp
    
    def read_active_axis_voltage(self):
        axis = self.settings['axis']
        resp = self.anc_interface.get_voltage(axis)
        return resp

    def write_active_axis_freq(self, frequency):
        axis = self.settings['axis']
        #frequency = self.settings['frequency{}'.format(axis)] 
        resp = self.anc_interface.set_frequency(axis, frequency)
        return resp
    
    def write_active_axis_voltage(self, voltage):
        axis = self.settings['axis'] 
        #voltage = self.settings['voltage{}'.format(axis)] 
        resp = self.anc_interface.set_voltage(axis, voltage)
        return resp
    
    def write_active_axis_mode(self, axis_mode):
        axis = self.settings['axis'] 
        #axis_mode = self.settings['axis_mode{}'.format(axis)] 
        resp = self.anc_interface.set_axis_mode(axis, axis_mode)
        return resp
    
    def write_active_axis_step_continuous(self):
        axis = self.settings['axis'] 
        dir = self.settings['move_direction{}'.format(axis)] 
        if self.settings['move_mode{}'.format(axis)]  == "c":
            c = self.settings['move_mode'.format(axis) ]

        else:
            logger.debug("Wrong Mode. Choose c")
        resp = self.anc_interface.step(axis, dir, c)
        return resp
    
    def write_active_axis_step_discrete(self):
        axis = self.settings['axis'] 
        dir = self.settings['move_direction{}'.format(axis)] 
        n = self.settings['move_steps{}'.format(axis)] 
        resp = self.anc_interface.step(axis, dir, n)
        return resp

    def write_active_axis_stop(self):
        axis = self.settings['axis'] 
        resp = self.anc_interface.stop(axis)
        return resp
