'''
Created on Feb 28, 2017

@author: Alan Buckley
Helpful feedback from Ed Barnard
'''

from __future__ import absolute_import, print_function, division
from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import time

class ANC_Optimizer(Measurement):
    
    name = "anc_optimizer"
    

    def setup(self):
        self.ui_filename = sibling_path(__file__, "anc150.ui")
        self.ui = load_qt_ui_file(self.ui_filename)

        self.anc = self.app.hardware['anc150']

        self.axis_lq_reload()
        self.anc.settings.get_lq('axis').connect_to_widget(
            self.ui.axis_comboBox)
        
#         self.ui.move_start_pushButton.clicked.connect(self.anc.move_start)
#         self.ui.move_stop_pushButton.clicked.connect(self.anc.move_stop)

        self.anc.settings.axis.updated_value.connect(self.axis_lq_reload)
        

        
    def axis_lq_reload(self):
        self.axis = self.anc.settings['axis']
        
        self.anc.settings.get_lq('axis_mode{}'.format(self.axis)).connect_to_widget(
            self.ui.axis_mode_comboBox)
        self.anc.settings.get_lq('frequency{}'.format(self.axis)).connect_to_widget(
            self.ui.frequency_doubleSpinBox)
        self.anc.settings.get_lq('voltage{}'.format(self.axis)).connect_to_widget(
            self.ui.voltage_doubleSpinBox)
        self.anc.settings.get_lq('capacitance{}'.format(self.axis)).connect_to_widget(
            self.ui.cap_doubleSpinBox)
        self.anc.settings.get_lq('move_direction{}'.format(self.axis)).connect_to_widget(
            self.ui.move_dir_comboBox)
        self.anc.settings.get_lq('move_mode{}'.format(self.axis)).connect_to_widget(
            self.ui.move_mode_comboBox)
        self.anc.settings.get_lq('move_steps{}'.format(self.axis)).connect_to_widget(
            self.ui.move_step_doubleSpinBox)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        