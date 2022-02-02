from ScopeFoundry import HardwareComponent
from .chameleon_laser_dev import ChameleonUltraIILaser

class ChameleonUltraIILaserHW(HardwareComponent):
    
    name = 'chameleon_laser'
    
    def setup(self):
        
        
        self.wavelength = self.add_logged_quantity('wavelength', dtype=float, si=False, unit='nm')
        self.uf_power = self.add_logged_quantity('uf_power', dtype=float, si=False, ro=0, unit='mW')
        self.port = self.add_logged_quantity('port', dtype=str, initial='COM22')
        
    def connect(self):
        
        # Open connection to hardware
        self.port.change_readonly(True)

        self.laser = ChameleonUltraIILaser(port=self.port.val, debug=self.debug_mode.val)

        # connect logged quantities
        self.wavelength.hardware_read_func = self.laser.read_wavelength
        self.wavelength.hardware_set_func = self.laser.write_wavelength
        self.uf_power.hardware_read_func = self.laser.read_uf_power

    def disconnect(self):
        self.port.change_readonly(False)
        
        #disconnect logged quantities from hardware
        self.settings.disconnect_all_from_hardware()

        #disconnect hardware
        if hasattr(self, 'laser'):
            self.laser.close()
    
            # clean up hardware object
            del self.laser

        