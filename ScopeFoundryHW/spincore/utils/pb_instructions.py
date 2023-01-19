from functools import reduce
from typing import List, Tuple

import numpy as np

from .pb_typing import PBInstructions
from .printing import print_pb_insts
from .pulse_blaster_channel import PulseBlasterChannel
from .short_pulse_feature import has_short_pulses, short_pulse_feature
from .spinapi import Inst


def create_pb_insts(
    channels: List[PulseBlasterChannel],
    all_off_padding_ns: int = 0,
    continuous=True,
    branch_to: int = 0,
    clock_period_ns: int = 2,
    short_pulse_bit_num: int = 21,
) -> PBInstructions:
    """
    Convinience function to create instructions for a pulse program from
    a list of PulseBlasterChannel.
    *all_off_padding_ns* adds time to end of the pulse program for which all channels are low.
    if *continuous* is True, the last instruction is changed such that the program 'branches'
        to the instruction with number *branch_to*. (pb_insts are zero-indexed)
    *clock_period_ns* is hardware specific
    *short_pulse_bit_num* is hardware specific: first bit in flags used for the short pulse
    feature.
    """
    pb_insts = _create_pb_insts(
        *_create_insts_lengths(channels, all_off_padding_ns))
    if pb_insts:
        if continuous:
            pb_insts = _make_continueous(pb_insts, branch_to)
        if has_short_pulses(pb_insts, clock_period_ns):
            print(
                "WARNING, applied short_pulse_feature. This might affects pulse program duration."
            )
            pb_insts = short_pulse_feature(
                pb_insts, clock_period_ns, short_pulse_bit_num)
    return pb_insts


def _create_insts_lengths(
    channels: List[PulseBlasterChannel], all_off_padding_ns: int = 0
) -> Tuple[np.ndarray, np.ndarray]:
    # this function is subtle see docs/_create_insts_lengths_explained.pdf
    # To ensure the first instruction length is counted from t=0 we add a zero.
    # Also, 0^flags = flags, so we can add a zero to swiych without effect
    # and maintaining the correct shape for sorting.
    unsorted_times = [0.0]
    unsorted_switch_flags = [0]
    for c in channels:
        for start_time, pulse_length in zip(c.start_times, c.pulse_lengths):
            unsorted_times.append(start_time)
            unsorted_switch_flags.append(c.flags)
            unsorted_times.append(start_time + pulse_length)
            unsorted_switch_flags.append(c.flags)

    # sort event w.r.t. times, ie. put them in chronological order
    unsorted_times = np.array(unsorted_times)
    indices = np.argsort(unsorted_times)
    switch_flags = np.array(unsorted_switch_flags)[indices]
    # the last switch_flags is used to switch off a final pulse
    # it can be dropped for programs with no additional padding at the end
    inst_length = np.ones_like(switch_flags) * all_off_padding_ns
    inst_length[:-1] = np.diff(unsorted_times[indices])
    return inst_length, switch_flags


def _create_pb_insts(
    inst_legnths: np.ndarray, switch_flags: np.ndarray
) -> PBInstructions:
    # If e.g. two channels turn high at same time, we would
    # have created two instructions where the former has inst_length=0.
    # Zero instructions length are not registered, but are rather
    # composed with subcessor instruction.
    pb_insts = []
    new_flags = 0  # initialize: all channels are low
    for inst_length, u_flags in zip(inst_legnths, switch_flags):
        new_flags = new_flags ^ u_flags
        if inst_length == 0:
            # we will not move in time and hence we do not register a flags
            # in the final pb instruction list.
            continue
        pb_insts.append((new_flags, Inst.CONTINUE, 0, inst_length))
    return pb_insts


def _make_continueous(pb_insts: PBInstructions, branch_to: int = 0) -> PBInstructions:
    """
    change the last instruction to 'branch'
    to the instruction with number *branch_to*.
    (pb_insts are zero-indexed)
    """
    n = pb_insts.pop(-1)
    pb_insts.append((n[0], Inst.BRANCH, int(branch_to), n[3]))
    return pb_insts


def calc_pulse_program_duration(pb_insts: PBInstructions):
    return int(np.sum(np.array(pb_insts)[:, -1]))


def extract_channels_used(pb_insts: PBInstructions, short_pulse_bit_num: int = 21) -> List[int]:
    used_flags = reduce(lambda x, y: x | y, [x[0] for x in pb_insts])
    channels_used = [cn for cn in range(
        short_pulse_bit_num) if used_flags & (1 << cn)]
    return channels_used
