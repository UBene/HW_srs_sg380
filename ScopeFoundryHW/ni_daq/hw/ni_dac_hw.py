from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.ni_daq.devices.NI_Daq import NI_DacTask

class NI_DAC_HW(HardwareComponent):
    
    def __init__(self, app, name='ni_dac', debug=False):
        self.name = name
        HardwareComponent.__init__(self, app, debug=debug)
    
    def setup(self):
        self.settings.New('dac_val', dtype=float, ro=False,  unit='V')
        self.settings.New('channel', dtype=str, initial='/Dev1/ao0')
        
    def connect(self):
        S = self.settings
        
        # Open connection to hardware
        self.dac_task = NI_DacTask(channel=S['channel'],
                                   name=self.name)
        
        self.dac_task.set_single()
        self.dac_task.start()
        
        #TODO disable channel and terminal_config 
        
        #connect settings to hardware
        self.settings.dac_val.connect_to_hardware(
                                write_func=self.dac_task.set)
        
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()

        #TODO reenable channel and terminal_config 
        
        if hasattr(self, 'dac_task'):
            self.dac_task.close()
            del self.dac_task