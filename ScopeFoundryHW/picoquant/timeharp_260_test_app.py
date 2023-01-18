'''
Created on April 20, 2022

@author: Benedikt Ursprung
'''

from ScopeFoundry.base_app import BaseMicroscopeApp

class TestApp(BaseMicroscopeApp):
    
    name = 'test_app'
    
    def setup(self):
        from ScopeFoundryHW.picoquant.timeharp_260_hw import TimeHarp260HW
        self.add_hardware(TimeHarp260HW(self))
        from ScopeFoundryHW.picoquant.timeharp_260_optimizer import TimeHarpOptimizerMeasure
        self.add_measurement(TimeHarpOptimizerMeasure(self))
        from ScopeFoundryHW.picoquant.timeharp_260_hist_measure import TimeHarpHistogramMeasure
        self.add_measurement(TimeHarpHistogramMeasure(self))
        from ScopeFoundryHW.picoquant.trpl_2d_scan_base import TRPL2DScanBase
        self.add_measurement(TRPL2DScanBase(self))
        from ScopeFoundryHW.picoquant.timeharp_260_tttr_measure import Timeharp260TTTRMeasure
        self.add_measurement(Timeharp260TTTRMeasure(self))


if __name__ == '__main__':
    app = TestApp()
    app.exec_()