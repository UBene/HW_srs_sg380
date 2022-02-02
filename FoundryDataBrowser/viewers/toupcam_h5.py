'''
Created on Aug 18, 2021

@author: Benedikt Ursprung
'''
from ScopeFoundry.data_browser import DataBrowserView
import pyqtgraph as pg
import numpy as np
import h5py


class ToupcamH5(DataBrowserView):

    name = 'toupcam'
    
    def setup(self):
        
        self.ui = self.imview = pg.ImageView()
        self.spot_px = pg.CircleROI((0 - 5, 0 - 5), (10, 10) , movable=False, pen=pg.mkPen('r', width=3))
        self.imview.view.addItem(self.spot_px)   
        self.spot_px.setZValue(100)

    def on_change_data_filename(self, fname):
        
        try:
            self.h5file = h5py.File(fname, 'r')
            M = self.h5file['measurement/toupcam_spot_optimizer']
            self.img = self.h5file['measurement/toupcam_spot_optimizer/image'][:]  # .swapaxes(0,1)
            print(self.img.shape)
            self.img = self.img[:, ::-1, :]
            self.imview.setImage(self.img)

            # if taken with spotoptimizer the file contains a spot_px
            S = M['settings'].attrs
            if 'spot_px_x' in S.keys():
                self.spot_px.setPos(S['spot_px_x'], S['spot_px_y'])     
                self.spot_px.setVisible(True)
            else:
                self.spot_px.setVisible(False)

            self.h5file.close()

        except Exception as err:
            self.imview.setImage(np.zeros((10, 10)))
            self.databrowser.ui.statusbar.showMessage("failed to load %s:\n%s" % (fname, err))
            raise(err)
        
    def is_file_supported(self, fname):
        return ('toupcam' in fname) and ('.h5' in fname)
