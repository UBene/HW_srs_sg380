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

class PowerScanSyncMeasure(Measurement):
    
    name = 'power_scan_sync'
    
    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "power_scan_sync.ui")
        Measurement.__init__(self, app)
        
    def setup(self):
        
        self.power_wheel_Si_min = self.add_logged_quantity("power_wheel_Si_min", 
                                                          dtype=int, unit='', initial=0, vmin=-3200, vmax=+3200, ro=False)
        self.power_wheel_Si_max = self.add_logged_quantity("power_wheel_Si_max", 
                                                          dtype=int, unit='', initial=1000, vmin=-3200, vmax=+3200, ro=False)
        self.power_wheel_Ge_min = self.add_logged_quantity("power_wheel_Ge_min", 
                                                          dtype=int, unit='', initial=0, vmin=-3200, vmax=+3200, ro=False)
        self.power_wheel_Ge_max = self.add_logged_quantity("power_wheel_Ge_max", 
                                                          dtype=int, unit='', initial=1000, vmin=-3200, vmax=+3200, ro=False)
        
        self.power_wheel_ndatapoints = self.add_logged_quantity("power_wheel_ndatapoints", 
                                                          dtype=int, unit='', initial=100, vmin=1, vmax=3200, ro=False)
        
        self.up_and_down_sweep    = self.add_logged_quantity("up_and_down_sweep",dtype=bool, initial=True)
        self.use_shutter    = self.add_logged_quantity("use_shutter",dtype=bool, initial=True)

        self.collect_apd      = self.add_logged_quantity("collect_apd",      dtype=bool, initial=False)
        self.collect_spectrum = self.add_logged_quantity("collect_spectrum", dtype=bool, initial=False)
        self.collect_lifetime = self.add_logged_quantity("collect_lifetime", dtype=bool, initial=False)
        #self.collect_ascom_img = self.add_logged_quantity('collect_ascom_img', dtype=bool, initial=False)
        
        self.settings.New("x_axis", dtype=str, initial='pm_power', choices=('power_wheel', 'pm_power'))
    
        self.powermeter_type = self.settings.New('powermeter_type', dtype=str, initial='Si',
                                                  choices=('Si', 'Ge', 'Sync'))
    
    def setup_figure(self):
        
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)

        self.power_wheel_Si_min.connect_to_widget(self.ui.powerwheel_Si_min_doubleSpinBox)
        self.power_wheel_Si_max.connect_to_widget(self.ui.powerwheel_Si_max_doubleSpinBox)
        self.power_wheel_Ge_min.connect_to_widget(self.ui.powerwheel_Ge_min_doubleSpinBox)
        self.power_wheel_Ge_max.connect_to_widget(self.ui.powerwheel_Ge_max_doubleSpinBox)
        self.power_wheel_ndatapoints.connect_to_widget(self.ui.num_datapoints_doubleSpinBox)
        self.powermeter_type.connect_to_widget(self.ui.powermeter_comboBox)
        
        
        self.use_shutter.connect_bidir_to_widget(self.ui.use_shutter_checkBox)
        self.up_and_down_sweep.connect_bidir_to_widget(self.ui.updown_sweep_checkBox)

        self.collect_apd.connect_to_widget(self.ui.collect_apd_checkBox)
        self.collect_spectrum.connect_to_widget(self.ui.collect_spectrum_checkBox)
        self.collect_lifetime.connect_to_widget(self.ui.collect_hydraharp_checkBox)
        #self.collect_ascom_img.connect_to_widget(self.ui.collect_ascom_img_checkBox)
        
        
        
        # Hardware connections
        if 'apd_counter' in self.app.hardware.keys():
            self.app.hardware.apd_counter.settings.int_time.connect_bidir_to_widget(
                                                                    self.ui.apd_int_time_doubleSpinBox)
        else:
            self.collect_apd.update_value(False)
            self.collect_apd.change_readonly(True)
        
        if 'lightfield' in self.app.hardware.keys():
            self.app.hardware['lightfield'].settings.exposure_time.connect_bidir_to_widget(
                                                                    self.ui.spectrum_int_time_doubleSpinBox)
        else:
            self.collect_spectrum.update_value(False)
            self.collect_spectrum.change_readonly(True)

        #if 'ascom_camera' in self.app.hardware.keys():
        #    self.app.hardware.ascom_camera.settings.exp_time.connect_bidir_to_widget(
        #        self.ui.ascom_img_int_time_doubleSpinBox)
        #else:
        #    self.collect_ascom_img.update_value(False)
        #    self.collect_ascom_img.change_readonly(True)
            
        if 'hydraharp' in self.app.hardware.keys():
            self.app.hardware['hydraharp'].settings.Tacq.connect_to_widget(
                self.ui.hydraharp_tacq_doubleSpinBox)
        else:
            self.collect_lifetime.update_value(False)
            self.collect_lifetime.change_readonly(True)
            
            
        # Plot
        if hasattr(self, 'graph_layout'):
            self.graph_layout.deleteLater() # see http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            del self.graph_layout
        self.graph_layout=pg.GraphicsLayoutWidget()
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)
        
        self.plot1 = self.graph_layout.addPlot(title="Power Scan_Si")

        self.plot_line1 = self.plot1.plot([0])
        
        self.graph_layout.nextRow()
        
        self.plot2 = self.graph_layout.addPlot(title="Power Scan_Ge")

        self.plot_line2 = self.plot2.plot([0])

    def update_display(self):
        
        ii = self.ii
        if self.settings['x_axis'] == 'power_wheel':
            X1 = self.power_wheel_Si_position[:ii]
            X2 = self.power_wheel_Ge_position[:ii]  
        else:
            X1 = self.pm_powers_Si[:ii]
            X2 = self.pm_powers_Ge[:ii] 
     
        if self.settings['collect_apd']:
            self.plot_line1.setData(X1, self.apd_count_rates[:ii])
            self.plot_line2.setData(X2, self.apd_count_rates[:ii])
        elif self.settings['collect_lifetime']:
            self.plot_line1.setData(X1, self.hydraharp_histograms[:ii, :].sum(axis=1)/self.hydraharp_elapsed_time[:ii])
            self.plot_line2.setData(X2, self.hydraharp_histograms[:ii, :].sum(axis=1)/self.hydraharp_elapsed_time[:ii])
        elif self.settings['collect_spectrum']:
            if self.powermeter_type.val == "Si":
                self.plot_line1.setData(X1, self.integrated_spectra[:ii])
                self.plot_line2.setData(X1, X2)
            elif self.powermeter_type.val == "Ge":
                self.plot_line1.setData(X2, self.integrated_spectra[:ii])
                self.plot_line2.setData(X2, X1)
            elif self.powermeter_type.val == "Sync":
                self.plot_line1.setData(X1, self.integrated_spectra[:ii])
                self.plot_line2.setData(X2, self.integrated_spectra[:ii])
            self.lightfield_readout.update_display()
        #elif self.settings['collect_ascom_img']:
        #    self.plot_line1.setData(X, self.ascom_img_integrated[:ii_sync])
        #    self.ascom_camera_capture.update_display()
        else: # no detectors set, show pm_powers
            self.plot_line1.setData(X1, self.pm_powers_Si[:ii])
            self.plot_line2.setData(X2, self.pm_powers_Si[:ii])

    def run(self):
       
        # hardware and delegate measurements
        self.power_wheel_Si_hw = self.app.hardware.Side_beam_power_wheel
        self.power_wheel_Si_dev = self.power_wheel_Si_hw.power_wheel_dev
        self.power_wheel_Ge_hw = self.app.hardware.Main_beam_power_wheel
        self.power_wheel_Ge_dev = self.power_wheel_Ge_hw.power_wheel_dev
        
        if self.settings['collect_apd']:
            self.apd_counter_hw = self.app.hardware.apd_counter
            self.apd_count_rate_lq = self.apd_counter_hw.settings.apd_count_rate     

        if self.settings['collect_lifetime']:
            self.ph_hw = self.app.hardware['hydraharp']

        if self.settings['collect_spectrum']:
            self.lightfield_readout = self.app.measurements['lightfield_readout']
                   
        #if self.settings['collect_ascom_img']:
            #self.ascom_camera_capture = self.app.measurements.ascom_camera_capture
            #self.ascom_camera_capture.settings['continuous'] = False
        
        #####
        self.Np = Np = self.power_wheel_ndatapoints.val
        self.step_size_Si = int( (self.power_wheel_Si_max.val-self.power_wheel_Si_min.val)/Np )
        self.step_size_Ge = int( (self.power_wheel_Ge_max.val-self.power_wheel_Ge_min.val)/Np )
    
        if self.settings['up_and_down_sweep']:
            self.direction = np.ones(Np*2) # step up
            self.direction[Np] = 0 # don't step at the top!
            self.direction[Np+1:] = -1 # step down
            Np = self.Np = 2*Np
        else:
            self.direction = np.ones(Np)
    
        # Create Data Arrays    
        self.power_wheel_Si_position = [] 
        self.power_wheel_Ge_position = []    
        
        self.pm_powers_Si = []
        self.pm_powers_Si_after = []
        self.pm_powers_Ge = []
        self.pm_powers_Ge_after = []

        if self.settings['collect_apd']:
            self.apd_count_rates = []
        if self.settings['collect_lifetime']:
            Nt = self.num_hist_chans = self.ph_hw.calc_num_hist_chans()
            self.hydraharp_time_array = np.zeros(Nt, dtype=float)
            self.hydraharp_elapsed_time = np.zeros(Np, dtype=float)
            self.hydraharp_histograms = np.zeros((Np,Nt ), dtype=int)
        if self.settings['collect_spectrum']:
            self.spectra = [] # don't know size of ccd until after measurement
            self.integrated_spectra = []
        #if self.settings['collect_ascom_img']:
        #    self.ascom_img_stack = []
        #    self.ascom_img_integrated = []
            
        ### Acquire data
        getattr(self, "move_to_min_pos_%s" % self.powermeter_type.val)()

        self.ii = 0
        
        # loop through power wheel positions
        for ii in range(self.Np):
            self.ii = ii
            self.settings['progress'] = 100.*ii/self.Np
            
            if self.interrupt_measurement_called:
                break
            
            #if self.powermeter_type.val == "Si":
            #    # record power wheel position
            #    self.power_wheel_Si_position.append(self.power_wheel_Si_hw.encoder_pos.read_from_hardware())
                # collect power meter value
            #    self.pm_powers_Si[ii].append(self.collect_pm_power_data_Si())
            #elif self.powermeter_type.val == "Ge":    
                # record power wheel position
            #    self.power_wheel_Ge_position.append(self.power_wheel_Ge_hw.encoder_pos.read_from_hardware())
                # collect power meter value
            #    self.pm_powers_Ge.append(self.collect_pm_power_data_Ge())
            #elif self.powermeter_type.val == "Sync": 
                # record power wheel position
            #    self.power_wheel_Si_position.append(self.power_wheel_Si_hw.encoder_pos.read_from_hardware())
            #    self.power_wheel_Ge_position.append(self.power_wheel_Ge_hw.encoder_pos.read_from_hardware())
                # collect power meter value
            #    self.pm_powers_Si_val, self.pm_powers_Ge_val=getattr(self, "collect_pm_power_data_%s" % self.powermeter_type.val)()
            #    self.pm_powers_Ge.append(self.pm_powers_Ge_val)
            #    self.pm_powers_Si.append(self.pm_powers_Si_val)
            
            # record power wheel position
            self.power_wheel_Si_position.append(self.power_wheel_Si_hw.encoder_pos.read_from_hardware())
            self.power_wheel_Ge_position.append(self.power_wheel_Ge_hw.encoder_pos.read_from_hardware())
                # collect power meter value
            self.pm_powers_Si_val, self.pm_powers_Ge_val=self.collect_pm_power_data_Sync()
            self.pm_powers_Ge.append(self.pm_powers_Ge_val)
            self.pm_powers_Si.append(self.pm_powers_Si_val)
            # read detectors
            if self.settings['collect_apd']:
                #self.apd_count_rates[ii] = \
                #    self.apd_counter_hw.settings.apd_count_rate.read_from_hardware()
                self.apd_count_rates.append(self.apd_counter_hw.settings.apd_count_rate.read_from_hardware())
            if self.settings['collect_lifetime']:
                hh = self.hh_hw.hydraharp
                hh.start_histogram()
                while not hh.check_done_scanning():
                    if self.interrupt_measurement_called:
                        break
                    hh.read_histogram_data()
                    self.hh_hw.settings.count_rate0.read_from_hardware()
                    self.hh_hw.settings.count_rate1.read_from_hardware()
                    time.sleep(0.1)        
                hh.stop_histogram()
                hh.read_histogram_data()
                self.hydraharp_histograms[ii,:] = hh.histogram_data[0:Nt]
                self.hydraharp_time_array =  hh.time_array[0:Nt]
                self.hydraharp_elapsed_time[ii] = hh.read_elapsed_meas_time()
            if self.settings['collect_spectrum']:
                self.lightfield_readout.ro_acquire_data()
                spec = np.array(self.lightfield_readout.img)
                self.spectra.append( spec )
                self.integrated_spectra.append(spec.sum())
            #if self.settings['collect_ascom_img']:
            #    self.ascom_camera_capture.interrupt_measurement_called = False
            #    self.ascom_camera_capture.run()
            #    img = self.ascom_camera_capture.img.copy()
            #    self.ascom_img_stack.append(img)
            #    self.ascom_img_integrated.append(img.astype(float).sum())
                
                
            # collect power meter value after measurement
            
#            if self.powermeter_type.val == "Si":
#                
#                self.pm_powers_Si_after[ii]=getattr(self, "collect_pm_power_data_%s" % self.powermeter_type.val)()
#                
#                self.power_wheel_Si_dev.write_steps_and_wait(self.step_size_Si*self.direction[ii])
#                time.sleep(0.5)
#                self.power_wheel_Si_hw.encoder_pos.read_from_hardware()
#
#                
#            elif self.powermeter_type.val == "Ge":    
#                
#                self.pm_powers_Ge_after[ii]=getattr(self, "collect_pm_power_data_%s" % self.powermeter_type.val)()
#                
#                self.power_wheel_Ge_dev.write_steps_and_wait(self.step_size_Ge*self.direction[ii])
#                time.sleep(0.5)
#                self.power_wheel_Ge_hw.encoder_pos.read_from_hardware()
#
#                
#            elif self.powermeter_type.val == "Sync": 
#                
#                self.pm_powers_Si_after[ii], self.pm_powers_Ge_after[ii]=getattr(self, "collect_pm_power_data_%s" % self.powermeter_type.val)()
#                
#                self.power_wheel_Si_dev.write_steps_and_wait(self.step_size_Si*self.direction[ii])
#                time.sleep(0.5)
#                self.power_wheel_Si_hw.encoder_pos.read_from_hardware()
#                
#                self.power_wheel_Ge_dev.write_steps_and_wait(self.step_size_Ge*self.direction[ii])
#                time.sleep(0.5)
#                self.power_wheel_Ge_hw.encoder_pos.read_from_hardware()
            
            #self.pm_powers_Si_after[ii], self.pm_powers_Ge_after[ii]=getattr(self, "collect_pm_power_data_%s" % self.powermeter_type.val)()
            self.pm_powers_Si_after_val, self.pm_powers_Ge_after_val=self.collect_pm_power_data_Sync()
            self.pm_powers_Ge_after.append(self.pm_powers_Ge_val)
            self.pm_powers_Si_after.append(self.pm_powers_Si_val)  
                      
            self.power_wheel_Si_dev.write_steps_and_wait(self.step_size_Si*self.direction[ii])
            time.sleep(0.5)
            self.power_wheel_Si_hw.encoder_pos.read_from_hardware()
            
            self.power_wheel_Ge_dev.write_steps_and_wait(self.step_size_Ge*self.direction[ii])
            time.sleep(0.5)
            self.power_wheel_Ge_hw.encoder_pos.read_from_hardware()
            # move to new power wheel position


        # write data to h5 file on disk
        
        self.t0 = time.time()
        #self.fname = "%i_%s.h5" % (self.t0, self.name)
        #self.h5_file = h5_io.h5_base_file(self.app, self.fname )
        self.h5_file = h5_io.h5_base_file(app=self.app,measurement=self)
        try:
            self.h5_file.attrs['time_id'] = self.t0
            H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
        
            #create h5 data arrays
            H['powermeter_type'] = self.powermeter_type.val
            if self.settings['collect_apd']:
                H['apd_count_rates'] = self.apd_count_rates
            if self.settings['collect_lifetime']:
                H['hydraharp_elapsed_time'] = self.hydraharp_elapsed_time
                H['hydraharp_histograms'] = self.hydraharp_histograms
                H['hydraharp_time_array'] = self.hydraharp_time_array
            if self.settings['collect_spectrum']:
                H['wls'] = self.winspec_readout.wls
                H['spectra'] = np.squeeze(np.array(self.spectra))
                H['integrated_spectra'] = np.array(self.integrated_spectra)
            #if self.settings['collect_ascom_img']:
            #    H['ascom_img_stack'] = np.array(self.ascom_img_stack)
            #    H['ascom_img_integrated'] = np.array(self.ascom_img_integrated)
            
            H['pm_powers_Si'] = self.pm_powers_Si
            H['pm_powers_Si_after'] = self.pm_powers_Si_after
            H['power_wheel_Si_position'] = self.power_wheel_Si_position
            H['pm_powers_Ge'] = self.pm_powers_Ge
            H['pm_powers_Ge_after'] = self.pm_powers_Ge_after
            H['power_wheel_Ge_position'] = self.power_wheel_Ge_position
            #H['Power Ratio'] = self.pm_powers_Ge/self.pm_powers_Si
            
            H['direction'] = self.direction
        finally:
            self.log.info("data saved "+self.h5_file.filename)
            self.h5_file.close()
        


    def move_to_min_pos_Si(self):
        self.power_wheel_Si_dev.read_status()
        
        delta_steps_Si = self.power_wheel_Si_min.val - self.power_wheel_Si_hw.encoder_pos.read_from_hardware()
        if delta_steps_Si != 0:
            #print 'moving to min pos'
            self.power_wheel_Si_dev.write_steps_and_wait(delta_steps_Si)
            #print 'done moving to min pos'
            
    def move_to_min_pos_Ge(self):        
        self.power_wheel_Ge_dev.read_status()
        
        delta_steps_Ge = self.power_wheel_Ge_min.val - self.power_wheel_Ge_hw.encoder_pos.read_from_hardware()
        if delta_steps_Ge != 0:
            #print 'moving to min pos'
            self.power_wheel_Ge_dev.write_steps_and_wait(delta_steps_Ge)
            #print 'done moving to min pos'
    
    def move_to_min_pos_Sync(self):
        self.power_wheel_Si_dev.read_status()
        self.power_wheel_Ge_dev.read_status()

        delta_steps_Si = self.power_wheel_Si_min.val - self.power_wheel_Si_hw.encoder_pos.read_from_hardware()
        if delta_steps_Si != 0:
            #print 'moving to min pos'
            self.power_wheel_Si_dev.write_steps_and_wait(delta_steps_Si)
            #print 'done moving to min pos'
        self.power_wheel_Ge_dev.read_status()
        
        delta_steps_Ge = self.power_wheel_Ge_min.val - self.power_wheel_Ge_hw.encoder_pos.read_from_hardware()
        if delta_steps_Ge != 0:
            #print 'moving to min pos'
            self.power_wheel_Ge_dev.write_steps_and_wait(delta_steps_Ge)
            #print 'done moving to min pos'
    
    def collect_pm_power_data_Si(self):
        PM_SAMPLE_NUMBER = 10

        # Sample the power at least one time from the power meter.
        samp_count = 0
        pm_power_Si = 0.0

        for samp in range(0, PM_SAMPLE_NUMBER):
            # Try at least 10 times before ultimately failing
            if self.interrupt_measurement_called: break
            try_count = 0
            #print "samp", ii_sync, samp, try_count, samp_count, pm_power
            while not self.interrupt_measurement_called:
                try:
                    pm_power_Si = pm_power_Si + self.app.hardware['thorlabs_powermeter_Si'].power.read_from_hardware(send_signal=True)
                    
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
           
        else:
            print("  Failed to read power")
            pm_power_Si = 10000.  

        
        return pm_power_Si
    
    def collect_pm_power_data_Ge(self):
        PM_SAMPLE_NUMBER = 10

        # Sample the power at least one time from the power meter.
        samp_count = 0
        pm_power_Ge = 0.0

        for samp in range(0, PM_SAMPLE_NUMBER):
            # Try at least 10 times before ultimately failing
            if self.interrupt_measurement_called: break
            try_count = 0
            #print "samp", ii_sync, samp, try_count, samp_count, pm_power
            while not self.interrupt_measurement_called:
                try:
                    pm_power_Ge = pm_power_Ge + self.app.hardware['thorlabs_powermeter_Ge'].power.read_from_hardware(send_signal=True)
                    
                    samp_count = samp_count + 1
                    break 
                except Exception as err:
                    try_count = try_count + 1
                    if try_count > 9:
                        print("failed to collect power meter sample:", err)
                        break
                    time.sleep(0.010)
         
        if samp_count > 0:              
            pm_power_Ge = pm_power_Ge/samp_count
           
        else:
            print("  Failed to read power")
            pm_power_Ge = 10000.  

        
        return pm_power_Ge
    
    def collect_pm_power_data_Sync(self):
        PM_SAMPLE_NUMBER = 10

        # Sample the power at least one time from the power meter.
        samp_count = 0
        pm_power_Si = 0.0
        pm_power_Ge = 0.0
        for samp in range(0, PM_SAMPLE_NUMBER):
            # Try at least 10 times before ultimately failing
            if self.interrupt_measurement_called: break
            try_count = 0
            #print "samp", ii_sync, samp, try_count, samp_count, pm_power
            while not self.interrupt_measurement_called:
                try:
                    pm_power_Si = pm_power_Si + self.app.hardware['thorlabs_powermeter_Si'].power.read_from_hardware(send_signal=True)
                    pm_power_Ge = pm_power_Ge + self.app.hardware['thorlabs_powermeter_Ge'].power.read_from_hardware(send_signal=True)
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
            pm_power_Ge = 10000.  
            pm_power_Si = 10000. 
        
        return pm_power_Si, pm_power_Ge