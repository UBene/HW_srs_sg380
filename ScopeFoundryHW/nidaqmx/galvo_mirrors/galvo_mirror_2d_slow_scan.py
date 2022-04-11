'''
Created on Mar 26, 2022

@author: Benedikt Ursprung
'''
from ScopeFoundry.scanning.base_raster_slow_scan import BaseRaster2DSlowScan
import time
import numpy as np


class GalvoMirror2DSlowScan(BaseRaster2DSlowScan):
    
    name = "galvo_mirror_2D_slow_scan"
    
    def __init__(self, app, use_external_range_sync=False, circ_roi_size=0.001, h_limits=(-12.5, 12.5), v_limits=(-12.5, 12.5), h_unit="um", v_unit="um"):
        BaseRaster2DSlowScan.__init__(self, app, h_limits=h_limits, v_limits=v_limits, h_unit=h_unit, v_unit=v_unit,
                                      use_external_range_sync=use_external_range_sync,
                                      circ_roi_size=circ_roi_size)        
    
    def setup(self):
        BaseRaster2DSlowScan.setup(self)
        
        # Hardware
        self.stage = self.app.hardware['galvo_mirrors']
        self.slow_move_timeout = 10.  # sec

        self.settings.New("h_axis", initial="x", dtype=str, choices=("x", "y", "z"))
        self.settings.New("v_axis", initial="y", dtype=str, choices=("x", "y", "z"))

    def collect_pixel(self, pixel_num, k, j, i):
        raise NotImplementedError
        pass

    def move_position_start(self, h, v):
        self.move_position_slow(h, v, 0, 0, timeout=30)
    
    def move_position_slow(self, h, v, dh, dv, timeout=10):
        # update target position
        S = self.settings 
        self.stage.settings[S['h_axis'] + "_target_position"] = h
        self.stage.settings[S['v_axis'] + "_target_position"] = v
        
        t0 = time.time()

    def move_position_fast(self, h, v, dh, dv):
        print("move_position_fast Not implemented, using move_position_slow instead")
        self.move_position_slow(h, v, dh, dv)
