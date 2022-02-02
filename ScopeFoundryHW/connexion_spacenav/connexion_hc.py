'''
Connexion SpaceNavigator/SpaceMouse ScopeFoundry module
@author: Alan Buckley

Suggestions for improvement from Ed Barnard. <esbarnard@lbl.gov>

'''
from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.connexion_spacenav.connexion_ec import Connexion_EC


class Connexion_HC(HardwareComponent):

    name = "connexion_hc"

    def setup(self):
        """Defines logged quantities upon startup."""
        self.x = self.settings.New(name='x', initial=0,
                                            dtype=float, fmt="%.2f", 
                                            ro=True, vmin=-1.0, vmax=1.0)
        self.y = self.settings.New(name='y', initial=0,
                                            dtype=float, fmt="%.2f", 
                                            ro=True, vmin=-1.0, vmax=1.0)
        self.z = self.settings.New(name='z', initial=0,
                                            dtype=float, fmt="%.2f", 
                                            ro=True, vmin=-1.0, vmax=1.0)
        self.roll = self.settings.New(name='roll', initial=0,
                                            dtype=float, fmt="%.2f", 
                                            ro=True, vmin=-1.0, vmax=1.0)
        self.pitch = self.settings.New(name='pitch', initial=0,
                                            dtype=float, fmt="%.2f", 
                                            ro=True, vmin=-1.0, vmax=1.0)
        self.yaw = self.settings.New(name='yaw', initial=0,
                                            dtype=float, fmt="%.2f", 
                                            ro=True, vmin=-1.0, vmax=1.0)
        self.button = self.settings.New(name='button', initial=0, dtype=int, fmt="%i",
                                            ro=True, vmin=0, vmax=3)
        self.left = self.settings.New(name='left', initial=0, dtype=bool,
                                            ro=True)
        self.right = self.settings.New(name='right', initial=0, dtype=bool,
                                            ro=True)
        self.left_right = self.settings.New(name='left_right', initial=0, dtype=bool,
                                            ro=True)
        self.none_setting = self.settings.New(name='none', initial=0, dtype=bool,
                                            ro=True)
        self.devices = self.settings.New(name='devices', initial="SpaceNavigator", dtype=str, choices = [("SpaceNavigator", "SpaceNavigator"),("SpaceMouse", "SpaceMouse")])

        self.axis_profile = None
        self.button_profile = None
        self.button_map = None
        
    def connect(self):
        """Connects to equipment level module, 
        loads the appropriate key map into memory,
        opens the selected device, sets data handler."""
        self.dev = Connexion_EC()
        if self.devices.val == "SpaceNavigator":
            self.load_spacenav_profile()
        elif self.devices.val == "SpaceMouse":
            self.load_spacemouse_profile()
        self.dev.select_device(name=self.settings.devices.val)
        self.dev.hid_device.open()
        self.dev.hid_device.set_raw_data_handler(self.data_update)
    
    def load_spacenav_profile(self):
        '''Loads SpaceNavigator key map.
        
        Description of `self.axis_profile` coordinates:
        
        Coordinates take the form (c1 , c2, c3, c4) and are paired with the name of a Connexion `logged_quantity`.
        
        ==============  ===============  ======================================================================================
        **Coordinate**  **Value Range**  **Description**
        **c1**          (1,2)            Channel header (raw data is presented in separate lists with differing headers.)
        **c2**          (1,11),(n)       The list position of byte 1 from two 8-bit integer pair offered in raw data.
        **c3**          (2,12),(n+1)     The list position of byte 2 from two 8-bit integer pair offered in raw data.
        **c4**          (-1) or (1)      Inversion multiplier, change this value to change the sign of your int16 output value.
        ==============  ===============  ======================================================================================
       
        **Note:** c2, and c3 are paired coordinates, c2 takes a n value, and c3 takes a n+1 value as they are sequential and order dependent.
        For example, if your raw data output prints following raw data list:
        [2, 0, 0, 246, 255, 0, 0]
        You can refer to byte pair (246, 255) using c2=3 and c3=4.
        
        Description of `self.button_profile` coordinates:
        
        Coordinates take the form (c1 , c2) and are paired with the name of a Connexion `logged_quantity`.
        
        ==============  ===============  ================================================================================================================
        **Coordinate**  **Value Range**  **Description**
        **c1**          (3)              Channel header (raw data is presented in separate lists with differing headers.)
        **c2**          (1)              The list position of byte offered in raw data. For buttons, it is always the second position (after the header).
        ==============  ===============  ================================================================================================================
        
        :returns: None
        '''
        self.axis_profile = {
            "x": (1,1,2,1),
            "y": (1,3,4,-1),
            "z": (1,5,6,-1),
            "roll": (2,3,4,-1),
            "pitch": (2,1,2,1),
            "yaw": (2,5,6,-1)}
        self.button_profile = {"left":(3,1),
            "right":(3,1),
            "left_right":(3,1)}
        self.button_map = { 0: "none",
            1: "left",
            2: "right",
            3: "left_right"}
    
    def load_spacemouse_profile(self):
        '''Loads SpaceMouse key map. 
        
        Description of `self.axis_profile` coordinates:
        
        Coordinates take the form (c1 , c2, c3, c4) and are paired with the name of a Connexion `logged_quantity`.
        
        ==============  ===============  ======================================================================================
        **Coordinate**  **Value Range**  **Description**
        **c1**          (1,2)            Channel header (raw data is presented in separate lists with differing headers.)
        **c2**          (1,11),(n)       The list position of byte 1 in the two 8-bit integer pair offered in raw data.
        **c3**          (2,12),(n+1)     The list position of byte 2 in the two 8-bit integer pair offered in raw data.
        **c4**          (-1) or (1)      inversion multiplier, change this value to change the sign of your int16 output value.
        ==============  ===============  ======================================================================================
        
        **Note:** c2, and c3 are paired coordinates, c2 takes a n value, and c3 takes a n+1 value as they are sequential and order dependent.
        For example, if your raw data output prints following raw data list:
        [2, 0, 0, 246, 255, 0, 0]
        You can refer to byte pair (246, 255) using c2=3 and c3=4.
        
        Description of `self.button_profile` coordinates:
        
        Coordinates take the form (c1 , c2) and are paired with the name of a Connexion `logged_quantity`.
        
        ==============  ===============  ================================================================================================================
        **Coordinate**  **Value Range**  **Description**
        **c1**          (3)              Channel header (raw data is presented in separate lists with differing headers.)
        **c2**          (1)              The list position of byte offered in raw data. For buttons, it is always the second position (after the header).
        ==============  ===============  ================================================================================================================
        
        :returns: None
        '''
        self.axis_profile = {
            "x": (1,1,2,1),
            "y": (1,3,4,-1),
            "z": (1,5,6,-1),
            "roll": (1,9,10,-1),
            "pitch": (1,7,8,1),
            "yaw": (1,11,12,-1)}
        self.button_profile = {"left":(3,1),
            "right":(3,1),
            "left_right":(3,1)}
        self.button_map = { 0: "none",
            1: "left",
            2: "right",
            3: "left_right"}
    
    def data_update(self, data):
        '''Data handler. Parses data, writes data to appropriate **LoggedQuantities**'''
        for k in self.button_profile.keys():
            self.parse_button(k, data)
        for k in self.axis_profile.keys():
            self.parse_axis(k, data)      
    
    def parse_axis(self, name, data):
        """Parses data by string name of axis, sets its value in its respective **LoggedQuantity**."""
        header, byte1, byte2, sign = self.axis_profile[name]
        if data[0] == header:
            value = sign * (self.dev.int16_bind(data[byte1], data[byte2]))/self.dev.scale
            self.settings[name] = value
     
    def parse_button(self, name, data):
        """Parses data by string name of button, sets its value in its respective **LoggedQuantity**."""
        header, byte = self.button_profile[name]
        if data[0] == header:
            self.settings['button'] = slot = data[byte]
            print("slot:", slot)
            active = self.button_map[slot]
            for v in self.button_map.values():
                self.settings[v] = False
                self.settings[active] = True
            
    def disconnect(self):
        """Hardware disconnect and cleanup function."""
        self.dev.close()
        self.profile = None
        self.axis_profile = None
        self.button_profile = None
        self.button_map = None
        del self.dev

