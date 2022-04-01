import time
from ScopeFoundryHW.ni_daq.measure.galvo_mirror_slow_scan import GalvoMirror2DSlowScan



class GalvoMirrorAPDScanMeasure(GalvoMirror2DSlowScan):
    
    name = 'galvo_mirror_2D_apd_scan'

    def __init__(self, app, use_external_range_sync=False, circ_roi_size=0.001):
        GalvoMirror2DSlowScan.__init__(self, app, h_limits=(-12.5,12.5), v_limits=(-12.5,12.5), h_unit="V", v_unit="V", 
                                      use_external_range_sync=use_external_range_sync,
                                      circ_roi_size=circ_roi_size)        
        
    def setup(self):
        self.stage = self.app.hardware['attocube_xyz_stage']
        self.target_range = 0.050e-3 # um
        self.slow_move_timeout = 10. # sec

        self.settings.New("h_axis", initial="x", dtype=str, choices=("x", "y", "z"))
        self.settings.New("v_axis", initial="y", dtype=str, choices=("x", "y", "z"))

    def pre_scan_setup(self):
        self.apd = self.app.hardware['apd_counter']

        if self.settings['save_h5']:
            self.count_rate_map_h5 = self.h5_meas_group.create_dataset('count_rate_map', 
                                                                       shape=self.scan_shape,
                                                                       dtype=float, 
                                                                       compression='gzip')


    def collect_pixel(self, pixel_num, k, j, i):
        count_rate = self.apd.settings.count_rate.read_from_hardware()
        
        self.display_image_map[k,j,i] = count_rate
        if self.settings['save_h5']:
            self.count_rate_map_h5[k,j,i] = count_rate



    def move_position_start(self, h,v):
        self.move_position_slow(h,v, 0, 0, timeout=30)



    def move_position_slow(self, h,v, dh,dv, timeout=10):
        # update target position
        self.stage.move_slow_x(h)
        self.stage.move_slow_y(v)
        

    def move_position_fast(self,  h,v, dh,dv):
        # Note implemented
        self.move_position_slow( h,v, dh,dv)



            
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
