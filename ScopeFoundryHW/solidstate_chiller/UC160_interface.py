"""
Created on Apr 14, 2021

@author: Benedikt Ursprung
"""
import serial

class UC160(object):

    def __init__(self, port="COM21", debug=False):
        
        self.debug = debug
        self.port = port
        
        self.ser = serial.Serial(port=self.port, 
                                   baudrate=9600, 
                                   bytesize=serial.EIGHTBITS,
                                   parity=serial.PARITY_NONE, 
                                   stopbits=serial.STOPBITS_ONE, 
                                   timeout=1.0)
    
    def close(self):
        self.ser.close()
        if self.debug:
            print('UC160 device closed')
            
    def write_setpoint(self, T):
        cmd = bytearray([225, int(10*T), 0]) #225_dec = E1_hex
        self.ser.write(cmd)
        success = self.ser.read(1) == b'\xe1'
        if self.debug:
            print(f"UC160 write setpoint ({T}C) success", success)
        return success
    
    def read_setpoint(self):
        self.ser.write(b'\xC1')
        temp = bytearray(self.ser.read(3))[1]/10.0
        if self.debug:
            print('UC160 read setpoint', temp)
        return temp
    
    def read_temperature(self):
        self.ser.write(b'\xC9')
        temp = bytearray(self.ser.read(3))[1]/10.0
        if self.debug:
            print('UC160 read temperature', temp)
        return temp
    
    def reset_chiller(self):
        self.ser.write(b'\xFF')
        success = self.ser.read(1) == b'\xFF'
        if self.debug:
            print("UC160 reset chiller success", success)
        return success
        
    def read_fault_table(self):
        self.ser.write(b'\xC8')
        success = self.ser.read(1) == b'\xC8'
        resp = format(bytearray(self.ser.read(1))[0], '08b')
        if self.debug: 
            print('faults resp', resp)
        if not success:
            return "COMMUNICATION FAILED"
        else:
            faults = ""
            if resp[0] == '1': faults += 'Tank Level Low '
            if resp[2] == '1': faults += 'Temperature above alarm range '
            if resp[4] == '1': faults += 'RTP fault '
            if resp[5] == '1': faults += 'Pump fault '
            if resp[7] == '1': faults += 'Temperature below alarm range '
            return faults
    
    def read_TE_power(self):
        pass
        
    
if __name__ == '__main__':
    uc160 = UC160(port='COM21', debug=True)  
    uc160.write_setpoint(21.8)
    uc160.read_setpoint()
    uc160.read_temperature()    
    uc160.close()
    
    
    
