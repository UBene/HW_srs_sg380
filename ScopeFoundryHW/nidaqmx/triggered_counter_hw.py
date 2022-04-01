'''
Created on Mar 31, 2022

@author: Benedikt Ursprung
'''
import nidaqmx
from nidaqmx.constants import Edge, AcquisitionType

from ScopeFoundry.hardware import HardwareComponent


class TriggeredCounterHW(HardwareComponent):

    name = "triggered_counter"

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
            "arm_trigger",
            str,
            initial="PFI5",
            description="""PFI that triggers the start of N readouts""",
        )
        S.New(
            "sample_clock",
            str,
            initial="PFI1",
            description="""PFI that triggers a readout""",
        )
        S.New("N", int, initial=1000,
              description='number of readouts before readout.')
        self.add_operation('read counts', self.read_counts)

    def connect(self):
        self.start_task()
        
    def restart(self, N=None):
        self.end_task()
        self.start_task(N)
        
    def start_task(self, N=None):
        
        S = self.settings
        
        if not N: 
            N = S['N'] 
        
        DAQ_APDInput = f"{S['dev']}/{S['counter']}"  # "Dev2/ai1"
        DAQ_SampleClk = S['sample_clock']  # "PFI0"
        DAQ_StartTrig = S['arm_trigger']  # "PFI5"
        
        self.task = readTask = nidaqmx.Task()
        channel = readTask.ci_channels.add_ci_count_edges_chan(DAQ_APDInput, edge=Edge.RISING)
        readTask.timing.cfg_samp_clk_timing(rate=1000,
                                            source=DAQ_SampleClk, active_edge=Edge.RISING,
                                            sample_mode=AcquisitionType.FINITE, samps_per_chan=N)
        arm_trigger = readTask.triggers.arm_start_trigger
        arm_trigger.dig_edge_src = DAQ_StartTrig
        arm_trigger.dig_edge_edge = Edge.RISING

    def read_counts(self, N=None, timeout=10):
        if not N: 
            N = self.settings['N'] 
        try:
            # print(self.channel.ci_count)
            # self.task.stop()
            # self.task.start()
            # time.sleep(1)
            counts = self.task.read(N, timeout)
        except Exception as excpt:
            print(
                self.name,
                "Error: could not read DAQ. Please check your DAQ's connections. Exception details:",
                type(excpt).__name__,
                ".",
                excpt,
            
            )
            counts = [-1] * N
        if self.settings['debug_mode']:
            print(self.name, 'read_counts counts', (counts))
        return counts
    
    def end_task(self):
        if hasattr(self, 'task'):
            self.task.close()
            del self.task

    def disconnect(self):
        self.end_task()
