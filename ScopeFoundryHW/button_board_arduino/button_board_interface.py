'''
Created on Jun 21, 2017

@author: Alan Buckley
'''

from __future__ import division, absolute_import, print_function
import serial
import time
import logging

logger = logging.getLogger(__name__)

class ButtonBoardInterface(object):
    
    name="button_board_interface"
    
    def __init__(self, port="COM4", debug = False):
        self.port = port
        self.debug = debug
        if self.debug:
            logger.debug("ButtonBoardInterface.__init__, port={}".format(self.port))
            
        self.ser = serial.Serial(port=self.port, baudrate=9600, timeout = 0.1)
        # Store relay values
        self.ser.flush()
        time.sleep(0.2)
        #time.sleep(1.7)
        self.relays = None
        self.poll()
        
    def ask_cmd(self, cmd):
        if self.debug: 
            logger.debug("ask_cmd: {}".format(cmd))
        message = cmd+b'\n'
        self.ser.write(message)
        resp = self.ser.readline()
        if self.debug:
            logger.debug("readout: {}".format(cmd))
        self.ser.flush()
        return resp
    
    def send_cmd(self, cmd):
        if self.debug:
            logger.debug("send: {}".format(cmd))
        message = cmd+b'\n'
        self.ser.write(message)
        if self.debug:
            logger.debug("message: {}".format(message))
        self.ser.flush()
    
    def listen(self):    
        rdata = self.ser.read(3)
        if len(rdata)>2:
            data = int(rdata.strip().decode())
            return data
        else:
            pass
        
    def write_state(self, chan, value):
        assert (chan in (1,2,3,4)), "Please enter a relay number in range 1 to 4"
        cmd = "{}".format(chan).encode()
        self.send_cmd(cmd)
        if self.debug:
            logger.debug("state_cmd: {}".format(cmd))

    def write_instrument_name(self, line, name):
#         cmd = "D{}".format(line).encode()
#         self.send_cmd(cmd)
        cmd = "L{}{}".format(line, name).encode()
        self.send_cmd(cmd)
        if self.debug:
            logger.debug("instrument command sent: {}".format(cmd))
        time.sleep(0.1)
        
    def line_blackout(self, line):
        cmd = "D{}".format(line).encode()
        self.send_cmd(cmd)
        if self.debug:
            logger.debug("blackout command sent: {}".format(cmd))
            
    def full_screen_blackout(self):
        cmd = "B".encode()
        self.send_cmd(cmd)
        if self.debug:
            logger.debug("screen blackout command sent")
            
    def full_button_blackout(self):
        cmd = "R".encode()
        self.send_cmd(cmd)
        if self.debug:
            logger.debug("screen blackout command sent")
        
    def poll(self):
        resp = self.ask_cmd(b"?")
        print("resp:", resp)
        data = resp.strip().decode().split(',')
        print("data:", data)
        if len(data) > 0:
            self.button_poll = poll = [int(x) for x in data]
        else:
            pass
        print("poll:", poll)
        if self.debug:
            logger.debug("stored val: {}".format(self.relays))
        return poll
           
    def close(self):
        self.ser.close()