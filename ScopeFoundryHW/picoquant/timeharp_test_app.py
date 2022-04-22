'''
Created on April 20, 2022

@author: Benedikt Ursprung
'''

from ScopeFoundry.base_app import BaseMicroscopeApp
from ScopeFoundryHW.picoquant.hydraharp_hw import HydraHarpHW
from ScopeFoundryHW.picoquant.hydraharp_optimizer import HydraHarpOptimizerMeasure
from ScopeFoundryHW.picoquant.hydraharp_hist_measure import HydraHarpHistogramMeasure
   
from ScopeFoundryHW.picoquant.timeharp_260_hw import TimeHarp260HW
from ScopeFoundryHW.picoquant.timeharp_optimizer import TimeHarpOptimizerMeasure
from ScopeFoundryHW.picoquant.timeharp_260_hist_measure import TimeHarpHistogramMeasure
from ScopeFoundryHW.picoquant.trpl_2d_scan_base import TRPL2DScanBase

class HydraHarpTestApp(BaseMicroscopeApp):
    
    name = 'hydraharp_test_app'
    
    def setup(self):
        
        self.add_hardware(TimeHarp260HW(self))
        self.add_measurement(TimeHarpOptimizerMeasure(self))
        self.add_measurement(TimeHarpHistogramMeasure(self))
        self.add_measurement(TRPL2DScanBase(self))

        #self.add_measurement(HydraHarpHistogramMeasure(self))
        #self.add_measurement(TRPL2DScan(self))


app = HydraHarpTestApp()
app.exec_()