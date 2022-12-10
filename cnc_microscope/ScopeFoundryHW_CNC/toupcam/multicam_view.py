
from toupcam.camera import ToupCamCamera, get_number_cameras
from ScopeFoundry import BaseApp
from qtpy import QtCore
import pyqtgraph as pg
import time
import numpy as np

class ToupCamMultiViewApp(BaseApp):
    
    def __init__(self, argv):
        BaseApp.__init__(self, argv)
        self.setup()
        
    def setup(self):
        self.num_cams = get_number_cameras()
        self.cams = []
        self.imviews = []
        
        for i in range(self.num_cams):
            cam = cam = ToupCamCamera(resolution=2, cam_index=i)
            cam.open()
            time.sleep(1.0)
            self.cams.append(cam)
        
            imview = pg.ImageView()
            self.imviews.append(imview)
            imview.show()
            imview.setWindowTitle("ToupCam Camera {}".format(i) )
    
        self.display_update_period = 0.1 # seconds
        self.display_update_timer = QtCore.QTimer(self)
        self.display_update_timer.timeout.connect(self.update_display)
        self.display_update_timer.start(self.display_update_period)
    
    def update_display(self):
        
        for i in range(self.num_cams):
            im = np.array(self.cams[i].get_image_data())
            #print(im.shape, np.max(im))
            self.imviews[i].setImage(np.transpose(im))
            

if __name__ == '__main__':
    app = ToupCamMultiViewApp([])
    app.exec_()