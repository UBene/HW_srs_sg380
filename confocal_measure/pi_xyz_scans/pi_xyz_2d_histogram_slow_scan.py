'''
Created on Apr 20, 2022

@author: Benedikt Ursprung
'''
from ScopeFoundryHW.picoquant.trpl_2d_scan_base import TRPL2DScanBase


class PIXYZ2DHistogramSlowScan(TRPL2DScanBase):

    name = 'histogram_2d_map'

    def setup(self):
        TRPL2DScanBase.setup(self)

        # Hardware
        self.stage = self.app.hardware['PI_xyz_stage']
        self.settings.New("h_axis", initial="x", dtype=str,
                          choices=("x", "y", "z"))
        self.settings.New("v_axis", initial="y", dtype=str,
                          choices=("x", "y", "z"))

    def move_position_start(self, h, v):
        self.move_position_slow(h, v, 0, 0, timeout=30)

    def move_position_slow(self, h, v, dh, dv, timeout=10):
        # update target position
        S = self.settings
        self.stage.settings[S['h_axis'] + "_target"] = h
        self.stage.settings[S['v_axis'] + "_target"] = v

    def move_position_fast(self, h, v, dh, dv):
        self.move_position_slow(h, v, dh, dv)
