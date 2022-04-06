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
from odmr_measurements.pulse_program_generator import PulseProgramGenerator
from odmr_measurements.helper_functions import ContrastModes, calculateContrast
from spinapi.spinapi import us, ns


class RabiPulseProgramGenerator(PulseProgramGenerator):

    def setup_settings(self):
        self.settings.New('t_uW', unit='ns', initial=200)
        self.settings.New('t_readoutDelay', unit='us', initial=2.3)
        self.settings.New('t_AOM', unit='us', initial=2.0)
    
    def make_pulse_channels(self):
        S = self.settings
        t_min = self.t_min
        
        t_AOM = S['t_AOM'] * us
        t_readoutDelay = S['t_readoutDelay'] * us
        
        start_delay = t_min * round(1 * us / t_min) + t_readoutDelay
        t_startTrig = t_min * round(300 * ns / t_min)
        t_readout = t_min * round(300 * ns / t_min)
        uWtoAOM_delay = t_min * round(1 * us / t_min)    
        firstHalfDuration = start_delay + S['t_uW'] + uWtoAOM_delay + t_AOM
        if S['t_uW'] <= 5 * t_min and S['t_uW'] > 0: 
            # For microwave pulses < 5 * t_min, the microwave channel (PB_MW) is instructed 
            # to pulse for 5 * t_min, but the short-pulse flags of the PB are pulsed 
            # simultaneously (shown in white) to the desired output pulse length at uW. 
            # This can be verified on an oscilloscope.          
            uWchannel = self.new_channel('uW', [start_delay], [5 * t_min])
            shortPulseChannel = self.new_one_period_channel(int(S['t_uW'] / 2), [start_delay], [5 * t_min])
            channels = [shortPulseChannel, uWchannel]  # Short pulse feature
        else:
            uWchannel = self.new_channel('uW', [start_delay], [S['t_uW']])
            channels = [uWchannel]
        AOMchannel = self.new_channel('AOM', [firstHalfDuration - t_AOM, 2 * firstHalfDuration - t_AOM], [t_AOM, t_AOM])
        DAQchannel = self.new_channel('DAQ', [firstHalfDuration - t_AOM + t_readoutDelay, 2 * firstHalfDuration - t_AOM + t_readoutDelay], [t_readout, t_readout])
        STARTtrigchannel = self.new_channel('STARTtrig', [0], [t_startTrig])
        channels.extend([AOMchannel, DAQchannel, STARTtrigchannel])
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

        S.New("Nsamples", int, initial=1000, description='Number of samples per frequency per sweep')
        S.New("Navg", int, initial=1, description='Number of sweeps')
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
        settings_layout.addWidget(self.pulse_duration_range.New_UI())
        settings_layout.addWidget(self.settings.New_UI(include=["contrast_mode", "Nsamples",
                                                                "Navg", "randomize", "save_h5"], style='form'))
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
        self.i_run = 0
        
        self.ui.addDock(dock=self.pulse_generator.make_dock(), position='right')
        
    def update_display(self):
        if self.data_ready:
            for name in ["signal_raw", "reference_raw", "contrast_raw"]:
                x = self.data["pulse_durations"] / 1e9
                y = self.data[name][:, 0:self.i_run + 1].mean(-1)
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
            DAQ.restart(2 * S['Nsamples'])
            
            N_freqs = len(pulse_durations)
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
                        shuffle(pulse_durations)
                index = np.argsort(pulse_durations)
                
                for i_scanPoint in range(N_freqs):
                    pct = 100 * (i_run * N_freqs + i_scanPoint) / (Navg * N_freqs)
                    self.set_progress(pct)
                    if self.interrupt_measurement_called:
                        break
                    
                    # SRS.settings["frequency"] = pulse_durations[i_scanPoint]
                    self.set_pulse_duration(pulse_durations[i_scanPoint])
                    
                    print("Scan point ", i_scanPoint + 1, " of ", N_freqs)
                    time.sleep(0.01)

                    cts = np.array(DAQ.read_counts(2 * S['Nsamples']))
                    ref = np.sum(cts[1::2] - cts[0::2])
                    sig = np.sum(cts[2::2] - cts[1:-2:2]) + cts[0]                 
                    
                    # print(cts[0::4].mean(), cts[1::4].mean(), cts[2::4].mean(), cts[3::4].mean(),)
                    # print(cts[:8])
                    # sig = cts[1::4] - cts[0::4]
                    # ref = cts[3::4] - cts[2::4]
                    
                    print(sig.sum(), ref.sum())
                    ii = index[i_scanPoint]
                    signal[ii][i_run] = sig
                    reference[ii][i_run] = ref
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

