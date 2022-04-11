'''
Created on Apr 4, 2022

@author: Benedikt Ursprung
'''

import numpy as np
from random import shuffle
import time

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
from odmr_measurements.pulse_program_generator import PulseProgramGenerator
from odmr_measurements.helper_functions import ContrastModes, calculateContrast


class ESRPulseProgramGenerator(PulseProgramGenerator):

    def setup_settings(self):
        self.settings.New('t_duration', unit='us', initial=160.0)
        self.settings.New('t_readout', unit='us', initial=10.0)
        self.settings.New('t_gate', unit='us', initial=50.0)
    
    def make_pulse_channels(self):
        S = self.settings
        t_duration = S['t_duration'] * 1e3
        t_readout = S['t_readout'] * 1e3
        t_gate = S['t_gate'] * 1e3
        
        AOMchannel = self.new_channel('AOM', [0], [t_duration])
        uWchannel = self.new_channel('uW', [0], [t_duration / 2])        
        # DAQ 
        _readout = t_readout + t_gate
        DAQ_sig = self.new_channel('DAQ_sig', [t_duration * 1 / 2 - _readout], [t_gate])
        DAQ_ref = self.new_channel('DAQ_ref', [t_duration * 2 / 2 - _readout], [t_gate])

        return [AOMchannel, DAQ_sig, DAQ_ref, uWchannel]     


def norm(x):
    return 1.0 * x / x.max()


class ESR(Measurement):

    name = "esr"

    def setup(self):

        S = self.settings

        self.frequency_range = S.New_Range(
            "frequency", initials=[2.7e9, 3e9, 3e6], unit="Hz", si=True
        )
        S.New("Nsamples", int, initial=1000, description='Number of samples per frequency per sweep')
        S.New("Navg", int, initial=1, description='Number of sweeps')
        S.New("randomize", bool, initial=False)
        S.New("shotByShotNormalization", bool, initial=False)
        S.New(
            "contrast_mode",
            str,
            initial="signalOverReference",
            choices=ContrastModes,
        )
        S.New("save_h5", bool, initial=True)        
        self.pulse_generator = ESRPulseProgramGenerator(self)

    def setup_figure(self):
        self.ui = DockArea()        
        
        widget = QWidget()
        self.plot_dock = self.ui.addDock(name=self.name, widget=widget, position='right')
        self.layout = QVBoxLayout(widget)
                
        settings_layout = QHBoxLayout()
        self.layout.addLayout(settings_layout)
        settings_layout.addWidget(self.frequency_range.New_UI())
        settings_layout.addWidget(self.settings.New_UI(include=["contrast_mode", "Nsamples", "Navg", "randomize", "save_h5"], style='form'))
        
        start_layout = QVBoxLayout()
        SRS = self.app.hardware["srs_control"]
        start_layout.addWidget(QLabel('<b>SRS control</b>'))
        start_layout.addWidget(SRS.settings.New_UI(['connected', 'amplitude']))
        start_layout.addWidget(self.settings.activation.new_pushButton())
        settings_layout.addLayout(start_layout)

        self.graph_layout = pg.GraphicsLayoutWidget(border=(100, 100, 100))
        self.layout.addWidget(self.graph_layout)
        self.plot = self.graph_layout.addPlot(title=self.name)
        self.data = {
            "signal_raw": np.arange(10),
            "reference_raw": np.arange(10) / 10,
            "contrast_raw": np.arange(10) / 100,
        }
        colors = ["g", "r", "w"]
        self.plot_lines = {}
        for i, name in enumerate(["signal_raw", "reference_raw", "contrast_raw"]):
            self.plot_lines[name] = self.plot.plot(
                self.data[name], pen=colors[i], symbol="o", symbolBrush=colors[i]
            )
        self.data["frequencies"] = np.arange(10) * 1e9
        self.data_ready = False
        self.i_run = 0
        
        self.ui.addDock(dock=self.pulse_generator.make_dock(), position='left')
        
    def update_display(self):
        if self.data_ready:
            for name in ["signal_raw", "reference_raw", "contrast_raw"]:
                y = self.data[name][:, 0:self.i_run + 1].mean(-1)
                self.plot_lines[name].setData(self.data["frequencies"], y)
        self.plot.setTitle(self.name)

    def pre_run(self):
        self.pulse_generator.update_pulse_plot()
        self.data_ready = False

    def run(self):
        self.data_ready = False
        self.data = {}
        S = self.settings

        SRS = self.app.hardware["srs_control"]
        PB = self.app.hardware["pulse_blaster"]
        DAQ = self.app.hardware['pulse_width_counters']

        frequencies = self.frequency_range.sweep_array
        self.data['frequencies'] = frequencies

        try:
            SRS.connect()
            SRS.settings["modulation"] = False

            SRS.settings["frequency"] = frequencies[0]
            # Program PB
            self.pulse_generator.program_hw()
            PB.configure()
            # PB.start()
            SRS.settings["output"] = True
            
            N_DAQ_readouts = 2 * S['Nsamples']
            DAQ.restart(N_DAQ_readouts)
            
            N_freqs = len(frequencies)
            Navg = S["Navg"]
            
            signal = np.zeros((N_freqs, Navg))
            reference = np.zeros_like(signal)
            contrast = np.zeros_like(signal)

            # Run experiment
            for i_run in range(Navg):
                self.i_run = i_run
                if self.interrupt_measurement_called:
                    break
                print("Run ", i_run + 1, " of ", Navg)
                if S["randomize"]:
                    if i_run > 0:
                        shuffle(frequencies)
                index = np.argsort(frequencies)
                
                for i_scanPoint in range(N_freqs):
                    pct = 100 * (i_run * N_freqs + i_scanPoint) / (Navg * N_freqs)
                    self.set_progress(pct)
                    if self.interrupt_measurement_called:
                        break
                    
                    SRS.settings["frequency"] = frequencies[i_scanPoint]

                    print("Scan point ", i_scanPoint + 1, " of ", N_freqs)
                    time.sleep(0.01)
                    
                    DAQ.restart(N_DAQ_readouts)
                    
                    # cts = np.array(DAQ.read_counts(N_DAQ_readouts))
                    # ref = np.sum(cts[1::2] - cts[0::2])
                    # sig = np.sum(cts[2::2] - cts[1:-2:2]) + cts[0]                 
                    
                    # print(cts[0::4].mean(), cts[1::4].mean(), cts[2::4].mean(), cts[3::4].mean(),)
                    # print(cts[:8])
                    # sig = cts[1::4] - cts[0::4]
                    # ref = cts[3::4] - cts[2::4]
                    
                    sig = np.array(DAQ.read_sig_counts(N_DAQ_readouts))
                    ref = np.array(DAQ.read_ref_counts(N_DAQ_readouts))
                    
                    print(sig.sum(), ref.sum())
                    ii = index[i_scanPoint]
                    signal[ii][i_run] = sig.mean()
                    reference[ii][i_run] = ref.mean()
                    if S["shotByShotNormalization"]:
                        contrast[ii][i_run] = np.mean(
                            calculateContrast(S["contrastMode"], sig, ref)
                        )
                    else:
                        contrast[ii][i_run] = calculateContrast(
                            S["contrast_mode"], signal[ii][i_run], reference[ii][i_run],
                        )

                    # Update data array
                    self.data["signal_raw"] = signal
                    self.data["reference_raw"] = reference
                    self.data["contrast_raw"] = contrast
                    self.data["frequencies"] = frequencies
                    self.data_ready = True

        finally:
            SRS.settings["output"] = False
            SRS.settings["modulation"] = False
            DAQ.end_tasks()
            PB.write_close()

    def post_run(self):
        if self.settings['save_h5']:
            self.save_h5_data()
        
    def save_h5_data(self):
        self.h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
        self.h5_meas_group = h5_io.h5_create_measurement_group(self, self.h5_file)
        ref = self.data['reference_raw'].mean(-1)
        sig = self.data['signal_raw'].mean(-1)
        self.h5_meas_group['reference'] = ref
        self.h5_meas_group['signal'] = sig
        for c in ContrastModes:
            self.h5_meas_group[c] = calculateContrast(c, sig, ref)
        for k, v in self.data.items():
            self.h5_meas_group[k] = v        
        self.pulse_generator.save_to_h5(self.h5_meas_group)
        self.h5_file.close()

