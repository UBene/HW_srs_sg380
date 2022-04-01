from __future__ import division, print_function
from ScopeFoundry import BaseMicroscopeApp
import logging



logging.basicConfig(level='DEBUG')
logging.getLogger("ipykernel").setLevel(logging.WARNING)
logging.getLogger('PyQt4').setLevel(logging.WARNING)
logging.getLogger('PyQt5').setLevel(logging.WARNING)
logging.getLogger('LoggedQuantity').setLevel(logging.WARNING)
logging.getLogger('pyvisa').setLevel(logging.WARNING)



class Microscope(BaseMicroscopeApp):

    name = 'odmr_microscope'

    def setup(self):    
        from ScopeFoundryHW.srs.SRS_HW import SRS
        self.add_hardware(SRS)
        
        from ScopeFoundryHW.spincore.spinapi_hw import PulseBlasterHW
        self.add_hardware(PulseBlasterHW(self))
        
        from measurements.transition import ConfigMeasurement
        self.add_measurement(ConfigMeasurement)
                
                
if __name__ == '__main__':
    import sys
    app = Microscope(sys.argv)
    app.settings_load_ini('defaults.ini')
    # app.load_window_positions_json(r'window_positions.json')
    sys.exit(app.exec_())
