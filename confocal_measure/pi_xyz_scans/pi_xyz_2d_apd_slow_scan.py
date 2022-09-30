from .pi_xyz_2d_slow_scan import PIXYZ2DSlowScan
import time


class PIXYZ2DAPDSlowScan(PIXYZ2DSlowScan):

    name = 'apd_2d_map'

    def setup(self):
        PIXYZ2DSlowScan.setup(self)
        self.stage = self.app.hardware['PI_xyz_stage']

        self.target_range = 0.050e-3  # um
        self.slow_move_timeout = 10.  # sec

    def pre_scan_setup(self):
        self.apd = self.app.hardware['apd_counter']
        if self.settings['save_h5']:
            self.count_rate_map_h5 = self.h5_meas_group.create_dataset('count_rate_map',
                                                                       shape=self.scan_shape,
                                                                       dtype=float,
                                                                       compression='gzip')

    def collect_pixel(self, pixel_num, k, j, i):
        time.sleep(2*self.apd.settings['int_time'])
        count_rate = self.apd.settings.count_rate.read_from_hardware()

        self.display_image_map[k, j, i] = count_rate
        if self.settings['save_h5']:
            self.count_rate_map_h5[k, j, i] = count_rate