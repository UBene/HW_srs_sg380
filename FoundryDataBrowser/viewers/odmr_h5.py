from ScopeFoundry.data_browser import DataBrowserView
import numpy as np
import h5py
import pyqtgraph as pg
from pyqtgraph.dockarea.DockArea import DockArea
from qtpy.QtWidgets import QVBoxLayout, QWidget

from pyqtgraph.dockarea.Dock import Dock
from odmr_measurements.helper_functions import channel_settings


class PulseProgramPlot:
    def __init__(self, channel_settings=None):
        if channel_settings:
            self.channel_settings = channel_settings
        else:
            self.channel_settings = {}
        self.pens = {d['name']: d['colors'][0] for d in channel_settings}

    def New_dock_UI(self) -> Dock:
        dock = Dock(name=' pulse generator')
        graph_layout = pg.GraphicsLayoutWidget(border=(0, 0, 0))
        dock.addWidget(graph_layout)
        self.plot = graph_layout.addPlot(title='pulse profile')
        self.plot.setLabel('bottom', units='s')
        self.plot.addLegend()
        return dock

    def update_pulse_plot(self, pulse_plot_arrays) -> None:
        plot: pg.PlotItem = self.plot
        plot.clear()
        for ii, (name, (t, y)) in enumerate(pulse_plot_arrays.items()):
            y = np.array(y) - 2 * ii
            t = np.array(t) / 1e9
            plot.plot(t, y, name=name,
                      pen=self.pens.get(name, 'w')
                      )


SUPPORTED_MEASUREMENTS = ('rabi',
                          'esr',
                          'T1',
                          'T2',
                          'XY8',
                          'correlation_spectroscopy',
                          'optimal_readout_delay')

SUPPORTED_XARRAYS = ('frequencies',
                     'pulse_durations')

SUPPORTED_YARRAYS = ("signal",
                     "reference",
                     'signalOnly',
                     'signalOverReference',
                     'differenceOverSum')


class ODMRH5(DataBrowserView):

    name = 'odmr'

    def setup(self):

        self.fname = None

        for name in SUPPORTED_YARRAYS:
            lq = self.settings.New(name, bool, initial=False)
            lq.add_listener(self.show_lines)

        self.settings['signal'] = True
        self.settings['reference'] = True

        self.ui = DockArea()
        widget = QWidget()
        self.plot_dock = self.ui.addDock(
            name='plot', widget=widget, position='right')
        self.layout = QVBoxLayout(widget)

        if hasattr(self, "graph_layout"):
            self.graph_layout.deleteLater()
            del self.graph_layout
        self.graph_layout = pg.GraphicsLayoutWidget(border=(100, 100, 100))
        self.layout.addWidget(self.graph_layout)
        self.plot = self.graph_layout.addPlot(title=self.name)
        self.data = {y: np.arange(10) for y in SUPPORTED_YARRAYS}
        self.plot_lines = {}
        for i, name in enumerate(SUPPORTED_YARRAYS):
            self.plot_lines[name] = self.plot.plot(
                self.data[name], symbol="o", name=name
            )

        self.plot.addLegend()

        self.pulse_plot = PulseProgramPlot(channel_settings)
        self.ui.addDock(self.pulse_plot.New_dock_UI())

        self.ui.addDock(name='settings', widget=self.settings.New_UI())

    def is_file_supported(self, fname):
        for exp in SUPPORTED_MEASUREMENTS:
            if exp in fname:
                self.exp = exp
                return True
        return False

    def show_lines(self):
        for name, line in self.plot_lines.items():
            line.setVisible(self.settings[name])

    def load_data(self, fname):
        with h5py.File(fname) as H:
            sample = H['app/settings'].attrs['sample']
            M = H[f'measurement/{self.exp}']

            X = list(set(M).intersection(set(SUPPORTED_XARRAYS)))

            for name in list(set(SUPPORTED_YARRAYS).intersection(set(M))):
                y = M[name][:]
                if X:
                    self.plot_lines[name].setData(M[X[0]][:], y)
                    self.plot.setLabel('bottom', X[0])
                else:
                    self.plot_lines[name].setData(y=y)
                    self.plot.setLabel('bottom', '')

            self.show_lines()
            self.plot.setTitle(self.exp)
            channels = ['STARTtrig', 'AOM', 'DAQ', 'DAQ_sig', 'DAQ_ref']
            pulse_plot_arrays = {p: M[p][:] for p in channels if p in M}

        self.pulse_plot.update_pulse_plot(pulse_plot_arrays)
        self.databrowser.ui.statusbar.showMessage(f"sample: {sample}")

    def on_change_data_filename(self, fname):
        self.load_data(fname)
