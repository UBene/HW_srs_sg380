'''
Created on Aug 22, 2017

@author: Alan Buckley <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
'''

from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import time 

class ThorlabsDMP40_Measure(Measurement):
    
    name = 'dmp40_measure'
    
    def setup(self):

        self.dmp40_hw = self.app.hardware['dmp40_hw']
        self.ui_filename = sibling_path(__file__, "mirror.ui")
        self.ui = load_qt_ui_file(self.ui_filename)
        self.ui.setWindowTitle(self.name)
        
        for k in self.dmp40_hw.zernike.keys():
            widget = getattr(self.ui, k)
            self.dmp40_hw.settings.get_lq(k).connect_to_widget(widget)
            self.dmp40_hw.settings.get_lq(k).add_listener(self.sync_checkBoxes)    
            
    def sync_checkBoxes(self):
        for k in self.dmp40_hw.zernike.keys():
            cb = getattr(self.ui, "{}_checkBox".format(k))
            if self.dmp40_hw.settings[k] != 0.0:
                if self.ui is not None:       
                    cb.setChecked(True)
            else:
                if self.ui is not None:
                    cb.setChecked(False)

        
    def run(self):
        while not self.interrupt_measurement_called:
            if hasattr(self.dmp40_hw, "dev"):
                IC1, IC2, Mir, E = self.dmp40_hw.dev.get_temperatures()
                self.dmp40_hw.settings['IC1_temp'] = IC1
                self.dmp40_hw.settings['IC2_temp'] = IC2
                self.dmp40_hw.settings['Mirror_temp'] = Mir
                self.dmp40_hw.settings['Electronics_temp'] = E
                time.sleep(1)
            else:
                self.interrupt()