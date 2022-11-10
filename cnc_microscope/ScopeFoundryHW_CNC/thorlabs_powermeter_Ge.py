from __future__ import division, absolute_import, print_function
from ScopeFoundry import HardwareComponent
try:
    from ScopeFoundryEquipment.thorlabs_pm100d_Ge import ThorlabsPM100D
except Exception as err:
    print("Cannot load required modules for Thorlabs Power meter: {}".format( err))


class ThorlabsPowerMeterGeHW(HardwareComponent):
    
    def setup(self):
        self.name = 'thorlabs_powermeter_Ge'
        
        # Created logged quantities
        self.wavelength = self.add_logged_quantity(
                                                     name = 'wavelength', 
                                                     unit = "nm",
                                                     dtype = int,
                                                     vmin=0,
                                                     vmax=50000, )
        
        self.power = self.add_logged_quantity(name = 'power', dtype=float, unit="W", vmin=-1, vmax = 10, ro=True, si=True)
        self.current = self.add_logged_quantity(name = 'current', dtype=float, unit="A", vmin=-1, vmax = 10, ro=True, si=True)
        
        
        self.power_range = self.add_logged_quantity(name = 'power_range', dtype=float, unit="W", vmin=0, vmax=1e3, si=True)
        
        self.auto_range = self.add_logged_quantity(name = 'auto_range', dtype=bool, ro=False)
        
        self.zero_state = self.add_logged_quantity(name = "zero_state", dtype=bool, ro=True)
        self.zero_magnitude = self.add_logged_quantity(name = "zero_magnitude", dtype=float, ro=True, si=True)
        
        self.photodiode_response = self.add_logged_quantity(name = "photodiode_response", dtype=float, unit="A/W", si=True)
        
        self.current_range = self.add_logged_quantity(name = "current_range", dtype=float, unit="A", si=True)
        
        self.port = self.add_logged_quantity('port', dtype=str, initial='USB0::0x1313::0x8078::P0017395::INSTR')
        
        # connect GUI
        #if hasattr(self.gui.ui, 'power_meter_wl_doubleSpinBox'):
        #    self.wavelength.connect_bidir_to_widget(self.gui.ui.power_meter_wl_doubleSpinBox)
        #    self.power.connect_bidir_to_widget(self.gui.ui.power_meter_power_label)
        
        #operations
        self.add_operation("run_zero", self.run_zero)
        
    def connect(self):
        if self.debug_mode.val: self.log.debug( "connecting to" +  self.name)
        
        # Open connection to hardware                        
        self.power_meter = ThorlabsPM100D(debug=self.debug_mode.val, port=self.port.val)
        
        #Connect lq
        self.wavelength.hardware_read_func = self.power_meter.get_wavelength
        self.wavelength.hardware_set_func  = self.power_meter.set_wavelength
        
        self.power.hardware_read_func = self.power_meter.measure_power
        
        self.current.hardware_read_func = self.power_meter.measure_current

        self.power_range.hardware_read_func = self.power_meter.get_power_range
        self.power_range.hardware_set_func  = self.power_meter.set_power_range

        self.auto_range.hardware_read_func = self.power_meter.get_auto_range
        self.auto_range.hardware_set_func = self.power_meter.set_auto_range

        self.zero_state.hardware_read_func = self.power_meter.get_zero_state
        self.zero_magnitude.hardware_read_func = self.power_meter.get_zero_magnitude

        self.photodiode_response.hardware_read_func = self.power_meter.get_photodiode_response

        self.current_range.hardware_read_func = self.power_meter.get_current_range
        
        self.read_from_hardware()
        
    def disconnect(self):
        #disconnect logged quantities from hardware
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        
        if hasattr(self, 'power_meter'):
            #disconnect hardware
            self.power_meter.close()
            
            # clean up hardware object
            del self.power_meter

    def run_zero(self):
        self.power_meter.run_zero()
        print ('zeroed')