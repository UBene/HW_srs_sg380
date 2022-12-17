from ScopeFoundry import HardwareComponent
import numpy as np

class ToupCamHW(HardwareComponent):
    
    name = 'toupcam'
    
    def setup(self):
        S = self.settings
        S.New('width_pixel', dtype=int, initial= 2048)
        S.New('height_pixel', dtype=int, initial= 1536) 
        S.New('centerx_pixel', initial= 1024) # this needs to be set in full resolution mode and is microscope specific
        S.New('centery_pixel', initial= 768)  # this needs to be set in full resolution mode and is microscope specific
        S.New('magnification', dtype=int, initial=40, vmin=0, vmax=150)
        S.New('calibration', dtype=float, initial=((5.+0.21) /162.)*100.) #micron/pixel*magnification
        S.New('cam_index', dtype=int, initial=0)
        S.New('res_mode', dtype=int, initial=1) #number of pixels scales with 1/res_mode
        
        S.New('auto_exposure', dtype=bool, initial=False)
        S.New('exposure', dtype=float, unit='s', initial=0.1, spinbox_decimals=6, vmin=0.000244, vmax=2)
        S.New('gain', dtype=int, initial=100, vmin=100, vmax=500, unit='%')
              
        S.New('ctemp', dtype=int, initial=6500, vmin=2000, vmax=15000)
        S.New('tint', dtype=int, initial=1000, vmin=200, vmax=2500)
        
        S.New('contrast', dtype=int, initial=0, vmin=-100, vmax=100)
        S.New('brightness', dtype=int, initial=0, vmin=-64, vmax=64)
        S.New('gamma', dtype=int, initial=100, vmin=20, vmax=180)
        
        calib_um_per_px_mag = S['calibration']*(S['res_mode']+1)
        if S['magnification'] != 0:
            calib_um_per_px = calib_um_per_px_mag/S['magnification']
        else:
            calib_um_per_px = 1
        S.New('calib_um_per_px', dtype=float, initial=calib_um_per_px, ro=True, spinbox_decimals=3)
        
        S.New('centerx_micron', dtype=float,initial= 1024.)
        S.New('centery_micron', dtype=float,initial= 768.)
        S.New('width_micron', dtype=float,initial= 2048.)
        S.New('height_micron', dtype=float, initial= 1536.)
        
        
    def connect(self):
        from .toupcam.camera import ToupCamCamera, get_number_cameras
        S = self.settings
        if S['magnification'] == 0:
            print('Set magnification first, then connect...')
            raise ValueError
        
        self.cam = ToupCamCamera(resolution=S['res_mode'], cam_index=S['cam_index'], debug=self.debug_mode.val)
        
        self.cam.open()
        
        #exposure
        S.auto_exposure.connect_to_hardware(
            read_func = self.cam.get_auto_exposure,
            write_func = self.set_auto_exposure
            )
        S.auto_exposure.read_from_hardware()
        S.exposure.connect_to_hardware(
            read_func = self.get_exposure_time,
            write_func = self.set_exposure_time
            )
        S.exposure.read_from_hardware()
        
        #white balance
        S.tint.connect_to_hardware(
            read_func = self.get_tint,
            write_func = self.set_tint
            )
        S.ctemp.connect_to_hardware(
            read_func = self.get_ctemp,
            write_func = self.set_ctemp
            )
        
        #color adjustment
        S.contrast.connect_to_hardware(
            read_func = self.get_contrast,
            write_func = self.set_contrast
            )
        S.brightness.connect_to_hardware(
            read_func = self.get_brightness,
            write_func = self.set_brightness
        )
        S.gamma.connect_to_hardware(
            read_func = self.get_gamma,
            write_func = self.set_gamma
            )
        S.gain.connect_to_hardware(
            read_func = self.get_gain,
            write_func = self.set_gain, 
            )
        
        #S.auto_exposure.hardware_set_func()

        # read and calibrate image size
        S['width_pixel'], S['height_pixel'] = self.get_size()
        calib_um_per_px_mag = S['calibration']*(S['res_mode']+1)
        calib_um_per_px = calib_um_per_px_mag/S['magnification']
        S['calib_um_per_px'] = calib_um_per_px
        S['width_micron'], S['height_micron'] = calib_um_per_px*S['width_pixel'], calib_um_per_px*S['height_pixel']
        S['centerx_micron'], S['centery_micron'] = calib_um_per_px*S['centerx_pixel']/(S['res_mode']+1), calib_um_per_px*S['centery_pixel']/(S['res_mode']+1)
        
    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'cam'):
            self.cam.close()
            del self.cam
    #####
    # functions camera     
    def get_size(self):
        w, h = self.cam.get_size()
        return w, h
    #####        
    # functions white balance      
    def set_tint(self,tint):
        ctemp = self.get_ctemp()
        self.cam.set_temperature_tint(int(ctemp), int(tint))     
    def get_tint(self):
        ctemp, tint = self.cam.get_temperature_tint()
        return tint

    def set_ctemp(self,ctemp):
        tint = self.get_tint()
        self.cam.set_temperature_tint(int(ctemp), int(tint))
    def get_ctemp(self):
        ctemp, tint = self.cam.get_temperature_tint()
        return ctemp
    #####
    # functions color adjustment  
    def get_contrast(self):
        return self.cam.get_contrast()
    def set_contrast(self, contrast):
        return self.cam.set_contrast(int(contrast))
    
    def get_brightness(self):
        return self.cam.get_brightness()
    def set_brightness(self, brightness):
        self.cam.set_brightness(int(brightness))
    
    def get_gamma(self):
        return self.cam.get_gamma()
    def set_gamma(self, gamma):
        return self.cam.set_gamma(int(gamma))
    #####
    # functions exposure  
    def get_exposure_time(self):
        return 1e-6 * self.cam.get_exposure_time()
    def set_exposure_time(self, exp_time):
        self.cam.set_exposure_time( int(1e6*exp_time))
    def get_gain(self):
        return self.cam.get_exposure_gain()
    def set_gain(self,gain):
        return self.cam.set_exposure_gain(gain)
        
    def set_auto_exposure(self, expo_enabled):
        #FixMe: always goes to auto exposure mode when openning connection?
        self.cam.set_auto_exposure(expo_enabled)
    
    def set_default_values(self):
        S = self.settings      
        S['tint'] = 1000
        S['ctemp'] = 6500
        S['contrast'] = 0
        S['gamma'] = 100
        S['brightness'] = 0
        S['gain'] = 100
        S['exposure'] = 0.096
        S['auto_exposure'] = False
        