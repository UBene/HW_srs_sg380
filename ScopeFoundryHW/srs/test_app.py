'''
Created on Dec 14, 2022

@author: Benedikt Ursprung
'''
from ScopeFoundry import BaseMicroscopeApp
import logging

logging.basicConfig(level='DEBUG')
logging.getLogger("ipykernel").setLevel(logging.WARNING)
logging.getLogger('PyQt4').setLevel(logging.WARNING)
logging.getLogger('PyQt5').setLevel(logging.WARNING)
logging.getLogger('LoggedQuantity').setLevel(logging.WARNING)
logging.getLogger('pyvisa').setLevel(logging.WARNING)


class Microscope(BaseMicroscopeApp):

    name = 'srs_test_app'

    def setup(self):

        from ScopeFoundryHW.srs.sg380_hw import SG380_HW
        self.add_hardware(SG380_HW(self))


if __name__ == '__main__':
    import sys
    app = Microscope(sys.argv)
    sys.exit(app.exec_())
