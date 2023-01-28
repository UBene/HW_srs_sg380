'''
Created on Dec 14, 2022

@author: Benedikt Ursprung
'''
import logging

from ScopeFoundry import BaseMicroscopeApp

logging.basicConfig(level='DEBUG')
logging.getLogger("ipykernel").setLevel(logging.WARNING)
logging.getLogger('PyQt4').setLevel(logging.WARNING)
logging.getLogger('PyQt5').setLevel(logging.WARNING)
logging.getLogger('LoggedQuantity').setLevel(logging.WARNING)
logging.getLogger('pyvisa').setLevel(logging.WARNING)


class Microscope(BaseMicroscopeApp):

    name = 'srs_sg380_test_app'

    def setup(self):

        from ScopeFoundryHW.srs_sg380 import SG380HW
        self.add_hardware(SG380HW(self))


if __name__ == '__main__':
    import sys
    app = Microscope(sys.argv)
    sys.exit(app.exec_())
