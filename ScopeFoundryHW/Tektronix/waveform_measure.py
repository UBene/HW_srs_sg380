'''
Created on Jan 15, 2023

@author: Mark Ziffer
'''
from ScopeFoundry import Measurement
import numpy as np
import pyqtgraph as pg
from qtpy import QtWidgets
import time
from ScopeFoundry import h5_io
from struct import unpack


class TektronixWaveform(Measurement):

    name = "tektronix_waveform"

    def setup(self):

        self.hw = self.app.hardware['tektronix_scope']
        S = self.settings
        S.New('chan', int, initial=1)
        S.New('mode', str, choices=('single', 'stream'))
        S.New('data_width', int, initial=1)

        t = np.arange(100) / 16
        self.data = {
            "times": t,
            "volts": [np.sin(t), np.sin(t - 1)],
        }

    def setup_figure(self):
        self.ui = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.ui)

        ctr_layout = QtWidgets.QHBoxLayout()
        ctr_layout.addWidget(self.settings.mode.new_default_widget())
        ctr_layout.addWidget(self.settings.activation.new_pushButton())
        layout.addLayout(ctr_layout)

        graph_layout = pg.GraphicsLayoutWidget(border=(0, 0, 0))
        self.plot = graph_layout.addPlot(title=self.name)
        self.plot_lines = {'waveform': self.plot.plot()}
        self.plot.setLabel('bottom', 'time', units='s')
        self.plot.setLabel('left', 'volt', units='V')
        layout.addWidget(graph_layout)

    def update_display(self):
        t = self.data["times"]
        volts = self.data["volts"]
        self.plot_lines['waveform'].setData(t, volts[-1])

    def run(self):
        S = self.settings

        if S['mode'] == 'stream':
            while not self.interrupt_measurement_called:
                times, volts = self.read_waveform()
                self.data['times'] = times
                self.data['volts'] = volts
                time.sleep(0.05)

        elif S['mode'] == 'stream':
            times, volts = self.read_waveform()
            self.data['times'] = times
            self.data['volts'] = volts
            self.save_h5()

    def read_waveform(self, chan=None):
        if chan is None:
            chan = self.settings['chan']

        self.hw.write(f'DATA:SOU CH{chan}')
        width = self.settings['data_width']
        self.hw.write(f'DATA:WIDTH {width}')
        self.hw.write('DATA:ENC RPB')

        ymult = float(self.hw.ask('WFMPRE:YMULT?'))
        yzero = float(self.hw.ask('WFMPRE:YZERO?'))
        yoff = float(self.hw.ask('WFMPRE:YOFF?'))
        xincr = float(self.hw.ask('WFMPRE:XINCR?'))

        self.write('CURVE?')
        data = self.dev.read_raw()
        headerlen = 2 + int(data[1])
        header = data[:headerlen]
        ADC_wave = data[headerlen:-1]

        ADC_wave = np.array(unpack('%sB' % len(ADC_wave), ADC_wave))

        volts = (ADC_wave - yoff) * ymult + yzero
        times = np.arange(0, xincr * len(volts), xincr)
        return times, volts

    def save_h5(self):
        h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
        h5_meas_group = h5_io.h5_create_measurement_group(self, h5_file)
        for k, v in self.data.items():
            h5_meas_group[k] = v
        h5_file.close()
