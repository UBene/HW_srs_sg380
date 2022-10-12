"""
Created on Mar 21, 2022

@author: Benedikt Ursprung
"""

from typing import List, Union

import numpy as np
import pyqtgraph as pg
from pyqtgraph.dockarea.Dock import Dock
from qtpy.QtWidgets import QPushButton

from ScopeFoundry.measurement import Measurement

from .pulse_blaster_hw import PulseBlasterHW
from .utils.pb_instructions import calc_pulse_program_duration, create_pb_insts
from .utils.pb_typing import PBInstructions
from .utils.plotting import PlotLines, make_plot_lines
from .utils.pulse_blaster_channel import PulseBlasterChannel, new_pb_channel


class PulseProgramGenerator:
    """
    Interface between a scope foundry Measurement and Scope_foundry PulseBlasterHW
    """

    name = "pulse_generator"

    def __init__(
        self, measurement: Measurement, pulse_blaser_hw_name: str = "pulse_blaster"
    ) -> None:
        self.hw: PulseBlasterHW = measurement.app.hardware[pulse_blaser_hw_name]
        self.settings = measurement.settings
        self.name = measurement.name
        self.measurement = measurement
        self.__pb_channels: List[PulseBlasterChannel] = list()
        self._setup_settings()

    def _setup_settings(self) -> None:
        # will settings add to the measurement settings.
        # keeps track which settings where created by PulseProgramGenerator
        self.measure_setting_names = [
            x.name for x in self.settings._logged_quantities.values()
        ]
        self.settings.New(
            "sync_out",
            float,
            unit="MHz",
            initial=-10.0,
            description="to deactivate set negative",
        )
        self.setup_additional_settings()
        self.settings.New(
            "all_off_padding",
            int,
            initial=0,
            unit="ns",
            vmin=0,
            spinbox_step=self.hw.clock_period_ns,
            description="trailing off time at the end of the pulse program",
        )
        self.settings.New(
            "enable_pulse_plot_update",
            bool,
            initial=True,
            description="disable for performance",
        )
        # settings generated to by generator, non the less part of
        # partent measurement.
        self.generator_settings = [
            x
            for x in self.settings._logged_quantities.values()
            if not x.name in self.measure_setting_names
        ]

    def setup_additional_settings(self) -> None:
        """Override this to add settings, e.g:

        self.settings.New('my_fancy_pulse_duration', unit='us', initial=160.0)
        """
        ...

    def make_pulse_channels(self) -> None:
        """Override this!!!
        add pulse pulse channel using self.new_channel. E.g:
        self.new_channel('pulse_blaster_hw_channel_name',
                         start_times=[0, 10],
                         pulse_lengths=[13, 12])  # all times in ns
        creates a channel with 2 pulses.
        """
        raise NotImplementedError(
            f"Overide make_pulse_channels() of {self.name} not Implemented"
        )

    @property
    def t_min(self) -> int:
        return self.hw.clock_period_ns

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
                exclude=self.measure_setting_names, style="form"
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

        for lq in self.generator_settings:
            lq.add_listener(self.update_pulse_plot)

        self.update_pulse_plot()
        return dock

    def get_pb_insts(self) -> PBInstructions:
        """also sets the pulse_prgram_duration"""
        pb_channels = self.get_pb_channels()
        pb_insts = create_pb_insts(
            pb_channels,
            all_off_padding=self.settings["all_off_padding"],
            continuous=True,
            branch_to=0,
            clock_period_ns=self.hw.clock_period_ns,
            short_pulse_bit_num=self.hw.short_pulse_bit_num,
        )
        self.pulse_program_duration = calc_pulse_program_duration(pb_insts)
        return pb_insts

    def get_pulse_plot_arrays(self) -> PlotLines:
        return make_plot_lines(self.get_pb_insts(), self.hw.channels_lookup)

    def save_to_h5(self, h5_meas_group) -> None:
        sub_group = h5_meas_group.create_group("pulse_plot_lines")
        for k, v in self.get_pulse_plot_arrays().items():
            sub_group[k] = np.array(v)

    def new_channel(
        self, channel: Union[str, int], start_times: List[float], pulse_lengths: List[float]
    ) -> PulseBlasterChannel:
        """channel can be a 
                - channel number (int) a physical output of the pulse blaster
                - channel name str as defined in the pulse blaster HW
        start_times: in ns 
        pulse_lengths: in ns"""
        if type(channel) == str:
            channel = self.hw.settings[channel]
        chan = new_pb_channel(channel, start_times,
                              pulse_lengths, self.hw.clock_period_ns)
        self.__pb_channels.append(chan)
        return chan

    def program_pulse_blaster_and_start(self) -> None:
        self.hw.write_pulse_program_and_start(self.get_pb_insts())
        self.measurement.log.info("programmed pulse blaster and start")

    def get_pb_channels(self) -> List[PulseBlasterChannel]:
        self.__pb_channels.clear()
        self.make_pulse_channels()
        self._add_sync_out_channel()
        return self.__pb_channels

    @property
    def sync_out_period_ns(self) -> float:
        return abs(1 / self.settings["sync_out"] * 1e3)

    def _add_sync_out_channel(self) -> None:
        if self.settings["sync_out"] <= 0:
            return

        pulse_program_duration = 0
        for c in self.__pb_channels:
            for start_time, length in zip(c.start_times, c.pulse_lengths):
                pulse_program_duration = max(
                    pulse_program_duration, start_time + length
                )

        # adjust pulse_program_duration to be integer multiple of of 'sync_out' period
        p = self.sync_out_period_ns
        N = int(abs(np.ceil(pulse_program_duration / p)))
        adjusted_program_duration = N * p
        for c in self.__pb_channels:
            for ii, (start_time, length) in enumerate(
                zip(c.start_times, c.pulse_lengths)
            ):
                if start_time + length == pulse_program_duration:
                    c.pulse_lengths[ii] = adjusted_program_duration - start_time
        sync_out = self.new_channel(
            "sync_out", np.arange(N) * p, np.ones(N) * 0.5 * p
        )  # 50% duty cycle
        self.__pb_channels.append(sync_out)
        return self.__pb_channels
