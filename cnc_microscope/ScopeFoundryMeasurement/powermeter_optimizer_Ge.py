'''
Created on Oct 27, 2016

@author: Edward Barnard
'''
from __future__ import absolute_import, division, print_function
from ScopeFoundry import Measurement
import numpy as np
import pyqtgraph as pg
import time
from ScopeFoundry.helper_funcs import sibling_path, replace_widget_in_layout
from ScopeFoundry import h5_io


class PowerMeterOptimizerMeasure(Measurement):

    name = "powermeter_optimizer_Ge"
    
    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "powermeter_optimizer.ui")
        super(PowerMeterOptimizerMeasure, self).__init__(app)    

    def setup(self):        
        self.display_update_period = 0.1 #seconds

        # logged quantities
        self.save_data = self.settings.New(name='save_data', dtype=bool, initial=False, ro=False)
        self.settings.New(name='update_period', dtype=float, si=True, initial=0.1, unit='s')
        
        # create data array
        self.OPTIMIZE_HISTORY_LEN = 500
        self.optimize_history = np.zeros(self.OPTIMIZE_HISTORY_LEN, dtype=np.float)        
        self.optimize_ii = 0

        # hardware???
        self.powermeter = self.app.hardware.thorlabs_powermeter_Ge
        
        #connect events
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        
        ###Refresh display when the "refresh display" button is clicked, added by Kaiyuan 11/10/2018
        self.ui.refresh_pushButton.clicked.connect(self.refresh_display)
        self.refresh_display_called = False
        

        self.save_data.connect_bidir_to_widget(self.ui.save_data_checkBox)
        
        self.ui.power_readout_PGSpinBox = replace_widget_in_layout(self.ui.power_readout_doubleSpinBox,
                                                                       pg.widgets.SpinBox.SpinBox())
        self.powermeter.settings.power.connect_bidir_to_widget(self.ui.power_readout_PGSpinBox)
        
        self.powermeter.settings.power.connect_bidir_to_widget(self.ui.power_readout_label)
        self.powermeter.settings.wavelength.connect_bidir_to_widget(self.ui.wavelength_doubleSpinBox)
        
        
    def setup_figure(self):
        self.optimize_ii = 0
        
        # ui window
        if hasattr(self, 'graph_layout'):
            self.graph_layout.deleteLater() # see http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            del self.graph_layout
        
        # graph_layout
        self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)

        # history plot
        self.plot = self.graph_layout.addPlot(title="Power Meter Optimizer")
        self.optimize_plot_line = self.plot.plot([0])        


    def run(self):
        self.display_update_period = 0.02 #seconds

        #self.apd_counter_hc = self.gui.apd_counter_hc
        #self.apd_count_rate = self.apd_counter_hc.apd_count_rate
        #self.pm_hc = self.gui.thorlabs_powermeter_hc
        #self.pm_analog_readout_hc = self.gui.thorlabs_powermeter_analog_readout_hc
        

        if self.save_data.val:
            self.full_optimize_history = []
            self.full_optimize_history_time = []
            self.t0 = time.time()

        while not self.interrupt_measurement_called:
            self.optimize_ii += 1
            self.optimize_ii %= self.OPTIMIZE_HISTORY_LEN
            
            pow_reading = self.powermeter.settings.power.read_from_hardware()

            self.optimize_history[self.optimize_ii-1] = pow_reading
            #self.pm_analog_readout_hc.voltage.read_from_hardware()
            
            ###Refresh display when the "refresh display" button is clicked, added by Kaiyuan 11/10/2018
            if self.refresh_display_called:
                self.optimize_history = np.zeros(self.OPTIMIZE_HISTORY_LEN, dtype=np.float)        
                self.optimize_ii = 0
                self.refresh_display_called = False

            
            if self.save_data.val:
                self.full_optimize_history.append(pow_reading)
                self.full_optimize_history_time.append(time.time() - self.t0)
            
            time.sleep(self.settings['update_period'])
            #time.sleep(0.02)
            
        if self.settings['save_data']:
            try:
                self.h5_file = h5_io.h5_base_file(self.app, measurement=self )
                self.h5_file.attrs['time_id'] = self.t0
                H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
            
                #create h5 data arrays
                H['power_optimze_history'] = self.full_optimize_history
                H['optimze_history_time'] = self.full_optimize_history_time
            finally:
                self.h5_file.close()
            
    
    def update_display(self):        
        #self.optimize_plot_line.setData(self.optimize_history)
        self.optimize_plot_line.setData(self.optimize_history[self.optimize_history!=0])
        
    def refresh_display(self):
        self.refresh_display_called = True
