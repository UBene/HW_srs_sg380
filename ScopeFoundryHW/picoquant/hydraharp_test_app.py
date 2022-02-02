'''
Created on June 7, 2019

@author: Benedikt Ursprung
'''

from ScopeFoundry.base_app import BaseMicroscopeApp
from ScopeFoundryHW.picoquant.hydraharp_hw import HydraHarpHW
from ScopeFoundryHW.picoquant.hydraharp_optimizer import HydraHarpOptimizerMeasure
from ScopeFoundryHW.picoquant.hydraharp_hist_measure import HydraHarpHistogramMeasure
from ScopeFoundryHW.picoquant.trpl_2d_scan_base import TRPL2DScan

class HydraHarpTestApp(BaseMicroscopeApp):
    
    name = 'hydraharp_test_app'
    
    def setup(self):
        
        self.add_hardware(HydraHarpHW(self))
        self.add_measurement(HydraHarpOptimizerMeasure(self))
        self.add_measurement(HydraHarpHistogramMeasure(self))
        #self.add_measurement(TRPL2DScan(self))


app = HydraHarpTestApp()
app.exec_()