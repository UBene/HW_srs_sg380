'''
Created on Jun 21, 2017

@author: Alan Buckley
'''
from __future__ import absolute_import, print_function, division
from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import time

class ButtonBoardOptimizer(Measurement):
    
    name = "button_board_optimizer"
    
    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "button_board_widget.ui")
        self.ui = load_qt_ui_file(self.ui_filename)
        self.ui.setWindowTitle(self.name)
        Measurement.__init__(self, app)
        self.dt = 0.05
    
    def setup(self):
        self.app
        self.hw = self.app.hardware['button_board_hw']
        
        self.hw.chan1.connect_to_widget(self.ui.chan1_cbox)
        
        self.hw.chan2.connect_to_widget(self.ui.chan2_cbox)
        
        self.hw.chan3.connect_to_widget(self.ui.chan3_cbox)
        
        self.hw.chan4.connect_to_widget(self.ui.chan4_cbox)
        
    def run(self):
#         while not self.interrupt_measurement_called:
#             time.sleep(self.dt)
        while not self.interrupt_measurement_called:
            time.sleep(self.dt)
            self.hw.button_listen()