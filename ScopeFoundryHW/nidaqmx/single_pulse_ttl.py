'''
Created on April 11, 2022

@author: Benedikt Ursprung
'''
import nidaqmx
from nidaqmx.constants import Edge, AcquisitionType, VoltageUnits
from nidaqmx.errors import DaqError

from ScopeFoundry.hardware import HardwareComponent



class SinglePulse(HardwareComponent):
    '''
    creates a single pulse
    '''

    name = "single_daq_pulse"

    def setup(self):
        
        S = self.settings
        
        S.New(
            "channel_0",
            str,
            initial="Dev1/ao0",
            description="""physical output channel""",
        )
        S.New('pulse_width', float, unit='s', si=True, initial=100e-3,
              description='sets width of the pulse')
        
        S.New('rate', initial=80e6, unit='Hz', si=True)
        S.New('voltage', initial=4.9, vmax=5, vmin=-5, unit='V')


        self.add_operation('write_voltages', self.write_voltage_program)
        self.add_operation('start', self.start_task)
        

    def connect(self):
        pass
    
    def disconnect(self):
        pass

    def write_voltage_program(self):
        S = self.settings

        
        
        rate = 1/S['pulse_width']
        voltages = [S['voltage'], 0]
        # rate = S['rate']
        # width = S['pulse_width']
        # voltage = S['voltage']
        # N = int(width/rate)        


        self.task = task = nidaqmx.Task()                
        task.ao_channels.add_ao_voltage_chan(S[f'channel_0'],
                                             min_val=-10,
                                             max_val=10,
                                             units=VoltageUnits.VOLTS)
        task.timing.cfg_samp_clk_timing(rate,
                                        source="",
                                        active_edge=Edge.RISING,
                                        sample_mode=AcquisitionType.FINITE,
                                        samps_per_chan=len(voltages))
        task.write(voltages, auto_start=False, timeout=10.0)
        
        if self.debug_mode.val:
            print(self.name, 'wrote', voltages, 'with rate',  rate)
        
    def start_task(self):
        if not hasattr(self, 'task'):
            print(self.name, 'write voltage program first')
            return
            
        if self.debug_mode.val:
            print(self.name, 'start task')
        task = self.task
        task.start()
        task.wait_until_done(timeout=10.0)
        task.close()
