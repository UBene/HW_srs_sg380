"""
Polulu Micro Maestro ScopeFoundry module
Created on Jul 18, 2017

@author: Alan Buckley
"""


from __future__ import division, absolute_import, print_function
import serial
import time
import logging

logger = logging.getLogger(__name__)

class PololuMaestroDevice(object):
    
    name="pololu_servo_device"
    
    def __init__(self, port, device_addr=0x0C, debug = False):
        self.port = port
        self.debug = debug
        if self.debug:
            logger.debug("PololuMaestroDevice.__init__, port={}".format(self.port))
            
        self.ser = serial.Serial(port=self.port, timeout=0.5, baudrate=9600,
                                 )
        self.pololu_header = chr(0xAA) + chr(device_addr)
        self.ser.flush()
        time.sleep(0.2)
        
    def ask_cmd(self, cmd):
        """
        Device specific serial write and query function.
        ==============  ==========  ==========================================================================
        **Arguments:**  **Type:**   **Description:**
        cmd             str         Serial command to be converted to byte string and sent via serial protocol                                      
        ==============  ==========  ==========================================================================
        :returns: byte str, serial response. 
        """
        if self.debug: 
            logger.debug("ask_cmd: {}".format(cmd))
        message = self.pololu_header + cmd
        self.ser.write(bytes(message, 'latin-1'))
        resp = self.ser.readline()
        if self.debug:
            logger.debug("readout: {}".format(cmd))
        self.ser.flush()
        return resp
    
    
    def write_position(self, chan, target):
        """
        ==============  ==========  ==============  =======================================================
        **Arguments:**  **Type:**   **Range:**      **Description:**
        chan            int         (1,6)           Servo channel/address                                    
        servo* target   int         (544,2544)      Rotary servo position in units of quarter microseconds or...
                                    (1008,2000)     Linear servo position in units of quarter microseconds.
        output* target  int         >1500           outputs +5V high if channel is configured to Output 
                                    <1500           outputs 0V  low If channel is configured to Output
        ==============  ==========  ==============  =======================================================
        *each channel can be configured to be of type "servo", "input" or "output" (Pololu Mastro Control)
        :returns: None
        """
        base_qty = target 
        cmd_hex = 0x84
        cl_hex = cmd_hex & 0x7F
        lsb = base_qty & 0x7F
        msb = (base_qty >> 7) & 0x7F
        cmd = chr(cl_hex) + chr(chan) + chr(lsb) + chr(msb)
        self.ask_cmd(cmd)
        
    def read_position(self, chan):
        """
        ==============  ==========  ==============  =======================================================
        **Arguments:**  **Type:**   **Range:**      **Description:**
        chan            int         (1,6)           Servo channel/address                                  
        ==============  ==========  ==============  =======================================================
        :returns: int, Position of selected servo in units of quarter microseconds.
        """
        cmd_hex = 0x10
        cmd = chr(cmd_hex) + chr(chan)
        resp = self.ask_cmd(cmd)
        lsb = resp[0]
        msb = resp[1]
        data = (msb << 8) + lsb
        return data
        
    def close(self):
        """
        Closes serial connection
        :returns: None
        """
        self.ser.close()
        del self.ser