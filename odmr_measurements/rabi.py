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
)
import pyqtgraph as pg
from pyqtgraph.dockarea.DockArea import DockArea

from ScopeFoundry import Measurement
from ScopeFoundry import h5_io
from odmr_measurements.pulse_program_generator import PulseProgramGenerator,\
    PulseBlasterChannel
from odmr_measurements.helper_functions import ContrastModes, calculateContrast
from spinapi.spinapi import us


class RabiPulseProgramGenerator(PulseProgramGenerator):
    
    name = 'rabi_pulse_generator'

    def setup_additional_settings(self) -> None:
        self.settings.New('t_uW', unit='ns', initial=200)
        self.settings.New('t_readout_delay', unit='us', initial=2.3)
        self.settings.New('t_AOM', unit='us', initial=2.0)
        self.settings.New('t_uW_to_AOM_delay', unit='us', initial=1.0)
        self.settings['program_duration'] = 30  # in us
        self.settings.New('t_gate', unit='us', initial=5.0)
    
    def make_pulse_channels(self) -> [PulseBlasterChannel]:
        S = self.settings
        t_min = self.t_min
        
        t_AOM = S['t_AOM'] * us
        t_readout_delay = S['t_readout_delay'] * us
        
        start_delay = 0  # t_min * round(1 * us / t_min) + t_readout_delay
        # t_startTrig = t_min * round(300 * ns / t_min)
        t_readout = S['t_gate'] * 1e3  # t_min * round(300 * ns / t_min)
        t_uW_to_AOM_delay = S['t_uW_to_AOM_delay']    
        
        t_half = S['program_duration'] * us / 2
        if S['t_uW'] <= 5 * t_min and S['t_uW'] > 0: 
            # For microwave pulses < 5 * t_min, the microwave channel (PB_MW) is instructed 
            # to pulse for 5 * t_min, but the short-pulse flags of the PB are pulsed 
            # simultaneously (shown in white) to the desired output pulse length at uW. 
            # This can be verified on an oscilloscope.          
            uWchannel = self.new_channel('uW', [start_delay], [5 * t_min])
            shortPulseChannel = self.new_one_period_channel(int(S['t_uW'] / 2), [start_delay], [5 * t_min])
            channels = [shortPulseChannel, uWchannel]  # Short pulse feature321e  
        else:
            uWchannel = self.new_channel('uW', [start_delay], [S['t_uW']])
            channels = [uWchannel]
            
        T = t_uW_to_AOM_delay + t_AOM + S['t_uW']
        AOM = self.new_channel('AOM', [T, t_half + T], [t_AOM, t_AOM])
        # DAQchannel = self.new_channel('DAQ', [t_half - t_AOM + t_readout_delay, 2 * t_half - t_AOM + t_readoutDelay], [t_readout, t_readout])
        # STARTtrigchannel = self.new_channel('STARTtrig', [0], [t_startTrig])
        
        DAQ_sig = self.new_channel('DAQ_sig', [T + t_AOM + t_readout_delay], [t_readout])
        DAQ_ref = self.new_channel('DAQ_ref', [t_half + T + t_AOM + t_readout_delay], [t_readout])
        
        channels.extend([AOM, DAQ_sig, DAQ_ref])
        return channels



def norm(x):
    return 1.0 * x / x.max()


class Rabi(Measurement):

    name = "rabi"

    def setup(self):

        S = self.settings

        self.pulse_duration_range = S.New_Range(
            "pulse_duration", initials=[0, 200, 2], unit="ns", si=True
        )

        S.New("N_samples", int, initial=1000)
        S.New("N_sweeps", int, initial=1)
        S.New("randomize", bool, initial=True)
        S.New("shotByShotNormalization", bool, initial=False)
        S.New(
            "contrast_mode",
            str,
            initial="signalOverReference",
            choices=ContrastModes,
        )
        S.New("save_h5", bool, initial=True)        
        self.pulse_generator = RabiPulseProgramGenerator(self)

    def setup_figure(self):
        self.ui = DockArea()        
        
        widget = QWidget()
        self.plot_dock = self.ui.addDock(name=self.name, widget=widget, position='right')
        self.layout = QVBoxLayout(widget)
                
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(self.pulse_duration_range.New_UI(True))
        settings_layout.addWidget(self.settings.New_UI(include=["contrast_mode", "N_samples",
                                                                "N_sweeps", "randomize", "save_h5"], style='form'))
        settings_layout.addWidget(self.settings.activation.new_pushButton())
        self.layout.addLayout(settings_layout)

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
        self.data["pulse_durations"] = np.arange(10) * 1e9
        self.data_ready = False
        self.i_sweep = 0
        
        self.ui.addDock(dock=self.pulse_generator.New_dock_UI(), position='left')
        
    def update_display(self):
        if self.data_ready:
            for name in ["signal_raw", "reference_raw", "contrast_raw"]:
                x = self.data["pulse_durations"] / 1e9
                y = self.data[name][:, 0:self.i_sweep + 1].mean(-1)
                self.plot_lines[name].setData(x, norm(y))
        self.plot.setTitle(self.name)
        self.plot.setLabel("bottom", units='s')

    def pre_run(self):
        self.pulse_generator.update_pulse_plot()
        self.data_ready = False
        
    def set_pulse_duration(self, duration):
        self.pulse_generator.settings['t_uW'] = duration
        self.pulse_generator.program_hw()

    def run(self):
        self.data_ready = False
        self.data = {}
        S = self.settings

        SRS = self.app.hardware["srs_control"]
        PB = self.app.hardware["pulse_blaster"]
        DAQ = self.app.hardware['triggered_counter']

        pulse_durations = self.pulse_duration_range.sweep_array
        self.data['pulse_durations'] = pulse_durations

        try:
            SRS.connect()
            SRS.settings["modulation"] = False

            self.set_pulse_duration(pulse_durations[0])
            PB.configure()
            SRS.settings["output"] = True
            DAQ.restart(2 * S['N_samples'])
            
            N_freqs = len(pulse_durations)
            N_sweeps = S["N_sweeps"]
            
            signal = np.zeros((N_freqs, N_sweeps))
            reference = np.zeros_like(signal)
            contrast = np.zeros_like(signal)

            # Run experiment
            for i_sweep in range(N_sweeps):
                self.i_sweep = i_sweep
                if self.interrupt_measurement_called:
                    break
                self.log.info(f"sweep {i_sweep + 1} of {N_sweeps}")
                if S["randomize"]:
                    if i_sweep > 0:
                        shuffle(pulse_durations)
                index = np.argsort(pulse_durations)
                
                for i_scanPoint, pulse_duration in enumerate(pulse_durations):
                    pct = 100 * (i_sweep * N_freqs + i_scanPoint) / (N_sweeps * N_freqs)
                    self.set_progress(pct)
                    if self.interrupt_measurement_called:
                        break
                    
                    # SRS.settings["frequency"] = pulse_durations[i_scanPoint]
                    self.set_pulse_duration(pulse_duration)
                    
                    time.sleep(0.01)

                    cts = np.array(DAQ.read_counts(2 * S['N_samples']))
                    ref = np.sum(cts[1::2] - cts[0::2])
                    sig = np.sum(cts[2::2] - cts[1:-2:2]) + cts[0]                 
                    
                    # print(cts[0::4].mean(), cts[1::4].mean(), cts[2::4].mean(), cts[3::4].mean(),)
                    # print(cts[:8])
                    # sig = cts[1::4] - cts[0::4]
                    # ref = cts[3::4] - cts[2::4]
                    
                    print(sig.sum(), ref.sum())
                    ii = index[i_scanPoint]
                    signal[ii][i_sweep] = sig
                    reference[ii][i_sweep] = ref
                    if S["shotByShotNormalization"]:
                        contrast[ii][i_sweep] = np.mean(
                            calculateContrast(S["contrastMode"], sig, ref)
                        )
                    else:
                        contrast[ii][i_sweep] = calculateContrast(
                            S["contrast_mode"], signal[ii][i_sweep], reference[ii][i_sweep],
                        )

                    # Update data array
                    self.data["signal_raw"] = signal
                    self.data["reference_raw"] = reference
                    self.data["contrast_raw"] = contrast
                    self.data["pulse_durations"] = pulse_durations
                    self.data_ready = True

        finally:
            SRS.settings["output"] = False
            SRS.settings["modulation"] = False
            DAQ.end_task()

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

