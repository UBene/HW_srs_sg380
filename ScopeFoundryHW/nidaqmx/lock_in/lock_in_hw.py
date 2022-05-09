'''
Created on April 11, 2022

@author: Benedikt Ursprung
'''
import nidaqmx
from nidaqmx.constants import Edge, AcquisitionType, TimeUnits, \
    ReadRelativeTo, OverwriteMode, VoltageUnits

from ScopeFoundry.hardware import HardwareComponent
from nidaqmx.errors import DaqError


class LockInHW(HardwareComponent):
    '''
    two counters active when corresponding gate is high.

    We are abusing a NIDAQ pulse width measurement, where the 
    pulse width become gate by setting the timebase=1Hz and clock ticks are replaced 
    by the photon counts.
    '''

    name = "lock_in"

    def setup(self):
        S = self.settings

        S.New('dev', str, initial='Dev1')
        S.New(
            "ctr",
            str,
            initial="ctr0",
            description="""counter""",
        )
        S.New(
            "count_terminal",
            str,
            initial="PFI8",
            #description="""terminal to count from.""",
        )
        S.New(
            "analog_input",
            str,
            initial="PFI8",
            description="""analog lock-in signal""",
        )
        S.New(
            "trigger_source",
            str,
            initial="PFI5",
            description="""starts a trigger""",
        )
        # S.New("N", int, initial=1000,
        #      description='number of readouts')
        S.New("sample_rate", float, initial=1_000_000, si=True, unit='Hz')
        S.New('pixel_time', float, initial=0.1, unit='sec', si=True)

        self.add_operation('read data', self.read_data)
        self.add_operation('restart tasks', self.restart)
        self.add_operation('start tasks', self.start_tasks)
        self.add_operation('close tasks', self.close_tasks)

        self.tasks = {'task': None}

    def configure_tasks(self):
        task = nidaqmx.Task()
        self.tasks = {'task': task}
        S = self.settings

        counter = f"{S['dev']}/{S['ctr']}"  # "Dev1/ctr0"
        task.ci_channels.add_ci_count_edges_chan(counter)

        task.ai_channels.add_ai_voltage_chan(S['analog_input'],
                                             #name_to_assign_to_channel, terminal_config,
                                             min_val=-10, max_val=+10,
                                             units=VoltageUnits.VOLTS,
                                             # custom_scale_name
                                             )

        task.triggers.start_trigger.cfg_dig_edge_start_trig(
            S['trigger_source'], trigger_edge=Edge.RISING)

        task.triggers.start_trigger.retriggerable = True

        self.N = N = int(S['pixel_time'] / S['sample_rate'])
        task.timing.cfg_samp_clk_timing(rate=S['sample_rate'],
                                        sample_mode=AcquisitionType.FINITE,
                                        samps_per_chan=N
                                        # samps_per_chan=10*N
                                        )

        task.register_done_event(self.callback)

    def callback(self):
        data = self.tasks['task'].read(self.N, timeout=10)

        print(len(data))

    def connect(self):
        self.configure_tasks()
        self.start_tasks()

    def disconnect(self):
        self.close_tasks()

    def restart(self, N=None):
        self.close_task()
        self.configure_tasks(N)
        return self.start_tasks()

    def _configure_tasks(self, N=None):
        self.tasks = {'sig': None, 'ref': None}

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

            # task.timing.cfg_implicit_timing(sample_mode=AcquisitionType.CONTINUOUS,
            #                                 samps_per_chan=4*N)
            # task.in_stream.offset = 0
            # task.in_stream.relative_to = ReadRelativeTo.MOST_RECENT_SAMPLE
            # task.in_stream.over_write = OverwriteMode.OVERWRITE_UNREAD_SAMPLES

    def _read_from_task(self, task, N=None, timeout=10):
        if N is None:
            N = self.settings['N']
        try:
            counts = task.read(N, timeout)
        except DaqError as excpt:
            print(self.name, type(excpt).__name__, ':\n', excpt)
            counts = [-1] * N
        if self.settings['debug_mode']:
            self.log.debug(f'read {counts[:4]} from {task}')
        return counts

    def read_data(self, N=None, timeout=10):
        data = self.tasks['task'].read(self.N, timeout=10)
        print(data)
        return data
        # return self._read_from_task(self.tasks['task'], N, timeout)

    def start_tasks(self):
        for task in self.tasks.values():
            task.start()
        if self.settings['debug_mode']:
            self.log.debug('tasks started')
            return self.tasks

    def close_tasks(self):
        if hasattr(self, 'tasks'):
            for task in self.tasks.values():
                if task is not None:
                    task.close()
            del self.tasks
