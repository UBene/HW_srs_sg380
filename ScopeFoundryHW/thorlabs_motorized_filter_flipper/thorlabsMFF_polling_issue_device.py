'''
Created on Nov 3, 2017

@author: Benedikt Ursprung

major update Jan 23, 2023
author suspects that his specific device has a polling issue as 
it does not work with kinesis as well. Try thorlabsMFF_device.py file first!
this version reconnects to for every operation which is slow!
'''
import ctypes
import time

TYPEID = 37


def catch_error(error_code):
    if error_code == 0:
        return
    else:
        raise IOError(
            f"ThorlabsMFFDev: Thorlabs Kinesis Error: {error_code}")


class ThorlabsMFFDev:

    def __init__(self, serial_num, debug=False):
        self.debug = debug

        self.serial_numbers = self.read_serial_numbers()

        h = self.set_handle(serial_num)
        if self.debug:
            print('using', h, 'flipper')

        # self.open() # ISSUE

    def set_handle(self, serial_num: str):
        if not self.serial_numbers:
            print('No thorlabs motorized flipper detected')
            return

        b_sn = str(serial_num).encode('ascii')

        if b_sn in self.serial_numbers:
            self._handle = b_sn
            return self.serial_num_in_use
        if self.serial_numbers:
            self._handle = self.serial_numbers[0]
            print(
                'WARNING selected first ThorlabsMFFDev device, not specified with serial number')
            print('available serial numbers', self.serial_numbers)
            return self.serial_num_in_use

    def read_serial_numbers(self):
        dll = ctypes.cdll.LoadLibrary(
            "C:\Program Files\Thorlabs\Kinesis\Thorlabs.MotionControl.DeviceManager.dll")
        dll.TLI_BuildDeviceList()
        serialNos = ctypes.create_string_buffer(100)
        dll.TLI_GetDeviceListByTypeExt(serialNos, 100, TYPEID)
        return [x for x in serialNos.value.split(b',') if x]

    @property
    def serial_num_in_use(self):
        return self._handle.decode()

    def write_position(self, position):
        assert position in (1, 2)
        self.open()  # ISSUE!
        time.sleep(0.1)
        if self.debug:
            print('ThorlabsMFFDev move pos', position)
        catch_error(self.ff_dll.FF_MoveToPosition(
            self._handle, position))
        self.close()  # ISSUE!

    def read_position(self):
        self.open()  # ISSUE!
        time.sleep(0.1)
        value = self.ff_dll.FF_GetPosition(self._handle)
        if self.debug:
            print('ThorlabsMFFDev read_position', value, type(value))
        self.close()  # ISSUE!
        return value

    def close(self):
        # self.ff_dll.FF_StopPolling(self._handle)
        self.ff_dll.FF_Close(self._handle)

    def open(self):
        self.ff_dll = ctypes.windll.LoadLibrary(
            "C:\Program Files\Thorlabs\Kinesis\Thorlabs.MotionControl.FilterFlipper.dll")
        if self.debug:
            print('selected serial number', self._handle)
        catch_error(self.ff_dll.FF_Open(self._handle))
        # catch_error(self.ff_dll.FF_StartPolling(self._handle, 10)) # ISSUE
        time.sleep(1)

    def get_other_position(self):
        cur_pos = self.read_position()
        return (cur_pos % 2) + 1

    def toggle(self):
        self.write_position(self.get_other_position())


if __name__ == '__main__':
    dev = ThorlabsMFFDev("37006062", debug=True)
    # dev.read_position()
    dev.toggle()
    time.sleep(0.6)
    dev.read_position()
