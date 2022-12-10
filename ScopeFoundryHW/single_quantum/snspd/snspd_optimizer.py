'''
Created on May 7, 2019

@author: Benedikt Ursprung
'''
import pyqtgraph as pg
from qtpy import QtWidgets

import time
from ScopeFoundry import Measurement

from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file


class SNSPDOptimizerMeasure(Measurement):

    name = "snspd_channel_optimizer"

    def setup(self):

        self.hw = self.app.hardware['snspd']
        self.max_number_of_detectors = self.hw.max_number_of_detectors

        for i in range(self.max_number_of_detectors):
            self.settings.New(f'show_channel_{i}', bool, initial=True)

    def setup_figure(self):
        hw = self.hw
        HS = hw.settings

        ui_filename = sibling_path(__file__, "channel_optimizer.ui")
        self.ui = load_qt_ui_file(ui_filename)

        controls_layout = self.ui.controls.layout()
        basic_controls = HS.New_UI(
            include=('connected', 'measurement_periode', 'enable_detectors'))
        basic_controls.layout().addWidget(self.settings.activation.new_pushButton())
        controls_layout.addWidget(basic_controls)

        # Channels
        channel_layout = QtWidgets.QGridLayout()
        controls_layout.addLayout(channel_layout)
        S = self.settings
        colors = ["#FFDB6D", "#00AFBB", "#119922", "#0000FF", "#FF0000",
                  "#00FF00", "#FF00FF", "#FFFF00", "#00FFFF", "#0AB001"] * 2
        for i in range(self.max_number_of_detectors):
            qlabel = QtWidgets.QLabel(f'{i}')
            qlabel.setStyleSheet(f"""QLabel{{background:{colors[i]}}}""")
            channel_layout.addWidget(qlabel, i, 0)
            channel_layout.addWidget(
                S.get_lq(f'show_channel_{i}').new_default_widget(), i, 1)
            channel_layout.addWidget(
                HS.get_lq(f'bias_current_{i}').new_default_widget(), i, 2)
            channel_layout.addWidget(
                HS.get_lq(f'trigger_level_{i}').new_default_widget(), i, 3)

        # Buttons
        btn = QtWidgets.QPushButton('read_bias_currents')
        btn.clicked.connect(hw.read_bias_currents)
        channel_layout.addWidget(btn, i + 1, 2)

        btn = QtWidgets.QPushButton('auto_bias_exposure')
        btn.clicked.connect(hw.auto_bias_exposure)
        channel_layout.addWidget(btn, i + 1, 2)

        btn = QtWidgets.QPushButton('read_trigger_levels')
        btn.clicked.connect(hw.read_trigger_levels)
        channel_layout.addWidget(btn, i + 1, 3)

        # Plot
        self.graph_layout = pg.GraphicsLayoutWidget()
        self.ui.centralwidget.layout().addWidget(self.graph_layout)
        self.plot = self.graph_layout.addPlot(title="Channel Optimizer")

        self.plotlines = {}
        for i in range(self.max_number_of_detectors):
            self.plotlines.update({f'line_{i}': self.plot.plot(pen=colors[i])})

    def run(self):

        while not self.interrupt_measurement_called:
            time.sleep(0.050)

    def update_display(self):
        t, rates = self.hw.buffered_count_rates()
        for i in range(self.max_number_of_detectors):
            line = self.plotlines[f'line_{i}']
            line.setData(t, rates[:, i])
            line.setVisible(self.settings[f'show_channel_{i}'])
