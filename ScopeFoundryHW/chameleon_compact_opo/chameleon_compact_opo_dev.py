"""
Created March 2019
@author: Benedikt Ursprung 
"""
import serial
import numpy as np
import logging
logger = logging.getLogger(__name__)


class ChameleonCompactOPO(object):
    '''
    Communicates with chameleon_compact_opo.exe (typically run on a panel PC).
    '''
    
    name = 'chameleon_compact_opo_dev'
    
    def __init__(self, port="COM22", debug=False, dummy=False):
        
        self.debug = debug
        self.dummy = dummy
        self.port = port
        
        if not self.dummy:
            self.ser = ser = serial.Serial(port=self.port, baudrate=38400, 
                                           bytesize=8, parity='N', 
                                           stopbits=1, xonxoff=False, timeout=1.0)
            ser.flush()
            
            #OPO communicates wavelengths in Angstrom and powers in mW. 
            self.unit2A_factor={'A':1,'nm':10, 'um':10000, 'm':10000000}
            self.unit2mW_factor={'mW':1, 'W':1000, 'uW':0.001}
            
    def close(self):
        if hasattr(self, 'ser'):
            self.ser.close()
            del self.ser

    def ask(self, cmd):
        self.write_cmd(cmd)
        response = self.ser.readline().decode().strip()     
        if self.debug:
            print (self.name, 'ask()', cmd, ' response:', repr(response))
        if 'Error' in response:
            raise IOError(self.name, 'command error: ' + repr(response))
        if response == '':
            raise IOError(self.name,  'responded empty string')
            pass
        try:
            return float(response)
        except ValueError:
            return response
        
    def write_cmd(self, cmd):
        if self.debug:print ('write_cmd():', cmd)
        cmd += '\r\n'
        self.ser.write(cmd.encode())

    #Tuning
    def write_opo_wavelength(self, wl, unit='nm'):
        '''OPO assumes Angstrom        
        '''
        wl = int(wl * self.unit2A_factor[unit])
        self.write_cmd("OPO WAVELENGTH={}".format(wl) )
        self.write_cmd('PHLDP=1')


    def read_opo_wavelength(self, unit='nm'):
        resp = self.ask('OPO WAVELENGTH?')
        return resp/self.unit2A_factor[unit]

    def read_opo_bandwidth(self, unit='nm'):
        return float(self.ask('OPO BANDWIDTH?') )/self.unit2A_factor[unit]
    
    def read_opo_spectrum(self, unit='nm'):
        '''
        TODO: FixMe The command OPO SPECTRUM does not seem to ever return something...
        '''
        ascii_resp = self.ask('OPO SPECTRUM?')
        wls = np.zeros(1024, dtype=float)
        spectrum = np.zeros(1024, dtype = float)
        print(ascii_resp)
        for i,wl_intensity in enumerate(ascii_resp.split(';')):
            wl,intensity = wl_intensity.split(' ')
            wls[i] = float(wl)
            spectrum[i] = float(intensity)
        return wls,spectrum/self.unit2A_factor[unit]

    def read_opo_power(self, unit='mW'):
        return float(self.ask('OPO POWER?') )/self.unit2mW_factor[unit]
    
    #Chameleon
    def read_pump_wavelength(self, unit='nm'):
        return float(self.ask('PUMP WAVELENGTH?') )/self.unit2A_factor[unit]
    
    def read_pump_bandwidth(self, unit='nm'):
        return float(self.ask('PUMP BANDWIDTH?'))/self.unit2A_factor[unit]
    
    def read_pump_reprate(self):
        return float(self.ask('PUMP REPRATE?') )
    
    #Shutter
    def _write_shutter(self, _open=False, shutter='PUMP IN SHUTTER'):
        '''
        Pump In Shutter (open / close)     PUMP IN SHUTTER=     1 / 0
        Pump Out Shutter (open /close)     PUMP OUT SHUTTER=    1 / 0
        OPO Out Shutter (open / close)     OPO OUT SHUTTER=     1 / 0
        Beam Splitter (Bypass / OPO)       BEAM SPLITTER=       1 / 0
        '''
        assert shutter in ['PUMP IN SHUTTER', 'PUMP OUT SHUTTER', 'OPO OUT SHUTTER', 'BEAM SPLITTER']
        n = {False:'0',True:'1'}[_open]
        return self.write_cmd( "{}={}".format(shutter,n) )
    def _read_shutter(self, shutter='OPO OUT SHUTTER'):
        '''
        ? Pump In Shutter (open / close)   PUMP IN SHUTTER?     1 / 0
        ? Pump Out Shutter (open /close)   PUMP OUT SHUTTER?    1 / 0
        ? OPO Out Shutter (open / close)   OPO OUT SHUTTER?     1 / 0
        ? Beam Splitter (Bypass / OPO)     BEAM SPLITTER?       1 / 0
        '''
        assert shutter in ['PUMP IN SHUTTER', 'PUMP OUT SHUTTER', 'OPO OUT SHUTTER', 'BEAM SPLITTER']     
        return bool(int( self.ask( "{}?".format(shutter) )))
    
    def write_pump_in_shutter(self, _open):
        self._write_shutter(_open, 'PUMP IN SHUTTER')
    def write_pump_out_shutter(self, _open):
        self._write_shutter(_open, 'PUMP OUT SHUTTER')        
    def write_opo_out_shutter(self, _open):
        self._write_shutter(_open, 'OPO OUT SHUTTER')
    def write_bypass_opo(self, _bypass): 
        '''set False to pump opp, True to bypass'''
        self._write_shutter(_bypass, 'BEAM SPLITTER')
        
    def read_pump_in_shutter(self):
        return self._read_shutter('PUMP IN SHUTTER')
    def read_pump_out_shutter(self):
        return self._read_shutter('PUMP OUT SHUTTER')        
    def read_opo_out_shutter(self):
        return self._read_shutter('OPO OUT SHUTTER') 
    def read_bypass_opo(self):
        '''returns True if opo is bypassed and False if pumped'''
        return self._read_shutter('BEAM SPLITTER')
                
    #Info            
    def read_status(self):
        '''
        reply             explanation
        ---------------   ------------------------------------------------------------
        not connected     OPO not connected
        no pump           No pump beam detected
        out of range      OPO wavelength not accessible with given pump wavelength
        wait for pump     Chameleon is currently changing its wavelength
        bypass            Beam splitter is set to bypass the OPO
        optimizing        Target wavelength reached, power optimization loop is running
        tuning (nnnn nm)  Wavelength tuning in progress (set wavelength in brackets)
        OK
        recover           Recovery routine is running
        adjusting         Pump or cavity mirrors are adjusting
        ---------------   ------------------------------------------------------------
        '''
        return self.ask('status?')
    def read_humidity(self):
        return float(self.ask('HUMIDITY?') )
    def read_temperature(self):
        return float(self.ask('TEMPERATURE?') )
    def read_error_code(self):
        return float(self.ask('ERROR?') )
    def read_IDN(self):
        return self.ask('*IDN?') 
    def read_all_parameters(self):
        return self.ask('PARAMETER?')






if __name__ == '__main__':
    try:    
        opo = ChameleonCompactOPO(port='COM24', debug=True)
        wl = opo.read_opo_wavelength()
        print(wl)
        
        opo.write_opo_wavelength(850)
        wl = opo.read_opo_wavelength()
        print(wl)
        opo.write_pump_in_shutter(True)
        opo.write_bypass_opo(False)
        
        print(str(opo.read_status()))
        print(opo.read_IDN())
        print(opo.read_status())
        print(opo.read_humidity())
        print(opo.read_opo_spectrum())
    except Exception as err:
        print(err)
    finally:
        opo.close()
    
