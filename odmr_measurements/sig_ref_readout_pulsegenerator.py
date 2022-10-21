'''
Created on Apr 19, 2022

@author: Benedikt Ursprung
'''
import numpy as np
from ScopeFoundryHW.spincore import PulseProgramGenerator, PulseBlasterChannel, us


class SigRefReadoutProgramGenerator(PulseProgramGenerator):

    name = 'sig_ref_readout_pulse_generator'

    def setup_additional_settings(self) -> None:
        self.settings.New('t_readout_sig', unit='us', initial=0.0)
        self.settings.New('t_readout_ref', unit='us', initial=50.0)

        self.settings.New('t_gate', unit='us', initial=50.0)


    def make_pulse_channels(self) -> [PulseBlasterChannel]:
        S = self.settings
        #t_min = self.t_min
        
        t_readout_sig = S['t_readout_sig'] * us
        #t_readout_ref = S['t_readout_ref'] * us
        t_gate = S['t_gate'] * us

        
        base_tick_freq = 2.5 #in MHz
        base_tick_period = (1.0/base_tick_freq) * us

        total_periods = 600
        periods_10MHz = (total_periods/3) * 4
        times_10MHz = np.arange(periods_10MHz) * (base_tick_period / 4)
        time_5_MHz_start = np.copy(times_10MHz[len(times_10MHz) - 1]) + base_tick_period / 4

        periods_5MHz = (total_periods/3) * 2
        times_5MHz = np.arange(periods_5MHz) * (base_tick_period / 2) + time_5_MHz_start
        time_2_5_MHz_start = np.copy(times_5MHz[len(times_5MHz) - 1]) + base_tick_period / 2

        times_2_5MHz = np.copy(np.arange(total_periods/3) * (base_tick_period) + time_2_5_MHz_start)

        pulses_10MHz = np.ones(len(times_10MHz))*0.5*base_tick_period/4
        pulses_5MHz = np.ones(len(times_5MHz))*0.5*base_tick_period/2
        pulses_2_5MHz = np.ones(len(times_2_5MHz))*0.5* base_tick_period

        uW_times = np.concatenate((times_10MHz, times_5MHz, times_2_5MHz))
        uW_pulses = np.concatenate((pulses_10MHz, pulses_5MHz, pulses_2_5MHz))
        
        
        uWchannel = self.new_channel('uW', uW_times, uW_pulses)
        
        #t_AOM = S['t_AOM'] * us
        #t_readout_delay = S['t_readout_delay'] * us

        #start_delay = 0  # t_min * round(1 * us / t_min) + t_readout_delay
        # t_startTrig = t_min * round(300 * ns / t_min)
        #t_readout = S['t_gate'] * us  # t_min * round(300 * ns / t_min)

        channels = [uWchannel]
        # DAQchannel = self.new_channel('DAQ', [t_half - t_AOM + t_readout_delay, 2 * t_half - t_AOM + t_readoutDelay], [t_readout, t_readout])
        # STARTtrigchannel = self.new_channel('STARTtrig', [0], [t_startTrig])

        
        DAQ_sig = self.new_channel(
            'DAQ_sig', [t_readout_sig], [t_gate])
        DAQ_ref = self.new_channel(
            'DAQ_ref', [S['t_readout_ref'] * us], [t_gate])
        channels.extend([DAQ_sig, DAQ_ref])
        return channels
