'''
Created on Jun 27, 2014

@author: Edward Barnard

updated 2022-02-09 Benedikt Ursprung
'''

from ScopeFoundry import HardwareComponent
from .flip_mirror_dev import FlipMirrorArduino

rainbow = '''qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 0, 0, 100), 
                stop:0.166 rgba(255, 255, 0, 100), stop:0.333 rgba(0, 255, 0, 100), stop:0.5 rgba(0, 255, 255, 100), 
                stop:0.666 rgba(0, 0, 255, 100), stop:0.833 rgba(255, 0, 255, 100), stop:1 rgba(255, 0, 0, 100))'''


class FlipMirrorHW(HardwareComponent):
    
    name = 'flip_mirror'
    
    def __init__(self, app, debug=False, name=None,
                 colors=(rainbow, None),
                 choices=(("Spectrometer", False), ("APD", True))):
        if len(choices[0]) == 2:
            self.choices = choices
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
