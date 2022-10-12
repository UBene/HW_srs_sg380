from typing import List

import numpy as np


class PulseBlasterChannel:
    """
    represents a pb channel
    flags: here, an int that represents the channel in question to be on (see also Flags in typing file).
    start_time: when channel is high.
    pulse_length: the duration the channel is high after start_time.
    """

    __slots__ = ["flags", "start_times", "pulse_lengths"]

    def __init__(
        self, flags: int, start_times: np.ndarray, pulse_lengths: np.ndarray
    ):
        self.flags = flags
        self.start_times = start_times
        self.pulse_lengths = pulse_lengths

    def __str__(self):
        return f"""Channel Nummer: {int(np.log2(self.flags))} \n
        flags: {self.flags:024b} \n
        #Pulses: {len(self.pulse_lengths)}"""


def _round(x: List, res: int) -> np.ndarray:
    return (res * np.round(np.array(x) / res)).astype(int)


def new_pb_channel(chan_num: int, start_times: List[float], pulse_lengths: List[float], clock_period: int = 2) -> PulseBlasterChannel:
    '''
    chan_num: physical channel number of pulse blaster.
    start_times: in ns 
    pulse_lengths: in ns 
    clock_period: period of the pulse blaster clock in ns
    '''
    return PulseBlasterChannel(1 << chan_num, _round(start_times, clock_period), _round(pulse_lengths, clock_period))
