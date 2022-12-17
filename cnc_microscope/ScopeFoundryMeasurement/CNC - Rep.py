from ScopeFoundry import Measurement
import pyqtgraph as pg
from qtpy import QtCore
import numpy as np
import time
from tkinter import *
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path
import os
from PIL import Image
#from win32comext.shell.shell import BHID_SFObject


class CNC(Measurement):
    
    name = 'Laser CNC'
    
    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "CNC.ui")
        #self.ui = load_qt_ui_file(self.ui_filename)
        Measurement.__init__(self, app)

    def setup(self):

        self.V_xy = self.add_logged_quantity("XY Velocity",
                                                       dtype=float, spinbox_decimals=3, initial=0, vmin=0,
                                                       vmax=100, ro=False)
        self.delta_zx = self.add_logged_quantity("Delta(z/x)",
                                                       dtype=float, spinbox_decimals=4, initial=0, vmin=-1,
                                                       vmax=1, ro=False)
        self.delta_zy = self.add_logged_quantity("Delta(z/y)",
                                                       dtype=float, spinbox_decimals=4, initial=0, vmin=-1,
                                                       vmax=1, ro=False)
        self.extraSleepTime = self.add_logged_quantity("Extra Sleep Time",
                                                       dtype=float, spinbox_decimals=0, initial=0, vmin=0,
                                                       vmax=100, ro=False)
        

        self.Job_Filename = self.add_logged_quantity("Job_filename", dtype = str, initial = None, ro=False)
        self.Img_Filename = self.add_logged_quantity("Img_filename", dtype = str, initial = None, ro=False)
        
        







    def setup_figure(self):
        
        # Connect Spin Box
        self.V_xy.connect_to_widget(self.ui.Vxy_doubleSpinBox)
        self.delta_zx.connect_to_widget(self.ui.delta_zx_doubleSpinBox)
        self.delta_zy.connect_to_widget(self.ui.delta_zy_doubleSpinBox)
        self.extraSleepTime.connect_to_widget(self.ui.ExtraSleepTime_doubleSpinBox)
        
        # Connect Push Button
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        
        #########TO BE DEVELOPED#############
        self.ui.AutoFocus_PushButton.clicked.connect(self.print_JobFile)
        self.ui.AutoLevel_PushButton.clicked.connect(self.print_ImgFile)
        ###########################
        
        ######### Connect to File Browser ###############
        self.Job_Filename.connect_to_widget(self.ui.Job_File_lineEdit)
        self.ui.JobFileBrowseButton.clicked.connect(self.browse_job_file)
        
        self.Img_Filename.connect_to_widget(self.ui.Img_File_lineEdit)        
        self.ui.ImgFileBrowseButton.clicked.connect(self.browse_img_file)
        ###################################################
        
        
        
        self.graph_layout = pg.GraphicsLayoutWidget()
        self.ui.main_horizontalLayout.addWidget(self.graph_layout)


        
        #tcam.settings.ctemp.updated_value[int].connect(self.ui.ctemp_slider.setValue)
        #self.ui.ctemp_slider.sliderMoved[int].connect(tcam.settings.ctemp.update_value)
        
        #self.ui.ctemp_slider.valueChanged.connect(self.valuechange)
        #self.ui.ctemp_value.setText(str(self.ui.ctemp_slider.value()))
        
        # connect to spinboxes 



        
        
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
        
        
        self.CNCstage = self.app.hardware.PI_xyz_stage.nanopositioner
        jname = os.path.basename(self.Job_Filename.val)
        jdir = os.path.dirname(self.Job_Filename.val)
        
        os.chdir(jdir)
        
        # Close the shutter before opening
        #self.app.hardware.dual_position_slider.move_fwd()
        time.sleep(0.2)
        
        
        with open(jname, 'rt') as jobj:
            
            shutter_pos = 0
            
            for line in jobj:
                xt, yt, vxy, shutter_target = line.split(',')
                xt = float(xt)
                yt = float(yt)
                vxy = float(vxy)
                shutter_target = float(shutter_target)
                xv, yv = self.CNCstage.set_vel_xy(vxy, xt, yt)
                zt, zv = self.CNCstage.z_comp(self.delta_zx.val, self.delta_zy.val, xv, yv, xt, yt)
                
                #Open or close the shutter 
                if shutter_pos == shutter_target:
                    # If the current shutter position is same with the target position 
                    #do nothing
                    print("No Change in Shutter")
                
                elif shutter_target == 1:
                    self.app.hardware.dual_position_slider.move_bkwd()
                    #time.sleep(0.2)
                    print("Open the Shutter")
                    
                elif shutter_target == 0:
                    self.app.hardware.dual_position_slider.move_fwd()
                    #time.sleep(0.2)
                    print("Close the Shutter")
                    
                self.CNCstage.jogging(xt, yt, zt, xv, yv, zv)
                
                shutter_pos = shutter_target
                
        self.app.hardware.dual_position_slider.move_fwd()
        print("Done")
                #print(type(x6))
                
        
        
        #print(jname, '\n\t' ,jdir)
        
        
        #iname = os.path.basename(self.Img_Filename.val)
        #idir = os.path.dirname(self.Img_Filename.val)
        
        #open(self.Img_Filename.val)
        
        #print(iname, '\n\t' ,idir)
        
    def update_display(self):
        im = Image.open(self.Img_Filename)
        pix = np.flipud(np.rot90(np.array(im)))
        pg.image(pix)
        
    def get_rgb_image(self):
        cam = self.app.hardware['toupcam'].cam
        data = cam.get_image_data()
        raw = data.view(np.uint8).reshape(data.shape + (-1,))
        bgr = raw[..., :3]
        return bgr[..., ::-1]

    def print_JobFile(self):
        
        jnam = self.settings.Job_filename.val
        print(jnam)
    
    
    def print_ImgFile(self):

        jnam = self.settings.Img_filename.val
        print(jnam)
    
    
    def browse_job_file(self):
        # Browse the file and save the path to self.Job_Filename
        
        job = Tk()
        job.withdraw()   # Hide the TK window
        job.fileName = filedialog.askopenfilename( filetypes = ( ("Target list", "*.csv"), ("All Files", "*.*") ) )
        #job.deiconify()
        self.Job_Filename.val = job.fileName
        self.ui.Job_File_lineEdit.setText(job.fileName)
 
        
        
    def browse_img_file(self):
        # Browse the file and save the path to self.Img_Img_Filename
        
        img = Tk()
        img.withdraw()   # Hide the TK window
        img.fileName = filedialog.askopenfilename( filetypes = ( ("Image Background", "*.bmp"), ("All Files", "*.*") ) )
        #img.deiconify()  # Show the TK window
        self.Img_Filename.val = img.fileName
        self.ui.Img_File_lineEdit.setText(img.fileName)
        
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
