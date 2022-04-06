from ScopeFoundryHW.nidaqmx.galvo_mirrors.galvo_mirror_2d_slow_scan import GalvoMirror2DSlowScan


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
        self.apd = self.app.hardware['apd_counter']
        if self.settings['save_h5']:
            self.count_rate_map_h5 = self.h5_meas_group.create_dataset('count_rate_map',
                                                                       shape=self.scan_shape,
                                                                       dtype=float,
                                                                       compression='gzip')

    def collect_pixel(self, pixel_num, k, j, i):
        count_rate = self.apd.settings.count_rate.read_from_hardware()
        
        self.display_image_map[k, j, i] = count_rate
        if self.settings['save_h5']:
            self.count_rate_map_h5[k, j, i] = count_rate

            
# class PicoharpApdScan(AttoCube2DSlowScan):
#
#     name = 'apd_scan'
#
#
#     def setup(self):
#         AttoCube2DSlowScan.setup(self)
#         self.Tacq = self.settings.New('Tacq', dtype = float, initial = 1.0, vmin=0.1)
#         self.set_details_widget(self.settings.New_UI(include=['Tacq']))
#
#
#
#     def pre_scan_setup(self):
#         self.ph = self.app.hardware['picoharp']
#
#         if self.settings['save_h5']:
#             self.count_rate_map_h5 = self.h5_meas_group.create_dataset('count_rate_map', 
#                                                                        shape=self.scan_shape,
#                                                                        dtype=float, 
#                                                                        compression='gzip')
#
#
#     def collect_pixel(self, pixel_num, k, j, i):
#         if self.ph.settings.debug_mode.val:
#             print(self.name, "collecting pixel_num:",pixel_num)
#
#         t0 = t1 = time.time()
#
#         avg_count_rate = 0
#         n = 0 
#
#         while not self.interrupt_measurement_called and t1-t0 <= self.Tacq.val:
#             time.sleep(0.100) # 100ms gate time
#             #avg_count_rate += self.ph.settings.count_rate1.read_from_hardware()
#             avg_count_rate += self.ph.settings.count_rate1.val
#             n += 1
#             t1 = time.time()
#
#
#         avg_count_rate /= n
#
#         self.display_image_map[k,j,i] = avg_count_rate
#         if self.settings['save_h5']:
#             self.count_rate_map_h5[k,j,i] = avg_count_rate
#
#
#     def post_scan_cleanup(self):
#         del self.count_rate_map_h5
#
#
