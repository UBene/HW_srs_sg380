'''
Created on Dec 11, 2018

@author: Benedikt
'''

import time
from ScopeFoundry import Measurement, h5_io
import numpy as np


class CalibrationSweep(Measurement):
    
    name = 'calibration_sweep'

    def __init__(self, app, name=None,
                 camera_readout_measure_name='picam_readout',
                 spectrometer_hw_name='acton_spectrometer',
                 shutter_open_lq_path='hardware/shutter/open'):
        self.camera_readout_measure_name = camera_readout_measure_name
        self.spectrometer_hw_name = spectrometer_hw_name
        self.shutter_open_lq_path = shutter_open_lq_path
        Measurement.__init__(self, app, name)
        
    def setup(self):
        self.center_wl_range = self.settings.New_Range('center_wls')      
        self.record_bg = self.settings.New('record_bg', bool, initial=False)      
    
    def run(self):
        self.spec_readout = self.app.measurements[self.camera_readout_measure_name]
        
        if 'continuous' in self.camera_readout_measure_name.settings:
            self.spec_readout.settings['continuous'] = False 
        
        self.spec_center_wl = self.app.hardware[self.spectrometer_hw_name].settings.center_wl     
        
        self.t0 = time.time()      
        
        self.spectra = []
        self.center_wls = []  # center wls read from spectrometer
        self.wls = []  # intended for intensity calibration 

        if self.record_bg.val:
            self.shutter_open = self.app.lq_path(self.shutter_open_lq_path)
            self.bg_spectra = []
        
        N = len(self.center_wl_range.array)
        
        for i, center_wl in enumerate(self.center_wl_range.array):
            if self.interrupt_measurement_called:
                break

            self.set_progress(100 * (i + 1) / N)
            
            self.spec_center_wl.update_value(center_wl)
            self.spec_center_wl.write_to_hardware()
            time.sleep(1.)
            
            if self.record_bg.val:
                self.shutter_open.update_value(False)
                print('closing shutter for background acquisition')
                time.sleep(2)
                self.start_nested_measure_and_wait(self.spec_readout, polling_time=0.1, start_time=0.1)
                self.shutter_open.update_value(True)
                self.bg_spectra.append(self.spec_readout.get_spectrum())
                print('opening shutter')
                time.sleep(2)
            if self.interrupt_measurement_called:
                break

            self.start_nested_measure_and_wait(self.spec_readout, nested_interrupt=False)
            time.sleep(0.1)
            
            self.spectra.append(self.spec_readout.get_spectrum())
            self.center_wls.append(self.spec_center_wl.val)
            try:
                self.wls.append(self.spec_readout.get_wavelengths())
            except:
                print(self.spec_readout, 'has no get_wavelengths() method: wls will not be saved')
                
        self.h5_file = h5_io.h5_base_file(self.app, measurement=self)
        # self.h5_file.attrs['time_id'] = self.t0
        H = self.h5_meas_group = h5_io.h5_create_measurement_group(self, self.h5_file)
        H['spectra'] = np.array(self.spectra)
        H['center_wls'] = np.array(self.center_wls)
        H['wls'] = np.array(self.wls)  # intended for intensity calibration 
        if self.record_bg.val:
            H['bg_spectra'] = np.array(self.bg_spectra)
        
        self.h5_file.close()
