'''
Created on Feb 4, 2016

@author: Edward Barnard
'''

from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file,replace_widget_in_layout
import numpy as np
import pyqtgraph as pg
import time
from qtpy import QtCore
from ScopeFoundry import LQRange

class BaseParallelogramRasterScan(Measurement):
    
    name = "base_parallelogram_raster_2D_scan"
    
    def __init__(self, app, 
                 x_limits=(-1,1),        y_limits=(-1,1),         z_limits=(-1,1), 
                 x_unit='',              y_unit='',               z_unit='',
                 spinbox_decimals=6,     spinbox_step=0.001,
                 use_external_range_sync=False):        
        
        self.spinbox_decimals = spinbox_decimals
    
        self.spinbox_step = spinbox_step
        
        self.x_limits = x_limits
        self.y_limits = y_limits
        self.z_limits = z_limits
        
        self.x_unit = x_unit
        self.y_unit = y_unit
        self.z_unit = z_unit
        
        Measurement.__init__(self, app)
        
    def setup(self):
        self.ui_filename = sibling_path(__file__,"parallelogram_raster_scan_base.ui")
        self.ui = load_qt_ui_file(self.ui_filename)
        self.ui.show()
        
        self.ui.setWindowTitle(self.name)

        self.display_update_period = 0.010 #seconds

        #connect events        

        # local logged quantities
        
        S = self.settings
        lq_kwargs = dict(spinbox_decimals=self.spinbox_decimals,spinbox_step = self.spinbox_step)      


        #logged quantities e1_x, e1_y...         
        self.p0 = self.settings.New_Vector('p0', initial = [1,1,1], **lq_kwargs)
        self.e1 = self.settings.New_Vector('e1', initial = [1,0,0], **lq_kwargs)
        self.e2 = self.settings.New_Vector('e2', initial = [0,1,0], **lq_kwargs)
        
        #Ranges
        self.mag_1 = S.New_Range(name='mag_1', include_center_span=True, **lq_kwargs)
        self.mag_2 = S.New_Range(name='mag_2', include_center_span=True, **lq_kwargs)
        
        self.scan_type = self.settings.New('scan_type', dtype=str, initial='raster',
                                                  choices=('raster', ))
        
        self.Npixels = S['mag_1_num']*S['mag_2_num']
        

        
        self.continuous_scan = S.New("continuous_scan", dtype=bool, initial=False)
        S.New('save_h5', dtype=bool, initial=True, ro=False)
        
        S.New('show_previous_scans', dtype=bool, initial=True)
        
        
        S.New('n_frames', dtype=int, initial=1, vmin=1)
        
        S.New('pixel_time', dtype=float, ro=True, si=True, initial=1, unit='s')
        S.New('line_time' , dtype=float, ro=True, si=True, unit='s')
        S.New('frame_time', dtype=float, ro=True, si=True, unit='s')        
        S.New('total_time', dtype=float, ro=True, si=True, unit='s')
        

            
 
        #connect events
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)

        self.settings.p0_x.connect_to_widget(self.ui.p0_x_doubleSpinBox)
        self.settings.p0_y.connect_to_widget(self.ui.p0_y_doubleSpinBox)
        self.settings.p0_z.connect_to_widget(self.ui.p0_z_doubleSpinBox)

        self.settings.e1_x.connect_to_widget(self.ui.e1_x_doubleSpinBox)
        self.settings.e1_y.connect_to_widget(self.ui.e1_y_doubleSpinBox)
        self.settings.e1_z.connect_to_widget(self.ui.e1_z_doubleSpinBox)
        
        self.settings.e2_x.connect_to_widget(self.ui.e2_x_doubleSpinBox)
        self.settings.e2_y.connect_to_widget(self.ui.e2_y_doubleSpinBox)
        self.settings.e2_z.connect_to_widget(self.ui.e2_z_doubleSpinBox)                
        
        self.settings.mag_1_min.connect_to_widget(self.ui.mag_1_min_doubleSpinBox)
        self.settings.mag_1_max.connect_to_widget(self.ui.mag_1_max_doubleSpinBox)
        self.settings.mag_1_num.connect_to_widget(self.ui.mag_1_num_doubleSpinBox)
        self.settings.mag_1_step.connect_to_widget(self.ui.mag_1_step_doubleSpinBox)
        
        self.settings.mag_2_min.connect_to_widget(self.ui.mag_2_min_doubleSpinBox)
        self.settings.mag_2_max.connect_to_widget(self.ui.mag_2_max_doubleSpinBox)
        self.settings.mag_2_num.connect_to_widget(self.ui.mag_2_num_doubleSpinBox)
        self.settings.mag_2_step.connect_to_widget(self.ui.mag_2_step_doubleSpinBox)
        
        self.progress.connect_to_widget(self.ui.progress_doubleSpinBox)
        
        self.settings.continuous_scan.connect_to_widget(
            self.ui.continuous_scan_checkBox)
        self.settings.save_h5.connect_to_widget(
            self.ui.save_h5_checkBox)

        self.settings.show_previous_scans.connect_to_widget(
            self.ui.show_previous_scans_checkBox)


        # listeners
        self.p0.add_listener(self.on_update_params)
        self.e1.add_listener(self.on_update_params)
        self.e2.add_listener(self.on_update_params)
        
        for lq_name in ['mag_1_num', 'mag_2_num', 'pixel_time', 'n_frames']:
            S.get_lq(lq_name).add_listener(self.compute_times)            
        self.compute_times()
        
        for s in 'mag_1, mag_2'.split(', '):
            self.settings.ranges[s].add_listener(self.compute_scan_params)

            
        self.initial_scan_setup_plotting = False
        self.scan_specific_setup()

        
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
         
    def compute_scan_params(self):
        self.log.debug('compute_scan_params')
        # Don't recompute if a scan is running!
        if self.is_measuring():
            return # maybe raise error
        
        # project
        
        S = self.settings
        self.calc_projections()

        self.imshow_extent = [self.e_2_0 - 0.5*S['mag_2_step'],
                              self.e_2_0 + S['mag_2_span'] + 0.5*S['mag_2_step'],
                              self.e_1_0 - 0.5*S['mag_1_step'],
                              self.e_1_0 + S['mag_1_span'] + 0.5*S['mag_1_step']]
        
        print(self.imshow_extent)
        
        self.compute_times()
        
        # call appropriate scan generator to determine scan size, don't compute scan arrays yet
        getattr(self, "gen_{}_scan".format(self.settings.scan_type.val))(gen_arrays=True)

    
    def compute_scan_arrays(self):
        pass

    
    def create_empty_scan_arrays(self):
        self.scan_slow_move   = np.zeros(self.Npixels, dtype=bool)
        self.scan_index_array = np.zeros((self.Npixels, 3), dtype=int)
        self.scan_position_array   = np.zeros((self.Npixels, 3), dtype=float)

    def pre_run(self):
        # set all logged quantities read only
        for lqname in 'e1_x,e1_y,e1_z,e2_x,e2_y,e2_z,p0_x,p0_y,p0_z,mag_1_span,mag_2_span,mag_1_step,mag_2_step'.split(','):
            self.settings.as_dict()[lqname].change_readonly(True)
            
        self.compute_scan_params()

    
    def post_run(self):
            # set all logged quantities writable
            for lqname in 'e1_x,e1_y,e1_z,e2_x,e2_y,e2_z,p0_x,p0_y,p0_z,mag_1_span,mag_2_span,mag_1_step,mag_2_step'.split(','):
                self.settings.as_dict()[lqname].change_readonly(False)


    def clear_qt_attr(self, attr_name):
        if hasattr(self, attr_name):
            attr = getattr(self, attr_name)
            attr.deleteLater()
            del attr
            


    def scan_specific_setup(self):
        "subclass this function to setup additional logged quantities and gui connections"
        pass

        
    def compute_times(self):
        S = self.settings
        S['line_time']  = S['pixel_time'] * S['mag_1_num']
        S['frame_time'] = S['line_time']  * S['mag_2_num']
        S['total_time'] = S['frame_time'] * S['n_frames']
    
    
    #### Scan Generators
    def gen_raster_scan(self, gen_arrays=True):
        '''
        e2 is the fast axis
        '''
        
        S = self.settings
        self.Npixels = S['mag_1_num']*S['mag_2_num']
        self.scan_shape = (1, S['mag_1_num'], S['mag_2_num'])
        
        e1_x, e1_y, e1_z = norm_lq_vec_vals([self.settings.e1_x, self.settings.e1_y, self.settings.e1_z])
        e2_x, e2_y, e2_z = norm_lq_vec_vals([self.settings.e2_x, self.settings.e2_y, self.settings.e2_z])
        
        i_pixel = 0
        if gen_arrays:
            self.create_empty_scan_arrays()
            for n1 in range(S['mag_1_num']):
                for n2 in range(S['mag_2_num']):
                    if n2 == 0:
                        self.scan_slow_move[i_pixel] = True
                    self.scan_position_array[i_pixel,0] = S['p0_x'] + S['mag_1_step']*n1*e1_x + S['mag_2_step']*n2*e2_x
                    self.scan_position_array[i_pixel,1] = S['p0_y'] + S['mag_1_step']*n1*e1_y + S['mag_2_step']*n2*e2_y
                    self.scan_position_array[i_pixel,2] = S['p0_z'] + S['mag_1_step']*n1*e1_z + S['mag_2_step']*n2*e2_z
                    i_pixel += 1

            II,JJ = np.meshgrid(np.arange(S['mag_2_num']), np.arange(S['mag_1_num']))
            self.scan_index_array[:,1] = JJ.flat
            self.scan_index_array[:,2] = II.flat
                    
                    
    def setup_figure(self):            
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

        #axis arrow        
        self.e1_arrow_item = pg.ArrowItem(angle=90, tailLen=30, tailWidth=4)
        self.e1_arrow_item.setZValue(100)
        self.img_plot.addItem(self.e1_arrow_item)

        self.e2_arrow_item = pg.ArrowItem(pen=pg.mkPen('g'), brush=pg.mkBrush('g'), 
                                          angle=180, tailLen=30, tailWidth=4)
        self.e2_arrow_item.setZValue(101)
        self.img_plot.addItem(self.e2_arrow_item)

        self.p0_arrow_item = pg.ArrowItem(pen=pg.mkPen('y'), brush=pg.mkBrush('y'), 
                                          angle=45, tailLen=0, tailWidth=0)
        self.e2_arrow_item.setZValue(102)
        self.img_plot.addItem(self.p0_arrow_item)

        self.scan_roi = pg.ROI([0,0],[1,1], movable=True)
        self.scan_roi.addScaleHandle([1, 1], [0, 0])
        self.scan_roi.addScaleHandle([0, 0], [1, 1])
        self.scan_roi.sigRegionChangeFinished.connect(self.mouse_update_scan_roi)    
        
        
        self.img_plot.addItem(self.scan_roi)        
        for lqname in 'mag_1 mag_2'.split():
            self.settings.ranges[lqname].add_listener(self.update_scan_roi)
            
    
    def update_scan_roi(self):
        self.log.debug("update_scan_roi")
        self.compute_scan_params()
        x0, x1, y0, y1 = self.imshow_extent
        self.scan_roi.blockSignals(True)
        self.scan_roi.setPos( (x0, y0, 0))
        self.scan_roi.setSize( (x1-x0, y1-y0, 0))
        self.scan_roi.blockSignals(False)    
                    
                
    def calc_projections(self):
        '''
        some coordinates in the e1,e2 plane
        '''
        S = self.settings
        self.p0_1 = self.p0.project_to(self.e1)
        self.p0_2 = self.p0.project_to(self.e2)
        self.e_1_0 = self.p0_1 + S['mag_1_min']
        self.e_2_0 = self.p0_2 + S['mag_2_min']
        
        
    def calc_stage_position_projections(self, x,y,z):
        self.pos_1 = np.dot(self.e1.normed_values, np.array([x,y,z]))
        self.pos_2 = np.dot(self.e2.normed_values, np.array([x,y,z]))
    

    def on_update_params(self):
        self.calc_projections()
        self.p0_arrow_item.setPos(self.p0_2,self.p0_1)
        self.e1_arrow_item.setPos(self.e_2_0, self.e_1_0)
        self.e2_arrow_item.setPos(self.e_2_0, self.e_1_0)
        
    def mouse_update_scan_roi(self):
        x0,y0 = self.scan_roi.pos()
        w, h  = self.scan_roi.size()
        self.settings.mag_2_center.update_value(x0 + w/2)
        self.settings.mag_1_center.update_value(y0 + h/2)
        self.settings.mag_2_span.update_value(w-self.settings.mag_1_step.val)
        self.settings.mag_1_span.update_value(h-self.settings.mag_2_step.val)
        self.compute_scan_params()
        self.update_scan_roi()
        
        
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
            self.log.debug('update_display set bounds {} {} {} {}'.format(x0, x1, y0, y1))
            self.img_item_rect = QtCore.QRectF(x0, y0, x1-x0, y1-y0)
            self.img_item.setRect(self.img_item_rect)
            self.log.debug('update_display set bounds {}'.format(self.img_item_rect))
            
            self.initial_scan_setup_plotting = False
        else:
            #if self.settings.scan_type.val in ['raster']
            kk, jj, ii = self.current_scan_index
            self.disp_img = self.display_image_map[kk,:,:].T
            self.img_item.setImage(self.disp_img, autoRange=False, autoLevels=True)
            self.img_item.setRect(self.img_item_rect) # Important to set rectangle after setImage for non-square pixels
            self.update_LUT()
                    
    def update_LUT(self):
        ''' override this function to control display LUT scaling'''
        self.hist_lut.imageChanged(autoLevel=False)
    
def norm_lq_vec_vals(component_list = []):
    '''
    returns the components of the unit vector defined by 
    (lq_vec_x, lq_vec_y, lq_vec_z)
    '''
    vec = np.array( [lq.val for lq in component_list], dtype=float)
    mag = np.sqrt(np.dot(vec,vec))
    return vec/mag
