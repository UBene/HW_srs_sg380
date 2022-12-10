import numpy as np
from ScopeFoundry import Measurement
import pyqtgraph as pg
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file

class OOSpecLive(Measurement):

    name = "oo_spec_live"
    
    def setup(self):
        
        self.display_update_period = 0.050 #seconds
        self.hw = self.app.hardware['ocean_optics_spec']
        
    def setup_figure(self):
               
        self.ui = load_qt_ui_file(sibling_path(__file__, 'oo_spec_live.ui'))
        
        
        ### Plot
        self.plot = pg.PlotWidget()
        self.ui.plot_groupBox.layout().addWidget(self.plot)

        self.plotline = self.plot.plot()
        
        #ax.set_xlabel("wavelengths (nm)")
        #ax.set_ylabel("Laser Spectrum (counts)")
        
        
        ### Controls
        self.hw.settings.int_time.connect_to_widget(self.ui.int_time_doubleSpinBox)
        self.hw.settings.connected.connect_to_widget(self.ui.hw_connect_checkBox)
        self.settings.activation.connect_to_widget(self.ui.run_checkBox)
        
    def run(self):
        self.oo_spec_dev = self.hw.oo_spectrometer
        while not self.interrupt_measurement_called:    
            self.oo_spec_dev.acquire_spectrum()
        
    
    def update_display(self):
        self.oo_spec_dev.spectrum[:10]=np.nan
        self.oo_spec_dev.spectrum[-10:]=np.nan
        self.plotline.setData(
                                   self.oo_spec_dev.wavelengths[10:-10],
                                   self.oo_spec_dev.spectrum[10:-10])
        #ax.relim()
        #ax.autoscale_view(scalex=True, scaley=True)
        #self.fig.canvas.draw()       
