'''
Created on Sep 17, 2021

@author: Benedikt Ursprung
'''
from ScopeFoundry.base_app import BaseMicroscopeApp
import lock_in_hw
import lock_in_map


class App(BaseMicroscopeApp):

    name = 'test_app'

    def setup(self):

        self.add_hardware(lock_in_hw.LockInHW(self))
        self.add_measurement(lock_in_map.LockIn2dMap(self))


if __name__ == '__main__':
    import sys
    app = App(sys.argv)
    sys.exit(app.exec_())
