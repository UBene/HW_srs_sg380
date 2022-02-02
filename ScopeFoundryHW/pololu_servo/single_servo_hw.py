from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.pololu_servo.pololu_interface import PololuMaestroDevice

class PololuMaestroServoHW(HardwareComponent):
    
    name = 'pololu_maestro_servo'
    
    
    def setup(self):        
        S = self.settings
        
        S.New(name='port', initial='COM1', dtype=str, ro=False)
        S.New(name='servo_num', dtype=int, initial=0, ro=False)
        S.New(name="raw_position", dtype=int,  ro=False)
        
        S.New('raw_min', dtype=float, initial=2000, ro=False)
        S.New('raw_max', dtype=float, initial=10000, ro=False)
        S.New('pos_scale', dtype=float, initial=180, ro=False)
        S.New('position', dtype=float, ro=False)
        
        
        def pos_rev_func(new_pos, old_vals):
            raw, rmin, rmax, scale = old_vals
            new_raw = rmin + new_pos/scale*(rmax-rmin)
            return (new_raw, rmin, rmax, scale)

        S.position.connect_lq_math( (S.raw_position, S.raw_min, S.raw_max, S.pos_scale),
                                    func=lambda raw, rmin, rmax, scale: scale*( (raw - rmin)/(rmax-rmin) ),
                                    reverse_func= pos_rev_func)
        
        
        S.New('jog_step', dtype=float, initial=10.0)
        
        self.add_operation("Jog +", self.jog_fwd)
        self.add_operation("Jog -", self.jog_bkwd)
    
    def connect(self):
        self.dev = PololuMaestroDevice(port=self.settings['port'])

        self.settings.raw_position.connect_to_hardware(
            read_func=lambda: self.dev.read_position(self.settings['servo_num']),
            write_func=lambda pos: self.dev.write_position(self.settings['servo_num'],pos)
            )
        
        self.settings.raw_position.read_from_hardware()
        
    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev
            
    
    def jog_fwd(self):
        S = self.settings
        S['position'] += S['jog_step']
    
    def jog_bkwd(self):
        S = self.settings
        S['position'] -= S['jog_step']
    