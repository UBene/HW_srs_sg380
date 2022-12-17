from ScopeFoundry import Measurement
import pyqtgraph as pg
from qtpy import QtCore
import numpy as np
import time
from tkinter import *
from tkinter.filedialog import askopenfilename
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path
import os
#from win32comext.shell.shell import BHID_SFObject



class ToupCamLiveMeasure(Measurement):
    
    name = 'toupcam_live'

    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "toupcam_live_measure_ver_2.ui")
        #self.ui = load_qt_ui_file(self.ui_filename)
        Measurement.__init__(self, app)
    
    def setup(self):
        ## setup for live measurement
        self.settings.New('auto_level', dtype=bool, initial=False)


        ## setup for cnc
        self.Job_Filename = self.add_logged_quantity("Job_filename", dtype=str, initial=None, ro=False)
        self.IncludePreview = self.add_logged_quantity("include_preview", dtype=bool, initial=False)
        # self.job_preview = None

    def setup_figure(self):

        self.graph_layout = pg.GraphicsLayoutWidget()
        self.ui.main_horizontalLayout.addWidget(self.graph_layout)

        self.settings.activation.connect_to_widget(self.ui.live_checkBox)
        self.settings.auto_level.connect_to_widget(self.ui.auto_level_checkBox)

        tcam = self.app.hardware['toupcam']        
        tcam.settings.connected.connect_to_widget(self.ui.cam_connect_checkBox)
        tcam.settings.cam_index.connect_to_widget(self.ui.cam_index_doubleSpinBox)
        tcam.settings.res_mode.connect_to_widget(self.ui.res_mode_doubleSpinBox)
        tcam.settings.auto_exposure.connect_to_widget(self.ui.auto_exp_checkBox)
        tcam.settings.magnification.connect_to_widget(self.ui.mag_doubleSpinBox)
        
        # connect to sliders 
        tcam.settings.exposure.connect_to_widget(self.ui.exposure_horizontalSlider)
        #tcam.settings.ctemp.connect_to_widget(self.ui.ctemp_slider)
        #tcam.settings.tint.connect_to_widget(self.ui.tint_slider)

        tcam.settings.gain.connect_to_widget(self.ui.gain_horizontalSlider)        
        #tcam.settings.contrast.connect_to_widget(self.ui.contrast_horizontalSlider)
        #tcam.settings.brightness.connect_to_widget(self.ui.brightness_horizontalSlider)
        #tcam.settings.gamma.connect_to_widget(self.ui.gamma_horizontalSlider)
        
        #tcam.settings.ctemp.updated_value[int].connect(self.ui.ctemp_slider.setValue)
        #self.ui.ctemp_slider.sliderMoved[int].connect(tcam.settings.ctemp.update_value)
        
        #self.ui.ctemp_slider.valueChanged.connect(self.valuechange)
        #self.ui.ctemp_value.setText(str(self.ui.ctemp_slider.value()))
        
        # connect to spinboxes 
        tcam.settings.exposure.connect_to_widget(self.ui.exp_value)
        #tcam.settings.ctemp.connect_to_widget(self.ui.ctemp_value)
        #tcam.settings.tint.connect_to_widget(self.ui.tint_value)

        tcam.settings.gain.connect_to_widget(self.ui.gain_doubleSpinBox)        
        #tcam.settings.contrast.connect_to_widget(self.ui.contrast_doubleSpinBox)
        #tcam.settings.brightness.connect_to_widget(self.ui.brightness_doubleSpinBox)
        #tcam.settings.gamma.connect_to_widget(self.ui.gamma_doubleSpinBox)

        tcam.settings.calibration.connect_to_widget(self.ui.calibration_doubleSpinBox)

        # pushButtons
        self.ui.snap_pushButton.clicked.connect(self.snap_h5)        
        self.ui.defaults_pushButton.clicked.connect(tcam.set_default_values)

        ######### Connect to File Browser ###############
        self.Job_Filename.connect_to_widget(self.ui.Job_File_lineEdit)
        self.ui.JobFileBrowseButton.clicked.connect(self.browse_job_file)
        self.IncludePreview.connect_to_widget(self.ui.include_preview_checkBox)
        ###################################################

        ## setup the plotted figure
        #self.graph_layout = pg.GraphicsLayoutWidget()
        #self.ui.main_horizontalLayout.addWidget(self.graph_layout)

        self.plot = self.graph_layout.addPlot()
        self.img_item = pg.ImageItem()
        self.plot.addItem(self.img_item)
        self.plot.setAspectLocked(lock=True, ratio=1)
        
        self.center_roi = pg.CircleROI((0-5,0-5), (10,10) , movable=False, pen=pg.mkPen('c', width=3))
        self.plot.addItem(self.center_roi)
        #\font = QFont()
        #font.setPointSize(14)
        #font.setBold(True)
        self.roi_label = pg.TextItem('')
        #self.roi_label.setFont(font)
        self.plot.addItem(self.roi_label)
        self.roi_label.setText(str(self.center_roi.size()[0]))


        ## to do add functionality that a double click on a position in the image moves the stage to the position.

    def run(self):
        tcam = self.app.hardware['toupcam']
        tcam.settings['connected'] = True
        print('The camera is Live, if you want to preview the job file, check the Include Preview button and re-run')

        # create preview of files (updated by update_display)
        if self.IncludePreview.val:
            jname = os.path.basename(self.Job_Filename.val)
            jdir = os.path.dirname(self.Job_Filename.val)
            os.chdir(jdir)
            self.Yt, self.Xt = self.previewCurve(jname)
            self.Xo, self.Yo, self.fUni_per_um = self.Xt[0], self.Yt[0], 1

        # update the camera feed
        while not self.interrupt_measurement_called:
            self.im = self.get_rgb_image().swapaxes(0, 1)
            time.sleep(0.05)
            if tcam.settings['auto_exposure']:
                tcam.settings.exposure.read_from_hardware()

    def previewCurve(self, jname):
        with open(jname, 'rt') as jobj:
            XtList = []
            YtList = []
            for line in jobj:
                lineVals = line.split(',')
                xt = lineVals[0]
                yt = lineVals[1]
                xt = float(xt)
                yt = float(yt)
                XtList.append(xt)
                YtList.append(yt)
            Xt = np.array(XtList)
            Yt = np.array(YtList)

        return Xt, Yt
        
    def update_display(self):
        tcam = self.app.hardware['toupcam']
        self.img_item.setImage(self.im, autoLevels=self.settings['auto_level'])
        if not self.settings['auto_level']:
            self.img_item.setLevels((0, 255))
        
        width  = tcam.settings['width_micron']
        height = tcam.settings['height_micron']
        x_center, y_center = tcam.settings['centerx_micron'], tcam.settings['centery_micron']
        
        x0 = -x_center
        y0 = -y_center
        
        self.img_rect = pg.QtCore.QRectF(x0, y0, width, height)
        self.img_item.setRect(self.img_rect)
        self.roi_label.setText('{:.2f} micron'.format(self.center_roi.size()[0]))
        
        self.plot.addItem(self.roi_label)

    def get_rgb_image(self):
        cam = self.app.hardware['toupcam'].cam
        data = cam.get_image_data()
        raw = data.view(np.uint8).reshape(data.shape + (-1,))
        bgr = raw[..., :3]
        return bgr[..., ::-1]


    def snap_h5(self):
        
        #
        from ScopeFoundry import h5_io
        #self.app.hardware['asi_stage'].correct_backlash(0.02)


        self.h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
        H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
        im = self.get_rgb_image()
        im = np.flip(im.swapaxes(0,1),0)
        H['image'] = im
        self.h5_file.close()
        print('saved file successfully', im.sum())
        
        return im

    def print_JobFile(self):

        jnam = self.settings.Job_filename.val
        print(jnam)

    def print_ImgFile(self):

        jnam = self.settings.Img_filename.val
        print(jnam)

    def browse_job_file(self):
        # Browse the file and save the path to self.Job_Filename

        job = Tk()
        job.withdraw()  # Hide the TK window
        job.fileName =  askopenfilename(filetypes=(("Target list", "*.csv"), ("All Files", "*.*")))
        # job.deiconify()
        self.Job_Filename.val = job.fileName
        self.ui.Job_File_lineEdit.setText(job.fileName)

    # def browse_img_file(self):
    #     # Browse the file and save the path to self.Img_Img_Filename
    #
    #     img = Tk()
    #     img.withdraw()  # Hide the TK window
    #     img.fileName = askopenfilename(filetypes=(("Image Background", "*.bmp"), ("All Files", "*.*")))
    #     # img.deiconify()  # Show the TK window
    #     self.Img_Filename.val = img.fileName
    #     self.ui.Img_File_lineEdit.setText(img.fileName)