from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.rigol.rigol_DG1000Z_dev import RigolDG1000Z, RIGOL_WAVEFORMS


class RigolDG1000ZHW(HardwareComponent):
    
    name = 'rigol_waveform_generator'
    
    def __init__(self, app, debug=None, name=None, channels=[1]):
        self.channels = channels
        HardwareComponent.__init__(self, app, debug, name)

    def setup(self):
        S = self.settings

        for chan in self.channels:
            S.New(f'waveform_{chan}', str, initial='?', choices=RIGOL_WAVEFORMS)
            S.New(f'applied_waveform_{chan}', str, initial='?', ro=True,
                  description='Query the waveform type as well as the frequency, amplitude, offset and phase')
            S.New(f'output_{chan}', bool, initial=False,
                  description=f'Output channel {chan} is <i>on</i> if checked.', colors=['none', 'yellow'])
            S.New(f'V_DC_{chan}', initial=1.5, unit='V', spinbox_decimals=3)
            S.New(f'pulse_period_{chan}', initial=1e-1, unit='sec', spinbox_decimals=6)
            S.New(f'V_amplitude_{chan}', initial=1, unit='Vpp', spinbox_decimals=3)
            # S.New('V_level_{chan}', initial=1, unit='V', spinbox_decimals=3)  #seems to be equivalent to V_amplitude
            S.New(f'V_offset_{chan}', initial=0, unit='V', spinbox_decimals=3)
            S.New(f'pulse_width_{chan}', initial=1e-3, unit='sec', spinbox_decimals=6)
    
        S.New('port', initial="USB0::0x1AB1::0x0642::DG1ZA204405136::INSTR", dtype=str)
        S.New('error', str, initial='?', ro=True)
    
    def connect(self):
        S = self.settings
        
        self.dev = RigolDG1000Z(port=S['port'], debug=S['debug_mode'])
        print(self.dev.write('*CLS'))
        print(self.dev.ask('*IDN?'))

        for chan in self.channels:
            
            S.get_lq(f'waveform_{chan}').connect_to_hardware(
                lambda: self.dev.read_waveform(chan),
                lambda x:self.dev.write_waveform(chan, x)
                )   
            
            S.get_lq(f'applied_waveform_{chan}').connect_to_hardware(
                lambda: self.dev.read_apply(chan),
                None
                )
            
            S.get_lq(f'output_{chan}').connect_to_hardware(
                lambda: self.dev.read_output_on(chan),
                lambda x:self.dev.write_output_on(chan, x)
                )        
            
            S.get_lq(f'V_DC_{chan}').connect_to_hardware(
                lambda: self.dev.read_volt_DC(chan),
                lambda x:self.dev.write_volt_DC(chan, x)         
                )
            
            S.get_lq(f'pulse_period_{chan}').connect_to_hardware(
                lambda: self.dev.read_pulse_period(chan),
                lambda x:self.dev.write_pulse_period(chan, x)
                )        
            
            S.get_lq(f'V_amplitude_{chan}').connect_to_hardware(
                lambda: self.dev.read_volt_amplitude(chan),
                lambda x:self.dev.write_volt_amplitude(chan, x)
                )
            
            # S.get_lq(f'V_level_{chan}').connect_to_hardware(
            #    lambda: self.dev.read_volt_level(chan),
            #    lambda x:self.dev.write_volt_level(chan, x)
            #    )
            
            S.get_lq(f'V_offset_{chan}').connect_to_hardware(
                lambda: self.dev.read_volt_offset(chan),
                lambda x:self.dev.write_volt_offset(chan, x)
                )

            S.get_lq(f'pulse_width_{chan}').connect_to_hardware(
                lambda: self.dev.read_pulse_width(chan),
                lambda x:self.dev.write_pulse_width(chan, x)
                )
                
        S.error.connect_to_hardware(lambda:self.dev.ask(':SYSTem:ERRor?'))

        self.read_from_hardware()
        
    def disconnect(self):
        pass
        
