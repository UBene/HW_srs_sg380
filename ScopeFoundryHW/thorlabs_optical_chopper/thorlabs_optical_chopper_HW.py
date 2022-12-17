'''
Created on Sep 18, 2014

@author: Benedikt Ursprung
'''

from thorlabs_optical_chopper import ThorlabsOpticalChopper

from ScopeFoundry import HardwareComponent


class ThorlabsOpticalChopperHW(HardwareComponent):
    
    name = 'thorlabs_optical_chopper'
    
    def setup(self):
        S = self.settings
        S.New('port', str, initial='COM4')
        S.New('chopp_frequency', int, unit='Hz', ro=False, si=True)
        S.New('spinning', bool, unit='Hz', ro=False)        
        S.New('blade', int, initial=2)
        
        
    def connect(self):
        if hasattr(self, 'dev'):
            self.disconnect()
        S = self.settings        
        dev = self.dev = ThorlabsOpticalChopper(S['port'],S['debug_mode'])    
        S.chopp_frequency.connect_to_hardware(dev.read_freq, dev.write_freq)
        S.spinning.connect_to_hardware(dev.read_enable, dev.write_enable)
        S.blade.connect_to_hardware(dev.read_blade, dev.write_blade)

    def disconnect(self):
        
        if not hasattr(self, 'dev'):

            # disconnect hardware
            self.dev.close()
            
            # clean up hardware object
            del self.dev
            
            print('disconnected ', self.name)
