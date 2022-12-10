"""Written by Alan Buckley 9-19-2016

Edward Barnard 9/20
"""
from __future__ import division, print_function
import serial
import time
import numpy


class ChameleonUltraIILaser(object):

    def __init__(self, port, debug=False, dummy=False): #change port according to device listing in windows.
        
        self.debug = debug
        self.dummy = dummy
        self.port = port
        
        if not self.dummy:

            self.ser = ser = serial.Serial(port=self.port, baudrate=19200, 
                                           bytesize=8, parity='N', 
                                           stopbits=1, xonxoff=False, timeout=1.0)
            self.ser.flushInput()
            #self.ser.reset_input_buffer()
            self.ser.flushOutput()
            #self.ser.reset_output_buffer()
            
            ser.flush()

            self.write_echo_mode(False)
            self.write_prompt(False)

            ser.flush()
            
    def close(self):
        self.ser.close()

    def write_cmd(self, cmd):
        serialcmd = cmd+'\r\n'
        #print(serialcmd)
        #print('cmd done')
        self.ser.write(serialcmd.encode())
        #self.ser.write(cmd+'\r\n')
        if self.debug:
            print ('write:', cmd)
        response = self.ser.readline()
        if self.debug:
            print ('response:', repr(response))
        if 'Error'.encode() in response:
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
        return self.write_cmd("HM=%i" % 1)
    
    def write_home_slit_stepper(self):
        """Homes the tuning motor. This can take 3 to 30 seconds."""
        return self.write_cmd("HMSLIT=%i" % 1)

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
            n = 1
        else:
            n = 0
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
        print('read_wavelength {}'.format(repr(resp.decode())))
        return float(resp.decode())

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
    
    def write_alignment_mode_wavelength(self, _lambda):
        'Set alignment mode wavelength'
        wl = int(_lambda)
        return self.write_cmd("ALIGNW=%i" % wl)
    
    def read_alignment_mode_wavelength(self):
        resp = self.write_cmd('?ALIGNW')
        return int(resp)
        
    
    def write_auto_modelock(self, enabled = True ):
        'Try to enable and disenable modelock'
        if enabled:
            n = 1
        else:
            n = 0
        return self.write_cmd("AMDLK=%i" % n)
    
    def read_auto_modelock(self):
        'Returns the status of the automodelock routing'
        resp = self.write_cmd('?AMDLK')
        if int(resp) == 1:
            auto_modelock = 'Enabled'
        if int(resp) == 0:
            auto_modelock = 'Disabled'
        return auto_modelock    
        
    def read_uf_power(self):
        #resp = self.write_cmd('PRINT UF POWER')
        resp = self.write_cmd('?UF')
        return float(resp)
    
    def read_tuning_status(self):
        resp = self.write_cmd('?TS')
        if int(resp) == 0:
            tuning_stat = 'Ready'
        if int(resp) == 1:
            tuning_stat = 'Tuning in progress'
        if int(resp) == 2:
            tuning_stat = 'Search for Modelock in progress'
        if int(resp) == 3:
            tuning_stat = 'Recovery operation in progress'
        print("Chameleon laser tuning status: {}".format(tuning_stat))
        return tuning_stat
    
    def read_shutter(self):
        resp = self.write_cmd('?S')
        if int(resp) == 0:
            shutter_stat = False #'Closed'
        if int(resp) == 1:
            shutter_stat = True #'Open'
        return shutter_stat
    
    def read_modelocked(self):
        'return the current modelock status'
        resp = self.write_cmd('?MDLK')
        if int(resp) == 0:
            mdlk = 'Off(Standby)'
        if int(resp) == 1:
            mdlk = 'ModeLocked'
        if int(resp) == 2:
            mdlk = 'CW'
        return mdlk
    
    def read_search_modelock(self):
        'return the status of searching for modelock'
        resp = self.write_cmd('?SM')
        if int(resp) == 0:
            sm = 'SM Disabled'
        if int(resp) == 1:
            sm = 'SM Enabled'
        return sm
    
    def read_stepper_pos(self):
        'returns the position (counts) that the motor was last moved to for a desired tuning'
        resp = self.write_cmd('?STPRPOS')
        return int(resp)
    
    def read_alignment_mode(self):
        'returns the status of alignment mode'
        resp = self.write_cmd('?ALIGN')
        if int(resp) == 1:
            align_mode = True
        if int(resp) == 0:
            align_mode = False
        return align_mode
    
    def home_motor(self):
        'Homes the tuning motor. This action can take 3-30 secons'
        n = 1
        return self.write_cmd("HM=%i" % n)
    
    def read_homed(self):
        'Returns the homing status of the tuning motor 0=Has not been homed; 1=Has been homed'
        resp = self.write_cmd('?HM')
        if int(resp) == 1:
            homed = True
        if int(resp) == 0:
            homed = False
        return homed
    

        
        
        
        

    
        

if __name__ == '__main__':
    
    def status_checking(dead_time):
        ################ Status Waiting Loop ####################
        flag = 0 
        time0 = time.time()
        time.sleep(3)
        time_elapse = time.time()-time0
        while (laser.read_tuning_status() != 'Ready') and (time_elapse < dead_time) :
            time.sleep(3)
            time_elapse = time.time()-time0
        if time_elapse > dead_time:
            print ('*********Warning: exceeding dead time')
            flag = 1
            raise ('Error: tuning status not ready')
        return flag
        ###########################################################
        
    def modelock_CW_checking(dead_time):
        ################### Check if the modelock has been set to CW ###########
        flag = 0
        time0 = time.time()
        time.sleep(3)
        time_elapse = time.time()-time0
        while (laser.read_modelocked() != 'CW') and (time_elapse < dead_time) :
            time.sleep(3)
            time_elapse = time.time()-time0
        if time_elapse > dead_time:
            print ('*********Warning: exceeding dead time for setting CW')
            flag = 1
            raise ('Error: CW not set')
        return flag
        
        

    try:    
        laser = ChameleonUltraIILaser(port='COM7', debug=True)
        
        wl0=750
        dead_t = 30
        
        #laser.write_alignment_mode(enabled=False)
        laser.write_shutter(_open=True)
        laser.write_wavelength(wl0)
        print('*********setting initial wavelength to: {}'.format(wl0))
        ################################################
        dead_check = status_checking(dead_time = dead_t)

        
        laser.write_alignment_mode(enabled=True)
        laser.write_shutter(_open=True)
        print('*********Enabling alignment mode')
        
        ###############################################
        dead_check = status_checking(dead_time = dead_t)
        dead_check_CW = modelock_CW_checking(dead_time = dead_t)

        print('*********Initial alignment modelock status:{}'.format(laser.read_modelocked()))
        
        
        wl_set = numpy.linspace(690, 980, 10)
        ##################################################
        for wl in wl_set:
            
            #laser.write_wavelength(wl)
            #time.sleep(5)
            
            laser.write_alignment_mode_wavelength(wl)
            ###############################################
            dead_check = status_checking(dead_time = dead_t)
            dead_check_CW = modelock_CW_checking(dead_time = dead_t)

            print('*********alignment wavelength reading: {}'.format(laser.read_alignment_mode_wavelength()) ) 
            print('*********laser wavelength reading: {}'.format(laser.read_wavelength()) )
            print('*********alignment modelock status reading:{}'.format(laser.read_modelocked()))
        ################################################    
        
        laser.write_alignment_mode(enabled=False)
        time.sleep(5)
        laser.write_wavelength(wl0)
        time.sleep(5)


    
    except Exception as err:
        print(err)
    finally:
        laser.close()
    
