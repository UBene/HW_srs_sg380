"""
Created on Mar 21, 2022

@author: bened
"""
from ScopeFoundry.hardware import HardwareComponent

# Note: this is not
from .spinapi import (
    pb_core_clock,
    pb_set_debug,
    pb_init,
    pb_get_error,
    pb_close,
    pb_inst_pbonly, pb_start_programming, PULSE_PROGRAM, pb_stop_programming,
    pb_start, Inst, pb_get_version
)


class PulseBlasterHW(HardwareComponent):

    name = "pulse_blaster"

    def __init__(self, app, debug=False, name=None,
                 channel_settings: [{}]=None):
        self.channel_settings = channel_settings
        HardwareComponent.__init__(self, app, debug, name)

    def setup(self):
        S = self.settings
        S.New("debug", int, initial=1, choices=(('ON', 1), ('OFF', 0)),
              description='Enable debug log. When enabled, spinapi will generate a file called log.txt, which contains some debugging information')
        S.New("clock_frequency", initial=500, unit="MHz",
              description='inherit to specific board - see manual')
        S.New('last_error', str, ro=True)
        S.New('version', str, ro=True)

        if self.channel_settings is None:
            self.channel_settings = [{'name': f'channel_name_{i}', 'initial':i,
                                      'description': f'physical output channel {i}'} for i in range(24)]

        for channel in self.channel_settings:
            S.New(dtype=int, **channel)

        self.channels_list = [
            k.get('name', f'channel_{i}') for i, k in enumerate(self.channel_settings)]

        self.add_operation('configure', self.configure)
        self.add_operation('write close', self.write_close)

        print(self.channel_settings)

        self.pens = {k.get('name', f'channel_name_{i}'): k.get('colors', ['w'])[
            0] for i, k in enumerate(self.channel_settings)}

    def catch_error(self, status):
        if status == -91:
            print('pulse_blaster not initialize: Connect pulse_blaster')
        if status < 0:
            error = pb_get_error()
            self.settings['last_error'] = error
            print("pulse_blaster last error: ", repr(error), status)
        else:
            self.settings['last_error'] = 'last call ok'

    def connect(self):
        S = self.settings
        S.clock_frequency.connect_to_hardware(write_func=self.write_core_clock)
        S.debug.connect_to_hardware(write_func=self.write_debug)
        S.version.connect_to_hardware(pb_get_version)

        S.debug.write_to_hardware()
        self.write_init()
        S.clock_frequency.write_to_hardware()

    def disconnect(self):
        self.write_close()

    def write_core_clock(self, freq):
        pb_core_clock(freq)  # does not return a status integer

    def write_debug(self, debug):
        pb_set_debug(debug)  # does not return a status integer

    def write_init(self):
        '''Initializes the board. This must be called before any other functions 
        are used which communicate with the board. 
        If you have multiple boards installed in your system, pb_select_board() 
        may be called first to select which board to initialize.'''
        self.catch_error(pb_init())

    def write_pb_inst_pbonly(self, flags, inst, inst_data, length):
        self.catch_error(pb_inst_pbonly(int(flags),  # np.int32 can not be directly converted?
                                        int(inst),
                                        int(inst_data),
                                        float(length)))

    def configure(self):
        self.write_close()
        self.settings.debug.write_to_hardware()
        self.write_init()
        self.settings.clock_frequency.write_to_hardware()

    def write_pulse_program_and_start(self, pb_insts):
        self.configure()
        self.start_programming(PULSE_PROGRAM)
        if self.settings['debug_mode']:
            from .pulse_program_generator import print_pb_insts
            print_pb_insts(pb_insts)
        for pb_inst in pb_insts:
            self.write_pb_inst_pbonly(*pb_inst)
        self.stop_programming()
        self.write_start()
        self.write_close()

    def start_programming(self, target):
        self.catch_error(pb_start_programming(target))

    def stop_programming(self):
        self.catch_error(pb_stop_programming())

    def write_start(self):
        self.catch_error(pb_start())

    def write_close(self):
        '''End communication with the board. This is generally called as the last line in a program. 
        Once this is called, no further communication can take place with the board unless the board 
        is reinitialized with pb_init(). However, any pulse program that is loaded and running at the 
        time of calling this function will continue to run indefinitely.'''
        self.catch_error(pb_close())

    def get_flags(self, channel: str) -> int:
        '''
        flags is an integer representing the output state of the pulse blaster.

        E.g: flags=5 represents that physical channels 0 and 2 are high and the others low 
            as the binary representation of 5 is 000000000000000000000101

        Note:
        - To create the flags to turn on the channels 'A' and 'B' (and all other channels off) use:
            flags_AB = self.get_flags('A') ^ self.get_flags('B')

        - To turn channel 'B' low (w/o changing low)
            flags_A = flags_AB ^ self.get_flags('B')
        '''
        return 2 ** self.settings[channel]

    @property
    def flags_lookup(self):
        return {2 ** self.settings[i]: i for i in self.channels_list}

    @property
    def rev_flags_lookup(self):
        return {2 ** self.settings[i]: i for i in self.channels_list}

    @property
    def channels_lookup(self):
        return {i: self.settings[i] for i in self.channels_list}

    @property
    def rev_channels_lookup(self):
        return {self.settings[i]: i for i in self.channels_list}
