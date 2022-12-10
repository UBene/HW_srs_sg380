'''
Created on Feb 4, 2016

@author: Edward Barnard
'''

from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file,replace_widget_in_layout
import numpy as np
import pyqtgraph as pg
from ScopeFoundry import h5_io
import time
from qtpy import QtCore
from ScopeFoundry import LQRange

def ijk_zigzag_generator(dims, axis_order=(0,1,2)):
    """3D zig-zag scan pattern generator with arbitrary fast axis order"""

    ax0, ax1, ax2 = axis_order
    
    for i_ax0 in range( dims[ax0] ):
        zig_or_zag0 = (1,-1)[i_ax0 % 2]
        for i_ax1 in range( dims[ax1] )[::zig_or_zag0]:
            zig_or_zag1 = (1,-1)[(i_ax0+i_ax1) % 2]
            for i_ax2 in range( dims[ax2] )[::zig_or_zag1]:
            
                ijk = [0,0,0]
                ijk[ax0] = i_ax0
                ijk[ax1] = i_ax1
                ijk[ax2] = i_ax2
                
                yield tuple(ijk)
    return

class PowerScanMap2D(Measurement):
    name = "power_scan_map"
    
    def __init__(self, app, 
                 h_limits=(0,3200),        v_limits=(0,3200), 
                 h_unit='',              v_unit='', 
                 h_spinbox_decimals=0,   v_spinbox_decimals=0,
                 h_spinbox_step=1.0,     v_spinbox_step=1.0,
                 use_external_range_sync=False):    
            
        self.h_spinbox_decimals = h_spinbox_decimals
        self.v_spinbox_decimals = v_spinbox_decimals
        self.h_spinbox_step = h_spinbox_step
        self.v_spinbox_step = v_spinbox_step
        self.h_limits = h_limits
        self.v_limits = v_limits
        self.h_unit = h_unit
        self.v_unit = v_unit
        self.use_external_range_sync = use_external_range_sync
        Measurement.__init__(self, app)
        
    def setup(self):
        self.ui_filename = sibling_path(__file__,"power_scan_map.ui")
        self.ui = load_qt_ui_file(self.ui_filename)
        #self.ui.show()
        self.ui.setWindowTitle(self.name)
        
        #self.stage_x = self.app.hardware.side_beam_power_wheel
        #self.stage_y = self.app.hardware.main_beam_power_wheel
        #self.stage_x_dev = self.stage_x.power_wheel_dev
        #self.stage_y_dev = self.stage_y.power_wheel_dev
        self.ax_map = dict(side=0, main=1)
        
        self.display_update_period = 0.010 #seconds
        
        #connect events        

        # local logged quantities
        h_lq_params = dict(vmin=self.h_limits[0], vmax=self.h_limits[1], unit=self.h_unit, 
                                spinbox_decimals=self.h_spinbox_decimals, spinbox_step=self.h_spinbox_step,
                                dtype=float,ro=False)
        h_range = self.h_limits[1] - self.h_limits[0]
        self.h0 = self.settings.New('h0',  initial=self.h_limits[0]+h_range*0.25, **h_lq_params  )
        self.h1 = self.settings.New('h1',  initial=self.h_limits[0]+h_range*0.75, **h_lq_params  )
        v_lq_params = dict(vmin=self.v_limits[0], vmax=self.v_limits[1], unit=self.v_unit, 
                                spinbox_decimals=self.v_spinbox_decimals, spinbox_step=self.v_spinbox_step,
                                dtype=float,ro=False)
        v_range = self.v_limits[1]-self.v_limits[0]
        self.v0 = self.settings.New('v0',  initial=self.v_limits[0] + v_range*0.25, **v_lq_params  )
        self.v1 = self.settings.New('v1',  initial=self.v_limits[0] + v_range*0.75, **v_lq_params  )

        lq_params = dict(dtype=float, vmin=1, vmax=abs(h_range), ro=False, unit=self.h_unit )
        self.dh = self.settings.New('dh', initial=self.h_spinbox_step, **lq_params)
        self.dh.spinbox_decimals = self.h_spinbox_decimals
        lq_params = dict(dtype=float, vmin=1, vmax=abs(v_range), ro=False, unit=self.v_unit )
        self.dv = self.settings.New('dv', initial=self.v_spinbox_step, **lq_params)
        self.dv.spinbox_decimals = self.v_spinbox_decimals
        
        self.Nh = self.settings.New('Nh', initial=11, vmin=1, dtype=int, ro=False)
        self.Nv = self.settings.New('Nv', initial=11, vmin=1, dtype=int, ro=False)
        
        self.h_center = self.settings.New('h_center', dtype=float, ro=False)
        self.v_center = self.settings.New('v_center', dtype=float, ro=False)

        self.h_span = self.settings.New('h_span', dtype=float, ro=False)
        self.v_span = self.settings.New('v_span', dtype=float, ro=False)
        
        self.settings.New("h_axis", initial="side", dtype=str, choices=("side",))
        self.settings.New("v_axis", initial="main", dtype=str, choices=("main",))
        
        self.Npixels = self.Nh.val*self.Nv.val
        
        self.scan_type = self.settings.New('scan_type', dtype=str, initial='serpentine',
                                                  choices=('raster', 'serpentine', 'trace_retrace', 
                                                           'ortho_raster', 'ortho_trace_retrace'))
        
        self.speed = self.settings.New('speed', dtype=str, initial='slow',
                                                  choices=('slow',))
        
        self.continuous_scan = self.settings.New("continuous_scan", dtype=bool, initial=False)
        self.settings.New('save_h5', dtype=bool, initial=True, ro=False)
        self.settings.New('update_position', dtype=bool, initial=True)
        
        self.settings.New('show_previous_scans', dtype=bool, initial=True)
        
        
        self.settings.New('n_frames', dtype=int, initial=1, vmin=1)
        
        self.settings.New('pixel_time', dtype=float, ro=True, si=True, initial=0.01, unit='s')
        self.settings.New('line_time' , dtype=float, ro=True, si=True, unit='s')
        self.settings.New('frame_time' , dtype=float, ro=True, si=True, unit='s')        
        self.settings.New('total_time', dtype=float, ro=True, si=True, unit='s')
        
        for lq_name in ['Nh', 'Nv', 'pixel_time', 'n_frames']:
            self.settings.get_lq(lq_name).add_listener(self.compute_times)
            
        self.compute_times()
        
        if not self.use_external_range_sync:
            self.h_range = LQRange(self.h0, self.h1, self.dh, self.Nh, self.h_center, self.h_span)    
            self.v_range = LQRange(self.v0, self.v1, self.dv, self.Nv, self.v_center, self.v_span)

        for s in 'h0 h1 dh v0 v1 dv'.split():
            self.settings.get_lq(s).add_listener(self.compute_scan_params)

        self.scan_type.updated_value.connect(self.compute_scan_params)
        
        #connect events
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)

        self.h0.connect_to_widget(self.ui.h0_doubleSpinBox)
        self.h1.connect_to_widget(self.ui.h1_doubleSpinBox)
        self.v0.connect_to_widget(self.ui.v0_doubleSpinBox)
        self.v1.connect_to_widget(self.ui.v1_doubleSpinBox)
        self.dh.connect_to_widget(self.ui.dh_doubleSpinBox)
        self.dv.connect_to_widget(self.ui.dv_doubleSpinBox)
        self.Nh.connect_to_widget(self.ui.Nh_doubleSpinBox)
        self.Nv.connect_to_widget(self.ui.Nv_doubleSpinBox)
        self.scan_type.connect_to_widget(self.ui.scan_type_comboBox)
        self.speed.connect_to_widget(self.ui.speed_comboBox)
        
        self.progress.connect_to_widget(self.ui.progress_doubleSpinBox)
        #self.progress.updated_value[str].connect(self.ui.xy_scan_progressBar.setValue)
        #self.progress.updated_value.connect(self.tree_progressBar.setValue)

        self.settings.continuous_scan.connect_to_widget(
            self.ui.continuous_scan_checkBox)
        self.settings.save_h5.connect_to_widget(
            self.ui.save_h5_checkBox)
        self.settings.update_position.connect_to_widget(
            self.ui.update_position_checkBox)
        
        
        self.settings.show_previous_scans.connect_to_widget(
            self.ui.show_previous_scans_checkBox)

        self.initial_scan_setup_plotting = False
        self.scan_specific_setup()
        

        self.add_operation('clear_previous_scans', self.clear_previous_scans)

        self.ui.clear_previous_scans_pushButton.clicked.connect(
            self.clear_previous_scans)
        
        self.compute_scan_params()
        
    def set_details_widget(self, widget = None, ui_filename=None):
        #print('LOADING DETAIL UI')
        if ui_filename is not None:
            details_ui = load_qt_ui_file(ui_filename)
        if widget is not None:
            details_ui = widget
        if hasattr(self, 'details_ui'):
            if self.details_ui is not None:
                self.details_ui.deleteLater()
                self.ui.details_groupBox.layout().removeWidget(self.details_ui)
                #self.details_ui.hide()
                del self.details_ui
        self.details_ui = details_ui
        #return replace_widget_in_layout(self.ui.details_groupBox,details_ui)
        self.ui.details_groupBox.layout().addWidget(self.details_ui)
        return self.details_ui
        
    def set_h_limits(self, vmin, vmax, set_scan_to_max=False):
        self.settings.h0.change_min_max(vmin, vmax)
        self.settings.h1.change_min_max(vmin, vmax)
        if set_scan_to_max:
            self.settings['h0'] = vmin
            self.settings['h1'] = vmax
    def set_v_limits(self, vmin, vmax, set_scan_to_max=False):
        self.settings.v0.change_min_max(vmin, vmax)
        self.settings.v1.change_min_max(vmin, vmax)
        if set_scan_to_max:
            self.settings['v0'] = vmin
            self.settings['v1'] = vmax

    def compute_scan_params(self):
        self.log.debug('compute_scan_params')
        # Don't recompute if a scan is running!
        if self.is_measuring():
            return # maybe raise error

        #self.h_array = self.h_range.array #np.arange(self.h0.val, self.h1.val, self.dh.val, dtype=float)
        #self.v_array = self.v_range.array #np.arange(self.v0.val, self.v1.val, self.dv.val, dtype=float)
        
        #self.Nh.update_value(len(self.h_array))
        #self.Nv.update_value(len(self.v_array))
        
        self.range_extent = [self.h0.val, self.h1.val, self.v0.val, self.v1.val]

        #self.corners =  [self.h_array[0], self.h_array[-1], self.v_array[0], self.v_array[-1]]
        self.corners = self.range_extent
        
        self.imshow_extent = [self.h0.val - 0.5*self.dh.val,
                              self.h1.val + 0.5*self.dh.val,
                              self.v0.val - 0.5*self.dv.val,
                              self.v1.val + 0.5*self.dv.val]
        
        self.compute_times()
        
        # call appropriate scan generator to determine scan size, don't compute scan arrays yet
        getattr(self, "gen_%s_scan" % self.scan_type.val)(gen_arrays=False)
    
    def compute_scan_arrays(self):
        print("params")
        self.compute_scan_params()
        gen_func_name = "gen_%s_scan" % self.scan_type.val
        print("gen_arrays:", gen_func_name)
        # calls correct scan generator function
        getattr(self, gen_func_name)(gen_arrays=True)
    
    def create_empty_scan_arrays(self):
        self.scan_h_positions = np.zeros(self.Npixels, dtype=float)
        self.scan_v_positions = np.zeros(self.Npixels, dtype=float)
        #self.scan_move_speed   = np.zeros(self.Npixels, dtype=str)
        self.scan_index_array = np.zeros((self.Npixels, 3), dtype=int)
    
    
    def pre_scan_setup(self):
        ####Move slider to turn on illumination   
        ### Note: have trouble in reading position of slider 
        #if self.app.hardware.dual_position_slider.slider_pos.val == 'Closed':
        print ('Now open shutter...')
        self.app.hardware.dual_position_slider.move_bkwd()
        print("before if self.settings['collect_apd']")
        
        self.apd_counter_hw = self.app.hardware.apd_counter
        self.pm_powers_map       = np.zeros((2, 1, self.Nv.val, self.Nh.val), dtype=float)
        self.pm_powers_after_map = np.zeros((2, 1, self.Nv.val, self.Nh.val), dtype=float)
        
        if self.settings['collect_apd']:
            self.count_rate_map = np.zeros((1, self.Nv.val, self.Nh.val), dtype=float)
            #self.count_rate_map_h5 = self.h5_meas_group.create_dataset('count_rate_map',shape=(1, self.Nv.val, self.Nh.val), dtype=float, compression='gzip', shuffle=True)
            print("after if self.settings['collect_apd']")
            print("test_count_rate_map:{}", self.count_rate_map)
            self.apd_counter_hw = self.app.hardware.apd_counter
            self.apd_count_rate_lq = self.apd_counter_hw.settings.apd_count_rate         
            self.count_rate_map = np.zeros((1, self.Nv.val, self.Nh.val), dtype=float) ##Note: this data array needs to be setup before runing, otherwise will see display update errors
                  
        elif self.settings['collect_spectrum']:
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

    
    
    
    def pre_run(self):
        # set all logged quantities read only
        for lqname in "h0 h1 v0 v1 dh dv Nh Nv".split():
            self.settings.as_dict()[lqname].change_readonly(True)
            
        self.compute_scan_params()

    
    def post_run(self):
            # set all logged quantities writable
            for lqname in "h0 h1 v0 v1 dh dv Nh Nv".split():
                self.settings.as_dict()[lqname].change_readonly(False)

    def clear_qt_attr(self, attr_name):
        if hasattr(self, attr_name):
            attr = getattr(self, attr_name)
            attr.deleteLater()
            del attr
            
    def setup_figure(self):
        self.compute_scan_params()
        
        
        
        self.clear_qt_attr('graph_layout')
        self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)
        
        self.clear_qt_attr('img_plot')
        self.img_plot = self.graph_layout.addPlot()

        self.img_items = []
        
        
        self.img_item = pg.ImageItem()
        self.img_items.append(self.img_item)
        
        self.img_plot.addItem(self.img_item)
        self.img_plot.showGrid(x=True, y=True)
        self.img_plot.setAspectLocked(lock=True, ratio=1)
        

        self.hist_lut = pg.HistogramLUTItem()
        self.graph_layout.addItem(self.hist_lut)

        
        #self.clear_qt_attr('current_stage_pos_arrow')
        self.current_stage_pos_arrow = pg.ArrowItem()
        self.current_stage_pos_arrow.setZValue(100)
        self.img_plot.addItem(self.current_stage_pos_arrow)
        
        #self.stage = self.app.hardware_components['dummy_xy_stage']


        
        self.graph_layout.nextRow()
        self.pos_label = pg.LabelItem(justify='right')
        self.pos_label.setText("=====")
        self.graph_layout.addItem(self.pos_label)

        self.scan_roi = pg.ROI([0,0],[1,1], movable=True)
        self.scan_roi.addScaleHandle([1, 1], [0, 0])
        self.scan_roi.addScaleHandle([0, 0], [1, 1])
        self.update_scan_roi()
        self.scan_roi.sigRegionChangeFinished.connect(self.mouse_update_scan_roi)
        
        self.img_plot.addItem(self.scan_roi)        
        for lqname in 'h0 h1 v0 v1 dh dv'.split():
            self.settings.as_dict()[lqname].updated_value.connect(self.update_scan_roi)
                    
        self.img_plot.scene().sigMouseMoved.connect(self.mouseMoved)
        
        # GoTo position context menu
        #self.goto_cmenu_action = QtWidgets.QAction("GoTo Position", self.img_plot.scene())
        #self.img_plot.scene().contextMenu.append(self.goto_cmenu_action)
        #self.goto_cmenu_action.triggered.connect(self.on_goto_position)
        
        # Point ROI
        self.pt_roi = pg.CircleROI( (0,0), (2,2) , movable=True, pen=(0,9))
        #self.pt_roi.removeHandle(self.pt_roi.getHandles()[0])
        h = self.pt_roi.addTranslateHandle((0.5,.5))
        h.pen = pg.mkPen('r')
        h.update()
        self.img_plot.addItem(self.pt_roi)
        self.pt_roi.removeHandle(0)
        #self.pt_roi_plotline = pg.PlotCurveItem([0], pen=(0,9))
        #self.imview.getView().addItem(self.pt_roi_plotline) 
        self.pt_roi.sigRegionChangeFinished[object].connect(self.on_update_pt_roi)
        
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

    def on_update_pt_roi(self, roi=None):
        if roi is None:
            roi = self.circ_roi
        roi_state = roi.saveState()
        x0, y0 = roi_state['pos']
        xc = x0 + 1
        yc = y0 + 1
        self.new_pt_pos(xc,yc)
    
    def new_pt_pos(self, x,y):
        self.move_position_start(x, y)
        print('new_pt_pos', x,y)

    
    def mouse_update_scan_roi(self):
        x0,y0 =  self.scan_roi.pos()
        w, h =  self.scan_roi.size()
        self.h_center.update_value(x0 + w/2)
        self.v_center.update_value(y0 + h/2)
        self.h_span.update_value(w-self.dh.val)
        self.v_span.update_value(h-self.dv.val)
        self.compute_scan_params()
        self.update_scan_roi()
        
    def update_scan_roi(self):
        self.log.debug("update_scan_roi")
        x0, x1, y0, y1 = self.imshow_extent
        self.scan_roi.blockSignals(True)
        self.scan_roi.setPos( (x0, y0, 0))
        self.scan_roi.setSize( (x1-x0, y1-y0, 0))
        self.scan_roi.blockSignals(False)
        
    def update_arrow_pos(self):
        #### Modified 08/03/2018 Kaiyuan
        
        #######Note: this function does not physically read the current stage position. If only reads whatever the software (hardware component) already registered.
        #######  So we need to read stage position to actually update arrow position.
        x = self.stage_x.settings['encoder_pos']
        y = self.stage_y.settings['encoder_pos']
        #self.current_stage_pos_arrow.setPos(x,y)
        
        ###########Need to map h, v to XYZ
        if self.settings['h_axis'] =='side':
            h = x
        elif self.settings['h_axis'] =='main':
            h = y

        
        if self.settings['v_axis'] =='side':
            v = x
        elif self.settings['v_axis'] =='main':
            v = y
 
        self.current_stage_pos_arrow.setPos(h,v)
    
    def on_goto_position(self):
        pass
    
    def update_display(self):
        #self.log.debug('update_display')
        if self.initial_scan_setup_plotting:
            if self.settings['show_previous_scans']:
                self.img_item = pg.ImageItem()
                self.img_items.append(self.img_item)
                self.img_plot.addItem(self.img_item)
                self.hist_lut.setImageItem(self.img_item)
    
            self.img_item.setImage(self.display_image_map[0,:,:])
            x0, x1, y0, y1 = self.imshow_extent
            
            print ('debug check: ', x0, x1, y0, y1)
            
            self.log.debug('update_display set bounds {} {} {} {}'.format(x0, x1, y0, y1))
            self.img_item_rect = QtCore.QRectF(x0, y0, x1-x0, y1-y0)
            self.img_item.setRect(self.img_item_rect)
            self.log.debug('update_display set bounds {}'.format(self.img_item_rect))
            
            self.initial_scan_setup_plotting = False
        else:
            #if self.settings.scan_type.val in ['raster']
            kk, jj, ii = self.current_scan_index
            
            #print ('debug check: ', kk, jj, ii)
            
            if self.settings['collect_apd']:
                #self.disp_img = self.count_rate_map[kk,:,:]
                self.disp_img = self.count_rate_map[kk,:,:].T ##Note:changed by Kaiyuan, to make display right, 07/24/2018
            elif self.settings["collect_spectrum"]:
                self.disp_img = self.integrated_spectra_map[kk,:,:].T
                self.lightfield_readout.update_display()
            elif self.settings["collect_CCD_image"]:
                self.disp_img = self.integrated_spectra_map[kk,:,:].T
                self.lightfield_image_readout.update_display()
                
            self.img_item.setImage(self.disp_img, autoRange=False, autoLevels=True) 
            self.img_item.setRect(self.img_item_rect) # Important to set rectangle after setImage for non-square pixels
            self.update_LUT()
            

            
    def update_LUT(self):
        ''' override this function to control display LUT scaling'''
        self.hist_lut.imageChanged(autoLevel=False)
        # DISABLE below because of crashing
#         non_zero_index = np.nonzero(self.disp_img)
#         if len(non_zero_index[0]) > 0:
#             self.hist_lut.setLevels(*np.percentile(self.disp_img[non_zero_index],(1,99)))
               
    def clear_previous_scans(self):
        #current_img = img_items.pop()
        for img_item in self.img_items[:-1]:
            print('removing', img_item)
            self.img_plot.removeItem(img_item)  
            img_item.deleteLater()
    
        self.img_items = [self.img_item,]
    
    def mouseMoved(self,evt):
        mousePoint = self.img_plot.vb.mapSceneToView(evt)
        #print mousePoint
        
        #self.pos_label_text = "H {:+02.2f} um [{}], V {:+02.2f} um [{}]: {:1.2e} Hz ".format(
        #                mousePoint.x(), ii, mousePoint.y(), jj,
        #                self.count_rate_map[jj,ii] 
        #                )


        self.pos_label.setText(
            "H {:+02.2f} um [{}], V {:+02.2f} um [{}]: {:1.2e} Hz".format(
                        mousePoint.x(), 0, mousePoint.y(), 0, 0))

    def scan_specific_setup(self):
        "subclass this function to setup additional logged quantities and gui connections"
        self.settings.pixel_time.change_readonly(False)
        self.collect_apd      = self.add_logged_quantity("collect_apd",      dtype=bool, initial=False)
        self.collect_spectrum = self.add_logged_quantity("collect_spectrum", dtype=bool, initial=False)
        self.collect_lifetime = self.add_logged_quantity("collect_lifetime", dtype=bool, initial=False)
        self.collect_CCD_image = self.add_logged_quantity('collect_CCD_image', dtype=bool, initial=False)
        
        self.collect_apd.connect_to_widget(self.ui.collect_apd_checkBox)
        self.collect_spectrum.connect_to_widget(self.ui.collect_spectrum_checkBox)
        self.collect_lifetime.connect_to_widget(self.ui.collect_hydraharp_checkBox)
        self.collect_CCD_image.connect_to_widget(self.ui.collect_CCD_image_checkBox)
        
        #pass
        #self.stage = self.app.hardware.dummy_xy_stage
        
        #self.app.hardware_components['dummy_xy_stage'].x_position.connect_to_widget(self.ui.x_doubleSpinBox)
        #self.app.hardware_components['dummy_xy_stage'].y_position.connect_to_widget(self.ui.y_doubleSpinBox)
        
        #self.app.hardware_components['apd_counter'].int_time.connect_to_widget(self.ui.int_time_doubleSpinBox)
       
       
       
        # logged quantities
        # connect events
        
    

    def initialize_controller(self):
#        self.controller = self.app.hardware['xbox_controller']
#         
#         if hasattr(self, 'controller'):
#             self.pt_roi.sigRegionChangeFinished.connect(self.on_update_pt_roi)
        pass
    
    def update_point_roi_xbox(self):
        """Not yet implemented."""
        dx = self.controller.settings['Axis_4']
        dy = self.controller.settings['Axis_3']
        x, y = self.pt_roi.pos()
        if abs(dx) < 0.25:
            dx = 0
        if abs(dy) < 0.25:
            dy = 0
        if dx != 0 or dy != 0:
            c = self.controller.settings.sensitivity.val
            self.pt_roi.setPos(x+(c*dx), y+(c*dy))
        
    @property
    def h_array(self):
        return self.h_range.array

    @property
    def v_array(self):
        return self.v_range.array

    def compute_times(self):
        #self.settings['pixel_time'] = 1.0/self.scanDAQ.settings['dac_rate']
        S = self.settings
        S['line_time']  = S['pixel_time'] * S['Nh']
        S['frame_time'] = S['pixel_time'] * self.Npixels
        S['total_time'] = S['frame_time'] * S['n_frames']
    
    #### Scan Generators
    def gen_raster_scan(self, gen_arrays=True):
        self.Npixels = self.Nh.val*self.Nv.val
        self.scan_shape = (1, self.Nv.val, self.Nh.val)
        
        if gen_arrays:
            #print "t0", time.time() - t0
            self.create_empty_scan_arrays()            
            #print "t1", time.time() - t0
            
#             t0 = time.time()
#             pixel_i = 0
#             for jj in range(self.Nv.val):
#                 #print "tjj", jj, time.time() - t0
#                 self.scan_slow_move[pixel_i] = True
#                 for ii in range(self.Nh.val):
#                     self.scan_v_positions[pixel_i] = self.v_array[jj]
#                     self.scan_h_positions[pixel_i] = self.h_array[ii]
#                     self.scan_index_array[pixel_i,:] = [0, jj, ii] 
#                     pixel_i += 1
#             print "for loop raster gen", time.time() - t0
             
            t0 = time.time()
             
            H, V = np.meshgrid(self.h_array, self.v_array)
            self.scan_h_positions[:] = H.flat
            self.scan_v_positions[:] = V.flat
            
            II,JJ = np.meshgrid(np.arange(self.Nh.val), np.arange(self.Nv.val))
            self.scan_index_array[:,1] = JJ.flat
            self.scan_index_array[:,2] = II.flat
            #self.scan_v_positions
            print("array flatten raster gen", time.time() - t0)
            
        
    def gen_serpentine_scan(self, gen_arrays=True):
        self.Npixels = self.Nh.val*self.Nv.val
        self.scan_shape = (1, self.Nv.val, self.Nh.val)

        if gen_arrays:
            self.create_empty_scan_arrays()
            pixel_i = 0
            for jj in range(self.Nv.val):
                #self.scan_slow_move[pixel_i] = True
                
                if jj % 2: #odd lines
                    h_line_indicies = range(self.Nh.val)[::-1]
                else:       #even lines -- traverse in opposite direction
                    h_line_indicies = range(self.Nh.val)            
        
                for ii in h_line_indicies:            
                    self.scan_v_positions[pixel_i] = self.v_array[jj]
                    self.scan_h_positions[pixel_i] = self.h_array[ii]
                    self.scan_index_array[pixel_i,:] = [0, jj, ii]                 
                    pixel_i += 1
                
    def gen_trace_retrace_scan(self, gen_arrays=True):
        self.Npixels = 2*self.Nh.val*self.Nv.val
        self.scan_shape = (2, self.Nv.val, self.Nh.val)

        if gen_arrays:
            self.create_empty_scan_arrays()
            pixel_i = 0
            for jj in range(self.Nv.val):
                #self.scan_slow_move[pixel_i] = True     
                for kk, step in [(0,1),(1,-1)]: # trace kk =0, retrace kk=1
                    h_line_indicies = range(self.Nh.val)[::step]
                    for ii in h_line_indicies:            
                        self.scan_v_positions[pixel_i] = self.v_array[jj]
                        self.scan_h_positions[pixel_i] = self.h_array[ii]
                        self.scan_index_array[pixel_i,:] = [kk, jj, ii]                 
                        pixel_i += 1
    
    def gen_ortho_raster_scan(self, gen_arrays=True):
        self.Npixels = 2*self.Nh.val*self.Nv.val
        self.scan_shape = (2, self.Nv.val, self.Nh.val)

        if gen_arrays:
            self.create_empty_scan_arrays()
            pixel_i = 0
            for jj in range(self.Nv.val):
                #self.scan_slow_move[pixel_i] = True
                for ii in range(self.Nh.val):
                    self.scan_v_positions[pixel_i] = self.v_array[jj]
                    self.scan_h_positions[pixel_i] = self.h_array[ii]
                    self.scan_index_array[pixel_i,:] = [0, jj, ii] 
                    pixel_i += 1
            for ii in range(self.Nh.val):
                #self.scan_slow_move[pixel_i] = True
                for jj in range(self.Nv.val):
                    self.scan_v_positions[pixel_i] = self.v_array[jj]
                    self.scan_h_positions[pixel_i] = self.h_array[ii]
                    self.scan_index_array[pixel_i,:] = [1, jj, ii] 
                    pixel_i += 1
    
    def gen_ortho_trace_retrace_scan(self, gen_arrays=True):
        print("gen_ortho_trace_retrace_scan")
        self.Npixels = 4*len(self.h_array)*len(self.v_array) 
        self.scan_shape = (4, self.Nv.val, self.Nh.val)                        
        
        if gen_arrays:
            self.create_empty_scan_arrays()
            pixel_i = 0
            for jj in range(self.Nv.val):
                #self.scan_slow_move[pixel_i] = True     
                for kk, step in [(0,1),(1,-1)]: # trace kk =0, retrace kk=1
                    h_line_indicies = range(self.Nh.val)[::step]
                    for ii in h_line_indicies:            
                        self.scan_v_positions[pixel_i] = self.v_array[jj]
                        self.scan_h_positions[pixel_i] = self.h_array[ii]
                        self.scan_index_array[pixel_i,:] = [kk, jj, ii]                 
                        pixel_i += 1
            for ii in range(self.Nh.val):
                #self.scan_slow_move[pixel_i] = True     
                for kk, step in [(2,1),(3,-1)]: # trace kk =2, retrace kk=3
                    v_line_indicies = range(self.Nv.val)[::step]
                    for jj in v_line_indicies:            
                        self.scan_v_positions[pixel_i] = self.v_array[jj]
                        self.scan_h_positions[pixel_i] = self.h_array[ii]
                        self.scan_index_array[pixel_i,:] = [kk, jj, ii]                 
                        pixel_i += 1
                    

    def run(self):
        S = self.settings
        
        
        #Hardware
        # self.apd_counter_hc = self.app.hardware_components['apd_counter']
        # self.apd_count_rate = self.apd_counter_hc.apd_count_rate
        # self.stage = self.app.hardware_components['dummy_xy_stage']
        #self.stage = self.app.hardware.PI_xyz_stage
        # Data File
        # H5
        
        self.stage_x = self.app.hardware.side_beam_power_wheel
        self.stage_y = self.app.hardware.main_beam_power_wheel
        self.stage_x_dev = self.stage_x.power_wheel_dev
        self.stage_y_dev = self.stage_y.power_wheel_dev
        
        self.stage_x.settings.encoder_pos.updated_value.connect(self.update_arrow_pos)#, QtCore.Qt.UniqueConnection)
        self.stage_x.settings.encoder_pos.connect_to_widget(self.ui.x_doubleSpinBox)
        
        self.stage_y.settings.encoder_pos.updated_value.connect(self.update_arrow_pos)#, QtCore.Qt.UniqueConnection)
        self.stage_y.settings.encoder_pos.connect_to_widget(self.ui.y_doubleSpinBox)
        
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
            
                    
                    
        except Exception as err:
            self.log.error('Failed to Scan {}'.format(err))
            raise(err)
        finally:
            #H.update(self.scan_specific_savedict())
            H['pm_powers_map'] = np.array(self.pm_powers_map)
            H['pm_powers_after_map'] = np.array(self.pm_powers_after_map)
            #H['power_wheel_position'] = np.array(self.power_wheel_position)
            
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


    def move_position_start(self, h,v):
        #self.stage.y_position.update_value(x)
        #self.stage.y_position.update_value(y)
        
        S = self.settings
        
        coords = [None, None, None]
        coords[self.ax_map[S['h_axis']]] = h
        coords[self.ax_map[S['v_axis']]] = v
        
        #self.stage.move_pos_slow(x,y,None)
        h_current = self.stage_x.settings.encoder_pos.read_from_hardware()
        v_current = self.stage_y.settings.encoder_pos.read_from_hardware()
        
        if abs(h-h_current) >= 1:
            self.stage_x_dev.write_steps_and_wait(h-h_current)
            time.sleep(0.1)
        if abs(v-v_current) >= 1:
            self.stage_y_dev.write_steps_and_wait(v-v_current)
            time.sleep(2.0)
        #self.stage.move_pos_slow(*coords)
        #self.stage_x.settings.encoder_pos
    
    def move_position_slow(self, h,v):
        self.move_position_start(h, v)
        if self.settings["update_position"]:
            self.stage_x.settings.encoder_pos.read_from_hardware()
            self.stage_y.settings.encoder_pos.read_from_hardware()
            
    def collect_pixel(self, pixel_num, k, j, i):
        
        pm_powers_Si_val, pm_powers_Ge_val=self.collect_pm_power_data_Sync()
        self.pm_powers_map[0, k, j, i] = pm_powers_Si_val
        self.pm_powers_map[1, k, j, i] = pm_powers_Ge_val
        
        if self.settings['collect_apd']:      
            count_reading = self.apd_count_rate_lq.read_from_hardware()
            self.count_rate_map[k, j, i] = count_reading  # changed from [k, i, j] to [k, j, i] by Kaiyuan, 07/24/2018, to fix data recording and display problems.
            #self.count_rate_map_h5[k,j,i] = self.apd_count_rate_lq.value
            
            #print('Count rate: ', self.apd_count_rate_lq.value)
            
        if self.settings['collect_lifetime']:
            self.ph_hw = self.app.hardware['hydraharp']

        if self.settings['collect_spectrum']:
            self.lightfield_readout.ro_acquire_data()
            
            spec = np.array(self.lightfield_readout.img)
            self.spectra_map[k,j,i,:] = spec
            self.integrated_spectra_map[k,j,i] = spec.sum()
            self.wls = np.array(self.lightfield_readout.wls)
            
        if self.settings['collect_CCD_image']:
            self.lightfield_image_readout.ro_acquire_data()
            spec = np.array(self.lightfield_image_readout.img)
            CCD_image = np.array(self.lightfield_image_readout.acquired_data)
            self.spectra_map[k,j,i,:] = spec
            self.integrated_spectra_map[k,j,i] = spec.sum()
            self.wls = np.array(self.lightfield_image_readout.wls)
            self.image_map[k,j,i,:,:] = CCD_image
            print ('***********image total intensity: {}'.format(spec.sum())  )
            
        
        self.pm_powers_Si_after_val, self.pm_powers_Ge_after_val=self.collect_pm_power_data_Sync()
        self.pm_powers_after_map[0, k, j, i] = pm_powers_Si_val
        self.pm_powers_after_map[1, k, j, i] = pm_powers_Ge_val
        time.sleep(self.settings['pixel_time'])
    
    def collect_pm_power_data_Sync(self):
        PM_SAMPLE_NUMBER = 10

        # Sample the power at least one time from the power meter.
        samp_count = 0
        pm_power_Si = 0.0
        pm_power_Ge = 0.0
        for samp in range(0, PM_SAMPLE_NUMBER):
            # Try at least 10 times before ultimately failing
            if self.interrupt_measurement_called: break
            try_count = 0
            #print "samp", ii_sync, samp, try_count, samp_count, pm_power
            while not self.interrupt_measurement_called:
                try:
                    pm_power_Si = pm_power_Si + self.app.hardware['thorlabs_powermeter_Si'].power.read_from_hardware(send_signal=True)
                    pm_power_Ge = pm_power_Ge + self.app.hardware['thorlabs_powermeter_Ge'].power.read_from_hardware(send_signal=True)
                    samp_count = samp_count + 1
                    break 
                except Exception as err:
                    try_count = try_count + 1
                    if try_count > 9:
                        print("failed to collect power meter sample:", err)
                        break
                    time.sleep(0.010)
         
        if samp_count > 0:              
            pm_power_Si = pm_power_Si/samp_count
            pm_power_Ge = pm_power_Ge/samp_count
        else:
            print("  Failed to read power")
            pm_power_Ge = 10000.  
            pm_power_Si = 10000. 
        
        return pm_power_Si, pm_power_Ge
    
    def post_scan_cleanup(self):
        
        ###Move slider back to turn off illumination
        #if self.app.hardware.dual_position_slider.slider_pos.val == 'Open':
        print ('Now close shutter...')
        self.app.hardware.dual_position_slider.move_fwd()
        
        pass
    