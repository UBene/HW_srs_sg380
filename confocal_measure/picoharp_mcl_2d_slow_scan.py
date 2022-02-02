from __future__ import print_function, absolute_import, division
from ScopeFoundryHW.mcl_stage import MCLStage2DSlowScan

import numpy as np
import time
import pyqtgraph as pg
from ScopeFoundryHW.mcl_stage.mcl_stage_slowscan import MCLStage3DStackSlowScan

class Picoharp_MCL_2DSlowScan(MCLStage2DSlowScan):
    
    name = 'Picoharp_MCL_2DSlowScan'
    
    def pre_scan_setup(self):
        #hardware 
        self.picoharp_hw = self.app.hardware['picoharp']
        ph = self.picoharp_hw.picoharp # low level hardware
        
        #scan specific setup
        
        # create data arrays
        
        self.num_hist_chans = self.picoharp_hw.calc_num_hist_chans()

        time_trace_map_shape = self.scan_shape + (self.num_hist_chans,)
        self.time_trace_map = np.zeros(time_trace_map_shape, dtype=float)
        
        
        self.time_trace_map_h5 = self.h5_meas_group.create_dataset('time_trace_map', 
                                                                   shape=time_trace_map_shape,
                                                                   dtype=float, 
                                                                   compression='gzip')
        
        self.time_array = self.h5_meas_group['time_array'] = ph.time_array[0:self.num_hist_chans]*1e-3
        self.elapsed_time = self.h5_meas_group['elapsed_time'] = np.zeros(self.scan_shape, dtype=float)
        
        #self.app.settings_auto_save()
        

        # pyqt graph
        self.initial_scan_setup_plotting = True


        # set up experiment
        # experimental parameters already connected via LoggedQuantities
        
        # open shutter 
        # self.gui.shutter_servo_hc.shutter_open.update_value(True)
        # time.sleep(0.5)
        

        
    def post_scan_cleanup(self):
        # close shutter 
        #self.gui.shutter_servo_hc.shutter_open.update_value(False)
        pass
    
    def collect_pixel(self, pixel_num, k, j, i):
        
        # collect data
        print('Picoharp_MCL_2DSlowScan', 'collect_pixel', pixel_num, k, j, i)
        t0 = time.time()

        #hist_data, elapsed_time = self.read_picoharp_histogram()
        
        ph = self.picoharp_hw.picoharp
        ph.start_histogram()
        while not ph.check_done_scanning():
            self.picoharp_hw.settings.count_rate0.read_from_hardware()
            self.picoharp_hw.settings.count_rate1.read_from_hardware()
            if self.picoharp_hw.settings['Tacq'] > 0.2:
                ph.read_histogram_data()
            time.sleep(0.005) #self.sleep_time)  
        ph.stop_histogram()
        #ta = time.time()
        ph.read_histogram_data()

        hist_data = ph.histogram_data
        elapsed_time = ph.read_elapsed_meas_time()
        
        # store in arrays
        self.time_trace_map[k,j,i, :] = hist_data[0:self.num_hist_chans]
        self.time_trace_map_h5[k,j,i, :] = hist_data[0:self.num_hist_chans]
        
        self.elapsed_time[k,j,i] = elapsed_time

        # display count-rate
        self.display_image_map[k,j,i] = hist_data[0:self.num_hist_chans].sum() * 1.0/elapsed_time
        
        import datetime
        print('pixel',  datetime.timedelta(seconds=(self.Npixels - pixel_num)*elapsed_time*1e-3), 'left')
        
        print( 'pixel done' )
    
    def read_picoharp_histogram(self):
        print("asdf")

        ph = self.picoharp_hw.picoharp

        ph.start_histogram()

        while not ph.check_done_scanning():
            if self.picoharp_hw.settings['Tacq'] > 200:
                ph.read_histogram_data()
            time.sleep(0.005) #self.sleep_time)  
        ph.stop_histogram()
        #ta = time.time()
        ph.read_histogram_data()

        return ph.histogram_data, ph.read_elapsed_meas_time()

        
    def update_display(self):
        MCLStage2DSlowScan.update_display(self)
        
        # setup lifetime window
        if not hasattr(self, 'lifetime_graph_layout'):
            self.lifetime_graph_layout = pg.GraphicsLayoutWidget()
            self.lifetime_plot = self.lifetime_graph_layout.addPlot()
            self.lifetime_plotdata = self.lifetime_plot.plot()
            self.lifetime_plot.setLogMode(False, True)
        self.lifetime_graph_layout.show()
        
        kk, jj, ii = self.current_scan_index
        ph = self.picoharp_hw.picoharp
        self.lifetime_plotdata.setData(self.time_array,  1+ph.histogram_data[0:self.num_hist_chans])
        
class Picoharp_MCL_3DSlowScan(MCLStage3DStackSlowScan):
    
    name = 'Picoharp_MCL_3DSlowScan'
    
    def pre_scan_setup(self):
        #hardware 
        self.picoharp_hw = self.app.hardware['picoharp']
        ph = self.picoharp_hw.picoharp # low level hardware
        
        #scan specific setup
        
        # create data arrays
        
        cr0 = self.picoharp_hw.settings.count_rate0.read_from_hardware()
        rep_period_s = 1.0/cr0
        time_bin_resolution = self.picoharp_hw.settings['Resolution']*1e-12
        self.num_hist_chans = int(np.ceil(rep_period_s/time_bin_resolution))

        time_trace_map_shape = self.scan_shape + (self.num_hist_chans,)
        self.time_trace_map = np.zeros(time_trace_map_shape, dtype=float)
        
        
        self.time_trace_map_h5 = self.create_h5_framed_dataset(name='time_trace_map', single_frame_map=self.time_trace_map)
        
        self.time_array = self.h5_meas_group['time_array'] = ph.time_array[0:self.num_hist_chans]*1e-3
        
        self.elapsed_time = np.zeros(self.scan_shape, dtype=float)
        self.elapsed_time_h5 = self.create_h5_framed_dataset('elasped_time', self.elapsed_time)
        
        #self.app.settings_auto_save()
        
        # pyqt graph
        #self.initial_scan_setup_plotting = True

        
    def post_scan_cleanup(self):
        # close shutter 
        #self.gui.shutter_servo_hc.shutter_open.update_value(False)
        pass
    
    def collect_pixel(self, pixel_num, frame_i, k, j, i):
        
        # collect data
        print(pixel_num, frame_i, k, j, i)
        t0 = time.time()
        
        hist_data, elapsed_time = Picoharp_MCL_2DSlowScan.read_picoharp_histogram(self)

        # store in arrays
        self.time_trace_map[k,j,i, :] = hist_data[0:self.num_hist_chans]
        self.time_trace_map_h5[frame_i,k,j,i, :] = hist_data[0:self.num_hist_chans]
        
        self.elapsed_time[k,j,i] = elapsed_time
        self.elapsed_time_h5[frame_i, k,j,i] = elapsed_time

        # display count-rate
        self.display_image_map[k,j,i] = hist_data[0:self.num_hist_chans].sum() * 1.0/elapsed_time
        
        print( 'pixel done' )
        
    def on_new_frame(self, frame_i):
        MCLStage3DStackSlowScan.on_new_frame(self, frame_i)
        self.extend_h5_framed_dataset(self.time_trace_map_h5, frame_i)
        self.extend_h5_framed_dataset(self.elapsed_time_h5, frame_i)
        
    def on_end_frame(self, frame_i):
        MCLStage3DStackSlowScan.on_end_frame(self, frame_i)
        self.h5_file.flush()
        
    def update_display(self):
        MCLStage2DSlowScan.update_display(self)
    