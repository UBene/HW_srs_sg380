"""
Created on Mar 9, 2022

@author: Benedikt Ursprung
"""
import pyqtgraph as pg
import pyqtgraph.dockarea as dockarea
from qtpy import QtWidgets


class PlotNFitPGDockArea(dockarea.DockArea):
    """
    ui for plotNFit that provides
        1. setting_dock
        2. graph_dock with fit_line and data_lines
    """

    def __init__(self, Ndata_lines=1, pens=["w"]):
        super().__init__()

        self.settings_ui = QtWidgets.QWidget()
        self.settings_layout = QtWidgets.QVBoxLayout()
        self.settings_ui.setLayout(self.settings_layout)
        self.settings_dock = dockarea.Dock(name="Fit Settings", widget=self.settings_ui)
        self.addDock(self.settings_dock)
        VSpacerItem = QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        self.settings_layout.addItem(VSpacerItem)

        self.graph_layout = pg.GraphicsLayoutWidget()
        self.plot = self.graph_layout.addPlot()
        self.graph_dock = dockarea.Dock(name="Graph Plot", widget=self.graph_layout)
        self.addDock(self.graph_dock, position="right", relativeTo=self.settings_dock)
        self.settings_dock.setStretch(1, 1)

        self.data_lines = []
        for i in range(Ndata_lines):
            self.data_lines.append(self.plot.plot(y=[0, 2, 1, 3, 2], pen=pens[i]))

        self.fit_line = self.plot.plot(x=[0, 1, 2, 3], y=[0, 2, 1, 3], pen=pg.mkColor("g"))
        self.select_scatter = pg.ScatterPlotItem(
            x=[0, 1, 2, 3], y=[0, 2, 1, 3], pen="g"
        )
        self.plot.addItem(self.select_scatter)

        self.fitter_widgets = {}
        self.reset_highlight_x_values()

        self.clipboard = QtWidgets.QApplication.clipboard()

    def reset_highlight_x_values(self):
        if hasattr(self, "vertical_lines"):
            for l in self.vertical_lines:
                self.plot.removeItem(l)
                l.deleteLater()
        self.vertical_lines = []

    def highlight_x_values(self, values):
        self.reset_highlight_x_values()
        pen = "g"

        for x in values:
            l = pg.InfiniteLine(
                pos=(x, 0),
                movable=False,
                angle=90,
                pen=pen,
                label="{value:0.2f}",
                labelOpts={"color": pen, "movable": True, "fill": (200, 200, 200, 100)},
            )
            self.plot.addItem(l)
            self.vertical_lines.append(l)

    def clear(self):
        self.select_scatter.clear()
        self.fit_line.clear()

    def update_fit_line(self, x, y):
        self.fit_line.setData(x, y)

    def update_select_scatter(self, x, y):
        self.select_scatter.setData(x, y)

    def update_data_line(self, x, y, line_number=0):
        self.data_lines[line_number].setData(x, y)

    def add_to_settings_layout(self, widget):
        n = self.settings_layout.count() - 1
        self.settings_layout.insertWidget(n, widget)

    def add_button(self, name, callback_func):
        PB = QtWidgets.QPushButton(name)
        PB.clicked.connect(callback_func)
        self.add_to_settings_layout(PB)

    def add_fitter_widget(self, name, widget):
        self.fitter_widgets[name] = widget
        widget.setVisible(False)
        self.add_to_settings_layout(widget)

    def activate_fitter_widget(self, name: str):
        for k, widget in self.fitter_widgets.items():
            widget.setVisible(k == name)

    def set_clipboard_text(self, text):
        self.clipboard.setText(text)

    def clipboard_plot(self):
        import pyqtgraph.exporters as exp

        exporter = exp.SVGExporter(self.plot)
        exporter.parameters()["scaling stroke"] = False
        exporter.export(copy=True)
