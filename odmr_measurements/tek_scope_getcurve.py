import pyvisa
import numpy as np
from struct import unpack
from threading import Lock

class TekScope:
    
    def __init__(self, port, debug=False):
    
        self.port = port
        self.debug = debug
        self.lock = Lock()
        
        self.visa_resource_manager = pyvisa.ResourceManager()
        
        if debug: print('Visa devices detected:', self.visa_resource_manager.list_resources())

        print(port)
        self.TekScope = self.visa_resource_manager.get_instrument(port)
        self.TekScope.timeout = 100
        
    def write(self, cmd):
        with self.lock:
            self.TekScope.write(cmd)
    
    def ask(self, cmd):
        if self.debug: print("TekScope ask " + repr(cmd))
        with self.lock:
            try:
                resp = self.TekScope.query(cmd) 
            except:
                resp = self.TekScope.ask(cmd)  # Deprecated pyvisa method --> replaced by query()
            
        if self.debug: print("TekScope resp ---> " + repr(resp))
        return resp.rstrip('\n')
    
    def get_curve_and_time_array(self):
        
        self.write('DATA:SOU CH1')
        self.write('DATA:WIDTH 1')
        self.write('DATA:ENC RPB')
        
        ymult = float(self.ask('WFMPRE:YMULT?'))
        yzero = float(self.ask('WFMPRE:YZERO?'))
        yoff = float(self.ask('WFMPRE:YOFF?'))
        xincr = float(self.ask('WFMPRE:XINCR?'))

        self.write('CURVE?')
        data = self.TekScope.read_raw()
        headerlen = 2 + int(data[1])
        header = data[:headerlen]
        ADC_wave = data[headerlen:-1]

        ADC_wave = np.array(unpack('%sB' % len(ADC_wave), ADC_wave))

        Volts = (ADC_wave - yoff) * ymult + yzero
        Time = np.arange(0, xincr * len(Volts), xincr)
        return Time, Volts