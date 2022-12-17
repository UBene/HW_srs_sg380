from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import numpy as np
import time
import pyqtgraph as pg
from ScopeFoundry import h5_io


class HydraHarpHistogramMeasure(Measurement):    
    name = "hydraharp_histogram"
    
    hardware_requirements = ['hydraharp']
    
    def setup(self):
        self.display_update_period = 0.1 #seconds

        S = self.settings
#         self.stored_histogram_channels = self.add_logged_quantity(
#                                       "stored_histogram_channels", 
#                                      dtype=int, vmin=1, vmax=2**16, initial=2**16)
#         self.stored_histogram_channels.connect_bidir_to_widget(
#                                            self.gui.ui.trpl_live_stored_channels_doubleSpinBox)
        
        S.New('save_h5', dtype=bool, initial=True)
        S.New('continuous', dtype=bool, initial=False)
        
        # hardware
        hh_hw = self.hydraharp_hw = self.app.hardware['hydraharp']

        
        # UI 
        self.ui_filename = sibling_path(__file__,"hydraharp_hist_measure.ui")
        self.ui = load_qt_ui_file(self.ui_filename)
        self.ui.setWindowTitle(self.name)
        
        
        #connect events
        S.progress.connect_bidir_to_widget(self.ui.progressBar)
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        
        S.continuous.connect_to_widget(self.ui.continuous_checkBox)
        
        hh_hw.settings.Tacq.connect_bidir_to_widget(self.ui.hydraharp_tacq_doubleSpinBox)
        #hh.settings.histogram_channels.connect_bidir_to_widget(self.ui.histogram_channels_doubleSpinBox)
        hh_hw.settings.count_rate0.connect_to_widget(self.ui.ch0_doubleSpinBox)
        hh_hw.settings.count_rate1.connect_to_widget(self.ui.ch1_doubleSpinBox)
        
        
        S.save_h5.connect_bidir_to_widget(self.ui.save_h5_checkBox)
        #self.gui.ui.hydraharp_acquire_one_pushButton.clicked.connect(self.start)
        #self.gui.ui.hydraharp_interrupt_pushButton.clicked.connect(self.interrupt)
        self.time_array = [1,2,3,4,5,6]
        self.hist_data0 = [1,3,2,4,5,6]
    
    def setup_figure(self):
#         self.fig = self.gui.add_figure("hydraharp_live", self.gui.ui.hydraharp_plot_widget)
#                     
#         self.ax = self.fig.add_subplot(111)
#         self.plotline, = self.ax.semilogy([0,20], [1,65535])
#         self.ax.set_ylim(1e-1,1e5)
#         self.ax.set_xlabel("Time (ns)")
#         self.ax.set_ylabel("Counts")
        
        self.graph_layout = pg.GraphicsLayoutWidget()    
        
        self.plot = self.graph_layout.addPlot()
        self.plotdata = self.plot.plot(pen='r')
        self.plot.setLogMode(False, True)
        
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)
        
                
    def run(self):
        hh_hw = self.hydraharp_hw
        hh = self.hydraharp = self.hydraharp_hw.hydraharp
        #: type: hh: hydraHarp300
        
        #FIXME
        #self.plotline.set_xdata(hh.time_array*1e-3)
        print('Acuisition time in ms: {}'.format(hh.Tacq)) #in ms
        print('HistLen {}'.format(hh.HistLen))
        print('Hit Resolution {}'.format(hh.Resolution))
        sleep_time = min((max(0.1*hh.Tacq*1e-3, 0.010), 0.100)) # check every 1/10 of Tacq with limits of 10ms and 100ms
        #print("sleep_time", sleep_time, np.max(0.1*hh.Tacq*1e-3, 0.010))
        hh_hw.settings.Tacq.read_from_hardware()
        t0 = time.time()
                
        while not self.interrupt_measurement_called:
            hh.start_histogram()
            self.time_array = hh.time_array.copy()
            while not hh.check_done_scanning():
                self.set_progress( 100*(time.time() - t0)/hh_hw.settings['Tacq'] )
                if self.interrupt_measurement_called:
                    break
                hh.read_histogram_data(clear_after=False)
                self.hist_data0 = hh.hist_data_channel[0].copy()
                #print('hist_data sum: {}'.format(np.sum(self.hist_data0)) )
                
                hh_hw.settings.count_rate0.read_from_hardware()
                hh_hw.settings.count_rate1.read_from_hardware()
                
                time.sleep(sleep_time)
    
            hh.stop_histogram()
            hh.read_histogram_data(clear_after=True)
            self.hist_data0 = hh.hist_data_channel[0].copy()
            print("hist_data0: ", self.hist_data0)
            #print('final hist_data sum: {}'.format(np.sum(self.hist_data0)) )
            ###Register current histogram

            time.sleep(self.display_update_period) ###Give it enough time to update display after measurement
        
            if not self.settings['continuous']:
                break

        #print "elasped_meas_time (final):", hh.read_elapsed_meas_time()
        
        
        
#         ###########Save .npz files
#         save_dict = {
#                      #'time_histogram': hh.histogram_data,
#                      'time_histogram': hh.hist_data_channel[0],
#                      'time_array': hh.time_array,
#                      #'elapsed_meas_time': hh.read_elapsed_meas_time()
#                     }                                
# 
#         for lqname,lq in self.app.settings.as_dict().items():
#             save_dict[lqname] = lq.val
#         
#         for hc in self.app.hardware.values():
#             for lqname,lq in hc.settings.as_dict().items():
#                 save_dict[hc.name + "_" + lqname] = lq.val
#         
#         for lqname,lq in self.settings.as_dict().items():
#             save_dict[self.name +"_"+ lqname] = lq.val
# 
# 
#         self.fname = "%i_hydraharp.npz" % time.time()
#         np.savez_compressed(self.fname, **save_dict)
#         print("Hydraharp npz data Saved", self.fname)
        
        
        #############Save H5 files
        try:
            self.h5_file = h5_io.h5_base_file(self.app, measurement=self )
            self.t0 = time.time()
            self.h5_file.attrs['time_id'] = self.t0
            H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
            
            #create h5 data arrays
            H['time_histogram0'] = self.hist_data0
            #H['time_histogram1'] = hh.hist_data_channel[1]
            H['time_array'] = self.time_array
        finally:
            self.h5_file.close()    
            
        print("Hydraharp H5 data Saved")
    
    def read_lifetime(self, Tacq_input):
        
        hh_hw = self.hydraharp_hw
        hh = self.hydraharp = hh_hw.hydraharp
        #: type: hh: hydraHarp300
        
        hh.set_Tacq(Tacq_input)
        self.interrupt_measurement_called = False
        #FIXME
        #self.plotline.set_xdata(hh.time_array*1e-3)
        print('Acuisition time in ms: {}'.format(hh.Tacq)) #in ms
        print('HistLen {}'.format(hh.HistLen))
        print('Hit Resolution {}'.format(hh.Resolution))
        sleep_time = min((max(0.1*hh.Tacq*1e-3, 0.010), 0.100)) # check every 1/10 of Tacq with limits of 10ms and 100ms
        #print("sleep_time", sleep_time, np.max(0.1*hh.Tacq*1e-3, 0.010))
        
        t0 = time.time()

        hh.start_histogram()
        self.time_array = hh.time_array.copy()
        print(self.time_array)
        while not hh.check_done_scanning():
            if self.interrupt_measurement_called:
                    break
            self.set_progress( 100*(time.time() - t0)/hh_hw.settings['Tacq'] )
            hh.read_histogram_data(clear_after=False)
            self.hist_data0 = hh.hist_data_channel[0].copy()
            #print('hist_data sum: {}'.format(np.sum(self.hist_data0)) )
            
            hh_hw.settings.count_rate0.read_from_hardware()
            hh_hw.settings.count_rate1.read_from_hardware()
            
            time.sleep(sleep_time)
            

    
    
    
        hh.stop_histogram()
        hh.read_histogram_data(clear_after=True)
        self.hist_data0 = hh.hist_data_channel[0].copy()
        print("hist_data0: ", self.hist_data0)
        #print('final hist_data sum: {}'.format(np.sum(self.hist_data0)) )
        ###Register current histogram
        

        self.set_progress( 0.0)
        time.sleep(self.display_update_period) ###Give it enough time to update display after measurement
        

    
                          
    def update_display(self):
        #hh = self.hydraharp
        #self.plotdata.setData(hh.time_array*1e-3, hh.histogram_data+1)
        #self.plotdata.setData(hh.time_array*1e-3, hh.hist_data_channel[0]+1)
        self.plotdata.setData(self.time_array, self.hist_data0+1)
        #if hasattr(self, 'hist_data0'):
            #print('updating display')
            #self.plotdata.setData(self.time_array, self.hist_data0+1)
            #self.plotdata.setData(hh.time_array*1e-3, hh.hist_data_channel[0]+1)
        
        #self.fig.canvas.draw()
