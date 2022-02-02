import numpy as np
from ScopeFoundryHW.asi_stage.asi_stage_raster import ASIStage2DScan, ASIStage3DScan
from qtpy.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel
import math
import time
from h5py import h5
import pyqtgraph as pg
from qtpy import QtCore
import glob
import os


class ASIHyperSpec2DScan(ASIStage2DScan):
    
    def __init__(self, app):
        ASIStage2DScan.__init__(self, app)
        
    def setup(self):
        self.settings.New('debug',dtype=bool,initial=False)
        ASIStage2DScan.setup(self)
    
    def scan_specific_setup(self):
        #Hardware                  
        self.stage = self.app.hardware['asi_stage']
        self.add_operation('center scan on position',self.center_scan_on_pos)
        self.add_operation('center view on scan', self.center_view_on_scan)
        
        details_widget = QWidget()
        details = QVBoxLayout()
        details.addWidget(self.app.settings.New_UI(include=['save_dir','sample']))
        scan_params_settings = ['h_span', 'pixel_time', 'v_span',  'frame_time']
        details.addWidget(create_grid_layout_widget(self.settings, scan_params_settings))
        details.addWidget(create_operation_grid(self.operations))
        details_widget.setLayout(details)
        self.set_details_widget(widget=details_widget)
        
    def pre_scan_setup(self):
        self.settings.save_h5.change_readonly(True)
        if 'bg_subtract' in self.spec.settings:
            self.spec.settings['bg_subtract'] = False
        self.spec.settings['continuous'] = False
        self.spec.settings['save_h5'] = False
        time.sleep(0.01)
        self.stage.other_observer = True
    
    def collect_pixel(self, pixel_num, k, j, i):
        if self.settings['debug']: print("collect_pixel", pixel_num, k,j,i)
        self.spec.interrupt_measurement_called = self.interrupt_measurement_called
        # self.start_nested_measure_and_wait(self.spec)
        self.spec.run()
        print('spectrometer run complete')
        if pixel_num == 0:
            self.log.info("pixel 0: creating data arrays")
            if self.settings['debug']: print("pixel 0: creating data arrays")
            self.time_array = np.zeros(self.scan_h_positions.shape)
            spec_map_shape = self.scan_shape + self.spec.spectrum.shape
            
            self.spec_map = np.zeros(spec_map_shape, dtype=np.float)
            if self.settings['save_h5']:
                self.spec_map_h5 = self.h5_meas_group.create_dataset(
                                      'spec_map', spec_map_shape, dtype=np.float)
            else:
                self.spec_map_h5 = np.zeros(spec_map_shape)
 
            self.wls = np.array(self.spec.wls)
            if self.settings['save_h5']:
                self.h5_meas_group['wls'] = self.wls

        # store in arrays
        t = self.time_array[pixel_num] = time.time()
        print('time', t)
        spec = np.array(self.spec.spectrum)
        print(f"collect_pixel, {pixel_num}, {k}, {j}, {i}, {spec.shape}")
        self.spec_map[k,j,i,:] = spec
        self.spec_map_h5[k,j,i,:] = spec
        s = self.display_image_map[k,j,i] = spec.sum()
        if self.settings['debug']: print('time', t, 'sum', s)
        
    def post_scan_cleanup(self):
        self.settings.save_h5.change_readonly(False)
        self.stage.other_observer = False
        self.ui.setWindowTitle(self.name)

    def update_time(self):
        if ('run' in self.settings['run_state']) and hasattr(self, 'time_array'):
            
            if self.time_array[2] != 0:
                print(len(self.time_array))
                px_times = np.diff(self.time_array)
                print(np.nonzero(px_times)[0])
                num_px = len(np.nonzero(px_times)[0])
                avg_pixel_time = np.average(px_times[0:(num_px-1)])
                print(avg_pixel_time)
                self.settings.pixel_time.update_value(avg_pixel_time)
                
                total_time = np.sum(px_times[0:num_px-1])
                total_time_str = seconds_to_time_string(total_time)
                elapsed_time_str = seconds_to_time_string(self.settings['total_time'] - total_time)
                # self.ui.status_lineEdit.setText("time elapsed: %s, time remaining: %s" % (total_time_str, elapsed_time_str))
                self.ui.setWindowTitle("%s time elapsed: %s, time remaining: %s" % (self.name, total_time_str, elapsed_time_str))
        else: 
            for kk in ['exposure_time', 'int_time']:
                if kk in list(self.spec.hw.settings.keys()):
                    if self.settings['pixel_time'] != self.spec.hw.settings[kk]:
                        self.settings.pixel_time.update_value(self.spec.hw.settings[kk])
                        #self.ui.status_lineEdit.setText("estimated scan duration: %s" % seconds_to_time_string(self.settings['total_time']))
    
    
    def center_scan_on_pos(self):
        self.settings.h_center.update_value(new_val=self.stage.settings.x_position.val)
        self.settings.v_center.update_value(new_val=self.stage.settings.y_position.val)
        
    def center_view_on_scan(self):
        delta = 0.2
        del_h = self.h_span.val*delta
        del_v = self.v_span.val*delta
        self.img_plot.setRange(xRange=(self.h0.val-del_h, self.h1.val+del_h), yRange=(self.v0.val-del_v, self.v1.val+del_v))

    def interrupt(self):
        ASIStage2DScan.interrupt(self)
        self.spec.interrupt()
    
    def update_display(self):
        self.update_time()
        ASIStage2DScan.update_display(self)
        self.spec.update_display()
        
    
    def update_LUT(self):
        ''' override this function to control display LUT scaling'''
        self.hist_lut.imageChanged(autoLevel=True)
#         # DISABLE below because of crashing TODO - fix this?
#         non_zero_index = np.nonzero(self.disp_img)
#         if len(non_zero_index[0]) > 0:
#             self.hist_lut.setLevels(*np.percentile(self.disp_img[non_zero_index],(1,99)))


class ASIHyperSpec3DScan(ASIStage3DScan):
    
    def __init__(self, app):
        ASIStage3DScan.__init__(self, app)
        
    def setup(self):
        self.settings.New('debug',dtype=bool,initial=False)
        ASIStage3DScan.setup(self)
    
    def scan_specific_setup(self):
        #Hardware                  
        self.stage = self.app.hardware['asi_stage']
        self.add_operation('center scan on position',self.center_scan_on_pos)
        self.add_operation('center scan XY on position', self.center_xy_on_pos)
        self.add_operation('center view on scan', self.center_view_on_scan)
        self.add_operation('set z0', self.set_z0)
        
        details_widget = QWidget()
        details = QVBoxLayout()
        #details.addWidget(self.app.settings.New_UI(include=['save_dir','sample']))
        details.addWidget(create_grid_layout_widget(self.app.settings,['save_dir', 'sample']))
        scan_params_settings = ['h_span', 'pixel_time', 'v_span', 'frame_time', 'z_span', 'total_time']
        details.addWidget(create_grid_layout_widget(self.settings, scan_params_settings))
        
        details.addWidget(create_operation_grid(self.operations, num_cols=4))
        details_widget.setLayout(details)
        self.set_details_widget(widget=details_widget)
        
    def pre_scan_setup(self):
        self.settings.save_h5.change_readonly(True)
        self.spec.settings['bg_subtract'] = False
        self.spec.settings['continuous'] = False
        self.spec.settings['save_h5'] = False
        time.sleep(0.01)
        self.stage.other_observer = True
    
    def collect_pixel(self, pixel_num, k, j, i):
        if self.settings['debug']: print("collect_pixel", pixel_num, k,j,i)
        self.spec.interrupt_measurement_called = self.interrupt_measurement_called

        # self.start_nested_measure_and_wait(self.spec)
        self.spec.run()
        
        if pixel_num == 0:
            self.log.info("pixel 0: creating data arrays")
            spec_map_shape = self.scan_shape + self.spec.spectrum.shape
            self.time_array = np.zeros(self.scan_h_positions.shape, dtype=np.float)
            self.spec_map = np.zeros(spec_map_shape, dtype=np.float)
            if self.settings['save_h5']:
                self.spec_map_h5 = self.h5_meas_group.create_dataset(
                                      'spec_map', spec_map_shape, dtype=np.float)
            else:
                self.spec_map_h5 = np.zeros(spec_map_shape)
 
            self.wls = np.array(self.spec.wls)
            if self.settings['save_h5']:
                self.h5_meas_group['wls'] = self.wls

        # store in arrays
        spec = np.array(self.spec.spectrum)
        self.time_array[pixel_num] = time.time()
        self.spec_map[k,j,i,:] = spec
        self.spec_map_h5[k,j,i,:] = spec
        self.display_image_map[k,j,i] = spec.sum()
        
    def post_scan_cleanup(self):
        self.settings.save_h5.change_readonly(False)
        self.stage.other_observer = False
        del self.time_array

    def center_scan_on_pos(self):
        self.settings.h_center.update_value(new_val=self.stage.settings.x_position.val)
        self.settings.v_center.update_value(new_val=self.stage.settings.y_position.val)
        self.settings.z_center.update_value(new_val=self.stage.settings.z_position.val)
        
    def center_view_on_scan(self):
        delta = 0.2
        del_h = self.h_span.val*delta
        del_v = self.v_span.val*delta
        self.img_plot.setRange(xRange=(self.h0.val-del_h, self.h1.val+del_h), yRange=(self.v0.val-del_v, self.v1.val+del_v))
        
    def set_z0(self):
        span = self.settings['z_span']
        pos = self.stage.settings['z_position']
        self.settings.z0.update_value(pos)
        self.settings.z1.update_value(pos+span)
        
    def center_xy_on_pos(self):
        self.settings.h_center.update_value(new_val=self.stage.settings.x_position.val)
        self.settings.v_center.update_value(new_val=self.stage.settings.y_position.val)
    
    def update_time(self):
        if ('run' in self.settings['run_state']) and hasattr(self, 'time_array'):
            if self.time_array[0] != 0:
                px_times = np.diff(self.time_array)
                num_px = len(np.nonzero(px_times)[0])
                avg_pixel_time = np.average(px_times[0:num_px-1])
                self.settings.pixel_time.update_value(avg_pixel_time)
                
                total_time = np.sum(px_times[0:num_px-1])
                total_time_str = seconds_to_time_string(total_time)
                elapsed_time_str = seconds_to_time_string(self.settings['total_time'] - total_time)
                self.ui.status_lineEdit.setText("time elapsed: %s, time remaining: %s" % (total_time_str, elapsed_time_str))
        else: 
            for kk in ['exposure_time', 'int_time']:
                if kk in list(self.spec.hw.settings.keys()):
                    if self.settings['pixel_time'] != self.spec.hw.settings[kk]:
                        self.settings.pixel_time.update_value(self.spec.hw.settings[kk])
                        self.ui.status_lineEdit.setText("estimated scan duration: %s" % seconds_to_time_string(self.settings['total_time']))
    
    def interrupt(self):
        ASIStage3DScan.interrupt(self)
        self.spec.interrupt()
    
    def update_display(self):
        self.update_time()
        ASIStage3DScan.update_display(self)
        self.spec.update_display()
    
    def update_LUT(self):
        ''' override this function to control display LUT scaling'''
        self.hist_lut.imageChanged(autoLevel=True)
#         # DISABLE below because of crashing TODO - fix this?
#         non_zero_index = np.nonzero(self.disp_img)
#         if len(non_zero_index[0]) > 0:
#             self.hist_lut.setLevels(*np.percentile(self.disp_img[non_zero_index],(1,99)))


class AndorHyperSpecASIScan(ASIStage2DScan):
    
    name = "asi_hyperspec_scan"
    #name = "ASI_2DHyperspecscan"
    
    def scan_specific_setup(self):
        #Hardware
        self.stage = self.app.hardware['asi_stage']
        self.andor_ccd_readout = self.app.measurements['andor_ccd_readout']
        
        

    def pre_scan_setup(self):
        self.andor_ccd_readout.settings['acquire_bg'] = False
        self.andor_ccd_readout.settings['continuous'] = False
        self.andor_ccd_readout.settings['save_h5'] = False
        time.sleep(0.01)
    
    def collect_pixel(self, pixel_num, k, j, i):
        print("collect_pixel", pixel_num, k,j,i)
        self.andor_ccd_readout.interrupt_measurement_called = self.interrupt_measurement_called

        self.andor_ccd_readout.settings['continuous'] = False
        self.andor_ccd_readout.settings['save_h5'] = False
        self.andor_ccd_readout.run()
        
        if pixel_num == 0:
            self.log.info("pixel 0: creating data arrays")
            spec_map_shape = self.scan_shape + self.andor_ccd_readout.spectra_data.shape
            
            self.spec_map = np.zeros(spec_map_shape, dtype=np.float)
            self.spec_map_h5 = self.h5_meas_group.create_dataset(
                                 'spec_map', spec_map_shape, dtype=np.float)

            self.wls = np.array(self.andor_ccd_readout.wls)
            self.h5_meas_group['wls'] = self.wls

        # store in arrays
        spec = self.andor_ccd_readout.spectra_data
        self.spec_map[k,j,i,:] = spec
        if self.settings['save_h5']:
            self.spec_map_h5[k,j,i,:] = spec
  
        self.display_image_map[k,j,i] = spec.sum()


    def post_scan_cleanup(self):
        self.andor_ccd_readout.settings['save_h5'] = True
        
    def update_display(self):
        ASIStage2DScan.update_display(self)
        self.andor_ccd_readout.update_display()
            
    def insert_bg_from_folder(self, folder=None):
        if folder is None:
            folder = self.app.settings['save_dir']
            print(folder)
        bg_files = glob.glob(os.path.join(folder, '*toupcam*'))
        print(bg_files)
        for fname in bg_files:
            #try:
            self.insert_bg_img(os.path.join(folder, fname))
            #except:
                #print('failed to import:',fname)
                   
    def clear_bg_img(self):
        if hasattr(self, 'img_bkg_items') and hasattr(self, 'img_plot'):
            for item in self.img_bkg_items:
                self.img_plot.removeItem(item)
                            
    def insert_bg_img(self, fname=None):         
        #self.bkg_data = load_image('C:\\Users\\lab\\Documents\\image_100.tif')
        # remove existing
        #if hasattr(self, 'img_bkg'):
        #    self.img_plot.removeItem(self.img_bkg)
        import h5py
        with h5py.File(fname, mode='r') as H:
            self.bg_im = np.array(H['measurement/toupcam_live/image'])
            try:
                x_center_stage = H['hardware/asi_stage/settings'].attrs['x_position']
                y_center_stage = H['hardware/asi_stage/settings'].attrs['y_position']
            except:
                x_center = 0.
                y_center = 0.
                print('no coordinates found, loading image at (zero, zero)')
                
            x_center, y_center = H['hardware/toupcam/settings'].attrs['centerx_micron'],H['hardware/toupcam/settings'].attrs['centery_micron']
            width, height = H['hardware/toupcam/settings'].attrs['width_micron'], H['hardware/toupcam/settings'].attrs['height_micron']
            
        if  self.h_unit == 'mm':
            width /= 1000.
            height /= 1000.
            x_center /= 1000.
            y_center /= 1000.
            
        print(np.shape(self.bg_im))
        
        x0_bkg = x_center_stage - x_center
        y0_bkg = y_center_stage - y_center
        
        print('|center:', x_center_stage,y_center_stage, '|corner:', x0_bkg,y0_bkg, '|size:', width,height)
        
        self.img_bkg = pg.ImageItem(self.bg_im)
        if hasattr(self, 'img_bkg_items'):
            self.img_bkg_items.append(self.img_bkg)
        else:
            self.img_bkg_items = [self.img_bkg]
        self.img_bkg_rect = QtCore.QRectF(x0_bkg, y0_bkg, width, height)
        print("Rect: ", self.img_bkg_rect)
        self.img_plot.addItem(self.img_bkg)
        self.img_bkg.setRect(self.img_bkg_rect)
        self.img_bkg.setZValue(-1)
        
        
        

def create_grid_layout_widget(lq_collection, lq_names, num_cols=2):
    layout = QGridLayout()
    ii = 1
    ni = num_cols
    for key in lq_names:
        col = (ii - 1) % ni
        row = math.ceil(ii / ni) - 1
        layout.addWidget(QLabel(key),row,2*col)
        layout.addWidget(lq_collection.get_lq(key).new_default_widget(),row,2*col+1)
        ii += 1
    widget = QWidget()
    widget.setLayout(layout)
    return widget

def create_operation_grid(op_dict, num_cols=3):
    widget = QWidget()
    layout = QGridLayout()
    ii = 1
    ni = num_cols
    for key in list(op_dict.keys()):
        col = (ii - 1) % ni
        row = math.ceil(ii / ni) - 1
        pushButton = QPushButton(text=key)
        pushButton.clicked.connect(op_dict[key])
        layout.addWidget(pushButton,row,col)
        ii += 1
    widget.setLayout(layout)
    return widget

def seconds_to_time_string(val):
    val = int(val)
    mins = val / 60
    sec = val % 60
    hrs = mins / 60
    mins = mins % 60
    return "{:02d}:{:02d}:{:02d}" .format(int(hrs), int(mins), int(sec))
