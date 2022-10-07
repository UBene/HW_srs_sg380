import matplotlib.pylab as plt
import numpy as np

from .pb_typing import PBInstructions
from .plotting import make_plot_lines, make_test_pb_insts, matplotlib_plot
from .printing import print_flags, print_pb_insts


def has_short_pulses(pb_insts: PBInstructions, minimum_inst_length=10):
    '''checks if any instruction length is lower than the minimum instruction length'''
    return np.any(np.array(pb_insts)[:, -1] <= minimum_inst_length)


def short_pulse_feature(pb_insts: PBInstructions, clock_period: int = 2, short_pulse_bit_num=21) -> PBInstructions:
    '''
    Note that the pulse blaster can only process an instruction every 5 clock_period and hence
        min_inst_length = 5*clock_period
    However, the pb can output pulses with duration that are any multiple of the clock_period (subjected to caviats)
    This function replaces instructions with a instruction that:
        - has inst_length = 5*clock_period
        - flags contain the short pulse featture: 
            Channels with bit high are high for the orignal instruction length and low
            until 5*clock_period has passed.
            Channels with bit low will be low during the hole 5*clock_period. 

    short_pulse_bit_num is the first that is used to indicate that the flags encodes a short pulse.

    PI Define Bits 21-23 Clock Periods Pulse Length at 500 MHz (ns)

    number of per   bin # time high in ns
    -               000 - Always Low. See note (1).
    ONE_PERIOD      001 1 2
    TWO_PERIOD      010 2 4
    THREE_PERIOD    011 3 6
    FOUR_PERIOD     100 4 8
    FIVE_PERIOD     101 5 10
    ON              111 - No Short Pulse
    (1) For PBESR-PRO-500-PCI (design 17-16), PBESR-PRO-500-USB-RM (design 27-8, and 33-1), PBESR-PRO-500-
    USB-RM-FP (design 33-1), and PBESR-PRO-500-PCIe (design 31-1) when the upper 3 bits are low, there is no
    Short Pulse.
    '''

    min_inst_length = 5*clock_period
    new_insts = []
    for flags, a, b, inst_length in pb_insts:
        if inst_length <= min_inst_length:
            # print_flags(flags)
            # generate a flag with desired property
            flags = int(
                inst_length//clock_period) << short_pulse_bit_num | flags
            # print_flags(flags)
            inst_length = min_inst_length
        new_insts.append((flags, a, b, inst_length))
    return new_insts


def make_test_pb_insts_2() -> PBInstructions:
    return [
        (0b000000000000001000000001, 0, 0, 8),      # 0
        (0b000000000000001000000010, 0, 0, 10),     # 1
        (0b000000000000001000000011, 0, 0, 4),      # 2
        (0b000000000000001000000001, 0, 0, 2),      # 3
        (0b000000000000001000000001, 0, 0, 4),      # 4
        (0b000000000000001000000001, 0, 0, 6),      # 5
        (0b000000000000001000000001, 0, 0, 8),      # 6
        # (0b000000000000000000000000, 0, 0, 10),     # 7
        # (0b000000000000000000100111, 0, 0, 2),      # 8
        # (0b000000000000000001100111, 0, 0, 2),      # 9
        # (0b000000000000000001100101, 0, 0, 2),      # 10
        # (0b000000000000000001100001, 0, 0, 2),      # 11
        # (0b000000000000000001100101, 0, 0, 2),      # 12
        # (0b000000000000000000100101, 0, 0, 2),      # 13
        # (0b000000000000000000100101, 0, 0, 2),      # 14
        # (0b000000000000000000101101, 0, 0, 2),      # 15
    ]


def test_short_pulse_feature():

    print(has_short_pulses(make_test_pb_insts()))

    initial_insts = make_test_pb_insts_2()
    print(has_short_pulses(initial_insts))

    matplotlib_plot(make_plot_lines(initial_insts))
    print_pb_insts(initial_insts)

    final_insts = short_pulse_feature(initial_insts)
    print_pb_insts(final_insts)
    matplotlib_plot(make_plot_lines(final_insts), ax=None)
    plt.show()
