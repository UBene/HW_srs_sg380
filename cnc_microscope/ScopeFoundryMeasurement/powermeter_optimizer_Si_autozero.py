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

    name = "powermeter_optimizer_Si_auto"
    
    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "powermeter_optimizer_autozero.ui")
        super(PowerMeterOptimizerMeasure, self).__init__(app)    

    def setup(self):        
        self.display_update_period = 0.1 #seconds

        # logged quantities
        self.powerwheel_type = self.settings.New('powerwheel_type', dtype=str, initial='Main',
                                          choices=('Main', 'Side'))

        self.save_data = self.settings.New(name='save_data', dtype=bool, initial=False, ro=False)
        self.settings.New(name='update_period', dtype=float, si=True, initial=0.1, unit='s')
        
        # create data array
        self.OPTIMIZE_HISTORY_LEN = 500
        self.optimize_history = np.zeros(self.OPTIMIZE_HISTORY_LEN, dtype=np.float)        
        self.optimize_ii = 0

        # hardware???
        self.powermeter = self.app.hardware.thorlabs_powermeter_Si

        
        #connect events
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        
        #add operation for auto_zero_encoder
        
        self.add_operation('auto_zero_encoder', self.auto_zero_encoder)
        
        self.ui.auto_zero_encoder_pushButton.clicked.connect(self.auto_zero_encoder)

        self.save_data.connect_bidir_to_widget(self.ui.save_data_checkBox)
        self.powerwheel_type.connect_to_widget(self.ui.powerwheel_type_comboBox)
        
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
    
    # 
    def auto_zero_encoder(self):
        if self.powerwheel_type.val == "Main":
            self.powerwheel_hw = self.app.hardware.main_beam_power_wheel
        elif self.powerwheel_type.val == "Side":
            self.powerwheel_hw = self.app.hardware.side_beam_power_wheel
        
        self.powerwheel_dev = self.powerwheel_hw.power_wheel_dev

        
        
        rough_step = 200
        fine_step = 10
        
        current_pm_power = self.collect_pm_power_data()
        negative_slope = False

        for num_rotation in np.arange(18):
            previous_pm_power = current_pm_power
            self.powerwheel_dev.write_steps_and_wait(rough_step)
            current_pm_power = self.collect_pm_power_data()
            if current_pm_power < previous_pm_power:
                negative_slope = True
                
            if negative_slope == True and current_pm_power > previous_pm_power:
                self.powerwheel_dev.write_steps_and_wait(-1*rough_step)
                break
        
        if num_rotation > 16:
            print("Check if powerwheel is connected")
            scan_continue = False
        else:
            scan_continue = True
        

        
        if scan_continue:
            for num_rotation in np.arange(rough_step/fine_step):
                previous_pm_power = current_pm_power
                self.powerwheel_dev.write_steps_and_wait(-1*fine_step)
                current_pm_power = self.collect_pm_power_data()
                if current_pm_power > previous_pm_power:
                    self.powerwheel_dev.write_steps_and_wait(fine_step)
                    self.powerwheel_hw.zero_encoder()
                    break
        print("auto_zero_encoder done!")
            
    
    def collect_pm_power_data(self):
        PM_SAMPLE_NUMBER = 10

        # Sample the power at least one time from the power meter.
        samp_count = 0
        pm_power = 0.0
        for samp in range(0, PM_SAMPLE_NUMBER):
            # Try at least 10 times before ultimately failing
            if self.interrupt_measurement_called: break
            try_count = 0
            #print "samp", ii, samp, try_count, samp_count, pm_power
            while not self.interrupt_measurement_called:
                try:
                    #############Note: Need to Manually Change Which Powermeter to Use Here: Si or Ge
                    pm_power = pm_power + self.app.hardware['thorlabs_powermeter_Si'].power.read_from_hardware(send_signal=True)
                    samp_count = samp_count + 1
                    break 
                except Exception as err:
                    try_count = try_count + 1
                    if try_count > 9:
                        print("failed to collect power meter sample:", err)
                        break
                    time.sleep(0.010)
         
        if samp_count > 0:              
            pm_power = pm_power/samp_count
        else:
            print("  Failed to read power")
            pm_power = 10000.  

        
        return pm_power 
    
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

            self.optimize_history[self.optimize_ii] = pow_reading
            #self.pm_analog_readout_hc.voltage.read_from_hardware()
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
        self.optimize_plot_line.setData(self.optimize_history)
