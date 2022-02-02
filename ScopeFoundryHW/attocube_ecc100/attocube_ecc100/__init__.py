from __future__ import division, print_function
import ctypes
from ctypes import (c_int, c_int32, c_int16, c_uint32, c_int64, 
                    c_byte, c_ubyte, c_short, c_double, cdll, pointer, 
                    byref)
import os
import time
import numpy as np
from collections import namedtuple
from threading import Lock
ecc = cdll.LoadLibrary(
        os.path.abspath(os.path.join(
                         os.path.dirname(__file__),
                         r"ECC100_Library\Win64\ecc.dll")))

# /** Return values of functions */
#define NCB_Ok                   0              /**< No error                              */
#define NCB_Error              (-1)             /**< Unspecified error                     */
#define NCB_Timeout              1              /**< Communication timeout                 */
#define NCB_NotConnected         2              /**< No active connection to device        */
#define NCB_DriverError          3              /**< Error in comunication with driver     */
#define NCB_DeviceLocked         7              /**< Device is already in use by other     */
#define NCB_InvalidParam         9              /**< Parameter out of range                */
#define NCB_FeatureNotAvailable 10              /**< Feature only available in pro version */

NCB_ERROR_CODES = {
                   0: "NCB_Ok",
                   -1:"NCB_Error",
                   1: "NCB_Timeout",
                   2: "NCB_NotConnected",
                   3: "NCB_DriverError",
                   7: "NCB_DeviceLocked",
                   9: "NCB_InvalidParam",
                   11: "NCB_InvalidParam",
                   12:"NCB_FeatureNotAvailable"
                   }

ECC_ACTOR_TYPES = [
     "ECC_actorLinear",                           
     "ECC_actorGonio",                            
     "ECC_actorRot"]

def handle_err(retcode):
    if retcode != 0:
        raise IOError(NCB_ERROR_CODES[retcode])
    return retcode

EccDevInfo = namedtuple("EccDevInfo", ("dev_num", "dev_id", "dev_locked"))

def ecc_enumerate():
    'check for number of connected devices'
    num_devices = ecc.ECC_Check(0)
    ecc_devices = []
    for i in range(num_devices):        
        ## Int32 NCB_API ECC_getDeviceInfo( Int32 deviceNo, Int32 * devId, Bln32 * locked );
        dev_id = ctypes.c_int32()
        locked = ctypes.c_int32()
        ecc.ECC_getDeviceInfo( i, ctypes.byref(dev_id), ctypes.byref(locked) );
        ecc_devices.append(EccDevInfo( i, dev_id.value, locked.value))
        ##print( i, dev_id.value, locked.value)
    return ecc_devices


class EccInfo(ctypes.Structure):
    _fields_ = [
                ("id", c_int32),
                ("locked", c_int32),]
    _pack_ = 1 # Important for field alignment, might be wrong


class AttoCubeECC100(object):
    
    def __init__(self, device_num=0, device_id = None, debug=False):
        self.debug = debug
        self.device_num = device_num
        self.lock = Lock()
        
        if self.debug:
            print("Initializing AttoCubeECC100 device ", device_num)
        
        #self.num_devices = ecc.ECC_Check()
        self.dev_list = ecc_enumerate()
        
        # if device_id is defined, find the appropriate device_num
        if device_id is not None:
            dev_id_found = False
            for dev in self.dev_list:
                if dev.dev_id == device_id:
                    self.device_num = dev.dev_num
                    self.device_id = dev.dev_id
                    dev_id_found = True
            if not dev_id_found:
                ## no device based on ID found
                raise IOError("AttoCubeECC100 No Device found based on device_id={}".format(device_id))
        else:
            self.device_id = self.dev_list[self.device_num].dev_id
                    
        assert 0 <= self.device_num < len(self.dev_list), "Attocube device num out of range: {} of {}".format(self.device_num, len(self.dev_list))

        # check if device is locked
        assert not self.dev_list[self.device_num].dev_locked
        
        # Connect to Device
        self.devhandle = c_uint32()
        with self.lock:
            handle_err(ecc.ECC_Connect(self.device_num,byref(self.devhandle)))

        self.device_id = self.read_device_id()
        
        self.pro = self.pro_version_check()
        
        
    def close(self):
        handle_err(ecc.ECC_Close(self.devhandle))

    def pro_version_check(self):
        try:
            self.read_enable_auto_update_reference(0)
            return True
        except IOError as err:
            #probably should check if error is due to something else other than missing pro mode
            return False

    def read_actor_info(self, axis):
        return self.read_actor_name(axis), self.read_actor_type(axis)
    
    def read_actor_name(self,axis):
        actor_name = ctypes.create_string_buffer(20)
        with self.lock:
            handle_err(ecc.ECC_getActorName(
                                self.devhandle,
                                axis, # Int32 axis
                                byref(actor_name), # char * name
                                ))
        return actor_name.value.decode('ascii').strip()
    
    def read_actor_type(self,axis):
        actor_type_id = c_int32()
        with self.lock:
            handle_err(ecc.ECC_getActorType(
                                self.devhandle,
                                axis, # Int32 axis
                                byref(actor_type_id) #ECC_actorType * type (enum)
                                ))
        return ECC_ACTOR_TYPES[actor_type_id.value]

    def read_device_id(self):
        dev_id = ctypes.c_int32()
        with self.lock:
            handle_err(ecc.ECC_controlDeviceId(self.devhandle, byref(dev_id), False))
        return dev_id.value

    def read_enable_axis(self, axis):
        cenable = c_int32()
        with self.lock:
            handle_err(ecc.ECC_controlOutput(self.devhandle,
                                     axis, #axis
                                     byref(cenable), #Bln32 * enable,
                                     0, # read
                                     ))
        return cenable.value
        
    def enable_axis(self, axis, enable=True):
        cenable = c_int32(int(enable))
        with self.lock:
            handle_err(ecc.ECC_controlOutput(self.devhandle,
                                     axis, #axis
                                     byref(cenable), #Bln32 * enable,
                                     1, # set
                                     ))
        
    def read_enable_closedloop_axis(self, axis):
        cenable = c_int32()
        with self.lock:
            handle_err(ecc.ECC_controlMove(self.devhandle,
                                     axis, #axis
                                     byref(cenable), #Bln32 * enable,
                                     0, # read
                                     ))
        return cenable.value
        
    def enable_closedloop_axis(self, axis, enable=True):
        cenable = c_int32(int(enable))
        with self.lock:
            handle_err(ecc.ECC_controlMove(self.devhandle,
                                     axis, #axis
                                     byref(cenable), #Bln32 * enable,
                                     1, # set
                                     ))


    def single_step(self, axis, direction=True):
        """direction True (or >0): forward, False (or <=0): backward"""
        backward= (direction <= 0)
        #backward: Selects the desired direction. False triggers a forward step, true a backward step.
        with self.lock:  
            handle_err(ecc.ECC_setSingleStep(self.devhandle, # device handle
                                     axis,  # axis
                                     int(backward))) #backward (direction control)

    def single_step_forward(self, axis):
        self.single_step(axis, True)
    def single_step_backward(self, axis):
        self.single_step(axis, False)


    def read_position_axis(self, axis):
        """returns position in mm, device speaks nm
        """
        pos = c_int32()
        with self.lock:
            handle_err(ecc.ECC_getPosition( 
                                    self.devhandle, #Int32 deviceHandle,
                                    axis, #Int32 axis,
                                    byref(pos))) #Int32* position );
            return pos.value*1e-6


    def is_electrically_connected(self, axis):
        """Connected status.

        Retrieves the connected status. Indicates whether an actor is eletrically connected to the controller.
        """
        connected = c_int32()
        with self.lock:
            handle_err(ecc.ECC_getStatusConnected(
                                    self.devhandle,
                                    axis,
                                    byref(connected)))
            return bool(connected.value)

    def read_reference_position(self, axis):
        """returns position in mm, device speaks nm
        """
        refpos = c_int32()
        with self.lock:
            handle_err(ecc.ECC_getReferencePosition(
                                    self.devhandle,
                                    axis, #Int32 axis
                                    byref(refpos), #Int32* reference
                                    ))
            return refpos.value*1e-6

    def read_reference_status(self, axis):
        """
        Reference status.

        Retrieves the status of the reference position. It may be valid or invalid.
        """
        valid = c_int32()
        with self.lock:
            handle_err(ecc.ECC_getStatusReference(
                                      self.devhandle,
                                      axis,
                                      byref(valid)))
            return bool(valid.value)
    
    def read_target_range_axis(self, axis):
        raise NotImplementedError()
    
    def write_target_position_axis(self, axis, target_pos):
        """ position in mm, device speaks nm
        """
        tpos = c_int32(int(target_pos*1e6))
        with self.lock:
            handle_err(ecc.ECC_controlTargetPosition(
                                self.devhandle,
                                axis, #Int32 axis
                                byref(tpos), # Int32* target
                                1, #Bln32 set
                                ))
        time.sleep(0.000010)
        return tpos.value*1e-6
                   
    def read_target_position_axis(self, axis):
        tpos = c_int32()
        with self.lock:
            handle_err(ecc.ECC_controlTargetPosition(
                                self.devhandle,
                                axis, #Int32 axis
                                byref(tpos), # Int32* target
                                0, #Bln32 set
                                ))
        if self.debug: print('ecc100 read_target_position_axis', axis, tpos.value)

        return tpos.value*1e-6
    
    def read_target_status(self, axis):
        """
        Target status. 

        Retrieves the target status. Indicates whether the actual 
        position is within the target range.
        """
        target_status = c_uint32()
        with self.lock:
            handle_err(ecc.ECC_getStatusTargetRange(
                                self.devhandle,
                                axis, #Int32 axis
                                byref(target_status), # Bln32* target                            
                                ))
        return bool(target_status.value)

    def read_eot_back_status(self, axis):
        """
        Target status. 

        Retrieves eot end of travel status (pro).
        """
        eot_status = c_uint32()
        with self.lock:
            handle_err(ecc.ECC_getStatusEotBkwd(
                                self.devhandle,
                                axis, #Int32 axis
                                byref(eot_status), # Bln32* target                            
                                ))
        return bool(eot_status.value)

    def read_eot_forward_status(self, axis):
        """
        Target status. 

        Retrieves eot end of travel status (pro).
        """
        eot_status = c_uint32()
        with self.lock:
            handle_err(ecc.ECC_getStatusEotFwd(
                                self.devhandle,
                                axis, #Int32 axis
                                byref(eot_status), # Bln32* target                            
                                ))
        return bool(eot_status.value)

    def read_eot_stop_status(self, axis):
        """
        Target status. 

        Retrieves eot end of travel status (pro).
        """
        eot_status = c_uint32()
        with self.lock:
            handle_err(ecc.ECC_controlEotOutputDeactive(
                                self.devhandle,
                                axis, #Int32 axis
                                byref(eot_status), # Bln32* target  
                                0, #set                          
                                ))
        return bool(eot_status.value)
    
    def enable_eot_stop(self, axis, enable):
        """
        Target status. 

        Retrieves eot end of travel status (pro).
        """
        eot_status = c_uint32(enable)
        with self.lock:
            handle_err(ecc.ECC_controlEotOutputDeactive(
                                self.devhandle,
                                axis, #Int32 axis
                                byref(eot_status), # Bln32* target  
                                1, #set                          
                                ))
        return bool(eot_status.value)

    def read_enable_eot_stop(self, axis ):
        """
        Target status. 

        Retrieves eot end of travel status (pro).
        """
        eot_status = c_uint32()
        with self.lock:
            handle_err(ecc.ECC_controlEotOutputDeactive(
                                self.devhandle,
                                axis, #Int32 axis
                                byref(eot_status), # Bln32* target  
                                0, #set                          
                                ))
        return bool(eot_status.value)

    def read_frequency(self, axis):
        """returns Frequency in Hz, device speaks mHz"""
        freq = c_int32()
        with self.lock:
            handle_err(ecc.ECC_controlFrequency(
                                self.devhandle,
                                axis, #Int32 axis
                                byref(freq), #Int32* frequency
                                0, # Bln32 set
                                ))
        return freq.value*1e-3
    
    def write_frequency(self,axis, frequency):
        """freq: Frequency in mHz"""
        freq = c_int32(int(frequency*1e3))
        with self.lock:
            handle_err(ecc.ECC_controlFrequency(
                                self.devhandle,
                                axis, #Int32 axis
                                byref(freq), #Int32* frequency
                                1, # Bln32 set
                                ))
        return freq.value*1e-3
        
    def read_openloop_voltage(self, axis):
        """ Read open loop analog voltage adjustment
        
        returns voltage in V, unit speaks uV
        
        requires Pro version
        """
        ol_volt = c_int32()
        with self.lock:
            handle_err(ecc.ECC_controlFixOutputVoltage(
                                self.devhandle,
                                axis,
                                byref(ol_volt),# Int32 * voltage
                                0, #set
                                ))
        return ol_volt.value*1e-6
    
    def write_openloop_voltage(self, axis, voltage):
        """ Write open loop analog voltage adjustment
            voltage in V, unit speaks uV
        """
        ol_volt = c_int32(voltage*1e6)
        with self.lock:
            handle_err(ecc.ECC_controlFixOutputVoltage(
                                self.devhandle,
                                axis,
                                byref(ol_volt),# Int32 * voltage
                                1, #set
                                ))
        return ol_volt.value*1e-6

    def enable_ext_trigger(self, axis):
        raise NotImplementedError()

    def start_continuous_motion(self, axis, direction):
        """
        + 1 continuous motion start in Forward (+) direction
        - 1 continuous motion start in Backward (-) direction
        0   stop continuous motion
        
        Int32 NCB_API ECC_controlContinousFwd( Int32 deviceHandle,
                                       Int32 axis,
                                       Bln32* enable,
                                       Bln32 set );
        """
        c_enable = c_int32(1) # true to start motion
        if direction > 0:
            if self.lock:
                handle_err(ecc.ECC_controlContinousFwd(self.devhandle, axis, byref(c_enable), 1))
        elif direction < 0:
            if self.lock:
                handle_err(ecc.ECC_controlContinousBkwd(self.devhandle, axis, byref(c_enable), 1))
        else:
            self.stop_continous_motion(axis)
        
    def stop_continous_motion(self, axis):
        
        """The parameter "false" stops all movement of the axis regardless its direction.
        """
        c_enable = c_int32(0) # stop motion
        with self.lock:
            handle_err(ecc.ECC_controlContinousFwd(self.devhandle, axis, byref(c_enable), 1))


    def read_continuous_motion(self, axis):
        """ returns +1, 0, or -1
         + 1 continuous motion happening in Forward  (+) direction
         - 1 continuous motion happening in Backward (-) direction
           0 continuous motion stopped
        """

        c_enable = c_int32()
        with self.lock:
            handle_err(ecc.ECC_controlContinousFwd(self.devhandle,
                                     axis, #axis
                                     byref(c_enable), #Bln32 * enable,
                                     0, # read
                                     ))
        if c_enable.value:
            return +1
        
        c_enable = c_int32()
        with self.lock:
            handle_err(ecc.ECC_controlContinousBkwd(self.devhandle,
                                     axis, #axis
                                     byref(c_enable), #Bln32 * enable,
                                     0, # read
                                     ))
        if c_enable.value:
            return -1
        
        return 0
        
    
    def read_enable_auto_update_reference(self, axis):
        c_enable = c_int32()
        with self.lock:
            handle_err(ecc.ECC_controlReferenceAutoUpdate(self.devhandle,
                                     axis, #axis
                                     byref(c_enable), #Bln32 * enable,
                                     0, # read
                                     ))
        return c_enable.value
        
    def enable_auto_update_reference(self, axis, enable=True):
        c_enable = c_int32(enable)
        with self.lock:
            handle_err(ecc.ECC_controlReferenceAutoUpdate(self.devhandle,
                                     axis, #axis
                                     byref(c_enable), #Bln32 * enable,
                                     1, # set
                                     ))
        return c_enable.value
        
    def read_enable_auto_reset_reference(self, axis):
        c_enable = c_int32()
        with self.lock:
            handle_err(ecc.ECC_controlAutoReset(self.devhandle,
                                     axis, #axis
                                     byref(c_enable), #Bln32 * enable,
                                     0, # read
                                     ))
        return c_enable.value
        
    def enable_auto_reset_reference(self, axis, enable=True):
        c_enable = c_int32(enable)
        with self.lock:
            handle_err(ecc.ECC_controlAutoReset(self.devhandle,
                                     axis, #axis
                                     byref(c_enable), #Bln32 * enable,
                                     1, # set
                                     ))
        return c_enable.value
        
    def read_step_voltage(self, axis):
        """
        Control amplitude in V, device uses mV

        Read the amplitude of the actuator signal.

        """
        ampl = c_int32()
        with self.lock:
            handle_err(ecc.ECC_controlAmplitude(
                                self.devhandle,
                                axis, # Int32 axis
                                byref(ampl), #Int32* amplitude
                                0, #set
                                ))
        return ampl.value*1e-3
        
    def write_step_voltage(self, axis, volts=30):
        """
        Control amplitude in V, device uses mV

        Read the amplitude of the actuator signal.

        """
        ampl = c_int32(int(volts*1e3))
        with self.lock:
            handle_err(ecc.ECC_controlAmplitude(
                                self.devhandle,
                                axis, # Int32 axis
                                byref(ampl), #Int32* amplitude
                                1, #set
                                ))
        return ampl.value*1e-3
        
    
    def reset_axis(self,axis):
        """
        Reset position.

        Resets the actual position to zero and marks the reference position as invalid.
        
        """
        with self.lock:
            handle_err(ecc.ECC_setReset(self.devhandle, axis))
    
    
#ecc_infos = np.ones(10, dtype=c_uint32)
#num_devices = ecc.ECC_Check(ecc_infos.ctypes)

#print repr(num_devices)
#print ecc_infos



if __name__ == '__main__':
    
    dev_list = ecc_enumerate()
    print("Devices Found", len(dev_list))

    for i in range(len(dev_list)):
        print( 'ECC device ', dev_list[i])
    print('\r')
    
    for i in range(len(dev_list)):
        print( " ")
        e = AttoCubeECC100(device_num=i, debug=True)
    
        print("dev id:", e.read_device_id())
        
        print( 'ECC device ', dev_list[i])
        print( "="*40)
        for ax in [0,1,2]:
            print(ax, e.read_actor_info(ax))
            print(ax, "electrical", e.is_electrically_connected(ax))
            print(ax, "reference_status", e.read_reference_status(ax))
            print(ax, "reference_pos", e.read_reference_position(ax))
            print(ax, "step_voltage", e.read_step_voltage(ax))
            ##print ax, "dc_voltage", e.read_openloop_voltage(ax)
            #needs pro version
            print(ax, "frequency", e.read_frequency(ax))
            print(ax, "enable_axis", e.enable_axis(ax))
            print(ax, "position", e.read_position_axis(ax))
            #for i in range(10):
            #    e.single_step(ax, backward=False)
            #    print(ax, "position", e.read_position_axis(ax))
            #    time.sleep(0.05)
    
    #         print(ax, "enable_closedloop_axis", e.enable_closedloop_axis(ax, enable=True))
    #         print(ax, "moving", e.write_target_position_axis(ax, 3e6))
    #         for i in range(10):
    #             print(ax, "position", e.read_position_axis(ax))
    #             time.sleep(0.05)
            
        e.close()
        
    # Test loading via device id:
    print("\ntest loading device_id=199")
    e = AttoCubeECC100(device_id = 199, debug=True)
    print("dev id:", e.device_num, e.read_device_id())
    e.close()
    
    print("done")
