'''
Created on Apr 19, 2022

@author: Benedikt Ursprung
'''
from ScopeFoundryHW.spincore import PulseProgramGenerator, PulseBlasterChannel, us, ns
from .pulses import makeCPMGpulses


class T2PulseProgramGenerator(PulseProgramGenerator):

    def setup_additional_settings(self) -> None:
        self.settings.New('t_readout', unit='us', initial=10.0)
        self.settings.New('t_gate', unit='us', initial=5.0)
        self.settings.New('program_duration', float, unit='us', initial=160.0)
        self.settings['program_duration'] = 27
        self.settings.New('t_delay', unit='us', initial=1.0)
        self.settings.New('t_AOM', unit='us', initial=5.0)
        self.settings.New('t_readout_delay', unit='us', initial=2.3)
        self.settings.New('t_pi', unit='ns', initial=24.0)
        self.settings.New('t_IQ_padding', unit='ns', initial=30.0)
        self.settings.New('N_pi', int, initial=1)

    def make_pulse_channels(self) -> [PulseBlasterChannel]:
        S = self.settings

        t_min = self.t_min
        t_readout_delay = S['t_readout_delay'] * us

        # t_readout = S['t_readout'] * us

        t_gate = S['t_gate'] * us
        t_AOM = S['t_AOM'] * us
        t_delay = S['t_delay'] * us
        t_pi = S['t_pi'] * ns
        t_IQ_padding = S['t_IQ_padding'] * ns

        t_piby2 = t_pi / 2
        uWtoAOM_delay = t_min * round(1 * us / t_min)
        start_delay = (t_min * round(1 * us / t_min) + t_readout_delay)
        # Make pulses for signal half of the sequence:
        [uWstartTimes1, uWdurations, IstartTimes1, Idurations, QstartTimes1, Qdurations] = makeCPMGpulses(start_delay,
                                                                                                          S['N_pi'],
                                                                                                          t_delay,
                                                                                                          t_pi,
                                                                                                          t_piby2,
                                                                                                          t_IQ_padding)
        CPMGduration = uWstartTimes1[-1] + t_piby2 - start_delay
        AOMstartTime1 = start_delay + CPMGduration + uWtoAOM_delay
        firstHalfDuration = AOMstartTime1 + t_AOM
        # Make pulses for background half of the sequence:
        uWstartTimes2 = [x + firstHalfDuration for x in uWstartTimes1]
        # IstartTimes2 = [x+firstHalfDuration for x in IstartTimes1]
        QstartTimes2nd = QstartTimes1[:-1]
        QstartTimes2 = [x + firstHalfDuration for x in QstartTimes2nd]
        AOMstartTime2 = firstHalfDuration + AOMstartTime1
        # Make full uW, I and Q pulse lists
        # Make channels:
        uW = self.new_channel('uW', uWstartTimes1 +
                              uWstartTimes2, uWdurations + uWdurations)
        AOM = self.new_channel(
            'AOM', [AOMstartTime1, AOMstartTime2], [t_AOM, t_AOM])
        I = self.new_channel('I', IstartTimes1, Idurations)
        Q = self.new_channel('Q', QstartTimes1 + QstartTimes2,
                             Qdurations + Qdurations[:-1])
        DAQ_sig = self.new_channel('DAQ_sig', [AOMstartTime1], [t_gate])
        DAQ_ref = self.new_channel('DAQ_ref', [AOMstartTime2], [t_gate])

        self.settings['program_duration'] = (
            AOMstartTime2 + max(t_AOM, t_gate)) / 1e3 + 1
        return [uW, AOM, I, Q, DAQ_sig, DAQ_ref]
