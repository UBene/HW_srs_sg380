from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path
import pyqtgraph as pg
import time
import numpy as np

class AdcOptimizerMeasure(Measurement):

    name = 'dac_optimizer'
    ui_filename = sibling_path(__file__, "adc_optimizer.ui")

    def setup(self):
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)

        # graph_layout
        self.graph_layout = pg.GraphicsLayoutWidget()
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)

        # history plot
        self.plot = self.graph_layout.addPlot(title="ADC Optimizer")
        self.optimize_plot_line = self.plot.plot([0])        


    def run(self):
        adc = self.app.hardware['ni_adc']

        # create data array
        self.OPTIMIZE_HISTORY_LEN = 500
        self.optimize_history = np.zeros(self.OPTIMIZE_HISTORY_LEN, dtype=np.float)        
        self.optimize_ii = 0

        while not self.interrupt_measurement_called:
            time.sleep(0.1)
            self.optimize_history[self.optimize_ii] = adc.settings.adc_val.read_from_hardware()
            self.optimize_ii += 1
            self.optimize_ii %= self.OPTIMIZE_HISTORY_LEN


    def update_display(self):
        self.optimize_plot_line.setData(self.optimize_history)