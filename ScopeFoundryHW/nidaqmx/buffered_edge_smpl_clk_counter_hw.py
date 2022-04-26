'''
Created on Mar 31, 2022

@author: Benedikt Ursprung
'''
import nidaqmx
from nidaqmx.constants import Edge, AcquisitionType, TimeUnits, CountDirection

from ScopeFoundry.hardware import HardwareComponent


class BufferedEdgeSmplClkCounterHW(HardwareComponent):

    name = "buffered_edge_smpl_clk_counter"

    def setup(self):
        S = self.settings
        
        S.New('dev', str, initial='Dev1')
        S.New(
            "counter",
            str,
            initial="ctr0",
            description="""Currently only supports default PFI terminal routing. (see manual: PFI8 --> ctr0)""",
        )
        S.New(
            "sample_clock",
            str,
            initial="PFI5",
            description="""pulse-blaster...""",
        )
        # S.New(
        #    "arm_start_trigger",
        #    str,
        #    initial="PFI8",
        #    description="""apd...""",
        # )
        S.New("N", int, initial=1000,
              description='number of readouts before readout.')
        self.add_operation('read counts', self.read_counts)
        self.add_operation('start task', self.start_task)
        self.add_operation('restart task', self.restart)

        self.add_operation('end task', self.end_task)
        
        # self.configure_task()

    def connect(self):
        self.configure_task()
        self.start_task()
        
    def restart(self, N=None):
        self.end_task()
        self.configure_task()
        return self.start_task()
        
    def configure_task(self, N=None):

        S = self.settings
        
        if not N: 
            N = S['N'] 
            
        self.task = task = nidaqmx.Task()
        counter = f"{S['dev']}/{S['counter']}"  # "Dev1/ctr0"
        task.ci_channels.add_ci_count_edges_chan(counter,)
        task.timing.cfg_samp_clk_timing(rate=1e7,
                                        source=S['sample_clock'],
                                        active_edge=Edge.RISING,
                                        sample_mode=AcquisitionType.FINITE,
                                        samps_per_chan=N)
                
    def start_task(self):
        self.task.start()
        if self.settings['debug_mode']:
            print(self.name, 'task started')
        return self.task

    def read_counts(self, N=None, timeout=10):
        if not N: 
            N = self.settings['N'] 
        try:
            
            counts = self.task.read(N, timeout)

        except Exception as excpt:
            print(self.name, type(excpt).__name__, ':', excpt)
            counts = [-1] * N
        if self.settings['debug_mode']:
            print(self.name, 'read_counts counts', (counts))
        print('read_counts', counts)
        return counts
    
    def end_task(self):
        if hasattr(self, 'task'):
            self.task.close()
            del self.task

    def disconnect(self):
        self.end_task()
