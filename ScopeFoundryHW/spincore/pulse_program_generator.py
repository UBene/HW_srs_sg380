import numpy as np
from pyqtgraph.dockarea.Dock import Dock
import pyqtgraph as pg
from qtpy.QtWidgets import QPushButton
from .spinapi import Inst

from ScopeFoundry.measurement import Measurement
from .pulse_blaster_hw import PulseBlasterHW


class PulseBlasterChannel:

    __slots__ = ['flags', 'start_times', 'pulse_lengths']

    def __init__(self,
                 flags: int,
                 start_times: [float],
                 pulse_lengths: [float]):
        self.flags = flags
        self.start_times = start_times
        self.pulse_lengths = pulse_lengths

    def __str__(self):
        return f'''Channel: {int(np.log2(self.flags))} 
					flags: {self.flags:024b} 
					#Pulses: {len(self.pulse_lengths)}'''


# short pulse flags:
ONE_PERIOD = 0x200000


class PulseProgramGenerator:

    name = 'pulse_generator'

    def __init__(self, measurement: Measurement,
                 pulse_blaser_hw_name: str='pulse_blaster'):
        self.hw: PulseBlasterHW = measurement.app.hardware[pulse_blaser_hw_name]
        self.settings = measurement.settings
        self.name = measurement.name
        self.measurement = measurement

        self.non_pg_setting_names = [
            x.name for x in self.settings._logged_quantities.values()]
        #self.settings.New('program_duration', float, unit='us', initial=160.0)
        self.settings.New('sync_out', float, unit='MHz', initial=-10.0,
                          description='to deactivate set negative')
        self.setup_additional_settings()
        self.settings.New('enable_pulse_plot_update', bool, initial=True,
                          description='disable for performance')
        self.pg_settings = [x for x in self.settings._logged_quantities.values(
        ) if not x.name in self.non_pg_setting_names]

    def setup_additional_settings(self) -> None:
        ''' Override this to add settings, e.g:

        self.settings.New('my_fancy_pulse_duration', unit='us', initial=160.0)	

                returns None

        Note: PulseProgramGenerators have by default a 'program_duration' and 'sync_out'
                  setting. You can set a value here

        self.settings['sync_out'] = 3.3333  # in MHz
        self.settings['program_duration'] = 10  # in us
        '''
        ...

    def make_pulse_channels(self) -> [PulseBlasterChannel]:
        ''' Override this!!!
            should return a list of Channels
            Channels can be generated using self.new_channel
        '''
        raise NotImplementedError(
            f'Overide make_pulse_channels() of {self.name} not Implemented')

    def update_pulse_plot(self) -> None:
        if self.settings['enable_pulse_plot_update']:
            plot = self.plot
            plot.clear()
            pulse_plot_arrays = self.get_pulse_plot_arrays()
            for ii, (name, (t, y)) in enumerate(pulse_plot_arrays.items()):
                y = np.array(y) - 2 * ii
                t = np.array(t) / 1e9
                plot.plot(t, y, name=name, pen=self.hw.pens.get(name, 'w'))

    def New_dock_UI(self) -> Dock:
        dock = Dock(name=self.name + ' pulse generator',
                    widget=self.settings.New_UI(exclude=self.non_pg_setting_names, style='form'))

        pb = QPushButton('program and start pulse blaster')
        pb.clicked.connect(self.program_pulse_blaster_and_start)
        dock.addWidget(pb)

        graph_layout = pg.GraphicsLayoutWidget(border=(0, 0, 0))
        dock.addWidget(graph_layout)
        self.plot = graph_layout.addPlot(title='pulse profile')
        self.plot.setLabel('bottom', units='s')
        self.plot.addLegend()

        for lq in self.pg_settings:
            lq.add_listener(self.update_pulse_plot)

        self.update_pulse_plot()
        return dock

    def get_pulse_plot_arrays(self) -> {str: [[float], [float]]}:
        lu = self.hw.rev_flags_lookup
        channels, program_duration = self.get_pb_channels_program_duration()
        pulse_plot_arrays = {}
        for c in channels:
            if c.flags in lu:
                channel_name = lu[c.flags]
                den = 1
            else:
                channel_name = str(int(c.flags / ONE_PERIOD)) + ' period'
                den = ONE_PERIOD
            pulse_plot_arrays[channel_name] = [[0], [0]]
            for start, dt in zip(c.start_times, c.pulse_lengths):
                if start == 0:
                    pulse_plot_arrays[channel_name][0].pop(0)
                    pulse_plot_arrays[channel_name][1].pop(0)
                else:
                    pulse_plot_arrays[channel_name][0] += [start]
                    pulse_plot_arrays[channel_name][1] += [0]

                pulse_plot_arrays[channel_name][0] += [start, start + dt / den]
                pulse_plot_arrays[channel_name][1] += [1, 1]

                if start + dt / den != program_duration:
                    pulse_plot_arrays[channel_name][0] += [start + dt / den]
                    pulse_plot_arrays[channel_name][1] += [0]

        for v in pulse_plot_arrays.values():
            v[0] += [program_duration]
            v[1] += [v[1][-1]]

        self.pulse_plot_arrays = pulse_plot_arrays
        return pulse_plot_arrays

    def save_to_h5(self, h5_meas_group) -> None:
        for k, v in self.pulse_plot_arrays.items():
            h5_meas_group[k] = np.array(v)

    def _new_channel(self,
                     flags: int,
                     start_times: [float],
                     lengths: [float]) -> PulseBlasterChannel:
        t_min = self.t_min
        return PulseBlasterChannel(flags,
                                   [t_min * round(x / t_min)
                                    for x in start_times],
                                   [t_min * round(x / t_min) for x in lengths],
                                   )

    def new_channel(self, channel: str, start_times: [float], lengths: [float]) -> PulseBlasterChannel:
        ''' all times and lengths in ns '''
        flags = self.hw.get_flags(channel)
        return self._new_channel(flags, start_times, lengths)

    def new_one_period_channel(self, multiple: int, start_times: [float], lengths: [float]) -> PulseBlasterChannel:
        return self._new_channel(int(multiple) * ONE_PERIOD, start_times, lengths)

    @property
    def t_min(self) -> float:
        '''in ns'''
        return 1e3 / self.hw.settings['clock_frequency']

    def program_pulse_blaster_and_start(self,
                                        pulse_blaster_hw: PulseBlasterHW=None
                                        ) -> [int, int, int, float]:
        if not pulse_blaster_hw:
            pulse_blaster_hw = self.hw
        pb_insts = continuous_pulse_program_pb_insts(
            *self.get_pb_channels_program_duration())
        # print_pb_insts(pb_insts)
        pulse_blaster_hw.write_pulse_program_and_start(pb_insts)
        self.measurement.log.info('programmed pulse blaster and start')
        return pb_insts

    @property
    def sync_out_period_ns(self):
        return abs(1 / self.settings['sync_out'] * 1e3)

    def get_pb_channels_program_duration(self) -> ([PulseBlasterChannel], float):
        pb_channels = self.make_pulse_channels()
        max_t = 0
        for c in pb_channels:
            for start_time, length in zip(c.start_times, c.pulse_lengths):
                max_t = max(max_t, start_time + length)

        if self.settings['sync_out'] <= 0:
            self.pulse_program_duration = max_t
            return pb_channels, max_t

        # enforce program length to be integer multiple of of 'sync_out' period
        period = self.sync_out_period_ns
        N = int(abs(np.ceil(max_t / period)))
        pulse_program_duration = N * period
        for c in pb_channels:
            for ii, (start_time, length) in enumerate(zip(c.start_times, c.pulse_lengths)):
                if start_time + length == max_t:
                    c.pulse_lengths[ii] = pulse_program_duration - start_time
        sync_out = self.new_channel('sync_out',
                                    np.arange(N) * period,
                                    np.ones(N) * 0.5 * period)  # 50% duty cycle
        pb_channels.extend([sync_out])

        self.pulse_program_duration = pulse_program_duration
        return pb_channels, pulse_program_duration


def pulse_blaster_flags_length_lists(channels: [PulseBlasterChannel], program_duration: float) -> ([int], [float]):
    '''
    Convenience function used to generate a Pulse Blaster PULSE_PROGRAM

    returns ([flags], [length])
            flags: 	flags is an int that contains a the desired output state of the PULSE BLASTER
                            output. In its binary representation, the i-th least significant bit, 
                            tells the i-th channel to turn high or low. 
            length: the duration the state lasts
    '''

    # To ensure the first duration is counted from t=0
    # we add first elements.
    _times = [0]
    _flags_list = [0]

    for c in channels:
        for start_time, length in zip(c.start_times, c.pulse_lengths):
            _times.append(start_time)
            _flags_list.append(c.flags)
            _times.append(start_time + length)
            _flags_list.append(c.flags)
    _times.append(program_duration)

    # sort event w.r.t. times
    _times = np.array(_times)
    indices = np.argsort(_times)
    _flags_list = np.array(_flags_list)[indices[:-1]]

    # duration between events
    _lengths = np.diff(_times[indices])
    # note that some elements in _lengths are zero,
    # e.g. when we turn two channels high at same time

    flags_list = []
    lengths = []
    # current_time = _times[0]
    flags = _flags_list[0]  # initialize: (everything is low)
    for length, update_flags in zip(_lengths, _flags_list):
        if length == 0:
            # we will not move in time and hence
            # we just evaluate the change on the flags
            flags = flags ^ update_flags
        else:
            # register states that last >0
            flags_list.append(flags ^ update_flags)
            flags = flags_list[-1]
            lengths.append(length)

        # current_time += length
        # print(f'{flags:024b}', current_time)

    return flags_list, lengths


def print_flags_lengths(flags_list, lengths) -> None:
    print('{:<24} ns'.format('flags'))
    for flags, length in zip(flags_list, lengths):
        print(f'{flags:024b}', length)


def print_pb_insts(pb_insts) -> None:
    print('{:<7} {:<24} inst ns'.format('', 'flags'))
    for flags, inst, inst_data, length in pb_insts:
        print(f'{flags:>7} {flags:024b} {inst}, {inst_data} {length:0.1f}')


def pulse_program_pb_insts(channels: [PulseBlasterChannel], program_duration: float) -> [int, int, int, float]:
    flags_list, lengths = pulse_blaster_flags_length_lists(
        channels, program_duration)
    pb_insts = []
    for flags, duration in zip(flags_list, lengths):
        pb_insts.append([flags, Inst.CONTINUE, 0, duration])
    return pb_insts


def make_continueous(pb_insts, offset=0) -> [PulseBlasterChannel]:
    # change the last instruction to 'branch' back
    # to the instruction 'offset'. (pb_insts are zero-indexed)
    pb_insts[-1][1] = Inst.BRANCH
    pb_insts[-1][2] = int(offset)
    return pb_insts


def continuous_pulse_program_pb_insts(channels: [PulseBlasterChannel], program_duration) -> [int, int, int, float]:
    return make_continueous(pulse_program_pb_insts(channels, program_duration))
