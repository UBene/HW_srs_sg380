'''
Created on May 7, 2019

@author: Benedikt Ursprung
'''
from ScopeFoundry import Measurement
import numpy as np
import pyqtgraph as pg
import time
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from qtpy import QtWidgets


class HydraHarpOptimizerMeasure(Measurement):

    name = "hydraharp_channel_optimizer"
    
    hardware_requirements = ['hydraharp']
    
       
    def setup(self):
        
        self.n_channels = 2  # Update for additional channels 
        
        #Optimizer Measurement
        self.rates = ['SyncRate']
        for i in range(self.n_channels): self.rates.append('CountRate{}'.format(i))
        for rate in self.rates:
            self.settings.New('{}_visible'.format(rate), dtype=bool, initial=True)        

        self.settings.New('history_len', dtype=int, initial=300)        
        self.settings.New('avg_len', dtype=int, initial=40)        

        self.on_new_history_len()
        self.settings.history_len.add_listener(self.on_new_history_len)
        
        self.hydraharp_hw = self.app.hardware['hydraharp']


        
    def setup_figure(self):    
        hh_hw = self.hydraharp_hw
        HS = hh_hw.settings
    
        ui_filename = sibling_path(__file__, "hydraharp_channel_optimizer.ui")
        self.ui = load_qt_ui_file(ui_filename)
        
        
        #Connect hardware settings       
        spinboxes = ['DeviceIndex', 'HistogramBins', 'Tacq', 'Resolution',
                     'StopCount',
                     'SyncOffset', 'CFDLevelSync', 'CFDZeroCrossSync',
                     'SyncRate', 'SyncPeriod',]    
        for spinbox in spinboxes:
            widget = getattr(self.ui, '{}_doubleSpinBox'.format(spinbox))
            getattr(HS, spinbox).connect_to_widget(widget)            
        HS.SyncDivider.connect_to_widget(self.ui.SyncDivider_comboBox)        
        HS.connected.connect_to_widget(self.ui.connected_checkBox)    
        HS.Mode.connect_to_widget(self.ui.Mode_comboBox)
        HS.RefSource.connect_to_widget(self.ui.RefSource_comboBox)
        HS.StopOnOverflow.connect_to_widget(self.ui.StopOnOverflow_checkBox)
        HS.Binning.connect_to_widget(self.ui.Binning_comboBox)


        #settings for each channel:
        for i in range(self.n_channels):
            if i%2==0:
                q = int(i/2)
                self.add_timing_module(channels=np.arange(q,q+2))



        #Channel optimizer
        self.settings.activation.connect_to_widget(self.ui.run_checkBox)
        self.settings.SyncRate_visible.connect_to_widget(self.ui.SyncRate_visible_checkBox)
        self.settings.history_len.connect_to_widget(self.ui.history_len_doubleSpinBox)
        self.settings.avg_len.connect_to_widget(self.ui.avg_len_doubleSpinBox)        


        for i in range(self.n_channels):
            checkBox = QtWidgets.QCheckBox('show CountRate{}'.format(i)) 
            if i%2 == 0:
                VLayout = QtWidgets.QVBoxLayout()
                self.ui.optimizer_layout.addLayout(VLayout)
            VLayout.addWidget(checkBox)
            self.settings.get_lq('CountRate{}_visible'.format(i)).connect_to_widget(checkBox)

        
        self.graph_layout=pg.GraphicsLayoutWidget()
        self.ui.channel_optimizer_GroupBox.layout().addWidget(self.graph_layout)
        self.plot = self.graph_layout.addPlot(title="Hydraharp Channel Optimizer")
        
        self.plotlines = {}
        self.avglines = {}
        colors = ['y','r','g','b']
        for i,rate in enumerate(self.rates):
            self.plotlines.update({rate:self.plot.plot(pen=colors[i])})
            avg_line = pg.InfiniteLine(angle=0, movable=False, pen=colors[i%len(colors)])
            self.plot.addItem(avg_line)
            self.avglines.update({rate:avg_line})


    def add_timing_module(self, channels=[0,1]):
        module_layout = QtWidgets.QVBoxLayout()
        self.ui.modules_layout.addLayout(module_layout)
        for i in channels:
            include = ['{}{}'.format(x,i) for x in ['ChanEnable','CFDLevel',
                                                    'CFDZeroCross','ChanOffset',
                                                    'CountRate']]
            module_layout.addWidget(self.hydraharp_hw.settings.New_UI(include = include))
            

    def run(self):
        hh_hw = self.hydraharp_hw

        while not self.interrupt_measurement_called:
            self.optimize_ii += 1
            self.optimize_ii %= self.OPTIMIZE_HISTORY_LEN

            self.optimize_history[self.optimize_ii,:] = [hh_hw.settings[rate] for rate in self.rates]
            time.sleep(0.08) 

            
    def on_new_history_len(self):
        N = self.settings['history_len']
        self.optimize_ii = 0
        self.optimize_history = np.zeros( (N, self.n_channels+1), dtype=float)
        self.optimize_history_avg = np.zeros_like(self.optimize_history)
        self.OPTIMIZE_HISTORY_LEN = N

        
    def update_display(self):
        if self.optimize_ii == 0:
            return
        
        ii = self.optimize_ii                    
        title = ''
        
        N_AVG = min(self.settings['avg_len'],self.settings['history_len']-1)
        q = ii - N_AVG
        if q>=0:
            avg_val = self.optimize_history[q:ii,:].mean(axis=0)
        else:
            avg_val = self.optimize_history[:ii].mean(axis=0)*1.0*ii/N_AVG + self.optimize_history[q:].mean(axis=0)*(-q/N_AVG)
        
        for i,rate in enumerate(self.rates):
            self.plotlines[rate].setVisible(self.settings['{}_visible'.format(rate)])
            self.avglines[rate].setVisible(self.settings['{}_visible'.format(rate)])
            if self.settings['{}_visible'.format(rate)]:
                title += '<b>\u03BC</b><sub>{}</sub> = {:3.0f} <br />'.format(rate,avg_val[i])
                self.plotlines[rate].setData(y = self.optimize_history[:,i])
                self.avglines[rate].setPos((0,avg_val[i]))

        self.plot.setTitle(title)
             
        
