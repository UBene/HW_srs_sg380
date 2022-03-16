'''
Created on Jun 24, 2019

@author: Benedikt Ursprung
'''
from ScopeFoundryHW.toupcam.toupcam_live_measure import ToupCamLiveMeasure
import pyqtgraph as pg
import numpy as np
from scipy.optimize import curve_fit
from scipy import exp

def gaus(x, a, x0, sigma):
    return a * exp(-(x - x0) ** 2 / (2 * sigma ** 2))


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
        kernelx = np.array([[0, 0, 0], [-1, 2, -1], [0, 0, 0]])
        Lx = cv2.filter2D(img, cv2.CV_64F, kernelx)
        kernely = np.array([[0, -1, 0], [0, 2, 0], [0, -1, 0]])
        Ly = cv2.filter2D(img, cv2.CV_64F, kernely)
        return (np.abs(Lx) + np.abs(Ly)).mean()

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


class ToupCamSpotOptimizer(ToupCamLiveMeasure):
    
    name = 'toupcam_spot_optimizer'
    
    def setup(self):
        ToupCamLiveMeasure.setup(self)
        
        self.gamut_dimensions = {'r':0, 'g':1, 'b':2,  # 'a':3,
                          # 'C':0,'M':1,'Y':2,'K':3,
                          'grayscale_ITU-R_601-2':'grayscale_ITU-R_601-2',
                          'None':None,
                          }
        
        self.settings.New('spot_px_x', int, initial=426)
        self.settings.New('spot_px_y', int, initial=385)
        
        self.settings.New('img_chan', str, choices=self.gamut_dimensions, initial='grayscale_ITU-R_601-2')
        self.settings.New('img_slicing', int, choices=(('avg_along_horizontal', 0), ('avg_along_vertical', 1),
                                                    ('slice_spot_vertically', 2), ('slice_spot_horizontally', 3)),
                                        initial=1)
        
        self.settings.New('wl', initial=532.0, unit='nm')
        self.settings.New('NA', initial=0.9)
    
        self.settings.New('fit_gaus', bool, initial=False)
        self.settings.New('inv_FWHM', float, initial=1.0)
        self.settings.New('max_val', float, initial=0.0)
        
        self.settings.New('focus_measure_alg', str, choices=focus_measures_funcs.keys(),
                          initial='None')
        self.settings.New('focus_measure', float, initial=0.0)
        for name, ini in [("focus_measure_i0", 0), ("focus_measure_i1", 1024), ("focus_measure_j0", 0), ("focus_measure_j1", 756)]:
            self.settings.New(name, int, initial=ini) 
    
    def setup_figure(self):
        ToupCamLiveMeasure.setup_figure(self)
                
        U = self.settings.New_UI(include=['img_chan', 'img_slicing',
                                          'wl', 'NA', 'fit_gaus',
                                          'spot_px_x', 'spot_px_y',
                                          'focus_measure_alg', 'focus_measure']
                                )
        self.ui.settings_verticalLayout.addWidget(U)
                
        self.hist_plot = self.graph_layout.addPlot(row=1, col=0)
        self.hist_plot.setMinimumHeight(240)
        self.hist_plot.setMaximumHeight(250)
        self.hist_plot.enableAutoRange()
        self.hist_line = self.hist_plot.plot()
    
        self.linear_region_item = pg.LinearRegionItem()
        self.linear_region_item.setZValue(-1)                         
        self.hist_plot.addItem(self.linear_region_item)
        self.linear_region_item.setVisible(False)
    
        self.marker = pg.CircleROI((0, 0), (1, 1) , movable=False, pen=pg.mkPen('r', width=3))
        self.plot.addItem(self.marker)
        
        self.marker_label = pg.TextItem('', color='r')
        self.plot.addItem(self.marker_label)

        self.center_roi.setVisible(False)        
        self.roi_label.setVisible(False) 

        self.slice_indicator_line = pg.InfiniteLine(movable=False, angle=90, pen=(255, 0, 0, 200))
        self.plot.addItem(self.slice_indicator_line)    
        
        self.focus_roi = pg.ROI((0, 0), (1024, 768), movable=True)
        self.plot.addItem(self.focus_roi)
        self.focus_roi.addScaleHandle([1, 1], [0, 0])
        self.focus_roi.addScaleHandle([0, 0], [1, 1])
        self.update_roi()
        self.focus_roi.sigRegionChangeFinished.connect(self.mouse_update_roi)
        
    def mouse_update_roi(self):
        x0, y0 = self.focus_roi.pos()
        w, h = self.focus_roi.size()
        x1, y1 = min(x0 + w, self.img_item.width()), min(y0 + h, self.img_item.height())
        x0, y0 = max(x0, 0), max(y0, 0)
        S = self.settings
        S['focus_measure_i0'] = int(x0)
        S['focus_measure_i1'] = int(x1)
        S['focus_measure_j0'] = int(y0)
        S['focus_measure_j1'] = int(y1)
        self.update_roi()
                
    def update_roi(self):
        S = self.settings
        i0 = S['focus_measure_i0']
        i1 = S['focus_measure_i1']
        j0 = S['focus_measure_j0']
        j1 = S['focus_measure_j1']
        self.focus_roi.blockSignals(True)
        self.focus_roi.setPos(i0, j0)
        self.focus_roi.setSize((i1 - i0, j1 - j0))        
        self.focus_roi.blockSignals(False)
            
    def update_display(self):
        im = self.get_rgb_image()
        self.img_item.setImage(im, autoLevels=self.settings['auto_level'])
        if not self.settings['auto_level']:
            self.img_item.setLevels((0, 255))

        if self.settings['img_chan'] == 'None':
            return
                
        S = self.settings            
        TS = self.app.hardware['toupcam'].settings      
        
        # spot size positioning 
        # Note that the scale on the display image is in pixels
        w, h = TS['width_pixel'], TS['height_pixel']
        self.img_item.setRect(pg.QtCore.QRectF(-0.5, -0.5, w, h))
        
        dif_limited_spot_nm = S['wl'] / (2 * S['NA'])
        nm_per_px = TS['calib_um_per_px'] * 1000
        dif_limited_spot_px = dif_limited_spot_nm / nm_per_px
        info_text = 'diffraction limited spot size: {:3.1f} pxs'.format(dif_limited_spot_px)

        spot_pos_x, spot_pos_y = S['spot_px_x'], S['spot_px_y']  # AmScope is zero-indexed
        self.slice_indicator_line.setPos((spot_pos_x, spot_pos_y))
        
        self.marker.setSize(dif_limited_spot_px)
        marker_pos_x0 = spot_pos_x - 0.5 * dif_limited_spot_px
        marker_pos_y0 = spot_pos_y - 0.5 * dif_limited_spot_px
        self.marker.setPos((marker_pos_x0, marker_pos_y0))
        self.marker_label.setPos(marker_pos_x0 + dif_limited_spot_px, marker_pos_y0 + 0.2)
        self.marker_label.setText('{:3.0f}nm dif. spot size'.format(dif_limited_spot_nm), color='r')

        # Saturation
        max_val = im.max()
        self.settings['max_val'] = max_val
        saturation = max_val / 255.0  # Assumes 8bit depth
        if saturation == 1:
            text = 'Warning: Camera saturated!'
            color = 'r'
        elif saturation >= 0.65 and saturation < 1:
            text = '{:2.0f}% saturation'.format(saturation * 100) 
            color = 'g'
        else:
            text = '{:2.0f}% saturation'.format(saturation * 100)
            color = (200, 200, 200)
        self.plot.setTitle(text, color=color)

        # Data selection            
        if S['img_chan'] == 'grayscale_ITU-R_601-2': 
            # ITU-R_601-2 is a recommendation to convert rgb to gray scale:
            # L = R * 299/1000 + G * 587/1000 + B * 114/1000 
            L = im[..., 0] * 299 / 1000 + self.im[..., 1] * 587 / 1000 + im[..., 2] * 114 / 1000
        else:
            chan = self.gamut_dimensions[S['img_chan']]
            L = im[..., chan]
        
        if S['img_slicing'] in (0, 1): 
            y = L.mean(S['img_slicing']) - 1
            self.slice_indicator_line.setVisible(False)
        if S['img_slicing'] == 2: 
            y = L[spot_pos_x,:]
            self.slice_indicator_line.setVisible(True)
            self.slice_indicator_line.setAngle(90)
        if S['img_slicing'] == 3: 
            y = L[:, spot_pos_y]
            self.slice_indicator_line.setVisible(True)
            self.slice_indicator_line.setAngle(0)

        self.hist_line.setData(y)

        info_text = ""
        
        # FWHM
        self.linear_region_item.setVisible(S['fit_gaus'])
        if S['fit_gaus']:
            a, mean, sigma = self.fit_gaus(y, baseline_deg=2)
            FWHM = 2.355 * sigma
            off_dif_limited = FWHM / dif_limited_spot_px
            info_text += 'Gaus fit: FWHM {:3.0f}% of diffraction limited spot size'.format(off_dif_limited * 100)
            if S['img_slicing'] in (1, 3):
                d = mean - S['spot_px_x'] 
                info_text += '<br> horizontal beam offset {:0.1f}px'.format(d)
            else:
                d = mean - S['spot_px_y']
                info_text += '<br> vertical beam offset {:0.1f}px'.format(d)
            self.linear_region_item.setRegion((mean - 0.5 * FWHM, mean + 0.5 * FWHM))
            self.linear_region_item.getViewBox().setRange(xRange=(mean - 3 * FWHM, mean + 3 * FWHM))
            self.linear_region_item.getViewBox().enableAutoRange(y=True)
            
            S['inv_FWHM'] = 1 / FWHM
        
        # Focus Measure
        if S['focus_measure_alg'] != 'None':
            s = np.s_[S["focus_measure_i0"]:S["focus_measure_i1"], S["focus_measure_j0"]:S["focus_measure_j1"]]
            fm = focus_measures_funcs[S['focus_measure_alg']](L[s])
            S['focus_measure'] = fm
            info_text += f' focus measure {fm:1.2}'
            self.focus_roi.setVisible(True)
        else:
            self.focus_roi.setVisible(False)
            
        self.hist_plot.setTitle(info_text)      

    def fit_gaus(self, y, baseline_deg=0):
    
        if baseline_deg != 0:
            import peakutils
            base = 1.0 * peakutils.baseline(y, baseline_deg)
            y = y - base
        
        y -= y.min()
        n = len(y) 
        x = np.arange(n)  # pixels

        p0 = [y.max(), y.argmax(), 10]
        popt, pcov = curve_fit(gaus, x, y, p0=p0)
        return popt  # a,mean,sigma 

        
