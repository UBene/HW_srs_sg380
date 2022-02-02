from ScopeFoundry.data_browser import DataBrowser, DataBrowserView
import numpy as np
import h5py
import pyqtgraph as pg
from qtpy import QtWidgets
from xlwt.BIFFRecords import DSFRecord

class AugerSyncRasterScanH5View(DataBrowserView):

    name = 'auger_sync_raster_scan_h5'
    
    def setup(self):
        
        self.settings.New('frame', dtype=int, initial=0)
        self.settings.New('sub_frame', dtype=int, initial=0)
        chan_choices = ['adc0', 'adc1', 'ctr0', 'ctr1'] + ['auger{}'.format(i) for i in range(10)] + ['sum_auger']
        self.settings.New('channel', dtype=str, initial='adc1', choices=tuple(chan_choices))
        self.settings.New('auto_level', dtype=bool, initial=True)

        self.ui = QtWidgets.QWidget()
        self.ui.setLayout(QtWidgets.QVBoxLayout())
        self.ui.layout().addWidget(self.settings.New_UI(), stretch=0)
        self.info_label = QtWidgets.QLabel()
        self.ui.layout().addWidget(self.info_label, stretch=0)
        
        self.imview = pg.ImageView()
        self.ui.layout().addWidget(self.imview, stretch=1)
        
        self.spec_plot = pg.PlotWidget()
        self.spec_plotline = self.spec_plot.plot()
        self.ui.layout().addWidget(self.spec_plot, stretch=0.5)
        
        self.settings.frame.add_listener(self.update_display)
        self.settings.sub_frame.add_listener(self.update_display)
        self.settings.channel.add_listener(self.update_display)
        self.settings.auto_level.add_listener(self.update_display)

    def is_file_supported(self, fname):
        return "auger_sync_raster_scan.h5" in fname

    
    def on_change_data_filename(self, fname):
        
        try:
            self.databrowser.ui.statusbar.showMessage("Loading %s, please wait" %(fname))

            self.dat = h5py.File(fname, 'r')
            self.H = self.dat['measurement/auger_sync_raster_scan/']
            h = self.h_settings = self.H['settings'].attrs
            #self.adc_map = np.array(self.H['adc_map'])
            self.adc_map_h5 = self.H['adc_map']

            #self.ctr_map = np.array(self.H['ctr_map'])
            #self.auger_map = np.array(self.H['auger_chan_map'])
            self.auger_map_h5 = self.H['auger_chan_map']

            #self.auger_sum_map = self.auger_map[:,:,:,:,0:7].sum(axis=4)
            
            try:
                self.ke_interp = np.array(self.H['ke_interp'])
                self.global_spectrum = np.array(self.H['global_spectrum'])
                self.global_spec_loaded = True
            except:
                self.global_spec_loaded = False
                
            scan_shape = self.adc_map_h5.shape[:-1]
            
            self.settings.frame.change_min_max(0, scan_shape[0]-1)
            self.settings.sub_frame.change_min_max(0, scan_shape[1]-1)

            self.databrowser.ui.statusbar.showMessage("Loaded %s" %(fname))

            self.update_display()
        except Exception as err:
            self.imview.setImage(np.zeros((10,10)))
            self.databrowser.ui.statusbar.showMessage("Failed to load %s: %s" %(fname, err))
            raise(err)

    def update_display(self):
        
        frame = self.settings['frame']
        sub_frame = self.settings['sub_frame']
        chan = self.settings['channel']

#         chan_data = dict(
#             adc0 = self.adc_map[frame, sub_frame, :,:,0],
#             adc1 = self.adc_map[frame, sub_frame, :,:,1],
#             #ctr0 = self.ctr_map[frame, sub_frame, :,:,0],
#             #ctr1 = self.ctr_map[frame, sub_frame, :,:,1],
#             #sum_auger = self.auger_sum_map[frame,sub_frame,:,:]
#             )
#         for i in range(10):
#             #chan_data['auger{}'.format(i)] = self.auger_map[frame,sub_frame,:,:,i]
#             chan_data['auger{}'.format(i)] = self.auger_map_h5[frame,sub_frame,:,:,i]
#         
        
        if chan == 'adc0': chan_data = self.adc_map_h5[frame, sub_frame, :,:,0]
        if chan == 'adc1': chan_data = self.adc_map_h5[frame, sub_frame, :,:,1]
        for i in range(10):
            if chan == 'auger{}'.format(i):
                chan_data = self.auger_map_h5[frame,sub_frame,:,:,i]
        
        
        self.imview.setImage(chan_data,
                             autoLevels=self.settings['auto_level'],axes=dict(x=1,y=0))

        if self.global_spec_loaded:
            self.spec_plotline.setData(self.ke_interp, self.global_spectrum)
        else:
            self.spec_plotline.setData([0])
                                       
                                       
                                       