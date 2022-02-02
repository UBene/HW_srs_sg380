import serial
import threading

class ThorlabsElliptecDevice(object):
    
    def __init__(self, port="COM3", addr=0, debug=False):
        self.port = port
        self.addr = addr # default address
        self.debug = debug
        self.lock = threading.Lock()
        
        self.ser = serial.Serial(port,  baudrate=9600, timeout=2.0)
        
    
    """
    The communications protocol used in the ELLx Elliptec Thorlabs
    module is based on the message structure that always starts with
    a fixed length, 3-byte message header which, in some cases, is followed 
    by a variable length data packet. For simple commands, the 3-byte
    message header is sufficient to convey the entire command. 
    
    Some commands require parameters so 3 byte packet must be followed by the data bytes. 
    The number of data bytes depends on command and length is now part of the packet is implicit 
    (see command detail to see length).  
    
    Data packets coming from modules are terminated with carriage return CR (0xD)
    first and then line feed LS (0xA). Each module has a 2 second time out such 
    that the discard packet is discarded if time between each byte sent is higher
    longer than 2 seconds. Alternatively carriage return CR can be used to clear receiving 
    state machine and exit from a time out error or cancel a command not completed.
     
    Error must be cleared reading module status see "gs".
    """
    
    
    def ask(self, cmd, addr=None):
        if addr is None:
            addr = self.addr
        else:
            assert 0<= addr < 16 
        full_cmd = "{:X}{}".format(addr, cmd)
        if self.debug:
            print("ThorlabsElliptec -->" + full_cmd)
        with self.lock:
            self.ser.write(full_cmd.encode())
            resp = self.ser.readline().decode()
        if self.debug:
            print("ThorlabsElliptec <--" + resp)
        # TO DO check if error in resp
        if resp[1:3] == 'GS':
            code = int(resp[3:5], 16)
            if code > 0:
                raise IOError("Elliptec Error {}: {}".format(code, ERROR_TABLE.get(code, 'Reserved')))
        
        return resp
        
    
    def get_information(self, addr=None):
        resp = self.ask("in",addr)
        self.hw_info = dict(
            dev_type = int(resp[3:5], 16),
            serial_num = resp[5:13],
            year = int(resp[13:17]),
            firmware_release = int(resp[17:19], 16),
            hw_release = int(resp[19:21], 16) & 0x7F,
            imperial = bool(int(resp[19:21], 16) & 0x80),
            travel = int(resp[21:25], 16), # in mm or deg
            pulses_per_unit = int(resp[25:33], 16), # pulses per unit (mm or deg)
        )
        if self.hw_info['pulses_per_unit'] == 0:
            self.hw_info['pulses_per_unit'] = 1 # fix for slider style (ELL9)
        
        if   self.hw_info['dev_type'] == 18:
            self.hw_info['unit'] = 'deg'
        
        elif self.hw_info['dev_type'] == 14:
            self.hw_info['unit'] = 'deg'
            self.hw_info['pulses_per_unit'] /= 360.
        
        else:
            self.hw_info['unit'] = 'mm'
        if self.debug:
            for k,v in self.hw_info.items():
                print(k, "-->", v)
        
        return self.hw_info
        
    def close(self):
        self.ser.close()
    
    def jog_forward(self, addr=None):
        resp = self.ask('fw', addr)
        if resp[1:3] == 'PO':
            self.position = int(resp[3:], 16)
            self.position_mm = self.position / self.hw_info['pulses_per_unit']
        return self.position_mm

    def jog_backward(self, addr=None):
        resp = self.ask('bw', addr)
        if resp[1:3] == 'PO':
            self.position = int(resp[3:], 16)
            self.position_mm = self.position / self.hw_info['pulses_per_unit']
        return self.position_mm
    
    def get_jog_step_size(self, addr=None):
        resp = self.ask('gj', addr)
        return int(resp[3:],16)
    def get_jog_step_size_mm(self, addr=None):
        return self.get_job_step_size(addr) / self.hw_info['pulses_per_unit']
    
    def set_jog_step_size(self, step_size, addr=None):
        resp = self.ask('sj{:08X}'.format(step_size), addr)
        return resp
    def set_jog_step_size_mm(self, step_size, addr=None):
        return self.set_jog_step_size(step_size*self.hw_info['pulses_per_unit'], addr)

    def home_device(self, direction=0, addr=None):
        """Instruct hardware unit to move to the home position"""
        assert direction in (0,1)
        resp = self.ask('ho{}'.format(direction), addr)
        if resp[1:3] == 'PO':
            self.position = int(resp[3:], 16)
            self.position_mm = self.position / self.hw_info['pulses_per_unit']
        return self.position_mm

    
    def move_absolute(self, pos, addr=None):        
        """"
        Request a linear stage at address 'A' to move at position 4mm.
        Linear stage has 2048 encoder pulses per mm, hence 4 mm 8192 
        pulses (0x2000 in hexadecimal).
        TX'Ama00002000'
        """
        resp = self.ask('ma{:08X}'.format(int(pos)),addr) 
        if resp[1:3] == 'PO':
            self.position = int(resp[3:], 16)
            self.position_mm = self.position / self.hw_info['pulses_per_unit']
        return self.position

    def move_absolute_mm(self, pos, addr=None):
        return self.move_absolute(pos*self.hw_info['pulses_per_unit'], addr) / self.hw_info['pulses_per_unit']
    
    def get_position(self, addr=None):
        resp = self.ask('gp', addr)
        assert resp[1:3] == 'PO'
        pos = int(resp[3:], 16)
        def s32(value):
            return -(value & 0x80000000) | (value & 0x7fffffff)
        pos = s32(pos)
        if self.debug: print("get_position: {} units".format(pos))
        return pos
    def get_position_mm(self, addr=None):
        return self.get_position(addr)*1.0 / self.hw_info['pulses_per_unit']

    def get_status(self, addr=None):
        resp = self.ask("gs", addr)
        code = int(resp[3:5], 16)
        return code, ERROR_TABLE.get(code, 'Reserved')
    
    
    def get_unit(self):
        # TODO other device types
        if self.hw_info['dev_type'] == 18:
            return 'deg'
        else:
            return 'mm'

ERROR_TABLE = {
    0: "no error",
    1: "Communication time out",
    2: "Mechanical time out",
    3: "Command error or not supported",
    4: "Value out of range",
    5: "Module isolated",
    6: "Module out of isolation",
    7: "Initializing error",
    8: "Thermal error",
    9: "Busy",
    10: "Sensor Error (May appear during self test. If code persists there is an error)",
    11: "Motor Error (May appear during self test. If code persists there is an error)",
    12: "Out of Range (e.g. stage has been instructed to move beyond its travel range)",
    13: "Over Current error"
}


    
if __name__ == '__main__':
    
    dev = ThorlabsElliptecDevice(debug=True)
    import pprint
    
    pprint.pprint(dev.get_information())
    print("jog step size", dev.get_jog_step_size())
    
    dev.close()