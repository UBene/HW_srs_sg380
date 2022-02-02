'''
Created on Feb 28, 2017

@author: Alan Buckley
         Benedikt Ursprung
'''
from ScopeFoundry.base_app import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import sibling_path
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('PyQt5').setLevel(logging.WARN)
logging.getLogger('ipykernel').setLevel(logging.WARN)
logging.getLogger('traitlets').setLevel(logging.WARN)


class ThorlabsMFFApp(BaseMicroscopeApp):
    
    name="thorlabs_MFF_app"
    
    def setup(self):
        """Registers :class:`HardwareComponent` object, such that the top level `DLIApp` may access its functions."""
        from ScopeFoundryHW.thorlabs_motorized_filter_flipper.thorlabsMFF_hardware import ThorlabsMFFHW
        self.add_hardware(ThorlabsMFFHW(self))
        

if __name__ == '__main__':
    import sys
    app = ThorlabsMFFApp(sys.argv)
    sys.exit(app.exec_())    
