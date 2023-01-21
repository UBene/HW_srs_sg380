'''
Created on Jan 20, 2023

@author: Benedikt Ursprung
'''
import sys
import os
import inspect
# Import the .NET Common Language Runtime (CLR) to allow interaction with .NET
import clr
import numpy as np
import time

print("Python %s\n\n" % (sys.version,))

strCurrFile = os.path.abspath(inspect.stack()[0][1])
print("Executing File = %s\n" % strCurrFile)

# Initialize the DLL folder path to where the DLLs are located
strPathDllFolder = os.path.dirname(strCurrFile)
print("Executing Dir  = %s\n" % strPathDllFolder)

# Add the DLL folder path to the system search path (before adding references)
sys.path.append(strPathDllFolder)

# Add a reference to each .NET assembly required
clr.AddReference("UsbDllWrap")

# Import a class from a namespace
from Newport.USBComm import *
from System.Text import StringBuilder
from System.Collections import Hashtable
from System.Collections import IDictionaryEnumerator


class Dev:

    def __init__(self, device_num=0, debug=False):
        self.debug = debug
        self.device_keys = []
        # Call the class constructor to create an object
        self.usb = oUSB = USB(True)

        # Discover all connected devices
        bStatus = oUSB.OpenDevices(0, True)
        if (bStatus):
            oDeviceTable = oUSB.GetDeviceTable()
            nDeviceCount = oDeviceTable.Count
            # print("Device Count = %d" % nDeviceCount)

            # If no devices were discovered
            if (nDeviceCount == 0):
                print("No discovered devices.\n")
            else:
                if self.debug:
                    print(f'found {nDeviceCount} devices')
                oEnumerator = oDeviceTable.GetEnumerator()
                strDeviceKeyList = np.array([])

                # Iterate through the Device Table creating a list of Device
                # Keys
                for nIdx in range(0, nDeviceCount):
                    if (oEnumerator.MoveNext()):
                        strDeviceKeyList = np.append(
                            strDeviceKeyList, oEnumerator.Key)

                # print('strDeviceKeyList', strDeviceKeyList)
                # print("\n")

                strBldr = StringBuilder(64)
                # print('strBldr', repr(strBldr.ToString()), strBldr.Length)
                self.device_keys = [str(oDeviceKey)
                                    for oDeviceKey in strDeviceKeyList]

                self.set_device_num(device_num)
        else:
            print("\n***** Error:  Could not open the devices")

    def set_device_num(self, device_num=0):
        self.device_key = self.device_keys[device_num]

    def query(self, cmd):
        strBldr = StringBuilder(64)
        resp = self.usb.Query(self.device_key, cmd, strBldr)
        if self.debug:
            print(
                f'query ({self.device_key}): {cmd} success:{resp==0} --> {strBldr.ToString()}')
        return strBldr.ToString()

    # *IDN? Identification string query **
    def read_identification(self):
        return self.query("*IDN?")

    # *RCL Recall parameters
    # *RST Reset instrument **

    # AB Abort motion **
    def write_abort_motion(self):
        self.query(f"AB")
    # AC Set acceleration **
    # AC? Get acceleration **
    # DH Define home position
    # DH? Get home position **
    # MC Motor check

    # MD? Get motion done status **
    def read_is_in_motion(self, axis=1):
        # response values
        #       0 Motion is in progress
        #       1 Motion is not in progress
        return not bool(int(self.query(f"{axis}MD?")))
    # MV Move indefinitely
    # MV? Get motion direction **

    # PA Move to a target position
    def write_target_position(self, pos, axis=1):
        self.query(f"{axis}PA{int(pos)}")

    # PA? Get destination position **

    # PR Move relative
    def write_move_relative(self, delta, axis=1):
        self.query(f"{axis}PR{int(delta)}")

    # PR? Get destination position **
    def read_target_position(self, axis=1):
        return int(self.query(f"{axis}PR?"))
    # QM Set motor type **
    # QM? Get motor type **
    # RS Reset the controller **
    # SA Set controller address **
    # SA? Get controller address **
    # SC Scan RS-485 network **
    # SC? Get RS-485 network controller addresses **
    # SD? Get scan status **
    # SM Save to non-volatile memory **
    # ST Stop motion **
    # TB? Get error message **
    # TE? Get error number **
    # TP? Get position **

    def read_position(self, axis=1):
        return int(self.query(f"{axis}TP?"))

    # VA Set velocity **
    # VA? Get velocity **
    # VE? Firmware version string query **
    # XX Purge memory
    # ZZ Set configuration register **
    # ZZ? Get configuration register **

    def close(self):
        self.usb.CloseDevices()
        print("Devices Closed.\n")


if __name__ == '__main__':
    dev = Dev(debug=True)
    dev.read_identification()
    pos = dev.read_position(axis=1)
    dev.write_position(pos + 2, axis=1)
    pos = dev.read_position(axis=1)
    dev.read_motion_status(1)
    time.sleep(0.1)
    dev.read_motion_status(1)
    dev.close()
