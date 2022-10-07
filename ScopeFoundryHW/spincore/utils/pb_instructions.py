from typing import List, Tuple

import numpy as np

from .pb_typing import PBInstructions
from .pulse_blaster_channel import PulseBlasterChannel
from .spinapi import Inst


def ordered_inst_lengths_and_update_flags(
    channels: List[PulseBlasterChannel], program_duration: int
) -> Tuple[np.ndarray, np.ndarray]:
    # To ensure the first duration is counted from t=0 we add a zero.
    # Also, 0^flags = flags, so we can add a zero to update_flags without effect
    # and maintaining the correct shape.
    update_times = [0.0]
    update_flags = [0]
    for c in channels:
        for start_time, pulse_length in zip(c.start_times, c.pulse_lengths):
            update_times.append(start_time)
            update_flags.append(c.flags)
            update_times.append(start_time + pulse_length)
            update_flags.append(c.flags)
    update_times.append(program_duration)

    # sort event w.r.t. times, ie. put them in chronological order
    update_times = np.array(update_times)
    indices = np.argsort(update_times)
    ordered_update_flags = np.array(update_flags)[indices[:-1]]
    ordered_inst_lengths = np.diff(update_times[indices])

    return ordered_inst_lengths, ordered_update_flags


def create_pb_insts(
    inst_legnths: np.ndarray, update_flags: np.ndarray
) -> PBInstructions:
    # If e.g. two channels turn high at same time, we would
    # have created two instructions where the former has inst_length=0.
    # Zero instructions length are not registered, but are rather
    # combined with subcessor instructions before adding to the next.
    pb_insts = []
    new_flags = 0  # initialize: all channels are low.
    for inst_length, update_flags in zip(inst_legnths, update_flags):
        new_flags = new_flags ^ update_flags
        if inst_length == 0:
            # we will not move in time and hence we do not register a flags
            # in the final pb instruction list.
            continue
        pb_insts.append((new_flags, Inst.CONTINUE, 0, inst_length))
    # print_pb_insts(pb_insts)
    return pb_insts


def pulse_program_pb_insts(
    channels: List[PulseBlasterChannel], program_duration: int
) -> PBInstructions:
    """
    Convenience function used to generate instructions for a Pulse Blaster PULSE_PROGRAM
    from a list of PulseBasterChanne
    """
    return create_pb_insts(*ordered_inst_lengths_and_update_flags(channels, program_duration))


def make_continueous(pb_insts: PBInstructions, offset: int = 0) -> PBInstructions:
    """
    change the last instruction to 'branch' 
    to the instruction with number 'offset'. 
    (pb_insts are zero-indexed)
    """
    n = pb_insts.pop(-1)
    pb_insts.append((n[0], Inst.BRANCH, int(offset), n[3]))
    return pb_insts


def continuous_pulse_program_pb_insts(
    channels: List[PulseBlasterChannel], program_duration: int
) -> PBInstructions:
    return make_continueous(pulse_program_pb_insts(channels, program_duration))
