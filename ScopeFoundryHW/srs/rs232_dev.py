"""
Created on Dec 14, 2022

@author: Benedikt Ursprung
"""

import serial
import time


class RS232_Dev:
    '''Mimics a pyvisa resource'''

    def __init__(self, port="COM1",
                 baudrate=115200,
                 bytesize=8,
                 parity='N',
                 stopbits=1,
                 xonxoff=0,
                 rtscts=1,
                 timeout=1.0,
                 debug=False):
        self.port = port
        self.debug = debug

        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            xonxoff=xonxoff,
            rtscts=rtscts,
            timeout=timeout
        )

    def write(self, cmd: str):
        if self.debug:
            print("write:", repr(cmd))
        self.ser.write((cmd + '\r').encode())

    def query(self, cmd: str):
        self.write(cmd)
        time.sleep(0.01)
        resp: str = self.ser.readline()
        if self.debug:
            print("resp:", resp.decode().strip('\r\n'))
        return resp.decode().strip('\r\n')

    def close(self):
        self.ser.close()


if __name__ == '__main__':
    print('start')
    dev = RS232_Dev(debug=True)
    dev.write("*CLS")
    print(dev.query('*IDN?'))
    print('done')
