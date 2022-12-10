from ScopeFoundry import Measurement
import numpy as np
import pyqtgraph as pg
import time
from ScopeFoundry.helper_funcs import sibling_path, replace_widget_in_layout
# from nltk.app.nemo_app import initialFind
from ScopeFoundry import h5_io

class LightFieldImageReadout(Measurement):

    name = "lightfield_image_readout"

    #ui_filename = "ScopeFoundryMeasurement/apd_optimizer.ui"
    
    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "lightfield_readout_image.ui")
        super(LightFieldImageReadout, self).__init__(app) 
    
    def setup(self):        
        #self.display_update_period = 0.1 #seconds
        
        # logged quantities

        self.settings.New('continuous', dtype=bool, initial=False, ro=False)
        self.settings.New('num_row', dtype=int, ro=False)
        self.settings.New('save_h5', dtype=bool, initial=True)
        # create data array
        self.OPTIMIZE_HISTORY_LEN = 200

        self.optimize_history = np.zeros(self.OPTIMIZE_HISTORY_LEN, dtype=np.float)        
        self.optimize_ii = 0
        
        self.app.hardware_components['lightfield'].exposure_time.connect_bidir_to_widget(self.ui.int_time_doubleSpinBox)
        self.lightfield_hw = self.app.hardware.lightfield

        
        self.settings.continuous.connect_to_widget(self.ui.continuous_checkBox)
        self.settings.save_h5.connect_to_widget(self.ui.save_h5_checkBox)
        self.settings.num_row.connect_to_widget(self.ui.row_number_doubleSpinBox)

        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        
        self.wls = [1,2,3,4,5,6]
        self.img = [1,3,2,4,5,6]
        #self.acquired_data = np.ones( (2,2), dtype=int )

    
    def setup_figure(self):
        self.optimize_ii = 0

        # ui window
        if hasattr(self, 'graph_layout'):
            self.graph_layout.deleteLater() # see http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            del self.graph_layout

        
        
        self.graph_layout = pg.GraphicsLayoutWidget(border=(100,100,100))
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)
        

        self.spec_plot = self.graph_layout.addPlot(title="LightField Spectrum Readout")
        self.spec_plot_line = self.spec_plot.plot([1,3,2,4,3,5])
        self.spec_plot.enableAutoRange()
        
        self.graph_layout.nextRow()
        
        self.img_plot = self.graph_layout.addPlot(title="LightField Image Readout")
        self.img_item = pg.ImageItem()
        self.img_plot.addItem(self.img_item)
        
        self.hist_lut = pg.HistogramLUTItem()
        self.graph_layout.addItem(self.hist_lut)
        self.hist_lut.setImageItem(self.img_item)  
        
        self.graph_layout.nextRow()
        self.pos_label = pg.LabelItem(justify='right')
        self.pos_label.setText("=====")
        self.graph_layout.addItem(self.pos_label)
        
        self.img_plot.scene().sigMouseMoved.connect(self.mouseMoved)
        
            #self.infline = pg.InfiniteLine(movable=True, angle=90, label='x={value:0.2f}', 
            #               labelOpts={'position':0.8, 'color': (200,200,100), 'fill': (200,200,200,50), 'movable': True})         
            #self.spec_plot.addItem(self.infline)
                    
            #self.graph_layout.nextRow()


            #self.img_item.setImage(self.img, autoLevels=False)

        #self.graph_layout.addLabel('Long Vertical Label', angle=-90, rowspan=3)
        
        ## Add 3 plots into the first row (automatic position)
        #self.p1 = self.graph_layout.addPlot(title="LightField Readout")

        #self.optimize_plot_line = self.p1.plot([1,3,2,4,3,5])
    
    def mouseMoved(self,evt):
        mousePoint = self.img_plot.vb.mapSceneToView(evt)
        #print mousePoint
        
        #self.pos_label_text = "H {:+02.2f} um [{}], V {:+02.2f} um [{}]: {:1.2e} Hz ".format(
        #                mousePoint.x(), ii, mousePoint.y(), jj,
        #                self.count_rate_map[jj,ii] 
        #                )


        self.pos_label.setText(
            "(X, Y): ({}, {})".format(
                        int(mousePoint.x()), int(mousePoint.y())))
     
    def ro_acquire_data(self):

        lf = self.lightfield_hw.lightfield_dev

        wls_raw, acquired_data_raw, image_width, image_height = lf.get_acquired_data()
        
        self.image_height = image_height
        self.image_width = image_width
        
        ccd_width = lf.Nx

        acquired_data = []
        wls = []

        for i in np.arange(0,image_height*image_width):
            acquired_data.append(acquired_data_raw[i])
        for i in np.arange(0,ccd_width):
            wls.append(wls_raw[i])
        self.acquired_data = np.array(acquired_data)
        wls = np.array(wls)
        
        if lf.roi_type_int == 2:
            xbin = self.lightfield_hw.settings["x_binning"]
            print ('Binned full sensor')
        elif lf.roi_type_int == 4:
            xbin = self.lightfield_hw.settings["custom_roi_xbinning"]
            print ('Custom ROI sensor')
        else:
            xbin = 1
            print ('Full sensor reading or Single line reading')

        print('xbin: {}'.format(xbin))
        print('roi: {}'.format(lf.roi_type_int))
        
#        if xbin == 1:
#            if image_height == 1:
#                self.img = self.acquired_data
#                self.wls = wls
#            else:
#                self.acquired_data = self.acquired_data.reshape((image_height, image_width))
#                self.img = np.array(self.acquired_data[self.settings.num_row.value])
#                self.wls = wls
        
        if image_height == 1:
            self.img = self.acquired_data
        else:
            self.acquired_data = self.acquired_data.reshape((image_height, image_width))

            #self.img = np.array(self.acquired_data[int(image_height/2)-1])
            ##Should we actually use height-integrated cts for spectra output?
            #self.img = np.array(  np.sum(self.acquired_data[self.settings.num_row.value, :], axis=0)  )
            self.img = np.array(self.acquired_data[self.settings.num_row.value])
        
        if xbin == 1:
            self.wls = wls
        
        elif xbin > 1:
            print ('xbin updated')
            self.wls = np.zeros(image_width)
            for i in np.arange(0, xbin):
                #print ('readout diagnostic: {}, {}, {}'.format(xbin, self.wls.shape, wls.shape) )
                self.wls += wls[i::xbin]
            self.wls = self.wls/xbin
        
        
        #######self.img is actually 1D array of spectrum 
        #######self.acquired_data is 2D array of image    
        return self.wls, self.img, self.acquired_data 
    
        

   
             
    def run(self):
        self.display_update_period = 0.001 #seconds

        #self.apd_counter_hc = self.gui.hardware_components['apd_counter']
        #self.apd_count_rate = self.apd_counter_hc.apd_count_rate

        while not self.interrupt_measurement_called:
            #print("test")
            try:

                
                self.ro_acquire_data()

                if self.settings['save_h5']:
                    self.t0 = time.time()
                    self.h5_file = h5_io.h5_base_file(self.app, measurement=self )
                    self.h5_file.attrs['time_id'] = self.t0
                    H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
                    #create h5 data arrays
                    H['wls'] = self.wls
                    H['spectrum'] = self.img
                    H['image'] = self.acquired_data
                
                    self.h5_file.close()
            finally:
                if not self.settings['continuous']:
                    break
        


        
        #is this right place to put this?
        #self.measurement_state_changed.emit(False)
        if not self.interrupt_measurement_called:
            self.measurement_sucessfully_completed.emit()
        else:
            self.measurement_interrupted.emit()
            
        time.sleep(self.display_update_period) #to make sure display is refreshed after each run
    

    def update_display(self):        
        #ii = self.optimize_ii
        #print "display update", ii, self.optimize_history[ii]
        #print("Test, {}, {}".format(self.wls, self.img))
        # pyqtgraph
        #self.p1.plot(self.optimize_history)
       
        self.spec_plot_line.setData(self.wls, self.img)
        
        if hasattr(self, 'acquired_data'):
            self.img_item.setImage(self.acquired_data.T)

        self.hist_lut.imageChanged(autoLevel=True, autoRange=True)
            #self.wls_mean = self.wls.mean()
            #self.infline.setValue([self.wls_mean,0])

