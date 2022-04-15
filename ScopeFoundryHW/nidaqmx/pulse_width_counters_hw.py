'''
Created on April 11, 2022

@author: Benedikt Ursprung
'''
import nidaqmx
from nidaqmx.constants import Edge, AcquisitionType, TimeUnits, \
    ReadRelativeTo, OverwriteMode

from ScopeFoundry.hardware import HardwareComponent


class PulseWidthCounters(HardwareComponent):
    '''
    two counters active when corresponding gate is high.
    
    We are abusing a NIDAQ pulse width measurement, where the 
    pulse width become gate by setting the timebase=1Hz and clock ticks are replaced 
    by the photon counts.
    '''

    name = "pulse_width_counters"

    def setup(self):
        S = self.settings
        
        S.New('dev', str, initial='Dev1')
        S.New(
            "ctr_sig",
            str,
            initial="ctr0",
            description="""Counts while <i>gate_sig</i> is high. 
                            Its physical terminal is the <i>count_terminal</i>""",
        )
        S.New(
            "ctr_ref",
            str,
            initial="ctr1",
            description="""Counts while <i>gate_ref</i> is high. 
                            Its physical terminal is the <i>count_terminal</i>""",
        )
        S.New(
            "count_terminal",
            str,
            initial="PFI8",
            description="""(Timebase) physical terminal on which is being counted 
                            with <i>ctr_sig</i> and <i>ctr_ref</i>""",
        )
        S.New(
            "gate_sig",
            str,
            initial="PFI5",
            description="""(sig Pulsewidth), serves as a gate in this experiment.""",
        )
        S.New(
            "gate_ref",
            str,
            initial="PFI6",
            description="""(ref Pulsewidth), serves as a gate in this experiment.""",
        )        
        S.New("N", int, initial=1000,
              description='number of readouts')
        
        self.add_operation('read sig counts', self.read_sig_counts)
        self.add_operation('read ref counts', self.read_ref_counts)
        self.add_operation('restart tasks', self.restart)
        self.add_operation('start tasks', self.start_tasks)
        self.add_operation('end tasks', self.end_tasks)
        
        self.tasks = {'sig':None, 'ref':None}

    def connect(self):
        self.configure_tasks()
        self.start_tasks()

    def disconnect(self):
        self.end_tasks()
        
    def restart(self, N=None):
        self.end_tasks()
        self.configure_tasks(N)
        return self.start_tasks()
        
    def configure_tasks(self, N=None):
        self.tasks = {'sig':None, 'ref':None}

        S = self.settings
        
        if not N:
            N = S['N'] 
                
        for x in ['sig', 'ref']:
            self.tasks[x] = task = nidaqmx.Task()
            counter = f"{S['dev']}/{S['ctr_'+ x]}"  # "Dev1/ctr0"
            channel = task.ci_channels.add_ci_pulse_width_chan(counter,
                min_val=10,
                max_val=100,
                units=TimeUnits.SECONDS,
                starting_edge=Edge.RISING
                )
            channel.ci_pulse_width_term = S['gate_' + x]
            channel.ci_ctr_timebase_rate = 1
            channel.ci_ctr_timebase_src = S['count_terminal']
            task.timing.cfg_implicit_timing(sample_mode=AcquisitionType.FINITE,
                                            samps_per_chan=N)
            task.in_stream.relative_to = ReadRelativeTo.CURRENT_READ_POSITION
            task.in_stream.offset = 0
            task.in_stream.over_write = OverwriteMode.DO_NOT_OVERWRITE_UNREAD_SAMPLES

    def _read_from_task(self, task, N=None, timeout=10):
        if not N: 
            N = self.settings['N'] 
        try:
            counts = task.read(N, timeout)
        except Exception as excpt:
            print(self.name, type(excpt).__name__, ':\n', excpt)
            counts = [-1] * N
        if self.settings['debug_mode']:
            print(self.name, '_read_from_task', task, counts)
        return counts
    
    def read_sig_counts(self, N=None, timeout=10):
        return self._read_from_task(self.tasks['sig'], N, timeout)

    def read_ref_counts(self, N=None, timeout=10):
        return self._read_from_task(self.tasks['ref'], N, timeout)
                
    def start_tasks(self):
        for task in self.tasks.values():
            task.start()
        if self.settings['debug_mode']:
            print(self.name, 'task started')
        return self.tasks
        
    def end_tasks(self):
        if hasattr(self, 'tasks'):
            for task in self.tasks.values():
                task.close()
            del self.tasks