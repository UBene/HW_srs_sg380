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


class DLIApp(BaseMicroscopeApp):
    
    name="dli_app"
    
    def setup(self):
        """Registers :class:`HardwareComponent` object, such that the top level `DLIApp` may access its functions."""
        from ScopeFoundryHW.dli_powerswitch.dlipower_hardware import DLIPowerSwitchHW
        self.add_hardware(DLIPowerSwitchHW(self))
        

if __name__ == '__main__':
    import sys
    app = DLIApp(sys.argv)
    sys.exit(app.exec_())    
        