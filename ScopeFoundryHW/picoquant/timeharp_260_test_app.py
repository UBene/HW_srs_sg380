'''
Created on April 20, 2022

@author: Benedikt Ursprung
'''

from ScopeFoundry.base_app import BaseMicroscopeApp


class TestApp(BaseMicroscopeApp):

    name = 'test_app'

    def setup(self):
        from ScopeFoundryHW.picoquant import TimeHarp260HW, TimeHarpOptimizerMeasure, TimeHarpHistogramMeasure, Timeharp260TTTRMeasure, TRPL2DScanBase
        self.add_hardware(TimeHarp260HW(self))
        self.add_measurement(TimeHarpOptimizerMeasure(self))
        self.add_measurement(TimeHarpHistogramMeasure(self))
        self.add_measurement(Timeharp260TTTRMeasure(self))
        self.add_measurement(TRPL2DScanBase(self))


if __name__ == '__main__':
    app = TestApp()
    app.exec_()
