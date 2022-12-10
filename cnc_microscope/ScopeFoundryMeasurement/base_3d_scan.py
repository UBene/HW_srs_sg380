from __future__ import division, print_function
import numpy as np
from cnc_microscope.scanning.base_raster_slow_scan import BaseRaster2DSlowScan
import time
from cnc_microscope.scanning.base_raster_frame_slow_scan import BaseRaster2DFrameSlowScan

class PIStage2DSlowScan(BaseRaster2DSlowScan):
    
    name = "PIStage2DSlowScan"
    def __init__(self, app):
        BaseRaster2DSlowScan.__init__(self, app, h_limits=(0,200), v_limits=(0,200), h_unit="um", v_unit="um") ,
        #                              h_spinbox_step = 0.1, v_spinbox_step=0.1,
        #                                     
    
    def setup(self):
        BaseRaster2DSlowScan.setup(self)
        
        self.settings.New("h_axis", initial="X", dtype=str, choices=("X", "Y", "Z"))
        self.settings.New("v_axis", initial="Y", dtype=str, choices=("X", "Y", "Z"))
        
        self.ax_map = dict(X=0, Y=1, Z=2)
        
        #Hardware
        self.stage = self.app.hardware.PI_xyz_stage
        
        #self.scan_specific_setup()
        
    def setup_figure(self):
        BaseRaster2DSlowScan.setup_figure(self)
        self.set_details_widget(widget=self.settings.New_UI(include=['h_axis', 'v_axis']))
        
        
        

        
    def move_position_start(self, h,v):
        #self.stage.y_position.update_value(x)
        #self.stage.y_position.update_value(y)
        
        S = self.settings
        
        coords = [None, None, None]
        coords[self.ax_map[S['h_axis']]] = h
        coords[self.ax_map[S['v_axis']]] = v
        
        #self.stage.move_pos_slow(x,y,None)
        self.stage.move_pos_slow(*coords)

    
    def move_position_slow(self, h,v):
        self.move_position_start(h, v)
        if self.settings["update_position"]:
            self.stage.settings.x_position.read_from_hardware()
            self.stage.settings.y_position.read_from_hardware()
            self.stage.settings.z_position.read_from_hardware()

    
    def move_position_fast(self,  h,v):
        #self.stage.x_position.update_value(x)
        S = self.settings        
        coords = [None, None, None]
        coords[self.ax_map[S['h_axis']]] = h
        coords[self.ax_map[S['v_axis']]] = v
        self.stage.move_pos_fast(*coords)
        ###### Note: there's time.sleep (0.05) in the mov_pos_fast function in PI equipment code: pi_nanopositioner
        
        if self.settings["update_position"]:
            self.stage.settings.x_position.read_from_hardware()
            self.stage.settings.y_position.read_from_hardware()
            self.stage.settings.z_position.read_from_hardware()
        #self.stage.move_pos_fast(x, y, None)
        #self.current_stage_pos_arrow.setPos(x, y)
        #self.stage.settings.x_position.read_from_hardware()
        #self.stage.settings.y_position.read_from_hardware()
        #self.stage.settings.z_position.read_from_hardware()
        
    
class PIStage2DFrameSlowScan(BaseRaster2DFrameSlowScan):
    
    name = "PIStage2DFrameSlowScan"
    
    def __init__(self, app):
        BaseRaster2DFrameSlowScan.__init__(self, app, h_limits=(0,75), v_limits=(0,75), h_unit="um", v_unit="um")        
    
    def setup(self):
        PIStage2DSlowScan.setup(self)

    def move_position_start(self, h,v):
        PIStage2DSlowScan.move_position_start(self, h, v)
    
    def move_position_slow(self, h,v, dh,dv):
        PIStage2DSlowScan.move_position_slow(self, h,v, dh,dv)
        
    def move_position_fast(self,  h,v, dh,dv):
        PIStage2DSlowScan.move_position_fast(self,  h,v, dh,dv)
        
        
class PIStage3DStackSlowScan(PIStage2DFrameSlowScan):
    
    name = 'PIStage3DScan'
    
    def setup(self):
        PIStage2DFrameSlowScan.setup(self)
        
        self.settings.New("stack_axis", initial="Z", dtype=str, choices=("X", "Y", "Z"))
        self.settings.New_Range('stack', dtype=float)
        
        self.settings.stack_num.add_listener(self.settings.n_frames.update_value, int)
        
    def on_new_frame(self, frame_i):
        S = self.settings
        stack_range = S.ranges['stack']
        
        stack_pos_i = stack_range.array[frame_i]
        coords = [None, None, None]
        coords[self.ax_map[S['stack_axis']]] = stack_pos_i
        
        self.stage.move_pos_slow(*coords)
        self.stage.settings.x_position.read_from_hardware()
        self.stage.settings.y_position.read_from_hardware()
        self.stage.settings.z_position.read_from_hardware()



class PI_2DScan(PIStage2DSlowScan):
    
    
    name = "PI_2DScan"
        

    def setup_figure(self):
        PIStage2DSlowScan.setup_figure(self)
        self.set_details_widget(widget=self.settings.New_UI(include=['h_axis', 'v_axis', 'pixel_time', 'frame_time']))
        
        # Hardware connections
        if 'apd_counter' in self.app.hardware.keys():
            self.app.hardware.apd_counter.settings.int_time.connect_bidir_to_widget(
                                                                    self.ui.apd_int_time_doubleSpinBox)
        else:
            self.collect_apd.update_value(False)
            self.collect_apd.change_readonly(True)
        
        if 'lightfield' in self.app.hardware.keys():
            self.app.hardware['lightfield'].settings.exposure_time.connect_bidir_to_widget(
                                                                    self.ui.spectrum_int_time_doubleSpinBox)
        
        else:
            self.collect_spectrum.update_value(False)
            self.collect_spectrum.change_readonly(True)

            
        if 'hydraharp' in self.app.hardware.keys():
            self.app.hardware['hydraharp'].settings.Tacq.connect_bidir_to_widget(self.ui.hydraharp_tacq_doubleSpinBox)

        else:
            self.collect_lifetime.update_value(False)
            self.collect_lifetime.change_readonly(True)


    def scan_specific_setup(self):
        PIStage2DSlowScan.scan_specific_setup(self)
#         self.settings['pixel_time'] = 0.01
        self.settings.pixel_time.change_readonly(False)
        self.collect_apd      = self.add_logged_quantity("collect_apd",      dtype=bool, initial=False)
        self.collect_spectrum = self.add_logged_quantity("collect_spectrum", dtype=bool, initial=False)
        self.collect_lifetime = self.add_logged_quantity("collect_lifetime", dtype=bool, initial=False)
        self.collect_CCD_image = self.add_logged_quantity('collect_CCD_image', dtype=bool, initial=False)
        self.collect_toupcam = self.add_logged_quantity("collect_toupcam", dtype=bool, initial=False)

        self.collect_apd.connect_to_widget(self.ui.collect_apd_checkBox)
        self.collect_spectrum.connect_to_widget(self.ui.collect_spectrum_checkBox)
        self.collect_lifetime.connect_to_widget(self.ui.collect_hydraharp_checkBox)
        self.collect_CCD_image.connect_to_widget(self.ui.collect_CCD_image_checkBox)
        self.collect_toupcam.connect_to_widget(self.ui.collect_toupcam_checkBox)


        ##################################################################
        ####### spectrum integration

        self.collect_spectrum_wls_min = self.add_logged_quantity("wavelength_min", initial=0, vmin=0, dtype=float, ro=False)
        self.collect_spectrum_wls_min.connect_to_widget(self.ui.spectrum_wavelength_min_doubleSpinBox)
        self.collect_spectrum_wls_max = self.add_logged_quantity("wavelength_max", initial=2000, vmin=1, dtype=float, ro=False)
        self.collect_spectrum_wls_max.connect_to_widget(self.ui.spectrum_wavelength_max_doubleSpinBox)
        ###################################################################
        # ########### Autofocus Panel
        # #self.autofoc_enable = self.add_logged_quantity("autofoc_enable", dtype=bool, initial=False)
        # #self.autofoc_enable.connect_to_widget(self.ui.autofoc_enable_checkBox)
        #
        # #self.autofoc_dt = self.settings.New('autofoc_dt', initial=6, vmin=1, dtype=int, ro=False) #in seconds
        # #self.autofoc_dt.connect_to_widget(self.ui.autofoc_dt_doubleSpinBox)
        #
        # ###################################################################################################
        # ############Note: the integration time for the axial scan needs to be long enough to overcome shot noise from the measurement!!!!!
        # ############      Ohterwise the axial scan will be very noisy!!!!
        # self.autofoc_tacq_ratio = self.settings.New('autofoc_tacq_ratio', initial=10, vmin=0, dtype=float, ro=False) #in seconds
        # self.autofoc_tacq_ratio.connect_to_widget(self.ui.autofoc_tacq_ratio_doubleSpinBox)
        #
        # self.autofoc_CCD_dark_noise = self.settings.New('autofoc_CCD_dark_noise', initial = 800, vmin=1, dtype=float, ro=False)
        # self.autofoc_CCD_dark_noise.connect_to_widget(self.ui.autofoc_CCD_dark_noise_doubleSpinBox)
        #
        # self.autofoc_APD_dark_noise = self.settings.New('autofoc_APD_dark_noise', initial = 50, vmin=1, dtype=float, ro=False)
        # self.autofoc_APD_dark_noise.connect_to_widget(self.ui.autofoc_APD_dark_noise_doubleSpinBox)
        #
        # self.autofoc_fix_pix = self.add_logged_quantity("autofoc_fix_pix", dtype=bool, initial=False)
        # self.autofoc_fix_pix.connect_to_widget(self.ui.autofoc_fix_pix_checkBox)
        #
        # h_lq_params = dict(vmin=self.h_limits[0], vmax=self.h_limits[1], unit=self.h_unit,
        #                    spinbox_decimals=self.h_spinbox_decimals, spinbox_step=self.h_spinbox_step,
        #                    dtype=float,ro=False)
        # h_range = self.h_limits[1] - self.h_limits[0]
        # self.autofoc_pix_H = self.settings.New('autofoc_pix_H', initial=self.h_limits[0]+h_range*0.25, **h_lq_params)
        # self.autofoc_pix_H.connect_to_widget(self.ui.autofoc_pix_H_doubleSpinBox)
        #
        # v_lq_params = dict(vmin=self.v_limits[0], vmax=self.v_limits[1], unit=self.v_unit,
        #                    spinbox_decimals=self.v_spinbox_decimals, spinbox_step=self.v_spinbox_step,
        #                    dtype=float,ro=False)
        # v_range = self.v_limits[1] - self.v_limits[0]
        # self.autofoc_pix_V = self.settings.New('autofoc_pix_V', initial=self.v_limits[0]+v_range*0.25, **v_lq_params)
        # self.autofoc_pix_V.connect_to_widget(self.ui.autofoc_pix_V_doubleSpinBox)
        #
        ######################################################################
        ####################################################################
        
    def pre_scan_setup(self):
        ####Move slider to turn on illumination   
        ### Note: have trouble in reading position of slider 
        #if self.app.hardware.dual_position_slider.slider_pos.val == 'Closed':
        print ('Now open shutter...')
        self.app.hardware.dual_position_slider.move_bkwd()
        print("before if self.settings['collect_apd']")
        
        if self.settings['collect_apd']:
            self.count_rate_map = np.zeros((1, self.Nv.val, self.Nh.val), dtype=float)
            #self.count_rate_map_h5 = self.h5_meas_group.create_dataset('count_rate_map',shape=(1, self.Nv.val, self.Nh.val), dtype=float, compression='gzip', shuffle=True)
            print("after if self.settings['collect_apd']")
            print("test_count_rate_map:{}", self.count_rate_map)
            self.apd_counter_hw = self.app.hardware.apd_counter
            self.apd_count_rate_lq = self.apd_counter_hw.settings.apd_count_rate         
            self.count_rate_map = np.zeros((1, self.Nv.val, self.Nh.val), dtype=float) ##Note: this data array needs to be setup before runing, otherwise will see display update errors
                  
        elif self.settings['collect_spectrum']:
            print ('*************Set to collect CCD Spectrum')
            self.lf_hw = self.app.hardware.lightfield
            self.lightfield_readout = self.app.measurements['lightfield_readout']
            self.lightfield_readout.ro_acquire_data()
            Nx_spectra = self.lightfield_readout.image_width
            self.wls = np.zeros(Nx_spectra)
            self.integrated_spectra_map = np.zeros((1, self.Nv.val, self.Nh.val), dtype=float)
            self.spectra_map = np.zeros((1, self.Nv.val, self.Nh.val, Nx_spectra), dtype=float)  ##Nx is the wls axis
        
        elif self.settings['collect_CCD_image']:
            print ('*************Set to collect CCD image')
            self.lf_hw = self.app.hardware.lightfield
            self.lightfield_image_readout = self.app.measurements['lightfield_image_readout']
            self.lightfield_image_readout.ro_acquire_data()
            Nx_image = self.lightfield_image_readout.image_width
            Ny_image = self.lightfield_image_readout.image_height
            self.wls = np.zeros(Nx_image)
            self.integrated_spectra_map = np.zeros((1, self.Nv.val, self.Nh.val), dtype=float)
            self.spectra_map = np.zeros((1, self.Nv.val, self.Nh.val, Nx_image), dtype=float)  ##Nx is the wls axis
            self.image_map = np.zeros((1, self.Nv.val, self.Nh.val, Ny_image, Nx_image), dtype=float)  ##Nx is the wls axis, Ny is the vertical

        if self.settings['collect_lifetime']:
            self.ph_hw = self.app.hardware['hydraharp']
            self.hydraharp_histogram = self.app.measurements['hydraharp_histogram']
            self.hydraharp_histogram.read_lifetime()
            time_array = self.hydraharp_histogram.time_array
            Nx_histogram = np.shape(time_array)[0]
            self.time_array_hh = np.zeros((1, self.Nv.val, self.Nh.val, Nx_histogram), dtype=float)
            self.hist_data0 = np.zeros((1, self.Nv.val, self.Nh.val, Nx_histogram), dtype=float)
            self.integrated_hist_data0 = np.zeros((1, self.Nv.val, self.Nh.val), dtype=float)

        if self.settings['collect_toupcam']:
            self.toupcam_hw = self.app.hardware['toupcam']

            N_width, N_height = self.toupcam_hw.get_size()

            self.R_mat = np.zeros((1, self.Nv.val, self.Nh.val, N_width, N_height), dtype=np.uint8)
            self.G_mat = np.zeros((1, self.Nv.val, self.Nh.val, N_width, N_height), dtype=np.uint8)
            self.B_mat = np.zeros((1, self.Nv.val, self.Nh.val, N_width, N_height), dtype=np.uint8)
            self.integrated_grayscale = np.zeros((1, self.Nv.val, self.Nh.val), dtype=int)


        ##########################################################################
        #########For Autofocus function
        # if self.settings['autofoc_enable']:
        #     self.autofoc_pixel_numbers = np.array([], int)  ##register the number of pixels that will go through autofocus
        #     self.autofoc_coord_H = np.array([], float)
        #     self.autofoc_coord_V = np.array([], float)
        #     self.autofoc_coord_zbefore = np.array([], float)
        #     self.autofoc_coord_zafter = np.array([], float)
        #     self.autofoc_z_scan_intensity = np.array([0], float)
        ###############################################################################
        ###############################################################################
    
    
    
    def collect_pixel(self, pixel_num, k, j, i):
        if self.settings['collect_apd']:      
            count_reading = self.apd_count_rate_lq.read_from_hardware()
            self.count_rate_map[k, j, i] = count_reading  # changed from [k, i, j] to [k, j, i] by Kaiyuan, 07/24/2018, to fix data recording and display problems.
            #self.count_rate_map_h5[k,j,i] = self.apd_count_rate_lq.value
            
            #print('Count rate: ', self.apd_count_rate_lq.value)
            


        elif self.settings['collect_spectrum']:

            self.Int_max = 0
            self.Int_min = 1

            if self.lightfield_readout.settings['MultiSpecAvg'] == False:
                self.lightfield_readout.ro_acquire_data()
                spec = np.array(self.lightfield_readout.img)
                self.spectra_map[k,j,i,:] = spec
                #self.integrated_spectra_map[k,j,i] = spec.sum()     #  Original
                self.wls = np.array(self.lightfield_readout.wls)
                self.Int_min = min(range(len(self.wls)), key=lambda i: abs(self.wls[i] - self.collect_spectrum_wls_min.val))  # Finde the index of desired min/max in wls
                self.Int_max = min(range(len(self.wls)), key=lambda i: abs(self.wls[i] - self.collect_spectrum_wls_max.val))
                Int_spec = spec[self.Int_min: self.Int_max]
                self.integrated_spectra_map[k,j,i] = Int_spec.sum()     #  To sum up the interested wavelength region only
                #self.wls = np.array(self.lightfield_readout.wls)
            
            if self.lightfield_readout.settings['MultiSpecAvg'] == True:
                print('******PI_2DScan Use MultiSpecAvg')
                
                ##########
                self.lightfield_readout.wls_MultiSpec, self.lightfield_readout.img_MultiSpec = self.lightfield_readout.ro_acquire_data()
                #for iMulti in np.arange(0, self.MultiSpecAvg_Number.val-1):
                for iMulti in np.arange(0, self.lightfield_readout.settings.MultiSpecAvg_Number.val-1):
                    self.lightfield_readout.wls, self.lightfield_readout.img = self.lightfield_readout.ro_acquire_data()
                    self.lightfield_readout.img_MultiSpec += self.lightfield_readout.img
                    
                spec = np.array(self.lightfield_readout.img_MultiSpec)
                self.spectra_map[k,j,i,:] = spec
                self.integrated_spectra_map[k,j,i] = spec.sum()
                self.wls = np.array(self.lightfield_readout.wls)
                
                ##########
                
            
        elif self.settings['collect_CCD_image']:
            self.lightfield_image_readout.ro_acquire_data()
            spec = np.array(self.lightfield_image_readout.img)
            CCD_image = np.array(self.lightfield_image_readout.acquired_data)
            #self.spectra_map[k,j,i,:] = spec # Tom: took out second colon operator 
            self.integrated_spectra_map[k,j,i] = spec.sum()
            self.wls = np.array(self.lightfield_image_readout.wls)
            self.image_map[k,j,i,:,:] = CCD_image
            print ('***********image total intensity: {}'.format(spec.sum())  )
            
        elif self.settings['collect_lifetime']:
            self.hydraharp_histogram.read_lifetime()
            self.time_array_hh[k,j,i,:] = self.hydraharp_histogram.time_array
            self.hist_data0[k,j,i,:]= self.hydraharp_histogram.hist_data0
            self.integrated_hist_data0[k,j,i] = np.sum(self.hydraharp_histogram.hist_data0)

        elif self.settings['collect_toupcam']:
            #print ('exposure time: ', self.toupcam_hw.get_exposure_time())
            time.sleep(self.toupcam_hw.get_exposure_time())

            im = np.flip(self.toupcam_hw.get_rgb_image().swapaxes(0,1),0)

            self.R_mat[k,j,i,:,:] = im[..., 0]
            self.G_mat[k,j,i,:,:] = im[..., 1]
            self.B_mat[k,j,i,:,:] = im[..., 2]
            L = im[..., 0] * 299 / 1000 + im[..., 1] * 587 / 1000 + im[..., 2] * 114 / 1000
            self.integrated_grayscale[k,j,i] = np.sum(L)

            time.sleep(self.toupcam_hw.get_exposure_time() * 0.05)
#         time.sleep(self.toupcam_hw.get_exposure_time())
        else:
            time.sleep(5.0)
    
    #def scan_specific_savedict(self):
    #    savedict = {}
    #    if self.settings['collect_apd']: 
    #        H['count_rate_map' ] = self.count_rate_map
    #    
    #    #savedict = {'count_rate_map': self.count_rate_map}
    #    return savedict
    
        
    def post_scan_cleanup(self):
        
        ###Move slider back to turn off illumination
        #if self.app.hardware.dual_position_slider.slider_pos.val == 'Open':
        print ('Now close shutter...')
        self.app.hardware.dual_position_slider.move_fwd()
        
        pass
    
    #def update_display(self):
    #    #PIStage2DSlowScan.update_display(self)
    #    self.stage.settings.x_position.read_from_hardware()
    #    self.stage.settings.y_position.read_from_hardware()
    #    if self.stage.nanopositioner.num_axes > 2:
    #        self.stage.settings.z_position.read_from_hardware()
        
        
        




