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


class PowerMeterOptimizerMeasureSetPm(Measurement):

    name = "powermeter_optimizer_Ge_set_pw"
    
    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "powermeter_optimizer_auto_set.ui")
        super(PowerMeterOptimizerMeasureSetPm, self).__init__(app)    

    def setup(self):        
        self.display_update_period = 0.1 #seconds

        # logged quantities
        self.save_data = self.settings.New(name='save_data', dtype=bool, initial=False, ro=False)
        self.settings.New(name='update_period', dtype=float, si=True, initial=0.1, unit='s')
        self.settings.New('powerwheel_type', dtype=str, initial='side', choices=('main', 'side'))
        self.set_power = self.settings.New('set_power', dtype=float, unit='uW', si=False, initial=100.0, ro=False)
        self.set_power_tol_percent = self.settings.New('set_power_tol_percent', dtype=float, initial=0.02, ro=False )
        self.pw_move_steps = self.settings.New('pw_move_steps', dtype=int, initial = 10, ro=False )
        
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
        
        self.ui.power_readout_PGSpinBox = replace_widget_in_layout(self.ui.power_readout_doubleSpinBox,pg.widgets.SpinBox.SpinBox())
        
        self.powermeter.settings.power.connect_bidir_to_widget(self.ui.power_readout_PGSpinBox)
        
        self.powermeter.settings.power.connect_bidir_to_widget(self.ui.power_readout_label)
        
        self.powermeter.settings.wavelength.connect_bidir_to_widget(self.ui.wavelength_doubleSpinBox)
        self.powerwheel_type.connect_to_widget(self.ui.powerwheel_comboBox)
        self.set_power_tol_percent.connect_bidir_to_widget(self.ui.set_power_tol_percent_doubleSpinBox)      
        self.set_power.connect_bidir_to_widget(self.ui.set_power_doubleSpinBox)
        self.pw_move_steps.connect_bidir_to_widget(self.ui.pw_move_steps_doubleSpinBox)
        
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
        
        self.t0 = time.time()
        refresh_time = 0.0
        refresh_time_step = 1.0
        if self.save_data.val:
            self.full_optimize_history = []
            self.full_optimize_history_time = []
            

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
            
            if time.time() - self.t0 > refresh_time + refresh_time_step:
                refresh_time += refresh_time_step
                self.set_pm_power_data_ge(self, self.set_power.val, self.set_power_tol_percent.val, self.pw_move_steps.val, 5.0)

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
    
    def collect_pm_power_data(self):
        PM_SAMPLE_NUMBER = 10

        # Sample the power at least one time from the power meter.
        samp_count = 0
        pm_power_Si = 0.0
        pm_power_Ge = 0.0
        for samp in range(0, PM_SAMPLE_NUMBER):
            # Try at least 10 times before ultimately failing
            if self.interrupt_measurement_called: break
            try_count = 0
            #print "samp", ii, samp, try_count, samp_count, pm_power
            while not self.interrupt_measurement_called:
                try:
                    #############Note: Need to Manually Change Which Powermeter to Use Here: Si or Ge
                    powermeter_Si_hw_name = 'thorlabs_powermeter_Si'
                    powermeter_Ge_hw_name = 'thorlabs_powermeter_Ge'
                    while samp_count < 6:
                        pm_power_Si = pm_power_Si + self.app.hardware[powermeter_Si_hw_name].power.read_from_hardware(send_signal=True)
                        pm_power_Ge = pm_power_Ge + self.app.hardware[powermeter_Ge_hw_name].power.read_from_hardware(send_signal=True)
                        samp_count = samp_count + 1
                    break 
                except Exception as err:
                    try_count = try_count + 1
                    if try_count > 9:
                        print("failed to collect power meter sample:", err)
                        break
                    time.sleep(0.010)
         
        if samp_count > 0:              
            pm_power_Si = pm_power_Si/samp_count
            pm_power_Ge = pm_power_Ge/samp_count
        else:
            print("  Failed to read power")
            pm_power_Si = 10000.  
            pm_power_Ge = 10000.

        return pm_power_Si, pm_power_Ge
    
    def set_pm_power_data_ge(self, set_pm_power, set_error, set_dstep, set_time):
        
        pm_pwr_si, pm_pwr_ge = self.collect_pm_power_data()
        t0 = time.time()
        print("set_pm_power: ", set_pm_power)
        print("current_pm_power: ", pm_pwr_ge)
        pm_power_set = 0.001*set_pm_power
        
        min_bound = (1 - set_error*0.01)*pm_power_set
        max_bound = (1 + set_error*0.01)*pm_power_set
        i = 0
        while pm_pwr_ge > max_bound or pm_pwr_ge < min_bound:
            if pm_pwr_ge > max_bound:
                self.side_power_wheel_dev.write_steps_and_wait(-set_dstep)
                time.sleep(0.5)
                
            elif pm_pwr_ge < min_bound:
                self.side_power_wheel_dev.write_steps_and_wait(set_dstep)
                time.sleep(0.5)
                
            pm_pwr_si, pm_pwr_ge = self.collect_pm_power_data()
            print("power correction: ", i)
            time_now = time.time()
            i += 1
            if time_now - t0 > set_time:
                break
            
        
        return 