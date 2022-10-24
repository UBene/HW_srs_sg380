import random, math, platform
import logger
from prologix_usb_gpib import prologix_usb_gpib_dev as gpibdev

#import dummy_visa
#try:
#    import pyvisa as visa
#except ImportError:
#    try: import gpib_visa as visa
#    except:
#        logger.write('WARNING : error loading visa module, using dummy_visa instead!')
#        visa = dummy_visa

float_tolerance = 1E-2

class SRSlockin(object):
    def __init__(self, port="/dev/ttyUSB1", gpibaddr=8, input=None, time_constant=None,
        sensitivity=None, reserve_mode=None, debug=False):
        #if platform.system() == 'Windows': name = 'GPIB::8'
        
	self.gpibdev = gpibdev(port=port, addr=gpibaddr,debug=debug)

        self.lockin_init = False
        #self.name = name
        self.debug = debug
        
        #if not self.debug:
        #    self.lockin = visa.instrument(self.name)
        #else:
        #    self.lockin = dummy_visa.instrument(self.name)
        #lockin = self.lockin

	        

	# restore GPIB defaults
        #lockin.write('*RST')
        
        # query device ID, check for response
        id = self.gpibdev.ask('*IDN?')
        if debug:
		print "lockin id:", id
        if id == '':
            print 'SRSlockin.init failed!'
            self.lockin_init = False
            return
        
        # see page 9 for summary of commands
        # sets the output interface to GPIB
        self.gpibdev.write('OUTX 1')
        
        # set reference source to external (0=external, 1=internal)
        #lockin.write('FMOD 0')
        # query reference frequency
        freq = float(self.gpibdev.ask('FREQ?'))
        #print 'lockin reference freq = %gHz' % (freq)
        
        # to query measured value, use 'OUTP? 3' (1=X, 2=Y, 3=R, 4=theta), returns ASCII floats with units of volts or degrees (p.89 of manual)
        # can also use 'SNAP? i,j{k,l,m,n}' (1=X, 2=Y, 3=R, 4=theta, 5=AuxIn1, 6=AuxIn2, 7=AuxIn3, 8=AuxIn4, 9=RefFreq, 10=Ch1Disp) (p. 89 of manual)
        self.lockin_init = True
        
        if input:
            self.set_input_configuration(input)
        if time_constant:
            self.set_time_constant(time_constant)
        if sensitivity:
            self.set_sensitivity(sensitivity)
        if reserve_mode:
            self.set_reserve_mode(reserve_mode)
    
    def start(self): pass
    def stop(self): pass
    
    input_configurations = ['A', 'A-B', 'I (1MOhm)', 'I (100MOhm)']
    def get_input_configurations(self): return self.input_configurations
    
    def get_input_configuration(self):
        input_config = self.gpibdev.ask('ISRC?')
        try:
            i = int(input_config)
        except ValueError:
            logger.write('bad input_config response from lockin : "%s", expecting int' % input_config)
            i = 0
        return self.input_configurations[i]
    
    def set_input_configuration(self, input_config):
        try: input_config = self.input_configurations.index(input_config)
        except ValueError: return False
        self.gpibdev.write('ISRC %d' % input_config)
        if input_config == self.get_input_configuration(): return True
        return False
    
    def get_signal(self):
        # query R (phase independent)
        # OUTP? i  :   i=1 --> X, 2 --> Y, 3 --> R, 4 --> theta
        signal = self.gpibdev.ask('OUTP? 3')
        try: return float(signal)
        except ValueError: return -1
    
    def get_X_signal(self):
        # query X (phase dependent)
        # OUTP? i  :   i=1 --> X, 2 --> Y, 3 --> R, 4 --> theta
        signal = self.gpibdev.ask('OUTP? 1')
        try: return float(signal)
        except ValueError: return -1
    
    def get_frequency(self):
        freq = self.gpibdev.ask('FREQ?')
        try: freq = float(freq)
        except ValueError: return -1
        return freq
    
    def set_frequency(self, freq):
        self.gpibdev.write('FMOD %g' % freq)
        current_freq = self.get_frequency()
        if abs(freq - current_freq) > float_tolerance: return False
        return True
    
    def get_phase(self):
        phase = self.gpibdev.ask('PHAS?')
        try: phase = float(phase)
        except ValueError: return -1
        return phase
    
    def set_phase(self, phase):
        self.gpibdev.write('PHAS %g' % phase)
        current_phase = self.get_phase()
        if abs(phase - current_phase) > float_tolerance: return False
        return True
    
    def auto_phase(self):
        self.gpibdev.write('APHS')
        status = 0
        counter = 0
        while not(status) and counter < 100:
            status = int(self.gpibdev.ask('*STB? 1'))
            counter += 1
        if status: return True
        return False
    
    sensitivities = [
        '2nV/fA', '5nV/fA', '10nV/fA', '20nV/fA', '50nV/fA', '100nV/fA', '200nV/fA', '500nV/fA', 
        '1uV/pA', '2uV/pA', '5uV/pA', '10uV/pA', '20uV/pA', '50uV/pA', '100uV/pA', '200uV/pA', '500uV/pA',
        '1mV/nA', '2mV/nA', '5mV/nA', '10mV/nA', '20mV/nA', '50mV/nA', '100mV/nA', '200mV/nA', '500mV/nA',
        '1V/uA'
    ]
    Vsensitivities = [
        2E-9, 5E-9, 10E-9, 20E-9, 50E-9, 100E-9, 200E-9, 500E-9,
        1E-6, 2E-6, 5E-6, 10E-6, 20E-6, 50E-6, 100E-6, 200E-6, 500E-6,
        1E-3, 2E-3, 5E-3, 10E-3, 20E-3, 50E-3, 100E-3, 200E-3, 500E-3,
        1.0
    ]
    Isensitivities = [Vs * 1E-6 for Vs in Vsensitivities] # scale by 1E-6 to go from voltage -> current
    def get_sensitivity(self, float=False):
        sensitivity = self.gpibdev.ask('SENS?')
        try:
            i = int(sensitivity)
            self.sensitivity_index = i
        except ValueError:
            logger.write('bad sensitivity response from lockin : "%s", expecting int' % sensitivity)
            i = 0
        if float:
            input_config = self.get_input_configuration()
            if input_config.startswith('I'):
                self.sensitivity = self.Isensitivities[i]
            else: 
                self.sensitivity = self.Vsensitivities[i]
        else:
            self.sensitivity = self.sensitivities[i]
        return self.sensitivity
    
    def set_sensitivity(self, sensitivity):
        try: self.sensitivity_index = self.sensitivities.index(sensitivity)
        except ValueError: return False
        self.gpibdev.write('SENS %d' % self.sensitivity_index)
        read_sensitivity = self.get_sensitivity()
        if sensitivity == read_sensitivity:
            self.sensitivity = read_sensitivity
            return True
        return False
    
    def auto_sensitivity(self):
        changed = True
        while changed:
            signal = self.get_signal()
            sensitivity = self.get_sensitivity(float=True)
            
            input_config = self.get_input_configuration()
            if input_config.startswith('I'): isens = self.Isensitivities.index(sensitivity)
            else: isens = self.Vsensitivities.index(sensitivity)
            
            #print 'srs.auto_sensitivity : signal = %g, sensitivity = %g, isens = %d' % (signal, sensitivity, isens)
            if signal < 0.1*sensitivity and isens > 0:
                self.set_sensitivity(self.sensitivities[isens-1])
            elif signal > 0.4*sensitivity and isens < len(self.sensitivities)-1:
                self.set_sensitivity(self.sensitivities[isens+1])
            else:
                changed = False
        return changed
    
    def auto_sensitivity_quick(self):
        #Assume A (Voltage) input, uses self.sensitivity instead of get_sensitivity
        changed = True
        while changed:
            signal = self.get_signal()
            if not hasattr(self, 'sensitivity'):
                self.sensitivity = self.get_sensitivity(float=True)
            sensitivity = self.sensitivity #self.get_sensitivity(float=True)
            
            #input_config = self.get_input_configuration()
            #if input_config.startswith('I'): isens = self.Isensitivities.index(sensitivity)
            #else:
            isens = self.Vsensitivities.index(sensitivity)
            
            #print 'srs.auto_sensitivity : signal = %g, sensitivity = %g, isens = %d' % (signal, sensitivity, isens)
            if signal < 0.1*sensitivity and isens > 0:
                self.set_sensitivity(self.sensitivities[isens-1])
            elif signal > 0.9*sensitivity and isens < len(self.sensitivities)-1:
                self.set_sensitivity(self.sensitivities[isens+1])
            else:
                changed = False
        return
    
    def auto_gain(self):
        self.gpibdev.write('AGAN')
        status = 0
        counter = 0
        while not(status) and counter < 100:
            status = int(self.gpibdev.ask('*STB? 1'))
            counter += 1
        if status: return True
        return False
    
    time_constants = [
        '10us', '30us', '100us', '300us', '1ms', '3ms', '10ms', '30ms', '100ms', '300ms',
        '1s', '3s', '10s', '30s', '100s', '300s', '1ks', '3ks', '10ks', '30ks'
    ]
    ftime_constants = [
        10E-6, 30E-6, 100E-6, 300E-6, 1E-3, 3E-3, 10E-3, 30E-3, 100E-3, 300E-3,
        1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1E3, 3E3, 10E3, 30E3
    ]
    def get_time_constant(self):
        time_constant_id = self.gpibdev.ask('OFLT?')
        try:
            i = int(time_constant_id)
        except ValueError:
            logger.write('bad time_constant response from lockin : "%s", expecting int' % time_constant_id)
            return None
        return self.time_constants[i]
    
    def set_time_constant(self, time_constant):
        if time_constant in self.time_constants:
            time_constant_id = self.time_constants.index(time_constant)
        elif time_constant in self.ftime_constants:
            time_constant_id = self.ftime_constants.index(time_constant)
        else:
            return False
        
        self.gpibdev.write('OFLT %d' % time_constant_id)
        if self.time_constants[time_constant_id] == self.get_time_constant():
            return True
        return False
    
    reserve_modes = ['high reserve', 'normal', 'low noise']
    def get_reserve_mode(self):
        index = self.gpibdev.ask('RMOD?')
        try:
            index = int(index)
        except ValueError:
            logger.write('bad reserve mode response from lockin : "%s", expected int' % index)
            return None
        return self.reserve_modes[index]
    
    def set_reserve_mode(self, reserve_mode):
        reserve_mode = reserve_mode.lower()
        if reserve_mode not in self.reserve_modes:
            logger.write('given bad reserve mode : "%s"' % reserve_mode)
            return False
        
        index = self.reserve_modes.index(reserve_mode)
        self.gpibdev.write('RMOD %d' % index)
        if self.reserve_modes[index] == self.get_reserve_mode():
            return True
        return False
    
    def get_ainput(self, channel):
        channel = int(channel)
        channel = max(1, min(4, channel))
        value = self.gpibdev.ask('OAUX? %d' % channel)
        
        try: return float(value)
        except ValueError: return -1
        return -1
    
    def set_aoutput(self, channel, value):
        channel = int(channel)
        channel = max(1, min(4, channel))
        value = float(value)
        value = min(10.0, value)
        value = max(-10.0, value)
        
        self.gpibdev.write('AUXV %d, %g' % (channel, value))
        
        return self.get_aoutput(channel)
    
    def get_aoutput(self, channel):
        channel = int(channel)
        channel = max(1, min(4, channel))
        value = self.gpibdev.ask('AUXV? %d' % channel)
        
        try: return float(value)
        except ValueError: return -1
        return -1
    
    def status(self):
        d = {}
        d['frequency'] = self.get_frequency()
        d['time_constant'] = self.get_time_constant()
        d['sensitivity'] = self.get_sensitivity()
        d['input configuration'] = self.get_input_configuration()
        d['reserve mode'] = self.get_reserve_mode()
        return d
    
    def close(self):
        self.stop()
        if self.lockin_init:
            self.gpibdev.ser.close()

if __name__ == '__main__':
    lockin = SRSlockin(port="COM12", debug=True)
    lockin.start()
    print 'frequency = %gHz' % lockin.get_frequency()
    print 'time constant = %s' % lockin.get_time_constant()
    print 'sensitivity = %s' % lockin.get_sensitivity()
    print 'signal = %gV' % lockin.get_signal()
    
    import time
    for i in range(100):
        #print i, lockin.set_aoutput(1, i % 2)
        #time.sleep(0.5)
        print i, lockin.get_signal()
        #9time.sleep(0.5)
        
    lockin.close()
