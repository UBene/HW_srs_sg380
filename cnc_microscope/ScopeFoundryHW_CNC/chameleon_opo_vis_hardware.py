from ScopeFoundry import HardwareComponent
from ScopeFoundryEquipment.chameleon_opo_vis import ChameleonOPOVis
import time

class ChameleonOPOVisHW(HardwareComponent):
    
    name = 'ChameleonOPOVis'
    
    def setup(self):
        
        
        self.OPO_wavelength = self.add_logged_quantity('OPO_wavelength', dtype=float, si=False, unit='nm')
        self.OPO_power = self.add_logged_quantity('OPO_power', dtype=float, si=False, ro=0, unit='mW')
        
        self.pump_wavelength = self.add_logged_quantity('pump_wavelength', dtype=float, si=False, unit='nm')
        #self.pump_power = self.add_logged_quantity('pump_power', dtype=float, si=False, ro=0, unit='mW')
        
        self.bypass_status = self.add_logged_quantity('bypass status', dtype=str)
        self.add_operation("Pump OPO", self.pump_opo_on)
        self.add_operation("Pump bypass", self.pump_opo_off)
        
        self.OPO_out_shutter_status = self.add_logged_quantity('OPO out shutter', dtype=str)
        self.add_operation("Open OPO shutter", self.opo_out_shutter_open)
        self.add_operation("Close OPO shutter", self.opo_out_shutter_close)
        
        self.OPO_SHG_mirror_status = self.add_logged_quantity('OPO SHG mirror', dtype=str)
        self.add_operation("OPO SHG on", self.opo_SHG_on)
        self.add_operation("OPO SHG off", self.opo_SHG_off)
    
        self.pump_out_shutter_status = self.add_logged_quantity('Pump out shutter', dtype=str)
        self.add_operation("Open pump shutter", self.pump_out_shutter_open)
        self.add_operation("Close pump shutter", self.pump_out_shutter_close)
        
        self.pump_SHG_mirror_status = self.add_logged_quantity('Pump SHG mirror', dtype=str)
        self.add_operation("Pump SHG on", self.pump_SHG_on)
        self.add_operation("Pump SHG off", self.pump_SHG_off)
        
        self.OPO_status = self.add_logged_quantity('OPO_status', dtype=str)
        

        self.port = self.add_logged_quantity('port', dtype=str, initial='COM1')
        
        

        
    def connect(self):
        
        # Open connection to hardware
        self.port.change_readonly(True)

        self.opo = ChameleonOPOVis(port=self.port.val, debug=self.debug_mode.val)

        # connect logged quantities
        self.OPO_wavelength.hardware_read_func = self.opo.read_OPO_wavelength
        self.OPO_wavelength.hardware_set_func = self.opo.write_OPO_wavelength
        self.OPO_power.hardware_read_func = self.opo.read_OPO_power
        
        self.pump_wavelength.hardware_read_func = self.opo.read_pump_wavelength
        #self.pump_power.hardware_read_func = self.opo.read_pump_power()
        
        self.bypass_status.hardware_read_func = self.opo.read_bypass_status
        self.OPO_out_shutter_status.hardware_read_func = self.opo.read_OPO_out_shutter
        self.OPO_SHG_mirror_status.hardware_read_func = self.opo.read_OPO_SHG_mirror
        self.pump_out_shutter_status.hardware_read_func = self.opo.read_pump_out_shutter
        self.pump_SHG_mirror_status.hardware_read_func = self.opo.read_pump_SHG_mirror
        
        self.OPO_status.hardware_read_func = self.opo.query_OPO_status

    def disconnect(self):
        self.port.change_readonly(False)

        #disconnect hardware
        if hasattr(self, 'opo'):
            self.opo.close()
            # clean up hardware object
            del self.opo
        
        #disconnect logged quantities from hardware
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        


    
    
    def pump_opo_on(self):
        self.opo.write_bypass_status(bypassOPO=False)
        time.sleep(0.1)    
        
    def pump_opo_off(self):
        self.opo.write_bypass_status(bypassOPO=True)
        time.sleep(0.1)    
        
    def opo_out_shutter_open(self):
        self.opo.write_OPO_out_shutter(OPO_Out=True)
        time.sleep(0.1)    
        
    def opo_out_shutter_close(self):
        self.opo.write_OPO_out_shutter(OPO_Out=False)
        time.sleep(0.1)    
        
    def pump_out_shutter_open(self):
        self.opo.write_pump_out_shutter(Pump_Out=True)
        time.sleep(0.1)    
        
    def pump_out_shutter_close(self):
        self.opo.write_pump_out_shutter(Pump_Out=False)
        time.sleep(0.1)    
    
    def opo_SHG_on(self):
        self.opo.write_OPO_SHG_mirror(OPO_SHG = True)
        time.sleep(0.1)
        
    def opo_SHG_off(self):
        self.opo.write_OPO_SHG_mirror(OPO_SHG = False)
        time.sleep(0.1)
    
    def pump_SHG_on(self):
        self.opo.write_pump_SHG_mirror(Pump_SHG = True)
        time.sleep(0.1)
        
    def pump_SHG_off(self):
        self.opo.write_pump_SHG_mirror(Pump_SHG = False)
        time.sleep(0.1)