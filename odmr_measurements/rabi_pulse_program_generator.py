'''
Created on Apr 19, 2022

@author: Benedikt Ursprung
'''
from ScopeFoundryHW.spincore import PulseProgramGenerator, PulseBlasterChannel, us


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
            shortPulseChannel = self.new_one_period_channel(
                int(S['t_uW'] / 2), [start_delay], [5 * t_min])
            # Short pulse feature
            channels = [shortPulseChannel, uWchannel]
        else:
            uWchannel = self.new_channel('uW', [start_delay], [S['t_uW']])
            channels = [uWchannel]

        T = t_uW_to_AOM_delay + t_AOM + S['t_uW']
        AOM = self.new_channel('AOM', [T, t_half + T], [t_AOM, t_AOM])
        # DAQchannel = self.new_channel('DAQ', [t_half - t_AOM + t_readout_delay, 2 * t_half - t_AOM + t_readoutDelay], [t_readout, t_readout])
        # STARTtrigchannel = self.new_channel('STARTtrig', [0], [t_startTrig])

        DAQ_sig = self.new_channel(
            'DAQ_sig', [T + t_AOM + t_readout_delay], [t_readout])
        DAQ_ref = self.new_channel(
            'DAQ_ref', [t_half + T + t_AOM + t_readout_delay], [t_readout])

        channels.extend([AOM, DAQ_sig, DAQ_ref])
        return channels
