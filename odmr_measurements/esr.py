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

from odmr_measurements.contrast import ContrastModes, calculate_contrast
from ScopeFoundry import Measurement, h5_io
from ScopeFoundryHW.spincore import (PulseBlasterChannel,
                                     PulseProgramGenerator, ns, us)


class ESRPulseProgramGenerator(PulseProgramGenerator):

    def setup_additional_settings(self) -> None:

        self.settings.New('t_gate', unit='us', vmin=0, initial=1.0)
        self.settings.New('program_duration', float, unit='us', initial=200.0)

        max_readout_sig_ref = (
            self.settings['program_duration'] / 2) - self.settings['t_gate']
        self.settings.New('t_readout_sig', unit='us', vmin=0, initial=0.1)
        self.settings.New('t_readout_ref', unit='us', vmin=0, initial=0.1)

    def make_pulse_channels(self):
        S = self.settings

        # all times must be in ns.
        t_duration = S['program_duration'] * us
        t_readout_sig = S['t_readout_sig'] * us
        t_readout_ref = S['t_readout_ref'] * us

        t_gate = S['t_gate'] * us

        self.new_channel('AOM', [0], [t_duration])
        self.new_channel('uW', [0], [t_duration / 2])

        # DAQ
        #_readout_sig = t_readout_sig + t_gate
        #_readout_ref = t_readout_ref + t_gate
        self.new_channel(
            'DAQ_sig', [t_readout_sig], [t_gate])
        # 'DAQ_sig', [0.5 * t_duration - _readout_sig], [t_gate])
        self.new_channel(
            'DAQ_ref', [(t_duration/2) + t_readout_ref], [t_gate])
        # 'DAQ_ref', [t_duration - _readout_ref], [t_gate])


def norm(x):
    return 1.0 * x / x.max()


class ESR(Measurement):

    name = "esr"

    def setup(self):

        S = self.settings

        self.range = S.New_Range(
            "frequency", initials=[2.7e9, 3e9, 3e6], unit="Hz", si=True
        )
        S.New("N_samples", int, initial=1000)
        S.New("N_sweeps", int, initial=1)
        S.New("randomize", bool, initial=False,
              description='probe frequencies in a random order.')
        S.New("shotByShotNormalization", bool, initial=False)
        S.New(
            "contrast_mode",
            str,
            initial="fractionaldifferenceOverReference",
            choices=ContrastModes,
        )
        S.New("save_h5", bool, initial=True)

        self.data = {
            "frequencies": np.arange(10) * 1e9,
            # emulates N_sweeps=2
            "signal_raw": np.random.rand(20).reshape(2, -1),
            "reference_raw": np.random.rand(20).reshape(2, -1),
        }
        self.i_sweep = 0

        self.pulse_generator = ESRPulseProgramGenerator(self)

    def setup_figure(self):
        self.ui = DockArea()

        widget = QWidget()
        self.plot_dock = self.ui.addDock(
            name=self.name, widget=widget, position='right')
        self.layout = QVBoxLayout(widget)

        settings_layout = QHBoxLayout()
        self.layout.addLayout(settings_layout)
        settings_layout.addWidget(self.range.New_UI(True))
        settings_layout.addWidget(self.settings.New_UI(include=[
                                  "contrast_mode", "N_samples", "N_sweeps", "randomize", "save_h5"], style='form'))

        start_layout = QVBoxLayout()
        SRS = self.app.hardware["srs_control"]
        start_layout.addWidget(QLabel('<b>SRS control</b>'))
        start_layout.addWidget(SRS.settings.New_UI(['connected', 'amplitude']))
        start_layout.addWidget(self.settings.activation.new_pushButton())
        settings_layout.addLayout(start_layout)

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
        self.plot_lines['contrast'] = self.contrast_plot.plot(
            name=self.data["signal_raw"], pen='w')

        self.ui.addDock(
            dock=self.pulse_generator.New_dock_UI(), position='left')
        self.update_display()

    def update_display(self):
        x = self.data["frequencies"]

        signal = self.data["signal_raw"][0:self.i_sweep + 1, :].mean(0)
        reference = self.data["reference_raw"][0:self.i_sweep + 1, :].mean(0)

        self.plot_lines["signal"].setData(x, signal)
        self.plot_lines["reference"].setData(x, reference)

        S = self.settings
        contrast = calculate_contrast(S["contrast_mode"], signal, reference)
        self.plot_lines['contrast'].setData(x, contrast)

    def pre_run(self):
        self.pulse_generator.update_pulse_plot()
        self.pulse_generator.settings['enable_pulse_plot_update'] = False

    def run(self):
        S = self.settings

        SRS = self.app.hardware["srs_control"]
        if not SRS.settings['connected']:
            pass
            # raise RuntimeError('SRS_control hardware not connected')
        PB = self.app.hardware["pulse_blaster"]
        DAQ = self.app.hardware['pulse_width_counters']

        self.data['frequencies'] = frequencies = self.range.sweep_array

        N = len(frequencies)
        N_sweeps = S["N_sweeps"]
        N_DAQ_readouts = S['N_samples']

        try:
            SRS.connect()
            SRS.settings["modulation"] = False
            SRS.settings["frequency"] = frequencies[0]
            SRS.settings["output"] = True

            PB.connect()
            self.pulse_generator.program_pulse_blaster_and_start()

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
                        shuffle(frequencies)
                self.indices = np.argsort(frequencies)

                t0 = time.perf_counter()
                for j, frequency in enumerate(frequencies):
                    if self.interrupt_measurement_called:
                        break
                    pct = 100 * (i_sweep * N + j) / (N_sweeps * N)
                    self.set_progress(pct)

                    SRS.settings["frequency"] = frequency

                    # Update data arrays
                    jj = self.indices[j]
                    DAQ.restart(N_DAQ_readouts)
                    #time.sleep(N_DAQ_readouts * self.pulse_generator.pulse_program_duration/1e9)
                    self.data["signal_raw"][i_sweep][jj] = np.mean(
                        DAQ.read_sig_counts(N_DAQ_readouts))
                    self.data["reference_raw"][i_sweep][jj] = np.mean(
                        DAQ.read_ref_counts(N_DAQ_readouts))

                print('delta time', time.perf_counter() - t0)

        finally:
            SRS.settings["output"] = False
            SRS.settings["modulation"] = False
            DAQ.close_tasks()
            PB.write_close()

    def post_run(self):
        self.pulse_generator.settings['enable_pulse_plot_update'] = True
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
        self.h5_meas_group['frequencies'] = self.data['frequencies']
        for cm in ContrastModes:
            self.h5_meas_group[cm] = calculate_contrast(cm, signal, reference)
        for k, v in self.data.items():
            self.h5_meas_group[k] = v
        self.pulse_generator.save_to_h5(self.h5_meas_group)
        self.h5_file.close()
