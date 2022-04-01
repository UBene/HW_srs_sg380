'''
Created on Mar 26, 2022

@author: bened
'''
from ScopeFoundry.scanning.base_raster_slow_scan import BaseRaster2DSlowScan
import time
import numpy as np

class GalvoMirror2DSlowScan(BaseRaster2DSlowScan):
    
    name = "galvo_mirror_2D_slow_scan"
    
    def __init__(self, app, use_external_range_sync=False, circ_roi_size=0.001):
        BaseRaster2DSlowScan.__init__(self, app, h_limits=(-12.5,12.5), v_limits=(-12.5,12.5), h_unit="mm", v_unit="mm", 
                                      use_external_range_sync=use_external_range_sync,
                                      circ_roi_size=circ_roi_size)        
    
    def setup(self):
        BaseRaster2DSlowScan.setup(self)
        #Hardware
        self.stage = self.app.hardware['galvo_mirrors']
        self.target_range = 0.050e-3 # um
        self.slow_move_timeout = 10. # sec

        self.settings.New("h_axis", initial="x", dtype=str, choices=("x", "y", "z"))
        self.settings.New("v_axis", initial="y", dtype=str, choices=("x", "y", "z"))
        #self.ax_map = dict(x=0, y=1, z=2)
        

    def collect_pixel(self, pixel_num, k, j, i):
        raise NotImplementedError
        pass

    def move_position_start(self, h,v):
        self.move_position_slow(h,v, 0, 0, timeout=30)
    
    def move_position_slow(self, h,v, dh,dv, timeout=10):
        # update target position
        S = self.settings 
        self.stage.settings[S['h_axis'] + "_target_position"] = h
        self.stage.settings[S['v_axis'] + "_target_position"] = v
        
        t0 = time.time()
        
        # Wait until stage has moved to target
        while True:
            self.stage.settings.x_position.read_from_hardware()
            self.stage.settings.y_position.read_from_hardware()
            self.stage.settings.z_position.read_from_hardware()
            if self.distance_from_target() < self.target_range:
                #print("settle time {}".format(time.time() - t0))
                break
            if (time.time() - t0) > timeout:
                raise IOError("AttoCube ECC100 took too long to reach position")
            time.sleep(0.005)

    def move_position_fast(self,  h,v, dh,dv):
        self.move_position_slow( h,v, dh,dv)
        #settle time even on small steps seems to be 30ms,
        #so we should always wait until settle
        """# update target position, but don't wait to settle to target
        self.stage.settings.x_target_position.update_value(x)
        self.stage.settings.y_target_position.update_value(y)
        self.stage.settings.x_position.read_from_hardware()
        self.stage.settings.y_position.read_from_hardware()
        """
    def distance_from_target(self):
        S = self.stage.settings
        return np.sqrt(    (S['x_position'] - S['x_target_position'])**2 
                         + (S['y_position'] - S['y_target_position'])**2
                         + (S['z_position'] - S['z_target_position'])**2)
