from ScopeFoundryHW.asi_stage.asi_stage_raster import ASIStage2DScan
import numpy as np
import time

class APD_ASI_2DSlowScan(ASIStage2DScan):
    
    name = 'APD_ASI_2DSlowScan'
    
    def pre_scan_setup(self):
        #hardware 
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
        
        
        # open shutter 
        # self.gui.shutter_servo_hc.shutter_open.update_value(True)
        # time.sleep(0.5)
        
    def post_scan_cleanup(self):
        # close shutter 
        #self.gui.shutter_servo_hc.shutter_open.update_value(False)
        pass
    
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
    