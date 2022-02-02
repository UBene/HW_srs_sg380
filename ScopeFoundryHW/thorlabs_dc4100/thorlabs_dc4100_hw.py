from ScopeFoundry import HardwareComponent
from .thorlabs_dc4100_interface import ThorlabsDC4100
import numpy as np


class ThorlabsDC4100HW(HardwareComponent):
    name = 'thorlabs_dc4100'
    
    def __init__(self, app, debug=False):
        HardwareComponent.__init__(self, app, debug=debug, name=self.name)
    
    def setup(self):
        S = self.settings
        S.New('port', dtype=str, initial='COM3')
        for LED in range(1,5):
            S.New('LED%s' % LED, dtype=bool, ro=True)
            S.New('LED%s wavelength' % LED, dtype=str,
                  initial='n/a', ro=True)
            S.New('LED%s brightness' % LED, dtype=int, vmin=0, vmax=100, unit='%', ro=True)
        
    def connect(self):
        S = self.settings
        self.ctrl = ThorlabsDC4100(port=S['port'], debug=False)
        S.debug_mode.add_listener(self.set_debug_mode)
        self.ctrl.set_multiselection_mode(False)
        self.ctrl.set_operation_mode(1)
        
        for LED in np.nonzero(self.ctrl.LEDS)[0]+1:
            S.get_lq('LED%s' % LED).change_readonly(False)
            S.get_lq('LED%s' % LED).connect_to_hardware(
                read_func=getattr(self, 'get_LED%d_onoff' % LED),
                write_func=getattr(self, 'set_LED%d_onoff' % LED))
            
            wl = self.ctrl.get_LED_wavelength(LED)
            if wl > 0:
                S.get_lq('LED%s wavelength' % LED).update_value('%0.0f nm' % wl)
            else:
                S.get_lq('LED%s wavelength' % LED).update_value('White')
            
            S.get_lq('LED%s brightness' % LED).change_readonly(False)
            S.get_lq('LED%s brightness' % LED).connect_to_hardware(
                read_func=getattr(self,'get_LED%d_brightness' % LED),
                write_func=getattr(self,'set_LED%d_brightness' % LED))
        
        self.read_from_hardware()
        
    def disconnect(self):
        if hasattr(self, 'ctrl'):
            S = self.settings 
            for LED in np.nonzero(self.ctrl.LEDS)[0]+1:
                S.get_lq('LED%s' % LED).disconnect_from_hardware()
                S.get_lq('LED%s' % LED).change_readonly(True)
                S.get_lq('LED%s wavelength' % LED).disconnect_from_hardware()
                S.get_lq('LED%s brightness' % LED).disconnect_from_hardware()
                S.get_lq('LED%s brightness' % LED).change_readonly(True)
                
            self.ctrl.disconnect()
            del self.ctrl
        
    def get_LED1_onoff(self):
        return self.ctrl.get_LED_status(1)
    def set_LED1_onoff(self,val):
        return self.ctrl.set_LED_status(1, val)
    def get_LED1_brightness(self):
        return self.ctrl.get_LED_brightness(1)
    def set_LED1_brightness(self,val):
        self.ctrl.set_LED_brightness(1, val)
            
    def get_LED2_onoff(self):
        return self.ctrl.get_LED_status(2)
    def set_LED2_onoff(self,val):
        return self.ctrl.set_LED_status(2, val)
    def get_LED2_brightness(self):
        return self.ctrl.get_LED_brightness(2)
    def set_LED2_brightness(self,val):
        self.ctrl.set_LED_brightness(2, val)
            
    def get_LED3_onoff(self):
        return self.ctrl.get_LED_status(3)
    def set_LED3_onoff(self,val):
        return self.ctrl.set_LED_status(3, val)
    def get_LED3_brightness(self):
        return self.ctrl.get_LED_brightness(3)
    def set_LED3_brightness(self,val):
        self.ctrl.set_LED_brightness(3, val)
            
    def get_LED4_onoff(self):
            return self.ctrl.get_LED_status(4)
    def set_LED4_onoff(self,val):
        return self.ctrl.set_LED_status(4, val)
    def get_LED4_brightness(self):
        return self.ctrl.get_LED_brightness(4)
    def set_LED4_brightness(self,val):
        self.ctrl.set_LED_brightness(4, val)
            
    def set_debug_mode(self):
        self.ctrl.debug = self.settings.debug_mode.value