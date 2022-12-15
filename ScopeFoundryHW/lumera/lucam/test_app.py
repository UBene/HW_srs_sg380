'''
Created on Dec 9, 2022

@author: Benedikt Ursprung
'''
import logging

from ScopeFoundry import BaseMicroscopeApp


level = 'DEBUG'
logging.basicConfig(level='DEBUG')
logging.getLogger('LoggedQuantity').setLevel(logging.DEBUG)


class TestApp(BaseMicroscopeApp):

    name = 'lucam_test_app'

    def setup(self):

        from ScopeFoundryHW.lumera.lucam.lucam_hw import LucamHW
        self.add_hardware(LucamHW(self))
        from ScopeFoundryHW.lumera.lucam.lucam_measure import LucamMeasure
        self.add_measurement(LucamMeasure(self))


if __name__ == '__main__':
    import sys
    app = TestApp(sys.argv)
    sys.exit(app.exec_())
