from dataclasses import dataclass
from turtle import color
from typing import Dict

import matplotlib.pylab as plt
import numpy as np

from .pb_instructions import extract_channels_used
from .pb_typing import ChannelNameLU, List, PBInstructions, PlotLines, Union


@dataclass
class _Constants:
    low: int
    high: int
    clock_period: int
    short_pulse_bit_num: int


def _append_lowering_shape(xs: List[int], ys: List[int], time: int, c: _Constants) -> None:
    xs += [time, time]
    ys += [c.high, c.low]


def _append_rising_shape(xs: List[int], ys: List[int], time: int, c: _Constants) -> None:
    xs += [time, time]
    ys += [c.low, c.high]


def _append_short_pulse_from_high(xs: List[int], ys: List[int], time: int, n_clock_periods: int, c: _Constants) -> None:
    t1 = time + (c.clock_period * n_clock_periods)
    xs += [t1, t1]
    ys += [c.high, c.low]


def _append_short_pulse_from_low(xs: List[int], ys: List[int], time: int, n_clock_periods: int, c: _Constants) -> None:
    t0 = time
    t1 = time + (c.clock_period * n_clock_periods)
    if n_clock_periods < 5:
        # draw an extra line down
        xs += [t0, t0, t1, t1]
        ys += [c.low, c.high, c.high, c.low]
    else:
        xs += [t0, t0, t1]
        ys += [c.low, c.high, c.high]


def make_plot_lines(
    pb_insts: PBInstructions,
    channel_name_lu: Union[None, ChannelNameLU] = None,
    low: int = 0,
    high: int = 1,
    clock_period: int = 2,
    short_pulse_bit_num: int = 21,
) -> PlotLines:
    c = _Constants(low, high, clock_period, short_pulse_bit_num)
    # channel_name_lu may contain names of unused channels
    # construct a name look up for only channels being used in the pb_insts
    used_channels = extract_channels_used(pb_insts, short_pulse_bit_num)
    channel_name_lu = channel_name_lu if channel_name_lu else {}
    lu = {i: channel_name_lu.get(i, f"chan_{i}") for i in used_channels}

    return _create_lu_based_plot_lines(pb_insts, lu, c)


def _create_lu_based_plot_lines(pb_insts: PBInstructions, lu: ChannelNameLU, c: _Constants) -> PlotLines:
    '''
    creates a plot line for each channel represented in lu.
    '''

    # lines = {channel_name: (time-coordinates, y-coordinates)}
    # all lines start at (0,0)
    lines = {name: ([0], [c.low]) for name in lu.values()}
    time = 0
    for state, _, _, length in pb_insts:
        # periods_count is non-zero if short pulse feature was used
        periods_count = state >> c.short_pulse_bit_num
        for num, name in lu.items():
            xs, ys = lines[name]
            is_high = 1 << num & state
            was_high = ys[-1] == c.high
            if periods_count:
                if is_high and was_high:
                    _append_short_pulse_from_high(
                        xs, ys, time, periods_count, c)
                elif is_high and not was_high:
                    _append_short_pulse_from_low(
                        xs, ys, time, periods_count, c)
            else:
                if is_high and not was_high:
                    _append_rising_shape(xs, ys, time, c)
                elif not is_high and was_high:
                    _append_lowering_shape(xs, ys, time, c)
        time += length

    # make sure all lines end at the end of pulse program
    for name, (xs, ys) in lines.items():
        if xs[-1] != time:
            xs.append(time)
            ys.append(ys[-1])
    return lines


def matplotlib_plot(plot_lines: PlotLines, colors_lu: Dict[str, str] = {}, ax=None):
    if not ax:
        _, ax = plt.subplots()

    for i, (channel_name, (x, y)) in enumerate(plot_lines.items()):
        ax.plot(x, np.array(y) * 0.5 + i, '-o',
                color=colors_lu.get(channel_name, None),
                label=channel_name)
    plt.yticks(range(len(plot_lines)), list(plot_lines.keys()))
    return ax
