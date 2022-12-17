'''
Created on Sep 23, 2014
reworked Feb 04, 2022

@author: Benedikt 
'''
from ScopeFoundry import HardwareComponent
from .ell6k_dual_position_slider_dev import ELL6KDualPositionSliderDev


class ELL6KDualPositionSliderHW(HardwareComponent):
    
    name = 'dual_position_slider'
    debug = False
    
    def __init__(self, app, debug=False, name=None, choices=(('open', 0), 
                                                             ('closed', 1))):
        assert len(choices) == 2
        if len(choices[0]) == 1:
            self.choices = [(x, i) for i, x in enumerate(choices)]
        else:
            self.choices = choices
        HardwareComponent.__init__(self, app, debug, name)
    
    def setup(self):
        self.settings.New('position', dtype=int, choices=self.choices)
        self.settings.New('port', dtype=str, initial='COM11')

    def connect(self):
        S = self.settings
        self.dev = ELL6KDualPositionSliderDev(port=S['port'],
                                 debug=S['debug_mode'])

        S.position.connect_to_hardware(self.dev.read_position,
                                       self.dev.write_position)
        
        self.read_from_hardware()

    def disconnect(self):
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev

