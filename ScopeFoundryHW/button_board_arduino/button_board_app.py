'''
Created on Jun 21, 2017

@author: Alan Buckley
'''

from ScopeFoundry.base_app import BaseMicroscopeApp
import logging

logging.basicConfig(level=logging.DEBUG)

class ButtonBoardApp(BaseMicroscopeApp):
    
    name = 'button_board_app'
    
    def setup(self):
        
        from ScopeFoundryHW.button_board_arduino.button_board_hw import ButtonBoardHW
        self.add_hardware(ButtonBoardHW(self))
        
        from ScopeFoundryHW.button_board_arduino.button_board_optimizer import ButtonBoardOptimizer
        self.add_measurement(ButtonBoardOptimizer(self))
        
        self.ui.show()
        self.ui.activateWindow()
    
if __name__ == '__main__':
    import sys
    app = ButtonBoardApp(sys.argv)
    sys.exit(app.exec_())