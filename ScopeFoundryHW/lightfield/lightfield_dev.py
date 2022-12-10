# -*- coding: utf-8 -*-
"""
Created on Tue Jul 17 20:19:25 2018

@author: Schuck Lab M1
"""

# Import the .NET class library
import clr

# Import python sys module
import sys

# Import modules
import os, glob, string
from time import strftime
import time
import numpy as np
# Import System.IO for saving and opening files
from System.IO import *





from System.Threading import AutoResetEvent

# Import C compatible List and String
from System import String
from System import Int32 as Int
from System.Collections.Generic import List


# Add needed dll references
sys.path.append(os.environ['LIGHTFIELD_ROOT'])
sys.path.append(os.environ['LIGHTFIELD_ROOT']+"\\AddInViews")
clr.AddReference('PrincetonInstruments.LightFieldViewV5')
clr.AddReference('PrincetonInstruments.LightField.AutomationV5')
clr.AddReference('PrincetonInstruments.LightFieldAddInSupportServices')

# PI imports
from PrincetonInstruments.LightField.Automation import Automation
from PrincetonInstruments.LightField.AddIns import CameraSettings
from PrincetonInstruments.LightField.AddIns import SpectrometerSettings
from PrincetonInstruments.LightField.AddIns import ExperimentSettings
from PrincetonInstruments.LightField.AddIns import RegionOfInterest
from PrincetonInstruments.LightField.AddIns import AdcQuality
from PrincetonInstruments.LightField.AddIns import DeviceType   
from PrincetonInstruments.LightField.AddIns import ShutterType

class LightFieldDev(object):
    def __init__(self, debug = False):
        if debug: print ("LightField initializing")
        
        self.debug = debug
        self.save_spe = True
        
        self.file_generation_dir = 'C:\\Users\\Schuck Lab M1\\Documents\\LightField'
        
        auto = Automation(True, List[String]())
        
        application = auto.LightFieldApplication
        # Get experiment object
        self.experiment = application.Experiment

        # Load Pro-EM camera setting
        self.experiment.Load('Experiment_Vis')
        
        # Get file manager object
        self.file_manager = application.FileManager
                
        # Notifies a waiting thread that an event has occurred
        self.acquireCompleted = AutoResetEvent(False)
        
        self.experiment.ExperimentCompleted += self.experiment_completed   
        # Check for lightfield has available devices
        if (self.experiment.AvailableDevices.Count == 0):
            print("Device not found. Please add a device and try again.")

        # else:
        #     self.add_available_devices()
        # Experiment already loaded 1 camera and 1 spectrometer
        # Do not need to load more devices onto the experiment

        # Check for lightfield is connected to a camera and spectrometer
        
        self.device_found()
        
        
        # Check if Lightfield is ready to run
        if (self.experiment.IsReadyToRun == True):
            self.debug: print("LightField is ready to run")
        else:
            raise print("LightField is not ready to run")
        
        # Set Aquisition Time
        self.set_exposure_time(30e-3)
        
        # Correct Background
        
        
        # Set Analog to Digital Converter

        self.set_adc_quality()
        self.set_adc_speed()
        self.set_adc_AnalogGain()
        self.set_adc_EMGain()


        # Set ROI Type
        
        self.set_roitype()
        
        if (self.roi_type_int == 2):
            self.set_XBinning()
            self.set_YBinning()
        elif (self.roi_type_int == 4):
            self.set_custom_ROI(roi_dim_x = 0 , roi_dim_y = 0, roi_width = 1600, roi_height=200, roi_xbinning=1, roi_ybinning=1)
        
        # Set CCD Temperature
        
        self.set_Temp()
        if self.debug: self.get_Temp()
        
        #Set Sutter Parameters
        self.set_shutter_mode()
        self.set_shutter_opening_delay()
        self.set_shutter_closing_delay()
        
        #Set Trigger-out Parameter
        
        self.set_trigger_out()
        
        #Set File Name Increment Number 
        self.set_incrementNumber()
        
        # Read Dimension of the sensor
        dimensions = self.get_device_dimensions()
        
        self.Nx = dimensions.Width
        self.Ny = dimensions.Height
        
        if self.debug: print("Dimensions: {} x {}".format(self.Nx, self.Ny))
        
        if self.debug:
            grating = self.get_grating()
            grating_center = self.get_grating_center_wavelength()
            print("grating: {}, center wavelength: {}".format(grating, grating_center))
    
    def experiment_completed(self, sender, event_args):    
        print("Experiment Completed")    
        # Sets the state of the event to signaled,
        # allowing one or more waiting threads to proceed.
        self.acquireCompleted.Set()

    
    def set_incrementNumber(self, bool_increment_number = True):
        self.experiment.SetValue(ExperimentSettings.FileNameGenerationAttachIncrement, bool_increment_number)
        if self.debug: print("File Increment Number: {}".format(str(bool_increment_number)))
    
    def set_correct_background(self, correct_bg_bool):
        self.experiment.SetValue(ExperimentSettings.OnlineCorrectionsBackgroundCorrectionEnabled, correct_bg_bool)
        if self.debug: print("Correct Background: {}".format(str(correct_bg_bool)))
    
    def set_new_folder(self):
        new_dir = self.file_generation_dir + "\\" + strftime("%d%b%Y %H%M%S")
        self.create_folder(new_dir)
        self.experiment.SetValue(ExperimentSettings.FileNameGenerationDirectory, new_dir)
        if self.debug: print("New File Save Directory: {}".format(new_dir))

    def create_folder(self, directory):
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
        except OSError:
            print ('Error: Creating directory. ' +  directory)
            
    
    def get_image_file(self):
        # Access previously saved image
        
        directory = self.experiment.GetValue(ExperimentSettings.FileNameGenerationDirectory)
        if( os.path.exists(directory)):        
            print("\nOpening .spe file...")        
    
            # Returns all .spe files
            ####### Note: Need to wait till the file is written onto the harddrive before reading from the harddrive!!!!!
            ####### Especially when the previous file needs to be first removed!!!
            files = []
            read_trial = int(0)
            
            ####Note: sleep sometime before reading data
            ####################################################Need to delete this for fast imaging!!!!!!!
            time.sleep(0.01)
            print ('sleep 10ms before reading .spe')
            ###################################################################
            ### 07/08 changed waiting time from 10ms to 2ms, reduced trial count from 50 to 30
            #print (directory)
            while ( (files==[]) & (read_trial<30) ):
                files = glob.glob(directory +'/*.spe')
                read_trial+=1
                time.sleep(0.002)
            if read_trial>29:
                print('Could not read .spe files!!!, read more than 50 times' )
            
            
            # Returns recently acquired .spe file
            
            #t0 = time.time()
            #print ('files len 1', len(files))
            self.last_image_acquired = max(files, key=os.path.getctime)
            
            #print('section 1 run time: {}'.format(time.time()-t0))    
            
            try:
                # Open file
                
                file_name = self.file_manager.OpenFile(
                    self.last_image_acquired, FileAccess.Read)
                
                # Access image
                
                data_y, wid, hei =  self.get_image_data(file_name)
                
    
                #Dispose of image
                
                file_name.Dispose()
                self.remove_image_file()
                
                
            except IOError:
                print ("Error: can not find file or read data")
            
        else:
            print(".spe file not found...")
        return data_y, wid, hei
    
    def remove_image_file(self):
        try:
            os.remove(self.last_image_acquired)
        except IOError:
            print ("Error: can not find file or read data")
    
    def get_image_data(self, file):        
        # Get the first frame
        imageData = file.GetFrame(0, 0);
        
        # Print Height and Width of first frame           
        if self.debug:
            print(String.Format(
                '\t{0} {1}X{2}',
                "Image Width and Height:",
                imageData.Width,imageData.Height))
    
        # Get image data
        buffer = imageData.GetData()
        
        # Print first 10 pixel intensities
        #for pixel in range(0,10):
        #    print(String.Format('\t{0} {1}', 'Pixel Intensity:',
        #                        str(buffer[pixel])))
        return buffer, imageData.Width, imageData.Height
    
    def get_wls(self):
        wavelength_range = self.experiment.SystemColumnCalibration
        return wavelength_range
    
    def get_acquired_data(self):
        self.experiment.Acquire()

        # Wait for acquisition to complete
        self.acquireCompleted.WaitOne()
        t0 = time.time() ### 07/08 KY
        image_data, width, height = self.get_image_file()
        wls = self.get_wls()
        print('*******equipment code get_image_file run time: {}'.format(time.time()-t0)) ### 07/08 KY
        
#        w_size = np.size(wavelength_data)
#        i_size = np.size(int_data)
#        if self.debug: print("x axis array size: {}, y axis array size: {}".format(w_size, i_size))
#        
#        if (w_size != i_size):
#            num_low = i_size/w_size
#            int_data_new = np.zeros(w_size)
#            for i in np.arange(0, num_low):
#                int_data_new += int_data(i*w_size, (i+1)*w_size)
#            int_data = int_data_new/num_low
        
        return wls, image_data, width, height
        
    def get_vertical_shift_rate(self):
      
        shift_rate = self.experiment.GetValue(CameraSettings.ReadoutControlVerticalShiftRate)
        
        if self.debug: print("Vertical Shift Rate: {}".format(shift_rate))
        return shift_rate
    
    def set_vertical_shift_rate(self, shift_rate = 6.0):
        if self.adc_quality_int == 1 and shift_rate < 4.0:
            print("Recommended minimum vertical shift rateis 4.0 when adc quality is low noise mode ")
            shift_rate = 4.0
        elif self.adc_quality_int == 3 and shift_rate > 3.0:
            print("Recommended maximum vertical shift rate when adc quality is EM mode is 3.0")
            shift_rate = 3.0
        self.experiment.SetValue(CameraSettings.ReadoutControlVerticalShiftRate, shift_rate)
        if self.debug: print("Vertical Shift Rate: {}".format(shift_rate))
    
    def set_grating_center_wavelength(self, center_wavelength = 500.0):
        self.experiment.SetValue(SpectrometerSettings.GratingCenterWavelength, center_wavelength)
        if self.debug: print("Current Grating: {}".format(center_wavelength))
    
    def get_grating_center_wavelength(self):
        center_wavelength = self.experiment.GetValue(SpectrometerSettings.GratingCenterWavelength)
        if self.debug: print("Current Grating: {}".format(center_wavelength))
        return center_wavelength
    
    def get_grating(self):
        grating = self.experiment.GetValue(SpectrometerSettings.Grating)
        if self.debug: print("Current Grating: {}".format(grating))
        return grating
    
    def set_grating(self, default_grating = '[500nm,150][2][0]'):
        self.experiment.SetValue(SpectrometerSettings.Grating, default_grating)
        if self.debug: print("Current Grating: {}".format(default_grating))
    
    
    def set_trigger_out(self, default_trigger_out = "ShutterOpen"):
        trigger_out_dic = {"Acquiring"          :6, 
                           "AlwaysHigh"         :5, 
                           "Exposing"           :8, 
                           "ReadingOut"         :10, 
                           "ShiftingUnderMask"  :7,  
                           "ShutterOpen"        :2, 
                           "WaitingForTrigger"  :11 }
        trigger_out_int = trigger_out_dic[default_trigger_out]
        self.experiment.SetValue(CameraSettings.HardwareIOOutputSignal, Int(trigger_out_int))
    
    def set_shutter_mode(self, default_shutter_mode = "Normal"):
        shutter_mode_dic = {"Normal":1, "AlwaysClosed":2, "AlwaysOpen":3}
        shutter_mode_int = shutter_mode_dic[default_shutter_mode]
        
        self.experiment.SetValue(CameraSettings.ShutterTimingMode, Int(shutter_mode_int))
        if self.debug: print("Shutter Mode: {}".format(default_shutter_mode))
    
    def get_shutter_opening_delay(self):
        shutter_opening_delay = self.experiment.GetValue(CameraSettings.ShutterTimingOpeningDelay)
        if self.debug: print("Shutter Opening Delay: {}".format(shutter_opening_delay))
        return shutter_opening_delay
    
    def set_shutter_opening_delay(self, default_op_delay = 20):
        self.experiment.SetValue(CameraSettings.ShutterTimingOpeningDelay, Int(default_op_delay))
        if self.debug: print("Shutter Opening Delay: {}".format(default_op_delay))
    
    def get_shutter_closing_delay(self):
        shutter_closing_delay = self.experiment.GetValue(CameraSettings.ShutterTimingClosingDelay)
        if self.debug: print("Shutter Closing Delay: {}".format(shutter_closing_delay))
        return shutter_closing_delay
        
    def set_shutter_closing_delay(self, default_cl_delay = 20):
        self.experiment.SetValue(CameraSettings.ShutterTimingClosingDelay, Int(default_cl_delay))
        if self.debug: print("Shutter Closing Delay: {}".format(default_cl_delay))

    def get_Temp(self):
        current_temp = self.experiment.GetValue(CameraSettings.SensorTemperatureReading)
        if self.debug: print("Current CCD Temperature: {}".format(current_temp))
        return current_temp
        
    def set_Temp(self, ccd_temp = -60.0):  
        self.experiment.SetValue(CameraSettings.SensorTemperatureSetPoint, Int(int(ccd_temp)))
        if self.debug: print("Target EMCCD Temperature: {}".format(ccd_temp))
    
    def set_custom_ROI(self, roi_dim_x , roi_dim_y, roi_width, roi_height, roi_xbinning, roi_ybinning):
        # Get device full dimensions
        print ("Test: {}, {}, {}, {}, {}, {}".format(roi_dim_x, roi_dim_y,roi_width, roi_height,roi_xbinning, roi_ybinning))
        regions = []
        # Add two ROI to regions
        regions.append(
            RegionOfInterest
            (roi_dim_x, roi_dim_y,
             roi_width, roi_height,
             roi_xbinning, roi_ybinning))
        
        # Set both ROI
        self.experiment.SetCustomRegions(regions)
    
        # Display the dimensions for each ROI
        if self.debug: 
            for roi in regions:
                self.print_region(roi)    

    
    def print_region(self, region):
        print("Custom Region Setting:")
        print(String.Format("{0} {1}", "\tX:", region.X))
        print(String.Format("{0} {1}", "\tY:", region.Y))
        print(String.Format("{0} {1}", "\tWidth:", region.Width))
        print(String.Format("{0} {1}", "\tHeight:", region.Height))
        print(String.Format("{0} {1}", "\tXBinning:", region.XBinning))
        print(String.Format("{0} {1}", "\tYBinning:", region.YBinning))
    
    def set_backgroung(self):
        #Not yet implemented
        pass
    
    def set_roitype(self, roitype = "CustomRegions"):
        roi_type_dic = {"FullSensor" : 1, "BinnedSensor" : 2, "LineSensor" : 3, "CustomRegions":4}
        self.roi_type_int = roi_type_dic[roitype]
        print('roi_type_in in device code: {}'.format(self.roi_type_int))
        self.experiment.SetValue(CameraSettings.ReadoutControlRegionsOfInterestSelection, Int(self.roi_type_int))
        
        if self.debug: print("Roi Type : {}".format(roitype))
        
    def set_XBinning(self, bin_width = 1):
        self.experiment.SetValue(CameraSettings.ReadoutControlRegionsOfInterestBinnedSensorXBinning, Int(bin_width))
        
        if self.debug: print("Bin Width : {}".format(bin_width))
        
    def set_YBinning(self, bin_width = 1, bin_height = 1):
        self.experiment.SetValue(CameraSettings.ReadoutControlRegionsOfInterestBinnedSensorYBinning, Int(bin_height))
        
        if self.debug: print("Bin Height : {}".format(bin_height))
        
    def get_XBinning(self):
        xbin = self.experiment.GetValue(CameraSettings.ReadoutControlRegionsOfInterestBinnedSensorXBinning)
        
        if self.debug: print("Bin Width : {}".format(xbin))
        return xbin
        
    def get_YBinning(self, bin_width = 1, bin_height = 1):
        ybin = self.experiment.GetValue(CameraSettings.ReadoutControlRegionsOfInterestBinnedSensorYBinning)
        
        if self.debug: print("Bin Height : {}".format(ybin))
        return ybin
    
    def get_exposure_time(self):
        exposure_time = self.experiment.GetValue(CameraSettings.ShutterTimingExposureTime)
        if self.debug: print("Exposure Time: {} ms".format(exposure_time))
        return exposure_time/1000
        
    def set_exposure_time(self, exposure_time):
        exposure_time = int(exposure_time*1000)
        if (exposure_time < 29):
            print("Minimum Exposure Time of the Shutter we are using is 29ms")
        self.experiment.SetValue(CameraSettings.ShutterTimingExposureTime, Int(exposure_time))
        if self.debug: print("Exposure Time: {} ms".format(exposure_time))
        
    def set_adc_quality(self, quality = "Low Noise"):
        adc_quality_dic = {"Low Noise" : 1, "Electron Multiplied" : 3}
        self.adc_quality_int = adc_quality_dic[quality]
        
        if self.adc_quality_int == 1:
            self.set_vertical_shift_rate(6.0)
        elif self.adc_quality_int == 3:
            self.set_vertical_shift_rate(3.0)
        self.experiment.SetValue(CameraSettings.AdcQuality, Int(self.adc_quality_int))
        if self.debug: print("ADC Quality: {}".format(quality))
        
        
    def set_adc_speed(self, adc_speed = 1.0):
        
        self.adc_speed = adc_speed
        
        if (self.adc_quality_int == 1 and self.adc_speed > 1.0):
            print("Maximum speeed for Low Noise Mode is 1Mhz. Speed is changed to 1Mhz")
            self.adc_speed = 1.0
        elif (self.adc_quality_int == 3 and self.adc_speed < 1.0):
            print("Minimum speed for Electron Multiplied Mode is 1Mhz. Speed is changed to 1Mhz")
            self.adc_speed = 1.0
        
        self.experiment.SetValue(CameraSettings.AdcSpeed, self.adc_speed)
        if self.debug: print("ADC Speed: {}".format(self.adc_speed))
        
        
    def set_adc_AnalogGain(self, gain = "High"):
        adc_AnalogGain_dic = {"Low" : 1, "Medium" : 2, "High" : 3}
        
        self.adc_AnalogGain_int = adc_AnalogGain_dic[gain]
        self.experiment.SetValue(CameraSettings.AdcAnalogGain, Int(self.adc_AnalogGain_int))
        if self.debug: print("ADC AnalogGain: {}".format(gain))
    
    def get_adc_EMGain(self):
        gain = self.experiment.GetValue(CameraSettings.AdcEMGain)
        if self.debug: print("ADC EMGain: {}".format(gain))
        return gain
        
    def set_adc_EMGain(self, gain = 1):
 
        if gain > 100:
            print ("Maximum EMGain is 100 in order not to damage ccd sensor.")
            gain = 100
        
        self.experiment.SetValue(CameraSettings.AdcEMGain, Int(gain))
        if self.debug: print("ADC EMGain: {}".format(gain))
        
        
    def get_device_dimensions(self):
        return self.experiment.FullSensorRegion

    def add_available_devices(self):
        # Add first available device and return
        count = 0
        # count 0 : Pixis BRE, count 1: proEM ccd, count 2: HRS 300
        for device in self.experiment.AvailableDevices:
            print("\n\tAdding Device...")
            self.experiment.Add(device)
            print(self.experiment.AvailableDevices)
            
            #if count > 0:
            #    self.experiment.Add(device)
            #count += 1
        return self.experiment.AvailableDevices    

    
    def device_found(self):
        # Find connected device
        for device in self.experiment.ExperimentDevices:
            if (device.Type == DeviceType.Camera):
                camera_status = True
            elif (device.Type == DeviceType.Spectrometer):
                spec_status = True
        if (camera_status == True and spec_status == True):
            if self.debug: print("LighField: Camera and Spectrometer connected ")
        else:
            raise IOError( "LighField: Error Finding a Camera or Spectrometer ")
            
        return True
    
    def close(self):
        for device in self.experiment.ExperimentDevices:
            self.experiment.Remove(device)


if __name__ == '__main__':
    print(os.environ['LIGHTFIELD_ROOT'])
    print(AutoResetEvent(False))

