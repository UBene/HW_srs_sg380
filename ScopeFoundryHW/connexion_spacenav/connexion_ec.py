'''
Connexion SpaceNavigator/SpaceMouse ScopeFoundry module
@author: Alan Buckley

Suggestions for improvement from Ed Barnard. <esbarnard@lbl.gov>


'''

import pywinusb.hid as hid
from time import sleep

class Connexion_EC(object):
    
    name = "connexion_ec"
    
    def __init__(self):
        """Creates storage objects and hid filters"""
        self.space_nav_filter = hid.HidDeviceFilter(vendor_id=0x46d, product_id=0xc626)
        self.space_mouse_filter = hid.HidDeviceFilter(vendor_id=0x256f, product_id=0xc62f)
        self.data = None
        self.hid_device = None
        self.scale = 350.0
    
    def int16_bind(self, v1,v2):
        """Calculates a 16 bit integer using two 8 bit integers.
        
        =============  ========  ===============================================================
        **Arguments**  **type**  **Description**
        *v1*           int8      first 8-bit integer in a axis-specific pair given in raw data. 
        *v2*           int8      second 8-bit integer in a axis-specific pair given in raw data.
        =============  ========  ===============================================================
        
        :returns: a 16-bit integer value described by two 8-bit integers.
        """
        value = (v1) | (v2<<8)
        if value >= 32768:
            value = - (65536 - value)
        return value
    
    def select_device(self, name):
        """Loads hid filter based on a string given by the UI drop-down menu.
        
        =============  ========  ======================================================
        **Arguments**  **type**  **Description**
        *name*         string    name given by "Connexion Device" drop-down menu in UI. 
        =============  ========  ======================================================
        
        :returns: None
        """
        if name == "SpaceMouse":
            try:
                self.hid_device = self.space_mouse_filter.get_devices()[0]
            except IOError:
                print("Device not connected.")
            self.name = name

        elif name == "SpaceNavigator":
            try:
                self.hid_device = self.space_nav_filter.get_devices()[0]
            except IOError:
                print("Device not connected.")
            self.name = name
            
        else:
            print("No Devices")
      
    def close(self):
        """Closes connection to active HID device."""
        self.hid_device.close()
        
    