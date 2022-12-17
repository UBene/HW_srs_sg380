# -*- coding: utf-8 -*-
"""
Created on Wed Jul 18 03:03:05 2018

@author: Schuck Lab M1
"""

from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.lightfield.lightfield_dev import LightFieldDev


class LightFieldHW(HardwareComponent):
    
    def setup(self):
        self.name = "lightfield"
        self.background = None
        
        self.correct_background = self.add_logged_quantity(name="correct_background", dtype=bool, ro=False, initial = False)
        self.temperature = self.add_logged_quantity(name="temperature", dtype=int,
                                                    ro=True, unit = "C", vmin = -300, vmax = 300, si=False)
        
        self.cooler_on = self.add_logged_quantity(name="cooler_on", dtype=bool, ro=False)
        
        #self.diplay_type = self.add_logged_quantity("diplay_type", dtype=str, ro=False, 
        #                                            choices = [("image","image"),
        #                                                       ("graph","graph")]
        #                                            ,initial = "graph")
        
        self.exposure_time = self.add_logged_quantity(name="exposure_time", 
                                                      dtype=float,
                                                      fmt="%e", ro=False,
                                                      unit = "sec", si=True,
                                                      vmin = 1e-3, vmax=1000)     
        
        
        
        self.adc_quality = self.add_logged_quantity("adc_quality", dtype=str, ro=False, 
                                                    choices = [("Low Noise","Low Noise"), ("Electron Multiplied","Electron Multiplied")]
                                                    )
        
        self.adc_speed = self.add_logged_quantity("adc_speed", dtype=float, ro=False, 
                                                    choices = [("100 kHz",0.1), ("1 MHz",1.0), ("4 MHz",4.0), ("8 MHz",8.0)]
                                                    , initial = 1.0)
        
        self.analogy_gain = self.add_logged_quantity("analogy_gain", dtype=str, ro=False,
                                                   choices = [("High","High"), ("Medium","Medium"), ("Low", "Low")]
                                                   , initial = "High")
        
        self.em_gain = self.add_logged_quantity("em_gain", dtype=int, ro=False,
                                                si=False,
                                                vmin=1, vmax=100, initial = 1)
        self.roi_type = self.add_logged_quantity("roi_type", dtype=str, ro=False, 
                                                    choices = [("FullSensor","FullSensor"),
                                                               ("BinnedSensor","BinnedSensor"),  
                                                               ("LineSensor","LineSensor"),  
                                                               ("CustomRegions","CustomRegions")]
                                                    ,initial = "CustomRegions")
        
        
        
        self.x_binning = self.add_logged_quantity("x_binning", dtype=int, ro=False, initial = 1)
        self.y_binning = self.add_logged_quantity("y_binning", dtype=int, ro=False, initial = 1)
        
        self.custom_roi_x =  self.add_logged_quantity("custom_roi_x", dtype=int, ro=False, initial=0)
        self.custom_roi_y =  self.add_logged_quantity("custom_roi_y", dtype=int, ro=False, initial=50)
        self.custom_roi_width =  self.add_logged_quantity("custom_roi_width", dtype=int, ro=False, initial=1600)
        self.custom_roi_height =  self.add_logged_quantity("custom_roi_height", dtype=int, ro=False, initial=100)
        self.custom_roi_xbinning =  self.add_logged_quantity("custom_roi_xbinning", dtype=int, ro=False, initial=1)
        self.custom_roi_ybinning =  self.add_logged_quantity("custom_roi_ybinning", dtype=int, ro=False, initial=1)
        
        self.vs_speed = self.add_logged_quantity("current_vs_speed", dtype=int, unit = "um", ro = True)
        self.vs_speed_setting = self.add_logged_quantity("vs_speed_setting",
                                                dtype=int, choices=[('2 us', 2), ('3 us', 3), ('4 us', 4), ('6 us', 6)], initial=6 )
        
        self.shutter_mode = self.add_logged_quantity("shutter_mode", dtype=str, ro=False, 
                                                    choices = [("Normal","Normal"),
                                                               ("AlwaysClosed","AlwaysClosed"),  
                                                               ("AlwaysOpen","AlwaysOpen")]
                                                    ,initial = "Normal")
        self.shutter_op_delay =  self.add_logged_quantity("shutter_op_delay", dtype=int, unit = "ms", si=False, ro=False, initial = 20)
        self.shutter_cl_delay =  self.add_logged_quantity("shutter_cl_delay", dtype=int, unit = "ms", si=False, ro=False, initial = 20)
        
        self.trigger_out_signal = self.add_logged_quantity("trigger_out_signal", dtype=str, ro=False, 
                                                    choices = [("Acquiring","Acquiring"),
                                                               ("AlwaysHigh","AlwaysHigh"),  
                                                               ("Exposing","Exposing"),  
                                                               ("ReadingOut","ReadingOut"), 
                                                               ("ShiftingUnderMask","ShiftingUnderMask"),
                                                               ("ShutterOpen","ShutterOpen"),
                                                               ("WaitingForTrigger","WaitingForTrigger")]
                                                    ,initial = "ShutterOpen")
        
        self.grating = self.add_logged_quantity("current_grating", dtype=str, ro=True)
        self.grating_setting = self.add_logged_quantity("grating_setting", dtype=str, ro=False, 
                                                choices = [("[500nm,1200][0][0]", "[500nm,1200][0][0]"),
                                                           ("[1.0um,600][1][0]", "[1.0um,600][1][0]"),
                                                           ("[500nm,150][2][0]", "[500nm,150][2][0]")])
        
        self.center_wavelength = self.add_logged_quantity("center_wavelength", dtype=float, unit = "nm", ro=False)

        # A single operation to update the ROI values in the camera
        self.add_operation("read_temp", self.read_temp_op)
        self.add_operation("set_custom_roi", self.set_custom_roi)
        
        
    def connect(self):
        if self.settings['debug_mode']: print ("Connecting to LightField")
        
        # Open connection to hardware
        self.lightfield_dev= LightFieldDev(debug = self.settings['debug_mode'])

        # connect logged quantities
        self.correct_background.hardware_set_func = self.lightfield_dev.set_correct_background
        self.temperature.hardware_read_func = self.lightfield_dev.get_Temp
        self.exposure_time.hardware_set_func = self.lightfield_dev.set_exposure_time
        self.exposure_time.hardware_read_func = self.lightfield_dev.get_exposure_time
        self.adc_quality.hardware_set_func = self.lightfield_dev.set_adc_quality
        self.adc_speed.hardware_set_func = self.lightfield_dev.set_adc_speed
        self.analogy_gain.hardware_set_func = self.lightfield_dev.set_adc_AnalogGain
        self.em_gain.hardware_set_func = self.lightfield_dev.set_adc_EMGain
        self.em_gain.hardware_read_func = self.lightfield_dev.get_adc_EMGain
        self.roi_type.hardware_set_func = self.lightfield_dev.set_roitype
        self.x_binning.hardware_read_func = self.lightfield_dev.get_XBinning
        self.x_binning.hardware_set_func = self.lightfield_dev.set_XBinning
        self.y_binning.hardware_read_func = self.lightfield_dev.get_YBinning
        self.y_binning.hardware_set_func = self.lightfield_dev.set_YBinning
        self.vs_speed.hardware_read_func = self.lightfield_dev.get_vertical_shift_rate
        self.vs_speed_setting.hardware_set_func = self.lightfield_dev.set_vertical_shift_rate
        self.shutter_mode.hardware_set_func = self.lightfield_dev.set_shutter_mode
        self.shutter_op_delay.hardware_set_func = self.lightfield_dev.set_shutter_opening_delay
        self.shutter_op_delay.hardware_read_func = self.lightfield_dev.get_shutter_opening_delay
        self.shutter_cl_delay.hardware_set_func = self.lightfield_dev.set_shutter_closing_delay
        self.shutter_cl_delay.hardware_read_func = self.lightfield_dev.get_shutter_closing_delay
        self.trigger_out_signal.hardware_set_func = self.lightfield_dev.set_trigger_out
        self.grating.hardware_read_func = self.lightfield_dev.get_grating
        self.grating_setting.hardware_set_func = self.lightfield_dev.set_grating
        self.center_wavelength.hardware_set_func = self.lightfield_dev.set_grating_center_wavelength
        self.center_wavelength.hardware_read_func = self.lightfield_dev.get_grating_center_wavelength
        
        
        # Update the ROI min and max values to the CCD dimensions
        #width = 1340
        #height = 400
        width = self.lightfield_dev.Nx
        height = self.lightfield_dev.Ny
        self.custom_roi_x.change_min_max(0, width)
        self.custom_roi_y.change_min_max(0, height)
        self.custom_roi_width.change_min_max(1, width)
        self.custom_roi_height.change_min_max(1, height)
        self.custom_roi_xbinning.change_min_max(1, width)
        self.custom_roi_ybinning.change_min_max(1, height)

        DEFAULT_TEMPERATURE = -60
        # Set some default values that are useful
        self.lightfield_dev.set_Temp(DEFAULT_TEMPERATURE)
        
        if not self.has_been_connected_once:
            # initialize the readout parameters
            self.custom_roi_x.update_value(0)        
            self.custom_roi_y.update_value(50)
            self.custom_roi_width.update_value(1600)      
            self.custom_roi_height.update_value(100)
            self.custom_roi_xbinning.update_value(1)          
            self.custom_roi_ybinning.update_value(1)     




        #######################################################
        ########### Note: Bug to deal with later
        ########### the camera settings are not connected to its UI. 
        ########### Need ot Fix!!!!!!


        
        #self.lightfield_dev.set_shutter_closing_delay()
        
        print('shutter_cl_delay.val initial value {}'.format(self.shutter_cl_delay.val))
        self.shutter_cl_delay.update_value(self.shutter_cl_delay.val)
        
        self.lightfield_dev.set_roitype(self.roi_type.val)
        print('lf.roi_type_int initiazlied to {}'.format(self.lightfield_dev.roi_type_int))
        
        
        self.set_custom_roi()
        
        
        
        self.read_from_hardware()
        
        self.lightfield_dev.set_new_folder()
        self.is_connected = True
        

    def disconnect(self):
        #disconnect logged quantities from hardware
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
            
        if hasattr(self, 'lightfield_dev'):
        # clean up hardware object
            self.lightfield_dev.close()
            del self.lightfield_dev
        
        self.is_connected = False
    
#    def is_background_valid(self):
#        bg = self.background
#        if bg is not None:
#            if bg.shape == self.andor_ccd.buffer.shape:
#                return True
#            else:
#                print "Background not the correct shape", self.andor_ccd.buffer.shape, bg.shape
#        else:
#            print "No Background available, raw data shown"
#    
#        return False
    
#    def interrupt_acquisition(self):
#        '''If the camera status is not IDLE, calls abort_acquisition()
#        '''
#        stat = self.andor_ccd.get_status()
#        if stat != 'IDLE':
#            self.andor_ccd.abort_acquisition()
    

    def set_custom_roi(self):
        #self.andor_ccd.set_image_flip(self.hflip.val, self.vflip.val)
        #print (self.custom_roi_xbinning.val)
        self.lightfield_dev.set_custom_ROI(self.custom_roi_x.val, self.custom_roi_y.val, 
                                       self.custom_roi_width.val, self.custom_roi_height.val, 
                                       self.custom_roi_xbinning.val, self.custom_roi_ybinning.val)

    def read_temp_op(self):
        #print self.andor_ccd.get_status(
        self.lightfield_dev.get_Temp()

        #self.gui.ui.andor_ccd_shutter_open_checkBox.setChecked(True)
        
