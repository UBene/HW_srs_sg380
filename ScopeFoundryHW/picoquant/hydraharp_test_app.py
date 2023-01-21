'''
Created on June 7, 2019

@author: Benedikt Ursprung
'''

from ScopeFoundry.base_app import BaseMicroscopeApp


class TestApp(BaseMicroscopeApp):

    name = 'test_app'

    def setup(self):
        from ScopeFoundryHW.picoquant.hydraharp_hw import HydraHarpHW
        self.add_hardware(HydraHarpHW(self))
        from ScopeFoundryHW.picoquant.hydraharp_optimizer import HydraHarpOptimizerMeasure
        self.add_measurement(HydraHarpOptimizerMeasure(self))
        from ScopeFoundryHW.picoquant.hydraharp_hist_measure import HydraHarpHistogramMeasure
        self.add_measurement(HydraHarpHistogramMeasure(self))
        from ScopeFoundryHW.picoquant.trpl_2d_scan_base import TRPL2DScanBase
        self.add_measurement(TRPL2DScanBase(self))
        # from ScopeFoundryHW.picoquant.timeharp_260_tttr_measure import Timeharp260TTTRMeasure
        # self.add_measurement(Timeharp260TTTRMeasure(self))


if __name__ == '__main__':
    app = TestApp()
    app.exec_()
