import numpy as np

from .pb_typing import PBInstructions


def has_short_pulses(pb_insts: PBInstructions, clock_period_ns: int):
    """checks if any instruction length is lower than the minimum instruction length"""
    return np.any(np.array(pb_insts)[:, -1] <= 5 * clock_period_ns)


def short_pulse_feature(
    pb_insts: PBInstructions, clock_period_ns: int = 2, short_pulse_bit_num: int = 21
) -> PBInstructions:
    """
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
    """

    min_inst_length = 5 * clock_period_ns
    new_insts = []
    for ii, (flags, a, b, inst_length) in enumerate(pb_insts):
        # Special case: if current is all low and previous was a short pulse we can combine
        if ii > 0 and flags == 0:
            pflags, pa, pb, plength = new_insts[-1]
            p_orginal_inst_length = (
                pflags >> short_pulse_bit_num) * clock_period_ns
            if p_orginal_inst_length:
                comb_time = inst_length + p_orginal_inst_length
                inst_length = comb_time if comb_time > min_inst_length else min_inst_length
                new_insts[-1] = (pflags, pa, pb, inst_length)
                continue
        if inst_length <= min_inst_length:
            flags = int(inst_length //
                        clock_period_ns) << short_pulse_bit_num | flags
            inst_length = min_inst_length
        new_insts.append((flags, a, b, inst_length))
    return new_insts
