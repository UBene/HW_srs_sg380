from typing import List

import numpy as np


class PulseBlasterChannel:
    """
    flags: 	here, an int that represents the selected channel to be on (see also Flags in typing file)
    length: the duration the channel is high after star_time
    """

    __slots__ = ["flags", "start_times", "pulse_lengths"]

    def __init__(
        self, flags: int, start_times: List[int], pulse_lengths: List[int]
    ):
        self.flags = flags
        self.start_times = start_times
        self.pulse_lengths = pulse_lengths

    def __str__(self):
        return f"""Channel Nummer: {int(np.log2(self.flags))} 
					flags: {self.flags:024b} 
					#Pulses: {len(self.pulse_lengths)}"""


def new_pulse_blaster_channel(flags: int, start_times: List[float], pulse_lengths: List[float], clock_period: int = 2) -> PulseBlasterChannel:
    '''
    flags: 	here, an int that represents the selected channel to be on (see also Flags in typing file)
    start_times: in ns 
    pulse_lengths: in ns 
    clock_period: period of the pulse blaster clock in ns
    '''
    return PulseBlasterChannel(
        flags,
        [clock_period * round(x / clock_period) for x in start_times],
        [clock_period * round(x / clock_period) for x in pulse_lengths],
    )
