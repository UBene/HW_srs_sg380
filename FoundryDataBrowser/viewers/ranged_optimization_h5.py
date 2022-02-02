'''
Created on Jul 25, 2021

@author: Benedikt Ursprung
'''
from ScopeFoundry.data_browser import DataBrowserView
import pyqtgraph as pg
import pyqtgraph.dockarea as dockarea
import h5py


class RangedOptimizationH5View(DataBrowserView):
    
    name = 'ranged_optimization_h5'
    
    def is_file_supported(self, fname):
        # ADD other ranged optimization here
        for measure_type in ['auto_focus']:
            if measure_type + '.h5' in fname:
                self.measure_type = measure_type
                return True            
        return False
            
    def setup(self):
        self.ui = self.dockarea = dockarea.DockArea()

        self.layout = pg.GraphicsLayoutWidget()
        self.dock = self.dockarea.addDock(name='ranged_optimization', widget=self.layout)

        self.plot = self.layout.addPlot()
        self.plot.setLabel('bottom', 'f(z)')
        self.plot.setLabel('left', 'z') 
        self.line_coarse = self.plot.plot(y=[0, 2, 1, 3, 2])
        self.line_fine = self.plot.plot(y=[0, 2, 1, 3, 2], pen="r")
        
        # indicator lines
        self.line_z_original = pg.InfiniteLine(
            angle=0,
            movable=False,
            pen="b",
            label="original position: {value:0.6f}",
            labelOpts={
                "color": "b",
                "movable": True,
                "position": 0.15,
                "fill": (200, 200, 200, 200),
            },
        )
        self.line_z0_coarse = pg.InfiniteLine(
            angle=0,
            movable=False,
            pen=(200, 200, 200),
            label="coarse optimized: {value:0.6f}",
            labelOpts={
                "color": (200, 200, 200),
                "movable": True,
                "position": 0.30,
                "fill": (200, 200, 200, 60),
            },
        )
        self.line_z0_fine = pg.InfiniteLine(
            angle=0,
            movable=False,
            pen="r",
            label="fine optimized: {value:0.6f}",
            labelOpts={
                "color": "r",
                "movable": True,
                "position": 0.45,
                "fill": (200, 200, 200, 80),
            },
        )
        self.plot.addItem(self.line_z_original, ignoreBounds=True)
        self.plot.addItem(self.line_z0_coarse, ignoreBounds=True)
        self.plot.addItem(self.line_z0_fine, ignoreBounds=True)
        
    def on_change_data_filename(self, fname=None):
        if hasattr(self, 'h5_file'):
            try:
                self.h5_file.close()
            except:
                pass  # Was already closed
            finally:
                del self.h5_file
        
        self.h5_file = h5py.File(fname, 'r')
        H = self.h5_file['measurement/' + self.measure_type] 
        
        self.plot.setTitle(self.measure_type)
        self.line_coarse.setData(H['f_coarse'][:], H['z_coarse'][:]) 
        self.line_z0_fine.setPos(H['z0_coarse'].value)
        self.line_z_original.setPos(H['z_original'].value)
        
        has_fine = bool(H['settings'].attrs['use_fine_optimization'])
        self.line_z0_fine.setVisible(has_fine)
        self.line_fine.setVisible(has_fine)
        if has_fine:
            self.line_fine.setData(H['f_fine'][:], H['z_fine'][:])
            self.line_z0_fine.setPos(H['z0_fine'].value)
            
        self.h5_file.close()
        
