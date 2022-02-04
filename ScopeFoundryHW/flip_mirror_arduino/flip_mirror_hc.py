'''
Created on Jun 27, 2014

@author: Edward Barnard
'''
from __future__ import division, absolute_import, print_function
from ScopeFoundry import HardwareComponent

try:
    from .flip_mirror_arduino_interface import FlipMirrorArduino
except Exception as err:
    print("Cannot load required modules for FlipMirrorArduino:", err)



class FlipMirrorHW(HardwareComponent):
    
    name = 'flip_mirror'
    
    def __init__(self, app, debug=False, name=None, colors=None):
        self.colors = colors
        HardwareComponent.__init__(self, app, debug=debug, name=name)
        
    
    def setup(self):
        self.settings.New('port', dtype=str, initial='COM8')
        # Create logged quantities        
        self.flip_mirror_position = self.add_logged_quantity("mirror_position", dtype=bool,
                                                                choices = [
                                                                        ("Spectrometer", False),
                                                                        ("APD", True)],
                                                                colors = self.colors
                                                             )
        self.POSITION_SPEC = False
        self.POSITION_APD = True
        
        # connect GUI
        if hasattr(self.gui.ui, 'flip_mirror_checkBox'):
            self.flip_mirror_position.connect_bidir_to_widget(self.gui.ui.flip_mirror_checkBox)
        
    def connect(self):
        if self.settings['debug_mode']: self.log.debug( "connecting to flip mirror arduino")
        
        # Open connection to hardware
        self.flip_mirror = FlipMirrorArduino(port=self.settings['port'], 
                                             debug=self.settings['debug_mode'])

        # connect logged quantities
        self.flip_mirror_position.hardware_read_func = \
                self.flip_mirror.read_position
        self.flip_mirror_position.hardware_set_func = \
                self.flip_mirror.write_posititon
        

        
        
    def disconnect(self):
        
        #disconnect logged quantities from hardware
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'flip_mirror'):
            #disconnect hardware
            self.flip_mirror.close()
            
            # clean up hardware object
            del self.flip_mirror
