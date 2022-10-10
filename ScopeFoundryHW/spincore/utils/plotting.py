from typing import List

import matplotlib.pylab as plt
import numpy as np

from .pb_typing import ChannelsLookUp, PBInstructions, PlotLines, Union


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
    if channel_look_up is None:
        # assuming there are 21 channels named output_i and number i for i = 0,...20
        channel_look_up = {
            i: f"output_{i}" for i in range(short_pulse_bit_num)}

    # lines = {channel_name: (x-coordinates, y-coordinates)}
    # all lines start at (0,0)
    time = 0
    lines = {channel_name: ([time], [low])
             for channel_name in channel_look_up.values()}

    for state, _, _, length in pb_insts:
        n_clock_periods = state >> short_pulse_bit_num
        for channel_number, channel_name in channel_look_up.items():
            xs, ys = lines[channel_name]
            now_high = 1 << channel_number & state
            prev_high = ys[-1] == high
            if n_clock_periods:
                if now_high and prev_high:
                    _append_short_pulse_from_high(
                        xs, ys, time, n_clock_periods, clock_period, low, high)
                elif now_high and not prev_high:
                    _append_short_pulse_from_low(
                        xs, ys, time, n_clock_periods, clock_period, low, high)
            else:
                if now_high and not prev_high:
                    _append_rising_shape(xs, ys, time, low, high)
                elif not now_high and prev_high:
                    _append_lowering_shape(xs, ys, time, low, high)
        time += length

    for channel_name, (xs, ys) in lines.copy().items():
        if len(xs) < 2:
            lines.pop(channel_name)
            continue

        # draw a line to the end of pulse instructions
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
