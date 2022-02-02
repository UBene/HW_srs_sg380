'''
Created on Jun 21, 2017

@author: Alan Buckley
'''
from __future__ import division, absolute_import, print_function
from ScopeFoundry import HardwareComponent

import logging

logger = logging.getLogger(__name__)

try: 
    from ScopeFoundryHW.button_board_arduino.button_board_interface import ButtonBoardInterface
except Exception as err:
    logger.error("Cannot load required modules for ButtonBoardInterface, {}".format(err))

class ButtonBoardHW(HardwareComponent):
    
    name = 'button_board_hw'
    
    def setup(self):
        self.port = self.settings.New(name="port", initial="COM4", dtype=str, ro=False)
        
        self.chan1 = self.settings.New(name="Channel_1", initial=False, dtype=bool, ro=False)
        self.chan2 = self.settings.New(name="Channel_2", initial=False, dtype=bool, ro=False)
        self.chan3 = self.settings.New(name="Channel_3", initial=False, dtype=bool, ro=False)
        self.chan4 = self.settings.New(name="Channel_4", initial=False, dtype=bool, ro=False)
        
        for i in range(4):
            self.settings.New(name="inst_name{}".format(i+1), initial="Instrument{}".format(i+1), dtype=str, ro=False)

    
    def connect(self):
        self.button_interface = ButtonBoardInterface(port=self.port.val, 
                                                     debug=self.settings['debug_mode'])
        
        self.update_chan_lq()
        
        for i in range(4):
            def f(x, n=i):
                if self.settings.get_lq("inst_name{}".format(n+1)).val == "":
                    self.button_interface.line_blackout(n+1)
                else: 
                    self.button_interface.write_instrument_name(n+1, x)
                    
            self.settings.get_lq("inst_name{}".format(i+1)).connect_to_hardware(
                                                write_func = f)
            self.settings.get_lq("inst_name{}".format(i+1)).write_to_hardware()

        self.chan1.connect_to_hardware(
            write_func = self.write_button1)
        self.chan2.connect_to_hardware(
            write_func = self.write_button2)
        self.chan3.connect_to_hardware(
            write_func = self.write_button3)
        self.chan4.connect_to_hardware(
            write_func = self.write_button4)
        

    def update_chan_lq(self):
        self.settings['Channel_1'] = self.button_interface.button_poll[0]
        self.settings['Channel_2'] = self.button_interface.button_poll[1]
        self.settings['Channel_3'] = self.button_interface.button_poll[2]
        self.settings['Channel_4'] = self.button_interface.button_poll[3]
    
    def update_default_chan_names(self):
        for i in range(4):
            def f(x, n=i):
                self.button_interface.write_instrument_name(n, x)
            self.settings.get_lq("inst_name{}".format(i+1)).connect_to_hardware(f)
        
    def button_listen(self):
        data = self.button_interface.listen()
        if data: 
            button_state = self.settings['Channel_{}'.format(data)]
            print("data:", data)
            print("button_state:", button_state)
            self.settings['Channel_{}'.format(data)] = not button_state
            print("not button_state:", not button_state)
        
    def write_button1(self, value):
        self.button_interface.write_state(1, value)
    
    def write_button2(self, value):
        self.button_interface.write_state(2, value)
    
    def write_button3(self, value):
        self.button_interface.write_state(3, value)
    
    def write_button4(self, value):
        self.button_interface.write_state(4, value)
         
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        self.button_interface.full_button_blackout()
        self.button_interface.full_screen_blackout()
        if hasattr(self, 'button_interface'):
            self.button_interface.close()
            del self.button_interface
        

