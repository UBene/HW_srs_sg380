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


class PowerScanMeasure_2pm(Measurement):
    
    name = 'power_scan_for_2pm'
    
    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "power_scan_for_Ge_Si_2.ui")
        Measurement.__init__(self, app)
        
    def setup(self):
        
        self.power_wheel_min = self.add_logged_quantity("power_wheel_min", 
                                                          dtype=int, unit='', initial=0, vmin=-3200, vmax=+3200, ro=False)
        self.power_wheel_max = self.add_logged_quantity("power_wheel_max", 
                                                          dtype=int, unit='', initial=1000, vmin=-3200, vmax=+3200, ro=False)
        self.power_wheel_ndatapoints = self.add_logged_quantity("power_wheel_ndatapoints", 
                                                          dtype=int, unit='', initial=100, vmin=1, vmax=3200, ro=False)
        
        self.up_and_down_sweep    = self.add_logged_quantity("up_and_down_sweep",dtype=bool, initial=True)

        self.use_shutter    = self.add_logged_quantity("use_shutter",dtype=bool, initial=True)

        self.collect_apd      = self.add_logged_quantity("collect_apd",      dtype=bool, initial=False)
        self.collect_spectrum = self.add_logged_quantity("collect_spectrum", dtype=bool, initial=True)
        self.collect_lifetime = self.add_logged_quantity("collect_lifetime", dtype=bool, initial=False)
        #self.collect_ascom_img = self.add_logged_quantity('collect_ascom_img', dtype=bool, initial=False)
        
        self.powermeter_type = self.settings.New('powermeter_type', dtype=str, initial='Si',
                                                  choices=('Si', 'Ge'))
        self.powerwheel_type = self.settings.New('powerwheel_type', dtype=str, initial='main',
                                                  choices=('main', 'side'))
        self.settings.New("x_axis", dtype=str, initial='pm_power', choices=('power_wheel', 'pm_power'))
    
        #self.powermeter_type = self.settings.New('powermeter_type', dtype=str, initial='Si',
        #                                          choices=('Si', 'Ge', 'Synchronized'))
    
    def setup_figure(self):
        
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)

        self.power_wheel_min.connect_to_widget(self.ui.powerwheel_min_doubleSpinBox)
        self.power_wheel_max.connect_to_widget(self.ui.powerwheel_max_doubleSpinBox)
        self.power_wheel_ndatapoints.connect_to_widget(self.ui.num_datapoints_doubleSpinBox)

        self.use_shutter.connect_bidir_to_widget(self.ui.use_shutter_checkBox)
        self.up_and_down_sweep.connect_bidir_to_widget(self.ui.updown_sweep_checkBox)

        self.collect_apd.connect_to_widget(self.ui.collect_apd_checkBox)
        self.collect_spectrum.connect_to_widget(self.ui.collect_spectrum_checkBox)
        self.collect_lifetime.connect_to_widget(self.ui.collect_hydraharp_checkBox)
        self.powerwheel_type.connect_to_widget(self.ui.powerwheel_comboBox)
        self.powermeter_type.connect_to_widget(self.ui.powermeter_comboBox)
        
        
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
        
        self.plot1 = self.graph_layout.addPlot(title="Power Scan")

        self.plot_line1 = self.plot1.plot([0])

    def update_display(self):
        if hasattr(self, "ii"):
            ii = self.ii
        else:
            ii = 0    
            
        if self.settings['x_axis'] == 'power_wheel':
            if hasattr(self, 'power_wheel_position'):
                X = self.power_wheel_position[:ii]
        else:
            if hasattr(self, 'pm_powers'):
                X = self.pm_powers[:ii]
        
        if self.settings['collect_apd']:
            self.plot_line1.setData(X, self.apd_count_rates[:ii])
        elif self.settings['collect_lifetime']:
            self.plot_line1.setData(X, self.hydraharp_histograms[:ii, :].sum(axis=1)/self.hydraharp_elapsed_time[:ii])
        elif self.settings['collect_spectrum']:
            if hasattr(self, 'integrated_spectra'):
                self.plot_line1.setData(X, self.integrated_spectra[:ii])
            self.lightfield_readout.update_display()
        #elif self.settings['collect_ascom_img']:
        #    self.plot_line1.setData(X, self.ascom_img_integrated[:ii])
        #    self.ascom_camera_capture.update_display()
        else: # no detectors set, show pm_powers
            self.plot_line1.setData(X, self.pm_powers[:ii])


    def run(self):
        
        ####Temporary
        self.settings['x_axis'] = 'pm_powers'
        
        
        ##############################
        if self.use_shutter.val == True:
            print ('Now closing shutter...')
            self.app.hardware.dual_position_slider.move_fwd()
            
            
        # hardware and delegate measurements
        if self.powerwheel_type.val == "main":
            self.power_wheel_hw = self.app.hardware.main_beam_power_wheel
        elif self.powerwheel_type.val == "side":
            self.power_wheel_hw = self.app.hardware.side_beam_power_wheel
        self.power_wheel_dev = self.power_wheel_hw.power_wheel_dev
        
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
        self.step_size = int( (self.power_wheel_max.val-self.power_wheel_min.val)/(Np) )
        
    
        if self.settings['up_and_down_sweep']:
            self.direction = np.ones(Np*2+2) # step up
            self.direction[Np] = 0 # don't step at the top!
            self.direction[Np+1:] = -1 # step down
            Np = self.Np = 2*Np+2
        else:
            self.direction = np.ones(Np)
    
        # Create Data Arrays    
#        self.power_wheel_position = np.zeros(Np)      
        
#        self.pm_powers = np.zeros(Np, dtype=float)
#        self.pm_powers_after = np.zeros(Np, dtype=float)

        self.power_wheel_position = []
        self.pm_powers = []
        self.pm_powers_after = []

        if self.settings['collect_apd']:
            #self.apd_count_rates = np.zeros(Np, dtype=float)
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
        
        self.move_to_min_pos()
        
        self.ii = 0
        
        # loop through power wheel positions
        for ii in range(self.Np):
            self.ii = ii
            self.settings['progress'] = 100.*ii/self.Np
            
            if self.interrupt_measurement_called:
                break
            
            # record power wheel position
            #self.power_wheel_position[ii] = self.power_wheel_hw.encoder_pos.read_from_hardware()
            self.power_wheel_position.append(self.power_wheel_hw.encoder_pos.read_from_hardware())
            # collect power meter value
            #self.pm_powers[ii]=self.collect_pm_power_data()
            time.sleep(1.0) 
            self.pm_powers.append(self.collect_pm_power_data())
            
            
            #########Open shutter
            if self.use_shutter.val == True:
                print ('Now opening shutter...')
                self.app.hardware.dual_position_slider.move_bkwd()
            
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
            
            
            #########Closing shutter
            
                
                
            # collect power meter value after measurement
            #self.pm_powers_after[ii]=self.collect_pm_power_data()
            self.pm_powers_after.append(self.collect_pm_power_data())
            
            # move to new power wheel position
            self.power_wheel_dev.write_steps_and_wait(self.step_size*self.direction[ii])
            time.sleep(0.5)
            self.power_wheel_hw.encoder_pos.read_from_hardware()
            
            if self.use_shutter.val == True:
                print ('Now closing shutter...')
                self.app.hardware.dual_position_slider.move_fwd()

        # write data to h5 file on disk
        
        self.t0 = time.time()
        #self.fname = "%i_%s.h5" % (self.t0, self.name)
        #self.h5_file = h5_io.h5_base_file(self.app, self.fname )
        self.h5_file = h5_io.h5_base_file(app=self.app,measurement=self)
        try:
            self.h5_file.attrs['time_id'] = self.t0
            H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
        
            #create h5 data arrays
    
            if self.settings['collect_apd']:
                H['apd_count_rates'] = np.array(self.apd_count_rates)
            if self.settings['collect_lifetime']:
                H['hydraharp_elapsed_time'] = self.hydraharp_elapsed_time
                H['hydraharp_histograms'] = self.hydraharp_histograms
                H['hydraharp_time_array'] = self.hydraharp_time_array
            if self.settings['collect_spectrum']:
                H['wls'] = self.lightfield_readout.wls
                H['spectra'] = np.squeeze(np.array(self.spectra))
                H['integrated_spectra'] = np.array(self.integrated_spectra)
            #if self.settings['collect_ascom_img']:
            #    H['ascom_img_stack'] = np.array(self.ascom_img_stack)
            #    H['ascom_img_integrated'] = np.array(self.ascom_img_integrated)
                
            H['pm_powers'] = np.array(self.pm_powers)
            H['pm_powers_after'] = np.array(self.pm_powers_after)
            H['power_wheel_position'] = np.array(self.power_wheel_position)
            H['direction'] = self.direction
        finally:
            self.log.info("data saved "+self.h5_file.filename)
            self.h5_file.close()
        


    def move_to_min_pos(self):
        self.power_wheel_dev.read_status()
        
        delta_steps = self.power_wheel_min.val - self.power_wheel_hw.encoder_pos.read_from_hardware()
        if delta_steps != 0:
            #print 'moving to min pos'
            self.power_wheel_dev.write_steps_and_wait(delta_steps)
            #print 'done moving to min pos'

    
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
                    powermeter_hw_name = 'thorlabs_powermeter_' + self.powermeter_type.val
                    while samp_count < 6:
                        pm_power = pm_power + self.app.hardware[powermeter_hw_name].power.read_from_hardware(send_signal=True)
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