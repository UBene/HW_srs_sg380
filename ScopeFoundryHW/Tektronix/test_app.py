'''
Created on Jan 16, 2023

@author: Benedikt Ursprung
'''
from ScopeFoundry.base_app import BaseMicroscopeApp


class TestApp(BaseMicroscopeApp):

    def setup(self):
        from ScopeFoundryHW.Tektronix.scope_hw import TektronixScopeHW
        self.add_hardware(TektronixScopeHW(self))
        from ScopeFoundryHW.Tektronix.waveform_measure import TektronixWaveform
        self.add_measurement(TektronixWaveform(self))

if __name__ == '__main__':
    app = TestApp([])
    app.exec_()
