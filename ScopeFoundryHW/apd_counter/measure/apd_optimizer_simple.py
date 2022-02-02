from ScopeFoundry import Measurement
import numpy as np
import pyqtgraph as pg
import time
import os

class APDOptimizerMeasure(Measurement):

    name = "apd_optimizer"



    def setup(self):
        self.ui_filename = os.path.join(os.path.dirname(__file__), "apd_optimizer.ui")
        self.load_ui(self.ui_filename)
            
        self.display_update_period = 0.001 #seconds

        # create data array
        self.OPTIMIZE_HISTORY_LEN = 500
        self.optimize_history = np.zeros(self.OPTIMIZE_HISTORY_LEN, dtype=np.float)        
        self.optimize_ii = 0
        
        # Connect events
        self.app.hardware['apd_counter'].int_time.connect_bidir_to_widget(self.ui.int_time_doubleSpinBox)
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)

    def setup_figure(self):
        self.optimize_ii = 0

        # add a pyqtgraph GraphicsLayoutWidget to the measurement ui window
        if hasattr(self, 'graph_layout'):
            self.graph_layout.deleteLater() # see http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            del self.graph_layout
        self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)

        ## Add plot and plot items
        self.opt_plot = self.graph_layout.addPlot(title="APD Optimizer")
        self.optimize_plot_line = self.opt_plot.plot([1,3,2,4,3,5])
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.opt_plot.addItem(self.vLine, ignoreBounds=True)

    def run(self):
        self.apd_counter_hc = self.app.hardware['apd_counter']
        self.apd_count_rate = self.apd_counter_hc.apd_count_rate
        self.ni_counter = self.apd_counter_hc.ni_counter
        # data arrays
        self.full_optimize_history = []
        self.full_optimize_history_time = []
        self.t0 = time.time()

        #self.ni_counter.start()

        while not self.interrupt_measurement_called:
            self.optimize_ii += 1
            self.optimize_ii %= self.OPTIMIZE_HISTORY_LEN
            
            progress_pct = (100. * self.optimize_ii/self.OPTIMIZE_HISTORY_LEN)
            self.set_progress(progress_pct)

            self.apd_count_rate.read_from_hardware()
            self.optimize_history[self.optimize_ii] = self.apd_count_rate.val
            #time.sleep(self.apd_counter_hc.int_time.val)
            #count_rate = self.ni_counter.read_average_freq_in_buffer()
            #self.optimize_history[self.optimize_ii] = count_rate
            
            self.full_optimize_history.append(self.apd_count_rate.val  )
            self.full_optimize_history_time.append(time.time() - self.t0)

    def pre_run(self):
        return
    
    def post_run(self):
        self.ni_counter.stop()

    def update_display(self):
        ii = self.optimize_ii
        #print "display update", ii, self.optimize_history[ii]
        self.vLine.setPos(ii)
        self.optimize_plot_line.setData(self.optimize_history)
        