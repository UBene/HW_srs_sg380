from ScopeFoundry import HardwareComponent


class ThorlabsPowerMeterHW(HardwareComponent):
    
    name = 'thorlabs_powermeter'
    
    def setup(self):
        S = self.settings
        S.New('wavelength', unit="nm", dtype=int, vmin=0, vmax=2000)
        
        self.power = S.New('power', float, unit="W", ro=True, spinbox_decimals=6)
        S.New('current', float, unit="A", ro=True, spinbox_decimals=6)
        S.New('power_range', float, unit="W", spinbox_decimals=6)
        S.New('auto_range', bool, ro=False)
        S.New("zero_state", bool, ro=True)
        S.New("zero_magnitude", float, ro=True)
        S.New("photodiode_response", float, unit="A/W", ro=True)
        S.New("current_range", float, unit="A", ro=True)
        S.New('port', str, initial='USB0::0x1313::0x8078::P0005750::INSTR')
        S.New('average_count', int, initial=1, vmax=3000,
                          description="""number of power acquisitions the power-meter controller averages over. 
                                        Each acquisition takes approximately 3ms.""")
        
        # operations
        self.add_operation("run_zero", self.run_zero)
        
    def connect(self):
        
        S = self.settings
        if S['debug_mode']: self.log.debug("connecting to" + self.name)
        
        # Open connection to hardware         
        from .thorlabs_pm100d import ThorlabsPM100D               
        self.dev = ThorlabsPM100D(debug=S['debug_mode'], port=S['port'])
        
        if hasattr(self, 'dev'):
            S.wavelength.connect_to_hardware(self.dev.get_wavelength, self.dev.set_wavelength)
            S.power.connect_to_hardware(self.dev.measure_power) 
            S.current.connect_to_hardware(self.dev.measure_current)
            S.power_range.connect_to_hardware(self.dev.get_power_range, self.dev.set_power_range)
            S.auto_range.connect_to_hardware(self.dev.get_auto_range, self.dev.set_auto_range)
            S.zero_state.connect_to_hardware(self.dev.get_zero_state, self.dev.get_zero_magnitude)
            S.photodiode_response.connect_to_hardware(self.dev.get_photodiode_response)
            S.current_range.connect_to_hardware(self.dev.get_current_range)
            S.average_count.connect_to_hardware(self.dev.get_average_count, self.dev.set_average_count)
            self.read_from_hardware()

    def disconnect(self):
        # disconnect logged quantities from hardware
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev

    def run_zero(self):
        self.dev.run_zero()
