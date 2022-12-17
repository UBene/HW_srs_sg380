'''
Created on Jul 8, 2021

@author: Benedikt Ursprung
'''
import serial
from threading import Lock

BAUDRATE = 19200
TIMEOUT = 0.1 
BYTESIZE = 8
PARITY = 'N'
STOPBITS = 1
XONXOFF = 0
RTSCTS = 0
TERMINATOR = '\r\n'


def str2float(string):
    # q, w = string.split('.')
    # r = int(q) + int(w) / (10.0 ** len(w)) 
    return float(string)


class PMD24:
    
    name = 'PMD24_DEV'    
    
    def __init__(self, port='COM28', debug=False):
        self.ser = serial.Serial(port,
                                 timeout=TIMEOUT,
                                 baudrate=BAUDRATE,
                                 bytesize=BYTESIZE,
                                 parity=PARITY,
                                 stopbits=STOPBITS,
                                 xonxoff=XONXOFF,
                                 rtscts=RTSCTS)
        self.debug = debug
        if self.debug: print(self.ser)
        self.lock = Lock()
        
    def ask(self, cmd):
        with self.lock:
            if self.debug: print(self.name, 'Sending %s' % cmd)
            self.ser.write((cmd + TERMINATOR).encode())
            resp = self.ser.readline()
            if self.debug: print(self.name, 'Received', resp)
            return resp.decode()[:-len(TERMINATOR)]
        
    def write(self, cmd):
        with self.lock:
            self.ser.write((cmd + TERMINATOR).encode())
      
    def read_power(self):
        ans = self.ask('POWER?')[:-2]
        v = str2float(ans)                   
        if self.debug: print(ans, v)
        return v
    
    def write_power(self, power):
        self.ask(f'POWER={power}')
        
    def write_on(self):
        self.ask('ON')
        
    def write_off(self):
        self.ask('OFF')
        
    def read_status(self):
        return self.ask('STAT?')
    
    def read_laser_temp(self):
        return str2float(self.ask('LASTEMP?')[:-1])

    def read_PSU_temp(self):
        return str2float(self.ask('PSUTEMP?')[:-1])
    
    def write_ACTP(self, ACTP):
        '''For laser re-calibration 
        1. set a power 
        2. measure actual calibration laser power using a power meter \
            and set ACTP.
        3. confirm calibration with write_confirm_calibration'''
        self.ask(f'ACTP={ACTP}')
        
    def write_STPOW(self, STPOW):
        ''' STPOW is the optical power in mW. Sets the default start-up power. This
            serial command must be followed by WRITE'''
        self.ask(f'STPO={STPOW}')
        self.ask(f'WRITE')
        
    def write_confirm_calibration(self, _):
        self.ask('WRITE')


if __name__ == '__main__':
    dev = PMD24(debug=True)        
    
