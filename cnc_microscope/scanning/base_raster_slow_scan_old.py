from .base_raster_scan import BaseRaster2DScan
from ScopeFoundry import h5_io
import numpy as np
import time
import os
import pylab as pl

class BaseRaster2DSlowScan(BaseRaster2DScan):

    name = "base_raster_2Dslowscan"

    def run(self):
        S = self.settings
        
        
        #Hardware
        # self.apd_counter_hc = self.app.hardware_components['apd_counter']
        # self.apd_count_rate = self.apd_counter_hc.apd_count_rate
        # self.stage = self.app.hardware_components['dummy_xy_stage']
        #self.stage = self.app.hardware.PI_xyz_stage
        # Data File
        # H5

        # Compute data arrays
        self.t0 = time.time()
        self.pre_scan_setup()
        
        self.compute_scan_arrays()
        
        self.initial_scan_setup_plotting = True
        
        self.display_image_map = np.zeros(self.scan_shape, dtype=float)
        
        if self.settings['save_h5']:
            if self.settings['collect_apd']:
                self.name = 'PI_2DScan_APD'
            elif self.settings['collect_spectrum']:
                self.name = 'PI_2DScan_LIGHTFIELD'
            elif self.settings['collect_CCD_image']:
                self.name = 'PI_2DScan_CCD_Image'
            elif self.settings['collect_lifetime']:
                self.name = 'PI_2DScan_HYDRAHARP'
                
            self.h5_file = h5_io.h5_base_file(self.app, measurement=self)
            #self.h5_filename = self.h5_file.filename

            
            self.h5_file.attrs['time_id'] = self.t0
            H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
            
            
            #create h5 data arrays
            H['h_array'] = self.h_array
            H['v_array'] = self.v_array
            H['range_extent'] = self.range_extent
            H['corners'] = self.corners
            H['imshow_extent'] = self.imshow_extent
            H['scan_h_positions'] = self.scan_h_positions
            H['scan_v_positions'] = self.scan_v_positions
            #H['scan_slow_move'] = self.scan_slow_move
            H['scan_index_array'] = self.scan_index_array
                    
        try:
            # start scan
            self.pixel_i = 0
            
            ##################################################
            ##############for AF
            self.autofoc_pixel_i = 0 ###autofocuse pixel number register
            self.autofoc_timer = time.time()
            ##################################################
            ##################################################
            
            self.current_scan_index = self.scan_index_array[0]

            self.pixel_time = np.zeros(self.scan_shape, dtype=float)
            if self.settings['save_h5']:
                self.pixel_time_h5 = H.create_dataset(name='pixel_time', shape=self.scan_shape, dtype=float)            

            
            self.move_position_start(self.scan_h_positions[0], self.scan_v_positions[0])
                
            for self.pixel_i in range(self.Npixels):
                while self.interrupt_measurement_called: 
                    break                
                if self.interrupt_measurement_called: break
                
                i = self.pixel_i
                
                self.current_scan_index = self.scan_index_array[i]
                kk, jj, ii = self.current_scan_index
                
                h,v = self.scan_h_positions[i], self.scan_v_positions[i]
                
                if self.pixel_i == 0:
                    dh = 0
                    dv = 0
                else:
                    dh = self.scan_h_positions[i] - self.scan_h_positions[i-1] 
                    dv = self.scan_v_positions[i] - self.scan_v_positions[i-1] 
                
                #if self.scan_slow_move[i]:
                #    if self.interrupt_measurement_called: break
                #    self.move_position_slow(h,v, dh, dv)
                #    if self.settings['save_h5']:    
                #        self.h5_file.flush() # flush data to file every slow move
                #    #self.app.qtapp.ProcessEvents()
                #    time.sleep(0.01)
                #else:
                #    self.move_position_fast(h,v, dh, dv)
                    
                if self.interrupt_measurement_called: break    
                getattr(self, "move_position_%s" % self.speed.value)(h,v)
                
                if self.speed.value == "slow":
                    if self.settings['save_h5']:    
                        self.h5_file.flush() # flush data to file every slow move
                    #self.app.qtapp.ProcessEvents()
                    time.sleep(0.01)     
                
                
                self.pos = (h,v)
                # each pixel:
                # acquire signal and save to data array
                pixel_t0 = time.time()
                self.pixel_time[kk, jj, ii] = pixel_t0
                if self.settings['save_h5']:
                    self.pixel_time_h5[kk, jj, ii] = pixel_t0
                    
                self.collect_pixel(self.pixel_i, kk, jj, ii)
                S['progress'] = 100.0*self.pixel_i / (self.Npixels)
            
            
                ##############################################    
                ####Autofocus function 08/02/2018
                ###Note: collect this pixel first, then do autofoc, better for minimizing photobeaching
                if self.settings['autofoc_enable']:
                    if time.time() - self.autofoc_timer > self.autofoc_dt.value:
                        self.autofoc_timer = time.time()
                        self.autofoc_pixel_numbers = np.hstack( (self.autofoc_pixel_numbers, self.pixel_i) )
                        self.autofoc_coord_H = np.hstack( (self.autofoc_coord_H, h) )
                        self.autofoc_coord_V = np.hstack( (self.autofoc_coord_V, v) )
                        self.autofoc_coord_zbefore = np.hstack( (self.autofoc_coord_zbefore,  self.stage.settings.z_position.read_from_hardware()) )
                        
                        if self.settings['collect_apd']:
                            self.autofoc_tacq = self.app.hardware.apd_counter.settings.int_time.val/self.autofoc_tacq_ratio.val
                            #print('apd int time: {}'.format(self.app.hardware.apd_counter.settings.int_time.val)  )
                        elif self.settings['collect_spectrum']:
                            self.autofoc_tacq = self.app.hardware['lightfield'].settings.exposure_time.val/self.autofoc_tacq_ratio.val
                        
                        z_after = self.autofoc(z_step = 0.1, z_num = 12, 
                                               tacq   = self.autofoc_tacq,
                                               FixPix = self.autofoc_fix_pix.val,
                                               pix_H  = self.autofoc_pix_H.val,
                                               pix_V  = self.autofoc_pix_V.val,
                                               CCD_dark_noise = self.autofoc_CCD_dark_noise.val,
                                               APD_dark_noise = self.autofoc_APD_dark_noise.val,
                                               dummy  = False )
                        
                        self.autofoc_coord_zafter = np.hstack( (self.autofoc_coord_zafter, z_after) )
                        
                        #print ('Autofocus finished for the {}th time at time {} after scan starts'.format(self.autofoc_pixel_i, time.time()-self.t0))
                        
                        self.autofoc_pixel_i += 1
                        
                
                #############################################    
                    
                    
        except Exception as err:
            self.log.error('Failed to Scan {}'.format(err))
            raise(err)
        finally:
            #H.update(self.scan_specific_savedict())
            if self.settings['save_h5']:
                if self.settings['collect_apd']:
                    H['count_rate_map' ] = self.count_rate_map
                elif self.settings['collect_spectrum']:
                    H["wls"] = self.wls
                    H["spectra_map"] = self.spectra_map
                    H["integrated_spectra_map"] = self.integrated_spectra_map
                elif self.settings['collect_CCD_image']:
                    H["wls"] = self.wls
                    H["spectra_map"] = self.spectra_map
                    H["integrated_spectra_map"] = self.integrated_spectra_map
                    H["image_map"] = self.image_map
                    
            
            self.post_scan_cleanup()
            
            if hasattr(self, 'h5_file'):
                print('h5_file', self.h5_file)
                try:
                    self.h5_file.close()
                except ValueError as err:
                    self.log.warning('failed to close h5_file: {}'.format(err))
            #if not self.settings['continuous_scan']:
            #    break
        print(self.name, 'done')
        
        
    def autofoc(self, z_step=0.2, z_num=4, tacq=0.1, dummy=False, FixPix=False, pix_H=10, pix_V=10, CCD_dark_noise=600, APD_dark_noise=50):
        ######## 08/03/2018 Kaiyuan
        #z_step: each step of z movement for autofocusing in um
        #z_num: number of data points for z movement on each side
        #tacq: acquisition time for each z scanning acquisition. Expected to be shorter than normal acquisition time, to save time
        #
        ##Note: If this is a dark pixel (count~0), then disgard this autofocus pixel
        #Note: if using CCD, bin the CCD to 1 pixel for this purpose. Also need to uncheck correct background after chaging binning? 
        
        
        
        ###################### Define an inner function to be called
        def set_back_to_scanning_condition():
        ### Move back from the fixed autofoc position to scanning position
            coords = [None, None, None]
            ###back to [h,v] scanning position
            coords[self.ax_map[S['h_axis']]] = self.scan_h_positions[self.pixel_i]
            coords[self.ax_map[S['v_axis']]] = self.scan_v_positions[self.pixel_i]
            ###optimized z position
            coords[2] = z_after
            self.stage.move_pos_fast(*coords)
            
            print('z_before: {}, z_after: {}'.format(z_now, z_after))
            
        ### change integration time back
            if self.settings['collect_apd']:
                self.apd_counter_hw.int_time.val = tacq0
            if self.settings['collect_spectrum']:
                self.lf_hw.lightfield_dev.set_exposure_time(tacq0)
                self.lf_hw.lightfield_dev.set_correct_background(correct_bg_bool=True)
                
                self.lf_hw.custom_roi_xbinning.val = int(custom_roi_xbinning_original)
                self.lf_hw.custom_roi_ybinning.val = int(custom_roi_ybinning_original)
                self.lf_hw.set_custom_roi()
                
                
#                 self.lf_hw.lightfield_dev.set_custom_ROI(roi_dim_x  = self.lf_hw.custom_roi_x.value, 
#                                                          roi_dim_y  = self.lf_hw.custom_roi_y.value, 
#                                                          roi_width  = self.lf_hw.custom_roi_width.value, 
#                                                          roi_height = self.lf_hw.custom_roi_height.value, 
#                                                          roi_xbinning = custom_roi_xbinning_original, 
#                                                          roi_ybinning = custom_roi_xbinning_original)
        ##############################################################
        

        S = self.settings
        
        z_now = self.stage.settings.z_position.read_from_hardware()
        z_after = z_now
        
        #dark_count_percentile_threshold = 50
        
        #########################################################
        ### Move to a fixed position for autofocusing if desired
        if FixPix == True:
            #move to fix pixel for af as defined in h, v
            coords = [None, None, None]
            coords[self.ax_map[S['h_axis']]] = pix_H
            coords[self.ax_map[S['v_axis']]] = pix_V
            self.stage.move_pos_fast(*coords)
            
            h_now = pix_H
            v_now = pix_V
            
            x_AF = self.stage.settings.x_position.read_from_hardware()
            y_AF = self.stage.settings.y_position.read_from_hardware()
            print('Autofocusing at fixed pixel, stage moved to fixed pixel x={}, y={}'.format(x_AF, y_AF))
        else:
            h_now = self.scan_h_positions[self.pixel_i]
            v_now = self.scan_v_positions[self.pixel_i]
            
        #########################################################
        ##### Start autofocusing process
        if dummy==True:
            print ('dummy autofoc initiated at scanning coord H={}, V={}'.format(self.autofoc_coord_H[-1], self.autofoc_coord_V[-1]) )
            print ('zbefore: {}, zafter: {}'.format(self.autofoc_coord_zbefore, z_after) )
            
        else:    
            ##############################################################################
            ############Perform real autofocusing
            #print ('Autofoc initiated at scanning coord H={}, V={}'.format(self.autofoc_coord_H[-1], self.autofoc_coord_V[-1]) )
            
            z_scan_pos       = np.arange(z_now-z_num*z_step, z_now+(z_num+0.1)*z_step, z_step)
            z_scan_intensity = np.zeros(z_scan_pos.shape, float)
            z_scan_pos_fit   = np.arange(z_now-z_num*z_step, z_now+(z_num+0.1)*z_step, 0.1*z_step)
            
            
            ###########If the APD is used as detector
            if self.settings['collect_apd']:
                tacq0 = self.apd_counter_hw.int_time.val
                ###change to lower integration time for fast AF
                self.apd_counter_hw.int_time.val = tacq
                
                #print('tacq0: {}, tacq {}'.format(tacq0, tacq))
                
                ########Test if this is a dark pixel
                test_cts = self.apd_counter_hw.read_count_rate()  ##APD reading, in count rate, Hz
                #dark_count_threshold = np.percentile(self.count_rate_map[self.count_rate_map>0], dark_count_percentile_threshold)  ###Estimate the general dark count, as the 5th percentile in the previously-scanned intensity data
                #dark_threshold = np.min( [dark_count_threshold, 100] )
                dark_threshold = APD_dark_noise
                if test_cts < dark_threshold: ###The dark counts on MPD APD is unlikley to be larger than 100Hz. So we set a minimum bound here.
                    set_back_to_scanning_condition()
                    print ('*********Give up autofoc at dark autofoc pixel {}'.format(self.autofoc_pixel_i))
                    print ('*********Current count: {}, Threshold: {}'.format(test_cts, dark_threshold ))
                    return z_after
                
                for iz in np.arange(z_scan_pos.shape[0]):
                    z_scan = z_scan_pos[iz]
                    coords = [None, None, None]
                    coords[self.ax_map[S['h_axis']]] = h_now
                    coords[self.ax_map[S['v_axis']]] = v_now
                    coords[2] = z_scan
                    self.stage.move_pos_fast(*coords)
                    #t_apd0 = time.time()
                    #z_scan_intensity[iz] = self.apd_count_rate_lq.read_from_hardware()
                    z_scan_intensity[iz] = self.apd_counter_hw.read_count_rate()
                    #print('apd AF time {}'.format(time.time()-t_apd0) )

                
            ###########If the CCD spectrometer is used as detector   
            if self.settings['collect_spectrum']:
                
                if self.lf_hw.lightfield_dev.roi_type_int !=4:
                    print ('Error: autofocus only implemented for custom ROI')
                    return z_after
                
                autofoc_Npixel = 8
                ####Bin the ROI of CCD array to be 16x1 pixels for faster readout
                self.lf_hw.lightfield_dev.set_correct_background(correct_bg_bool=False) #cannot use background correction since binning have been changed
                custom_roi_ybinning_original = self.lf_hw.custom_roi_ybinning.value
                custom_roi_xbinning_original = self.lf_hw.custom_roi_xbinning.value
                
                self.lf_hw.custom_roi_xbinning.val = int(self.lf_hw.custom_roi_width.val/autofoc_Npixel)
                self.lf_hw.custom_roi_ybinning.val = self.lf_hw.custom_roi_height.val
                self.lf_hw.set_custom_roi()
                
#                 self.lf_hw.lightfield_dev.set_custom_ROI(roi_dim_x  = self.lf_hw.custom_roi_x.value, 
#                                                          roi_dim_y  = self.lf_hw.custom_roi_y.value, 
#                                                          roi_width  = self.lf_hw.custom_roi_width.value, 
#                                                          roi_height = self.lf_hw.custom_roi_height.value, 
#                                                          roi_xbinning = int(self.lf_hw.custom_roi_width.value/autofoc_Npixel), 
#                                                          roi_ybinning = self.lf_hw.custom_roi_height.value)
                
                ###change to shorter exposure time for faster AF
                tacq0 = self.lf_hw.lightfield_dev.get_exposure_time()
                self.lf_hw.lightfield_dev.set_exposure_time(tacq)
                
                ######Test if this is a dark pixel
                lf_wls, lf_intensity = self.lightfield_readout.ro_acquire_data()
                test_ct = np.sum(lf_intensity) #Note, for CCD this is reading COUNT, not count RATE.
                dark_threshold = CCD_dark_noise*autofoc_Npixel #the dark noise should be the readout noise. SO the threshold is readout noise per pixel times pixel number.
                if test_ct < dark_threshold: ##
                    set_back_to_scanning_condition()
                    print ('*********Give up autofoc at dark autofoc pixel {}'.format(self.autofoc_pixel_i))
                    print ('*********Current count: {}, Threshold: {}'.format(test_ct, dark_threshold ))
                    return z_after
                
                for iz in np.arange(z_scan_pos.shape[0]):
                    z_scan = z_scan_pos[iz]
                    coords = [None, None, None]
                    coords[self.ax_map[S['h_axis']]] = h_now
                    coords[self.ax_map[S['v_axis']]] = v_now
                    coords[2] = z_scan
                    self.stage.move_pos_fast(*coords)
                        
                    lf_wls, lf_intensity = self.lightfield_readout.ro_acquire_data()
                    z_scan_intensity[iz] = np.sum(lf_intensity)
                


            #####################################################################################
            ##############################################################################
                
            ##########Plot z scan result, and fit for optimized z position
            self.autofocus_z_scan_intensity = z_scan_intensity.copy()
            self.autofocus_z_scan_pos = z_scan_pos.copy()
            
            z_scan_p = np.polyfit(z_scan_pos, z_scan_intensity-z_scan_intensity[0], deg=2)
            z_scan_intensity_fit = np.polyval(z_scan_p, z_scan_pos_fit)
            
            iz_after = np.argmax(z_scan_intensity_fit)
            z_after = z_scan_pos_fit[iz_after]
            
            iz_after_raw = np.argmax(z_scan_intensity)
            z_after_raw = z_scan_pos[iz_after_raw]
           
            
#             pl.figure(1)
#             pl.plot(z_scan_pos, z_scan_intensity-z_scan_intensity[0], 'o')
#             pl.plot(z_scan_pos_fit, z_scan_intensity_fit, '-')
#             pl.axvline(z_after)
#             pl.show()  #####Signal only works in main thread!!!

            

        set_back_to_scanning_condition()
        
        self.autofoc_z_after_current = z_after

        return z_after

#########These functions are defined duplicatedly with those in base_3d_scan. These ones should be discarded!!!!                
#     def move_position_start(self, h,v):
#         self.stage.settings.x_position.update_value(h)
#         self.stage.settings.y_position.update_value(v)
#     
#     def move_position_slow(self, h,v, dh, dv):
#         self.stage.settings.x_position.update_value(h)
#         self.stage.settings.y_position.update_value(v)
#         
#     def move_position_fast(self, h,v, dh, dv):
#         self.stage.settings.x_position.update_value(h)
#         self.stage.settings.y_position.update_value(v)
#         
#         #x = self.stage.settings['x_position']
#         #y = self.stage.settings['y_position']        
#         #x = self.stage.settings.x_position.read_from_hardware()
#         #y = self.stage.settings.y_position.read_from_hardware()
#         #print(x,y)
    
    def scan_specific_savedict(self):
        pass 
        
    def pre_scan_setup(self):
        print(self.name, "pre_scan_setup not implemented")
        # hardware
        # create data arrays
        # update figure        

    def collect_pixel(self, pixel_num, k, j, i):
        # collect data
        # store in arrays        
        print(self.name, "collect_pixel", pixel_num, k,j,i, "not implemented")
    
    def post_scan_cleanup(self):
        print(self.name, "post_scan_cleanup not implemented")

    def new_pt_pos(self, x,y):
        self.move_position_start(x, y)