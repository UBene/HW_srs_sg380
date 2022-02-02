'''
Created on Sep 18, 2014

@author: Benedikt Ursprung
'''

from __future__ import division
import time
import serial



class ThorlabsOpticalChopper(object):
    '''
    classdocs
    '''
    ThorlabsOpticalChopperBaudRate = 115200
    
    def __init__(self, port="COM4", debug=False):
        self.port = port
        self.debug = debug
        
        self.ser = serial.Serial(port=self.port, baudrate = self.ThorlabsOpticalChopperBaudRate,bytesize = serial.EIGHTBITS, 
                                 stopbits=1, parity = serial.PARITY_NONE,xonxoff=0,rtscts=0, timeout = 0.5)#,  stopbits=1, xonxoff=0, rtscts=0, timeout=5.0       
        self.ser.flushInput()
        
        #sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
        time.sleep(0.3)


    def write_command(self, cmd, waittime=0.5):
        if self.debug: print "cmd: ", cmd
        self.ser.write(cmd +"\r")
        time.sleep(waittime)
        
        out = bytearray()
        char = ""
        missed_char_count = 0
        while char != ">":
            char = self.ser.read(1)
            #if self.debug: print "readbyte", repr(char)
            if char == "": #handles a timeout here
                missed_char_count += 1
                if self.debug: print "no character returned, missed %i so far" % missed_char_count
                if missed_char_count > 3:
                    return 0
                continue
            out.append(char)

        if self.debug: print "complete message", repr(out), out.split()
        
        #assert out[-3:] == ";FF"
        #assert out[:7] == "@%03iACK" % self.address   
        
        self.ser.flushInput()
        self.ser.flushOutput()

        return out.split()[-2]



    def _write(self, cmd):
        self.ser.write(cmd+'\r')
        if self.debug:
            print "Optical Chopper Write", cmd
        resp = self.ser.read(1024)
        if self.debug:
            print "-->", resp


        
    def close(self):
        self.ser.close()
        print 'closed thorlabs_optical_chopper'



    def enable(self, enable_=True):
        if enable_:
             self.write_command('enable=1')
        else:
            self.disable()
 
 
        
    def disable(self):
        self.write_command('enable=0')
  
  
    
    def read_enable(self):
        return bool(int(self.write_command('enable?')))



    def read_freq(self):
        fstr = self.write_command('freq?')
        return float(fstr)
    

    
    def write_freq(self,f):
        self.write_command('freq='+str(int(f)))
        


    def setup(self):
        '''
        sets output defaults for measurements
        '''
        
        self.write_command('blade=2')
        self.write_command('ref=0')
        self.write_command('output=1')



if __name__ == '__main__':


    TOC1 = ThorlabsOpticalChopper()

    TOC1.enable(True)
    TOC1.write_freq(200)
    print TOC1.read_freq()
    print TOC1.read_enable()
