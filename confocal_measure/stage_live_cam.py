'''
Created on Jun 13, 2021

@author: Benedikt Ursprung
'''

from qtpy import QtCore, QtGui, QtWidgets
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
from numpy import dtype
from ScopeFoundry.measurement import Measurement
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path
import time


class EventProxy(QtCore.QObject):

    def __init__(self, qobj, callback):
        QtCore.QObject.__init__(self)
        self.callback = callback
        qobj.installEventFilter(self)

    def eventFilter(self, obj, ev):
        return self.callback(obj, ev)
    
    
class _ScaledLiveCam(Measurement):
    
    name = '_scaled_live_cam'
    
    def setup(self):
        self.settings.New('auto_level', dtype=bool, initial=False)
        self.settings.New('crosshairs', dtype=bool, initial=False)
        self.settings.New('flip_x', dtype=bool, initial=False)
        self.settings.New('flip_y', dtype=bool, initial=False)
    
    def setup_figure(self):
        
        self.settings.activation.connect_to_widget(self.ui.live_checkBox)        
        self.settings.auto_level.connect_to_widget(self.ui.auto_level_checkBox)
        self.settings.crosshairs.connect_to_widget(self.ui.crosshairs_checkBox)
                
        self.set_cam_hw_settings()       
        self.hw.settings.connected.connect_to_widget(self.ui.cam_connect_checkBox)

        
        self.graph_layout = pg.GraphicsLayoutWidget()
        self.plot = self.graph_layout.addPlot()
        self.img_item = pg.ImageItem()
        self.plot.addItem(self.img_item)
        self.plot.setAspectLocked(lock=True, ratio=1)
        self.img_label = QtWidgets.QLabel()        
        self.ui.plot_groupBox.layout().addWidget(self.img_label)
        
        def switch_camera_view():
            self.ui.plot_groupBox.layout().addWidget(self.graph_layout)
            self.graph_layout.showMaximized() 
        self.ui.show_pushButton.clicked.connect(switch_camera_view)
        #self.ui.plot_groupBox.layout().addWidget(self.imview)
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)
        
        
        self.ui.auto_exposure_comboBox.addItem("placeholder")
        self.ui.auto_exposure_comboBox.setCurrentIndex(0)
        def apply_auto_exposure_index():
            self.hw.cam.set_auto_exposure(self.ui.auto_exposure_comboBox.currentIndex())
        self.ui.auto_exposure_comboBox.currentIndexChanged.connect(apply_auto_exposure_index)
        self.ui.save_pushButton.clicked.connect(self.save_image)
        
        self.crosshairs = [pg.InfiniteLine(movable=False, angle=90, pen=(255,0,0,200)),
                           pg.InfiniteLine(movable=False, angle=0, pen=(255,0,0,200))]
        for ch in self.crosshairs:
            self.plot.addItem(ch)
            ch.setZValue(100)
            
            
    def get_rgb_image(self):
        '''override'''
        
        
    def set_cam_hw_settings(self):
        '''Override, def self.hw, '''
        
        self.ui = load_qt_ui_file(sibling_path(__file__,'flircam_live_measure.ui'))
        self.hw = self.app.hardware['flircam']
        self.hw.settings.cam_index.connect_to_widget(self.ui.cam_index_doubleSpinBox)
        self.hw.settings.frame_rate.connect_to_widget(self.ui.framerate_doubleSpinBox)
        self.hw.settings.exposure.connect_to_widget(self.ui.exp_doubleSpinBox)
        pass
        
    def run(self):
        self.hw.settings['connected'] = True
        if self.ui.auto_exposure_comboBox.count() == 1:
            self.ui.auto_exposure_comboBox.addItems(self.hw.cam.get_auto_exposure_options())
            self.ui.auto_exposure_comboBox.removeItem(0)
            self.ui.auto_exposure_comboBox.setCurrentIndex(2)

        while not self.interrupt_measurement_called:
            time.sleep(0.5)
            self.hw.settings.exposure.read_from_hardware()
    
    def update_display(self):
        self.display_update_period = 0.01
        if not self.hw.img_buffer:
            #print("no new frame")
            return
        self.im = im = self.hw.img_buffer.pop(0).copy()
        self.img_item.setImage(im.swapaxes(0,1),autoLevels=self.settings['auto_level'])
        
        for ch,(x,y) in zip(self.crosshairs, [(im.shape[1]/2,0), (0,im.shape[0]/2)]):
            ch.setPos((x,y))
            ch.setZValue({True:1, False:-1}[self.settings['crosshairs']])    
        
        
    

class StageLiveCam:
    '''us as a base class, requires: 
    A) live cam measure sister class  
        1. plot 
        2. img_item 
        3. get_rgb_image()
        
    B) to enable moving using shift double click override
        1. get_current_stage_position
        2. set_stage_position
        
    C) call setup() and setup_figure()
    
    see ir_microscope/measurements/stage_live_cam for an example
    '''

    def setup(self):

        if not hasattr(self.settings, 'flip_x'):
            self.settings.New('flip_x', dtype=bool, initial=False)
        if not hasattr(self.settings, 'flip_y'):
            self.settings.New('flip_y', dtype=bool, initial=False)
        if not hasattr(self.settings, 'center_x'):
            self.settings.New("center_x", dtype=float, unit='%', initial=50)
        if not hasattr(self.settings, 'center_y'):
            self.settings.New("center_y", dtype=float, unit='%', initial=50)
        if not hasattr(self.settings, 'img_scale'):
            self.img_scale = self.settings.New("img_scale", dtype=float, unit='um', initial=50.)
        if not hasattr(self.settings, 'crosshairs'):
            self.settings.New('crosshairs', dtype=bool, initial=False)

        self.add_operation('save_image', self.save_image)

    def setup_figure(self):
        self.plot.scene().sigMouseClicked.connect(self.on_scene_clicked)
        self.graph_layout_eventProxy = EventProxy(self.graph_layout, self.graph_layout_event_filter)

        self.crosshairs = [pg.InfiniteLine(movable=False, angle=90, pen=(255, 0, 0, 200)),
                           pg.InfiniteLine(movable=False, angle=0, pen=(255, 0, 0, 200))]
        for ch in self.crosshairs:
            self.plot.addItem(ch)
            ch.setZValue(100)

        self.img_rect = pg.QtCore.QRectF(0.01, 0.1, 1, 1)
        #self.img_item.setRect(self.img_rect)

        self.status = {'text':None, 'color':'g'}

    def get_current_stage_position(self):
        """Override! return x,y,z position in um (z can be None) """
        return (0, 0, 0)

    def set_stage_position(self, x, y, z=None):
        """Override! sets the x,y stage position in um and z if applicable"""
        pass

    def set_scale(self):
        x, y, z = self.get_current_stage_position()
        S = self.settings
        scale = S['img_scale']
        self.im_aspect = im_aspect = self.img_item.height() / self.img_item.width()
        
        
        self.img_rect = pg.QtCore.QRectF(x - S['center_x'] * scale / 100,
                                y - S['center_y'] * scale * im_aspect / 100,
                                scale,
                                scale * im_aspect)
        self.img_item.setRect(self.img_rect)


        for ch in self.crosshairs:
            ch.setPos((x, y))
            ch.setZValue({True:1, False:-1}[self.settings['crosshairs']])

        if hasattr(self, 'center_roi'):
            self.center_roi.setVisible(False)

    def get_image(self):
        img = self.get_rgb_image()
        if type(img) == bool:
            return False
        img = np.flip(img.swapaxes(0, 1), 0)

        if self.settings['flip_x']:
            img = img[::-1,:,:]
        if self.settings['flip_y']:
            img = img[:,::-1,:]
        return img

    def update_display(self):
        self.img = img = self.get_image()
        if type(img) == bool:
            return

        self.img_item.setImage(img)
        self.img = img

        if not self.settings['auto_level']:
            self.img_item.setLevels((0, 255))

        self.set_scale()

        if type(self.status) == dict:
            self.plot.setTitle(**self.status)
        elif type(self.status) == str:
            self.plot.setTitle(self.status)

    def on_scene_clicked(self, event):
        p = self.plot
        viewbox = p.vb
        pos = event.scenePos()
        pt = viewbox.mapSceneToView(pos)

        x = pt.x()
        y = pt.y()

        if  event.modifiers() == QtCore.Qt.ShiftModifier and event.double():
            print(self.name, 'Shift + Double click')
            
            xs, ys, zs = self.get_current_stage_position()
            dx = x - xs
            dy = y - ys
            
            print(x,y, dx, dy)
            self.set_stage_position(xs + dx, ys + dy, None)
            

    def graph_layout_event_filter(self, obj, event):
        # print(self.name, 'eventFilter', obj, event)
        try:
            if type(event) == QtGui.QKeyEvent:

                if event.key() == QtCore.Qt.Key_Space:
                    self.snap()
                    print(event.key(), repr(event.text()), event.isAutoRepeat())

                    # event.accept()
                    # return True
        finally:
            # standard event processing
            return QtCore.QObject.eventFilter(self, obj, event)

    def save_image(self):
        
        # save h5
        self.h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
        H = self.h5_meas_group = h5_io.h5_create_measurement_group(self, self.h5_file)
        im = self.get_image()
        H['image'] = im
        x, y = self.img_rect.x(), self.img_rect.y()
        w, h = self.img_rect.width(), self.img_rect.height()
        imshow_extent = [x, y, x + w, y + h]

        H['imshow_extent'] = imshow_extent

        print(imshow_extent)
        self.h5_file.close()
        print(self.name, 'h5 saved file successfully')
        
        
        #TODO save jpg/png


'''
functions taken from http://stackoverflow.com/questions/7765810/is-there-a-way-to-detect-if-an-image-is-blurry
is reference of 
http://www.sayonics.com/publications/pertuz_PR2013.pdf
Pertuz 2012: Analysis of focus measure operators for shape-from-focus

code transformed from C++.openCV -> python.cv2

RETURN: focusMeasure - parameter describing sharpness of an image
'''
try:
    import cv2

    def modifiedLaplacian(img):
        ''''LAPM' algorithm (Nayar89)'''
        print('modifiedLaplacian could not make this work yet, CHOOSE DIFFERENT ALGO')
        return 0.0
        # kernelx = np.array([[0, 0, 0], [-1, 2, -1], [0, 0, 0]], dtype=np.float32)
        # Lx = cv2.filter2D(img, cv2.CV_64F, kernelx)
        # kernely = np.array([[0, -1, 0], [0, 2, 0], [0, -1, 0]], dtype=np.float32)
        # Ly = cv2.filter2D(img, cv2.CV_64F, kernely)
        # return (np.abs(Lx) + np.abs(Ly)).mean()

    def varianceOfLaplacian(img):
        ''''LAPV' algorithm (Pech2000)'''
        lap = cv2.Laplacian(img, ddepth=-1)  # cv2.cv.CV_64F)
        stdev = cv2.meanStdDev(lap)[1]
        s = stdev[0] ** 2
        return s[0]

    def tenengrad(img, ksize=3):
        ''''TENG' algorithm (Krotkov86)'''
        Gx = cv2.Sobel(img, ddepth=cv2.CV_64F, dx=1, dy=0, ksize=ksize)
        Gy = cv2.Sobel(img, ddepth=cv2.CV_64F, dx=0, dy=1, ksize=ksize)
        FM = Gx ** 2 + Gy ** 2
        return cv2.mean(FM)[0]

    def normalizedGraylevelVariance(img):
        ''''GLVN' algorithm (Santos97)'''
        mean, stdev = cv2.meanStdDev(img)
        s = stdev[0] ** 2 / mean[0]
        return s[0]

    focus_measures_funcs = {'None':None,
                            'modifiedLaplacian':modifiedLaplacian,
                            'varianceOfLaplacian':varianceOfLaplacian,
                            'tenengrad':tenengrad,
                            'normalizedGraylevelVariance':normalizedGraylevelVariance}
except ImportError:
    focus_measures_funcs = {'None':None}
    print('Warning OpenCV does not exist: conda install -c conda-forge opencv')


class AutoFocusStageLiveCam(StageLiveCam):

    def setup(self):
        StageLiveCam.setup(self)
        self.settings.New('focus_measure_alg', str, choices=focus_measures_funcs.keys(),
                          initial='None')
        self.settings.New('focus_measure', float, initial=0.0)

        # T
        for name, ini in [("focus_measure_dx", 0), ("focus_measure_dy", 0)]:
            self.settings.New(name, float, initial=ini)

    def setup_figure(self):
        StageLiveCam.setup_figure(self)

        self.focus_roi = pg.ROI((0, 0), (1024, 768), movable=True)
        self.plot.addItem(self.focus_roi)
        self.focus_roi.addScaleHandle([1, 1], [0, 0])
        #self.focus_roi.addScaleHandle([0, 0], [1, 1])
        self.focus_roi.sigRegionChangeFinished.connect(self.mouse_update_scan_roi)

    def mouse_update_scan_roi(self):
        x0, y0 = self.focus_roi.pos()
        x1, y1, z1 = self.get_current_stage_position()

        self.settings['focus_measure_dx'] = -(x1 - x0)
        self.settings['focus_measure_dy'] = -(y1 - y0)

        #self.update_scan_roi

    def update_scan_roi(self):
        x, y, z1 = self.get_current_stage_position()
        
        S = self.settings
        
        dx = S['focus_measure_dx']
        dy = S['focus_measure_dy']
        
        
        
        
        w0,h0 = self.focus_roi.size()
        w = min(w0, S['img_scale']*(1-S['center_x']/100))
        
        img_aspect = self.img_rect.height()/self.img_rect.width()
        h = min(h0, S['img_scale']*(1-S['center_y']/100)*img_aspect)
        
        
        self.focus_roi.blockSignals(True)
        #self.focus_roi.maxBounds = self.img_rect
        self.focus_roi.setSize((w,h))
        self.focus_roi.setPos((x+dx, y+dy))
        self.focus_roi.blockSignals(False)



    def update_display(self):
        StageLiveCam.update_display(self)
        self.update_scan_roi()
        self.focus_roi.setZValue(1002)

        S = self.settings
        if S['focus_measure_alg'] != 'None':
            self.focus_roi.setVisible(True)
            
            L = np.float32(self.img)
            selected = self.focus_roi.getArrayRegion(self.img, self.img_item)
            fm = focus_measures_funcs[S['focus_measure_alg']](selected)
            #fm = focus_measures_funcs[S['focus_measure_alg']](L)

            S['focus_measure'] = fm
            self.status = f' focus measure {fm:1.2}'
        else:
            self.focus_roi.setVisible(True)
