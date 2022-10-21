'''
Created on Apr 4, 2022

@author: Benedikt Ursprung
'''

import time
from random import shuffle

import numpy as np
import pyqtgraph as pg
from pyqtgraph.dockarea.DockArea import DockArea
from qtpy.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from odmr_measurements.contrast import calculate_contrast, contrast_modes
from odmr_measurements.rabi_pulse_program_generator import \
    RabiPulseProgramGenerator
from ScopeFoundry import Measurement, h5_io


def norm(x:np.ndarray):
    return 1.0 * x / x.max()


class Rabi(Measurement):

    name = "rabi"

    def setup(self):

        S = self.settings

        self.range = S.New_Range(
            "pulse_duration", initials=[0, 200, 2], unit="ns", si=True
        )

        S.New("N_samples", int, initial=1000)
        S.New("N_sweeps", int, initial=1)
        S.New("randomize", bool, initial=True)
        S.New("shot_by_shot_normalization", bool, initial=False)
        S.New(
            "contrast_mode",
            str,
            initial="signal_over_reference",
            choices=contrast_modes,
        )
        S.New("save_h5", bool, initial=True)

        self.data = {
            "pulse_durations": np.arange(10) * 1e9,
            # emulates N_sweeps=2
            "signal_raw": np.random.rand(20).reshape(2, -1),
            "reference_raw": np.random.rand(20).reshape(2, -1),
        }
        self.i_sweep = 0
        self.pulse_generator = RabiPulseProgramGenerator(self)

    def setup_figure(self):
        self.ui = DockArea()

        widget = QWidget()
        self.plot_dock = self.ui.addDock(
            name=self.name, widget=widget, position='right')
        self.layout = QVBoxLayout(widget)

        settings_layout = QHBoxLayout()
        settings_layout.addWidget(self.range.New_UI(True))
        settings_layout.addWidget(self.settings.New_UI(include=["contrast_mode", "N_samples",
                                                                "N_sweeps", "randomize", "save_h5"], style='form'))
        start_layout = QVBoxLayout()
        SRS = self.app.hardware["srs_control"]
        start_layout.addWidget(QLabel('<b>SRS control</b>'))
        start_layout.addWidget(SRS.settings.New_UI(
            ['connected', 'amplitude', 'frequency']))
        start_layout.addWidget(self.settings.activation.new_pushButton())
        settings_layout.addLayout(start_layout)
        self.layout.addLayout(settings_layout)

        # Signal/reference Plots
        self.graph_layout = pg.GraphicsLayoutWidget(border=(100, 100, 100))
        self.layout.addWidget(self.graph_layout)
        self.plot = self.graph_layout.addPlot(title=self.name)
        self.plot.addLegend()

        self.plot_lines = {}
        self.plot_lines["signal"] = self.plot.plot(
            pen="g", symbol="o", symbolBrush="g")
        self.plot_lines["reference"] = self.plot.plot(
            pen="r", symbol="o", symbolBrush="r")

        # contrast Plots
        self.contrast_plot = self.graph_layout.addPlot(
            title='contrast', row=1, col=0)
        self.plot_lines['contrast'] = self.contrast_plot.plot(pen='w')

        self.ui.addDock(
            dock=self.pulse_generator.New_dock_UI(), position='left')
        self.update_display()

    def update_display(self):
        x = self.data["pulse_durations"]

        signal = self.data["signal_raw"][0:self.i_sweep + 1, :].mean(0)
        reference = self.data["reference_raw"][0:self.i_sweep + 1, :].mean(0)

        self.plot_lines["signal"].setData(x, signal)
        self.plot_lines["reference"].setData(x, reference)

        S = self.settings
        contrast = calculate_contrast(S["contrast_mode"], signal, reference)
        self.plot_lines['contrast'].setData(x, contrast)


    def pre_run(self):
        self.pulse_generator.update_pulse_plot()

    def set_pulse_duration(self, duration):
        self.pulse_generator.settings['t_uW'] = duration
        self.pulse_generator.program_pulse_blaster_and_start()

    def run(self):
        S = self.settings

        SRS = self.app.hardware["srs_control"]
        PB = self.app.hardware["pulse_blaster"]
        DAQ = self.app.hardware['pulse_width_counters']

        self.data['pulse_durations'] = pulse_durations = self.range.sweep_array

        N = len(pulse_durations)
        N_sweeps = S["N_sweeps"]
        N_DAQ_readouts = S['N_samples']

        try:
            SRS.connect()
            SRS.settings["modulation"] = False
            SRS.settings["output"] = True

            self.set_pulse_duration(pulse_durations[0])

            DAQ.restart(N_DAQ_readouts)

            # data arrays
            self.data["signal_raw"] = np.zeros((N_sweeps, N))
            self.data["reference_raw"] = np.zeros_like(self.data["signal_raw"])

            # Run experiment
            for i_sweep in range(N_sweeps):

                self.i_sweep = i_sweep
                if self.interrupt_measurement_called:
                    break
                self.log.info(f"sweep {i_sweep + 1} of {N_sweeps}")
                if S["randomize"]:
                    if i_sweep > 0:
                        shuffle(pulse_durations)
                self.indices = np.argsort(pulse_durations)

                for j, pulse_duration in enumerate(pulse_durations):
                    if self.interrupt_measurement_called:
                        break
                    pct = 100 * (i_sweep * N + j) / (N_sweeps * N)
                    self.set_progress(pct)

                    self.set_pulse_duration(pulse_duration)
                    time.sleep(0.01)

                    # Update data arrays
                    jj = self.indices[j]
                    DAQ.restart(N_DAQ_readouts)
                    #t_aquisition = N_DAQ_readouts * self.pulse_generator.pulse_program_duration/1e9
                    # time.sleep(t_aquisition)
                    self.data["signal_raw"][i_sweep][jj] = np.mean(
                        DAQ.read_sig_counts(N_DAQ_readouts))
                    self.data["reference_raw"][i_sweep][jj] = np.mean(
                        DAQ.read_ref_counts(N_DAQ_readouts))

        finally:
            SRS.settings["output"] = False
            SRS.settings["modulation"] = False
            DAQ.end_task()
            PB.write_close()

    def post_run(self):
        if self.settings['save_h5']:
            self.save_h5_data()

    def save_h5_data(self):
        self.h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
        self.h5_meas_group = h5_io.h5_create_measurement_group(
            self, self.h5_file)
        reference = self.data['reference_raw'].mean(0)
        signal = self.data['signal_raw'].mean(0)
        self.h5_meas_group['reference'] = reference
        self.h5_meas_group['signal'] = signal
        self.h5_meas_group['pulse_durations'] = self.data['pulse_durations']
        for cm in contrast_modes:
            self.h5_meas_group[cm] = calculate_contrast(cm, signal, reference)
        for k, v in self.data.items():
            try:
                self.h5_meas_group[k] = np.array(v)
            except RuntimeError:
                pass
        self.pulse_generator.save_to_h5(self.h5_meas_group)
        self.h5_file.close()
