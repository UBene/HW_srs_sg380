'''
Created on Jul 25, 2021

@author: Benedikt Ursprung
'''
from ScopeFoundry.data_browser import DataBrowserView
import pyqtgraph as pg
import pyqtgraph.dockarea as dockarea
import h5py
import numpy as np


class LakeshoreH5View(DataBrowserView):
    
    name = 'lakeshore_measure_h5'
    
    def is_file_supported(self, fname):
        for measure_type in ['lakeshore_measure']:
            if measure_type + '.h5' in fname:
                self.measure_type = measure_type
                return True            
        return False
            
    def setup(self):
        self.ui = self.dockarea = dockarea.DockArea()

        self.layout = pg.GraphicsLayoutWidget()
        self.dock = self.dockarea.addDock(name=self.name, widget=self.layout)

        self.plot = self.layout.addPlot()
        xaxis = pg.DateAxisItem(orientation="bottom")
        self.plot.setAxisItems({"bottom":xaxis})
        self.plot.setLabel('left', text='T', units='K')
        
        self.optimize_plot_line_A = self.plot.plot([3, 4, 2], name='T_A', pen={'color': "r", 'width': 2}) 
        self.optimize_plot_line_B = self.plot.plot([1, 2, 0], name='T_B', pen={'color': "b", 'width': 2})
        
        
    def on_change_data_filename(self, fname=None):
        if hasattr(self, 'h5_file'):
            try:
                self.h5_file.close()
            except:
                pass  # Was already closed
            finally:
                del self.h5_file
        
        self.h5_file = h5py.File(fname, 'r')
        
        M = self.h5_file['measurement/' + self.measure_type] 
        T_A = M['T_A'][:]
        T_B = M['T_B'][:]
        mA = np.mean(T_A)
        sA = np.std(T_A)
        mB = np.mean(T_B)
        sB = np.std(T_B)
                
        H = self.h5_file['hardware/lakeshore331'] 
        T = H['settings'].attrs['setpoint_T']
        control_input = H['settings'].attrs['control_input']
        #print(control_input.keys())
        
        title = '<br>'.join([f'std,mean T_A: {sA:0.3f},{mA:0.3f}K',
                              f'std,mean T_B: {sB:0.3f},{mB:0.3f}K',
                              f'setpoint (T_{control_input})={T}K'])
        self.plot.setTitle(title)
        
        
        print(M['time_array'][:].shape, T_A.shape)
        
        self.optimize_plot_line_A.setData(M['time_array'][:len(T_A)], T_A) 
        self.optimize_plot_line_B.setData(M['time_array'][:len(T_B)], T_B) 

        #self.regA.setRegion((mA - 0.5 * sA, mA + 0.5 * sA))
        #self.regB.setRegion((mB - 0.5 * sB, mB + 0.5 * sB))
        
        
        if hasattr(self, 'events'):
            for line, text, time in self.events:
                self.plot.removeItem(line)  
        
        
        
        self.events = []
        if 'time_events' in M:
            print(M['time_events'])

            for text, time in M['time_events'].attrs.items():
                line = pg.InfiniteLine(
                angle=90,
                movable=False,
                pen=(200, 200, 200),
                label=f"{text}: {time} sec",
                labelOpts={
                    "color": (200, 200, 200),
                    "movable": True,
                    "position": 0.4,
                    "fill": (200, 200, 200, 60),
                    'rotateAxis': [1, 0],
                    },
                )
                line.setPos(time)
                self.plot.addItem(line)
                self.events.append([line, text, time])
        
        
        self.plot.enableAutoRange()
        self.h5_file.close()
