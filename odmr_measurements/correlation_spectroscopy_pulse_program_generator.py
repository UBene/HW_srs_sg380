'''
Created on Apr 19, 2022

@author: Benedikt Ursprung
'''
from ScopeFoundryHW.spincore import PulseProgramGenerator, us, ns
from .pulses import makeXY8pulses


class CSPulseProgramGenerator(PulseProgramGenerator):

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
        self.settings.New('tau0', unit='ns', initial=1500,
                          description='Delay between pi-pulses in the XY8 pulse sequences')

    def make_pulse_channels(self):
        S = self.settings

        t_min = self.t_min

        t_gate = S['t_gate'] * us
        t_AOM = S['t_AOM'] * us
        t_delay = S['t_delay'] * us
        t_pi = S['t_pi'] * ns
        t_IQ_padding = S['t_IQ_padding'] * ns
        t_readout_delay = S['t_readout_delay'] * us
        tau0 = S['tau0']

        t_piby2 = t_pi / 2
        uWtoAOM_delay = t_min * round(1 * us / t_min)
        start_delay = t_min * round(2 * us / t_min)
        # Make pulses for first XY8 in the first half of the sequence (I only
        # pulses in second XY8 of second half, so we will take the I times here
        # and shift them in time):
        [uWstartTimes1a, uWdurations1a, IstartTimes, Idurations, QstartTimes1a,
            Qdurations1a] = makeXY8pulses(start_delay, S['N_pi'], t_delay, t_pi, t_piby2, t_IQ_padding)
        # Make pulses for second XY8 in the first half of the sequence:
        firstXY8duration = uWstartTimes1a[-1] + t_piby2
        uWstartTimes1b = [x + firstXY8duration + tau0 for x in uWstartTimes1a]
        QstartTimes1b = [x + firstXY8duration + tau0 for x in QstartTimes1a]
        Qdurations1b = Qdurations1a
        # Make AOM pulse and DAQ pulse for signal half
        XY8duration = uWstartTimes1b[-1] + t_pi / 2 - start_delay
        AOMstartTime1 = start_delay + XY8duration + uWtoAOM_delay
        DAQstartTime1 = AOMstartTime1 + t_readout_delay
        firstHalfDuration = AOMstartTime1 + t_AOM

        # Make pulses for first XY8 in the second half of the sequence (no I's
        # on this half):
        uWstartTimes2 = [
            x + firstHalfDuration for x in uWstartTimes1a + uWstartTimes1b]
        QstartTimes2 = [
            x + firstHalfDuration for x in QstartTimes1a + QstartTimes1b[:-1]]
        AOMstartTime2 = firstHalfDuration + AOMstartTime1
        DAQstartTime2 = firstHalfDuration + DAQstartTime1
        IstartTimes = [x + firstHalfDuration +
                       firstXY8duration + tau0 for x in IstartTimes]

        # concatenate pulse times:
        uWstartTimes = uWstartTimes1a + uWstartTimes1b + uWstartTimes2
        uWdurations = uWdurations1a * 4
        QstartTimes = QstartTimes1a + QstartTimes1b + QstartTimes2
        Qdurations = Qdurations1a + Qdurations1b + \
            Qdurations1a + Qdurations1b[:-1]

        # Make channels:
        self.new_channel('uW', uWstartTimes, uWdurations)
        self.new_channel(
            'AOM', [AOMstartTime1, AOMstartTime2], [t_AOM, t_AOM])
        self.new_channel('I', IstartTimes, Idurations)
        self.new_channel('Q', QstartTimes, Qdurations)
        self.new_channel('DAQ_sig', [DAQstartTime1], [t_gate])
        self.new_channel('DAQ_ref', [DAQstartTime2], [t_gate])

        self.settings['program_duration'] = max(
            AOMstartTime2 + t_AOM, DAQstartTime2 + t_gate) / 1e3 + 1
