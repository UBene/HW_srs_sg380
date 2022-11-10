from ScopeFoundry import Measurement
import numpy as np
import pyqtgraph as pg
import time
from ScopeFoundry.helper_funcs import sibling_path, replace_widget_in_layout
# from nltk.app.nemo_app import initialFind
from ScopeFoundry import h5_io

class LightFieldReadout_IR(Measurement):

    name = "lightfield_readout_IR"

    #ui_filename = "ScopeFoundryMeasurement/apd_optimizer.ui"
    
    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "lightfield_readout_IR.ui")
        super(LightFieldReadout_IR, self).__init__(app)
    
    def setup(self):        
        #self.display_update_period = 0.1 #seconds
        
        # logged quantities

        self.settings.New('continuous', dtype=bool, initial=False, ro=False)
        self.settings.New('save_h5', dtype=bool, initial=True)
        # self.settings.New('save_image', dtype=bool, initial=False)
        self.settings.New('MultiSpecAvg', dtype=bool, initial=False)
        self.MultiSpecAvg_Number = self.settings.New('MultiSpecAvg_Number', dtype=int, initial=5)
        
        # create data array
        self.OPTIMIZE_HISTORY_LEN = 200

        self.optimize_history = np.zeros(self.OPTIMIZE_HISTORY_LEN, dtype=np.float)        
        self.optimize_ii = 0
        
        self.app.hardware_components['lightfield_IR'].exposure_time.connect_bidir_to_widget(self.ui.int_time_doubleSpinBox)
        self.lightfield_hw_IR = self.app.hardware.lightfield_IR

        
        self.settings.continuous.connect_to_widget(self.ui.continuous_checkBox)
        self.settings.save_h5.connect_to_widget(self.ui.save_h5_checkBox)
        # self.settings.save_image.connect_to_widget(self.ui.save_image_checkBox)
        self.settings.MultiSpecAvg.connect_bidir_to_widget(self.ui.MultiSpecAvg_checkBox)
        self.settings.MultiSpecAvg_Number.connect_bidir_to_widget(self.ui.MultiSpecAvg_Number_doubleSpinBox)

        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        
        self.wls = [1,2,3,4,5,6]
        self.img = [1,3,2,4,5,6]

    
    def setup_figure(self):
        self.optimize_ii = 0

        # ui window
        if hasattr(self, 'graph_layout'):
            self.graph_layout.deleteLater() # see http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            del self.graph_layout

        
        self.graph_layout = pg.GraphicsLayoutWidget(border=(100,100,100))
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)
        

        self.spec_plot = self.graph_layout.addPlot(title="LightField Readout IR")
        self.spec_plot_line = self.spec_plot.plot([1,3,2,4,3,5])
        self.spec_plot.enableAutoRange()
            
            #self.infline = pg.InfiniteLine(movable=True, angle=90, label='x={value:0.2f}', 
            #               labelOpts={'position':0.8, 'color': (200,200,100), 'fill': (200,200,200,50), 'movable': True})         
            #self.spec_plot.addItem(self.infline)
                    
            #self.graph_layout.nextRow()


            #self.img_item.setImage(self.img, autoLevels=False)

        #self.graph_layout.addLabel('Long Vertical Label', angle=-90, rowspan=3)
        
        ## Add 3 plots into the first row (automatic position)
        #self.p1 = self.graph_layout.addPlot(title="LightField Readout")

        #self.optimize_plot_line = self.p1.plot([1,3,2,4,3,5])
    
    def ro_acquire_data(self):

        lf = self.lightfield_hw_IR.lightfield_dev
        
        #############################################
        ######## when number of files in this folder gets large, reading data from hard disk becomes tooooo slow!!!!
        ######## To do: need to find a better way to read in data
        ######## To do: or delete the spe files once they're loaded into h5!
        t0 = time.time()
        
        wls_raw, acquired_data_raw, image_width, image_height = lf.get_acquired_data()
        
        print('lf.get_acquired_data run time: {}'.format(time.time()-t0))
        
        # self.image_height = image_height
        # self.image_width = image_width

        self.image_height = 1
        self.image_width = 1024

        acquired_data = []
        wls = []
        ccd_width = lf.Nx
        
        #######################################################################
        ### To do: try to restructure these loops to reduce readout time if possible
        ### Actually this for loop takes about 3ms, not the bottle neck, but may wanna optimize for fast scanning applications
        
        for i in range(0,image_height*image_width):
            acquired_data.append(acquired_data_raw[i])
        for i in range(0,ccd_width):
            wls.append(wls_raw[i])
        self.acquired_data = np.array(acquired_data)
        wls = np.array(wls)
        

        # #print(lf.roi_type_int)
        # if lf.roi_type_int == 2:
        #     xbin = self.lightfield_hw_IR.settings["x_binning"] #Full sensor binned
        #     #print ('Binned full sensor')
        # elif lf.roi_type_int == 4:
        #     xbin = self.lightfield_hw_IR.settings["custom_roi_xbinning"] #custom ROI binned
        #     #print ('Custom ROI sensor')
        # else:
        #     xbin = 1
            #print ('Full sensor reading or Single line reading')
        xbin = 1
        #print ('roi_type_int={}, xbin={}'.format(lf.roi_type_int, xbin))
        

        # IR camera is only 1024(width) * 1(height)
        if image_height == 1:
            self.img = self.acquired_data
        # else:
        #     self.acquired_data = self.acquired_data.reshape((image_height, image_width))
        #
        #     #self.img = np.array(self.acquired_data[int(image_height/2)-1])
        #     ##Should we actually use height-integrated cts for spectra output?
        #     self.img = np.array(  np.sum(self.acquired_data[:, :], axis=0)  )
            #print ('changed to sum')
        
        #print ('size of self.img: {}'.format(self.image.shape[0]))


        
        
        if xbin == 1:
            self.wls = np.zeros(image_width)
            self.wls = wls

        elif xbin > 1:
            self.wls = np.zeros(image_width)
            for i in np.arange(0, xbin):
                #print ('readout diagnostic: {}, {}, {}'.format(xbin, self.wls.shape, wls.shape) )
                self.wls += wls[i::xbin]
            self.wls = self.wls/xbin
            
        return self.wls, self.img
        

   
             
    def run(self):
        
        t0 = time.time()
        
        self.display_update_period = 0.001 #seconds

        #self.apd_counter_hc = self.gui.hardware_components['apd_counter']
        #self.apd_count_rate = self.apd_counter_hc.apd_count_rate

        while not self.interrupt_measurement_called:
            #print("test")
            try:
                
                if self.settings['MultiSpecAvg'] == False:
                    
                    self.ro_acquire_data()
                    #print('self.ro_acquire_data run time {}'.format(time.time()-t0))
                    
                    #####################################
                    ########Note: the h5 saving process takes about 30ms per spectra
                    ######## Does this time also apply to hyperspectral scan?
                    ######## Does APD readout also have the same problem?
                
                else:
                    #self.all_img_data_MultiSpec_raw = []
                    time_array = []
                    self.wls_MultiSpec, self.img_MultiSpec = self.ro_acquire_data()
                    self.all_img_data_MultiSpec = self.img_MultiSpec.copy()
                    time_start = self.t0 = time.time()
                    time_array.append(0)
                    #for iMulti in np.arange(0, self.MultiSpecAvg_Number.val-1):
                    for iMulti in np.arange(0, self.settings.MultiSpecAvg_Number.val-1):
                        self.wls, self.img = self.ro_acquire_data()
                        self.img_MultiSpec += self.img
                        self.all_img_data_MultiSpec = np.vstack( (self.all_img_data_MultiSpec, self.img) )
                        time_array.append(time.time() - time_start)
                        print (time.time() - time_start)
                        
                        #self.all_img_data_MultiSpec_raw.append(self.img)
                        print('***********all_img_data array shape: {}'.format(self.all_img_data_MultiSpec.shape))
                
                
                if self.settings['save_h5']:
                    self.t0 = time.time()
                    self.h5_file = h5_io.h5_base_file(self.app, measurement=self )
                    self.h5_file.attrs['time_id'] = self.t0
                    H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
                    #create h5 data arrays
                    H['wls'] = self.wls
                    H['spectrum'] = self.img
                    
                    # if self.settings['save_image']:
                    #     H['image'] = self.acquired_data
                        
                    if self.settings['MultiSpecAvg']:
                        H['img_MultiSpec'] = self.img_MultiSpec
                        H['wls_MultiSpec'] = self.wls_MultiSpec
                        H['all_img_data_MultiSpec'] = self.all_img_data_MultiSpec
                        H["time"] = time_array
                        #H['all_img_data_MultiSpec_raw'] = self.all_img_data_MultiSpec_raw
                
                    self.h5_file.close()
                    
            except Exception as err:
                self.log.error('Failed to read lightfield {}'.format(err))
                raise(err)
            
            finally:
                if not self.settings['continuous']:
                    break
        


        
        #is this right place to put this?
        #self.measurement_state_changed.emit(False)
        print('CCD acquisition run time {}'.format(time.time()-t0))
        
        if not self.interrupt_measurement_called:
            self.measurement_sucessfully_completed.emit()
        else:
            self.measurement_interrupted.emit()
    

    def update_display(self):        
        #ii = self.optimize_ii
        #print "display update", ii, self.optimize_history[ii]
        #print("Test, {}, {}".format(self.wls, self.img))
        # pyqtgraph
        #self.p1.plot(self.optimize_history)
        if self.settings['MultiSpecAvg'] == False: 
            self.spec_plot_line.setData(self.wls, self.img)
            #self.wls_mean = self.wls.mean()
            #self.infline.setValue([self.wls_mean,0])
        else:
            if hasattr(self, 'wls_MultiSpec'):
                self.spec_plot_line.setData(self.wls_MultiSpec, self.img_MultiSpec)

