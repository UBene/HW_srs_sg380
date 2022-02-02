from ctypes import c_int, c_uint, c_byte, c_ubyte, c_short, c_double, c_float, c_long
from ctypes import pointer, byref, windll, cdll, create_string_buffer


SHAMROCK_COMMUNICATION_ERROR = 20201
SHAMROCK_SUCCESS = 20202
SHAMROCK_P1INVALID = 20266
SHAMROCK_P2INVALID = 20267
SHAMROCK_P3INVALID = 20268
SHAMROCK_P4INVALID = 20269
SHAMROCK_P5INVALID = 20270
SHAMROCK_NOT_INITIALIZED = 20275
SHAMROCK_NOT_AVAILABLE = 20292

SHAMROCK_ACCESSORYMIN = 0
SHAMROCK_ACCESSORYMAX = 1
SHAMROCK_FILTERMIN = 1
SHAMROCK_FILTERMAX = 6
SHAMROCK_TURRETMIN = 1
SHAMROCK_TURRETMAX = 3
SHAMROCK_GRATINGMIN = 1
SHAMROCK_SLITWIDTHMIN = 10
SHAMROCK_SLITWIDTHMAX = 2500
SHAMROCK_I24SLITWIDTHMAX = 24000
SHAMROCK_SHUTTERMODEMIN = 0
SHAMROCK_SHUTTERMODEMAX = 1
SHAMROCK_DET_OFFSET_MIN = -240000
SHAMROCK_DET_OFFSET_MAX = 240000
SHAMROCK_GRAT_OFFSET_MIN = -20000
SHAMROCK_GRAT_OFFSET_MAX = 20000

SHAMROCK_SLIT_INDEX_MIN  = 1
SHAMROCK_SLIT_INDEX_MAX  = 4

SHAMROCK_INPUT_SLIT_SIDE  = 1
SHAMROCK_INPUT_SLIT_DIRECT  = 2
SHAMROCK_OUTPUT_SLIT_SIDE  = 3
SHAMROCK_OUTPUT_SLIT_DIRECT = 4

SHAMROCK_FLIPPER_INDEX_MIN  = 1
SHAMROCK_FLIPPER_INDEX_MAX  = 2
SHAMROCK_PORTMIN = 0
SHAMROCK_PORTMAX = 1

SHAMROCK_INPUT_FLIPPER   = 1
SHAMROCK_OUTPUT_FLIPPER = 2
SHAMROCK_DIRECT_PORT = 0
SHAMROCK_SIDE_PORT = 1

SHAMROCK_ERRORLENGTH = 64

consts_by_num = dict()
for name,num in list(locals().items()):
    if name.startswith("SHAMROCK_"):
        consts_by_num[num] = name
        
        
def _err(retval):
    if retval == SHAMROCK_SUCCESS:
        return retval
    else:
        err_name = consts_by_num.get(retval)
        raise IOError( "Andor SHAMROCK Failure {}: {}".format(retval, err_name))


class AndorShamrockSpec(object):
    
    def __init__(self, dev_id=0):
        self.dev_id = dev_id
        
        self.lib0 = windll.LoadLibrary( r"C:\Program Files\Andor SDK\Shamrock64\atshamrock.dll")
        lib = self.lib = windll.LoadLibrary(r"C:\Program Files\Andor SDK\Shamrock64\ShamrockCIF.dll")
        
        _err(lib.ShamrockInitialize(""))
        
        n_dev = c_int()
        _err(lib.ShamrockGetNumberDevices(byref(n_dev)))
        n = n_dev.value

        print("Found {} Andor Shamrock Spectrometers".format(n))
        
        assert dev_id < n

        
        # Serial Number
        x = create_string_buffer(64)
        _err(lib.ShamrockGetSerialNumber(dev_id,x))
        self.serial_number = x.value.decode()
        
        # EEPROM parameters
        f = c_float()
        ang = c_float()
        tilt = c_float()
        
        _err(lib.ShamrockEepromGetOpticalParams(dev_id, byref(f), byref(ang), byref(tilt)))

        self.focal_length = f.value
        self.angular_deviation = ang.value
        self.focal_tilt = tilt.value
        
        # gratings
        x = c_int()
        _err(lib.ShamrockGetNumberGratings(dev_id, byref(x)))
        self.num_gratings = x.value
        
        self.gratings = dict()
        for i in range(1, self.num_gratings+1):
            lines, blaze, home, offset = self.get_grating_info(i)
            self.gratings[i] = "{:1.0f}g/mm {}".format(lines, blaze)
        
        # Slits
        self.slit_ids = dict(
            input_side = 1,
            input_direct = 2,
            ouput_side = 3,
            output_direct = 4)

        self.slit_present = dict()
        
        for name, num in self.slit_ids.items():
            x = c_int()
            _err(lib.ShamrockAutoSlitIsPresent(dev_id, num, byref(x)))
            self.slit_present[name] = bool(x.value)
            
        # Focus mirror
        x = c_int()
        ## Gets maximum possible focus position in steps
        _err(lib.ShamrockGetFocusMirrorMaxSteps(dev_id, byref(x)))
        self.focus_mirror_max_steps = x.value
        
        # Flipper mirrors
        self.flipper_mirror_ids = dict(
            input = 1,
            output = 2,
            )
        self.flipper_mirror_present = dict()
        for name, num in self.flipper_mirror_ids.items():
            x = c_int()
            _err(lib.ShamrockFlipperMirrorIsPresent(dev_id, num, byref(x)))
            self.flipper_mirror_present[name] = bool(x.value)

        
         
        
    
    def close(self):
        self.lib.ShamrockClose()
        
    def get_turret(self):
        x = c_int()
        _err(self.lib.ShamrockGetTurret(self.dev_id, byref(x)))
        self.turret_num = x.value
        return self.turret_num
    
    ### Grating
    
    def get_grating(self):
        x = c_int()
        _err(self.lib.ShamrockGetGrating(self.dev_id, byref(x)))
        self.grating_num = x.value
        return self.grating_num
    
    def set_grating(self, grating_id):
        _err(self.lib.ShamrockSetGrating(self.dev_id, int(grating_id)))
    
    def get_grating_info(self, grating_num):
        lines = c_float()
        blaze = create_string_buffer(64)
        home = c_int()
        offset = c_int()
        _err(self.lib.ShamrockGetGratingInfo(self.dev_id, grating_num, 
                                             byref(lines), blaze, byref(home), byref(offset)))
        
        return(lines.value, blaze.value.decode(), home.value, offset.value)

    

    ### Wavelength
        
    def get_wavelength(self):
        x = c_float()
        _err(self.lib.ShamrockGetWavelength(self.dev_id, byref(x)))
        self.wavelength = x.value
        return self.wavelength
    
    def set_wavelength(self, wl):
        _err(self.lib.ShamrockSetWavelength(self.dev_id, c_float(wl)))
        
    ### Slits
    
    def get_slit_width(self, slit):
        s_id = self.slit_ids[slit]
        x = c_float()
        _err(self.lib.ShamrockGetAutoSlitWidth(self.dev_id, s_id, byref(x)))
        return x.value
    
    def set_slit_width(self, slit, width):
        s_id = self.slit_ids[slit]
        _err(self.lib.ShamrockSetAutoSlitWidth(self.dev_id, s_id, c_float(width)))

    
    ### Focus Mirror
    
    def get_focus_mirror_position(self):
        x = c_int()
        _err(self.lib.ShamrockGetFocusMirror(self.dev_id, byref(x)))
        self.focus_mirror_position = x.value
        return self.focus_mirror_position
    
    def set_focus_mirror_position_rel(self, delta):
        """
        Relative Focus Mirror motion
        Sets the required Focus movement. Focus movement is possible
        from 0 to max steps, so possible values will be from
        (0 - current steps) to (max - current steps).
        +steps move focus mirror forward
        -steps move focus mirror backwards
        """
        _err(self.lib.ShamrockSetFocusMirror(self.dev_id, int(delta)))
        
    def set_focus_mirror_position_abs(self, pos):
        assert 0 <= pos <= self.focus_mirror_max_steps # might be < instead of <=
        current_pos = self.get_focus_mirror_position()
        delta = int(pos) - current_pos
        self.set_focus_mirror_position_rel(delta)
        
    ### Flipper Mirror
    
    def get_flipper_mirror(self, flipper):
        m_id = self.flipper_mirror_ids[flipper]
        
        x = c_int()
        _err(self.lib.ShamrockGetFlipperMirror(self.dev_id, m_id, byref(x)))
        #print('mirror', m_id, x.value)

        flipper_positions = {0: 'direct', 1:'side'}
        return flipper_positions[x.value]
        
        #_err(self.lib.ShamrockGetFlipperMirrorPosition(self.dev_id, m_id, byref(x)))
        #print('pos', m_id, x.value)
        #_err(self.lib.ShamrockGetFlipperMirrorMaxPosition(self.dev_id, m_id, byref(x)))
        #print('max', x.value)
        
        
    def set_flipper_mirror(self, flipper, port):
        assert self.flipper_mirror_present[flipper]
        m_id = self.flipper_mirror_ids[flipper]
        flipper_position_ids = {'direct':0, 'side':1}
        pos_id = flipper_position_ids[port]
        _err(self.lib.ShamrockSetFlipperMirror(self.dev_id, m_id, pos_id))

        
        
# test code
if __name__ == '__main__':
    
    s = AndorShamrockSpec()
    try:
        print("serial_number", s.serial_number)
        print("focal_length", s.focal_length)
        print("angular_deviation", s.angular_deviation)
        print("focal_tilt", s.focal_tilt)

        print("turret", s.get_turret())
        print("grating", s.get_grating())
        for i in range(4):
            print("grating_info", i+1, s.get_grating_info(i+1))
        print(s.gratings)
        print("wl", s.get_wavelength())
        
        print("focus_mirror", s.get_focus_mirror_position())
        #s.set_focus_mirror_position_abs(261)
        #print("focus_mirror", s.get_focus_mirror_position())

        print("Slits", s.slit_present)
        
        print("Flipper Mirror", s.flipper_mirror_present)
        print("-->input", s.get_flipper_mirror('input'))
        print("-->output", s.get_flipper_mirror('output'))
        
#         print("-->input", s.get_flipper_mirror('input'))
#         print("move to direct")
#         s.set_flipper_mirror('input', 'direct')
#         print("-->input", s.get_flipper_mirror('input'))
#         print("move to side")
#         s.set_flipper_mirror('input', 'side')
#         print("-->input", s.get_flipper_mirror('input'))
        
        
    finally:
        s.close()