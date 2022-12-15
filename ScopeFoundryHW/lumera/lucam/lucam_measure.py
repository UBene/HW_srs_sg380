'''
Created on Dec 9, 2022

@author: Benedikt Ursprung
'''
import time
import os

import pyqtgraph as pg
from qtpy import QtWidgets

from ScopeFoundry import Measurement, h5_io
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file


class LucamMeasure(Measurement):

    name = "lucam"

    def setup(self):

        self.hw = self.app.hardware['lucam']
        S = self.settings
        S.New('save_png', dtype=bool, initial=False, ro=False)
        S.New('save_tif', dtype=bool, initial=False, ro=False)
        S.New('save_ini', dtype=bool, initial=False, ro=False)
        S.New('save_h5', dtype=bool, initial=True, ro=False)
        S.New('mode', str, choices=('streaming', 'snapshot'), initial='streaming')

    def setup_figure(self):
        hw = self.hw
        HS = hw.settings
        S = self.settings

        ui_filename = sibling_path(__file__, "lucam.ui")
        self.ui = load_qt_ui_file(ui_filename)

        controls_layout = self.ui.controls.layout()
        ctr_widget = HS.New_UI(include=('connected', 'frame_rate', 'exposure'))
        controls_layout.addWidget(ctr_widget)

        # dims
        dim_lay = QtWidgets.QGridLayout()
        controls_layout.addLayout(dim_lay)
        dim_lay.addWidget(HS.New_UI(include=('width', 'height')))

        # Channels
        channel_layout = QtWidgets.QGridLayout()
        controls_layout.addLayout(channel_layout)
        channel_layout.addWidget(S.New_UI(include=('save_h5', 'mode')))
        channel_layout.addWidget(S.activation.new_pushButton())

        # imview
        self.imview = pg.ImageView(view=pg.PlotItem())
        self.ui.centralwidget.layout().addWidget(self.imview)

    def run(self):
        S = self.settings

        if S['mode'] == 'snapshot':
            self.img = self.hw.read_snapshot()
            self.save_image()
            return

        if S['mode'] == 'streaming':
            self.display_update_period = 0.01
            callback_id = self.hw.start_streaming(self.streaming_callback)
            while not self.interrupt_measurement_called:
                time.sleep(0.050)
            self.hw.stop_streaming(callback_id)

    def streaming_callback(self, context, frame_pointer, frame_size):
        self.img = self.hw.convert_to_rgb24(frame_pointer)

    def update_display(self):
        if not hasattr(self, "img"):
            return
        saturation = self.img[:, :, :3].max() / 255.0
        self.imview.view.setTitle(
            '{:2.0f}% max saturation'.format(saturation * 100.0))
        self.imview.setImage(self.img,
                             #axes={'y':0, 'x':1, 'c':2},
                             autoLevels=True)

    def save_image(self):
        print(self.name, 'save_image')
        S = self.settings
        t0 = time.time()
        fname = os.path.join(
            self.app.settings['save_dir'], "%i_%s" % (t0, self.name))

        if S['save_ini']:
            self.app.settings_save_ini(fname + ".ini")
        if S['save_png']:
            self.imview.export(fname + ".png")
        if S['save_tif']:
            self.imview.export(fname + ".tif")
        if S['save_h5']:
            with h5_io.h5_base_file(app=self.app, measurement=self) as H:
                M = h5_io.h5_create_measurement_group(
                    measurement=self, h5group=H)
                M.create_dataset('img', data=self.img, compression='gzip')
