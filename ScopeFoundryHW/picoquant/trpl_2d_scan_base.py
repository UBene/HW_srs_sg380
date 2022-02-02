'''
Created on 05/20/2019

Base measurement for TRPL scan with
-picoharp (not tested)
-hydraharp (tested with 2 input channels).

see example of use bellow bellow

@author: Edward Barnard, Benedikt Ursprung
'''
import numpy as np
import time
import pyqtgraph as pg
from ScopeFoundry.scanning import BaseRaster2DSlowScan

class TRPL2DScanBase(BaseRaster2DSlowScan):
    
    name = 'trpl_2d_scan'
        
    def __init__(self, app, shutter_open_lq_path=None):
        self.shutter_open_lq_path = shutter_open_lq_path
        if shutter_open_lq_path != None:
            self.shutter_open = app.lq_path(shutter_open_lq_path)
    
    def setup(self):        
        S = self.settings
        S.New('acq_mode', str, initial='fixed_Tacq', choices=('fixed_sig_cts','fixed_Tacq'))
        S.New('dark_counts', int, initial=0, unit = 'Hz')
        S.New('sig_cts', int, initial=50000, unit='cts')
        S.New('dark_histograms_accumulations', int, initial=0)
        S.New('counting_device', str, choices=('hydraharp','picoharp'), initial='hydraharp') 
        S.New('auto_HistogramBins', bool, initial=True)
        if not hasattr(self.settings, 'use_shutter'):
            S.New('use_shutter', bool, initial=False, ro=True)
        
        self.display_ready = False
        self.acquiring_dark_histogram = False        

        
    def setup_figure(self):
        # Details widgets
        details_layout = self.ui.details_groupBox.layout()
        
        meas_widget = self.settings.New_UI(include=['counting_device','auto_HistogramBins','acq_mode',])
        details_layout.addWidget(meas_widget) 
        
        self.sig_cts_widget = self.settings.New_UI(include=['sig_cts','dark_counts'])
        self.sig_cts_widget.hide()
        details_layout.addWidget(self.sig_cts_widget)
            
        if hasattr(self, 'shutter_open'):
            widget = self.settings.New_UI(include=['use_shutter','dark_histograms_accumulations'])
            details_layout.addWidget(widget)
            self.settings.use_shutter.change_readonly(False)   
        else:
            self.settings['use_shutter'] = False
            self.settings.use_shutter.change_readonly(True)   

        # Hardware widgets
        self.hw_widgets = {}
        try:
            ph_widget = self.app.hardware['picoharp'].settings.New_UI(
                include=['connected','Tacq','Binning'])        
            self.ui.device_details_GroupBox.layout().addWidget(ph_widget)
            self.hw_widgets.update({'picoharp':ph_widget})
        except:
            pass
        
        try:
            hh_widget = self.app.hardware['hydraharp'].settings.New_UI(
                include=['connected','Tacq','ChanEnable0','ChanEnable1',
                         'Binning','HistogramBins','SyncDivider'])
            self.ui.device_details_GroupBox.layout().addWidget(hh_widget)
            self.hw_widgets.update({'hydraharp':hh_widget})
            ph_widget.hide()
        except:
            pass

        self.settings.counting_device.change_choice_list(self.hw_widgets.keys())
        self.settings.counting_device.add_listener(self.on_change_counting_device)
        self.settings.acq_mode.add_listener(self.on_change_acq_mode)

        # Plots
        BaseRaster2DSlowScan.setup_figure(self)
        self.graph_layout.nextRow()
        self.lifetime_plot = self.graph_layout.addPlot(colspan=2)
        #self.lifetime_plot.setMinimumHeight(300)
        self.lifetime_plot.setLabel('left', 'counts')
        self.lifetime_plot.setLabel('bottom', 'time', units='s', unitPrefix=None)
        self.lifetime_plot.setLogMode(False, True)
        
    def pre_scan_setup(self):
        S = self.settings        
        self.hw = hw = self.app.hardware[S['counting_device']]
        self.hw.settings['connected'] = True
            
        if self.settings['auto_HistogramBins']:
            self.hw.update_HistogramBins()
                        
        if S['counting_device'] == 'picoharp':
            self.n_channels = 1            
            self.dev = dev = self.hw.picoharp
            HistogramBins = self.hw.settings['histogram_channels']
            self.hist_slice = np.s_[0:self.n_channels, 0:HistogramBins]
            time_trace_map_shape = self.scan_shape + (HistogramBins,)

        if S['counting_device'] == 'hydraharp':
            self.dev = dev = self.hw.dev
            self.n_channels = self.hw.enabled_channels
            self.hist_slice = self.hw.hist_slice
            print(self.hist_slice)
            time_trace_map_shape = self.scan_shape + self.hw.hist_shape

        
        self.hw_widgets[self.settings['counting_device']].setDisabled(True)


        
        self.integrated_count_map_h5 = self.h5_meas_group.create_dataset('integrated_count_map', 
                                                                   shape=self.scan_shape + (self.n_channels,),
                                                                   dtype=float, 
                                                                   compression='gzip')
        
        self.time_trace_map_h5 = self.h5_meas_group.create_dataset('time_trace_map',
                                                              shape=time_trace_map_shape,
                                                              dtype=float)
        
        self.elapsed_time_h5 = self.h5_meas_group.create_dataset('elaspsed_time',
                                                                   shape=self.scan_shape,
                                                                   dtype=float, 
                                                                   compression='gzip')
        
    
        # pyqt graph
        self.initial_scan_setup_plotting = True
        self.lifetime_plot_curves = []
        self.lifetime_plot.clear()
        for i in range(self.n_channels):
            self.lifetime_plot_curves.append(self.lifetime_plot.plot())
        self.infline = pg.InfiniteLine(movable=False, angle=90, label='Histogram Bins stored', 
                       labelOpts={'position':0.1, 'color':(200,200,100), 'fill':(200,200,200,50), 'movable':True})
        self.lifetime_plot.addItem(self.infline)    
        

        self.sleep_time = min((max(0.1*self.hw.settings['Tacq']*1e-3, 0.010), 0.100))        
        

        #Dark Histogram [Requires Shutter]
        self.acquiring_dark_histogram = False        
        if self.settings['use_shutter'] and S['dark_histograms_accumulations'] != 0:
                
                self.shutter_open.update_value(False)
                time.sleep(1)
                                
                self.dark_hist_data = self.aquire_histogram()[self.hist_slice]
                self.time_array = self.hw.time_array[self.hist_slice[-1]]

                self.acquiring_dark_histogram = True
                
                i = 0
                while i < S['dark_histograms_accumulations'] and not self.interrupt_measurement_called:
                    self.dark_hist_data += self.aquire_histogram()[self.hist_slice]
                    i += 1
                self.dark_hist_data = 1.0 * self.dark_hist_data / S['dark_histograms_accumulations']
                self.h5_meas_group.create_dataset('dark_histogram', data=self.dark_hist_data)
                S['dark_counts'] = self.dark_hist_data.sum()
                self.acquiring_dark_histogram = False


        if self.settings['use_shutter']:
            self.shutter_open.update_value(True)
            time.sleep(1)
            
    
    def collect_pixel(self, pixel_num, k, j, i):
        self.histogram_data = self.aquire_histogram()

        elapsed_time = self.hw.settings['ElapsedMeasTime']
        self.elapsed_time_h5[k,j,i] = elapsed_time
        
        hist_data = self.histogram_data[self.hist_slice]
        self.time_trace_map_h5[k,j,i,:] = hist_data
        self.integrated_count_map_h5[k,j,i,:] = hist_data.sum(axis=-1) * 1.0/elapsed_time
        self.display_image_map[k,j,i] = hist_data.sum() * 1.0/elapsed_time

        if pixel_num == 0:
            self.display_image_map[:,:,:] = hist_data.sum() * 1.0/elapsed_time - 1

            self.time_array = self.hw.time_array
            self.h5_meas_group['time_array'] = self.time_array[self.hist_slice[-1]]
            pos_x = self.time_array[self.hw.settings['HistogramBins']-1]*1e-12
            self.lifetime_plot.setRange(xRange=(0,1.01*pos_x))
            self.infline.setPos([pos_x,0])
            self.display_ready = True

        self.pixel_num = pixel_num
        
    def update_display(self):
        BaseRaster2DSlowScan.update_display(self)
        if self.acquiring_dark_histogram:
            self.lifetime_plot.setTitle('Acquiring dark histograms ...')
            for i in range(self.n_channels):
                self.lifetime_plot_curves[i].setData(self.time_array*1e-12, self.dark_hist_data[i,:])
        
        elif self.display_ready:                       
            n = self.settings['n_frames'] * self.Npixels
            
            self.lifetime_plot.setTitle('collecting pixel {} of {} total time: {} min'.format(self.pixel_num + 1, n, n*self.hw.settings['Tacq']/60))
            for i in range(self.n_channels):
                self.lifetime_plot_curves[i].setData(self.time_array*1e-12, self.histogram_data[i,:])

        else:
            self.lifetime_plot.setTitle('display_ready=False / scan done')
                    
            

    def aquire_histogram(self):
        dev = self.dev
        
        if self.settings['acq_mode'] == 'fixed_Tacq':
            self.hw.start_histogram()
            while not dev.check_done_scanning():
                if self.hw.settings['Tacq'] > 0.2:
                    self.histogram_data = self.hw.read_histogram_data()
                time.sleep(0.005) #self.sleep_time)  
            self.hw.stop_histogram()            
            
        if self.settings['acq_mode'] == 'fixed_sig_cts':
            t_start_pixel = time.time()
            self.hw.start_histogram()
            while not dev.check_done_scanning():
                dev.read_histogram_data()
                self.histogram_data = self.hw.read_histogram_data()
                t_measure = time.time()-t_start_pixel
                total_signal = self.histogram_data[self.hist_slice].sum() \
                                    -self.settings['dark_counts']*t_measure
                if total_signal >= self.settings['sig_cts']:
                    print(t_measure)
                    self.hw.stop_histogram()
                    break
    
        return np.array(self.hw.read_histogram_data())  


    def post_scan_cleanup(self):
        if self.settings['use_shutter']:
            self.shutter_open.update_value(True)
            
        self.hw_widgets[self.settings['counting_device']].setDisabled(False)
        self.display_ready = False

    def on_change_counting_device(self):
        for dev,widegt in self.hw_widgets.items():
            if dev == self.settings['counting_device']:
                widegt.show()
            else:
                widegt.hide()
        self.ui.device_details_GroupBox.setTitle(self.settings['counting_device'])
                
    def on_change_acq_mode(self):
        if self.settings['acq_mode'] == 'fixed_sig_cts':
            self.sig_cts_widget.show()  
        else:
            self.sig_cts_widget.hide() 
            
            
            
class DummyStageBase2DScan(BaseRaster2DSlowScan):
    
    name = 'dummy_stage_base_2D_scan'
        
    #def setup(self)
    #self.stage = self.hardware['dummy_stage']
        
#Example of usage: 
class DummyStageTRPL2DScan(DummyStageBase2DScan, TRPL2DScanBase):
    
    name = 'trpl_2d_scan'
        
    def __init__(self, app):
        DummyStageBase2DScan.__init__(self, app)
    
    def setup(self):
        DummyStageBase2DScan.setup(self)
        TRPL2DScanBase.setup(self)

    def pre_scan_setup(self):
        TRPL2DScanBase.pre_scan_setup(self)
    
    def collect_pixel(self, pixel_num, k, j, i):
        TRPL2DScanBase.collect_pixel(self, pixel_num, k, j, i)   

    def post_scan_cleanup(self):
        TRPL2DScanBase.post_scan_cleanup(self)
        
    def update_display(self):
        TRPL2DScanBase.update_display(self)