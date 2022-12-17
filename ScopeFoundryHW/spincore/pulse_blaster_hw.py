"""
Created on Mar 21, 2022

@author: Benedikt Ursprung
"""
from typing import Dict, List, Union

from ScopeFoundry.hardware import HardwareComponent
from ScopeFoundryHW.spincore.utils.colors import get_colors

from .utils.pb_typing import ChannelNameLU, PBInstructions
from .utils.spinapi import (PULSE_PROGRAM, pb_close, pb_core_clock,
                            pb_get_error, pb_get_version, pb_init,
                            pb_inst_pbonly, pb_set_debug, pb_start,
                            pb_start_programming, pb_stop_programming)

NamedChannelsKwargs = List[Dict]


class PulseBlasterHW(HardwareComponent):

    name = "pulse_blaster"

    def __init__(self, app, debug=False, name=None,
                 named_channels_kwargs: Union[NamedChannelsKwargs,
                                              None] = None,
                 clock_frequency_Hz: int = 500_000_000,
                 short_pulse_bit_num: int = 21
                 ):
        '''
        named_channels_kwargs: [{'name': '<MyName>'}, {'name': '<MyName2>'}]
        clock_frequency_Hz: see manual of your board 
        short_pulse_bit_num: Typically is equal to the number of physical output channels, see manual of the board.
                             Only required for "short pulses".
                             Short pulses are are pulses that are short than the max. instructions length,
                             which is 5*clock_period_ns)
        '''
        self.named_channel_kwargs = named_channels_kwargs
        self._clock_frequency = clock_frequency_Hz
        self._clock_period_ns = int(1e9 / clock_frequency_Hz)
        self.short_pulse_bit_num = short_pulse_bit_num
        HardwareComponent.__init__(self, app, debug, name)

    def setup(self):
        S = self.settings
        S.New("debug", int, initial=1, choices=(('ON', 1), ('OFF', 0)),
              description='''Enable debug log. When enabled, spinapi will generate a file called log.txt, 
                                which contains some debugging information''')
        S.New('last_error', str, ro=True)
        S.New('version', str, ro=True)
        S.New('clock_frequency', int,
              initial=self._clock_frequency, unit='Hz', si=True)

        # if self.named_settings is None:
        #     self.named_settings = [{'name': f'chan_{i}', 'initial': i, 'ro': False,
        #                             'description': f'physical output channel {i}'} for i in range(self.short_pulse_bit_num)]

        self.add_operation('_configure', self._configure)
        self.add_operation('write close', self.write_close)

        self.colors_lu = {f'chan_{i}': c for i, c in enumerate(get_colors())}
        self.named_channels = []
        if not self.named_channel_kwargs:
            return
        for ii, channel in enumerate(self.named_channel_kwargs):
            S.New(dtype=int, **channel)
            self.colors_lu.update({channel['name']: channel['colors'][0]})
            self.named_channels.append(channel['name'])

    @property
    def clock_period_ns(self)-> int:
        return int(1e9 / self.settings['clock_frequency'])

    def connect(self):
        S = self.settings
        S.debug.connect_to_hardware(write_func=self._write_debug)
        S.version.connect_to_hardware(pb_get_version)
        S.debug.write_to_hardware()
        self._write_init()

    def disconnect(self):
        self.write_close()

    def write_pulse_program_and_start(self, pb_insts: PBInstructions):
        self.write_pulse_program(pb_insts)
        self.write_start()
        self.write_close()

    def write_pulse_program(self, pb_insts: PBInstructions):
        self._configure()
        self._start_programming(PULSE_PROGRAM)
        if self.settings['debug_mode']:
            from .utils.printing import print_pb_insts
            print_pb_insts(pb_insts)
        for pb_inst in pb_insts:
            self._write_pb_inst_pbonly(*pb_inst)
        self._stop_programming()

    def write_start(self):
        self._catch_error(pb_start())

    def write_close(self):
        '''End communication with the board. This is generally called as the last line in a program. 
        Once this is called, no further communication can take place with the board unless the board 
        is reinitialized with pb_init(). However, any pulse program that is loaded and running at the 
        time of calling this function will continue to run indefinitely.'''
        self._catch_error(pb_close())

    def get_flags(self, chan_name: str) -> int:
        # Note:
        # - To create the flags to turn on the chan_name 'A' and 'B' (and all other channels off) use:
        #     self.get_flags('A') ^ self.get_flags('B')
        #
        # - from an old_flags with chan_name 'A' on use
        #     old_flags ^ self.get_flags('A')
        #     To turn channel 'A' off again.
        # '''
        return 2 ** self.settings[chan_name]

    def get_channel_number(self, chan_name: str) -> int:
        return self.settings[chan_name]

    @property
    def channel_name_lu(self) -> ChannelNameLU:
        return {self.settings[i]: i for i in self.named_channels}

    # private methods
    def _catch_error(self, status):
        if status == -91:
            print('pulse_blaster not initialize: Connect pulse_blaster')
        if status < 0:
            error = pb_get_error()
            self.settings['last_error'] = error
            print("pulse_blaster last error: ", repr(error), status)
        else:
            self.settings['last_error'] = 'last call ok'

    def _write_core_clock(self, freq_in_MHz):
        pb_core_clock(freq_in_MHz)  # does not return a status integer

    def _write_debug(self, debug):
        pb_set_debug(debug)  # does not return a status integer

    def _write_init(self):
        '''Initializes the board. This must be called before any other functions 
        are used which communicate with the board. 
        If you have multiple boards installed in your system, pb_select_board() 
        may be called first to select which board to initialize.'''
        self._catch_error(pb_init())
        self._write_core_clock(
            freq_in_MHz=self.settings['clock_frequency'] / 1e6)

    def _write_pb_inst_pbonly(self, flags, inst, inst_data, length):
        self._catch_error(pb_inst_pbonly(int(flags),  # np.int32 can not be directly converted?
                                         int(inst),
                                         int(inst_data),
                                         float(length)))

    def _configure(self):
        self.write_close()
        self.settings.debug.write_to_hardware()
        self._write_init()

    def _start_programming(self, target):
        self._catch_error(pb_start_programming(target))

    def _stop_programming(self):
        self._catch_error(pb_stop_programming())
