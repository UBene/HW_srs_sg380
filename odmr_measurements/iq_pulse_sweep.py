'''
Created on Apr 4, 2022

@author: Benedikt Ursprung
'''

import numpy as np

from qtpy.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QLabel
)
import pyqtgraph as pg
from pyqtgraph.dockarea.DockArea import DockArea

from ScopeFoundry import Measurement
from ScopeFoundry import h5_io
from ScopeFoundryHW.spincore import PulseProgramGenerator, PulseBlasterChannel

from spinapi.spinapi import us
import time


class IQPulseSweepProgramGenerator(PulseProgramGenerator):

    def setup_additional_settings(self) -> None:
        self.settings.New('t_readout_delay', unit='us',
                          initial=2.3, spinbox_decimals=4)
        self.settings.New('t_AOM', unit='us', initial=10)
        self.settings.New('AOM_on_off_delay', unit='us', initial=10)
        #self.settings.New('program_duration', float, unit='us', initial=160.0)
        #self.settings['program_duration'] = 15  # us
        self.settings.New('t_gate', unit='us', initial=1.0)

    def make_pulse_channels(self) -> [PulseBlasterChannel]:
        t_gate = self.settings['t_gate'] * us
        t_AOM = self.settings['t_AOM'] * us
        t_readout_delay = self.settings['t_readout_delay'] * us
        AOM_on_off_delay = self.settings['AOM_on_off_delay'] * us
        return [self.new_channel('AOM', [AOM_on_off_delay], [t_AOM]),
                self.new_channel('DAQ_sig', [AOM_on_off_delay + t_readout_delay], [t_gate]),
                self.new_channel('dummy_channel', [AOM_on_off_delay + t_AOM], [AOM_on_off_delay])]


def norm(x):
    return 1.0 * x / x.max()


class IQPulseSweep(Measurement):

    name = "iq_pulse_sweep"

    def setup(self):

        S = self.settings

        self.range = S.New_Range(
            "t_readout_delays", initials=[-5, 15, 0.05], unit="us", si=True
        )
        S.New("N_samples", int, initial=1000)
        S.New("N_sweeps", int, initial=1)
        S.New("randomize", bool, initial=False,
              description='probe t_readout_delays in a random order.')
        S.New("shotByShotNormalization", bool, initial=False)

        S.New("save_h5", bool, initial=True)


        t = np.arange(100)/16
        self.data = {
            "t_readout_delays": np.arange(10) * 1e9,
            # emulates N_sweeps=2
            "wave_form_t": t,
            "wave_forms": [np.sin(t), np.sin(t-1)],
        }
        self.i_sweep = 0

        self.pulse_generator = IQPulseSweepProgramGenerator(self)

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
                                  "N_samples", "N_sweeps", "randomize", "save_h5"], style='form'))

        start_layout = QVBoxLayout()
        #SRS = self.app.hardware["srs_control"]
        #start_layout.addWidget(QLabel('<b>SRS control</b>'))
        #start_layout.addWidget(SRS.settings.New_UI(
            #['connected', 'amplitude', 'frequency']))
        start_layout.addWidget(self.settings.activation.new_pushButton())
        settings_layout.addLayout(start_layout)

        # Signal/reference Plots
        self.graph_layout = pg.GraphicsLayoutWidget(border=(100, 100, 100))
        self.layout.addWidget(self.graph_layout)
        self.plot = self.graph_layout.addPlot(title=self.name)
        self.plot.addLegend()

        self.plot_lines = {}
        self.plot_lines["wave_form"] = self.plot.plot(pen="g")

        self.ui.addDock(
            dock=self.pulse_generator.New_dock_UI(), position='left')
        self.update_display()

    def update_display(self):
        t = self.data["wave_form_t"]
        y = self.data["wave_forms"][-1]
        self.plot_lines["wave_form"].setData(t, y)
        self.plot.setLabel('bottom', 'time')

    def pre_run(self):
        self.pulse_generator.update_pulse_plot()
        self.pulse_generator.settings['enable_pulse_plot_update'] = True

    def run(self):
        S = self.settings

        SRS = self.app.hardware["srs_control"]
        #if not SRS.settings['connected']:
            #pass
            # raise RuntimeError('SRS_control hardware not connected')
        PB = self.app.hardware["pulse_blaster"]

        self.data['t_readout_delays'] = t_readout_delays = self.range.sweep_array


        try:
            SRS.connect()
            SRS.settings["modulation"] = False
            SRS.settings["output"] = True

            PB.connect()
            self.pulse_generator.program_pulse_blaster_and_start(PB)


            # data arrays
            self.data["wave_forms"] = []

            # Run experiment
            for t_read_out_delay in t_readout_delays:
                S['t_readout_delay'] = t_read_out_delay
                self.pulse_generator.program_pulse_blaster_and_start(PB)
                time.sleep(1)
                self.data["wave_forms"].append(np.sin(self.data['wave_form_t'])*t_read_out_delay)


        finally:
            SRS.settings["output"] = False
            SRS.settings["modulation"] = False
            #DAQ.close_tasks()
            PB.write_close()

    def post_run(self):
        self.pulse_generator.settings['enable_pulse_plot_update'] = True
        if self.settings['save_h5']:
            self.save_h5_data()

    def save_h5_data(self):
        self.h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
        self.h5_meas_group = h5_io.h5_create_measurement_group(
            self, self.h5_file)
        for k, v in self.data.items():
            self.h5_meas_group[k] = v
        self.pulse_generator.save_to_h5(self.h5_meas_group)
        self.h5_file.close()
