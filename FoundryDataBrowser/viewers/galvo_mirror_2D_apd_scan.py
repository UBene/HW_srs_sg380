'''
Created on Apr 7, 2022

@author: Benedikt Ursprung
'''
from ScopeFoundry.data_browser import DataBrowserView
import numpy as np
import h5py
import pyqtgraph as pg


class GalvoMirror2DApdScan(DataBrowserView):

    name = 'apd_2d_map'
    
    def setup(self):
        
        self.ui = self.imview = pg.ImageView()
        self.imview.getView().invertY(False) # lower left origin
        
        #self.graph_layout = pg.GraphicsLayoutWidget()
        #self.graph_layout.addPlot()
        
    def on_change_data_filename(self, fname):
        
        try:            
            self.dat = h5py.File(fname, 'r')
            self.im_data = np.array(self.dat[f'measurement/{self.meas_name}/count_rate_map'][0,:,:].T) # grab first frame
            self.imview.setImage(self.im_data)
        except Exception as err:
            self.imview.setImage(np.zeros((10,10)))
            self.databrowser.ui.statusbar.showMessage("failed to load %s:\n%s" %(fname, err))
            raise(err)
        
    def is_file_supported(self, fname):
        self.supported_files = ['galvo_mirror_2D_apd_scan', 'pi_xyz_2d_apd_slow_scan', 'apd_2d_map']
        for meas_name in self.supported_files:
            if meas_name in fname:
                self.meas_name = meas_name
                return True
        return False