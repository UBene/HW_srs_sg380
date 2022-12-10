'''
Created on Apr 19, 2022

@author: Benedikt Ursprung
'''
from ScopeFoundryHW.spincore import PulseProgramGenerator, us, ns
from .pulses import makeXY8pulses

class XY8PulseProgramGenerator(PulseProgramGenerator):

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

    def make_pulse_channels(self):
        S = self.settings

        t_min = self.t_min

        t_gate = S['t_gate'] * us
        t_AOM = S['t_AOM'] * us
        t_delay = S['t_delay'] * us
        t_pi = S['t_pi'] * ns
        t_IQ_padding = S['t_IQ_padding'] * ns
        t_readout_delay = S['t_readout_delay'] * us

        t_piby2 = t_pi / 2
        uWtoAOM_delay = t_min * round(1 * us / t_min)
        start_delay = (t_min * round(1 * us / t_min) + S['t_readout_delay'])
        # Make pulses for signal half of the sequence:
        [uWstartTimes1, uWdurations, IstartTimes1, Idurations, QstartTimes1, Qdurations] = makeXY8pulses(
            start_delay, S['N_pi'], t_delay, t_pi, t_piby2, t_IQ_padding)
        XY8duration = uWstartTimes1[-1] + t_pi / 2 - start_delay
        AOMstartTime1 = start_delay + XY8duration + uWtoAOM_delay
        DAQstartTime1 = AOMstartTime1 + t_readout_delay
        firstHalfDuration = AOMstartTime1 + t_AOM
        # Make pulses for background half of the sequence:
        uWstartTimes2 = [x + firstHalfDuration for x in uWstartTimes1]
        QstartTimes2nd = QstartTimes1[:-1]
        QstartTimes2 = [x + firstHalfDuration for x in QstartTimes2nd]
        AOMstartTime2 = firstHalfDuration + AOMstartTime1
        DAQstartTime2 = firstHalfDuration + AOMstartTime1

        # Make channels:

        uW = self.new_channel('uW', uWstartTimes1 +
                              uWstartTimes2, uWdurations + uWdurations)
        AOM = self.new_channel(
            'AOM', [AOMstartTime1, AOMstartTime2], [t_AOM, t_AOM])
        I = self.new_channel('I', IstartTimes1, Idurations)
        Q = self.new_channel('Q', QstartTimes1 + QstartTimes2,
                             Qdurations + Qdurations[:-1])
        DAQ_sig = self.new_channel('DAQ_sig', [DAQstartTime1], [t_gate])
        DAQ_ref = self.new_channel('DAQ_ref', [DAQstartTime2], [t_gate])

        self.settings['program_duration'] = (
            max(AOMstartTime2 + t_AOM, DAQstartTime2 + t_gate)) / 1e3 + 1
        return [uW, AOM, I, Q, DAQ_sig, DAQ_ref]
