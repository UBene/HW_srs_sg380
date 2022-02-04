'''
Created on Jul 8, 2021

@author: Benedikt Ursprung
'''
from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.laser_quantum.pmd24 import PMD24
import time


class PMD24HW(HardwareComponent):
    
    name = "laser_quantum"
    
    def setup(self):
        print('setup')
        
        self.settings.New('port', str, initial='COM28')
        self.settings.New('power', float, initial=10, unit='mW',
                          spinbox_decimals=1)
        self.settings.New('target_power', float, initial=10.1, unit='mW',
                          spinbox_decimals=1)
        self.settings.New('status', str, initial='?', ro=True)
        self.settings.New('laser_temperature', float, ro=True, unit='C')
        self.settings.New('PSU_temperature', float, ro=True, unit='C')
        self.add_operation('ON', self.toggle_laser_on)
        self.add_operation('OFF', self.toggle_laser_off)

    def connect(self):
        if self.debug_mode.val: print("connecting to", self.name)
        
        S = self.settings
        self.dev = PMD24(port=S['port'], debug=S['debug_mode'])
        
        S.power.connect_to_hardware(self.dev.read_power)
        S.target_power.connect_to_hardware(None, self.dev.write_power)
        
        S.status.connect_to_hardware(self.dev.read_status)
        S.laser_temperature.connect_to_hardware(self.dev.read_laser_temp)
        S.PSU_temperature.connect_to_hardware(self.dev.read_PSU_temp)
        
        import threading
        self.update_thread_interrupted = False
        self.update_thread = threading.Thread(target=self.update_thread_run)        
        self.update_thread.start()

        # print(self.update_thread)
        self.read_from_hardware()

    def disconnect(self):
        if self.debug_mode.val: print("disconnect " + self.name)
        if hasattr(self, 'update_thread'):
            self.update_thread_interrupted = True
            self.update_thread.join(timeout=0.0)
            del self.update_thread
            
        if hasattr(self, 'dev'):
            self.dev.ser.close()            
            del self.dev
                            
    def toggle_laser_on(self):
        self.dev.write_STPOW(self.settings['target_power'])
        self.settings.status.read_from_hardware()
        self.dev.write_on()
        self.settings.status.read_from_hardware()
        
    def toggle_laser_off(self):
        self.settings.status.read_from_hardware()
        self.dev.write_off()
        self.settings.status.read_from_hardware()

    def update_thread_run(self):
        S = self.settings
        while not self.update_thread_interrupted:
            S.status.read_from_hardware()
            S.power.read_from_hardware()
            S.laser_temperature.read_from_hardware()
            S.PSU_temperature.read_from_hardware()
            # print(self.name, 'update_thread_run', S.status.value,
                  # S.power.value,
                  # S.laser_temperature.value,
                  # S.PSU_temperature.value)
            time.sleep(0.1)
