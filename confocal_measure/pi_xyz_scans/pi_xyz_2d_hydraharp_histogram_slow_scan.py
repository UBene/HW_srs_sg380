from .pi_xyz_2d_slow_scan import PIXYZ2DSlowScan
import numpy as np


class PIXYZ2DHydraharpHistogramSlowScan(PIXYZ2DSlowScan):
    
    name = 'hydraharp_histogram_2d_map'

    def __init__(self, app):
        PIXYZ2DSlowScan.__init__(self, app)        
        
    def setup(self):
        PIXYZ2DSlowScan.setup(self)
        self.stage = self.app.hardware['PI_xyz_stage']

        self.target_range = 0.050e-3  # um
        self.slow_move_timeout = 10.  # sec

    def collect_pixel(self, pixel_num, k, j, i):
        
        measure = self.app.measurements["hydraharp_histogram"]
        self.start_nested_measure_and_wait(measure, nested_interrupt=False)
                
        data = measure.data
        
        if pixel_num == 0:
            time_array = data['time_array']
            self.data_spape = (*self.scan_shape, len(time_array)) 
            if self.settings['save_h5']:
                self.spec_map_h5 = self.h5_meas_group.create_dataset('time_histogram',
                                                                   shape=self.data_spape,
                                                                   dtype=float,
                                                                   compression='gzip')
                self.h5_meas_group.create_dataset(
                    'time_array',
                    data=time_array
                    )

        hist = data['time_histogram']
        self.display_image_map[k, j, i] = np.sum(hist)
        if self.settings['save_h5']:
            self.spec_map_h5[k, j, i] = hist
