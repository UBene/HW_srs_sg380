'''
Created on Mar 20, 2017

@author: lab
'''


from __future__ import division, print_function
from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import sibling_path#, load_qt_ui_file

import logging
logging.basicConfig(level=logging.DEBUG)

class ANC_Remote_App(BaseMicroscopeApp):

    name = 'anc_remote_app'
    
    def setup(self):


        from ScopeFoundryHW.attocube_anc150.anc150_HW import ANC_HW
        self.add_hardware(ANC_HW(self))
        
        from ScopeFoundryHW.xbox_controller.xbcontrol_hc import XboxControlHW
        self.add_hardware(XboxControlHW(self))

        from ScopeFoundryHW.attocube_anc150.anc_remote_measure import ANC_RemoteMeasure
        self.add_measurement(ANC_RemoteMeasure(self)) 
        
        from ScopeFoundryHW.xbox_controller.xbcontrol_mc import XboxControlMeasure
        self.add_measurement(XboxControlMeasure(self))
        
        self.settings_load_ini(sibling_path(__file__, 'anc_defaults.ini'))

if __name__ == '__main__':
    import sys
    app = ANC_Remote_App(sys.argv)
    sys.exit(app.exec_())