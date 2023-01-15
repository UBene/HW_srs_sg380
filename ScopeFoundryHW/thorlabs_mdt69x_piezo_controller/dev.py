"""
Created on Jan 15, 2023

@author: Benedikt Ursprung
"""

import serial
import time


class Dev:

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
        resp: str = self.ser.readline()
        if self.debug:
            print("resp:", resp.decode().split('*')[-1])
        return resp.decode().split('*')[-1]

    def query_float(self, cmd):
        try:
            return float(self.query(cmd)[1:-2])
        except ValueError:
            return 0

    def close(self):
        self.ser.close()


if __name__ == '__main__':
    print('start')
    dev = Dev(port='COM8', debug=True)
    dev.write('XV2.0')
    # print(dev.query('XR?'))
    print(dev.query_float('XR?'))

    dev.write('XV1.0')
    # print(dev.query('XR?'))
    print(dev.query_float('XR?'))

    dev.close()
    print('done')
