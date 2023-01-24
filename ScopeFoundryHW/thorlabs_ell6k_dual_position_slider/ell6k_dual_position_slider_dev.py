import serial
import time


class ELL6KDualPositionSliderDev:
    """
    Thorlabs ELL6K Dual Position Slider Kit
    """

    def __init__(self, port="COM6", debug=False):
        self.port = port
        self.debug = debug

        if self.debug:
            print(f"ThorlabsELL6K init, port=%s" % self.port)

        self.ser = serial.Serial(port=self.port, baudrate=9600, timeout=1.0)
        time.sleep(0.1)
        self.ser.flushInput()
        time.sleep(0.1)
        self.ser.readline()

    def send_cmd(self, cmd):
        if self.debug:
            print("send_cmd:", repr(cmd))
        self.ser.write(cmd + b"\n")

    def ask_cmd(self, cmd):
        if self.debug:
            print("ask:", repr(cmd))
        self.send_cmd(cmd)
        time.sleep(0.01)
        resp = self.ser.readline()
        if self.debug:
            print("resp:", repr(resp))
        return resp

    def write_position(self, pos):
        d = {0: b'0fw', 1: b'0bw'}
        assert pos in d
        self.send_cmd(d[pos])

    def read_position(self):
        ans = self.ask_cmd(b'0gp').decode("utf-8")[9:11]
        return {"00": 0, "1F": 1}[ans]

    def read_other_position(self):
        return int(not bool(self.read_position()))

    def close(self):
        self.ser.close()
