'''
Created on Apr 19, 2022

@author: Benedikt Ursprung
'''
from ScopeFoundryHW.spincore import PulseProgramGenerator, PulseBlasterChannel, us, ns


class RabiPulseProgramGenerator(PulseProgramGenerator):

    name = 'rabi_pulse_generator'

    def setup_additional_settings(self) -> None:
        self.settings.New('t_uW', unit='ns', initial=200)
        self.settings.New('t_sig_readout', unit='us', initial=0.35)
        self.settings.New('t_ref_readout', unit='us', initial=200)
                
        self.settings.New('t_AOM_duration', unit='us', initial=210)
        self.settings.New('t_uW_to_AOM_delay', unit='us', initial=10.0, spinbox_decimals=3)
        #self.settings.New('program_duration', float, unit='us', initial=160.0)

        #self.settings['program_duration'] = 30  # in us
        self.settings.New('t_gate', unit='us', initial=0.5)
    def make_pulse_channels(self):
        S = self.settings
        t_uW = S['t_uW'] * ns
        t_AOM_duration = S['t_AOM_duration'] * us
        t_sig_readout = S['t_sig_readout'] * us
        t_ref_readout = S['t_ref_readout'] * us
        start_delay = 0  
        t_readout_duration = S['t_gate'] * us  
        t_uW_to_AOM_delay = S['t_uW_to_AOM_delay'] * us

        T_AOM_start = t_uW_to_AOM_delay + t_uW + start_delay
        print(T_AOM_start)

        self.new_channel('uW', [start_delay], [t_uW])
        self.new_channel('AOM', [T_AOM_start], [t_AOM_duration])
        self.new_channel('DAQ_sig', [T_AOM_start + t_sig_readout], [t_readout_duration])
        self.new_channel('DAQ_ref', [T_AOM_start + t_ref_readout], [t_readout_duration])
        self.settings['all_off_padding'] = t_uW_to_AOM_delay
        
    def make_pulse_channels_old(self):
        S = self.settings
        t_min = self.t_min

        t_AOM_duration = S['t_AOM_duration'] * us
        t_sig_readout = S['t_sig_readout'] * us
        t_ref_readout = S['t_ref_readout'] * us

        start_delay = 0  # t_min * round(1 * us / t_min) + t_readout_delay
        # t_startTrig = t_min * round(300 * ns / t_min)
        t_readout_duration = S['t_gate'] * us  # t_min * round(300 * ns / t_min)
        t_uW_to_AOM_delay = S['t_uW_to_AOM_delay'] * us
        print(t_uW_to_AOM_delay)

        #t_half = S['program_duration'] * us / 2
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
            

        #T = t_uW_to_AOM_delay + t_AOM + S['t_uW']
        T_AOM_start = t_uW_to_AOM_delay + S['t_uW']
        AOM = self.new_channel('AOM', [T_AOM_start], [t_AOM_duration])
        # DAQchannel = self.new_channel('DAQ', [t_half - t_AOM + t_readout_delay, 2 * t_half - t_AOM + t_readoutDelay], [t_readout, t_readout])
        # STARTtrigchannel = self.new_channel('STARTtrig', [0], [t_startTrig])

        DAQ_sig = self.new_channel(
            'DAQ_sig', [T_AOM_start + t_sig_readout], [t_readout_duration])
        DAQ_ref = self.new_channel(
            'DAQ_ref', [T_AOM_start + t_ref_readout], [t_readout_duration])
        
        dummy_channel = self.new_channel(
            'dummy_channel', [T_AOM_start + t_AOM_duration], [t_uW_to_AOM_delay])
       
        channels.extend([AOM, DAQ_sig, DAQ_ref, dummy_channel])
        return channels
