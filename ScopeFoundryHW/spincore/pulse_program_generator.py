from typing import List, Tuple, Union

import numpy as np
import pyqtgraph as pg
from pyqtgraph.dockarea.Dock import Dock
from qtpy.QtWidgets import QPushButton

from ScopeFoundry.measurement import Measurement

from .pulse_blaster_hw import PulseBlasterHW
from .pulse_program_ploting import PlotLines, make_plot_lines
from .spinapi import Inst
from .typing import PBInstructions, Flags


class PulseBlasterChannel:
    """
    flags: 	here, an int that represents the selected channel to be on (see also Flags in typing file)
    length: the duration the channel is high after star_time
    """

    __slots__ = ["flags", "start_times", "pulse_lengths"]

    def __init__(
        self, flags: int, start_times: List[float], pulse_lengths: List[float]
    ):
        self.flags = flags
        self.start_times = start_times
        self.pulse_lengths = pulse_lengths

    def __str__(self):
        return f"""Channel Nummer: {int(np.log2(self.flags))} 
					flags: {self.flags:024b} 
					#Pulses: {len(self.pulse_lengths)}"""


# short pulse flags:
ONE_PERIOD = 0x200000


class PulseProgramGenerator:

    name = "pulse_generator"

    def __init__(
        self, measurement: Measurement, pulse_blaser_hw_name: str = "pulse_blaster"
    ):
        self.hw: PulseBlasterHW = measurement.app.hardware[pulse_blaser_hw_name]
        self.settings = measurement.settings
        self.name = measurement.name
        self.measurement = measurement

        self.non_pg_setting_names = [
            x.name for x in self.settings._logged_quantities.values()
        ]
        self.settings.New("program_duration", float, unit="us", initial=160.0)
        self.settings.New(
            "sync_out",
            float,
            unit="MHz",
            initial=-10.0,
            description="to deactivate set negative",
        )
        self.setup_additional_settings()
        self.settings.New(
            "enable_pulse_plot_update",
            bool,
            initial=True,
            description="disable for performance",
        )
        self.pg_settings = [
            x
            for x in self.settings._logged_quantities.values()
            if not x.name in self.non_pg_setting_names
        ]

    def setup_additional_settings(self) -> None:
        """Override this to add settings, e.g:

        self.settings.New('my_fancy_pulse_duration', unit='us', initial=160.0)

                returns None

        Note: PulseProgramGenerators have by default a 'program_duration' and 'sync_out'
                  setting. You can set a value here

        self.settings['sync_out'] = 3.3333  # in MHz
        self.settings['program_duration'] = 10  # in us
        """
        ...

    def make_pulse_channels(self) -> List[PulseBlasterChannel]:
        """Override this!!!
        should return a list of PulseBlasterChannel
        PulseBlasterChannel can be generated using self.new_channel
        """
        raise NotImplementedError(
            f"Overide make_pulse_channels() of {self.name} not Implemented"
        )

    def update_pulse_plot(self) -> None:
        if self.settings["enable_pulse_plot_update"]:
            plot = self.plot
            plot.clear()
            pulse_plot_arrays = self.get_pulse_plot_arrays()
            for ii, (name, (t, y)) in enumerate(pulse_plot_arrays.items()):
                y = np.array(y) - 2 * ii
                t = np.array(t) / 1e9
                plot.plot(t, y, name=name, pen=self.hw.pens.get(name, "w"))

    def New_dock_UI(self) -> Dock:
        dock = Dock(
            name=self.name + " pulse generator",
            widget=self.settings.New_UI(
                exclude=self.non_pg_setting_names, style="form"
            ),
        )

        pb = QPushButton("program and start pulse blaster")
        pb.clicked.connect(self.program_pulse_blaster_and_start)
        dock.addWidget(pb)

        graph_layout = pg.GraphicsLayoutWidget(border=(0, 0, 0))
        dock.addWidget(graph_layout)
        self.plot = graph_layout.addPlot(title="pulse profile")
        self.plot.setLabel("bottom", units="s")
        self.plot.addLegend()

        for lq in self.pg_settings:
            lq.add_listener(self.update_pulse_plot)

        self.update_pulse_plot()
        return dock

    def get_pb_insts(self) -> PBInstructions:
        return continuous_pulse_program_pb_insts(*self.get_pb_program_and_duration())

    def get_pulse_plot_arrays(self) -> PlotLines:
        return make_plot_lines(self.get_pb_insts(), self.hw.channels_lookup)

    def save_to_h5(self, h5_meas_group) -> None:
        for k, v in self.get_pulse_plot_arrays().items():
            h5_meas_group[k] = np.array(v)

    def _new_channel(
        self, flags: int, start_times: List[float], pulse_lengths: List[float]
    ) -> PulseBlasterChannel:
        t_min = self.t_min
        return PulseBlasterChannel(
            flags,
            [t_min * round(x / t_min) for x in start_times],
            [t_min * round(x / t_min) for x in pulse_lengths],
        )

    def new_channel(
        self, channel: str, start_times: List[float], pulse_lengths: List[float]
    ) -> PulseBlasterChannel:
        """all times and lengths in ns"""
        flags = self.hw.get_flags(channel)
        return self._new_channel(flags, start_times, pulse_lengths)

    def new_one_period_channel(
        self, multiple: int, start_times: List[float], lengths: List[float]
    ) -> PulseBlasterChannel:
        return self._new_channel(int(multiple) * ONE_PERIOD, start_times, lengths)

    @property
    def t_min(self) -> float:
        """in ns"""
        return 1e3 / self.hw.settings["clock_frequency"]

    def program_pulse_blaster_and_start(
        self, pulse_blaster_hw: Union[PulseBlasterHW, None] = None
    ) -> PBInstructions:
        if not pulse_blaster_hw:
            pulse_blaster_hw = self.hw
        pb_insts = self.get_pb_insts()
        # print_pb_insts(pb_insts)
        pulse_blaster_hw.write_pulse_program_and_start(pb_insts)
        self.measurement.log.info("programmed pulse blaster and start")
        return pb_insts

    @property
    def sync_out_period_ns(self):
        return abs(1 / self.settings["sync_out"] * 1e3)

    def get_pb_program_and_duration(self) -> Tuple[List[PulseBlasterChannel], float]:
        pb_channels = self.make_pulse_channels()
        max_t = 0
        for c in pb_channels:
            for start_time, length in zip(c.start_times, c.pulse_lengths):
                max_t = max(max_t, start_time, start_time + length)

        if self.settings["sync_out"] <= 0:
            self.pulse_program_duration = max_t
            return pb_channels, max_t

        # enforce program length to be integer multiple of of 'sync_out' period
        period = self.sync_out_period_ns
        N = int(abs(np.ceil(max_t / period)))
        pulse_program_duration = N * period
        for c in pb_channels:
            for ii, (start_time, length) in enumerate(
                zip(c.start_times, c.pulse_lengths)
            ):
                if start_time + length == max_t:
                    c.pulse_lengths[ii] = pulse_program_duration - start_time
        sync_out = self.new_channel(
            "sync_out", np.arange(N) * period, np.ones(N) * 0.5 * period
        )  # 50% duty cycle
        pb_channels.extend([sync_out])

        self.pulse_program_duration = pulse_program_duration
        return pb_channels, pulse_program_duration


def ordered_durations_and_flags(
    channels: List[PulseBlasterChannel], program_duration: float
) -> Tuple[np.ndarray, np.ndarray]:
    # To ensure the first duration is counted from t=0 we add a zero.
    # Also, 0^flags = flags, so we can add a zero to update_flags without effect
    # and maintaining the correct shape.
    update_times = [0.0]
    unordered_update_flags = [0]
    for c in channels:
        for start_time, duration in zip(c.start_times, c.pulse_lengths):
            update_times.append(start_time)
            unordered_update_flags.append(c.flags)
            update_times.append(start_time + duration)
            unordered_update_flags.append(c.flags)
    update_times.append(program_duration)

    # sort event w.r.t. times, ie. put them in chronological order
    update_times = np.array(update_times)
    indices = np.argsort(update_times)
    ordered_update_flags = np.array(unordered_update_flags)[indices[:-1]]

    ordered_durations = np.diff(update_times[indices])
    return ordered_durations, ordered_update_flags


def create_pb_insts(
    ordered_durations: np.ndarray, ordered_update_flags: np.ndarray
) -> PBInstructions:
    # note that some durations are zero and we do not register them, but rather
    # e.g. when we turn two channels high at same time
    pb_insts = []
    new_flags = 0  # initialize: all channels are low.
    for duration, update_flags in zip(ordered_durations, ordered_update_flags):
        new_flags = new_flags ^ update_flags
        if duration == 0:
            # we will not move in time and hence we do not register a flags 
            # in the final pb instr. 
            continue
        pb_insts.append((new_flags, Inst.CONTINUE, 0, duration))
        
    print_pb_insts(pb_insts)
    return pb_insts


def pulse_program_pb_insts(
    channels: List[PulseBlasterChannel], program_duration: float
) -> PBInstructions:
    """
    Convenience function used to generate instructions for a Pulse Blaster PULSE_PROGRAM
    from a list of PulseBasterChanne
    """
    return create_pb_insts(*ordered_durations_and_flags(channels, program_duration))


def make_continueous(pb_insts: PBInstructions, offset=0) -> PBInstructions:
    """
    change the last instruction to 'branch' 
    to the instruction with number 'offset'. (pb_insts are zero-indexed)
    """
    n = pb_insts.pop(-1)
    pb_insts.append((n[0], Inst.BRANCH, int(offset), n[3]))
    return pb_insts


def continuous_pulse_program_pb_insts(
    channels: List[PulseBlasterChannel], program_duration: float
) -> PBInstructions:
    return make_continueous(pulse_program_pb_insts(channels, program_duration))


def print_flags_lengths(flags_list, lengths) -> None:
    print("{:<24} ns".format("flags"))
    for flags, length in zip(flags_list, lengths):
        print(f"{flags:024b}", length)


def print_pb_insts(pb_insts: PBInstructions) -> None:
    print("{:<7} {:<24} inst ns".format("", "flags"))
    for flags, inst, inst_data, length in pb_insts:
        print(f"{flags:>7} {flags:024b} {inst}, {inst_data} {length:0.1f}")
