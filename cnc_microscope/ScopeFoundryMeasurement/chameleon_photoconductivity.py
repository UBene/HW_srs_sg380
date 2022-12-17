
'''
Kaiyuan Yao
12/08/2018

'''


from ScopeFoundry import Measurement
import numpy as np
import time
import pyqtgraph as pg
from ScopeFoundry.helper_funcs import sibling_path, replace_widget_in_layout
from nltk.app.nemo_app import initialFind
from ScopeFoundry import h5_io



class ChameleonPhotoconductivityMeasure(Measurement):
    
    name = "chameleon_photoconductivity"
    
    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "chameleon_photoconductivity.ui")
        super(ChameleonPhotoconductivityMeasure, self).__init__(app) 
    
    def setup(self):
        
        #self.app.hardware_components['keithley_sourcemeter'].V_source.connect_bidir_to_widget(self.ui.Vsd_doubleSpinBox)
        
        self.Vsd = self.settings.New(name='Vsd', dtype=float, unit='V', si=True, initial=0.0, ro=False)
        self.Vsd.connect_bidir_to_widget(self.ui.Vsd_doubleSpinBox)
        
        self.output_port = self.settings.New(name='output_port', dtype=str,  choices=[("OPO","OPO"),("Pump","Pump"),("Pump Align","Pump Align"), ("Pump SHG","Pump SHG"),("OPO SHG", "OPO SHG")], initial='OPO' )
        self.output_port.connect_bidir_to_widget(self.ui.output_port_comboBox)
        
        self.powermeter_choice = self.settings.New(name='powermeter_choice', dtype=str,  choices=[("Si","Si"),("Ge","Ge")], initial='Ge' )
        self.powermeter_choice.connect_bidir_to_widget(self.ui.powermeter_choice_comboBox)
        
        self.ND_wheel_choice = self.settings.New(name='ND_wheel_choice', dtype=str,  choices=[("Main","Main"),("Side","Side")], initial='Main' )
        self.ND_wheel_choice.connect_bidir_to_widget(self.ui.ND_filter_choice_comboBox)
        
        self.constant_Iph = self.settings.New('constant_Iph', dtype=bool, initial=True)
        self.settings.constant_Iph.connect_bidir_to_widget(self.ui.constant_Iph_checkBox)
        
        self.power_reg_deadtime = self.settings.New('power_reg_deadtime', dtype=float, unit='s', si=True, initial=60, ro=False )
        self.settings.power_reg_deadtime.connect_bidir_to_widget(self.ui.power_reg_deadtime_doubleSpinBox)
        
        self.save_h5 = self.settings.New('save_h5', dtype=bool, initial=True)
        self.settings.save_h5.connect_bidir_to_widget(self.ui.save_h5_checkBox)
        
        #################################################################
        ##### Note: need to change this unit to nA in the following codes
        self.set_constant_Iph = self.settings.New('set_constant_Iph', dtype=float, unit='nA', si=False, initial=0.1, ro=False)
        self.settings.set_constant_Iph.connect_bidir_to_widget(self.ui.set_constant_Iph_doubleSpinBox) 
        
        self.set_Iph_tol_percent = self.settings.New('set_Iph_tol_percent', dtype=float, initial=0.02, ro=False )
        self.settings.set_Iph_tol_percent.connect_bidir_to_widget(self.ui.set_Iph_tol_percent_doubleSpinBox)
        
        self.pw_move_steps = self.settings.New('pw_move_steps', dtype=int, initial = 10, ro=False )
        self.settings.pw_move_steps.connect_bidir_to_widget(self.ui.pw_move_steps_doubleSpinBox)
        
        self.start_wls = self.settings.New('start_wls', dtype=float, unit='nm', si=False, initial=1500.0, ro=False)
        self.settings.start_wls.connect_bidir_to_widget(self.ui.start_wls_doubleSpinBox)
        
        self.end_wls = self.settings.New('end_wls', dtype=float, unit='nm', si=False, initial=1010.0, ro=False)
        self.settings.end_wls.connect_bidir_to_widget(self.ui.end_wls_doubleSpinBox)
        
        self.step_wls = self.settings.New('step_wls', dtype=float, unit='nm', si=False, initial=5.0, ro=False)
        self.settings.step_wls.connect_bidir_to_widget(self.ui.step_wls_doubleSpinBox)
        
        self.up_down_scan = self.settings.New('up_down_scan', dtype=bool, initial=True)
        self.settings.up_down_scan.connect_bidir_to_widget(self.ui.up_down_scan_checkBox)
        
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        
        

        
        
    def setup_figure(self):
        # ui window
        if hasattr(self, 'graph_layout'):
            self.graph_layout.deleteLater() # see http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            del self.graph_layout
        
        ###################Emission spectrum
        self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)
        

        self.emission_plot = self.graph_layout.addPlot(title="Not Used")
        self.emission_plot_line = self.emission_plot.plot([1,3,2,4,3,5])
        self.emission_plot.enableAutoRange()
        

        ###################Photocurrent Spectrum
        self.graph_layout.nextCol()
        
        self.photocurrent_plot = self.graph_layout.addPlot(title="Photocurrent Spectrum (A)")
        self.photocurrent_plot_line = self.photocurrent_plot.plot([1,3,2,4,3,5])
        self.photocurrent_plot.enableAutoRange()
        
        ##############Excitation Power Spectrum
        self.graph_layout.nextCol()
        
        self.excitation_power_plot = self.graph_layout.addPlot(title="Excitation Power Spectrum (mW)")
        self.excitation_power_plot_line = self.excitation_power_plot.plot([1,3,2,4,3,5])
        #self.excitation_power_plot_line1 = self.excitation_power_plot.plot([1,3,2,4,3,5])
        self.excitation_power_plot.enableAutoRange()
        
        
        
        
        
        
    def run(self):
        

        ##############################################################
        ###### Hardwares, Equipment, and Measurement sub-modules to use
            
        self.laser_hw = self.app.hardware.ChameleonUltraIILaser
        self.laser_dev = self.laser_hw.laser
        self.opo_hw   = self.app.hardware.ChameleonOPOVis
        self.opo_dev  = self.opo_hw.opo
        self.keithley_hw = self.app.hardware.keithley_sourcemeter
        self.keithley_dev = self.keithley_hw.keithley
        
        self.ext_shutter_hw = self.app.hardware.dual_position_slider
        self.ext_shutter_hw.move_fwd() ##Make sure excitation shutter is closed at first
        

        if self.powermeter_choice.val == 'Ge':
            self.pm_hw = self.app.hardware.thorlabs_powermeter_Ge
            self.pm_dev = self.pm_hw.power_meter
        elif self.powermeter_choice.val == 'Si':
            self.pm_hw = self.app.hardware.thorlabs_powermeter_Si
            self.pm_dev = self.pm_hw.power_meter
        else:
            print('unknown choice of powermeter')
            print('self.powermeter_choice is {}'.format(self.powermeter_choice))
        
        #####################################################################
        ###################Note: double check here. The names of power wheels have been changed.
        ###############!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!   
        if self.ND_wheel_choice.val == 'Side':
            self.pw_hw = self.app.hardware.side_beam_power_wheel
            self.pw_dev = self.pw_hw.power_wheel_dev
        elif self.ND_wheel_choice.val == 'Main':
            self.pw_hw = self.app.hardware.main_beam_power_wheel
            self.pw_dev = self.pw_hw.power_wheel_dev
        else:
            print('unknown choice of ND wheel')
            print('self.ND_wheel_choice is {}'.format(self.ND_wheel_choice))
        
        
        ############################################### 
        ##################Set scanning wavelengths range
        if self.start_wls.val > self.end_wls.val:
            print ('Low energy to high energy')
            self.step_wls.val = -np.abs(self.step_wls.val) 
        else:
            print ('High energy to Low energy')
            self.step_wls.val = np.abs(self.step_wls.val)
            
        print ('Start wavelength: {}nm,  End wavelength: {}nm,  Step wavelength: {}nm'.format(self.start_wls.val, self.end_wls.val, self.step_wls.val))    
        if self.up_down_scan.val == True:
            print ('Using up and down scanning')
            wls_range_1 = np.arange(self.start_wls.val, self.end_wls.val, self.step_wls.val, dtype=float)
            wls_range_2 = wls_range_1[::-1]
            self.wls_range = np.hstack( (wls_range_1, wls_range_2) )
        else:
            print ('Using one way scanning')
            self.wls_range = np.arange(self.start_wls.val, self.end_wls.val, self.step_wls.val, dtype=float)
        print('wls_range shape: {}'.format(self.wls_range.shape))
        print ('Wavelength to scan: {}'.format(self.wls_range))
        
        
#         #########################################################
#         ############ Configure Keithley for Isd measurement
#         self.keithley_dev.set_source_mode(target_mode = 'voltage')
#         self.keithley_dev.set_auto_range()
#         self.keithley_dev.disable_source()
        
        
        ##################################################
        ################# Define how many powermeter and keithley readings are used for averaging
        N_P_read = 6
        N_I_read = 10
        
        
        
                
        ###################################################
        ####################### Initialize data arrays
        self.ext_wls_range      = np.zeros(self.wls_range.shape, dtype=float)
        self.ext_wls_linewidth  = np.zeros(self.wls_range.shape, dtype=float)
        self.photocurrent   = np.zeros(self.ext_wls_range.shape, dtype=float)
        self.I_lightON   =  np.zeros(self.ext_wls_range.shape, dtype=float)
        self.I_lightOFF   = np.zeros(self.ext_wls_range.shape, dtype=float)
        self.ext_power          = np.zeros(self.ext_wls_range.shape, dtype=float)
        self.ext_power_after_exposure = np.zeros(self.ext_wls_range.shape, dtype=float) ##register the poewr right after CCD acquisition
        self.ext_power_before_exposure = np.zeros(self.ext_wls_range.shape, dtype=float) 
        self.ext_flux           = np.zeros(self.ext_wls_range.shape, dtype=float)
        self.ext_FLAG           = np.zeros(self.ext_wls_range.shape, dtype=bool) ##########FLAG to register if OPO status is OK or not.
        #self.ems_specs          = np.zeros((self.ext_wls_range.shape[0], self.ems_wls_now.shape[0]), dtype=float)
       
       
               
#         ##################################################
#         ########Powermeter RunZero
#         #############Open OPO shutter here
#         self.opo_hw.opo_out_shutter_close()
#         print('Closing OPO output shutter')
#         self.ext_shutter_hw.move_fwd() #close excitation shutter as well
#         
        wl_now = self.wls_range[0]
#         self.pm_dev.set_wavelength(wl=wl_now)
#         self.pm_hw.read_from_hardware() 
#         print ('**************PM reading BEFORE running zero: {} mW'.format( self.powermeter_avg_reading(N_read=3) ) )
#         time.sleep(0.5)
#         
#         self.laser_dev.write_shutter(_open=False)
#         time.sleep(1)
#         self.pm_hw.run_zero()
#         self.pm_dev.set_auto_range()
#         #self.ems_wls_background, self.ems_intensity_background = self.lf_spec_readout.ro_acquire_data() ####Take a background spec here!!    
#         time.sleep(0.2)
#         print ('**************PM reading AFTER running zero: {} mW'.format( self.powermeter_avg_reading(N_read=3) ) )
#         time.sleep(0.3)
#         self.laser_dev.write_shutter(_open=True)
#         time.sleep(1)
#         print ('**************PM reading AFTER opening laser shutter: {} mW'.format( self.powermeter_avg_reading(N_read=3) ) )
#         time.sleep(0.3)
    
    
        ############################
        ## Ramp the Vsd to the desired value
        print ('Ramping voltage source to: {}[V] ...'.format(self.Vsd.val) )
        
        self.keithley_dev.set_source_mode(target_mode = 'voltage')
        self.keithley_dev.set_auto_range()
        self.keithley_dev.enable_source()
        self.keithley_dev.ramp_source_voltage(target_voltage = self.Vsd.val, steps=10, pause=0.5)
        self.keithley_dev.configure_measure_current(nplc_val=1, current_lim = 1e-6, auto_range=True)
        time.sleep(0.1)
        
        
        
        
        ##########Set update display period
        self.display_update_period = 0.01 #seconds
        
        opo_set_wl_dead_time = 60
        
        #########Set the tolerance for the fixed set power
        #self.set_power_tol = self.set_power.val*self.set_power_tol_percent.val
        #
        
        #################################################
        ###########Initial setup before scanning
        
        ####Start Pump OPO, and open the desired output port
        ####Set wavelength to initial values
        ####Wait until system status OK
        if self.output_port.val=='OPO':
            print ('Err: OPO Not Implemented')
            
                
        if self.output_port.val == 'Pump':
            print('!!!Use Pump Main Beam')
            ########Do not pump opo
            self.opo_hw.pump_opo_off()
            print('Stop pumping OPO')
            #######close unused ports
            self.opo_hw.opo_out_shutter_close()
            print('Closing OPO output shutter')
            self.opo_hw.pump_SHG_off()
            print('Closing pump SHG')
            self.opo_hw.opo_SHG_off()  ###Note: setting opo_SHG off will simultaneously set OPO out shutter off!
            print('Closing OPO SHG')
            ###################Open Pump Output Shutter
            self.opo_hw.pump_out_shutter_open()
            print('Opening pump output shutter')
            ######### Set Main Beam to Initial Wavelength
            self.laser_dev.write_wavelength(_lambda=wl_now)
            print('Setting initial pump main beam wavelength')
            main_beam_tuning_wait_time = 5
            time.sleep(main_beam_tuning_wait_time)
            
        if self.output_port.val == 'Pump Align':
            print('!!!Use Pump Alignment Mode')
            ########Do not pump opo
            self.opo_hw.pump_opo_off()
            print('Stop pumping OPO')
            #######close unused ports
            self.opo_hw.opo_out_shutter_close()
            print('Closing OPO output shutter')
            self.opo_hw.pump_SHG_off()
            print('Closing pump SHG')
            self.opo_hw.opo_SHG_off()  ###Note: setting opo_SHG off will simultaneously set OPO out shutter off!
            print('Closing OPO SHG')
            ###################Open Pump Output Shutter
            self.opo_hw.pump_out_shutter_open()
            print('Opening pump output shutter')
            
            
            ###################Entering Alignment Mode Here
            self.laser_dev.write_alignment_mode(enabled = True)
            time.sleep(0.3)
            self.laser_dev.write_shutter(_open=True)
            time.sleep(0.3)
            print('Entering Alignment Mode and Opening Front Panel Shutter')
            ######### Set Alignment Mode to Initial Wavelength
            self.laser_dev.write_alignment_mode_wavelength(_lambda=wl_now)
            print('Setting initial alignment mode wavelength')
            align_mode_tuning_wait_time = 5
            time.sleep(align_mode_tuning_wait_time)
            
        if self.output_port.val == 'Pump SHG':
            print('Err: Pump SHG output port is not implemented')
            
        if self.output_port.val == 'OPO SHG':
            print('Err: OPO SHG Not Implemented')

    
        #######Read initial powermeter reading
        self.current_pm_reading = 1000.0 * self.pm_dev.measure_power() #read the pm power in unit of mW
        print('Initial pm power (mW): {}'.format(self.current_pm_reading))
                
    
        N_wl = self.wls_range.shape[0] #number of wavelegnth to scan
        self.iwl = int(0) #index of current wavelength
        print ('Start Photocurrent Scanning...')
        Scan_start_time = time.time()
        ########### Start PLE Scanning Main Loop
        while not ( (self.interrupt_measurement_called) or (self.iwl>N_wl-1) ):
            try:

                ##################################################################################
                ################Start wavelenth scan
                
                ##################################################################################    
                #########Set the excitation wavelength and Tune the laser
                wl_now = self.wls_range[self.iwl]
                    
                if self.output_port.val == 'OPO': 
                    print('OPO Not Implemented')

                if self.output_port.val == 'Pump':
                    print('!!!Using Pump Main Beam')
                    self.laser_dev.write_wavelength(_lambda=wl_now)
                    print('Setting pump main beam wavelength to {} nm'.format(wl_now))
                    self.laser_current_stat = self.laser_dev.read_tuning_status()
                    time0 = time.time()
                    wait_time = time.time()-time0
                    dead_time = 90 ##seconds
                    while ( (self.laser_current_stat != 'Ready') and (wait_time < dead_time) ):
                        try:
                            laser_current_stat1 = self.laser_dev.read_tuning_status()
                            print ('Laser status first reading is {}'.format(laser_current_stat1))
                            time.sleep(0.5)
                            laser_current_stat2 = self.laser_dev.read_tuning_status()
                            print ('Laser status second reading is {}'.format(laser_current_stat2))
                            time.sleep(0.5)
                            laser_current_stat3 = self.laser_dev.read_tuning_status()
                            print ('Laser status third reading is {}'.format(laser_current_stat3))
                            time.sleep(0.5)
                            #######Note: sometimes OPO status flash between Tuning and OK, so we need to check three consecutive "OK"s to trust it.
                            if (laser_current_stat1 == 'Ready' and laser_current_stat2 == 'Ready' and laser_current_stat3 == 'Ready' ):
                                self.laser_current_stat =  self.laser_dev.read_tuning_status()
                            else:
                                self.laser_current_stat = 'Not Stably Ready'
                            
                            wait_time = time.time()-time0
                            print('Tuning Laser to wavelength {}nm. Time elapsed {}s.'.format(wl_now, wait_time))
                        except Exception as err:
                            self.log.error('Failed to set laser wavelength to {}nm: {}'.format(wl_now, err))
                            raise(err)
                    
                    ###########Handle the case when laser doesn't set to Ready
                    if wait_time>dead_time-1:
                        print('Could not set laser wavelength to {}nm, status is no Ready'.format(wl_now))
                        self.ext_FLAG[self.iwl] = True ###FLAG == 1, means opo status is not OK
                    ################Read in the current main beam wls info    
                    self.ext_wls_range[self.iwl]     =  self.laser_dev.read_wavelength()   #can also use: self.opo_dev.read_OPO_wavelength()
                    self.ext_wls_linewidth[self.iwl] =  self.opo_dev.read_OPO_bandwidth() ###Will this still work? Lets check
                
                if self.output_port.val == 'Pump Align':
                    print('!!!Using Pump Align Mode')
                    self.laser_dev.write_alignment_mode_wavelength(_lambda=wl_now)
                    time.sleep(0.1)
                    print('Setting align mode wavelength to {} nm'.format(wl_now))
                    self.laser_current_stat = self.laser_dev.read_tuning_status()
                    time0 = time.time()
                    wait_time = time.time()-time0
                    dead_time = 90 ##seconds
                    
                    time.sleep(1)
                    
                    while ( (self.laser_current_stat != 'Ready') and (wait_time < dead_time) ):
                        try:
                            laser_current_stat1 = self.laser_dev.read_tuning_status()
                            print ('Laser status first reading is {}'.format(laser_current_stat1))
                            time.sleep(0.5)
                            laser_current_stat2 = self.laser_dev.read_tuning_status()
                            print ('Laser status second reading is {}'.format(laser_current_stat2))
                            time.sleep(0.5)
                            laser_current_stat3 = self.laser_dev.read_tuning_status()
                            print ('Laser status third reading is {}'.format(laser_current_stat3))
                            time.sleep(0.5)
                            #######Note: sometimes OPO status flash between Tuning and OK, so we need to check three consecutive "OK"s to trust it.
                            if (laser_current_stat1 == 'Ready' and laser_current_stat2 == 'Ready' and laser_current_stat3 == 'Ready' ):
                                self.laser_current_stat =  self.laser_dev.read_tuning_status()
                            else:
                                self.laser_current_stat = 'Not Stably Ready'
                            
                            wait_time = time.time()-time0
                            print('Tuning Laser to wavelength {}nm. Time elapsed {}s.'.format(wl_now, wait_time))
                        except Exception as err:
                            self.log.error('Failed to set laser wavelength to {}nm: {}'.format(wl_now, err))
                            raise(err)
                    
                    ###########Handle the case when laser doesn't set to Ready
                    if wait_time>dead_time-1:
                        print('Could not set laser wavelength to {}nm, status is no Ready'.format(wl_now))
                        self.ext_FLAG[self.iwl] = True ###FLAG == 1, means opo status is not OK
                        
                    ############ Check Mode Lock
                    MLK = self.laser_dev.read_modelocked()   
                    print ('**********************Laser Modelock Status: {}'.format(MLK))    
                    ################Read in the current main beam wls info    
                    self.ext_wls_range[self.iwl]     =  self.laser_dev.read_alignment_mode_wavelength()   #can also use: self.opo_dev.read_OPO_wavelength()
                    self.ext_wls_linewidth[self.iwl] =  self.opo_dev.read_OPO_bandwidth() ###Will this still work? Lets check    
                    
        
                if self.output_port.val == 'Pump SHG':
                    print('Err: Pump SHG output port is not implemented')
        
                if self.output_port.val == 'OPO SHG':
                    print('Err: OPO SHG Not Implemented')

                     
                
                
                
                
                
                ###############################################################
                ############## Regulate excitation power based on constant photocurrent
               
                #### Read the excitation power
                self.pm_dev.set_wavelength(wl=wl_now)
                self.pm_hw.read_from_hardware() 
                self.current_pm_reading = self.powermeter_avg_reading(N_read=3) #in mW, read 3 times and take average
                self.current_photon_flux = self.current_pm_reading*wl_now #photon flux in a.u.
                
                
                #### Read the Isd: Photocurrent = Light On - Light Off
                self.current_Iph = self.Iph_avg_reading(N_read = N_I_read) 
                
                ##########Regulate power if desired
                #print ('*****Check self.power_regulation: {}'.format(self.power_regulation))
                if self.constant_Iph.val==True:
                    
                    power_reg_time0 = time.time()
                    power_reg_time = time.time()-power_reg_time0
                    
                    self.set_constant_Iph_tol = self.set_constant_Iph.val*self.set_Iph_tol_percent.val ##note: in [nA]
                    
                    while ( (np.abs(self.current_Iph - self.set_constant_Iph.val) > self.set_constant_Iph_tol ) and (power_reg_time < self.power_reg_deadtime.val) ):
                        self.current_Iph = self.Iph_avg_reading(N_read=N_I_read) # in [nA]

                        ####Determine wheter coarse or fine movement of ND wheel should be used
                        if (np.abs(self.current_Iph - self.set_constant_Iph.val) > 10.0*self.set_constant_Iph_tol):
                            pw_step_to_use = self.pw_move_steps.val*10
                            print ('Use coarse step')
                        else:
                            pw_step_to_use = self.pw_move_steps.val
                            print ('Use fine step')
                        
                        ###############
                        ###############################Note: here assuming higher laser power gives higher photocurrent
                        if self.current_Iph > self.set_constant_Iph.val:
                            self.pw_dev.write_steps_and_wait(-1.0*pw_step_to_use)
                            time.sleep(0.1)
                        if self.current_Iph < self.set_constant_Iph.val:
                            self.pw_dev.write_steps_and_wait(pw_step_to_use)
                            time.sleep(0.1)
                        
                        power_reg_time = time.time()-power_reg_time0
                            
                        #self.current_pm_reading = self.powermeter_avg_reading(N_read=3) #in mW
                        #self.current_photon_flux = self.current_pm_reading*wl_now
                        
                        self.current_Iph = self.Iph_avg_reading(N_read = N_I_read) # in A
                        
                        print ('***********Regulating excitation power at {}nm. Current Iph {}A. Time elapsed: {}s'.format(wl_now, self.current_Iph, power_reg_time) )
                    
                    if power_reg_time > self.power_reg_deadtime.val:
                        print ('*********Failed to regulate power at wavelength of {}nm after {}s'.format(wl_now, self.power_reg_deadtime))
                

                    
                ########### Register the current reading on the powermeter
                self.current_pm_reading = self.powermeter_avg_reading(N_read=N_P_read) #in mW
                self.current_photon_flux = self.current_pm_reading*wl_now
                self.current_Iph = self.Iph_avg_reading(N_read = N_I_read)
                
                self.ext_power[self.iwl] = self.current_pm_reading
                self.ext_flux[self.iwl] = self.current_photon_flux
                self.I_lightOFF[self.iwl] = self.Isd_avg_reading(N_read=N_I_read)
                self.photocurrent[self.iwl] = self.current_Iph
                self.ext_power_after_exposure[self.iwl] = self.powermeter_avg_reading(N_read=N_P_read)

                
                
                ##############
                self.iwl += 1
                    

                
            except Exception as err:
                self.log.error('Failed to run Photocurrent scan {}'.format(err))
                raise(err)
            
            finally:
                print ('One acquisition done at wavelength of {}nm'.format(wl_now))
                
                
        Scan_run_time = time.time()-Scan_start_time    
        print ('Photocurrent scanning finished after {} seconds'.format(Scan_run_time))
        
        
        #################################
        #### Disable source
        self.keithley_dev.ramp_source_voltage(target_voltage = 0, steps=10, pause=0.2)
        self.keithley_dev.disable_source()
        
        
        ###############Close all shutters
        self.opo_hw.opo_out_shutter_close()
        print('Closing OPO output shutter')
        self.opo_hw.pump_out_shutter_close()
        print('Closing pump output shutter')
        self.opo_hw.opo_SHG_off()
        print('Closing OPO SHG')
        self.opo_hw.pump_SHG_off()
        print('Closing pump SHG')
        
        if self.output_port.val == 'Pump Align':

            self.laser_dev.write_alignment_mode_wavelength(_lambda = 760)
            time.sleep(0.2)
            self.laser_dev.write_alignment_mode(enabled=False)
            time.sleep(0.2)
            self.laser_dev.write_shutter(_open=True)
            
        ##############################################################################
        ########Save H5 files after all sacnnings are done
        ####Note: the h5 saving process takes about 30ms per spectra

        if self.settings['save_h5']:
            self.t0 = time.time()
            self.h5_file = h5_io.h5_base_file(self.app, measurement=self )
            self.h5_file.attrs['time_id'] = self.t0
            H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
                    
            #create h5 data arrays
            #H['ems_wls']           = self.ems_wls_now
            H['ext_wls_range']     = self.ext_wls_range
            H['ext_power']         = self.ext_power
            #H['ext_power_before_opening_shutter']         = self.ext_power
            H['ext_power_after_exposure']   = self.ext_power_after_exposure
            #H['ext_power_before_exposure'] = self.ext_power_before_exposure
            H['ext_flux']          = self.ext_flux
            H['ext_wls_linewidht'] = self.ext_wls_linewidth
            H['ext_FLAG']          = self.ext_FLAG
            H['photocurrent']      = self.photocurrent
            H['I_lightOFF']        = self.I_lightOFF
            #H['ems_specs']         = self.ems_specs
            H['Vsd']               = self.Vsd.val
            
#             if self.read_CCD_image.val == True:
#                 H['ems_image']         = self.ems_image
#                 
#             H['background_spec']   = self.ems_intensity_background
                    
            self.h5_file.close()




    def powermeter_avg_reading(self, N_read=3):
        #N_read = 3
        pw_reading = 0.0
        for i_read in np.arange(N_read):
            pw_reading += 1000.0 * self.pm_dev.measure_power() ##in mW
            time.sleep(0.1)
        pm_avg_reading = pw_reading/N_read
        return  pm_avg_reading # in mW
    

    def Isd_avg_reading(self, N_read):
        ###Enable source
        #self.keithley_dev.set_auto_range()
        #self.keithley_dev.enable_source()
        #time.sleep(0.1)
        
        Isd_reading = 0.0
        for i_read in np.arange(N_read):
            
            print ('Isd reading: {}[A]'.format(self.keithley_dev.read_current() ) )
            
            temp = self.keithley_dev.read_current() # in A
            
            Isd_reading += temp
            time.sleep(0.1)
        Isd_avg_reading = Isd_reading/N_read
        
        ###Disable source
        #self.keithley_dev.disable_source()
        #time.sleep(0.1)
        
        ####Note: return current in [nA]
        return Isd_avg_reading*1e9
    
    def Iph_avg_reading(self, N_read):
        ##################################
        ######## Turn off shutter, measure I_light_off
        ######## Turn on shutter, measure I_light_on
        ######## Subtract, get I photocurrent
        self.ext_shutter_hw.move_fwd() #close excitation shutter
        time.sleep(0.4)
        current_I_light_off = self.Isd_avg_reading(N_read) # in [nA]
        self.ext_shutter_hw.move_bkwd() #open excitation shutter 
        time.sleep(0.4)
        current_I_light_on = self.Isd_avg_reading(N_read) # in [nA]
        self.ext_shutter_hw.move_fwd() #close excitation shutter
        current_Iph = current_I_light_on - current_I_light_off 
        
        ###Note: return current in [nA]
        return current_Iph
        

        
    def update_display(self):
        #if hasattr(self, 'ems_wls_now') and hasattr(self, 'iwl'):
        #    self.emission_plot_line.setData(x=self.ems_wls_now, y=self.ems_intensity_now)
        if hasattr(self, 'photocurrent') and hasattr(self, 'iwl'):
            self.photocurrent_plot_line.setData(x=self.ext_wls_range[0:self.iwl], y=self.photocurrent[0:self.iwl])
        if hasattr(self, 'ext_power') and hasattr(self, 'iwl'):
            self.excitation_power_plot_line.setData(x=self.ext_wls_range[0:self.iwl], y=self.ext_power[0:self.iwl])
            #self.excitation_power_plot_line1.setData(x=self.ext_wls_range[0:self.iwl], y=self.ext_power_before_exposure[0:self.iwl])
        
            