import serial
import subprocess
import ctypes as ct
from ctypes import byref
from ctypes import c_uint
import time
import threading

AOTFCMD_PATH = r"C:\Program Files\Crystal Technology\AotfCmd\AotfCmd.exe"
AOTFLIB_PATH = r"C:\Program Files\Crystal Technology\AotfCmd\AotfLibrary.dll"


class CrystalTechDDS(object):

    def __init__(self, comm="serial", port=0, debug=True):
    
        self.comm = comm
        self.port = port
        self.debug = debug
        
        assert comm in ['serial', 'aotfcmd', 'aotflib']
        
        self.frequency = [0,0,0,0,0,0,0,0]
        self.amplitude = [0,0,0,0,0,0,0,0]
        
        self.lock = threading.Lock()
        
        if self.comm == "serial":
            print('Opening serial')
            self.ser = serial.Serial(port, 38400, timeout=2,
                        parity=serial.PARITY_NONE, 
                        stopbits=serial.STOPBITS_ONE, 
                        xonxoff=False, 
                        rtscts=False)
            self.ser.flush()
            out = "x"
            while out != b'':
                out = self.ser.read()
            self.ser.write(b"\x04")
            for i in range(4):
                print(i)
                self.readline()
        elif self.comm == "aotfcmd":
            self._proc = subprocess.Popen([AOTFCMD_PATH,"-i","dds f 0"], shell=True,
                                    #stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE)#, stderr=subprocess.STDOUT)
            self.readline()
            self.readline()
            self.readline()

        elif self.comm == 'aotflib':
            self.port = int(self.port)
            self._lib = ct.cdll.LoadLibrary(AOTFLIB_PATH)
            self._handle = self._lib.AotfOpen(self.port)
            assert self._handle
    
    
    def readline(self):
        if self.comm == 'serial':
            with self.lock:
                data = self.ser.readline()
        elif self.comm == 'aotfcmd':
            data = self._proc.stdout.readline()
        elif self.comm == 'aotflib':
            if self._lib.AotfIsReadDataAvailable(self._handle):
                bytes_read = c_uint(0)
                read_buf = ct.create_string_buffer(256)
                retval = AotfRead(self._handle,  len(read_buf), byref(read_buf), byref(bytes_read))
                assert retval
            else:
                if self.debug: print("crystaltech_dds readline: no data available")
        if self.debug: print("crystaltech_dds readline:", data)                  
        return data.decode()
        
    def read(self): # read one character from buffer
        with self.lock:
            data = self.ser.read().decode()
        if self.debug: print("crystaltech_dds read:", data)
        #data = data.lstrip('\n')

        #data = data.lstrip('* ')
        return data

    def write(self, data):
        if self.comm == 'serial':
            with self.lock:
                self.ser.write(('{}\r\n'.format(data)).encode())
        elif self.comm == 'aotfcmd':
            self._proc.stdin.write(data  + '\r\n')
        elif self.comm == 'aotfcmd':
            data_buf = ct.create_string_buffer(data)
            retval = self._lib.AotfWrite(self._handle, len(data), ct.byref(data_buf))
            assert retval
        return
        
    def write_with_echo(self, data):
        if self.debug: print("crystaltech_dds write_with_echo:", data)

        self.write(data)
        return self.readline()

    def close(self):
        if self.comm =="serial":
            self.ser.flush()        
            self.ser.close()
        elif self.comm == 'aotfcmd':
            self._proc.terminate()      
        elif self.comm == 'aotflib':
            retval = self._lib.AotfClose(self._handle)
            assert retval                 
                    
    def set_calibration(self, c0,c1,c2,c3):
        for i, c in enumerate([c0,c1,c2,c3]):
            self.write_with_echo("cal tuning %i %g" % (i, c))
            
    def get_calibration(self):
    
        # old version: out put should look like this: "Tuning Polynomial Coefficient 0 is 3.531000e+02"
        # new version: Channel 0 profile 0 frequency 0.000000e+00Hz (Ftw 0)
        
        c = [0,0,0,0]
        for i in [0,1,2,3]:
            self.write_with_echo("cal tuning %i" % i)
            output = self.readline() 

            c[i] = float( output.split()[-1] )
        
        return tuple(c)
    
    def set_frequency(self, freq, channel=0):
        assert 10 < freq < 200
        self.write_with_echo("dds f %i %f" % (channel, freq))
        
    def set_wavelength(self, wl,  channel=0):
        assert 300 < wl < 2000
        self.write_with_echo("dds wave %i %f" % (channel, wl))
        
    def get_frequency(self, channel=0):
    
        #output in the form:"* Channel 0 profile 0 frequency 8.278661e+07Hz (Ftw 888914432)"
        self.write_with_echo("dds f %i" % channel)
        output = self.readline()
        self.frequency[channel] = float(output.split()[-3][:-2])/1.e6
        return self.frequency[channel]
    
    def get_wavelength(self, channel=0):
        #FIXME
        #TODO
        #self.write_with_echo("cal tune %f" % self.get_frequency())
        #output = self.readline()
        pass

    def set_amplitude(self, amp, channel=0):
        "amplitude range from 0 to 16383 (2^14)"
        self.write_with_echo("dds a %i %i" % (channel, amp))

    def get_amplitude(self, channel=0):
        self.write_with_echo("dds a %i" % channel)
        output = self.readline()
        #output should look like:"Channel 1 @ 0"
        self.amplitude[channel] = int(output.split()[-1])
        return self.amplitude[channel]

    def modulation_enable(self):
        self.write_with_echo("dau en")
        self.write_with_echo("dau gain * 255")
        
    def modulation_disable(self):
        self.write_with_echo("dau gain * 0")
        self.write_with_echo("dau dis" )
    
    def set_modulation(self, mod=True):
        if mod:
            self.modulation_enable()
        else:
            self.modulation_disable()
            
if __name__ == '__main__':

    cdds = CrystalTechDDS(comm="serial", port="COM1", debug=True)
    
    print(cdds.get_calibration())
    
    cdds.close()
