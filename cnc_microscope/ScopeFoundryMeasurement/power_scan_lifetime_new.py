'''
Created on Jun 19, 2014

@author: Edward Barnard
'''
from ScopeFoundry import Measurement
import numpy as np
import time
from scipy.optimize import curve_fit
from ScopeFoundry import h5_io
from ScopeFoundry.helper_funcs import sibling_path
import pyqtgraph as pg

#################################################
#### A few things to do on this code:
######### (1) Select which power meter to use. Now this is manually changed in code. Need to change it.
######### (2) Add x-axis selection into the ui
######### (3) Use shutter is not really used. Need to change it.


class PowerScanMeasure_lifetime(Measurement):
    
    name = 'power_scan_lifetime'
    
    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "power_scan_lifetime_new.ui")
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

        self.collect_apd      = self.add_logged_quantity("collect_apd",      dtype=bool, initial=True)
        self.collect_spectrum = self.add_logged_quantity("collect_spectrum", dtype=bool, initial=False)
        self.collect_lifetime = self.add_logged_quantity("collect_lifetime", dtype=bool, initial=True)
        
        self.collect_apd_trace = self.add_logged_quantity("collect_apd_trace", dtype=bool, initial=False)
        self.apd_trace_Tacq = self.add_logged_quantity("apd_trace_Tacq", 
                                                          dtype=float, unit='s', initial=5.0, vmin=1.0, vmax=60.0, ro=False)

        self.total_ct_lifetime = self.add_logged_quantity("total_ct_lifetime", dtype=float, initial= 100000, vmin=1, vmax = 1.0e8, ro=False)
        self.curvefitting_time = self.add_logged_quantity("curvefitting_time", dtype = float, unit="ms", initial=5, vmin=0.0, vmax = 1000.0, ro=False, si=True)
        
        #self.collect_ascom_img = self.add_logged_quantity('collect_ascom_img', dtype=bool, initial=False)
        
        self.powermeter_type = self.settings.New('powermeter_type', dtype=str, initial='Si',
                                                  choices=('Si', 'Ge'))
        self.settings.New("x_axis", dtype=str, initial='pm_power', choices=('power_wheel', 'pm_power'))
    
        #self.powermeter_type = self.settings.New('powermeter_type', dtype=str, initial='Si',
        #                                          choices=('Si', 'Ge', 'Synchronized'))
    
    def setup_figure(self):
        
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)

        self.power_wheel_min.connect_to_widget(self.ui.powerwheel_min_doubleSpinBox)
        self.power_wheel_max.connect_to_widget(self.ui.powerwheel_max_doubleSpinBox)
        self.power_wheel_ndatapoints.connect_to_widget(self.ui.num_datapoints_doubleSpinBox)
        self.apd_trace_Tacq.connect_to_widget(self.ui.apd_trace_Tacq_doubleSpinBox)

        self.use_shutter.connect_bidir_to_widget(self.ui.use_shutter_checkBox)
        self.up_and_down_sweep.connect_bidir_to_widget(self.ui.updown_sweep_checkBox)

        self.collect_apd.connect_to_widget(self.ui.collect_apd_checkBox)
        self.collect_spectrum.connect_to_widget(self.ui.collect_spectrum_checkBox)
        self.collect_lifetime.connect_to_widget(self.ui.collect_hydraharp_checkBox)
        self.collect_apd_trace.connect_to_widget(self.ui.collect_apd_trace_checkBox)
        
        self.total_ct_lifetime.connect_to_widget(self.ui.total_ct_lifetime_doubleSpinBox)
        self.curvefitting_time.connect_to_widget(self.ui.curvefitting_time_doubleSpinBox)
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
            self.plot_line1.setData(X, self.lifetime_graph[:ii])
            self.hydraharp_measurement.update_display()
        elif self.settings['collect_spectrum']:
            if hasattr(self, 'integrated_spectra'):
                self.plot_line1.setData(X, self.integrated_spectra[:ii])
            self.lightfield_readout.update_display()
        #elif self.settings['collect_ascom_img']:
        #    self.plot_line1.setData(X, self.ascom_img_integrated[:ii])
        #    self.ascom_camera_capture.update_display()
        elif self.settings['collect_apd_trace']:
            self.plot_line1.setData(X, self.integrated_apd_count_trace[:ii])
            self.apd_optimizer.update_display()
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
        self.power_wheel_hw = self.app.hardware.side_beam_power_wheel
        self.power_wheel_dev = self.power_wheel_hw.power_wheel_dev
        
        if self.settings['collect_apd']:
            self.apd_counter_hw = self.app.hardware.apd_counter
            self.apd_count_rate_lq = self.apd_counter_hw.settings.apd_count_rate     

        if self.settings['collect_lifetime']:
            self.apd_counter_hw = self.app.hardware.apd_counter
            self.apd_count_rate_lq = self.apd_counter_hw.settings.apd_count_rate

            self.hydraharp_measurement = self.app.measurements['hydraharp_histogram']
        if self.settings['collect_spectrum']:
            self.lightfield_readout = self.app.measurements['lightfield_readout']
        
        if self.settings['collect_apd_trace']:
            self.apd_optimizer = self.app.measurements['apd_optimizer']   
                   
        #if self.settings['collect_ascom_img']:
            #self.ascom_camera_capture = self.app.measurements.ascom_camera_capture
            #self.ascom_camera_capture.settings['continuous'] = False
            
            
        
        #####
        self.Np = Np = self.power_wheel_ndatapoints.val
        self.step_size = int( (self.power_wheel_max.val-self.power_wheel_min.val)/Np )
        
    
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
            self.hh_time = []
            self.hh_histograms = []
            self.popt = []
            self.pcov = []
            self.lifetime_graph = []
            self.elapsed_time = []
            self.apd_ct = []
        if self.settings['collect_spectrum']:
            self.spectra = [] # don't know size of ccd until after measurement
            self.integrated_spectra = []
        if self.settings['collect_apd_trace']:
            self.apd_time = []
            self.apd_count_trace = []
            self.npoint_trace = []
            self.integrated_apd_count_trace = []
            self.pm_power_trace = []
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
            
                
                ct = 0
                for i in np.arange(5):
                    ct += self.apd_counter_hw.settings.apd_count_rate.read_from_hardware()
                    time.sleep(0.1)
                ct = ct/5
                
                set_time = self.total_ct_lifetime.val/ct*1000
                if set_time < 30000.0:
                    set_time = 30000.0
                if set_time > 600000.0:
                    set_time = 600000.0
            
                
                self.hydraharp_measurement.read_lifetime(set_time)
                
                
                time_array = np.array(self.hydraharp_measurement.time_array)
                hist_data0 = self.hydraharp_measurement.hist_data0
                
                
                number_point = np.argmin(abs(time_array - self.curvefitting_time.val*10**9))+1
                
                popt_bool = True
                try:
                    popt0, pcov0 = curve_fit(self.expfunc, time_array[0:number_point]/10**9, hist_data0[0:number_point], bounds = [[0.0, 0.0, 0.0],[3.0, np.inf, np.inf]])
                except:
                    popt0 = np.array([0.0,0.0,0.0,0.0,0.0])
                    pcov0 = np.array([0.0,0.0,0.0,0.0,0.0])
                    pass
                
                #print("time_array: ",self.time_array[0:number_point])
                #print("hist_data0: ",self.hist_data0)
                print("number of point: ",number_point)
                #print("popt0: ", popt0)
                
                if popt_bool == True:
                    if np.size(popt0) > 4:
                        index = np.argmax([popt0[2], popt0[3]])
    
                        print("index: ",index)
                        lifetime1 = popt0[index]
                
                self.elapsed_time.append(int(set_time))
                self.hh_time.append(time_array)
                self.hh_histograms.append(hist_data0)

                self.popt.append(popt0)
                self.pcov.append(pcov0)
                
                self.lifetime_graph.append(lifetime1)
                self.apd_ct.append(ct)

            if self.settings['collect_spectrum']:
                self.lightfield_readout.ro_acquire_data()
                spec = np.array(self.lightfield_readout.img)
                self.spectra.append( spec )
                self.integrated_spectra.append(spec.sum())
            
            if self.settings['collect_apd_trace']:
                self.apd_optimizer.trace_apd(self.apd_trace_Tacq.val, self.powermeter_type.val)
                
                self.apd_time.append(self.apd_optimizer.full_optimize_history_time)
                count_trace = np.array(self.apd_optimizer.full_optimize_history)
                self.apd_count_trace.append(count_trace)
                
                
                npoint_trace = self.apd_optimizer.optimize_ii_1
                self.npoint_trace.append(npoint_trace)
                self.integrated_apd_count_trace.append(count_trace.sum()/npoint_trace)
                self.pm_power_trace.append(self.apd_optimizer.full_optimize_history_pmpower)
                
            #if self.settings['collect_ascom_img']:
            #    self.ascom_camera_capture.interrupt_measurement_called = False
            #    self.ascom_camera_capture.run()
            #    img = self.ascom_camera_capture.img.copy()
            #    self.ascom_img_stack.append(img)
            #    self.ascom_img_integrated.append(img.astype(float).sum())
            
            
            #########Closing shutter
            if self.use_shutter.val == True:
                print ('Now closing shutter...')
                self.app.hardware.dual_position_slider.move_fwd()
                
                
            # collect power meter value after measurement
            #self.pm_powers_after[ii]=self.collect_pm_power_data()
            self.pm_powers_after.append(self.collect_pm_power_data())
            
            # move to new power wheel position
            self.power_wheel_dev.write_steps_and_wait(self.step_size*self.direction[ii])
            time.sleep(1.0)
            self.power_wheel_hw.encoder_pos.read_from_hardware()

        # write data to h5 file on disk
        
        self.t0 = time.time()
        #self.fname = "%i_%s.h5" % (self.t0, self.name)
        #self.h5_file = h5_io.h5_base_file(self.app, self.fname )
        self.h5_file = h5_io.h5_base_file(app=self.app,measurement=self)
        try:
            self.h5_file.attrs['time_id'] = self.t0
            H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
            
            H['pm_powers'] = np.array(self.pm_powers)
            H['pm_powers_after'] = np.array(self.pm_powers_after)
            H['power_wheel_position'] = np.array(self.power_wheel_position)
            H['direction'] = self.direction
            
            #create h5 data arrays
    
            if self.settings['collect_apd']:
                H['apd_count_rates'] = np.array(self.apd_count_rates)
            if self.settings['collect_lifetime']:
                H['histograms'] = self.hh_histograms
                H['time_array'] = self.hh_time
                H['popt'] = self.popt
                H['pcov'] = self.pcov
                H['lifetime_graph'] = self.lifetime_graph
                #H['elapsed_time'] = self.elapsed_time
                H['apd_ct'] = self.apd_ct
            if self.settings['collect_spectrum']:
                H['wls'] = self.lightfield_readout.wls
                H['spectra'] = np.squeeze(np.array(self.spectra))
                H['integrated_spectra'] = np.array(self.integrated_spectra)
            if self.settings['collect_apd_trace']:
                
                height_array = np.shape(self.apd_time)[0]
                width_array = int(np.average(self.npoint_trace))
                
                self.time_array = np.zeros((height_array, width_array))
                self.pm_power_trace_array = np.zeros((height_array, width_array))
                self.apd_count_trace_array = np.zeros((height_array, width_array))
                print("height_array: ",height_array)
                print("width_array: ",width_array)
                for i in np.arange(height_array):
                    for j in np.arange(width_array):
                        print(self.apd_time[i][j])
                        self.time_array[i,j] = self.apd_time[i][j]
                        
                        self.pm_power_trace_array[i,j] = self.pm_power_trace[i][j]
                        self.apd_count_trace_array[i,j] = self.apd_count_trace[i][j]
                        
                print(self.apd_time)
                H['time'] = self.time_array
                H['apd_count_trace'] = self.apd_count_trace_array
                H['integrated_apd_count_trace'] = self.integrated_apd_count_trace
                H['npoint_trace'] = self.npoint_trace
                H['pm_power_trace'] = self.pm_power_trace_array
            #if self.settings['collect_ascom_img']:
            #    H['ascom_img_stack'] = np.array(self.ascom_img_stack)
            #    H['ascom_img_integrated'] = np.array(self.ascom_img_integrated)
                

        finally:
            self.log.info("data saved "+self.h5_file.filename)
            print("Measurement done")
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
                    pm_power = pm_power + self.app.hardware[powermeter_hw_name].power.read_from_hardware(send_signal=True)
                    samp_count = samp_count + 1
                    if samp_count > 5:
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
    
    def biexpfunc(self, x, a1, b1, c1):
        return b1*np.exp(-x/a1) + c1