import matplotlib.pylab as plt
import numpy as np
from typing import List, Union
from .typing import ChannelsLookUp, PlotLines, PBInstructions

def make_plot_lines(
    pb_insts: PBInstructions,
    channel_look_up: Union[None, ChannelsLookUp] = None,
    low: int = 0,
    high: int = 1,
) -> PlotLines:
    if channel_look_up is None:
        # assuming there are 24 channels named output_i
        channel_look_up = {i: f"output_{i}" for i in range(24)}

    # lines = {channel_name: (x-coordinates, y-coordinates)}
    # all lines start at (0,0)
    time = 0.0
    lines = {channel_name: ([time], [low]) for channel_name in channel_look_up.values()}

    for state, _, _, length in pb_insts:
        for channel_number, channel_name in channel_look_up.items():
            xs, ys = lines[channel_name]
            if 2**channel_number & state:
                if ys[-1] == low:
                    xs.append(time)
                    ys.append(low)
                    xs.append(time)
                    ys.append(high)
            else:
                if ys[-1] == high:
                    xs.append(time)
                    ys.append(high)
                    xs.append(time)
                    ys.append(low)
        time += length

    for channel_name, (xs, ys) in lines.copy().items():
        if len(xs) < 2:
            lines.pop(channel_name)
            continue

        # draw a line to the end of period
        if xs[-1] != time:
            xs.append(time)
            ys.append(ys[-1])
    return lines


def matplotlib_plot(plot_lines: PlotLines) -> None:
    for i, (channel_name, (x, y)) in enumerate(plot_lines.items()):
        print(i, x, y)
        plt.plot(x, np.array(y) * 0.5 + i, label=channel_name)
    plt.yticks(range(len(plot_lines)), list(plot_lines.keys()))
    plt.show()


def test():
    states = [
        0b000000000000000001101000,  # 0
        0b000000000000000001100000,  # 1
        0b000000000000000000100000,  # 2
        0b000000000000000000100100,  # 3
        0b000000000000000000100110,  # 4
        0b000000000000000001100110,  # 5
        0b000000000000000001100100,  # 6
        0b000000000000000001100000,  # 7
        0b000000000000000001100100,  # 8
        0b000000000000000000100100,  # 9
        0b000000000000000000100101,  # 10
        0b000000000000000000101100,  # 11
    ]
    bp_insts = [(s,0,0,i) for i,s in enumerate(states)]
    plot_lines = make_plot_lines(bp_insts)
    matplotlib_plot(plot_lines)


if __name__ == "__main__":
    test()
