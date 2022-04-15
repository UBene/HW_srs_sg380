'''
Created on Apr 4, 2022

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
from ScopeFoundryHW.spincore import PulseProgramGenerator, PulseBlasterChannel
from odmr_measurements.helper_functions import ContrastModes, calculateContrast
from spinapi.spinapi import us


class ESRPulseProgramGenerator(PulseProgramGenerator):

    def setup_additional_settings(self) -> None:
        self.settings.New('t_readout', unit='us', initial=10.0)
        self.settings.New('t_gate', unit='us', initial=50.0)
    
    def make_pulse_channels(self) -> [PulseBlasterChannel]:
        S = self.settings

        # All times must be in ns
        t_duration = S['program_duration'] * us
        t_readout = S['t_readout'] * us
        t_gate = S['t_gate'] * us
        
        AOM = self.new_channel('AOM', [0], [t_duration])
        uW = self.new_channel('uW', [0], [t_duration / 2])
        
        # DAQ 
        _readout = t_readout + t_gate
        DAQ_sig = self.new_channel('DAQ_sig', [t_duration * 1 / 2 - _readout], [t_gate])
        DAQ_ref = self.new_channel('DAQ_ref', [t_duration * 2 / 2 - _readout], [t_gate])

        return [uW, AOM, 
                #I, Q, 
                DAQ_sig, DAQ_ref]

def norm(x):
    return 1.0 * x / x.max()


class ESR(Measurement):

    name = "esr"

    def setup(self):

        S = self.settings

        self.frequency_range = S.New_Range(
            "frequency", initials=[2.7e9, 3e9, 3e6], unit="Hz", si=True
        )
        S.New("N_samples", int, initial=1000)
        S.New("N_sweeps", int, initial=1)
        S.New("randomize", bool, initial=False)
        S.New("shotByShotNormalization", bool, initial=False)
        S.New(
            "contrast_mode",
            str,
            initial="signalOverReference",
            choices=ContrastModes,
        )
        S.New("save_h5", bool, initial=True)                
        
        self.data = {
            "frequencies": np.arange(10) * 1e9,
            "signal_raw": np.random.rand(20).reshape(-1, 2),  # emulates N_sweeps=2
            "reference_raw": np.random.rand(20).reshape(-1, 2),
        }
        self.i_sweep = 0

        self.pulse_generator = ESRPulseProgramGenerator(self)

    def setup_figure(self):
        self.ui = DockArea()        
        
        widget = QWidget()
        self.plot_dock = self.ui.addDock(name=self.name, widget=widget, position='right')
        self.layout = QVBoxLayout(widget)
                
        settings_layout = QHBoxLayout()
        self.layout.addLayout(settings_layout)
        settings_layout.addWidget(self.frequency_range.New_UI(True))
        settings_layout.addWidget(self.settings.New_UI(include=["contrast_mode", "N_samples", "N_sweeps", "randomize", "save_h5"], style='form'))
        
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
        self.plot_lines["signal"] = self.plot.plot(pen="g", symbol="o", symbolBrush="g")
        self.plot_lines["reference"] = self.plot.plot(pen="r", symbol="o", symbolBrush="r")
        
        # contrast Plots
        self.contrast_plot = self.graph_layout.addPlot(title='contrast', row=1, col=0)
        self.plot_lines['contrast'] = self.contrast_plot.plot(name=self.data["signal_raw"], pen='w')

        self.ui.addDock(dock=self.pulse_generator.New_dock_UI(), position='left')
        self.update_display()
        
    def update_display(self):
        
        signal = self.data["signal_raw"][:, 0:self.i_sweep + 1].mean(-1)
        reference = self.data["reference_raw"][:, 0:self.i_sweep + 1].mean(-1)
        
        self.plot_lines["signal"].setData(self.data["frequencies"], signal)
        self.plot_lines["reference"].setData(self.data["frequencies"], reference)
                
        S = self.settings
        contrast = calculateContrast(S["contrast_mode"], signal, reference)
        self.plot_lines['contrast'].setData(self.data["frequencies"], contrast)

    def pre_run(self):
        self.pulse_generator.update_pulse_plot()

    def run(self):
        S = self.settings

        SRS = self.app.hardware["srs_control"]
        if not SRS.settings['connected']:
            raise RuntimeError('SRS_control hardware not connected')
        PB = self.app.hardware["pulse_blaster"]
        DAQ = self.app.hardware['pulse_width_counters']

        frequencies = self.frequency_range.sweep_array
        self.data['frequencies'] = frequencies
        
        try:
            PB.connect()
            self.pulse_generator.write_pulse_program_and_start()
            # PB.configure()  # DO WE NEED THIS LINE ?
            
            SRS.settings["modulation"] = False
            SRS.settings["frequency"] = frequencies[0]
            SRS.settings["output"] = True
            
            N_DAQ_readouts = S['N_samples']
            DAQ.restart(N_DAQ_readouts)
            
            N = len(frequencies)
            N_sweeps = S["N_sweeps"]
            
            # data arrays
            signal_raw = np.zeros((N, N_sweeps))
            reference_raw = np.zeros_like(signal_raw)

            # Run experiment
            for i_sweep in range(N_sweeps):
                self.i_sweep = i_sweep
                if self.interrupt_measurement_called:
                    break
                self.log.info(f"sweep {i_sweep + 1} of {N_sweeps}")
                if S["randomize"]:
                    if i_sweep > 0:
                        shuffle(frequencies)
                indices = np.argsort(frequencies)
                
                for i_scanPoint, frequency in enumerate(frequencies):
                    if self.interrupt_measurement_called:
                        break
                    pct = 100 * (i_sweep * N + i_scanPoint) / (N_sweeps * N)
                    self.set_progress(pct)
                    
                    SRS.settings["frequency"] = frequency                 
                    
                    DAQ.restart(N_DAQ_readouts)
                    sig = np.array(DAQ.read_sig_counts(N_DAQ_readouts))
                    ref = np.array(DAQ.read_ref_counts(N_DAQ_readouts))   
                    ii = indices[i_scanPoint]
                    signal_raw[ii][i_sweep] = sig.mean()
                    reference_raw[ii][i_sweep] = ref.mean()

                    # Update data array
                    self.data["signal_raw"] = signal_raw
                    self.data["reference_raw"] = reference_raw
                    self.data["frequencies"] = frequencies

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
        reference = self.data['reference_raw'].mean(-1)
        signal = self.data['signal_raw'].mean(-1)
        self.h5_meas_group['reference'] = reference
        self.h5_meas_group['signal'] = signal
        for c in ContrastModes:
            self.h5_meas_group[c] = calculateContrast(c, signal, reference)
        for k, v in self.data.items():
            self.h5_meas_group[k] = v
        self.pulse_generator.save_to_h5(self.h5_meas_group)
        self.h5_file.close()

