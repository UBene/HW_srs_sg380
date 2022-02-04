'''
Created on Apr 15, 2021

@author: Benedikt Ursprung
'''
from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.solidstate_chiller.UC160_interface import UC160 

class UC160HW(HardwareComponent): 
    
    name = 'UC160_chiller'

    def setup(self):
        S = self.settings
        self.port = S.New('port',  dtype=str, initial='COM21')
        self.setpoint = S.New('setpoint', 
                                 dtype=float, 
                                 initial=10.0, 
                                 unit='C',
                                 spinbox_decimals=1,
                                 spinbox_step=0.1,
                                 vmin=2, vmax=45)
        self.temperature = S.New('temperature', 
                                 dtype=float, 
                                 initial=25.0, 
                                 ro=True,
                                 unit='C',
                                 spinbox_decimals=1)
        self.faults = S.New('faults', 
                            dtype=str,
                            initial='?',
                            ro=True)
        self.add_operation("restart/reset", self.restart)
        
    def connect(self):
        if self.debug_mode.val: print('connecting to', self.name)
        S=self.settings
        dev = self.dev = UC160(port=S['port'], debug=S['port'])
        self.setpoint.connect_to_hardware(dev.read_setpoint, dev.write_setpoint)
        self.temperature.connect_to_hardware(dev.read_temperature)        
        self.faults.connect_to_hardware(dev.read_fault_table)

    def disconnect(self):
        self.dev.close()
        del self.dev
        
    def restart(self):
        self.dev.reset_chiller()
        
          
            