from ScopeFoundryHW.mcl_stage import MCLStage2DSlowScan
import numpy as np
from ScopeFoundryHW.mcl_stage.mcl_stage_slowscan import MCLStage3DStackSlowScan
import time

class APD_MCL_2DSlowScan(MCLStage2DSlowScan):
    
    name = 'APD_MCL_2DSlowScan'
    
    def pre_scan_setup(self):
        MCLStage2DSlowScan.pre_scan_setup(self)
        self.apd_counter_hw = self.app.hardware['apd_counter']
        self.apd_count_rate = self.apd_counter_hw.settings.count_rate


        #scan specific setup
        
        # create data arrays
        self.count_rate_map = np.zeros(self.scan_shape, dtype=float)
        if self.settings['save_h5']:
            self.count_rate_map_h5 = self.h5_meas_group.create_dataset('count_rate_map', 
                                                                       shape=self.scan_shape,
                                                                       dtype=float, 
                                                                       compression='gzip')

    def collect_pixel(self, pixel_num, k, j, i):
        # collect data
        #print(pixel_num, k, j, i)
        time.sleep(self.apd_counter_hw.settings['int_time'])
        self.apd_count_rate.read_from_hardware()

        # store in arrays
        self.count_rate_map[k,j,i] = self.apd_count_rate.val
        if self.settings['save_h5']:
            self.count_rate_map_h5[k,j,i] = self.apd_count_rate.val
  
        self.display_image_map[k,j,i] = self.apd_count_rate.val
        
        
        
class APD_MCL_3DSlowScan(MCLStage3DStackSlowScan):
    
    name = 'APD_MCL_3DSlowScan'
    
    def pre_scan_setup(self):
        #hardware 
        self.apd_counter_hc = self.app.hardware.apd_counter
        self.apd_count_rate = self.apd_counter_hc.settings.count_rate


        #scan specific setup
        
        # create data arrays
        self.count_rate_map = np.zeros(self.scan_shape, dtype=float)
        if self.settings['save_h5']:
            self.count_rate_map_h5 = self.create_h5_framed_dataset('count_rate_map', self.count_rate_map)
        
        # open shutter 
        # self.gui.shutter_servo_hc.shutter_open.update_value(True)
        # time.sleep(0.5)
    
    def post_scan_cleanup(self):
        # close shutter 
        #self.gui.shutter_servo_hc.shutter_open.update_value(False)
        pass
    
    def collect_pixel(self, pixel_num, frame_i, k, j, i):
        # collect data
        print(pixel_num, frame_i, k, j, i)
        self.apd_count_rate.read_from_hardware()
                          
        # store in arrays
        self.count_rate_map[k,j,i] = self.apd_count_rate.val
        if self.settings['save_h5']:
            self.count_rate_map_h5[frame_i, k,j,i] = self.apd_count_rate.val
  
        self.display_image_map[k,j,i] = self.apd_count_rate.val
    