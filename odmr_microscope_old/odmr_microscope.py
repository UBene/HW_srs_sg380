from ScopeFoundry import BaseMicroscopeApp
import logging
from odmr_microscope.measurements.config_measurement import ConfigMeasurement



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


        from ScopeFoundryHW.nidaqmx.triggered_analog_readout import DAQTriggeredDReadout, DAQTriggeredAReadout
        self.add_hardware(DAQTriggeredDReadout(self))
        #self.add_hardware(DAQTriggeredAReadout(self))
                
        self.add_measurement(ConfigMeasurement(self))
                
                
if __name__ == '__main__':
    import sys
    app = Microscope(sys.argv)
    app.settings_load_ini('defaults.ini')
    # app.load_window_positions_json(r'window_positions.json')
    sys.exit(app.exec_())
