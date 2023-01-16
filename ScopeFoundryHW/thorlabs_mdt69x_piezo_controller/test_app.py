"""
Created on Jan 15, 2023

@author: Benedikt Ursprung
"""

from ScopeFoundry import BaseMicroscopeApp
import logging


logging.basicConfig(level='DEBUG')
logging.getLogger("ipykernel").setLevel(logging.WARNING)
logging.getLogger('PyQt4').setLevel(logging.WARNING)
logging.getLogger('PyQt5').setLevel(logging.WARNING)
logging.getLogger('LoggedQuantity').setLevel(logging.WARNING)
logging.getLogger('pyvisa').setLevel(logging.WARNING)


class Microscope(BaseMicroscopeApp):

    name = 'piezo_controller_test_app'

    def setup(self):

        from ScopeFoundryHW.thorlabs_mdt69x_piezo_controller.hw import HW
        self.add_hardware(HW(self))
        from ScopeFoundryHW.thorlabs_mdt69x_piezo_controller.base_2d_slow_scan import Base2DSlowScan
        self.add_measurement(Base2DSlowScan(self, h_unit='V', v_unit='V'))


if __name__ == '__main__':
    import sys
    app = Microscope(sys.argv)
    sys.exit(app.exec_())
