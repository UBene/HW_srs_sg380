'''
Created on Aug 13, 2021

@author: Benedikt Ursprung

Some functions to set the waveforms on a Rigol RigolDG1000Z series (tested on DG1022Z):
'''
from threading import Lock
import pyvisa

RIGOL_WAVEFORMS = ['PULSe',  # Fully supported 
                   'DC',  # supported
                   
                   'ARBitrary',
                   'HARMonic',
                   'NOISe',
                   'RAMP',
                   'SINusoid',
                   'USER',
                   'SQUare',
                   'TRIangle'
                   ]


class RigolDG1000Z:
    
    def __init__(self, port="USB0::0x1AB1::0x0642::DG1ZA204405136::INSTR", debug=False):
    
        self.port = port
        self.debug = debug
        self.lock = Lock()
        
        self.visa_resource_manager = pyvisa.ResourceManager()
        
        if debug: print('Visa devices detected:', self.visa_resource_manager.list_resources())

        print(port)
        self.RigolDG1000Z = self.visa_resource_manager.get_instrument(port)
        self.RigolDG1000Z.timeout = 100
        
    def ask(self, cmd):
        if self.debug: print("RigolDG1000Z ask " + repr(cmd))
        with self.lock:
            try:
                resp = self.RigolDG1000Z.query(cmd) 
            except:
                resp = self.RigolDG1000Z.ask(cmd)  # Deprecated pyvisa method --> replaced by query()
            
        if self.debug: print("RigolDG1000Z resp ---> " + repr(resp))
        return resp.rstrip('\n')
    
    def write(self, cmd):
        with self.lock:
            self.RigolDG1000Z.write(cmd)
                
    def read_output_on(self, chan=1):
        r = self.ask(f':OUTP{chan}?')
        return {'ON':True, 'OFF':False}[r]
            
    def write_output_on(self, chan=1, on=True):
        on = {True:'ON', False:'OFF'}[on]
        self.write(f':OUTP{chan} {on}')
                
    def write_pulse_width(self, chan=1, width=1):
        self.write(f':SOUR{chan}:FUNC:PULS:WIDT {width}')
        
    def read_pulse_width(self, chan=1):
        return self.ask(f':SOUR{chan}:FUNC:PULS:WIDT?')
    
    def write_pulse_period(self, chan=1, period=1):
        self.write(f':SOUR{chan}:FUNC:PULS:PER {period}')
        
    def read_pulse_period(self, chan=1):
        resp = self.ask(f':SOUR{chan}:FUNC:PULS:PER?')
        return float(self.ask(f':SOUR{chan}:FUNC:PULS:PER?'))  
                
    def write_volt_amplitude(self, chan=1, Vpp=1):
        self.write(f':SOUR{chan}:VOLT:AMPL {Vpp}')        
        
    def read_volt_amplitude(self, chan=1):
        return self.ask(f':SOUR{chan}:VOLT:AMPL?')
        
    def write_volt_level(self, chan=1, Vpp=1):
        self.write(f':SOUR{chan}:VOLT:LEV {Vpp}')        
        
    def read_volt_level(self, chan=1):
        return self.ask(f':SOUR{chan}:VOLT:LEV?')        
        
    def write_volt_offset(self, chan=1, V=1):
        self.write(f':SOUR{chan}:VOLT:OFFS {V}')        
        
    def read_volt_offset(self, chan=1):
        return self.ask(f':SOUR{chan}:VOLT:OFFS?')
    
    def write_volt_DC(self, chan=1, VDC=1):
        # 1,1 are placeholders for Frequency and amplitude
        cmd = f':SOUR{chan}:APPL:DC 1,1,{VDC}'
        self.write(cmd)
        
    def read_volt_DC(self, chan=1):
        resp = self.read_apply(chan).split(',')
        return float(resp[-1])

    def read_apply(self, chan=1):
        '''Query the waveform type as well as the frequency, amplitude, offset and phase of the
        specified channel. See also self.read_waveform'''
        return self.ask(f'SOUR{chan}:APPL?').strip('"')
    
    def write_waveform(self, chan=1, waveform='PULSe'):
        assert(waveform in RIGOL_WAVEFORMS, 'not a valid Rigol waveform')
        self.write(f':SOURce{chan}:APPLy:{waveform}')
                                
    def read_waveform(self, chan=1):
        return self.read_apply(chan=1).split(',')[0]

