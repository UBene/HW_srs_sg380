'''
Created on Jun 19, 2014

@author: Edward Barnard
'''
from ScopeFoundry import Measurement
import numpy as np
import time
from ScopeFoundry import h5_io
from ScopeFoundry.helper_funcs import sibling_path
import pyqtgraph as pg

#################################################
#### A few things to do on this code:
######### (1) Select which power meter to use. Now this is manually changed in code. Need to change it.
######### (2) Add x-axis selection into the ui
######### (3) Use shutter is not really used. Need to change it.


class PowerTrace_OnOff(Measurement):
    
    name = 'time_trace_on_off'
    
    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "power_trace_on_off_pmpower.ui")
        Measurement.__init__(self, app)
        
    def setup(self):

        self.side_power_wheel_min = self.add_logged_quantity("side_power_wheel_min", 
                                                          dtype=int, unit='', initial=0, vmin=-3200, vmax=+3200, ro=False)
        self.side_power_wheel_max = self.add_logged_quantity("side_power_wheel_max", 
                                                          dtype=int, unit='', initial=1000, vmin=-3200, vmax=+3200, ro=False)
        self.set_pm_power_min = self.add_logged_quantity("set_pm_power_min", 
                                                          dtype=float, unit='', si=True, initial=0.001, vmin=-1, vmax=5, ro=False)
        self.set_pm_power_max = self.add_logged_quantity("set_pm_power_max", 
                                                          dtype=float, unit='', si=True, initial=0.001, vmin=-1, vmax=5, ro=False)
        self.set_error = self.add_logged_quantity("set_error", 
                                                          dtype=float, unit='%', initial=5, vmin=0.0, vmax=100.0, ro=False)
        self.set_dstep = self.add_logged_quantity("step_size", 
                                                          dtype=int, unit='', initial=5, vmin=0.0, vmax=100.0, ro=False)
        self.set_time = self.add_logged_quantity("set_time", 
                                                          dtype=float, unit='sec', initial=10, vmin=0.0, vmax=100.0, ro=False)
        self.num_cycle = self.add_logged_quantity("num_cycle", 
                                                          dtype=int, unit='', initial=10, vmin=1, vmax=10000, ro=False)
        self.num_point = self.add_logged_quantity("num_pooint", 
                                                          dtype=int, unit='', initial=5, vmin=1, vmax=10000, ro=False)
        self.time_turn_on = self.add_logged_quantity("time_turn_on", 
                                                          dtype=float, unit='sec', initial=2.0, vmin=0.0, vmax=30.0, ro=False)
        self.time_turn_off = self.add_logged_quantity("time_turn_off", 
                                                          dtype=float, unit='sec', initial=2.0, vmin=0.0, vmax=30.0, ro=False)
        

        self.collect_apd      = self.add_logged_quantity("collect_apd",      dtype=bool, initial=True)


        self.settings.New("x_axis", dtype=str, initial='index', choices=('index', 'time'))
    
        #self.powermeter_type = self.settings.New('powermeter_type', dtype=str, initial='Si',
        #                                          choices=('Si', 'Ge', 'Synchronized'))
    
    def setup_figure(self):
        
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)

        self.side_power_wheel_min.connect_to_widget(self.ui.side_powerwheel_min_doubleSpinBox)
        self.side_power_wheel_max.connect_to_widget(self.ui.side_powerwheel_max_doubleSpinBox)
        
        self.set_pm_power_min.connect_to_widget(self.ui.doubleSpinBox_power_min)
        self.set_pm_power_max.connect_to_widget(self.ui.doubleSpinBox_power_max)
        self.set_error.connect_to_widget(self.ui.doubleSpinBox_set_error)
        self.set_dstep.connect_to_widget(self.ui.doubleSpinBox_set_step_size)
        self.set_time.connect_to_widget(self.ui.doubleSpinBox_set_time)
        
        
        self.num_cycle.connect_to_widget(self.ui.num_cycle_doubleSpinBox)
        self.num_point.connect_to_widget(self.ui.num_point_doubleSpinBox)
        self.time_turn_on.connect_to_widget(self.ui.time_turn_on_doubleSpinBox)
        self.time_turn_off.connect_to_widget(self.ui.time_turn_off_doubleSpinBox)


        self.collect_apd.connect_to_widget(self.ui.collect_apd_checkBox)

        
        # Hardware connections

        self.app.hardware.apd_counter.settings.int_time.connect_bidir_to_widget(self.ui.apd_int_time_doubleSpinBox)

        
        # Plot
        if hasattr(self, 'graph_layout'):
            self.graph_layout.deleteLater() # see http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            del self.graph_layout
        self.graph_layout=pg.GraphicsLayoutWidget()
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)
        
        self.plot1 = self.graph_layout.addPlot(title="Signal Trace")

        self.plot_line1 = self.plot1.plot([0])

    def update_display(self):
        if hasattr(self, "ii"):
            ii = self.index_i
        else:
            ii = 0    
            
        if self.settings['x_axis'] == 'index':
            if hasattr(self, 'index_array'):
                X = self.index_array[:ii]
        else:
            if hasattr(self, 'time'):
                X = self.time_array[:ii]
        
        self.plot_line1.setData(X, self.apd_count_rates[:ii])
  


    def run(self):
        
        ####Temporary
        self.settings['x_axis'] = 'index'
        
        
        ##############################

        print ('Now closing shutter...')
        self.app.hardware.dual_position_slider.move_fwd()
        self.app.hardware.dual_position_slider_2.move_fwd()
            
            
        # hardware and delegate measurements

        self.main_power_wheel_hw = self.app.hardware.main_beam_power_wheel
        self.side_power_wheel_hw = self.app.hardware.side_beam_power_wheel
        
        self.main_power_wheel_dev = self.main_power_wheel_hw.power_wheel_dev
        self.side_power_wheel_dev = self.side_power_wheel_hw.power_wheel_dev        


        self.apd_counter_hw = self.app.hardware.apd_counter
        self.apd_count_rate_lq = self.apd_counter_hw.settings.apd_count_rate     


            
        
        #####
        self.Np = self.num_cycle.val
        self.step_size = int( (self.side_power_wheel_max.val-self.side_power_wheel_min.val) )
        
        self.index_array = []
        self.index_turn_on_array = []
        self.time_array = []
        self.pm_powers_Si = []
        self.pm_powers_Ge = []
        self.apd_count_rates = []
        

        
        #self.move_to_min_pos()
        current_side_power_wheel_pos = self.side_power_wheel_hw.encoder_pos.read_from_hardware()
        self.side_power_wheel_dev.write_steps_and_wait(self.side_power_wheel_min.val - current_side_power_wheel_pos)
        #time.sleep(2.0)
        self.set_pm_power_data_ge(self.set_pm_power_min.val, self.set_error.val, self.set_dstep.val, self.set_time.val)
        self.side_power_wheel_pos_min = self.side_power_wheel_hw.encoder_pos.read_from_hardware()
        self.side_power_wheel_pos_max = self.side_power_wheel_max.val
        self.ii = 0
        
        # loop through power wheel positions
        t0 = time.time()
        self.index_i = 0
        for ii in range(self.Np):
            self.ii = ii
            self.settings['progress'] = 100.*ii/self.Np
            
            if self.interrupt_measurement_called:
                break
            
            # record power wheel position
            #self.power_wheel_position[ii] = self.power_wheel_hw.encoder_pos.read_from_hardware()
            

            # collect power meter value
            #self.pm_powers[ii]=self.collect_pm_power_data()

            
            

            
            print ('Now opening main shutter...')
            self.app.hardware.dual_position_slider.move_bkwd()
            
            
             
            # Measuring signals from single
            for i in np.arange(self.num_point.val):
                time_i = time.time() - t0
                self.index_array.append(self.index_i)
                self.time_array.append(time_i)
                self.apd_count_rates.append(self.apd_counter_hw.settings.apd_count_rate.read_from_hardware())
                pm_power_Si_i, pm_power_Ge_i = self.collect_pm_power_data()
                self.pm_powers_Si.append(pm_power_Si_i)
                self.pm_powers_Ge.append(pm_power_Ge_i)
                self.index_i += 1
            
            print ('Now closing main shutter...')
            self.app.hardware.dual_position_slider.move_fwd()
            # Measuring signals after 1064nm power rise
            self.side_power_wheel_dev.write_steps_and_wait(self.side_power_wheel_pos_max - self.side_power_wheel_pos_min)
            #time.sleep(2.0)
            self.set_pm_power_data_ge(self.set_pm_power_max.val, self.set_error.val, self.set_dstep.val, self.set_time.val)
            self.side_power_wheel_pos_max = self.side_power_wheel_hw.encoder_pos.read_from_hardware()
            
            print ('Now opening main shutter...')
            self.app.hardware.dual_position_slider.move_bkwd()
            
            print("time to turn off", self.time_turn_off.val)
            time.sleep(self.time_turn_off.val)
#             for i in np.arange(self.num_point.val):
#                 time_i = time.time() - t0
#                 self.index_array.append(self.index_i)
#                 self.time_array.append(time_i)
#                 self.apd_count_rates.append(self.apd_counter_hw.settings.apd_count_rate.read_from_hardware())
#                 pm_power_Si_i, pm_power_Ge_i = self.collect_pm_power_data()
#                 self.pm_powers_Si.append(pm_power_Si_i)
#                 self.pm_powers_Ge.append(pm_power_Ge_i)
#                 self.index_i += 1
            
            # Measuring signals after 1064nm power decrease
            #self.side_power_wheel_dev.write_steps_and_wait(-self.step_size)
            self.side_power_wheel_dev.write_steps_and_wait(self.side_power_wheel_pos_min - self.side_power_wheel_pos_max)
            #time.sleep(2.0)
            self.set_pm_power_data_ge(self.set_pm_power_min.val, self.set_error.val, self.set_dstep.val, self.set_time.val)
            self.side_power_wheel_pos_min = self.side_power_wheel_hw.encoder_pos.read_from_hardware()
            
            for i in np.arange(self.num_point.val):
                time_i = time.time() - t0
                self.index_array.append(self.index_i)
                self.time_array.append(time_i)
                self.apd_count_rates.append(self.apd_counter_hw.settings.apd_count_rate.read_from_hardware())
                pm_power_Si_i, pm_power_Ge_i = self.collect_pm_power_data()
                self.pm_powers_Si.append(pm_power_Si_i)
                self.pm_powers_Ge.append(pm_power_Ge_i) 
                self.index_i += 1   
            
            # Turnning on
            print ('Now closing main shutter and opening side shutter...')
            self.app.hardware.dual_position_slider.move_fwd()
            self.app.hardware.dual_position_slider_2.move_bkwd()
            self.index_turn_on_array.append(self.index_i)
            
            print("time to turn on", self.time_turn_on.val)
            time.sleep(self.time_turn_on.val)
            
            self.app.hardware.dual_position_slider_2.move_fwd()
            time.sleep(4.0)
            
    

        # write data to h5 file on disk
        
        self.t0 = time.time()
        #self.fname = "%i_%s.h5" % (self.t0, self.name)
        #self.h5_file = h5_io.h5_base_file(self.app, self.fname )
        self.h5_file = h5_io.h5_base_file(app=self.app,measurement=self)
        try:
            self.h5_file.attrs['time_id'] = self.t0
            H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
        
            #create h5 data arrays
    
            H['apd_count_rates'] = np.array(self.apd_count_rates)

            H['pm_powers_Si'] = np.array(self.pm_powers_Si)
            H['pm_powers_Ge'] = np.array(self.pm_powers_Ge)

            H['index_array'] = np.array(self.index_array)
            H['index_turn_on_array'] = np.array(self.index_turn_on_array)
            H['time_array'] = np.array(self.time_array)
            
        finally:
            self.log.info("data saved "+self.h5_file.filename)
            self.h5_file.close()
        


    def move_to_min_pos(self):
        self.side_power_wheel_dev.read_status()
        
        delta_steps = self.side_power_wheel_min.val - self.side_power_wheel_hw.encoder_pos.read_from_hardware()
        if delta_steps != 0:
            #print 'moving to min pos'
            self.side_power_wheel_dev.write_steps_and_wait(delta_steps)
            #print 'done moving to min pos'

    
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