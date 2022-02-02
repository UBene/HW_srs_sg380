from ScopeFoundry.data_browser import DataBrowserView
import numpy as np
import h5py
import pyqtgraph as pg

class SurveyScanMapView(DataBrowserView):

    name = 'survey_scan_map'
    
    def setup(self):
        
        self.ui = self.graph_layout = pg.GraphicsLayoutWidget()
        self.plot = self.graph_layout.addPlot(title="Survey Scan Map")
        
        self.img_items = []
        self.plot.setAspectLocked(lock=True, ratio=1)

        
    def on_change_data_filename(self, fname):
        
        try:
            self.dat = h5py.File(fname, 'r')
            
            self.H = self.dat['measurement/survey_scan']
            self.image_strips = np.array(self.H['image_strips'])
            self.strip_rects = np.array(self.H['strip_rects'])
            self.update_display()
            
        except Exception as err:
            self.databrowser.ui.statusbar.showMessage("failed to load %s:\n%s" %(fname, err))
            self.dat.close()
            raise(err)
        
    def is_file_supported(self, fname):
        return "survey_scan.h5" in fname      
      

    def update_display(self):    
        self.plot.clear()

        self.img_items = dict()

        for j in range(self.image_strips.shape[0]):
            img_strip = self.image_strips[j]
            img_item = self.img_items[j] = pg.ImageItem()
            self.plot.addItem(img_item)            
            img_item.setImage(img_strip[:,::-1,:])
            img_item.setRect(pg.QtCore.QRectF(*self.strip_rects[j]))
