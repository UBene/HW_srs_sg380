from ScopeFoundry import BaseApp
import pyqtgraph as pg
import pyqtgraph.dockarea as dockarea
from pyqtgraph.dockarea.DockArea import DockArea
import h5py
import numpy as np

class SurveyScanViewer(BaseApp):
    
    def __init__(self, argv):
        BaseApp.__init__(self, argv)
        self.setup()
        self.setup_ui()


    def setup(self):
        
        self.settings.New("file", dtype='file')
        self.settings.New("y_shift", dtype=float, unit='um')
        
        self.settings.file.add_listener(self.load_file)
        
    def setup_ui(self):
        #self.ui = load_qt_ui_file(sibling_path(__file__, "data_browser.ui"))
        #self.ui = load_qt_ui_from_pkg('ScopeFoundry', 'data_browser.ui')
        self.ui = DockArea()
        
        self.ui.show()
        self.ui.raise_()
        
        self.ui.addDock(name='settings', widget =         self.settings.New_UI())
        
        self.plot = pg.PlotWindow()
        self.ui.addDock(name='plot', widget= self.plot, position='right')
        
        cw = self.setup_console_widget()
        self.ui.addDock(name='console', widget=cw)
        
        
    def load_file(self):
        fname = self.settings['file']
        try:
            self.dat = h5py.File(fname, 'r')
            
            self.H = self.dat['measurement/survey_scan']
            self.image_strips = np.array(self.H['image_strips'])
            self.strip_rects = np.array(self.H['strip_rects'])
            self.setup_display()
            
        except Exception as err:
            #self.databrowser.ui.statusbar.showMessage("failed to load %s:\n%s" %(fname, err))
            self.dat.close()
            raise(err)

    def setup_display(self):    
        self.plot.clear()
        self.plot.setAspectLocked(lock=True, ratio=1)


        self.img_items = dict()

        for j in range(self.image_strips.shape[0]):
            img_strip = self.image_strips[j]
            img_item = self.img_items[j] = pg.ImageItem()
            self.plot.addItem(img_item)            
            img_item.setImage(img_strip[:,::-1,:])
            img_item.setRect(pg.QtCore.QRectF(*self.strip_rects[j]))

        
        
if __name__ == '__main__':
    
    app = SurveyScanViewer([])
    app.exec_()