'''
Benedikt Ursprung 2/21/2019
'''


from ScopeFoundry import HardwareComponent
from .chameleon_compact_opo_dev import ChameleonCompactOPO
import time

class ChameleonCompactOPOHW(HardwareComponent):
    
    name = 'chameleon_compact_opo'
    
    def setup(self):
        
        S = self.settings
        self.opo_wavelength = S.New('opo_wavelength', dtype=float, unit='nm')
        self.opo_set_wavelength = S.New('opo_set_wavelength', dtype=float, unit='nm')
        self.opo_power = S.New('opo_power', dtype=float, ro=True, unit='mW')
        self.status = S.New('status', dtype=str)
        self.port =  S.New('port', dtype=str, initial='COM22')
        
        self.shutters = ['pump_in_shutter', 'pump_out_shutter', 'opo_out_shutter', 'bypass_opo']
        for sh in self.shutters:
            S.New(sh, dtype=bool, ro=False)
        
    def connect(self):
        # Open connection to hardware
        self.opo = ChameleonCompactOPO(port=self.port.val, debug=self.debug_mode.val)


        # connect logged quantities
        self.opo_set_wavelength.connect_to_hardware(write_func = self.set_opo_wavelength_and_wait)
        self.opo_wavelength.connect_to_hardware(self.opo.read_opo_wavelength)
        self.opo_power.connect_to_hardware(self.opo.read_opo_power)
        self.status.connect_to_hardware( self.opo.read_status )
        for sh in self.shutters:
            getattr(self.settings, sh).connect_to_hardware(getattr(self.opo, 'read_'+sh), 
                                                            getattr(self.opo, 'write_'+sh) )
                
    def set_opo_wavelength_and_wait(self,wl, time_out = 10):
        self.opo.write_opo_wavelength(wl)
        t0 = time.time()
        time.sleep(0.1)
        while time.time()-t0 < time_out:
            self.satus.read_from_hardware()
            print(self.status.value)
            if self.status.value == 'OK':
                break
            time.sleep(0.1)
            
    def update_spectrum(self):
        return self.opo.read_opo_spectrum()
                
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        if hasattr(self, 'opo'):
            self.opo.close()    
            del self.opo