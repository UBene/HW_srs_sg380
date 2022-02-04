'''
Created on Sep 23, 2014
reworked Feb 04, 2022

@author: Benedikt 
'''
from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.thorlabs_ell6k_dual_position_slider.ell6k_dual_position_slider_dev import ELL6KDualPositionSliderDev



class ELL6KDualPositionSliderHW(HardwareComponent):
    
    name = 'dual_position_slider'
    debug = False
    
    def __init__(self, app, debug=False, name=None, choices=('open', 'closed')):
        assert len(choices) == 2
        self.choices = [(x, i) for i, x in enumerate(choices)]
        HardwareComponent.__init__(self, app, debug, name)
    
    def setup(self):
        self.settings.New('position', dtype=str, choices=self.choices)
        self.settings.New('port', dtype=str, initial='COM11')

    def connect(self):
        S = self.settings
        self.dev = ELL6KDualPositionSliderDev(port=S['port'],
                                 debug=S['debug_mode'])

        S.position.connect_to_hardware(self.dev.read_position,
                                       self.dev.read_position)
        
        self.read_from_hardware()

    def disconnect(self):
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev

