'''
Created on Apr 14, 2022

@author: Benedikt Ursprung
'''
import numpy as np
from random import shuffle

from qtpy.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QLabel,
)
import pyqtgraph as pg
from pyqtgraph.dockarea.DockArea import DockArea

from ScopeFoundry import Measurement
from ScopeFoundry import h5_io
from odmr_measurements.contrast import ContrastModes, calculate_contrast
from odmr_measurements.correlation_spectroscopy_pulse_program_generator import CSPulseProgramGenerator


class CorrelationSpectroscopy(Measurement):

    name = "correlation_spectroscopy"

    def setup(self):

        S = self.settings

        self.range = S.New_Range(
            "t_correlations", initials=[0, 40000, 200], unit="ns", si=False
        )
        S.New("N_samples", int, initial=10000)
        S.New("N_sweeps", int, initial=4)
        S.New("randomize", bool, initial=False,
              description='probe t_correlations in a random order.')
        S.New("shotByShotNormalization", bool, initial=False)
        S.New(
            "contrast_mode",
            str,
            initial="signalOverReference",
            choices=ContrastModes,
        )
        S.New("save_h5", bool, initial=True)

        self.data = {
            "t_correlations": np.arange(10) * 1e9,
            # emulates N_sweeps=2
            "signal_raw": np.random.rand(20).reshape(2, -1),
            "reference_raw": np.random.rand(20).reshape(2, -1),
        }
        self.i_sweep = 0

        self.pulse_generator = CSPulseProgramGenerator(self)

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
        start_layout.addWidget(SRS.settings.New_UI(
            ['connected', 'amplitude', 'frequency']))
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
        x = self.data["t_correlations"]

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

        self.data['t_correlations'] = t_correlations = self.range.sweep_array

        N = len(t_correlations)
        N_sweeps = S["N_sweeps"]
        N_DAQ_readouts = S['N_samples']

        try:
            SRS.connect()
            SRS.settings['modulation'] = True
            SRS.settings['modulation_type'] = 6
            SRS.settings['QFNC'] = 5  # External
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
                        shuffle(t_correlations)
                self.indices = np.argsort(t_correlations)

                for j, t_correlation in enumerate(t_correlations):
                    if self.interrupt_measurement_called:
                        break
                    pct = 100 * (i_sweep * N + j) / (N_sweeps * N)
                    self.set_progress(pct)

                    self.pulse_generator.settings['t_pi'] = t_correlation
                    self.pulse_generator.program_pulse_blaster_and_start()

                    # Update data arrays
                    jj = self.indices[j]
                    DAQ.restart(N_DAQ_readouts)
                    #time.sleep(N_DAQ_readouts * self.pulse_generator.pulse_program_duration/1e9)
                    self.data["signal_raw"][i_sweep][jj] = np.mean(
                        DAQ.read_sig_counts(N_DAQ_readouts))
                    self.data["reference_raw"][i_sweep][jj] = np.mean(
                        DAQ.read_ref_counts(N_DAQ_readouts))

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
        self.h5_meas_group['t_correlations'] = self.data['t_correlations']
        for cm in ContrastModes:
            self.h5_meas_group[cm] = calculate_contrast(cm, signal, reference)
        for k, v in self.data.items():
            self.h5_meas_group[k] = v
        self.pulse_generator.save_to_h5(self.h5_meas_group)
        self.h5_file.close()
