from ScopeFoundry import Measurement
import numpy as np
import time
import pyqtgraph as pg
from ScopeFoundry.helper_funcs import sibling_path, replace_widget_in_layout
from nltk.app.nemo_app import initialFind
from ScopeFoundry import h5_io



class ChameleonPLEMeasure(Measurement):
    
    name = "chameleon_PLE"
    
    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "chameleon_PLE.ui")
        super(ChameleonPLEMeasure, self).__init__(app) 
    
    
    
    
    
    
    
    
    
    
    
    
    
    def setup(self):
        
        self.use_shutter = self.add_logged_quantity('use_shutter', dtype=bool, initial=True)
        
        self.wl_start = self.add_logged_quantity('wl_start', dtype=float, initial=700, unit='nm')
        self.wl_stop  = self.add_logged_quantity('wl_stop',  dtype=float, initial=900, unit='nm')
        self.wl_step  = self.add_logged_quantity('wl_step', dtype=float, initial=10, unit='nm')
        
        self.use_ccd   = self.add_logged_quantity('use_ccd', dtype=bool, initial=True)
        self.ccd_bgsub = self.add_logged_quantity('ccd_bgsub', dtype=bool, initial=True)
        self.collect_apd   = self.add_logged_quantity('collect_apd', dtype=bool, initial=False)
        
        self.up_down_sweep = self.add_logged_quantity('up_down_sweep', dtype=bool, initial=True)
        
        
        self.update_period = 0.250
        self.laser_hc = self.gui.hardware_components['ChameleonUltraIILaser']
        self.powermeter = self.gui.hardware_components['thorlabs_powermeter']
        self.shutter = self.gui.hardware_components['shutter_servo']

    def setup_figure(self):
        self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))
        self.ui = self.graph_layout 
        self.ui.show()
        
        self.graph_layout.setWindowTitle("Chameleon PLE")
        
        self.plot_current_spec = self.graph_layout.addPlot(title="Current Spectrum")
        self.plotline_current_spec = self.plot_current_spec.plot([0])

        self.plot_pm_power = self.graph_layout.addPlot(title="PM Power vs laser wl")
        self.plotline_pm_power = self.plot_pm_power.plot([0])
        self.plotline_pm_power_after = self.plot_pm_power.plot([0])

        self.plot_ple = self.graph_layout.addPlot(title="PLE vs laser wl")
        self.plotline_ple = self.plot_ple.plot([0])
        
    
        
        
    def update_display(self):
        i_wl = self.i_wl
        self.plotline_current_spec.setData(self.ccd_wls, self.ccd_specs[i_wl])
        
        self.plotline_pm_power.setData(self.wls[0:i_wl], self.pm_powers[0:i_wl])
        self.plotline_pm_power_after.setData(self.wls[0:i_wl], self.pm_powers_after[0:i_wl])
        
        
        ##########CAREFUL: You Need to manually change the display here for 1p and 2p PLE....
        
        ###For one photon PLE
        self.plotline_ple.setData(self.wls[0:i_wl], self.integrated_specs[0:i_wl]*2.0/(
                                                       self.pm_powers[0:i_wl]+self.pm_powers_after[0:i_wl]))
        
        ##For two photon PLE
        #self.plotline_ple.setData(self.wls[0:i_wl], self.integrated_specs[0:i_wl]/(((
        #                                               self.pm_powers[0:i_wl]+self.pm_powers_after[0:i_wl])*0.5)**2))

    def _run(self):
        
        #####added by Kaiyuan 09/20
        SET_POWER_WHEEL_POS      = False   ###load .txt file for powerwheel pos
        POWER_CONTROL            = True   ###feedback control
        Reverse_Dir              = True   ###When True, sweep starts from low energy.
        USE_SHG                  = False   ###When True, the SHG of Chameleon is used for excitation. PM set wl needs to be halfed 
                
        # Hardware
        if self.use_ccd.val:
            ccd_hc = self.gui.andor_ccd_hc
            ccd = self.gui.andor_ccd_hc.andor_ccd
        if self.collect_apd.val:
            self.apd_counter_hc = self.gui.apd_counter_hc
            self.apd_count_rate_lq = self.gui.apd_counter_hc.apd_count_rate     
            
        
        
        # List of frequency steps to take based on min, max and step size specified 
        # in the GUI
        self.wls = np.arange(self.wl_start.val, self.wl_stop.val, self.wl_step.val) #Note this is the wls of the TiSph main beam
        
        if Reverse_Dir:
            self.wls=self.wls[::-1]
        
        if self.up_down_sweep.val:
            #print self.wls
            self.wls = np.concatenate([self.wls, self.wls[::-1]]) #Note, self.wls is always the wls of the TiSph main beam
            print self.wls
        
        N_wls = len(self.wls)
        
        # If use SHG, Kaiyuan 10/08
        if USE_SHG:
            self.wls_SHG=self.wls*0.5
        
        # Set Powerwhell Position, Kaiyuan 09/20
        if SET_POWER_WHEEL_POS:
            power_wheel_arduino = self.gui.power_wheel_arduino_hc.power_wheel
            power_wheel_arduino_hc = self.gui.power_wheel_arduino_hc
                    
            try:
                power_wheel_positions = np.transpose(
                    np.loadtxt('./measurement_components/ple_config_files/chameleon_power_wheel_positions.txt'))
            except ():
                print 'Failed to load power wheel position configuration file'
                return
                    
            if np.min(self.wls) < np.min(power_wheel_positions[0]):
                print "Out of range (min).  Exitting."
                return
            if np.max(self.wls) > np.max(power_wheel_positions[0]):
                print "Out of range (max).  Exitting."
                return
            
            self.power_wheel_positions = np.zeros(N_wls, dtype=int)   
        
        
        # FEED BACK POWER CONTROL, Kaiyuan 09/20

        if POWER_CONTROL:
            power_wheel_arduino = self.gui.power_wheel_arduino_hc.power_wheel
            power_wheel_arduino_hc = self.gui.power_wheel_arduino_hc
            
            Power_Set=10e-6 #the ideal power you want, in W
            Flux_Set=Power_Set*self.wls[0]
            
            Power_Tol=0.05*Power_Set #tolerance of feedback control
            Flux_Tol=0.05*Flux_Set
            self.power_wheel_positions = np.zeros(N_wls, dtype=int)  
            
            d_pos=5 #how many steps the powerwheel moves at a time during feedback control
            PC_max=20  #how many moves the feedback system trys before giving up    
        
        
        
        # create data arrays
        self.uf_powers = np.zeros(N_wls, dtype=float)
        self.pm_powers = np.zeros(N_wls, dtype=float)
        self.pm_powers_after = np.zeros(N_wls, dtype=float)        
        
        if self.use_ccd.val:
            self.ccd_specs = np.zeros( (N_wls, ccd.Nx_ro), dtype=int)
            self.integrated_specs = np.zeros(N_wls, dtype=float)
            
            width_px = ccd.Nx_ro
            height_px = ccd.Ny_ro
            
            self.ccd_wls  = pixel2wavelength(self.gui.acton_spec_hc.center_wl.val, 
                  np.arange(width_px), binning=ccd.get_current_hbin())
        if self.collect_apd.val:
            self.apd_count_rates = np.zeros(N_wls, dtype=float)


        
        # close shutter
        if self.use_shutter.val:
            self.shutter.shutter_open.update_value(False)
            time.sleep(0.5)        
        
        ####################################################################### main loop starts
        try:
        
            # initial spectra
            
            for i_wl, wl in enumerate(self.wls):
                if self.interrupt_measurement_called:
                    break
                
                
                # tune wavelength of laser, wait for stabilization, read nominal uf power
                self.laser_hc.wavelength.update_value(wl)
                time.sleep(20)        ###SHG needs about 20s to stablize!!!#####Main bean needs only ~5s
                self.uf_powers[i_wl] = self.laser_hc.uf_power.read_from_hardware()
                
                
                # set power wheel positions, Kaiyuan 09/20
                if SET_POWER_WHEEL_POS:
                    new_pos = int(np.interp(wl, power_wheel_positions[0], power_wheel_positions[1]))
                    curr_pos = power_wheel_arduino_hc.encoder_pos.read_from_hardware()
                    d_pos = new_pos - curr_pos 
                    # negative values to move_fwd causes it to move backwards.
                    print wl, new_pos, curr_pos, d_pos
                    power_wheel_arduino_hc.move_relative(d_pos)
                    time.sleep(0.2)
                    
                    self.power_wheel_positions[i_wl] = new_pos
                
                                                    
                # set power meter wavelength
                if USE_SHG:
                    self.powermeter.wavelength.update_value(wl*0.5)
                else:
                    self.powermeter.wavelength.update_value(wl)
                
                
                
                # Feed back power control
                if POWER_CONTROL:                   
                    
                    if 0:
                        pm_temp1=self.collect_pm_power_data()
                        time.sleep(0.1)
                        pm_temp2=self.collect_pm_power_data()
                        time.sleep(0.1)
                        pm_temp3=self.collect_pm_power_data()
                        time.sleep(0.1)                
                        pm_temp=(pm_temp1+pm_temp2+pm_temp3)/3.0
                    elif 1:
                        pm_temp = self.collect_pm_power_data()
                    
                    flux_temp=pm_temp*wl  #photon flux
                    
                    PC_ct=0
                    
                    while (abs(flux_temp-Flux_Set)>Flux_Tol) and (PC_ct<PC_max):
                        
                        if flux_temp<Flux_Set:
                            power_wheel_arduino_hc.move_relative(d_pos)
                            time.sleep(0.1)
                        if flux_temp>Flux_Set:
                            power_wheel_arduino_hc.move_relative(-d_pos)
                            time.sleep(0.1)  
                        
                        if 0:
                            pm_temp1=self.collect_pm_power_data()
                            time.sleep(0.1)
                            pm_temp2=self.collect_pm_power_data()
                            time.sleep(0.1)
                            pm_temp3=self.collect_pm_power_data()
                            time.sleep(0.1)                
                            pm_temp=(pm_temp1+pm_temp2+pm_temp3)/3.0
                        elif 1:
                            pm_temp = self.collect_pm_power_data()
                            
                        flux_temp=pm_temp*wl  #photon flux
                        
                        PC_ct+=1
                           
                    print PC_ct                     
                        
                    
                
                
                # read power meter value
                self.pm_powers[i_wl] = self.collect_pm_power_data()
                
                # open shutter
                if self.use_shutter.val:
                    self.shutter.shutter_open.update_value(True)
                    time.sleep(0.5)        
                
                # acquire data from detectors
                if self.use_ccd.val:
                    t_acq = self.gui.andor_ccd_hc.exposure_time.val #in seconds
                    wait_time = np.min(1.0,np.max(0.05*t_acq, 0.05))
                    ccd.start_acquisition()
                    stat = "ACQUIRING"
                    while (stat!= "IDLE") and (not self.interrupt_measurement_called):
                        time.sleep(wait_time)
                        stat = ccd.get_status()                    
                    
                    buffer_ = ccd.get_acquired_data()
                    if self.ccd_bgsub.val:
                        buffer_ = buffer_ - self.gui.andor_ccd_hc.background

                    spectrum = np.sum(buffer_, axis=0) # flatten to 1D
                    self.ccd_specs[i_wl] = spectrum
                    self.integrated_specs[i_wl] = spectrum.sum() 
                if self.collect_apd.val:
                    self.apd_count_rates[i_wl] = self.apd_count_rate_lq.read_from_hardware()

                
                # close shutter
                if self.use_shutter.val:
                    self.shutter.shutter_open.update_value(False)
                    time.sleep(0.5)
                                    
                # read power meter value after
                self.pm_powers_after[i_wl] = self.collect_pm_power_data()

                self.i_wl = i_wl
                self.progress.update_value( 100.*i_wl/N_wls)

        finally:
            
            # close shutter
            if self.use_shutter.val:
                self.shutter.shutter_open.update_value(False)
                time.sleep(0.5)
            
            # stop any running ccd acqusitions        
            if self.use_ccd.val and self.interrupt_measurement_called:
                    self.gui.andor_ccd_hc.interrupt_acquisition()

            #save data
            save_dict = {
                         'wls': self.wls,
                         'uf_powers': self.uf_powers,
                         'pm_powers': self.pm_powers,
                         'pm_powers_after': self.pm_powers_after,
                        }
            
            if self.use_ccd.val:
                save_dict.update({
                          'ccd_specs': self.ccd_specs,
                          'integrated_specs': self.integrated_specs,
                          'ccd_wls': self.ccd_wls,
                                  })

                if self.ccd_bgsub.val:
                    save_dict['ccd_bg'] = self.gui.andor_ccd_hc.background
            if self.collect_apd.val:
                save_dict.update({
                                  'apd_count_rates': self.apd_count_rates,
                })
            
            if SET_POWER_WHEEL_POS:
                save_dict.update({'power_wheel_positions': self.power_wheel_positions})

            
        
            data_fname = "%i_chameleon_ple_scan.npz" % time.time()
            np.savez_compressed(data_fname, **save_dict)
            print "Chameleon PLE scan complete, data saved as", data_fname
    
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
                    pm_power = pm_power + self.gui.thorlabs_powermeter_hc.power.read_from_hardware(send_signal=True)
                    samp_count = samp_count + 1
                    break 
                except Exception as err:
                    try_count = try_count + 1
                    if try_count > 9:
                        print "failed to collect power meter sample:", err
                        break
                    time.sleep(0.010)
         
        if samp_count > 0:              
            pm_power = pm_power/samp_count
        else:
            print "  Failed to read power"
            pm_power = 10000.  

        
        return pm_power
