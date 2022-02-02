import numpy as np
import time
from ScopeFoundryHW.mcl_stage.mcl_stage_slowscan import MCLStage2DSlowScan
 

class PolarizedHyperspecScanMeasure(MCLStage2DSlowScan):
    name = "polarized_hyperspec_scan"
    
    def scan_specific_setup(self):

        self.settings.New_Range('theta')        
        
        #Hardware
        self.stage = self.app.hardware['mcl_xyz_stage']
        self.winspec_hc= self.winspec_hw = self.app.hardware['winspec_remote_client']
        self.winspec_readout = self.app.measurements['winspec_readout']

    def pre_run(self):
        MCLStage2DSlowScan.pre_run(self)
                
    def pre_scan_setup(self):
        S = self.settings
        self.theta_target_positions = np.linspace(S['theta_min'],S['theta_max'],S['theta_num'],endpoint=True, dtype=float)
                
        self.winspec_readout.interrupt()
        print('Doing a quick dummy measurement')
        self.winspec_readout.settings['save_h5'] = False
        acq_time = self.winspec_hw.settings['acq_time']
        self.winspec_hw.settings['acq_time'] = 0.1
        self.winspec_readout.start()
        time.sleep(1)
        self.winspec_hw.settings['acq_time'] = acq_time
        
        #Reconnect to winspec (Clears Server Buffer)
        self.winspec_readout.winspec_hc.settings['connected'] = False
        time.sleep(0.2)
        self.winspec_readout.winspec_hc.settings['connected'] = True
        time.sleep(0.2)
                        
        #get useful logged quantities
        self.polarizer_target_position =  self.app.hardware['motorized_polarizer'].settings.get_lq('target_position')
        self.polarizer_position =  self.app.hardware['motorized_polarizer'].settings.get_lq('position')

        print("creating data arrays")
        spec_map_shape = (*self.scan_shape,*self.theta_target_positions.shape,self.winspec_readout.data.shape[-1])# size vec for saving matrix
        #self.spec_map = np.zeros(spec_map_shape, dtype=np.float)
        self.spec_map_h5 = self.h5_meas_group.create_dataset(
                         'polarized_hyperspec_map', spec_map_shape, dtype=np.float)# creating data set saving link
        self.theta_recorded_h5 = self.h5_meas_group.create_dataset(
                            'theta_recorded_on_last_pixel', self.theta_target_positions.shape, dtype=np.float)# creating data set saving link

        self.h5_meas_group.create_dataset('theta_target_positions', data=self.theta_target_positions)
        self.h5_file.flush()  

    def collect_pixel(self, pixel_num, k, j, i):
        print('current pixel (', j,i ,') of (', self.Nv.value-1, self.Nh.value-1,')')
        self.set_progress(pixel_num/(self.Nv.value*self.Nh.value)*100)  # updates progress bar
        
        if (pixel_num % 5) == 0:
            self.h5_file.flush()

        for p,theta in enumerate(self.theta_target_positions):
            if self.interrupt_measurement_called:
                break
            
            print('moving to angle', theta)
            self.polarizer_target_position.update_value(theta)
            self.start_nested_measure_and_wait(self.winspec_readout, start_time=0.5)           
            #self.spec_map[k,j,i,p,:] = self.winspec_readout.data.squeeze()# extra data picker
            self.spec_map_h5[k,j,i,p,:] = self.winspec_readout.data.squeeze()# direct saving matrix to hard drive using the created link
            self.theta_recorded_h5[p] = self.polarizer_position.value
            self.display_image_map[k,j,i] = self.winspec_readout.data.sum()# dumping the intensity pixel for the current scan            
            
                
        
    def post_scan_cleanup(self):   
        self.wavelength = self.winspec_readout.wls
        self.wavelength_h5 = self.h5_meas_group.create_dataset(
                               'wavelength', self.wavelength.shape, dtype=np.float)# creating data set saving link
        self.wavelength_h5[:] = self.wavelength[:]# direct saving wavelength vec to hard drive using the created link
        self.h5_file.flush()
        self.winspec_readout.settings['save_h5'] = True
    
    def update_display(self):
        MCLStage2DSlowScan.update_display(self)
        self.winspec_readout.update_display()            
            
        
    def setup_figure(self):
        super(MCLStage2DSlowScan, self).setup_figure()# calling/ operating the figure setup func of the ancester class
        self.set_details_widget(widget=self.settings.New_UI(
            include=['h_axis', 'v_axis','theta_min', 'theta_max', 'theta_num', 'theta_step']))# adding new panel daialogs of thata var only for scans measurments
