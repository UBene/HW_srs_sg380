'''
@author: Edward Barnard and Benedikt Ursprung
'''

from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.pololu_servo.pololu_interface import PololuMaestroDevice

class PololuMaestroHW(HardwareComponent):
    
    name = 'pololu_maestro'
    
    def __init__(self, app, debug=False, name=None, servo_names=None):
        self.servo_names = servo_names
        if not self.servo_names:
            self.servo_names = [(i, "ch{}".format(i)) for i in range(6)]
        HardwareComponent.__init__(self, app, debug=debug, name=name)
    
    def setup(self):        
        S = self.settings
        
        S.New(name='port', initial='COM1', dtype=str, ro=False)

        for servo_num, name in self.servo_names:
            raw = S.New(name + "_raw", dtype=int,  ro=False) # raw value of servo position output (in units of 1/4 us for PWM pulses)
            raw_min = S.New(name + '_raw_min', dtype=float, initial=2000, ro=False)
            raw_max = S.New(name + '_raw_max', dtype=float, initial=10000, ro=False)
            pos_scale = S.New(name + '_pos_scale', dtype=float, initial=280, ro=False)
            pos = S.New(name + '_position', dtype=float, ro=False)
        
            def pos_rev_func(new_pos, old_vals):
                raw, rmin, rmax, scale = old_vals
                new_raw = rmin + new_pos/scale*(rmax-rmin)
                return (new_raw, rmin, rmax, scale)
    
            pos.connect_lq_math( (raw, raw_min, raw_max, pos_scale),
                                        func=lambda raw, rmin, rmax, scale: scale*( (raw - rmin)/(rmax-rmin) ),
                                        reverse_func= pos_rev_func)
        
            S.New(name+'_jog_step', dtype=float, initial=10.0)
        
            self.add_operation(name + " Jog +", lambda n=name: self.jog_fwd(n))
            self.add_operation(name + " Jog -", lambda n=name: self.jog_bkwd(n))

    
    def connect(self):
        self.dev = PololuMaestroDevice(port=self.settings['port'])

        for servo_num, name in self.servo_names:

            raw = self.settings.get_lq(name+"_raw")
            raw.connect_to_hardware(
                read_func=lambda n=servo_num: self.dev.read_position(n),
                write_func=lambda pos, n=servo_num: self.dev.write_position(n,pos)
                )
        
            raw.read_from_hardware()
        
    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev
    
    def jog_fwd(self, servo_name):
        S = self.settings
        S[servo_name+'_position'] += S[servo_name + '_jog_step']
    
    def jog_bkwd(self, servo_name):
        S = self.settings
        S[servo_name+'_position'] -= S[servo_name + '_jog_step']


class PololuMaestroBaseServoHW(HardwareComponent):
    '''
    communicates to a pololu via a multi_servo_hw.PololuMaestroHW instantiation
    with name as specified with `pololu_maestro_hw_name`.
    '''
    name = 'pololu_maestro_base_servo'
    
    def __init__(self, app, debug=False, name=None, channel=0, pololu_maestro_hw_name='pololu_maestro'):
        self.channel = channel
        self.pololu_maestro_hw_name = pololu_maestro_hw_name
        if name is not None:
            self.name = name
        HardwareComponent.__init__(self, app, debug=debug, name=self.name)
            
            
    def setup(self, initials=[2000, 1000, 180, 10]):
                    #initials = [raw_min, raw_max, scale, jog_step]
        S = self.settings
        self.raw = S.New("raw", dtype=int,  ro=False) # raw value of servo position output (in units of 1/4 us for PWM pulses)
        self.raw_min = S.New('raw_min', dtype=float, initial=initials[0], ro=False)
        self.raw_max = S.New('raw_max', dtype=float, initial=initials[1], ro=False)
        self.pos_scale = S.New('pos_scale', dtype=float, initial=initials[2], ro=False)
        self.position = S.New('position', dtype=float, ro=False)
        self.jog_step = S.New('jog_step', dtype=float, initial=initials[3])
                
        self.add_operation("Jog +", self.jog_fwd)
        self.add_operation("Jog -", self.jog_bkwd)

        
    def connect(self):
        self.multi_servo_hw = self.app.hardware[self.pololu_maestro_hw_name]
        self.multi_servo_hw.settings.connected.connect_to_lq(self.settings.connected)
        for _lq_name in ['raw', 'raw_min', 'raw_max', 'pos_scale', 'position', 'jog_step']:
            print(getattr(self.settings, _lq_name))
            getattr(self.settings, _lq_name).connect_to_lq(self.get_pololu_maestro_hw_lq(_lq_name))
        if not self.settings['connected']:
            self.settings['connected'] = True
        self.post_connect()


    def disconnect(self):
        if self.settings['connected']:
            self.settings['connected'] = False
            
            
    def jog_fwd(self):
        self.multi_servo_hw.jog_fwd('ch{}'.format(self.channel)) 

    
    def jog_bkwd(self):
        self.multi_servo_hw.jog_bkwd('ch{}'.format(self.channel))


    def get_pololu_maestro_hw_lq(self, _multi_servo_lq_name):
        '''
        convience function: 
        Note: `ch{self.channel}_` is prefixed to _multi_servo_lq_name
        '''
        path = 'hardware/{}/ch{}_{}'.format(self.pololu_maestro_hw_name, self.channel, _multi_servo_lq_name)
        return self.app.lq_path(path)


    def post_connect(self):
        '''
        override me to connect to settings
        '''
        pass
    
    

class PololuMaestroWheelServoHW(PololuMaestroBaseServoHW):
    '''
    communicates to a pololu via a multi_servo_hw.PololuMaestroHW instantiation
    with name as specified with `pololu_maestro_hw_name`.
    '''
    name = 'pololu_maestro_wheel' 

            

class PololuMaestroShutterServoHW(PololuMaestroBaseServoHW):
    '''
    communicates to a pololu via a multi_servo_hw.PololuMaestroHW instantiation
    with name as specified with `pololu_maestro_hw_name`.
    '''
    name = 'polulo_maestro_shutter'
    
    def setup(self):
        PololuMaestroBaseServoHW.setup(self, initials=[2000, 10000, 100, 10])
        self.open = self.settings.New('open', bool, initial=False)
        self.open_position = self.settings.New('open_position', int, initial=0)
        self.closed_position = self.settings.New('closed_position', int, initial=100)
        self.open.add_listener(self.on_open_change)
        
    def on_open_change(self):
        S = self.settings
        if S['open']:
            S['position'] = S['open_position']
        else:
            S['position'] = S['closed_position']
            
