"""Written by Alan Buckley 9-19-2016

Edward Barnard 9/20
"""
from __future__ import division, print_function

import serial


class ChameleonUltraIILaser(object):

    def __init__(self, port="COM7", debug=False, dummy=False): #change port according to device listing in windows.
        
        self.debug = debug
        self.dummy = dummy
        self.port = port
        
        if not self.dummy:

            self.ser = ser = serial.Serial(port=self.port, baudrate=19200, 
                                           bytesize=8, parity='N', 
                                           stopbits=1, xonxoff=False, timeout=1.0)
            #self.ser.flushInput()
            #self.ser.reset_input_buffer()
            #self.ser.flushOutput()
            #self.ser.reset_output_buffer()
            
            ser.flush()

            self.write_echo_mode(False)
            self.write_prompt(False)

            ser.flush()
            
    def close(self):
        self.ser.close()

    def write_cmd(self, cmd):
        self.ser.write(cmd+'\r\n')
        if self.debug:
            print('write:', cmd)
        response = self.ser.readline()
        if self.debug:
            print('response:', repr(response))
        if 'Error' in response:
            raise IOError('Chameleon command error: ' + repr(response))
        return response.strip()

    def write_baudrate(self, rate):
        """Sets the RS232 serial port baud rate to the
        specified value."""
        assert rate in [1200,2400,4800,9600,19200,38400,57600,115200]
        return self.write_cmd("BAUDRATE=%i" % rate)

    def write_echo_mode(self, echo=False):
        """Toggle Echo mode. Note: A change in echo mode takes 
        effect with the first command sent after the echo command."""
        if echo:
            n = 1
        else:
            n = 0
        return self.write_cmd("ECHO=%i" % n)

    def write_laser_flash(self):
        """Flash Verdi laser output below lasing threshold to allow 
        single frequency mode to recenter."""
        return self.write_cmd("FLASH=%i" % 1)

    def write_home_stepper(self):
        """Homes the tuning motor. This can take 3 to 30 seconds."""
        return self.write_cmd("HOME STEPPER=%i" % 1)

    def write_laser(self, active=False):
        """Allows user to activate laser or place it in standby mode.
        Activating laser resets faults and powers on laser. Lasing resumes
        of there are no active faults. Keyswitch must be in ON position for
        operation of laser."""
        if active:
            n = 1
        else:
            n = 0
        return self.write_cmd("LASER=%i" % n)

    def write_LBO_heater(self, active=False):
        "Turns LBO heater on/off."
        if active:
            n = 1
        else:
            n = 0
        return self.write_cmd("LBO HEATER=%i" % n)

    def write_LBO_optimize(self, active=False):
        """Begins optimization routine. If run with active flag, 
        device begins optimization routine."""
        if active:
            n = 1
        else:
            n = 0
        return self.write_cmd("LBO OPTIMIZE=%i" % n)

    def write_front_panel_lock(self, enabled=False):
        """Enables/disables user input from the front panel."""
        if enabled:
            n = 0 #No, this isn't a typo according to the manual.
        else:
            n = 1 
        return self.write_cmd("LOCK FRONT PANEL=%i" % n)

    def write_prompt(self, enabled=False):
        """Turns "CHAMELEON>" prompt on/off."""
        if enabled:
            n = 1
        else:
            n = 0
        self.write_cmd("PROMPT=%i" % n)

    def write_search_modelock(self, enabled=True):
        """Enables/disables search for modelocking."""
        if enabled:
            n = 0
        else:
            n = 1
        return self.write_cmd("SEARCH MODELOCK=%i" % n)

    def write_shutter(self, _open=False):
        """Changes state of external shutter."""
        if _open:
            n = 1
        else:
            n = 0
        return self.write_cmd("SHUTTER=%i" % n)

    def write_wavelength(self, _lambda):
        """Sets the Chameleon Ultra wavelength to the specified 
        value in nanometers. If the specified wavelength is 
        beyond the allowed range of wavelengths, the wavelength 
        is set to either the upper or lower limit. (Whichever 
            is closer to the specified wavelength."""
        wl = int(_lambda)
        return self.write_cmd("WAVELENGTH=%i" % wl)
        
    def read_wavelength(self):
        resp = self.write_cmd('PRINT WAVELENGTH')
        #print (format(repr(resp)))
        print('read_wavelength {}'.format(repr(resp)))
        return float(resp)

    def write_wavelength_step(self, _delta):
        """Changes Chameleon Ultra wavelength by the specified amount in nanometers."""
        delta = int(_delta)
        return self.write_cmd("WAVELENGTH STEP=%i" % delta)

    def write_heartbeat(self, enabled=False):
        """Heartbeat is defined by the manufacturer as a timeout 
        for laser operation. When heartbeat is enabled, laser 
        shuts down in absence of RS232 activity after a set duration."""
        if enabled:
            n = 1
        else:
            n = 0
        return self.write_cmd("HEARTBEAT=%i" % n)

    def write_heartbeat_rate(self, timeout):
        """Heartbeat is defined by the manufacturer as a timeout 
        for laser operation. Heartbeat rate is defined as the laser 
        timeout in seconds. Range: 1 to 100 s."""
        assert 1 <= timeout <= 100
        return self.write_cmd("HEARTBEATRATE=%i" % int(timeout))

    def write_recovery_sequence(self):
        """Initiates recovery sequence. This can take up to 2 minutes to complete."""
        return self.write_cmd("RECOVERY=%i" % 1)

    def write_alignment_mode(self, enabled=True):
        """Enables alignment mode. Exits alignment mode otherwise."""
        if enabled:
            n = 1
        else:
            n = 0
        return self.write_cmd("ALIGN=%i" % n)
        
    def read_uf_power(self):
        #resp = self.write_cmd('PRINT UF POWER')
        resp = self.write_cmd('?UF')
        return float(resp)

if __name__ == '__main__':

    try:    
        laser = ChameleonUltraIILaser(port='COM7', debug=True)
        wl = laser.read_wavelength()
        print(wl)
        
        laser.write_wavelength(850)
        wl = laser.read_wavelength()
        print(wl)
        
        print(laser.read_uf_power())
    
    except Exception as err:
        print(err)
    finally:
        laser.close()
    
