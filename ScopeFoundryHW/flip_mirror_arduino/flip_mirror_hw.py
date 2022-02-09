'''
Created on Jun 27, 2014

@author: Edward Barnard

updated Feb 09 2022 Benedikt Ursprung
'''

from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.flip_mirror_arduino.flip_mirror_arduino_interface import FlipMirrorArduino


class FlipMirrorHW(HardwareComponent):
    
    name = 'flip_mirror'
    
    def __init__(self, app, debug=False, name=None, colors=None, choices=None):
        if choices == None:
            self.choices = [("Spectrometer", False),
                            ("APD", True)]
        else:
            self.choices = [(choices[0], False), (choices[1], True)]
        self.colors = colors
        HardwareComponent.__init__(self, app, debug=debug, name=name)
    
    def setup(self):
        self.settings.New('port', dtype=str, initial='COM8')
        self.flip_mirror_position = self.settings.New("mirror_position",
                                                      dtype=bool,
                                                      choices=self.choices,
                                                      colors=self.colors
                                                      )        
        
    def connect(self):
        S = self.settings
        dev = self.dev = FlipMirrorArduino(port=S['port'],
                                             debug=S['debug_mode'])

        S.mirror_position.connect_to_hardware(dev.read_position,
                                dev.write_posititon)
        
    def disconnect(self): 
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.flip_mirror
