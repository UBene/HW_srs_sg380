'''
Created on May 21, 2021

@author: Benedikt Ursprung
'''

from ScopeFoundryHW.mcl_stage.mcl_stage_slowscan import MCLStage2DSlowScan
from ScopeFoundryHW.picoquant.trpl_2d_scan_base import TRPL2DScanBase 

class MCL_TRPL2DScan(MCLStage2DSlowScan, TRPL2DScanBase):
    
    name = 'mcl_trpl_2d_scan'
        
    def __init__(self, app):
        MCLStage2DSlowScan.__init__(self, app)
    
    def setup(self):
        MCLStage2DSlowScan.setup(self)
        TRPL2DScanBase.setup(self)
    
    def setup_figure(self):
        TRPL2DScanBase.setup_figure(self)

    def pre_scan_setup(self):
        TRPL2DScanBase.pre_scan_setup(self)
    
    def collect_pixel(self, pixel_num, k, j, i):
        TRPL2DScanBase.collect_pixel(self, pixel_num, k, j, i)

    def post_scan_cleanup(self):
        TRPL2DScanBase.post_scan_cleanup(self)
                
    def update_display(self):
        TRPL2DScanBase.update_display(self)