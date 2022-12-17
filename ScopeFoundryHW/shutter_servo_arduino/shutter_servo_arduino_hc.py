'''
Created on Oct 27, 2014

@author: Edward Barnard
'''
from __future__ import division, absolute_import, print_function
from ScopeFoundry import HardwareComponent

try:
    from .shutter_servo_arduino_interface import ShutterServoArduino
except Exception as err:
    print("Cannot load required modules for ShutterServoArduino:", err)



class ShutterServoHW(HardwareComponent):
    
    name = 'shutter_servo'
    
    def __init__(self, app, debug=False, name=None, colors=None):
        self.colors = colors
        HardwareComponent.__init__(self, app, debug=debug, name=name)
        
    
    def setup(self):
       
        
        self.port = self.add_logged_quantity('port', dtype=str, initial='COM6', )
        
        # Create logged quantities        
        self.angle = self.add_logged_quantity("angle", dtype=int, vmin=0, vmax=180, unit='deg')

        self.shutter_open = self.settings.New("shutter_open", 
                                              dtype=bool,
                                              choices = [("Open", True),
                                                         ("Closed", False)],
                                              colors = self.colors,
                                              )

        # connect GUI
        #self.shutter_open.connect_bidir_to_widget(self.gui.ui.shutter_open_checkBox)
        
        
    def connect(self):
        if self.debug_mode.val: self.log.debug( "connecting to shutter servo arduino" )
        
        # Open connection to hardware
        self.shutter_servo = ShutterServoArduino(port=self.port.val, debug=self.debug_mode.val, 
                                                 CLOSE_POSITION = 135, OPEN_POSITION=180)

        # connect logged quantities
        self.angle.hardware_read_func = \
                self.shutter_servo.read_position
        self.angle.hardware_set_func = \
                self.shutter_servo.write_position
        

        self.shutter_open.hardware_read_func = \
                self.shutter_servo.read_open
        self.shutter_open.hardware_set_func = \
                self.shutter_servo.move_open
                
        def set_debug(d):
            self.shutter_servo.debug = d
        self.debug_mode.hardware_set_func = set_debug
        
        #connect logged quantities together        
        self.shutter_open.add_listener(self.angle.read_from_hardware)

        
    def disconnect(self):
        
        #disconnect logged quantities from hardware
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'shutter_servo'):
            #disconnect hardware
            self.shutter_servo.close()
            
            # clean up hardware object
            del self.shutter_servo