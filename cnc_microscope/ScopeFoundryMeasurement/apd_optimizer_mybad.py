from ScopeFoundry import Measurement
import numpy as np
import pyqtgraph as pg
import time
from ScopeFoundry.helper_funcs import sibling_path, replace_widget_in_layout
#from nltk.app.nemo_app import initialFind

class APDOptimizerMeasure(Measurement):

    name = "apd_optimizer"

    #ui_filename = "ScopeFoundryMeasurement/apd_optimizer.ui"
    
    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "apd_optimizer.ui")
        super(APDOptimizerMeasure, self).__init__(app) 

    def setup(self):        
        self.display_update_period = 0.1 #seconds
        
        # logged quantities
        #self.save_data = self.add_logged_quantity(name='save_data', dtype=bool, initial=False, ro=False)
        self.save_data = self.settings.New(name='save_data', dtype=bool, initial=False, ro=False)
        self.settings.New(name='update_period', dtype=float, si=True, initial=0.1, unit='s')

        # create data array
        self.OPTIMIZE_HISTORY_LEN = 500
        self.optimize_history = np.zeros(self.OPTIMIZE_HISTORY_LEN, dtype=np.float)        
        self.optimize_ii = 0
        
        # hardware
        self.apd = self.app.hardware.apd_counter

        #connect events
        try:
            self.gui.ui.apd_optimize_startstop_checkBox.stateChanged.connect(self.start_stop)
            self.measurement_state_changed[bool].connect(self.gui.ui.apd_optimize_startstop_checkBox.setChecked)
        except Exception as err:
            print ("APDOptimizerMeasurement: could not connect to custom main GUI", err)

        self.gui.hardware_components['apd_counter'].int_time.connect_bidir_to_widget(self.ui.int_time_doubleSpinBox)

        self.save_data.connect_bidir_to_widget(self.ui.save_data_checkBox)

        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        
        
        
        #connect events
        #self.ui.start_pushButton.clicked.connect(self.start)
        #self.ui.interrupt_pushButton.clicked.connect(self.interrupt)

        #self.save_data.connect_bidir_to_widget(self.ui.save_data_checkBox)
        
        #self.ui.power_readout_PGSpinBox = replace_widget_in_layout(self.ui.power_readout_doubleSpinBox,
        #                                                               pg.widgets.SpinBox.SpinBox())
        #self.powermeter.settings.power.connect_bidir_to_widget(self.ui.power_readout_PGSpinBox)
        
        #self.powermeter.settings.power.connect_bidir_to_widget(self.ui.power_readout_label)
        #self.powermeter.settings.wavelength.connect_bidir_to_widget(self.ui.wavelength_doubleSpinBox)

    def setup_figure(self):
        self.optimize_ii = 0

        # ui window
        if hasattr(self, 'graph_layout'):
            self.graph_layout.deleteLater() # see http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            del self.graph_layout
        self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)


        #self.graph_layout.addLabel('Long Vertical Label', angle=-90, rowspan=3)
        
        ## Add 3 plots into the first row (automatic position)
        self.p1 = self.graph_layout.addPlot(title="APD Optimizer")

        self.optimize_plot_line = self.p1.plot([1,3,2,4,3,5])

    def _run(self):
        self.display_update_period = 0.001 #seconds

        self.apd_counter_hc = self.gui.hardware_components['apd_counter']
        self.apd_count_rate = self.apd_counter_hc.apd_count_rate


        if self.save_data.val:
            self.full_optimize_history = []
            self.full_optimize_history_time = []
            self.t0 = time.time()

        while not self.interrupt_measurement_called:
            self.optimize_ii += 1
            self.optimize_ii %= self.OPTIMIZE_HISTORY_LEN

            self.apd_count_rate.read_from_hardware()            
            self.optimize_history[self.optimize_ii] = self.apd_count_rate.val    
            
            if self.save_data.val:
                self.full_optimize_history.append(self.apd_count_rate.val  )
                self.full_optimize_history_time.append(time.time() - self.t0)
            # test code
            #time.sleep(0.001)
            #self.optimize_history[self.optimize_ii] = random.random()    
        
        #save data afterwards
        if self.save_data.val:
            #save  data file
            save_dict = {
                     'optimize_history': self.full_optimize_history,
                     'optimize_history_time': self.full_optimize_history_time,
                        }               
                    
            for lqname,lq in self.gui.logged_quantities.items():
                save_dict[lqname] = lq.val
            
            for hc in self.gui.hardware_components.values():
                for lqname,lq in hc.logged_quantities.items():
                    save_dict[hc.name + "_" + lqname] = lq.val
            
            for lqname,lq in self.logged_quantities.items():
                save_dict[self.name +"_"+ lqname] = lq.val
    
            self.fname = "%i_%s.npz" % (time.time(), self.name)
            np.savez_compressed(self.fname, **save_dict)
            print (self.name, "saved:", self.fname)
            
            
        
        #is this right place to put this?
        self.measurement_state_changed.emit(False)
        if not self.interrupt_measurement_called:
            self.measurement_sucessfully_completed.emit()
        else:
            self.measurement_interrupted.emit()
    

    def update_display(self):        
        ii = self.optimize_ii
        #print "display update", ii, self.optimize_history[ii]

        # pyqtgraph
        #self.p1.plot(self.optimize_history)
        self.optimize_plot_line.setData(self.optimize_history)
        self.gui.app.processEvents()

        
