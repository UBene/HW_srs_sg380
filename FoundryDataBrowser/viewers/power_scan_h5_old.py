from ScopeFoundry.data_browser import DataBrowserView
import pyqtgraph as pg
import h5py
from qtpy import QtWidgets, QtCore
import numpy as np
from ScopeFoundry.widgets import RegionSlicer, DataSelector

import pyqtgraph.dockarea as dockarea
from FoundryDataBrowser.viewers.plot_n_fit.plot_n_fit import PlotNFit
from FoundryDataBrowser.viewers.plot_n_fit.fitters.lmfit_fitters import (
    LogisticFunctionFitter,
)
from FoundryDataBrowser.viewers.plot_n_fit.fitters.poly_fitters import (
    LogLogPolyFitter,
    PolyFitter,
)


class UI(dockarea.DockArea):
    def __init__(
        self, plot_n_fit,
    ):
        super().__init__()

        self.plot_n_fit = plot_n_fit

        self.fit_graph_dock = self.addDock(plot_n_fit.ui.graph_dock)
        self.fit_settings_dock = self.addDock(
            plot_n_fit.ui.settings_dock, "right", self.fit_graph_dock
        )

        self.scatter = pg.ScatterPlotItem([1], [1], pen='r')
        self.plot_n_fit.ui.plot.addItem(self.scatter)

        self.graph_layout = pg.GraphicsLayoutWidget()
        self.spec_plot = self.graph_layout.addPlot()
        self.spec_line = self.spec_plot.plot([1, 2, 3, 4], [1, 3, 2, 4], pen="r")
        self.spec_dock = self.addDock(
            None, name="spectrum", position="bottom", relativeTo=self.fit_graph_dock
        )
        self.spec_dock.addWidget(self.graph_layout)

        self.data_select_dock = self.addDock(
            name="data select", position="right", relativeTo=self.fit_graph_dock
        )
        self.data_select_widget = QtWidgets.QWidget()
        self.data_select_layout = QtWidgets.QVBoxLayout()
        self.data_select_dock.addWidget(self.data_select_widget)
        self.data_select_widget.setLayout(self.data_select_layout)


class PowerScanH5View(DataBrowserView):

    name = "power_scan_h5"

    def is_file_supported(self, fname):
        return ("power_scan" in fname) and (".h5" in fname)

    def setup(self):

        self.plot_n_fit = PlotNFit(
            [LogisticFunctionFitter(), PolyFitter()]
            
        )
        self.ui = UI(self.plot_n_fit)

        self.settings.New("spec_index", dtype=int, initial=0)
        self.settings.spec_index.add_listener(self.update_spec_plot)

        self.settings.New("chan", dtype=int, initial=0)
        self.power_x_axis_choices = (
            "pm_powers",
            "pm_powers_after",
            "power_wheel_position",
        )
        self.settings.New(
            "power_x_axis",
            dtype=str,
            initial="pm_powers",
            choices=self.power_x_axis_choices,
        )
        self.settings.New("power_binning", int, initial=1, vmin=1)
        self.settings.New("conversion_factor", float, initial=1.0)

        self.ui.data_select_layout.addWidget(self.settings.New_UI())
        #self.spec_selector = DataSelector(self.ui.spec_line, "signal select",)
        self.bg_selector = DataSelector(self.ui.spec_line, "bg select")
        self.ui.data_select_layout.addWidget(self.bg_selector.New_UI())
        #self.ui.data_select_layout.addWidget(self.spec_selector.New_UI())

        for key in self.settings.keys():
            self.settings.get_lq(key).add_listener(self.update_fit)

        #self.spec_selector.add_listener(self.update_fit)
        self.bg_selector.add_listener(self.update_fit)

        self.wls = np.arange(512)
        self.spectra = 0.5 * np.arange(512 * 21 * 1).reshape((21, 1, 512))
        self.power_arrays = {"pm_powers": np.arange(21)}

    def on_change_data_filename(self, fname=None):

        if fname == "0":
            return

        try:
            self.data_loaded = False
            self.h5file = h5py.File(fname, "r")

            self.sample = ""
            if "sample" in self.h5file["app/settings"].attrs.keys():
                self.sample = self.h5file["app/settings"].attrs["sample"]
            if self.sample == "":
                self.sample = "<->"
            print("sample string", self.sample)

            if "measurement/power_scan_df" in self.h5file:
                self.H = self.h5file["measurement/power_scan_df"]
            else:
                self.H = self.h5file["measurement/power_scan"]

            H = self.H

            # # Provide spec_x_array and hyperspec_data
            # self.spec_x_array has shape (N_wls,) [dim=1]
            # self.hyperspec_data has shape (Np, N_channels, N_wls).
            #    E.g. with Np=21 and N_wls=512:
            self.spec_x_array = np.arange(512)
            self.hyperspec_data = 0.5 * np.arange(512 * 21 * 1).reshape((21, 1, 512))
            # If present override acq_times_array which will be used
            # to normalize to counts per second:
            acq_times_array = [None]

            self.aquisition_type = (
                "No data found"  # some info text that will be shown in the title
            )

            if "integrated_spectra" in H:
                for k in H.keys():
                    if "acq_times_array" in k:
                        acq_times_array = H[k][:]
                self.spec_x_array = H["wls"][:]
                self.hyperspec_data = H["spectra"][:].reshape(
                    -1, 1, len(self.spec_x_array)
                )
                self.aquisition_type = "Spectrum"

            for harp in ["picoharp", "hydraharp"]:
                if "{}_histograms".format(harp) in H:
                    histograms = H["{}_histograms".format(harp)][:]
                    acq_times_array = elapsed_time = H["{}_elapsed_time".format(harp)][
                        :
                    ]
                    self.spec_x_array = H["{}_time_array".format(harp)][:]
                    if np.ndim(histograms) == 2:
                        histograms = histograms.reshape(-1, 1, len(self.spec_x_array))
                    self.hyperspec_data = histograms
                    self.aquisition_type = harp

            if "apd_count_rates" in H:
                self.spec_x_slicer.settings["activated"] = False
                self.bg_slicer.settings["activated"] = False
                import time

                time.sleep(0.1)
                apd_count_rates = H["apd_count_rates"][:]
                self.hyperspec_data = apd_count_rates.reshape((-1, 1, 1))
                self.aquisition_type = "APD"

            if "thorlabs_powermeter_2_powers" in H:
                self.spec_x_slicer.settings["activated"] = False
                self.bg_slicer.settings["activated"] = False
                import time

                time.sleep(0.1)
                powers_y = H["thorlabs_powermeter_2_powers"][:]
                self.hyperspec_data = powers_y.reshape((-1, 1, 1))
                self.aquisition_type = "power_meter_2"

            Np = self.hyperspec_data.shape[0]
            if np.any(acq_times_array == None):
                self.hyperspec_data = (1.0 * self.hyperspec_data.T / acq_times_array).T
            else:
                self.hyperspec_data = 1.0 * self.hyperspec_data  # ensure floats

            # if scan was no completed the power arrays will be chopped
            # get power arrays
            self.power_arrays = {}
            for key in self.power_x_axis_choices:
                try:
                    self.power_arrays.update({key: H[key][:Np]})
                except:
                    pass
            self.settings.spec_index.change_min_max(0, Np - 1)
            self.settings.power_binning.change_min_max(1, Np)

            if Np != len(H["pm_powers"][:]):
                self.aquisition_type = "[INTERRUPTED Scan] " + self.aquisition_type

            self.h5file.close()

            self.data_loaded = True

            # self.settings['spec_index'] = 0

            self.databrowser.ui.statusbar.showMessage("loaded:{}\n".format(fname))

            n_chan = self.hyperspec_data.shape[1]
            self.settings.chan.change_min_max(0, n_chan - 1)
            self.ui.chan_doubleSpinBox.setEnabled(bool(n_chan - 1))

            self.update_power_plotcurve()

        except Exception as err:
            self.databrowser.ui.statusbar.showMessage(
                "failed to load {}:\n{}".format(fname, err)
            )

    def update_hyperspec(self):
        self.wls = np.arange(512)
        self.spectra = 0.5 * np.arange(512 * 21 * 1).reshape((21, 1, 512))
        self.power_arrays = {"pm_powers": np.arange(21)}

    def get_dependence_data(self):

        if self.bg_selector.activated.val:
            s = np.s_[:, self.settings["chan"], self.bg_selector.slice]
            bg = self.spectra[s].sum()
        else:
            bg = 0
        #bg = 0

        print("bg", bg)
        print('sum', self.spectra.sum())

        s = np.s_[:, self.settings["chan"], self.bg_selector.slice]
        data = np.copy(self.spectra[s])
        #data = self.spectra[:, self.settings["chan"], self.spec_selector.slice]
        #data = self.spectra[:, self.settings["chan"], :]
        binning = self.settings["power_binning"]
        if binning > 1:
            Np, ns = data.shape
            data = (
                data[: (Np // binning) * binning, :]
                .reshape(-1, binning, ns)
                .mean(axis=1)
            )

        print("mx", self.spectra.max(), data.max())
        x = self.power_arrays[self.settings["power_x_axis"]]
        binning = self.settings["power_binning"]
        if binning > 1:
            x = x[: (len(x) // binning) * binning].reshape(-1, binning).mean(-1)

        return x * self.settings["conversion_factor"], data.sum(axis=-1) - bg

    def update_spec_plot(self):
        S = self.settings
        print('update_spec_plot')
        #self.plot_n_fit.data_lines[0].setData(self.wls, np.random.rand(512))
        #self.ui.spec_line.setData(self.wls, np.random.rand(512))
        y = np.copy(self.spectra[S["spec_index"], S["chan"], :])
        self.ui.spec_line.setData(self.wls, y)

    def update_fit(self):
        x, y = self.get_dependence_data()
        print(x.max(), y.max())
        self.plot_n_fit.update_data(x, y, 0, False)
        self.plot_n_fit.update_fit()
        S = self.settings

        ii = int(S["spec_index"] / S["power_binning"])
        self.ui.scatter.setData(x=(x[ii],), y=(y[ii],))
        print(ii, "update_fit")


class _PowerScanH5View(DataBrowserView):

    name = "power_scan_h5"

    def is_file_supported(self, fname):
        return ("power_scan" in fname) and (".h5" in fname)

    def setup(self):
        self.data_loaded = False

        self.settings.New("spec_index", dtype=int, initial=0)
        self.settings.spec_index.add_listener(self.on_spec_index_change)

        self.settings.New("chan", dtype=int, initial=0)
        self.settings.chan.add_listener(self.update_power_plotcurve)

        self.power_x_axis_choices = (
            "pm_powers",
            "pm_powers_after",
            "power_wheel_position",
        )
        self.settings.New(
            "power_x_axis",
            dtype=str,
            initial="pm_powers",
            choices=self.power_x_axis_choices,
        )

        self.ui = QtWidgets.QGroupBox()
        self.ui.setLayout(QtWidgets.QVBoxLayout())

        self.graph_layout = pg.GraphicsLayoutWidget()
        self.ui.layout().addWidget(self.graph_layout)

        self.power_plot = self.graph_layout.addPlot()
        self.power_plot.setLogMode(x=True, y=True)
        self.power_plotcurve = self.power_plot.plot(
            [1, 2, 3, 4], [1, 3, 2, 4], name="Data", symbol="+", symbolBrush="m"
        )
        self.power_plot_current_pos = self.power_plot.plot(
            [1, 2, 3, 4], [1, 3, 2, 4], symbol="o", symbolBrush="r"
        )
        self.power_plot_current_pos.setZValue(10)
        self.power_fit_plotcurve = self.power_plot.plot(
            [1, 2, 3, 4], [1, 3, 2, 4], pen="g", name="Fit"
        )
        self.power_plotcurve_selected = self.power_plot.plot(
            [1, 2, 3, 4], [1, 3, 2, 4], symbol="o", pen=None, symbolPen="g"
        )

        self.graph_layout.nextRow()
        self.spec_plot = self.graph_layout.addPlot()
        self.spec_plotcurve = self.spec_plot.plot([1, 2, 3, 4], [1, 3, 2, 4], pen="r")

        settings_layout = QtWidgets.QGridLayout()
        self.ui.layout().addLayout(settings_layout)

        settings_layout.addWidget(QtWidgets.QLabel("data index:"), 0, 0)
        self.ui.spec_index_doubleSpinBox = QtWidgets.QDoubleSpinBox()
        self.settings.spec_index.connect_to_widget(self.ui.spec_index_doubleSpinBox)
        settings_layout.addWidget(self.ui.spec_index_doubleSpinBox, 0, 1)

        settings_layout.addWidget(QtWidgets.QLabel("data channel:"), 1, 0)
        self.ui.chan_doubleSpinBox = QtWidgets.QDoubleSpinBox()
        self.settings.chan.connect_to_widget(self.ui.chan_doubleSpinBox)
        settings_layout.addWidget(self.ui.chan_doubleSpinBox, 1, 1)

        settings_layout.addWidget(QtWidgets.QLabel("power x-axis:"), 2, 0)
        self.ui.power_x_axis_comboBox = QtWidgets.QComboBox()
        self.settings.power_x_axis.connect_to_widget(self.ui.power_x_axis_comboBox)
        settings_layout.addWidget(self.ui.power_x_axis_comboBox, 2, 1)

        self.settings.New("power_binning", int, initial=1, vmin=1)
        settings_layout.addWidget(QtWidgets.QLabel("power_binning:"), 3, 0)
        self.ui.power_binning_doubleSpinBox = QtWidgets.QDoubleSpinBox()
        settings_layout.addWidget(self.ui.power_binning_doubleSpinBox, 3, 1)
        self.settings.power_binning.connect_to_widget(
            self.ui.power_binning_doubleSpinBox
        )
        self.settings.power_binning.add_listener(self.update_power_plotcurve)

        self.power_plot_slicer = RegionSlicer(
            self.power_plotcurve, name="fit slicer", activated=False,
        )
        self.power_plot_slicer.region_changed_signal.connect(self.redo_fit)
        settings_layout.addWidget(self.power_plot_slicer.New_UI(), 4, 0)

        self.spec_x_slicer = RegionSlicer(
            self.spec_plotcurve, name="spec slicer", activated=False,
        )
        self.spec_x_slicer.region_changed_signal.connect(self.update_power_plotcurve)
        settings_layout.addWidget(self.spec_x_slicer.New_UI(), 4, 1)

        self.bg_slicer = RegionSlicer(
            self.spec_plotcurve, name="bg subtract", activated=False,
        )
        self.bg_slicer.region_changed_signal.connect(self.update_power_plotcurve)
        settings_layout.addWidget(self.bg_slicer.New_UI(), 4, 2)

        self.settings.New("conversion_factor", float, initial=1.0)
        settings_layout.addWidget(QtWidgets.QLabel("conversion_factor:"), 5, 0)
        self.ui.conversion_factor_doubleSpinBox = QtWidgets.QDoubleSpinBox()
        self.settings.conversion_factor.connect_to_widget(
            self.ui.conversion_factor_doubleSpinBox
        )
        settings_layout.addWidget(self.ui.conversion_factor_doubleSpinBox, 5, 1)
        self.settings.conversion_factor.add_listener(self.on_change_power_x_axis)

        self.settings.power_x_axis.add_listener(self.on_change_power_x_axis)

    def on_change_data_filename(self, fname=None):

        if fname == "0":
            return

        try:
            self.data_loaded = False
            self.h5file = h5py.File(fname, "r")

            self.sample = ""
            if "sample" in self.h5file["app/settings"].attrs.keys():
                self.sample = self.h5file["app/settings"].attrs["sample"]
            if self.sample == "":
                self.sample = "<->"
            print("sample string", self.sample)

            if "measurement/power_scan_df" in self.h5file:
                self.H = self.h5file["measurement/power_scan_df"]
            else:
                self.H = self.h5file["measurement/power_scan"]

            H = self.H

            # # Provide spec_x_array and hyperspec_data
            # self.spec_x_array has shape (N_wls,) [dim=1]
            # self.hyperspec_data has shape (Np, N_channels, N_wls).
            #    E.g. with Np=21 and N_wls=512:
            self.spec_x_array = np.arange(512)
            self.hyperspec_data = 0.5 * np.arange(512 * 21 * 1).reshape((21, 1, 512))
            # If present override acq_times_array which will be used
            # to normalize to counts per second:
            acq_times_array = [None]

            self.aquisition_type = (
                "No data found"  # some info text that will be shown in the title
            )

            if "integrated_spectra" in H:
                for k in H.keys():
                    if "acq_times_array" in k:
                        acq_times_array = H[k][:]
                self.spec_x_array = H["wls"][:]
                self.hyperspec_data = H["spectra"][:].reshape(
                    -1, 1, len(self.spec_x_array)
                )
                self.aquisition_type = "Spectrum"

            for harp in ["picoharp", "hydraharp"]:
                if "{}_histograms".format(harp) in H:
                    histograms = H["{}_histograms".format(harp)][:]
                    acq_times_array = elapsed_time = H["{}_elapsed_time".format(harp)][
                        :
                    ]
                    self.spec_x_array = H["{}_time_array".format(harp)][:]
                    if np.ndim(histograms) == 2:
                        histograms = histograms.reshape(-1, 1, len(self.spec_x_array))
                    self.hyperspec_data = histograms
                    self.aquisition_type = harp

            if "apd_count_rates" in H:
                self.spec_x_slicer.settings["activated"] = False
                self.bg_slicer.settings["activated"] = False
                import time

                time.sleep(0.1)
                apd_count_rates = H["apd_count_rates"][:]
                self.hyperspec_data = apd_count_rates.reshape((-1, 1, 1))
                self.aquisition_type = "APD"

            if "thorlabs_powermeter_2_powers" in H:
                self.spec_x_slicer.settings["activated"] = False
                self.bg_slicer.settings["activated"] = False
                import time

                time.sleep(0.1)
                powers_y = H["thorlabs_powermeter_2_powers"][:]
                self.hyperspec_data = powers_y.reshape((-1, 1, 1))
                self.aquisition_type = "power_meter_2"

            Np = self.hyperspec_data.shape[0]
            if np.any(acq_times_array == None):
                self.hyperspec_data = (1.0 * self.hyperspec_data.T / acq_times_array).T
            else:
                self.hyperspec_data = 1.0 * self.hyperspec_data  # ensure floats

            # if scan was no completed the power arrays will be chopped
            # get power arrays
            self.power_arrays = {}
            for key in self.power_x_axis_choices:
                try:
                    self.power_arrays.update({key: H[key][:Np]})
                except:
                    pass
            self.settings.spec_index.change_min_max(0, Np - 1)
            self.settings.power_binning.change_min_max(1, Np)

            if Np != len(H["pm_powers"][:]):
                self.aquisition_type = "[INTERRUPTED Scan] " + self.aquisition_type

            self.h5file.close()

            self.data_loaded = True

            # self.settings['spec_index'] = 0

            self.databrowser.ui.statusbar.showMessage("loaded:{}\n".format(fname))

            n_chan = self.hyperspec_data.shape[1]
            self.settings.chan.change_min_max(0, n_chan - 1)
            self.ui.chan_doubleSpinBox.setEnabled(bool(n_chan - 1))

            self.update_power_plotcurve()

        except Exception as err:
            self.databrowser.ui.statusbar.showMessage(
                "failed to load {}:\n{}".format(fname, err)
            )

    def on_spec_index_change(self):
        if not self.data_loaded:
            return
        ii = int(self.settings["spec_index"] // self.settings["power_binning"])

        x, y = self.X[ii], self.Y[ii]
        self.power_plot_current_pos.setData(x=[x], y=[y])

        spectrum = self.get_hyperspecdata(apply_spec_x_slicer=False)[ii, :]
        if len(self.spec_x_array) == len(spectrum):
            self.spec_plotcurve.setData(self.spec_x_array, spectrum)
        elif len(spectrum) == 1:
            self.spec_plotcurve.setData(spectrum)

        # show power wheel position
        power_wheel_position = self.power_arrays["power_wheel_position"][ii]
        self.databrowser.ui.statusbar.showMessage(
            "power_wheel_position: {:1.1f}".format(power_wheel_position)
        )
        power = self.power_arrays[self.settings["power_x_axis"]][ii]
        title = " ".join(
            [
                f"{self.sample}",
                self.aquisition_type,
                f" power position: {power_wheel_position:1.1f}",
                f" power: {power*1e3:1.2f} mW",
            ]
        )
        self.spec_plot.setTitle(title, color="r")

    @QtCore.Slot()
    def update_power_plotcurve(self):
        if not self.data_loaded:
            return
        self.X = self.get_power_x() * self.settings["conversion_factor"]
        self.Y = self.get_power_y(apply_spec_x_slicer=True)
        self.power_plotcurve.setData(self.X, self.Y)
        self.on_spec_index_change()
        self.redo_fit()

    @QtCore.Slot()
    def redo_fit(self):
        if not self.data_loaded:
            return

        mX = self.X > 0
        mY = self.Y > 0
        print(
            f"rejected {np.sum(np.invert(mX))} neg. X-values and {np.sum(np.invert(mY))} neg. Y-values"
        )
        s = self.power_plot_slicer.mask * mX * mY

        m, b = np.polyfit(np.log10(self.X[s]), np.log10(self.Y[s]), deg=1)
        print("fit values m,b:", m, b)
        fit_data = 10 ** (np.poly1d((m, b))(np.log10(self.X)))
        self.power_fit_plotcurve.setData(self.X[s], fit_data[s])
        self.power_plotcurve_selected.setData(self.X[s], self.Y[s])
        self.power_plot.setTitle("<h1> I<sup>{:1.2f}</sup></h1>".format(m))

    def on_change_power_x_axis(self):
        if not self.data_loaded:
            return
        self.update_power_plotcurve()

    def get_bg(self):
        if not self.data_loaded:
            return
        if self.bg_slicer.activated.val:
            bg = self.hyperspec_data[
                :, self.settings["chan"], self.bg_slicer.slice
            ].mean()
        else:
            bg = 0
        return bg

    def get_hyperspecdata(self, apply_spec_x_slicer=True):
        bg = self.get_bg()
        if apply_spec_x_slicer:
            hyperspec_data = self.hyperspec_data[
                :, self.settings["chan"], self.spec_x_slicer.s_
            ]
        else:
            hyperspec_data = self.hyperspec_data[:, self.settings["chan"], :]

        binning = self.settings["power_binning"]
        if binning > 1:
            np, ns = hyperspec_data.shape
            hyperspec_data = (
                hyperspec_data[: (np // binning) * binning, :]
                .reshape(-1, binning, ns)
                .mean(axis=1)
            )

        return hyperspec_data - bg

    def get_power_y(self, apply_spec_x_slicer=True):
        hyperspec = self.get_hyperspecdata(apply_spec_x_slicer=apply_spec_x_slicer)
        y = hyperspec.sum(axis=-1)
        return y

    def get_power_x(self):
        x = self.power_arrays[self.settings["power_x_axis"]]

        binning = self.settings["power_binning"]
        if binning > 1:
            x = x[: (len(x) // binning) * binning].reshape(-1, binning).mean(-1)
        return x


if __name__ == "__main__":
    import sys
    from ScopeFoundry.data_browser import DataBrowser

    app = DataBrowser(sys.argv)
    p = PowerScanH5View(app)
    app.load_view(p)
    p.get_dependence_data()

    sys.exit(app.exec_())
