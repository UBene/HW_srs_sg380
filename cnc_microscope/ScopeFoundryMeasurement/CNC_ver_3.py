from ScopeFoundry import Measurement
import pyqtgraph as pg
from qtpy import QtCore
import numpy as np
import time
#from tkinter import *
from tkinter import Tk, filedialog
from scipy import spatial
from operator import itemgetter
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path
import os
#from win32comext.shell.shell import BHID_SFObject


class CNC(Measurement):
    
    name = 'Laser CNC'
    
    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "CNC_ver_3.ui")
        #self.ui = load_qt_ui_file(self.ui_filename)
        Measurement.__init__(self, app)
        self.wavepoints = []

    def setup(self):

        self.TableRate = self.add_logged_quantity("Table Rate",
                                                       dtype=float, spinbox_decimals=0, initial=0, vmin=0,
                                                       vmax=100000, ro=False)
        self.delta_zx = self.add_logged_quantity("Delta(z/x)",
                                                       dtype=float, spinbox_decimals=4, initial=0, vmin=-1,
                                                       vmax=1, ro=False)
        self.delta_zy = self.add_logged_quantity("Delta(z/y)",
                                                       dtype=float, spinbox_decimals=4, initial=0, vmin=-1,
                                                       vmax=1, ro=False)
        self.extraSleepTime = self.add_logged_quantity("Extra Sleep Time",
                                                       dtype=float, spinbox_decimals=0, initial=0, vmin=0,
                                                       vmax=100, ro=False)
        
        self.mode_line = self.add_logged_quantity("Line", dtype = bool, initial = False)
        self.mode_pnt = self.add_logged_quantity("Point", dtype = bool, initial = False)        

        self.Job_Filename = self.add_logged_quantity("Job_filename", dtype = str, initial = None, ro=False)
        self.Img_Filename = self.add_logged_quantity("Img_filename", dtype = str, initial = None, ro=False)
        
        







    def setup_figure(self):
        
        # Connect Spin Box
        self.TableRate.connect_to_widget(self.ui.TableRate_doubleSpinBox)
        self.delta_zx.connect_to_widget(self.ui.delta_zx_doubleSpinBox)
        self.delta_zy.connect_to_widget(self.ui.delta_zy_doubleSpinBox)
        
        # Connect Push Button
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        
        #########TO BE DEVELOPED#############
        self.ui.LoadJobFile_PushButton.clicked.connect(self.load_JobFile)
        self.ui.AutoLevel_PushButton.clicked.connect(self.print_ImgFile)
        ###########################
        
        ######### Connect to File Browser ###############
        self.Job_Filename.connect_to_widget(self.ui.Job_File_lineEdit)
        self.ui.JobFileBrowseButton.clicked.connect(self.browse_job_file)
        
        self.Img_Filename.connect_to_widget(self.ui.Img_File_lineEdit)        
        self.ui.ImgFileBrowseButton.clicked.connect(self.browse_img_file)
        ###################################################
        
        ########### Connect to Check Box ##################
        self.mode_line.connect_to_widget(self.ui.mode_line)
        self.mode_pnt.connect_to_widget(self.ui.mode_pnt)        
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
        wavegens = (1, 2, 3)
        oldtime = time.time()
        Total_Steps = self.CNCstage.pidevice.qWAV(1, 1)[1][1]
        try:
            self.CNCstage.startwave()
            while any(list(self.CNCstage.pidevice.IsGeneratorRunning(wavegens).values())):
                # Listens to interrupt command as fast as the computer can
                if self.interrupt_measurement_called:
                    print('process interrupted')
                    self.CNCstage.endwave()
                    return

                # Update Position and Progress Bar Every 0.5s
                if time.time() - oldtime > 0.5:
                    curr_pos = itemgetter('1', '2', '3')(self.CNCstage.pidevice.qPOS(('1', '2', '3')))
                    oldtime = time.time()
                    # Update Progress Bar
                    # StepNum = self.CNCstage.pidevice.qWGI(1) # WHY PI WHY!! NO INCLUDING THIS IN E 727 
                    StepNum = self.wavepoints.query(curr_pos)[1]
                    print('step {} of {}, position: {}'.format(StepNum, Total_Steps, curr_pos))
                    self.set_progress(StepNum / Total_Steps * 100)

            self.CNCstage.endwave()
            print("Done")
        except:
            self.CNCstage.endwave()
            raise


        

    def update_display(self):
        pass

    def load_JobFile(self):
        # I have repurposed this section to specifically load a txt file into the wavetable and activate wave generator

        # change directory to file location
        self.CNCstage = self.app.hardware.PI_xyz_stage.nanopositioner
        jname = os.path.basename(self.Job_Filename.val)
        jdir = os.path.dirname(self.Job_Filename.val)
        os.chdir(jdir)

        # read txt file into a numpy array
        # jobParams = np.loadtxt(jname, delimiter=',')
        jobParams = np.loadtxt(jname)
        xWave = np.squeeze(jobParams[:, 0])
        yWave = np.squeeze(jobParams[:, 1])
        zWave = np.squeeze(jobParams[:, 2] + self.CNCstage.z_comp_wave(self.delta_zx.val, self.delta_zy.val, xWave, yWave))
        shutter = np.squeeze(jobParams[:, 3])

        # save a tree structure for progress bar since E-727 in all its gloriousness did not include WGI? AHHHH!
        self.wavepoints = spatial.KDTree(jobParams[:, 0:3])

        # calculate table rate from velocity data
        # duration of a wave table point = servo cycle time * tablerate (default servo cycle time = 50us)
        # step_length = np.sqrt((xWave[3]-xWave[2])**2 + (yWave[3]-yWave[2])**2) # estimate step length by sampling the distance between arbitrary points
        # tablerate = step_length/(50E-6 * self.V_xy.val)

        # start wave generator
        self.CNCstage.loadWaveTable(xWave, yWave, zWave, shutter, tablerate = self.TableRate.val)




        print('Table Loaded. CNC is Good to GO!')
    
    
    def print_ImgFile(self):

        jnam = self.settings.Img_filename.val
        print(jnam)
    
    
    def browse_job_file(self):
        # Browse the file and save the path to self.Job_Filename
        
        job = Tk()
        job.withdraw()   # Hide the TK window
        job.fileName = filedialog.askopenfilename( filetypes = ( ("Target list", "*.txt"), ("All Files", "*.*") ) )
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
