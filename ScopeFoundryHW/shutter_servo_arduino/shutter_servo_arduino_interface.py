'''
Created on Oct 27, 2014

@author: Edward Barnard
'''
from __future__ import division, absolute_import, print_function
import serial
import time
import logging
import threading

logger = logging.getLogger(__name__)

class ShutterServoArduino(object):


    def __init__(self, port="COM22", debug = False, CLOSE_POSITION = 0, OPEN_POSITION=45):
        self.port = port
        self.debug = debug


        self.CLOSE_POSITION = CLOSE_POSITION
        self.OPEN_POSITION = OPEN_POSITION
        
        self.lock = threading.Lock()
        
        if self.debug: logger.debug( "ShutterServoArduino init, port=%s" % self.port)
        
        else:
            self.ser = serial.Serial(port=self.port, baudrate=9600, timeout=0.1)
            self.ser.flush()
        
        time.sleep(0.1)
        self.position=0
        
    def send_cmd(self, cmd):
        if self.debug: logger.debug( "send_cmd:" + repr(cmd))
        full_cmd = cmd + "\r\n"
        with self.lock:
#             self.ser.write(full_cmd)
            self.ser.write(full_cmd.encode())
    
    def ask(self, cmd):
        if self.debug: logger.debug( "ask:" +  repr(cmd) )
        self.send_cmd(cmd)
        with self.lock:
            resp = self.ser.readline().decode()
        if self.debug: self.log.debug( "resp: " + repr(resp) )
        return resp 
    
    
    def write_position(self, pos):
        pos = int(pos)
        assert 0 <=  pos <= 180
        self.send_cmd(str(pos))
        self.position = pos
        return self.position

    def read_position(self):
        resp = self.ask("?")
        self.position = int(resp)
        return self.position
        
    def move_open(self, open=True):
        if open:
            self.write_position(self.OPEN_POSITION)
        else:
            self.move_close()

    def move_close(self):
        return self.write_position(self.CLOSE_POSITION)

    def read_open(self):
        pos = self.read_position()
        assert pos in (self.OPEN_POSITION, self.CLOSE_POSITION)
        if pos == self.OPEN_POSITION:
            return True
        if pos == self.CLOSE_POSITION:
            return False
        else:
            raise ValueError()
        
    def close(self):
        if not self.debug:
            self.ser.close()
            del self.ser