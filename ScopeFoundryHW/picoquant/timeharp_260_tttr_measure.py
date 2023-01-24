'''
Created on Jan 14, 2023

@author: Benedikt Ursprung
'''
from ScopeFoundry import Measurement, h5_io
import h5py
import numpy as np
import time
from qtpy import QtWidgets


class Timeharp260TTTRMeasure(Measurement):

    name = "timeharp_260_tttr"

    def setup(self):

        self.hw = self.app.hardware['timeharp_260']
        self.settings.New('num_acquired', int, initial=0)

    def setup_figure(self):

        self.ui = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.ui)
        layout.addWidget(self.hw.settings.New_UI(include=(
            'Mode',
            'connected',
            'Tacq',
            'ChanEnable0',
            'ChanEnable1',
            'CFDLevelSync',
            'is_fifo_full')))
        layout.addWidget(self.settings.activation.new_pushButton())
        layout.addWidget(self.settings.New_UI(include=(
            'num_acquired',)))
        progress_bar = QtWidgets.QProgressBar()
        layout.addWidget(progress_bar)
        self.progress.connect_to_widget(progress_bar)

    def run(self):
        S = self.settings
        HWS = self.hw.settings

        t_acq = HWS['Tacq']
        estimated_N_iterations = t_acq // 0.001 + 1
        h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
        h5_meas_group = h5_io.h5_create_measurement_group(self, h5_file)
        dtype = h5py.vlen_dtype(np.dtype('uint32'))
        dset = h5_meas_group.create_dataset(
            'event_times',
            (estimated_N_iterations,),
            dtype=dtype
        )
        
        self.num_acquired = 0
        self.ii = 0
        self.data = []
        self.hw.start_tttr()

        while not self.interrupt_measurement_called:
            self.set_progress(HWS['ElapsedMeasTime'] / t_acq * 100)

            chunk = self.hw.read_tttr_data()
            self.data.append(chunk)
            dset[self.ii] = chunk
            # h5_file.flush()
            self.ii += 1
            self.num_acquired += len(chunk)

            if HWS.CTCStatus.read_from_hardware():
                break

            if HWS.is_fifo_full.read_from_hardware():
                pass
                # print('FIFO Buffer full, abort')
                # break
        print('number of data points acquired:', self.num_acquired)

        self.hw.stop_tttr()
        h5_file.flush()
        h5_file.close()

    def update_figure(self):
        S = self.settings
        S['num_acquired'] = self.num_acquired
