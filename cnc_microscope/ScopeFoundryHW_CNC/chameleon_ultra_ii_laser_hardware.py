from ScopeFoundry import HardwareComponent
from ScopeFoundryEquipment.chameleon_ultra_ii_laser import ChameleonUltraIILaser
import time

class ChameleonUltraIILaserHW(HardwareComponent):
    
    name = 'ChameleonUltraIILaser'
    
    def setup(self):
        
        
        self.wavelength = self.add_logged_quantity('wavelength', dtype=float, si=False, unit='nm')
        self.uf_power = self.add_logged_quantity('uf_power', dtype=float, si=False, ro=0, unit='mW')
        self.port = self.add_logged_quantity('port', dtype=str, initial='COM7')
        
        self.align_wl = self.add_logged_quantity('align_wl', dtype=int, si=False, unit='nm', ro=False)
        self.align_mode = self.add_logged_quantity('align_mode', dtype=bool, initial=False, ro=False)
        
        self.shutter_stat = self.add_logged_quantity('shutter_stat', dtype=bool, initial=False, ro=False)
        
        self.add_operation("Home Motor", self.home_motor)
        self.motor_home_stat = self.add_logged_quantity('motor_home_stat', dtype=bool, initial=False, ro=False)
        self.stepper_pos = self.add_logged_quantity('stepper_pos', dtype=int, si=False, ro=True)
        
    def connect(self):
        
        # Open connection to hardware
        self.port.change_readonly(True)

        self.laser = ChameleonUltraIILaser(port=self.port.val, debug=self.debug_mode.val)

        # connect logged quantities
        self.wavelength.hardware_read_func = self.laser.read_wavelength
        self.wavelength.hardware_set_func = self.laser.write_wavelength
        self.uf_power.hardware_read_func = self.laser.read_uf_power
        
        self.align_wl.hardware_read_func = self.laser.read_alignment_mode_wavelength
        self.align_wl.hardware_set_func = self.laser.write_alignment_mode_wavelength
        self.align_mode.hardware_read_func = self.laser.read_alignment_mode
        self.align_mode.hardware_set_func = self.laser.write_alignment_mode
        
        self.shutter_stat.hardware_read_func = self.laser.read_shutter
        self.shutter_stat.hardware_set_func = self.laser.write_shutter
        
        self.motor_home_stat.hardware_read_func = self.laser.read_homed
        self.motor_home_stat.hardware_set_func = self.laser.home_motor
        
        self.stepper_pos.hardware_read_func = self.laser.read_stepper_pos
        
        

    def disconnect(self):
        self.port.change_readonly(False)

        #disconnect hardware
        #self.laser.close()
        
        if hasattr(self, 'laser'):
            #disconnect hardware
            self.laser.close()
            
            # clean up hardware object
            del self.laser
        
        #disconnect logged quantities from hardware
        #for lq in self.logged_quantities.values():
        #    lq.hardware_read_func = None
        #    lq.hardware_set_func = None
            
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        
        # clean up hardware object
        # del self.laser
    
    def home_motor(self):
        self.laser.home_motor()
        time.sleep(1)

        