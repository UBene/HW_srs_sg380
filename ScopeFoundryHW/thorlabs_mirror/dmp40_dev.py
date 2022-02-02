'''
Created on Aug 22, 2017

@author: Alan Buckley
'''

import ctypes
from ctypes import windll
import numpy as np
import logging
from operator import itemgetter


class ThorlabsDMP40(object):
    """Thorlabs DMP40 Deformable Mirror for optical tables"""

    
    errors = {
            -1073807202: "VISA or a code library required by VISA could not be located or loaded. This is usually due to a required driver not being installed on the system.",
            -1073807360: "Unknown system error (miscellaneous error).",
            -1073807346: "The given session or object reference is invalid.",
            -1073807345: "Specified type of lock cannot be obtained, or specified operation cannot be performed, because the resource is locked.",
            -1073807344: "Invalid expression specified for search.",
            -1073807343: "Insufficient location information or the device or resource is not present in the system.",
            -1073807342: "Invalid resource reference specified. Parsing error.",
            -1073807341: "Invalid access mode.", 
            -1073807339: "Timeout expired before operation completed.",
            -1073807338: "The VISA driver failed to properly close the session or object reference. This might be due to an error freeing internal or OS resources, a failed network connection, or a lower level driver or OS error.",
            -1073807333: "Specified degree is invalid.",
            -1073807332: "Specified job identifier is invalid.",
            -1073807331: "The specified attribute is not defined or supported by the referenced resource.",
            -1073807330: "The specified state of the attribute is not valid, or is not supported as defined by the resource.",
            -1073807329: "The specified attribute is read-only.",
            -1073807328: "The specified type of lock is not supported by this resource.",
            -1073807327: "The access key to the specified resource is invalid.",
            -1073807322: "Specified event type is not supported by the resource.",
            -1073807321: "Invalid mechanism specified.",
            -1073807320: "A handler was not installed.",
            -1073807319: "The given handler reference is invalid.", 
            -1073807318: "Specified event context is invalid.",
            -1073807315: "The event queue for the specified type has overflowed. This is usually due to previous events not having been closed.",
            -1073807313: "You must be enabled for events of the specified type in order to receive them.",
            -1073807312: "User abort occurred during transfer.",
            -1073807308: "Violation of raw write protocol occurred during transfer.",
            -1073807307: "Violation of raw read protocol occurred during transfer.",
            -1073807306: "Device reported an output protocol error during transfer.",
            -1073807305: "Device reported an input protocol error during transfer.",
            -1073807304: "Bus error occurred during transfer.",
            -1073807303: "Unable to queue the asynchronous operation because there is already an operation in progress.",
            -1073807302: "Unable to start operation because setup is invalid (due to attributes being set to an inconsistent state).",
            -1073807301: "Unable to queue the asynchronous operation (usually due to the I/O completion event not being enabled or insufficient space in the session's queue).",
            -1073807300: "Insufficient system resources to perform necessary memory allocation.",
            -1073807299: "Invalid buffer mask specified.",
            -1073807298: "Could not perform operation because of I/O error.",
            -1073807297: "A format specifier in the format string is invalid.", 
            -1073807295: "A format specifier in the format string is not supported.", 
            -1073807294: "The specified trigger line is currently in use.",
            -1073807290: "The specified mode is not supported by this VISA implementation.",
            -1073807286: "Service request has not been received for the session.",
            -1073807282: "Invalid address space specified.",
            -1073807279: "Invalid offset specified.",
            -1073807278: "Invalid access width specified.",
            -1073807276: "Specified offset is not accessible from this hardware.",
            -1073807275: "Cannot support source and destination widths that are different.",
            -1073807273: "The specified session is not currently mapped.",
            -1073807271: "A previous response is still pending, causing a multiple query error.",
            -1073807265: "No listeners condition is detected (both NRFD and NDAC are deasserted).",
            -1073807264: "The interface associated with this session is not currently the controller in charge.",
            -1073807263: "The interface associated with this session is not the system controller.",
            -1073807257: "The given session or object reference does not support this operation.",
            -1073807256: "An interrupt is still pending from a previous call.",
            -1073807254: "A parity error occurred during transfer.",
            -1073807253: "A framing error occurred during transfer.",
            -1073807252: "An overrun error occurred during transfer. A character was not read from the hardware before the next character arrived.",
            -1073807250: "The path from trigSrc to trigDest is not currently mapped.",
            -1073807248: "The specified offset is not properly aligned for the access width of the operation.",
            -1073807247: "A specified user buffer is not valid or cannot be accessed for the required size.",
            -1073807246: "The resource is valid, but VISA cannot currently access it.",
            -1073807242: "Specified width is not supported by this hardware.",
            -1073807240: "The value of some parameter (which parameter is not known) is invalid.",
            -1073807239: "The protocol specified is invalid.",
            -1073807237: "Invalid size of window specified.",
            -1073807232: "The specified session currently contains a mapped window.",
            -1073807231: "The given operation is not implemented.",
            -1073807229: "Invalid length specified.", 
            -1073807215: "Invalid mode specified.",
            -1073807204: "The current session did not have a lock on the resource.",
            -1073807202: "VISA or a code library required by VISA could not be located or loaded. This is usually due to a required driver not being installed on the system.",
            -1073807201: "The interface cannot generate an interrupt on the requested level or with the requested statusID value.",
            -1073807200: "The value specified by the line parameter is invalid.", 
            -1073807199: "An error occurred while trying to open the specified file. Possible reasons include an invalid path or lack of access rights.",
            -1073807198: "An error occurred while performing I/O on the specified file.",
            -1073807197: "One of the specified lines, trigSrc or trigDest, is not supported by this VISA implementation, or the combination of lines is not a valid mapping.",
            -1073807196: "The specified mechanism is not supported for the given event type.",
            -1073807195: "The interface type is valid, but the specified interface number is not configured.",
            -1073807194: "The connection for the given session has been lost.",
            -1073807193: "The remote machine does not exist or is not accepting any connections. If the NI-VISA server is installed and running on the remote machine, it might have an incompatible version or might be listening on a different port.",
            -1073807192: "Access to the resource or remote machine is denied. This is due to lack of sufficient privileges for the current user or machine.",
            0: "Operation completed successfully.",
            1073676290: "Specified event is already enabled for at least one of the specified mechanisms.",
            1073676291: "Specified event is already disabled for at least one of the specified mechanisms.",
            1073676292: "Operation completed successfully, but queue was already empty.",
            1073676293: "The specified termination character was read.",
            1073676294: "The number of bytes transferred is equal to the requested input count. More data might be available.",
            1073676300: "VISA received more event information of the specified type than the configured queue size could hold.", 
            1073676407: "The specified configuration either does not exist or could not be loaded. VISA-specified defaults will be used.",
            1073676413: "Session opened successfully, but the device at the specified address is not responding.", 
            1073676414: "The path from trigSrc to trigDest is already mapped.",
            1073676416: "Wait terminated successfully on receipt of an event notification. There is at least one more event occurrence of the type specified by inEventType available for this session.",
            1073676418: "The specified object reference is uninitialized.", 
            1073676420: "Although the specified state of the attribute is valid, it is not supported by this resource implementation.",
            1073676421: "The status code passed to the operation could not be interpreted.",
            1073676424: "The specified I/O buffer is not supported.",
            1073676440: "Event handled successfully. Do not invoke any other handlers on this session for this event.",
            1073676441: "Operation completed successfully, and this session has nested shared locks.",
            1073676442: "Operation completed successfully, and this session has nested exclusive locks.",
            1073676443: "Operation completed successfully, but the operation was actually synchronous rather than asynchronous.",
            1073676457: "The operation succeeded, but a lower level driver did not implement the extended functionality."}
    
    def __init__(self, debug=False):
        self.debug = debug
        self.sessionHandle = ctypes.c_uint32(0)
        thorlib_path = r'C:\Program Files\IVI Foundation\VISA\Win64\Bin\TLDFM_64.dll' 
        thorlib_ext_path = r'C:\Program Files\IVI Foundation\VISA\Win64\Bin\TLDFMX_64.dll'
        self.dll = windll.LoadLibrary(thorlib_path)
        self.dll_ext = windll.LoadLibrary(thorlib_ext_path)
        self.get_device_info()
        self.instHandle = ctypes.c_uint32(0)
        ID_query = ctypes.c_bool(False)
        resetDevice = ctypes.c_bool(False)
        status = self.dll_ext.TLDFMX_init(self.resourceName, ID_query, resetDevice, ctypes.byref(self.instHandle))
        if self.debug:
            print("Connect:", self.errors[status])
        self.segment_count = self.get_segment_count()
        self.tilt_count = self.get_tilt_count()
    
    def get_count(self):
        VI_NULL = ctypes.c_uint32(0)
        deviceCount = ctypes.c_uint32(0)
        status = self.dll.TLDFM_get_device_count(VI_NULL, ctypes.byref(deviceCount))
        if self.debug:
            print("get_count", self.errors[status])
        return deviceCount
    
    def get_device_info(self):
        VI_NULL = ctypes.c_uint32(0)
        deviceIndex = self.get_count().value - 1
        manufacturer = ctypes.create_string_buffer(256)
        inst_name = ctypes.create_string_buffer(28)
        serial = ctypes.create_string_buffer(28)
        deviceAvailable = ctypes.c_bool()
        resourceName = ctypes.create_string_buffer(256)
        status = self.dll.TLDFM_get_device_information(VI_NULL, deviceIndex, 
                                                         manufacturer, inst_name, serial, 
                                                         ctypes.byref(deviceAvailable), resourceName)
        if deviceAvailable.value:
            self.resourceName = resourceName.value
        if self.debug:
            print("get_device_info:", self.errors[status], deviceAvailable)
    
    def get_device_configuration(self):
        segCount = ctypes.c_uint32(0)
        minSegV = ctypes.c_uint64(0)
        maxSegV = ctypes.c_uint64(0)
        segCommonVMax = ctypes.c_uint64(0)
        tiltElementCount = ctypes.c_uint32(0)
        minTiltV = ctypes.c_uint64(0)
        maxTiltV = ctypes.c_uint64(0)
        tiltCommonVMax = ctypes.c_uint64(0)
        status = self.dll.TLDFM_get_device_configuration(self.instHandle, 
                                                         ctypes.byref(segCount), 
                                                         ctypes.byref(minSegV), 
                                                         ctypes.byref(maxSegV), 
                                                         ctypes.byref(segCommonVMax), 
                                                         ctypes.byref(tiltElementCount),
                                                         ctypes.byref(minTiltV),
                                                         ctypes.byref(maxTiltV), 
                                                         ctypes.byref(tiltCommonVMax))
        if self.debug:
            print("get_device_config:", self.errors[status])
        seg = (minSegV.value, maxSegV.value)
        tilt = (minTiltV.value, maxTiltV.value)
        return seg, tilt
    
    def get_segment_count(self):
        count = ctypes.c_uint32(0)
        status = self.dll.TLDFM_get_segment_count(self.instHandle, ctypes.byref(count))
        if self.debug:
            print("get_segment_count:", self.errors[status])
        return count
    
    def get_tilt_count(self):
        count = ctypes.c_uint32(0)
        status = self.dll.TLDFM_get_segment_count(self.instHandle, ctypes.byref(count))
        if self.debug:
            print("get_tilt_count:", self.errors[status])
        return count
    
    def get_segment_voltages(self):
        segmentVoltages = (ctypes.c_double * 40)()
        status = self.dll.TLDFM_get_segment_voltages(self.instHandle, segmentVoltages)
        if self.debug:
            print("get_segment_voltages:", self.errors[status])
        return np.frombuffer(segmentVoltages)
    
    def get_tilt_voltages(self):
        tiltVoltages = (ctypes.c_double * 40)()
        status = self.dll.TLDFM_get_tilt_voltages(self.instHandle, tiltVoltages)
        if self.debug:
            print("get_tilt_voltages:", self.errors[status])
        return np.frombuffer(tiltVoltages)
    
    def set_segment_voltages(self, np_arr):
        c_array = self.np64_to_ctypes64(np_arr)
        status = self.dll.TLDFM_set_segment_voltages(self.instHandle, c_array)
        if self.debug:
            print("set_segment_voltages:", self.errors[status])
    
    def set_tilt_voltages(self, np_arr):
        c_array = self.np64_to_ctypes64(np_arr)
        status = self.dll.TLDFM_set_tilt_voltages(self.instHandle, c_array)
        if self.debug:
            print("set_tilt_voltages:", self.errors[status])
    

    def get_temperatures(self):
        IC1Temperatur = ctypes.c_double(0)
        IC2Temperatur = ctypes.c_double(0)
        mirrorTemperatur = ctypes.c_double(0)
        electronicTemperatur = ctypes.c_double(0)
        status = self.dll.TLDFM_get_temperatures(self.instHandle, ctypes.byref(IC1Temperatur),
                                            ctypes.byref(IC2Temperatur), ctypes.byref(mirrorTemperatur),
                                            ctypes.byref(electronicTemperatur))
        data = (IC1Temperatur.value, IC2Temperatur.value,
                mirrorTemperatur.value, electronicTemperatur.value)
        if self.debug:
            print("get_temperatures", self.errors[status])
        return list(data)
    
    def self_test(self):
        """This function causes the instrument to perform a self-test and returns the result of that self-test."""
        result = ctypes.c_uint16(0)
        message = ctypes.create_string_buffer(256)
        status = self.dll.TLDFM_self_test(self.instHandle, ctypes.byref(result), ctypes.byref(message))
        if self.debug:
            print("self_test:", self.errors[status])
        return result, message
    
    def relax(self):
        devicePart = ctypes.c_uint32(2) # MIRROR 0, TILT 1, BOTH 2
        isFirstStep = ctypes.c_bool(True)
        reload = ctypes.c_bool(False)
        relaxPatternMirror = (ctypes.c_double * 40)()
        relaxPatternArms = (ctypes.c_double * 40)()
        remainingSteps = ctypes.c_uint32(0)
        status = self.dll_ext.TLDFMX_relax(self.instHandle, devicePart, isFirstStep, reload,
                                           relaxPatternMirror, relaxPatternArms, ctypes.byref(remainingSteps))
        if self.debug:
            print("relax:", self.errors[status])
        if status == 0:
            self.dll.TLDFM_set_segment_voltages(self.instHandle, relaxPatternMirror)
            self.dll.TLDFM_set_tilt_voltages(self.instHandle, relaxPatternArms)
        else:
            print("relax:", self.errors[status])
            
        isFirstStep = ctypes.c_bool(False)
        while remainingSteps.value > 0:

            status = self.dll_ext.TLDFMX_relax(self.instHandle, devicePart, isFirstStep, reload,
                                            relaxPatternMirror, relaxPatternArms, ctypes.byref(remainingSteps))
            if status == 0:
                self.dll.TLDFM_set_segment_voltages(self.instHandle, relaxPatternMirror)
                self.dll.TLDFM_set_tilt_voltages(self.instHandle, relaxPatternArms)
            else:
                print("relax:", self.errors[status])
            
    
    def reset(self):
        """Places the instrument in a default state. 
        All segment and tilt arm voltages are reset to 0V."""
        status = self.dll.TLDFM_reset(self.instHandle)
        if self.debug:
            print("reset:", self.errors[status])
        
    def np64_to_ctypes64(self, np_arr):
        data = np_arr.astype(np.float64)
        array_ptr = ctypes.POINTER(ctypes.c_double)
        c_array = data.ctypes.data_as(array_ptr)
        return c_array
    
    def close(self):
        self.reset()
        status = self.dll_ext.TLDFMX_close(self.instHandle)
        if self.debug:
            print("close:", self.errors[status])