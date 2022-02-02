'''
Created on Feb 13, 2021

@author: Benedikt Ursprung
'''

from ScopeFoundryHW.asi_stage.asi_stage_raster import ASIStage2DScan
from ScopeFoundryHW.picoquant.trpl_2d_scan_base import TRPL2DScanBase 

class ASI_TRPL2DScan(ASIStage2DScan, TRPL2DScanBase):
    
    name = 'asi_trpl_2d_scan'
        
    def __init__(self, app):
        ASIStage2DScan.__init__(self, app)
    
    def setup(self):
        ASIStage2DScan.setup(self)
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