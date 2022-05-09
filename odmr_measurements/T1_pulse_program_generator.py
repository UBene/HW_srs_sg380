'''
Created on Apr 19, 2022

@author: Benedikt Ursprung
'''
from ScopeFoundryHW.spincore import PulseProgramGenerator, PulseBlasterChannel, us, ns


class T1PulseProgramGenerator(PulseProgramGenerator):

    def setup_additional_settings(self) -> None:
        self.settings.New('t_readout', unit='us', initial=10.0)
        self.settings.New('t_gate', unit='us', initial=50.0)

        # self.settings.New('t_delay', unit='us', initial=50.0)
        self.settings.New('t_AOM', unit='us', initial=5.0)
        self.settings.New('t_readout_delay', unit='us', initial=2.3)
        self.settings.New('t_pi_pulse', unit='ns', initial=24.0)

    def make_pulse_channels(self) -> [PulseBlasterChannel]:
        S = self.settings

        t_min = self.t_min
        t_half = S['program_duration'] * us / 2
        t_readout_delay = S['t_readout_delay'] * us

        # t_readout = S['t_readout'] * us
        t_readout = t_min

        t_gate = S['t_gate'] * us
        t_AOM = S['t_AOM'] * us
        t_delay = 0  # S['t_delay'] * us
        t_pi_pulse = S['t_pi_pulse'] * ns

        AOMstartTime1 = t_delay
        AOMstartTime2 = t_half + t_delay

        AOM = self.new_channel(
            'AOM', [AOMstartTime1, AOMstartTime2], [t_AOM, t_AOM])
        uW = self.new_channel(
            'uW', [t_half + t_readout_delay + 1 * us], [t_pi_pulse])

        # DAQ
        _readout = t_readout + t_gate

        DAQ_sig = self.new_channel(
            'DAQ_sig', [AOMstartTime1 + t_readout_delay], [t_gate])
        DAQ_ref = self.new_channel(
            'DAQ_ref', [AOMstartTime2 + t_readout_delay], [t_gate])

        return [uW, AOM, DAQ_sig, DAQ_ref]
