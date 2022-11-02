from ScopeFoundryHW.nidaqmx.galvo_mirrors.galvo_mirror_2d_slow_scan import GalvoMirror2DSlowScan
import time


class GalvoMirrorAPDScanMeasure(GalvoMirror2DSlowScan):

    name = 'galvo_mirror_2D_apd_scan'

    def __init__(self, app):
        GalvoMirror2DSlowScan.__init__(self, app)

    def setup(self):
        GalvoMirror2DSlowScan.setup(self)
        self.stage = self.app.hardware['galvo_mirrors']

        self.target_range = 0.050e-3  # um
        self.slow_move_timeout = 10.  # sec

    def pre_scan_setup(self):
        return
        self.apd = self.app.hardware['apd_counter']
        if self.settings['save_h5']:
            self.count_rate_map_h5 = self.h5_meas_group.create_dataset('count_rate_map',
                                                                       shape=self.scan_shape,
                                                                       dtype=float,
                                                                       compression='gzip')

    def collect_pixel(self, pixel_num, k, j, i):
        print(k,j, i)
        time.sleep(0.1)
        return
        time.sleep(self.apd.settings['int_time'])
        count_rate = self.apd.settings.count_rate.read_from_hardware()
        
        self.display_image_map[k, j, i] = count_rate
        if self.settings['save_h5']:
            self.count_rate_map_h5[k, j, i] = count_rate
