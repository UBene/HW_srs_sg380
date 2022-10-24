'''
Created on Sep 17, 2021

@author: Benedikt Ursprung
'''
from ScopeFoundry.base_app import BaseMicroscopeApp
# from ScopeFoundryHW.nidaqmx.pseudo_lock_in import PseudoLockIn
# from ScopeFoundryHW.nidaqmx.lock_in_map import LockIn2dMap


class App(BaseMicroscopeApp):

    name = 'test_app'

    def setup(self):

        # self.add_hardware(PseudoLockIn(self))
        # self.add_measurement(LockIn2dMap(self))
        from ScopeFoundryHW.nidaqmx.single_pulse_ttl import SinglePulse
        self.add_hardware(SinglePulse)


if __name__ == '__main__':
    import sys
    app = App(sys.argv)
    sys.exit(app.exec_())
