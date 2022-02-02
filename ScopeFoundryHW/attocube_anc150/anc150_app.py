'''
Created on Feb 28, 2017

@author: Alan Buckley
'''
from ScopeFoundry.base_app import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import sibling_path
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('PyQt5').setLevel(logging.WARN)
logging.getLogger('ipykernel').setLevel(logging.WARN)
logging.getLogger('traitlets').setLevel(logging.WARN)


class AttocubeANCApp(BaseMicroscopeApp):
    
    name="anc_app"
    
    def setup(self):
        from ScopeFoundryHW.attocube_anc150.anc150_HW import ANC_HW
        self.add_hardware(ANC_HW(self))
        
        #from ScopeFoundryHW.attocube_anc150.anc150_optimizer import ANC_Optimizer
        #self.add_measurement(ANC_Optimizer(self))
        
        from ScopeFoundryHW.xbox_controller.xbcontrol_hc import XboxControlHW
        self.add_hardware(XboxControlHW(self))
        
        from ScopeFoundryHW.attocube_anc150.anc_remote_measure import ANC_RemoteMeasure
        self.add_measurement(ANC_RemoteMeasure(self))
        
        self.ui.lq_trees_groupBox.hide()
        
        self.settings_load_ini(sibling_path(__file__, 'anc_defaults.ini'))
        
if __name__ == '__main__':
    import sys
    app = AttocubeANCApp(sys.argv)
    sys.exit(app.exec_())    
        