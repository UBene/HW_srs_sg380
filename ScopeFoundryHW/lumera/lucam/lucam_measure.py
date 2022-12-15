'''
Created on Dec 9, 2022

@author: Benedikt Ursprung
'''
from datetime import datetime
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
        s = S.New('scale', float, initial=1.0, unit='um/px')
        s.add_listener(self.update_display)

        self.data = {'image': [[1, 2, 3] * 4] * 3}

    def setup_figure(self):
        hw = self.hw
        HS = hw.settings
        S = self.settings

        ui_filename = sibling_path(__file__, "lucam.ui")
        self.ui = load_qt_ui_file(ui_filename)

        controls_layout = self.ui.controls.layout()
        ctr_widget = HS.New_UI(include=('connected', 'frame_rate', 'exposure'))
        controls_layout.addWidget(ctr_widget)

        # dimensions
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

        self.hw.write_format()
        S = self.settings

        if S['mode'] == 'snapshot':
            self.data['image'] = self.hw.read_snapshot()
            self.save_image()
            return

        if S['mode'] == 'streaming':
            self.display_update_period = 0.01
            callback_id = self.hw.start_streaming(self.streaming_callback)
            while not self.interrupt_measurement_called:
                time.sleep(0.050)
            self.hw.stop_streaming(callback_id)

    def streaming_callback(self, context, frame_pointer, frame_size):
        self.data['image'] = self.hw.convert_to_rgb24(frame_pointer)

    def update_display(self):
        img = self.data['image']
        saturation = img[:, :, :3].max() / 255.0
        self.imview.view.setTitle(
            '{:2.0f}% max saturation'.format(saturation * 100.0))
        self.imview.setImage(img,
                             #axes={'y':0, 'x':1, 'c':2},
                             autoLevels=True)
        self.imview.getImageItem().setScale(self.settings['scale'])

    def save_image(self):
        self.update_imshow_extent()
        print(self.name, 'save_image')
        S = self.settings
        t0 = time.time()
        f = self.app.settings['data_fname_format'].format(
            app=self.app,
            measurement=self,
            timestamp=datetime.fromtimestamp(t0),
            ext='h5')
        fname = os.path.join(self.app.settings['save_dir'], f)

        if S['save_ini']:
            self.app.settings_save_ini(fname.replace('h5', 'ini'))
        if S['save_png']:
            self.imview.export(fname.replace('h5', 'png'))
        if S['save_tif']:
            self.imview.export(fname.replace('h5', 'tif'))
        if S['save_h5']:
            self.save_h5()

    def save_h5(self):
        with h5_io.h5_base_file(app=self.app, measurement=self) as H:
            M = h5_io.h5_create_measurement_group(measurement=self, h5group=H)
            for name, data in self.data.items():
                M.create_dataset(name, data=data, compression='gzip')

    def update_imshow_extent(self):
        Nx, Ny = self.data['image'].shape[:2]
        s = self.settings['scale']
        self.data['imshow_extent'] = (-0.5 * s,
                                      s * (Nx + 0.5), -0.5 * s, s * (Ny + 0.5))
