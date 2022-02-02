import serial
from collections import OrderedDict
from threading import Lock
import numpy as np


BAUDRATE = 115200
TIMEOUT = 0.1 
BYTESIZE = 8
PARITY = 'N'
STOPBITS = 1
XONXOFF = 0
RTSCTS = 0
TERMINATOR = '\r\n'

DC4100_Status = OrderedDict([
        ('(VCC fail) Power supply is out of range.', 0x00000002),
        ('(OTP) Overheating chassis. All LEDs off.', 0x00000008),
        ('(No LED1)', 0x00000020),
        ('(No LED2)', 0x00000080),
        ('(No LED3)', 0x00000200),
        ('(No LED4)', 0x00000800),
        ('(LED1 Open) LED1 off. Maximum forward voltage reached. Reduce current.', 0x00002000),
        ('(LED2 Open) LED2 off. Maximum forward voltage reached. Reduce current.', 0x00008000),
        ('(LED3 Open) LED3 off. Maximum forward voltage reached. Reduce current.', 0x00020000),
        ('(LED4 Open) LED4 off. Maximum forward voltage reached. Reduce current.', 0x00008000),
        ('(Limit LED1) LED1 reached current limit. Decrease the input voltage.', 0x00200000),
        ('(Limit LED1) LED2 reached current limit. Decrease the input voltage.', 0x00800000),
        ('(Limit LED1) LED3 reached current limit. Decrease the input voltage.', 0x02000000),
        ('(Limit LED1) LED4 reached current limit. Decrease the input voltage.', 0x08000000),
    ])

DC4100_OperationModes = ['Constant Current Mode', 'Brightness Mode', 'External Control Mode']
DC4100_SupportedModels = ['DC4100', 'DC4104']

class ThorlabsDC4100(object):
    """
    A pyserial driven interface to the Thorlabs DC4100 controllers. 
    
    Credit to Olaf Wohlmann and their uManager plugin for nicely wrapping the undocumented serial commands. 
    
    Chris Chen
    christopherchen@lbl.gov
    """
    LEDS = [True, True, True, True]
    
    def __init__(self, port='COM3', debug=False):
        """
        Constructor for the serial interface to the DC4100 controllers. 
        
        Keyword Arguments:
            port (str): serial port address of DC4100
            debug (bool): enable/disable debug mode 
        """
        self.ser = serial.Serial(port, timeout=TIMEOUT, baudrate=BAUDRATE, 
                                 bytesize=BYTESIZE, parity=PARITY, stopbits=STOPBITS, 
                                 xonxoff=XONXOFF, rtscts=RTSCTS)
        self.debug = debug
        if self.debug: print(self.ser)
        if self.validate == False:
            print('DC4100: Invalid device at port %s' % port)
            self.disconnect()
            return
        self.lock = Lock()
        self.info()
        
    def ask(self,cmd):
        """
        Sends a command with the terminator over the interface and returns a string without the terminator. 

        Arguments:
            cmd (str): command to send
            
        Returns:
            resp (str): response from DC4100
        """
        with self.lock:
            if self.debug: print('DC4100: Sending %s' % cmd)
            self.ser.write(bytes(cmd + TERMINATOR, 'utf-8'))
            resp = self.ser.readline()
            if self.debug: print('DC4100: Received', resp)
            return resp.decode()[:-len(TERMINATOR)]
        
    def info(self):
        """
        Prints DC4100 details and status.
        """
        name = self.ask('n?')
        sn = self.ask('s?')
        ver = self.ask('v?')
        print('Thorlabs %s, serial # %s, firmware version %s' % (name, sn, ver))
        self.read_status()
        print(DC4100_OperationModes[self.get_operation_mode()])
        if self.get_multiselection_mode():
            print('Multiselection mode on')
        for LED in np.nonzero(self.LEDS)[0]+1:
            if self.get_LED_status(LED):
                led_str = '(on)\t'
            else: 
                led_str = '(off)\t'
                 
            led_str = led_str + 'LED %d: ' % LED
            
            wl = self.get_LED_wavelength(LED)
            if wl > 0:
                led_str = led_str + '%0.0f nm, ' % wl
            else: 
                led_str = led_str + 'WL, '

            if self.get_operation_mode() == 1:
                led_str = led_str + 'output set to %0.0f%s' % (self.get_LED_brightness(LED),'%')
            
            print(led_str)
        
    def validate(self):
        """
        Checks if the instrument receiving serial commands is supported. 
        
        Returns:
            result (bool): if the instrument is supported
        """
        name = self.ask('n?')
        if name in DC4100_SupportedModels:
            return True
        else:
            return False
        
    def get_status(self):
        return int(self.ask('r?'))
        
    def read_status(self):
        reg = self.get_status()
        err = []
        for key in DC4100_Status.keys():
            if reg & DC4100_Status[key] > 0:
                err.append(key)
                if '(No LED' in key:
                    self.LEDS[int(key[-2])-1] = False
                    if self.debug: print(key)
                else:
                    print('DC4100 Status:', key)
        return err.copy()
        
    def disconnect(self):
        self.ser.close()
        
    def get_operation_mode(self):
        return int(self.ask('m?'))
    
    def set_operation_mode(self, mode):
        assert mode in [0,1,2]
        self.ask('m %d' % mode)
        
    def get_LED_status(self, LED):
        assert LED in np.nonzero(self.LEDS)[0]+1
        return bool(int(self.ask('o? %d' % (LED-1))))
    
    def set_LED_status(self, LED, val):
        assert LED in np.nonzero(self.LEDS)[0]+1 and isinstance(val, bool)
        self.ask('o %d %d' % (LED-1, int(val)))
        
    def get_LED_wavelength(self, LED):
        assert LED in np.nonzero(self.LEDS)[0]+1
        return float(self.ask('wl? %d' % (LED-1)))
    
    def get_LED_brightness(self, LED):
        assert LED in np.nonzero(self.LEDS)[0]+1
        return float(self.ask('bp? %d' % (LED-1)))
    
    def set_LED_brightness(self, LED, val):
        assert LED in np.nonzero(self.LEDS)[0]+1 and val <= 100 and val >= 0
        self.ask('bp %d %f' % (LED-1, val))
    
    def get_multiselection_mode(self):
        return bool(int(self.ask('sm?')))
    
    def set_multiselection_mode(self, val):
        assert isinstance(val, bool)
        self.ask('sm %d' % val)
        
if __name__ == '__main__':
    try:
        ctrlr = ThorlabsDC4100(debug=False)
        ctrlr.set_LED_brightness(1,50)
        ctrlr.set_LED_brightness(2,0)
        ctrlr.set_LED_status(1,True)
        ctrlr.info()
        ctrlr.set_LED_brightness(1,25)
        ctrlr.set_LED_brightness(2,25)
        ctrlr.set_LED_status(1,False)
        ctrlr.disconnect()
    except Exception as ex:
        print('Error: ', ex)
        