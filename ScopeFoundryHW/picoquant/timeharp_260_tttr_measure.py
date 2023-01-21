'''
Created on Jan 14, 2023

@author: Benedikt Ursprung
'''
from ScopeFoundry import Measurement, h5_io
import h5py
import numpy as np
import pyqtgraph as pg
import time
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from qtpy import QtWidgets


class Timeharp260TTTRMeasure(Measurement):

    name = "timeharp_260_tttr"


    def setup(self):
        
        self.hw = self.app.hardware['timeharp_260']
        
        

    def setup_figure(self):
        
        self.ui = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.ui)
        layout.addWidget(self.hw.settings.New_UI(include=('Mode', 'connected', 'Tacq', 'ChanEnable0', 'ChanEnable1', 'CFDLevelSync','is_fifo_full')))
        layout.addWidget(self.settings.activation.new_pushButton())
        progress_bar = QtWidgets.QProgressBar()
        layout.addWidget(progress_bar)
        self.progress.connect_to_widget(progress_bar)
       
        
    def run(self):
        S = self.settings
        hw = self.hw
        
        HWS = hw.settings
        
        t_start = time.time()
        t_acq = HWS['Tacq']
                
        N = 0
        print(t_acq)

        h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
        h5_meas_group = h5_io.h5_create_measurement_group(self, h5_file)
        dt = h5py.vlen_dtype(np.dtype('uint32'))
                
        estimated_N_iterations = t_acq // 0.001 + 1
        dset = h5_meas_group.create_dataset('event_times', (estimated_N_iterations,), dtype=dt, 
                                            #compression="gzip"
                                            )

        counter = 0

        hw.start_tttr()
        
        data = []
        
        while not self.interrupt_measurement_called: 
            t_progress = time.time() - t_start
            self.set_progress(t_progress/t_acq * 100)
            
            chunk = hw.read_fifo()
            data.append(chunk)
            #dset[counter] = chunk
            #h5_file.flush()
            counter += 1
            N += len(chunk)
            # if len(chunk) == 0:
            #     print(N, t_progress)
            print(N, len(chunk))
            #
            #print(chunk)
            
            if hw.settings.CTCStatus.read_from_hardware():
                break
                
            if hw.settings.is_fifo_full.read_from_hardware():
                print('FIFO Buffer full, abort')
                # break
                
        print(N, len(chunk))
            
        hw.stop_tttr()
        
        h5_file.close()