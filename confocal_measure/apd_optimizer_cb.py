from ScopeFoundry import Measurement
import pyqtgraph as pg
import time
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path, replace_widget_in_layout


class APDOptimizerCBMeasurement(Measurement):

    name = "apd_optimizer"
        
    def setup(self):
        
        self.display_update_period = 0.1  # seconds

    def setup_figure(self):

        self.ui = load_qt_ui_file(sibling_path(__file__, "apd_optimizer.ui"))

        self.settings.activation.connect_to_pushButton(self.ui.start_pushButton)
        self.app.hardware['apd_counter'].settings.int_time.connect_to_widget(
            self.ui.int_time_doubleSpinBox)
        self.ui.count_rate_PGSpinBox = replace_widget_in_layout(self.ui.count_rate_doubleSpinBox,
                                                                       pg.widgets.SpinBox.SpinBox())
        
        
        self.app.hardware['apd_counter'].settings.count_rate.connect_to_widget(
            self.ui.count_rate_PGSpinBox
            )
        
        # add a pyqtgraph GraphicsLayoutWidget to the measurement ui window
        if hasattr(self, 'graph_layout'):
            self.graph_layout.deleteLater()  # see http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            del self.graph_layout
        self.graph_layout = pg.GraphicsLayoutWidget(border=(100, 100, 100))
        self.ui.plot_widget.layout().addWidget(self.graph_layout)

        # # Add plot and plot items
        self.opt_plot = self.graph_layout.addPlot(title="APD Optimizer")
        self.optimize_plot_line = self.opt_plot.plot([1, 3, 2, 4, 3, 5])
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.opt_plot.addItem(self.vLine, ignoreBounds=True)
        self.opt_plot.setLogMode(False, True)
        
        self.data = {'count_rate':0.1}
        
    def run(self):
        apd_counter = self.app.hardware['apd_counter']
        if not apd_counter.settings['connected']:
            apd_counter.settings['connected'] = True
            time.sleep(0.1)
        
        self.display_update_period = self.app.hardware['apd_counter'].settings['int_time']
        while not self.interrupt_measurement_called:
            time.sleep(0.1)
        self.data['count_rate'] = self.app.hardware['apd_counter'].settings['count_rate'] 
        
    def update_display(self):
        apd_counter = self.app.hardware['apd_counter']
        self.vLine.setPos(apd_counter.mean_buffer_i)
        X = apd_counter.mean_buffer
        self.optimize_plot_line.setData(X)
        self.opt_plot.setLogMode(False, True)
