from __future__ import division, absolute_import, print_function
from ScopeFoundry import HardwareComponent
try:
    from .thorlabs_pm100d import ThorlabsPM100D
except Exception as err:
    print("Cannot load required modules for Thorlabs Power meter: {}".format( err))

class ThorlabsPowerMeterHW(HardwareComponent):
    
    name = 'thorlabs_powermeter'
    
    def setup(self):
        
        # Created logged quantities
        self.wavelength = self.add_logged_quantity(
                                                     name = 'wavelength', 
                                                     unit = "nm",
                                                     dtype = int,
                                                     vmin=0,
                                                     vmax=2000, )
        
        self.power = self.add_logged_quantity(name = 'power', dtype=float, unit="W", vmin=-1, vmax = 10, ro=True, si=True)
        self.current = self.add_logged_quantity(name = 'current', dtype=float, unit="A", vmin=-1, vmax = 10, ro=True, si=True)
        
        
        self.power_range = self.settings.New(name = 'power_range', dtype=float, unit="W", vmin=0, vmax=1e3, si=True, spinbox_decimals=6)
        
        self.auto_range = self.add_logged_quantity(name = 'auto_range', dtype=bool, ro=False)
        
        self.zero_state = self.add_logged_quantity(name = "zero_state", dtype=bool, ro=True)
        self.zero_magnitude = self.add_logged_quantity(name = "zero_magnitude", dtype=float, ro=True, si=True)
        
        self.photodiode_response = self.add_logged_quantity(name = "photodiode_response", dtype=float, unit="A/W", si=True)
        
        self.current_range = self.add_logged_quantity(name = "current_range", dtype=float, unit="A", si=True)
        
        self.port = self.add_logged_quantity('port', dtype=str, initial='USB0::0x1313::0x8078::P0005750::INSTR')
                      
        self.settings.New('average_count', int, initial=1, vmax=3000, 
                          description="""number of power acquisitions the power-meter controller averages over. 
                                        Each acquisition takes approximately 3ms.""")
        
        #operations
        self.add_operation("run_zero", self.run_zero)
        
        self.auto_thread_lock = False
        
    def connect(self):
        if self.debug_mode.val: self.log.debug( "connecting to" +  self.name)
        
        # Open connection to hardware         
        from .thorlabs_pm100d import ThorlabsPM100D               
        self.power_meter = ThorlabsPM100D(debug=self.settings['debug_mode'], port=self.settings['port'])
        
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
        
        self.settings.average_count.connect_to_hardware(
            self.power_meter.get_average_count,
            self.power_meter.set_average_count,
            )
        
        self.read_from_hardware()

    def disconnect(self):
        #disconnect logged quantities from hardware
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'power_meter'):
            #disconnect hardware
            self.power_meter.close()
            
            # clean up hardware object
            del self.power_meter

    def run_zero(self):
        self.power_meter.run_zero()