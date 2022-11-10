"""
Kaiyuan 07/27/2018
"""
from __future__ import division, print_function
import serial
import time

class ChameleonOPOVis(object):

    def __init__(self, port="COM1", debug=False, dummy=False): #change port according to device listing in windows.
        ###Not yet sure why, but the OPO communication only works through real RS232 port, not USB serial converter!!!
        
        self.debug = debug
        self.dummy = dummy
        self.port = port
        
        if not self.dummy:
            
            print ('connecting OPO...')

            self.ser = ser = serial.Serial(port=self.port, baudrate=38400, 
                                           bytesize=8, parity='N', 
                                           stopbits=1, xonxoff=False, timeout=1.0)
            
            #self.ser.flushInput()
            #self.ser.reset_input_buffer()
            #self.ser.flushOutput()
            #self.ser.reset_output_buffer()
            
            ser.flush()
            time.sleep(1)
            self.ser.flushInput()
            time.sleep(0.1)
            self.ser.readline()

            
    def close(self):
        self.ser.close()
        print ('OPO closed')

    def write_cmd(self, cmd):
        sercmd = cmd+'\n'
        self.ser.write(sercmd.encode()) ##OPO commands are terminated by linefeed
        if self.debug:
            print ('write:', sercmd)
            print ('Encoded cmd: ', sercmd.encode() )
        response = self.ser.readline()
        if self.debug:
            print ('response:', repr(response))
        if 'Error'.encode() in response:
            raise IOError('Chameleon OPO command error: ' + repr(response))
        return response.strip()

#     Not sure if OPO actually has this BAUDRATE command
#     def write_baudrate(self, rate):
#         """Sets the RS232 serial port baud rate to the
#         specified value."""
#         assert rate in [1200,2400,4800,9600,19200,38400,57600,115200]
#         return self.write_cmd("BAUDRATE=%i" % rate)

    #### Need to double check, is this function returning a string, or actually a integer number code?
    def query_OPO_status(self):
        "query the current status of OPO"
        resp = self.write_cmd("STATUS?")
        print('OPO current status: {}'.format(repr(resp.decode())))
        return resp.decode() ##a string
    
    def query_OPO_ID(self):
        "query the OPO device ID"
        resp = self.write_cmd("*ID?")
        print ('ID decode value: ', resp.decode())
        print('OPO ID info: {}'.format(repr(resp)))
        return resp.strip() ##a string?

    def write_bypass_status(self, bypassOPO=False ):
        """Sets the beamsplitter position 1=bypass, 0=pump opo"""
        if bypassOPO:
            bp = int(1)
        else:
            bp = int(0)
        print('Write OPO beamsplitter position: %d' %bp)
        return self.write_cmd("BEAM SPLITTER=%i" %bp)
    
    def read_bypass_status(self):
        """Reads the beamsplitter position 1=bypass, 0=pump opo"""
        resp = self.write_cmd("BEAM SPLITTER?")
        if int(resp.strip()) == 1:
            print ('Read OPO beamsplitter position: bypass')
            bp_stat = True
        if int(resp.strip()) == 0:
            print ('Read OPO beamsplitter position: pump OPO') 
            bp_stat = False
        #return int(resp.strip())
        return bp_stat
    
    def write_OPO_SHG_mirror(self, OPO_SHG = False):
        """Sets the OPO SHG mirror position 1=on, 0=off"""
        if OPO_SHG:
            mp = int(1)
        else:
            mp = int(0)
        print('Write OPO SHG mirror position: %d' %mp)
        return self.write_cmd("OPO SHG MIRROR=%i" %mp)
    
    def read_OPO_SHG_mirror(self):
        """Reads the OPO SHG mirror position 1=on, 0=off"""
        resp = self.write_cmd("OPO SHG MIRROR?")
        if int(resp.strip()) == 1:
            print ('Read OPO SHG mirror: ON')
            opo_SHG_mirror_stat = True
        if int(resp.strip()) == 0:
            print ('Read OPO SHG mirror: OFF')
            opo_SHG_mirror_stat = False
        return opo_SHG_mirror_stat
        #return int(resp.strip())
    
    def write_pump_SHG_mirror(self, Pump_SHG = False):
        """Sets the pump SHG mirror position 1=on, 0=off"""
        if Pump_SHG:
            mp = int(1)
        else:
            mp = int(0)
        print('Write pump SHG mirror position: %d' %mp)
        return self.write_cmd("PUMP SHG MIRROR=%i" %mp)
    
    def read_pump_SHG_mirror(self):
        """Reads the pump SHG mirror position 1=on, 0=off"""
        resp = self.write_cmd("PUMP SHG MIRROR?")
        if int(resp.strip()) == 1:
            print ('Read PUMP SHG mirror: ON')
            pump_SHG_mirror_stat = True
        if int(resp.strip()) == 0:
            print ('Read PUMP SHG mirror: OFF')
            pump_SHG_mirror_stat = False
        return pump_SHG_mirror_stat
        #return int(resp.strip())
    
    def write_OPO_out_shutter(self, OPO_Out=False):
        """Sets the OPO output shutter position 1=open, 0=closed"""
        if OPO_Out:
            sp = int(1)
        else:
            sp = int(0)
        print('Write OPO out shutter position: %d' %sp)
        return self.write_cmd("OPO OUT SHUTTER=%i" %sp)
    
    def read_OPO_out_shutter(self):
        """Reads the OPO output shutter position 1=open, 0=closed"""
        resp = self.write_cmd("OPO OUT SHUTTER?")
        if int(resp.strip()) == 1:
            print ('Read OPO out shutter: OPEN')
            opo_out_stat = True
        if int(resp.strip()) == 0:
            print ('Read OPO out shutter: CLOSED')
            opo_out_stat = False
        #return int(resp.strip())
        return opo_out_stat
    
    def write_pump_in_shutter(self, Pump_In = True):
        """Sets the pump in shutter position 1=open, 0=closed"""
        if Pump_In:
            sp = int(1)
        else:
            sp = int(0)
        print('Write pump in shutter position: %d' %sp)
        return self.write_cmd("PUMP IN SHUTTER=%i" %sp)
    
    def read_pump_in_shutter(self):
        """Reads the pump in shutter position 1=open, 0=closed"""
        resp = self.write_cmd("PUMP IN SHUTTER?")
        if int(resp.strip()) == 1:
            print ('Read pump in shutter: OPEN')
        if int(resp.strip()) == 0:
            print ('Read pump in shutter: CLOSED')
        return int(resp.strip())
    
    def write_pump_out_shutter(self, Pump_Out):
        """Sets the pump out shutter position 1=open, 0=closed"""
        if Pump_Out:
            sp = int(1)
        else:
            sp = int(0)
        print('Write pump out shutter position: %d' %sp)
        return self.write_cmd("PUMP OUT SHUTTER=%i" %sp)
    
    def read_pump_out_shutter(self):
        """Reads the pump out shutter position 1=open, 0=closed"""
        resp = self.write_cmd("PUMP OUT SHUTTER?")
        if int(resp.strip()) == 1:
            print ('Read pump out shutter: OPEN')
            pump_out_stat = True
        if int(resp.strip()) == 0:
            print ('Read pump out shutter: CLOSED')
            pump_out_stat = False
        return pump_out_stat
        #return int(resp.strip())
    
    
    def write_OPO_wavelength(self, _lambda):
        """Sets the Chameleon OPO wavelength 
        _lambda is given in nm, and it needs to be converted to Angstrom for sending into OPO"""
        wl = int(_lambda*10) #in Angstrom
        print('Write OPO wavelength: %d Angstrom' %wl)
        return self.write_cmd("OPO WAVELENGTH=%i" % wl)
        
    def read_OPO_wavelength(self):
        resp = self.write_cmd('OPO WAVELENGTH?')
        print ('CC OPO wavelength from outside: ',  resp)
        print('Read OPO wavelength in Angstrom {}'.format(repr(resp.decode())))
        return float(resp.decode())/10 #returned value is set back to be in nm
    
    def read_OPO_bandwidth(self):
        resp = self.write_cmd('OPO BANDWIDTH?')
        print('Read OPO bandwidth in Angstrom {}'.format(repr(resp.decode())))
        return float(resp.decode())/10 #returned value is set back to be in nm
    
    def read_OPO_power(self):
        resp = self.write_cmd('OPO POWER?')
        print('Read OPO power in mW {}'.format(repr(resp.decode())))
        return float(resp.decode()) #returned value in mW
    
    def read_OPO_SHG_power(self):
        resp = self.write_cmd('OPO SHG POWER?')
        print('Read OPO SHG power in mW {}'.format(repr(resp.decode())))
        return float(resp.decode()) #returned value in mW
    
    def read_pump_SHG_power(self):
        resp = self.write_cmd('PUMP SHG POWER?')
        print('Read PUMP SHG power in mW {}'.format(repr(resp.decode())))
        return float(resp.decode()) #returned value in mW
    
    def read_pump_wavelength(self):
        resp = self.write_cmd('PUMP WAVELENGTH?')
        print('Read pump wavelength in Angstrom {}'.format(repr(resp.decode())))
        return float(resp.decode())/10 #returned value is set back to be in nm
    
    def read_pump_bandwidth(self):
        resp = self.write_cmd('PUMP BANDWIDTH?')
        print('Read pump bandwidth in Angstrom {}'.format(repr(resp.decode())))
        return float(resp.decode())/10 #returned value is set back to be in nm

    

if __name__ == '__main__':

    try:    
        opo = ChameleonOPOVis(port='COM1', debug=True)
        
        #resp_ID = opo.query_OPO_ID()
        #print ('CC ID: ', resp_ID)
        
#         resp_status = opo.query_OPO_status()
#         print ('CC status: ', resp_status)
#         if resp_status == 'OK':
#             print ('OPO status OK')
#         
#         resp_bypass = opo.read_bypass_status()
#         print ('bypass status return value:', resp_bypass)
#         
#         resp_opoSHG = opo.read_OPO_SHG_mirror()
#         print ('opo SHG mirror status return value:', resp_opoSHG)
#         
#         resp_pumpSHG = opo.read_pump_SHG_mirror()
#         print ('opo pump mirror status return value:', resp_pumpSHG)
#         
#         resp_opo_out_shutter = opo.read_OPO_out_shutter()
#         print ('opo out shutter return value:', resp_opo_out_shutter)
#         
#         resp_opo_wl = opo.read_OPO_wavelength()
#         print ('opo wavelenth return value:', resp_opo_wl)
#         
#         resp_opo_bw = opo.read_OPO_bandwidth()
#         print ('opo bandwidth return value:', resp_opo_bw)
#         
#         resp_opo_pw = opo.read_OPO_power()        
#         print ('opo power return value:', resp_opo_pw)
#         
#         resp_pump_wl = opo.read_pump_wavelength()
#         print ('opo pump wavelength return value:', resp_pump_wl)
#         
#         resp_pump_in_shutter = opo.read_pump_in_shutter()
#         print ('opo pump in shutter return value:', resp_pump_in_shutter)
        
#         opo.write_OPO_wavelength(1300)
#         time.sleep(0.1)
#         opo.query_OPO_status()
#         opo.read_OPO_bandwidth()
        
        opo.write_bypass_status(bypassOPO=True )
        opo.read_bypass_status()
        time.sleep(0.1)
        opo.query_OPO_status()
        
        #opo.write_OPO_wavelength(1200)
        
        #opo_wl = opo.read_OPO_wavelength()
        #print(opo_wl)
        
        
        #opo_wl = opo.read_OPO_wavelength()
        #print(opo_wl)
        
        #print(opo.read_OPO_power())
    
    except Exception as err:
        print(err)
    finally:
        opo.close()
    
