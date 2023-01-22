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

    name = 'snspd_test_app'

    def setup(self):

        from ScopeFoundryHW.single_quantum.snspd import SNSPDHW, SNSPDOptimizerMeasure, SNSPDAquireCounts
        self.add_hardware(SNSPDHW(self))
        self.add_measurement(SNSPDOptimizerMeasure(self))
        self.add_measurement(SNSPDAquireCounts(self))


if __name__ == '__main__':
    import sys
    app = TestApp(sys.argv)
    sys.exit(app.exec_())
