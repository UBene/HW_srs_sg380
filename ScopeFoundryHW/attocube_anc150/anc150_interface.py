'''
Created on Feb 23, 2017

@author: Alan Buckley
Helpful feedback from Ed Barnard and Frank Ogletree
Changes to error handling, add some error checking, relay command Frank & Ed 3/2/17
'''
from __future__ import division, absolute_import, print_function
import serial
import logging
import numpy as np
import time

logger = logging.getLogger(__name__)

class ANC_Interface(object):
    
    """
    Notes: 
        Need to handle timing for long moves, currently non-blocking
        Need to handle mode errors or power state problems
    """
    
    name="anc_interface"
    timeout = 0.1# long enough so that ANC returns multiline text response 
    modes = ['gnd','stp','ext','cap']
    
    def __init__(self, port="COM6", debug = False):
        self.port = port
        self.debug = debug
        if self.debug:
            logger.debug("ANC_Interface.__init__, port={}".format(self.port))
            
        self.ser = serial.Serial(port=self.port, baudrate=38400, bytesize=8, 
                                 parity='N', stopbits=1, timeout = 0.1)
        #self.ser.timeout = 0.1            
        #raise SerialException on fail
        

        self.position = np.zeros(6, dtype=int)
        self.freq = np.zeros(6, dtype=int)
        self.volt = np.zeros(6, dtype=int)
        self.hw_freq = np.zeros(3, dtype=int)
        self.hw_volt = np.zeros(3, dtype=int)    
        self.ground_state = None    
        self.relay = False #current relay status False for chan 0-2 or True for 3-5

        self.get_anc_hw_state()
        #FIX error handling to prompt for ANC on, channels in CCON mode

        
    def close(self):
        self.ser.close()
        del self.ser
        
    def __del__(self):
        self.close()

    #higher level functions=================================================================
    
    '''
    track state to minimize slow RS232 traffic
    virtualize 3 real channels into 6 effective channels with flip relay
    chan is between 0 and 5, axis between 1 and 3
    '''
    
    
    
    def get_anc_hw_state(self,ground=False):
        '''
        reads voltages and freqs from real channels, overloaded channels have same state
        
        '''
        for i in range(0,3):
            v = self.get_voltage(i+1)
            freq = self.get_frequency(i+1)
            self.hw_volt[i] = v
            self.volt[i] = v
            self.volt[i+3] = v
            self.freq[i] = freq
            self.freq[i+3] = freq

        self.relay = self.get_relay()
        self.ground_outputs(ground) #force known state
            
    def ground_outputs(self, state):
        '''
        ground all for low noise or to switch relay state
        '''
        if state == self.ground_state:
            return #nothing to do
        if state:
            self.ground_state = True
            self.set_axis_mode(1,'gnd')
            self.set_axis_mode(2,'gnd')
            self.set_axis_mode(3,'gnd')
        else:
            self.ground_state = False
            self.set_axis_mode(1,'stp')
            self.set_axis_mode(2,'stp')
            self.set_axis_mode(3,'stp')
    
    def select_chan(self,chan):
        '''
        checks relay state, updates relay/volts/freqs as required
        
        '''
        self.set_relay(bool(chan>=3)) #change relay state if required
        self.set_volts(self.volt) #update volts and freqs as HW state requires
        self.set_freqs(self.freq)

    def set_volts(self,volt):
        '''
        sets all 6 virtual channels, updates active HW channels only if state has changed
        '''
        self.volt = volt
        if self.relay: offset=3
        else: offset = 0
        
        for i in range(0,3):
            vset = self.volt[i+offset]
            if vset !=self.hw_volt[i]:
                self.set_voltage(i+1, vset)
                
    def get_volts(self):
        return self.volt
        
    def set_freqs(self,freq):
        '''
        sets all 6 virtual channels, updates active HW channels only if state has changed
        '''
        self.freq = freq
        if self.relay: offset=3
        else: offset = 0
        
        for i in range(0,3):
            fset = self.freq[i+offset]
            if fset !=self.hw_freq[i]:
                self.set_frequency(i+1, fset)
                
    def get_freqs(self):
        return self.freq
                
    def delta_pos(self,chan,steps,wait=False):
        '''
        increment current position by 'steps', flip relay as required
        unground during motion if required
        RS232 returns immediately, does not wait for move to finish, if
        wait is true, sleeps for estimated move time
        '''
        overhead = 0.15 #used in step wait
        if steps == 0:
            return

        prev_ground_state = self.ground_state
        self.ground_outputs(False) #could change ground state only for selected channel...
        self.select_chan(chan)
        if chan >=3:
            axis = chan - 2
        else:
            axis = chan + 1 
        self.move(axis,steps)
        self.position[chan] += steps
        if wait:
            delay = abs(steps) / float(self.freq[chan]) + overhead
            time.sleep(delay)
        self.ground_outputs(prev_ground_state)
        #FIX block with timer for motion to complete? When does function return?
    
    def goto_pos(self, chan, pos):
        self.delta_pos(chan, -self.position[chan])    
        
    def get_positions(self):
        return self.position
    
    def zero_positions(self):
        self.position = np.zeros(6, dtype=int)

    #low level functions====================================================================
    def anc_cmd(self, cmd):
        """
        Issues a command to the Attocube device.
        :returns: a list of strings from the Attocube device.
        """
        if self.debug: 
            logger.debug("anc_cmd: {}".format(cmd))
        message = cmd.encode()+b'\r\n'  #convert unicode to char() string
        self.ser.write(message)
        resp = self.ser.readlines()
        
        if len(resp) < 2:
            raise IOError( "No response from ANC 150, power off? {}".format(resp))
        
        if resp[-2] != b"OK\r\n":
            # example error string list [b'getc 1\r\n', b'Axis in wrong mode\r\n', b'ERROR\r\n', b'> ']
            err_msg = "ANC Error {} --> {}".format(cmd, resp)
            logger.error(err_msg)
            raise IOError(err_msg)
        # example success string list [b'getf 1\r\n', b'frequency = 2 Hz\r\n', b'OK\r\n', b'> '   ]
        if self.debug:
            logger.debug("anc_cmd response: {}".format(resp) )
        return resp[1:-2]   #trim command echo and OK/prompt

    def extract_value(self, resp):
        """
        Strips entry prior to terminating characters,
        Seeks out "=" sign and returns the next token 
        usually an int or a string 
        """
        entry = resp[0].strip().decode().split()
        for i in enumerate(entry):
            if i[1] == "=":
                index = i[0]
        return(entry[index+1])
    
    def get_version(self):
        """
        :returns: version number and the manufacturer.
        """
        return self.anc_cmd(b'ver')
    
    
    def get_relay(self):
        #resp is like: [b'off\r\n']
        resp = self.anc_cmd('rbctl')
        resp = resp[0].strip()
        if  resp == b'on':
            return True
        elif resp == b'off':
            return False
        else:
            raise IOError("ANC get_relay could not interpret resp {}".format(resp))
    
    def set_relay(self, state=False):
        '''
        state is a bool,
        convert to True for 4-6, false for 1-3        
        outputs must be grounded to switch inputs

        Notes:
        relay command sends 'on' or 'off'
        documentation does not specify what state should be, 0/1, true/false, etc... FIX
        '''        
        if state == self.relay:
            return  #nothing to do
        ground = self.ground_state 
        if not ground:
            self.ground_outputs(True)
        
        state_str = ['off', 'on'][state]
        resp = self.anc_cmd('rbctl {}'.format(state_str))
        if not ground:
            self.ground_outputs(False)
        self.relay = state
        return resp
    
    def set_axis_mode(self, axis_id, axis_mode):
        """
        Set axis <AID> to mode <AMODE>. Be sure to switch to the right mode
        whenever you are measuring capacitance or attempting to move the
        positioner. For sensitive, low noise measurements switch to "gnd".
        ============  ===================  ========================================
        **Argument**  **Range of values**  **Description**
        axis_id       1,2,3                One of the 3 axes offered on the ANC150.
        axis_mode     ext, stp, gnd, cap   Axis mode of the selected axis.
        ============  ===================  ========================================
        """
        if not(axis_mode in self.modes):
            err = 'requested axis mode {} is not in {}'.format(axis_mode,self.modes)
            logger.debug(err)
            raise IOError(err)
            
        message = "setm {} {}".format(axis_id, axis_mode)
        return self.anc_cmd(message)        
    
    def get_axis_mode(self, axis_id):
        """
        ============  ===================  ========================================
        **Argument**  **Range of values**  **Description**
        axis_id       1,2,3                One of the 3 axes offered on the ANC150.
        ============  ===================  ========================================
        
        :returns: The mode the corresponding axis is in.
        """
        message = "getm {}".format(axis_id)
        return self.extract_value(self.anc_cmd(message))
    
    def stop(self, axis_id):
        """
        Stop any motion on the given axis.
        
        ============  ===================  ========================================
        **Argument**  **Range of values**  **Description**
        axis_id       1,2,3                One of the 3 axes offered on the ANC150.
        ============  ===================  ========================================
        
        """
        message = "stop {}".format(axis_id)
        return self.anc_cmd(message)
    
    def move(self, axis_id, steps ):
        """
        Move 'steps', direction determined by sign, or continuously positive '+c' or negative '-c' (inwards).
        An error occurs when the axis is not in "stp" mode.
        
        ============  ===================  ============================================
        **Argument**  **Range of values**  **Description**
        axis_id       1,2,3                One of the 3 axes offered on the ANC150.
        dir           'u' or 'd'           Up or down direction flag
        c             'c' or (1,N)         'c' for continuous run or N number of steps.
        ============  ===================  ============================================
        
        """
        if steps == '+c': 
            mode = 'u'
            count = 'c'
        elif steps == '-c': 
            mode = 'd'
            count = 'c'
        else:
            if steps > 0: mode = 'u' 
            else: mode = 'd'
            count = abs(int(steps))
            
        message = "step{} {} {}".format(mode, axis_id, count)
        return self.anc_cmd(message)
        
    def set_frequency(self, axis_id, freq):
        """
        Set the frequency on axis <AID> to <FRQ>.
        
        ============  ===================  ========================================
        **Argument**  **Range of values**  **Description**
        axis_id       1,2,3                One of the 3 axes offered on the ANC150.
        frequency     (1,8000)             An integer frequency up to 8000 Hz.
        ============  ===================  ========================================

        """
        freq = min(8000,max(1,freq))
        message = "setf {} {}".format(axis_id, freq)
        self.hw_freq[axis_id-1] = freq #track state
        return self.anc_cmd(message)
    
    def get_frequency(self, axis_id):
        """
        ============  ===================  ========================================
        **Argument**  **Range of values**  **Description**
        axis_id       1,2,3                One of the 3 axes offered on the ANC150.
        ============  ===================  ========================================

        :returns: The frequency for axis <AID>.
        """
        message = "getf {}".format(axis_id)
        return int(self.extract_value(self.anc_cmd(message)))

    def set_voltage(self, axis_id, voltage):
        """
        Set the voltage on axis <AID> to <VOL>.
        
        ============  ===================  ========================================
        **Argument**  **Range of values**  **Description**
        axis_id       1,2,3                One of the 3 axes offered on the ANC150.
        voltage       (1,70)               An integer voltage up to 70 V.
        ============  ===================  ========================================

        """
        message = "setv {} {}".format(axis_id, voltage)
        self.hw_volt[axis_id-1] = voltage #track state
        return self.anc_cmd(message)    
    
    def get_voltage(self, axis_id):
        """
        ============  ===================  ========================================
        **Argument**  **Range of values**  **Description**
        axis_id       1,2,3                One of the 3 axes offered on the ANC150.
        ============  ===================  ========================================

        :returns: The voltage for axis <AID>.
        """
        message = "getv {}".format(axis_id)
        return int(self.extract_value(self.anc_cmd(message)))
    
    ''' these functions not used for now
    
    def get_capacity(self, axis_id):
        """
        ============  ===================  ========================================
        **Argument**  **Range of values**  **Description**
        axis_id       1,2,3                One of the 3 axes offered on the ANC150.
        ============  ===================  ========================================

        **Note:** You have to be in "cap" mode, otherwise an error message is given.

        :returns: The measured capacity for axis <AID>.
        """
        message = "getc {}".format(axis_id)
        resp = self.anc_cmd(message)
        return resp
    
    def set_pattern(self, axis_id, dir, pattern_number):
        """
        Set pattern number <PNUM> for upward movement or downward movement on axis <AID>.
        
        ==============  ===================  ===============================================
        **Argument**    **Range of values**  **Description**
        axis_id         1,2,3                One of the 3 axes offered on the ANC150.
        dir             'u' or 'd'           Up or down direction flag.
        pattern_number  (0,19)               Pattern number for upward or downward movement.
        ==============  ===================  ===============================================

        """
        message = "setp{} {} {}".format(dir, axis_id, pattern_number)
        resp = self.anc_cmd(message)
        return resp
        

    
    def get_pattern(self, axis_id, dir):
        """
        ==============  ===================  ========================================
        **Argument**    **Range of values**  **Description**
        axis_id         1,2,3                One of the 3 axes offered on the ANC150.
        dir             'u' or 'd'           Up or down direction flag.
        ==============  ===================  ========================================
        
        :returns: Pattern number <PNUM> for upward or downward movement on axis <AID>.
        
        """
        message = "getp{} {}".format(dir, axis_id)
        resp = self.anc_cmd(message)
        return resp

    
    def set_pattern_value(self, pattern_index, pattern_val):
        """
        Set value no. <PIDX> to value <PVAL> in the user curve.
        
        =============  ===================  ======================================================
        **Argument**   **Range of values**  **Description**
        pattern_index  (0,255)              Pattern index of choice (x-axis)
        pattern_value  (0,255)              Pattern value as a function of pattern index. (y-axis)
        =============  ===================  ======================================================
        
        """
        message = "setp {} {}".format(pattern_index, pattern_val)
        resp = self.anc_cmd(message)
        return resp
    
    def get_pattern_value(self, pattern_index):
        """
        Read value no. <PIDX> from the user curve.
        
        =============  ===================  ======================================================
        **Argument**   **Range of values**  **Description**
        pattern_index  (0,255)              Pattern index of choice (x-axis)
        pattern_value  (0,255)              Pattern value as a function of pattern index. (y-axis)
        =============  ===================  ======================================================
        
        """
        message = "getp {}".format(pattern_index)
        resp = self.anc_cmd(message)
        return resp
    
    def reset_patterns(self):
        """
        Reset all patterns to factory defaults.
        """
        message = b"Resetp"
        resp = self.anc_cmd(message)
        return resp
    
     '''   
        
        
        
        
        