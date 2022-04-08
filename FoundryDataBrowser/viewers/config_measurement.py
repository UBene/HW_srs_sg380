from ScopeFoundry.data_browser import DataBrowserView
import numpy as np
import h5py
import pyqtgraph as pg
from pyqtgraph.dockarea.DockArea import DockArea
from qtpy.QtWidgets import QVBoxLayout, QWidget


class ConfigMeasurement(DataBrowserView):
    
    name = 'config_measurement'
    
    def setup(self):
        
        self.ui = DockArea()        
        
        widget = QWidget()
        self.plot_dock = self.ui.addDock(name='plot', widget=widget, position='right')
        self.layout = QVBoxLayout(widget)

        if hasattr(self, "graph_layout"):
            self.graph_layout.deleteLater()  # see http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            del self.graph_layout
        self.graph_layout = pg.GraphicsLayoutWidget(border=(100, 100, 100))
        self.layout.addWidget(self.graph_layout)
        self.plot = self.graph_layout.addPlot(title=self.name)
        self.data = {
            "signal": np.arange(10),
            # "background": np.arange(10) / 10,
            "reference": np.arange(10) / 10,
            # "contrast": np.arange(10) / 100,
        }
        colors = ["g", "r", 'r', "w"]
        self.plot_lines = {}
        for i, name in enumerate(self.data):
            self.plot_lines[name] = self.plot.plot(
                self.data[name], pen=colors[i], symbol="o", symbolBrush=colors[i]
            )
        
    def is_file_supported(self, fname):
        return self.name in fname

    def on_change_data_filename(self, fname):

        try:
            dat = self.dat = h5py.File(fname)
            sample = dat['app/settings'].attrs['sample']
            self.M = dat[f'measurement/{self.name}']

            for name in ["signal", "reference"]:
                x = self.M["frequencies"][:]
                y = self.M[name][:]
                self.plot_lines[name].setData(x, y)
                
            self.databrowser.ui.statusbar.showMessage(f"sample: {sample}")
            
        except Exception as err:
            self.databrowser.ui.statusbar.showMessage("failed to load %s:\n%s" % (fname, err))
            raise(err)
