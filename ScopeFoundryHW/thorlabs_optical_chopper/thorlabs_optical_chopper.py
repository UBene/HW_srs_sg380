'''
Created on Sep 18, 2014

@author: Benedikt Ursprung
'''
import time

import serial


class ThorlabsOpticalChopper:

    def __init__(self, port="COM9", debug=False, baudrate=115200):
        self.port = port
        self.debug = debug

        self.ser = serial.Serial(port=self.port, baudrate=baudrate, bytesize=serial.EIGHTBITS,
                                 stopbits=1, parity=serial.PARITY_NONE, xonxoff=0, rtscts=0, timeout=0.5)  # ,  stopbits=1, xonxoff=0, rtscts=0, timeout=5.0
        self.ser.flushInput()
        time.sleep(0.010)

    def write(self, cmd):
        if self.debug:
            print("cmd: ", cmd, cmd.encode())
        self.ser.write(f'{cmd}\r'.encode())

    def ask(self, cmd):
        if self.debug:
            print("cmd: ", cmd)
        self.write(cmd)
        resp = self.ser.readline().decode()
        time.sleep(0.05)
        if self.debug:
            print("cmd: ", cmd, resp, resp.split('\r'), resp.split('\r')[-2])
        return resp.split('\r')[-2]

    def close(self):
        self.ser.close()
        print('closed thorlabs_optical_chopper')

    def read_enable(self):
        return bool(int(self.ask('enable?')))

    def write_enable(self, enable=True):
        if enable:
            self.write('enable=1')
        else:
            self.write('enable=0')

    def read_freq(self):
        return float(self.ask('freq?'))

    def write_freq(self, f):
        self.write(f'freq={int(f)}')

    def read_blade(self):
        self.write('blade?')

    def write_blade(self, n):
        self.write(f'blade={n}')


if __name__ == '__main__':

    TOC1 = ThorlabsOpticalChopper(debug=True)

    TOC1.write_enable(True)
    TOC1.write_freq(200)
    print(TOC1.read_freq())
    print(TOC1.read_enable())
