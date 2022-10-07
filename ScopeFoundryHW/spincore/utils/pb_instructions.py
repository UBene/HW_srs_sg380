from typing import List, Tuple

import numpy as np

from .pb_typing import PBInstructions
from .printing import print_pb_insts
from .pulse_blaster_channel import PulseBlasterChannel
from .spinapi import Inst


def create_pb_insts(channels: List[PulseBlasterChannel], all_off_padding:int=0, continuous=True, branch_to:int=0)-> PBInstructions:
    '''
    Convinience function to create instructions for a pulse program from a list of PulseBlasterChannel.
    *all_off_padding* adds time to end of the pulse program for which all channels are low.
    if *continuous* is True, the last instruction changed such that the program 'branches' 
        to the instruction with number *branch_to*. (pb_insts are zero-indexed)
    '''
    pb_insts = _create_pb_insts(*_ordered_inst_lengths_and_update_flags(channels),  all_off_padding)
    if continuous:
        pb_insts = _make_continueous(pb_insts, branch_to)
    return pb_insts
    

def _ordered_inst_lengths_and_update_flags(channels: List[PulseBlasterChannel]) -> Tuple[np.ndarray, np.ndarray]:
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

    # sort event w.r.t. times, ie. put them in chronological order
    update_times = np.array(update_times)
    indices = np.argsort(update_times)
    ordered_update_flags = np.array(update_flags)[indices]    
    # the last update_flags is used to switch off a final pulse
    # it can be dropped for continuous programs
    # it can be used to for all channels of padding at the end of the program.
    ordered_inst_lengths = np.diff(update_times[indices])
    return ordered_inst_lengths, ordered_update_flags


def _create_pb_insts(inst_legnths: np.ndarray, update_flags: np.ndarray, all_off_padding:int=0)-> PBInstructions:
    '''
    *all_off_padding* adds time to the pulse program for which all channels are low.
    '''
    # If e.g. two channels turn high at same time, we would
    # have created two instructions where the former has inst_length=0.
    # Zero instructions length are not registered, but are rather
    # combined with subcessor instructions before adding to the next.
    pb_insts = []
    new_flags = 0  # initialize: all channels are low
    for inst_length, u_flags in zip(inst_legnths, update_flags):
        new_flags = new_flags ^ u_flags
        if inst_length == 0:
            # we will not move in time and hence we do not register a flags
            # in the final pb instruction list.
            continue
        pb_insts.append((new_flags, Inst.CONTINUE, 0, inst_length))

    if all_off_padding:
        pb_insts.append((new_flags ^ update_flags[-1], Inst.CONTINUE, 0, all_off_padding))

    #print_pb_insts(pb_insts)
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
