"""
Address    Size(Byte)    Data Name    Access    Initial Value    Range    Unit
0    2    Model Number    R    1,060    -    -
2    4    Model Information    R    -    -    -
6    1    Firmware Version    R    -    -    -
7    1    ID    RW    1    0 ~ 252    -
8    1    Baud Rate    RW    1    0 ~ 7    -
9    1    Return Delay Time    RW    250    0 ~ 254    2 [usec]
10    1    Drive Mode    RW    0    0 ~ 5    -
11    1    Operating Mode    RW    3    0 ~ 16    -
12    1    Secondary(Shadow) ID    RW    255    0 ~ 252    -
13    1    Protocol Type    RW    2    1 ~ 2    -
20    4    Homing Offset    RW    0    -1,044,479 ~ 1,044,479    1 [pulse]
24    4    Moving Threshold    RW    10    0 ~ 1,023    0.229 [rev/min]
31    1    Temperature Limit    RW    72    0 ~ 100    1 [deg C]
32    2    Max Voltage Limit    RW    140    60 ~ 140    0.1 [V]
34    2    Min Voltage Limit    RW    60    60 ~ 140    0.1 [V]
36    2    PWM Limit    RW    885    0 ~ 885    0.113 [%]
44    4    Velocity Limit    RW    265    0 ~ 1,023    0.229 [rev/min]
48    4    Max Position Limit    RW    4,095    0 ~ 4,095    1 [pulse]
52    4    Min Position Limit    RW    0    0 ~ 4,095    1 [pulse]
63    1    Shutdown    RW    52    -    -


======

Address    Size(Byte)    Data Name    Access    Initial
Value    Range    Unit
64    1    Torque Enable    RW    0    0 ~ 1    -
65    1    LED    RW    0    0 ~ 1    -
68    1    Status Return Level    RW    2    0 ~ 2    -
69    1    Registered Instruction    R    0    0 ~ 1    -
70    1    Hardware Error Status    R    0    -    -
76    2    Velocity I Gain    RW    1,000    0 ~ 16,383    -
78    2    Velocity P Gain    RW    100    0 ~ 16,383    -
80    2    Position D Gain    RW    4,000    0 ~ 16,383    -
82    2    Position I Gain    RW    0    0 ~ 16,383    -
84    2    Position P Gain    RW    640    0 ~ 16,383    -
88    2    Feedforward 2nd Gain    RW    0    0 ~ 16,383    -
90    2    Feedforward 1st Gain    RW    0    0 ~ 16,383    -
98    1    Bus Watchdog    RW    0    1 ~ 127    20 [msec]
100    2    Goal PWM    RW    -    -PWM Limit(36) ~
PWM Limit(36)    0.113 [%]
104    4    Goal Velocity    RW    -    -Velocity Limit(44) ~
Velocity Limit(44)    0.229 [rev/min]
108    4    Profile Acceleration    RW    0    0 ~ 32,767
0 ~ 32,737    214.577 [rev/min2]
1 [ms]
112    4    Profile Velocity    RW    0    0 ~ 32,767    0.229 [rev/min]
116    4    Goal Position    RW    -    Min Position Limit(52) ~
Max Position Limit(48)    1 [pulse]
120    2    Realtime Tick    R    -    0 ~ 32,767    1 [msec]
122    1    Moving    R    0    0 ~ 1    -
123    1    Moving Status    R    0    -    -
124    2    Present PWM    R    -    -    -
126    2    Present Load    R    -    -1,000 ~ 1,000    0.1 [%]
128    4    Present Velocity    R    -    -    0.229 [rev/min]
132    4    Present Position    R    -    -    1 [pulse]
136    4    Velocity Trajectory    R    -    -    0.229 [rev/min]
140    4    Position Trajectory    R    -    -    1 [pulse]
144    2    Present Input Voltage    R    -    -    0.1 [V]
146    1    Present Temperature    R    -    -    1 [deg C]

"""
from collections import namedtuple
from enum import Enum
import threading

class OperatingModes(Enum):
    velocity = 1
    position = 3
    extended_position = 4
    pwm = 16 


CONTROL_TABLE = [
    ('model_num', 0, 2, 'r', int),
    ('mode', 11, 1, 'rw', OperatingModes),
    ('vel_limit', 44, 4, 'rw', int),
    #
    ('torque', 64, 1, 'rw', bool),
    ('led', 65, 1, 'rw', bool),
    ('time_tick', 120, 2, 'r', int),
    ('velocity', 128, 4, 'r', int),
    ('position', 132, 4, 'r', int),
    ('temp', 146, 1, 'r', int),
    ('target_position', 116, 4, 'rw', int ),
    ('moving', 122, 1, 'r', bool),
    ('profile_velocity', 112, 4, 'rw', int),
    ]

ctrl_row = namedtuple('ControlRow', ['name', 'addr', 'bytes', 'access', 'dtype'])
control_lut = dict()
for row in CONTROL_TABLE:
    control_lut[row[0]] = ctrl_row(*row)


from dynamixel_sdk import PortHandler, PacketHandler, COMM_SUCCESS

class DynamixelServos(object):
    
    def __init__(self, port, baud=57600):
        
        self.port = port
        
        self.lock = threading.Lock()
    
        self.portHandler = PortHandler(self.port)
        self.packetHandler = PacketHandler(2.0)
        
        success = self.portHandler.openPort()
        if not success:
            raise IOError("Dynamixel Servos failed to open port", self.port)
        
        success = self.portHandler.setBaudRate(baud)
        if not success:
            raise IOError("Dynamixel Servos failed to set baud on port", self.port, baud)
        
        
    def read_value(self, dxid, name):
        ctrl = control_lut[name]
        
        f = {1: self.packetHandler.read1ByteTxRx, 
             2: self.packetHandler.read2ByteTxRx,
             4: self.packetHandler.read4ByteTxRx}[ctrl.bytes]
        
        with self.lock:
            dxl_result, dxl_comm_result, dxl_error = f(self.portHandler, dxid, ctrl.addr)
        if dxl_comm_result != COMM_SUCCESS:
            raise IOError("DLX comm fail: %s" % self.packetHandler.getTxRxResult(dxl_comm_result))
        elif dxl_error != 0:
            raise IOError("DLX err: %s" % self.packetHandler.getRxPacketError(dxl_error))

        return dxl_result
    
    def write_value(self, dxid, name, value):
        ctrl = control_lut[name]
        
        if ctrl.access != 'rw':
            raise ValueError('Could not write, parameter {} is read-only'.format(name))

        f = {1: self.packetHandler.write1ByteTxRx, 
             2: self.packetHandler.write2ByteTxRx,
             4: self.packetHandler.write4ByteTxRx}[ctrl.bytes]
            
        with self.lock:
            dxl_comm_result, dxl_error = f(self.portHandler, dxid, ctrl.addr, value)
        if dxl_comm_result != COMM_SUCCESS:
            raise IOError("DLX comm fail: %s" % self.packetHandler.getTxRxResult(dxl_comm_result))
        elif dxl_error != 0:
            raise IOError("DLX err: %s" % self.packetHandler.getRxPacketError(dxl_error))

    
    def read_operating_mode(self, dxid):
        val = self.read_value(dxid, 'mode')
        return OperatingModes(val).name
    
    def write_operating_mode(self, dxid, mode_name):
        mode_id = OperatingModes[mode_name].value
        self.write_value(dxid, 'mode', mode_id)
    
    def close(self):
        self.portHandler.closePort()
    
if __name__ == '__main__':
    
    ds = DynamixelServos('COM13')
    
    for ctrl in control_lut.values():
        v = ds.read_value(2, ctrl.name)
        print(ctrl.name, repr(v))
    
    print("="*10)
    ds.write_value(2, 'vel_limit', 100)
    
    for ctrl in control_lut.values():
        v = ds.read_value(2, ctrl.name)
        print(ctrl.name, repr(v))

    print("="*10)
        
    ds.write_value(2, 'vel_limit', 72)

    for ctrl in control_lut.values():
        v = ds.read_value(2, ctrl.name)
        print(ctrl.name, repr(v))
        
    print("="*10)
    print("operating mode:", ds.read_operating_mode(2))
    print("="*10)
    ds.write_operating_mode(2, 'velocity')
    print("operating mode:", ds.read_operating_mode(2))
    print("="*10)
    ds.write_operating_mode(2, 'extended_position')
    print("operating mode:", ds.read_operating_mode(2))
