'''
Created on Jul 20, 2017

@author: Alan Buckley
'''

from ScopeFoundry.base_app import BaseMicroscopeApp
import logging

logging.basicConfig(level=logging.DEBUG)

class PololuApp(BaseMicroscopeApp):
    
    name = 'pololu_servo_app'
    
    def setup(self):
        """
        Adds Pololu servo hardware component into ScopeFoundry application.
        """
        from ScopeFoundryHW.pololu_servo.pololu_hw import PololuHW
        self.add_hardware(PololuHW(self))
        
        from ScopeFoundryHW.pololu_servo.single_servo_hw import PololuMaestroServoHW
        self.add_hardware(PololuMaestroServoHW(self))
    
if __name__ == '__main__':
    import sys
    app = PololuApp(sys.argv)
    sys.exit(app.exec_())