import numpy as np
from ScopeFoundryHW.mcl_stage.mcl_stage_slowscan import MCLStage2DSlowScan
from ScopeFoundry.scanning import BaseRaster2DSlowScan
import time



class AndorHyperSpec2DScanBase(BaseRaster2DSlowScan):
    '''
    Base class for a hyper-spectral scan with an Andor CCD.
    Derived class requires second inheritance of a <confocal_measure.BaseRaster2DSlowScan> 
    derivative. For example:
        `class AndorHyperSpec2DScan(AndorHyperSpec2DScanBase, MCLStage2DSlowScan):
            ...`
    Note: Order of Inheritance matters!            
    '''

    name = "andor_base_hyperspec_scan"

    
    def scan_specific_setup(self):
        # Measurement
        self.andor_ccd_readout = self.app.measurements['andor_ccd_readout']

        # add to base ui
        self.andor_ccd_hw = self.app.hardware['andor_ccd']
        device_ui = self.andor_ccd_hw.settings.New_UI(include=[
            'connected','exposure_time','temperature', 'ccd_status'])
        self.ui.device_details_layout.addWidget(device_ui)

    def pre_scan_setup(self):
        self.andor_ccd_readout.settings['acquire_bg'] = False
        self.andor_ccd_readout.settings['continuous'] = False
        self.andor_ccd_readout.settings['save_h5'] = False
        time.sleep(0.01)
    
    def collect_pixel(self, pixel_num, k, j, i):
        print("collect_pixel", pixel_num, k,j,i)
        # self.andor_ccd_readout.interrupt_measurement_called = self.interrupt_measurement_called

        self.andor_ccd_readout.settings['continuous'] = False
        self.andor_ccd_readout.settings['save_h5'] = False
                
        self.start_nested_measure_and_wait(self.andor_ccd_readout,
                                           nested_interrupt=False)
        
        if pixel_num == 0:
            self.log.info("pixel 0: creating data arrays")
            spec_map_shape = self.scan_shape + self.andor_ccd_readout.spectra_data.shape
            
            self.spec_map = np.zeros(spec_map_shape, dtype=np.float)
            self.spec_map_h5 = self.h5_meas_group.create_dataset(
                                 'spec_map', spec_map_shape, dtype=np.float)

            self.wls = np.array(self.andor_ccd_readout.wls)
            self.h5_meas_group['wls'] = self.wls

        # store in arrays
        spec = self.andor_ccd_readout.spectra_data
        self.spec_map[k,j,i,:] = spec
        if self.settings['save_h5']:
            self.spec_map_h5[k,j,i,:] = spec
  
        self.display_image_map[k,j,i] = spec.sum()


    def post_scan_cleanup(self):
        self.andor_ccd_readout.settings['save_h5'] = True


class AndorHyperSpec2DScan(AndorHyperSpec2DScanBase, MCLStage2DSlowScan):
    
    name = "andor_hyperspec_scan"
    
    def setup(self):
        MCLStage2DSlowScan.setup(self)
    
    def scan_specific_setup(self):
        AndorHyperSpec2DScanBase.scan_specific_setup(self)
        
    def pre_scan_setup(self):
        AndorHyperSpec2DScanBase.pre_scan_setup(self)
        MCLStage2DSlowScan.pre_scan_setup(self)
        
    def post_scan_cleanup(self):
        AndorHyperSpec2DScanBase.post_scan_cleanup(self)
        MCLStage2DSlowScan.post_scan_cleanup(self)
        
    def collect_pixel(self, pixel_num, k, j, i):
        MCLStage2DSlowScan.collect_pixel(self, pixel_num, k, j, i)
        AndorHyperSpec2DScanBase.collect_pixel(self, pixel_num, k, j, i)

    def update_display(self):
        MCLStage2DSlowScan.update_display(self)
