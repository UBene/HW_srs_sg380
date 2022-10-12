import matplotlib.pylab as plt
import numpy as np

from .pb_instructions import extract_used_channels
from .pb_typing import ChannelsLookUp, List, PBInstructions, PlotLines, Union


def _append_lowering_shape(xs: List[int], ys: List[int], time: int, low: int, high: int) -> None:
    xs += [time, time]
    ys += [high, low]


def _append_rising_shape(xs: List[int], ys: List[int], time: int, low: int, high: int) -> None:
    xs += [time, time]
    ys += [low, high]


def _append_short_pulse_from_high(xs: List[int], ys: List[int], time: int, n_clock_periods: int, clock_period: int, low: int, high: int) -> None:
    t1 = time + (clock_period * n_clock_periods)
    xs += [t1, t1]
    ys += [high, low]


def _append_short_pulse_from_low(xs: List[int], ys: List[int], time: int, n_clock_periods: int, clock_period: int, low: int, high: int) -> None:
    t0 = time
    t1 = time + (clock_period * n_clock_periods)
    if n_clock_periods < 5:
        # draw an extra line down
        xs += [t0, t0, t1, t1]
        ys += [low, high, high, low]
    else:
        xs += [t0, t0, t1]
        ys += [low, high, high]


def make_plot_lines(
    pb_insts: PBInstructions,
    channel_look_up: Union[None, ChannelsLookUp] = None,
    low: int = 0,
    high: int = 1,
    clock_period: int = 2,
    short_pulse_bit_num: int = 21,
) -> PlotLines:

    lu = {i: f"chan_{i}" for i in extract_used_channels(
        pb_insts, short_pulse_bit_num)}
    if channel_look_up:
        lu.update(channel_look_up)

    # lines = {channel_name: (time-coordinates, y-coordinates)}
    # all lines start at (0,0)
    time = 0
    lines = {name: ([time], [low]) for name in lu.values()}

    for state, _, _, length in pb_insts:
        # n_clock_periods is non-zero if short pulse feature was used
        n_clock_periods = state >> short_pulse_bit_num
        for num, name in lu.items():
            xs, ys = lines[name]
            is_high = 1 << num & state
            was_high = ys[-1] == high
            if n_clock_periods:
                if is_high and was_high:
                    _append_short_pulse_from_high(
                        xs, ys, time, n_clock_periods, clock_period, low, high)
                elif is_high and not was_high:
                    _append_short_pulse_from_low(
                        xs, ys, time, n_clock_periods, clock_period, low, high)
            else:
                if is_high and not was_high:
                    _append_rising_shape(xs, ys, time, low, high)
                elif not is_high and was_high:
                    _append_lowering_shape(xs, ys, time, low, high)
        time += length

    # draw a line to the end of pulse instructions
    for name, (xs, ys) in lines.items():
        if xs[-1] != time:
            xs.append(time)
            ys.append(ys[-1])

    return lines


def matplotlib_plot(plot_lines: PlotLines, ax=None):
    if not ax:
        _, ax = plt.subplots()

    for i, (channel_name, (x, y)) in enumerate(plot_lines.items()):
        ax.plot(x, np.array(y) * 0.5 + i, '-o', label=channel_name)
    plt.yticks(range(len(plot_lines)), list(plot_lines.keys()))
    return ax
