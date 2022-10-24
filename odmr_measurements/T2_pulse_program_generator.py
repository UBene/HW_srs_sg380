'''
Created on Apr 19, 2022

@author: Benedikt Ursprung
'''
from ScopeFoundryHW.spincore import PulseProgramGenerator, PulseBlasterChannel, us, ns


class T2PulseProgramGenerator(PulseProgramGenerator):

    def setup_additional_settings(self) -> None:
        self.settings.New('t_readout', unit='us', initial=0.35, spinbox_decimals=3)
        self.settings.New('t_gate', unit='us', initial=1.0)
        #self.settings.New('program_duration', float, unit='us', initial=160.0)
        #self.settings['program_duration'] = 27
        self.settings.New('tau', unit='us', initial=0.1, spinbox_decimals=3)
        self.settings.New('t_AOM_duration', unit='us', initial=250.0)
        #self.settings.New('t_readout_delay', unit='us', initial=2.3)
        self.settings.New('t_uW_to_AOM_delay', unit='us', initial=10.0)

        self.settings.New('t_pi', unit='ns', initial=60.0)
        self.settings.New('t_IQ_padding', unit='ns', initial=20.0)
        #self.settings.New('N_pi', int, initial=1)

    def make_pulse_channels(self) -> [PulseBlasterChannel]:
        S = self.settings

        t_min = self.t_min
        t_readout = S['t_readout'] * us

        # t_readout = S['t_readout'] * us

        t_gate = S['t_gate'] * us
        t_AOM_duration = S['t_AOM_duration'] * us
        tau = S['tau'] * us
        t_pi = S['t_pi'] * ns
        t_IQ_padding = S['t_IQ_padding'] * ns

        t_pi_half = t_pi / 2
        uWtoAOM_delay = S['t_uW_to_AOM_delay'] * us #t_min * round(1 * us / t_min)
        #start_delay = (t_min * round(1 * us / t_min) + t_readout_delay)
        # Make pulses for signal half of the sequence:
        #[uWstartTimes1, uWdurations, IstartTimes1, Idurations, QstartTimes1, Qdurations] = makeCPMGpulses(start_delay,
                                                                                                          #S['N_pi'],
                                                                                                          #t_delay,
                                                                                                          #t_pi,
                                                                                                          #t_piby2,
                                                                                                          #t_IQ_padding)
        #CPMGduration = uWstartTimes1[-1] + t_piby2 - start_delay
        #AOMstartTime1 = start_delay + CPMGduration + uWtoAOM_delay
        #firstHalfDuration = AOMstartTime1 + t_AOM
        # Make pulses for background half of the sequence:
        #uWstartTimes2 = [x + firstHalfDuration for x in uWstartTimes1]
        # IstartTimes2 = [x+firstHalfDuration for x in IstartTimes1]
        #QstartTimes2nd = QstartTimes1[:-1]
        #QstartTimes2 = [x + firstHalfDuration for x in QstartTimes2nd]
        #AOMstartTime2 = firstHalfDuration + AOMstartTime1
        # Make full uW, I and Q pulse lists
        # Make channels:
        
        #Start times
    
        pi_half_start_t_1 = uWtoAOM_delay
        pi_start_t_1 = pi_half_start_t_1 + t_pi_half + tau
        pi_half2_start_t_1 = pi_start_t_1 + t_pi + tau
        
        i_pi_start_t1 = pi_start_t_1 - t_IQ_padding
        i_pi_half_start_t1 = pi_half2_start_t_1 - t_IQ_padding
        
        q_pi_half_start_t1 = i_pi_half_start_t1
        
        aom_start_t1 = pi_half2_start_t_1 + t_pi_half + uWtoAOM_delay 
        sig_readout_t = aom_start_t1 + t_readout
        
        pi_half_start_t_2 = aom_start_t1 + t_AOM_duration + uWtoAOM_delay
        pi_start_t_2 = pi_half_start_t_2 + t_pi_half + tau
        pi_half2_start_t_2 = pi_start_t_2 + t_pi + tau
        
        i_pi_start_t2 = pi_start_t_2 - t_IQ_padding
        
        aom_start_t2 = pi_half2_start_t_2 + t_pi_half + uWtoAOM_delay 
        ref_readout_t = aom_start_t2 + t_readout
        
        #Durations
        i_q_pi_duration = t_pi + (2 * t_IQ_padding)
        i_q_pi_half_duration = t_pi_half + (2 * t_IQ_padding)
        
        
        #uWstartTimes1 = []
        uW = self.new_channel('uW', [pi_half_start_t_1, pi_start_t_1, pi_half2_start_t_1, pi_half_start_t_2, pi_start_t_2, pi_half2_start_t_2],
                              [t_pi_half, t_pi, t_pi_half, t_pi_half, t_pi, t_pi_half])
        AOM = self.new_channel('AOM', [aom_start_t1, aom_start_t2], [t_AOM_duration, t_AOM_duration])
        I = self.new_channel('I', [i_pi_start_t1, i_pi_half_start_t1, i_pi_start_t2], [i_q_pi_duration, i_q_pi_half_duration, i_q_pi_duration])
        Q = self.new_channel('Q', [q_pi_half_start_t1],[i_q_pi_half_duration])
        DAQ_sig = self.new_channel('DAQ_sig', [sig_readout_t], [t_gate])
        DAQ_ref = self.new_channel('DAQ_ref', [ref_readout_t], [t_gate])

        #self.settings['program_duration'] = (
            #AOMstartTime2 + max(t_AOM, t_gate)) / 1e3 + 1
        return [uW, AOM, I, Q, DAQ_sig, DAQ_ref]
