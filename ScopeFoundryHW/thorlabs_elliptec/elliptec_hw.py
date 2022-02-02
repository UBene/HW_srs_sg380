from ScopeFoundry.hardware import HardwareComponent
from ScopeFoundryHW.thorlabs_elliptec.elliptec_dev import ThorlabsElliptecDevice
import time

class ThorlabsElliptecSingleHW(HardwareComponent):
    
    name = 'elliptec'
    
    def __init__(self, app, debug=False, name=None, named_positions=None):
        """ named_positions is a dictionary of names:positions
        """
        self.named_positions = named_positions
        HardwareComponent.__init__(self, app, debug=debug, name=name)
        
    
    def setup(self):
        self.settings.New('port', dtype=str, initial='COM7')
        self.settings.New('addr', dtype=int, initial=0, vmin=0, vmax=15)
        self.settings.New('position', dtype=float, initial=0, unit='mm', spinbox_decimals=4)
        
        
        self.add_operation('Home', self.home_device)
        
        if self.named_positions is not None:
            self.settings.New('named_position', dtype=str, initial='Other', 
                              choices=('Other',) + tuple(self.named_positions.keys()) )
            
            for name, pos in self.named_positions.items():
                #self.add_operation('Goto '+name, lambda name=name: self.goto_named_position(name))
                self.add_operation('Goto '+name, lambda name=name: self.settings.named_position.update_value(name))
    def connect(self):
        S = self.settings
        self.dev = ThorlabsElliptecDevice(port=S['port'], addr=S['addr'], debug=S['debug_mode'])
        hw_info = self.dev.get_information()
        
        self.settings.position.change_unit(self.dev.get_unit())
        
        self.settings.position.reread_from_hardware_after_write = True
        self.settings.position.connect_to_hardware(
            read_func= self.dev.get_position_mm,
            write_func= self.goto_position
            )
        
        self.settings.position.change_unit(hw_info['unit'])
        
        if 'named_position' in self.settings:
            self.settings.named_position.connect_to_hardware(
                write_func=self.goto_named_position
                )

        self.settings.position.read_from_hardware()

        
    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev
            
    def home_device(self):
        self.dev.home_device()
        self.settings.position.read_from_hardware()
        
    def goto_position(self, pos):
        self.dev.move_absolute_mm(pos)
        if 'named_position' in self.settings:
            self.settings['named_position'] = "Other"
        
    def goto_named_position(self, name):
        if name != 'Other':
            self.dev.move_absolute_mm(self.named_positions[name])
            self.settings.position.read_from_hardware()

class ThorlabsElliptcMultiHW(HardwareComponent):
    
    name = 'elliptec_motors'
    
    def __init__(self, app, debug=False, name=None, motors=[(0, 'zero'), (1,'one')] ):
        self.motors = motors
        HardwareComponent.__init__(self, app, debug=debug, name=name)
        
    def setup(self):
        self.settings.New('port', dtype=str, initial='COM3')

        for addr, name in self.motors:
            self.add_operation('Home '+name, lambda name=name: self.home_device(name) )
            self.settings.New(name + '_position', dtype=float, initial=0, unit='mm', spinbox_decimals=4)


    def connect(self):
        S = self.settings
        self.dev = ThorlabsElliptecDevice(port=S['port'],  debug=S['debug_mode'])

        
        for addr, name in self.motors:
            hw_info = self.dev.get_information(addr)
                
            pos = self.settings.get_lq(name + "_position", )
            pos.change_unit(hw_info['unit'])

            pos.reread_from_hardware_after_write = True
            pos.connect_to_hardware(
                read_func= lambda addr=addr: self.dev.get_position_mm(addr),
                write_func=  lambda x, addr=addr: self.dev.move_absolute_mm(x, addr)
                )
            
            self.dev.get_information(addr)
            pos.read_from_hardware()


    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev
            
    def home_device(self, name):
        for addr, motor_name in self.motors:
            if name == motor_name:
                self.dev.home_device(addr=addr)

    
    def threaded_update(self):
        self.read_from_hardware()
        time.sleep(1.0)